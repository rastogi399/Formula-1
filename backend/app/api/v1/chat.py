"""
Solana Copilot - Chat Router
WebSocket-based chat interface for conversational wallet control
"""

import json
import logging
from typing import Dict, Any
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import User, Automation
from app.api.v1.auth import get_current_user
from app.agents.intent_classifier import classify_intent
from app.agents.transaction_planner import plan_swap_transaction
from app.schemas import ChatMessage, ChatResponse
from app.integrations.jupiter.client import (
    JupiterError,
    JupiterQuoteError,
    JupiterTransactionError,
    JupiterNetworkError,
    InsufficientLiquidityError,
    TokenNotFoundError,
)
from app.services.transaction_service import transaction_service

logger = logging.getLogger(__name__)


def get_user_friendly_error(error: Exception) -> str:
    """Convert exceptions to user-friendly messages"""
    if isinstance(error, TokenNotFoundError):
        return f"I don't recognize that token. {str(error)}"
    elif isinstance(error, InsufficientLiquidityError):
        return f"There isn't enough liquidity for this swap. Try a smaller amount or a different token pair."
    elif isinstance(error, JupiterNetworkError):
        return "I'm having trouble connecting to the exchange. Please try again in a moment."
    elif isinstance(error, JupiterQuoteError):
        return f"I couldn't get a quote for this swap. {str(error)}"
    elif isinstance(error, JupiterTransactionError):
        return f"I couldn't prepare the transaction. {str(error)}"
    elif isinstance(error, JupiterError):
        return f"Something went wrong with the swap service: {str(error)}"
    else:
        return f"An unexpected error occurred: {str(error)}"

router = APIRouter()


# ============================================
# WebSocket Connection Manager
# ============================================

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, wallet: str, websocket: WebSocket):
        """Accept and store connection"""
        await websocket.accept()
        self.active_connections[wallet] = websocket
        logger.info(f"WebSocket connected: {wallet}")
    
    def disconnect(self, wallet: str):
        """Remove connection"""
        if wallet in self.active_connections:
            del self.active_connections[wallet]
            logger.info(f"WebSocket disconnected: {wallet}")
    
    async def send_message(self, wallet: str, message: dict):
        """Send message to specific wallet"""
        if wallet in self.active_connections:
            await self.active_connections[wallet].send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast to all connections"""
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


# ============================================
# WebSocket Endpoint
# ============================================

@router.websocket("/ws")
async def websocket_chat(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time chat.
    
    Client sends:
    {
        "type": "message",
        "content": "Swap 20 USDC to SOL",
        "session_id": "optional"
    }
    
    Server responds:
    {
        "type": "response",
        "id": "msg_123",
        "status": "processing|awaiting_approval|success|error",
        "data": {...}
    }
    """
    
    # Verify token and get user
    from app.core.security import verify_token
    wallet = verify_token(token)
    
    if not wallet:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    # Connect
    await manager.connect(wallet, websocket)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "message":
                await handle_chat_message(websocket, wallet, data, db)
            
            elif message_type == "approval":
                await handle_approval(websocket, wallet, data, db)
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(wallet)
        logger.info(f"Client disconnected: {wallet}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(wallet)


async def handle_chat_message(
    websocket: WebSocket,
    wallet: str,
    data: Dict[str, Any],
    db: AsyncSession,
):
    """Handle incoming chat message"""
    
    try:
        user_input = data.get("content", "")
        message_id = str(uuid4())
        
        # Send acknowledgment
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "processing",
            "message": "Processing your request...",
        })
        
        # Step 1: Classify intent
        intent_result = await classify_intent(user_input, wallet)
        
        action = intent_result["action"]
        confidence = intent_result["confidence"]
        parameters = intent_result["parameters"]
        
        logger.info(f"Intent: {action} (confidence: {confidence})")
        
        # Step 2: Route to appropriate handler
        if action == "swap":
            await handle_swap_intent(
                websocket, wallet, message_id, parameters, db
            )
        
        elif action == "analyze":
            await handle_analyze_intent(
                websocket, wallet, message_id, parameters, db
            )
        
        elif action == "query":
            await handle_query_intent(
                websocket, wallet, message_id, parameters, db
            )

        elif action == "create_automation":
            await handle_automation_intent(
                websocket, wallet, message_id, parameters, db
            )

        elif action == "send":
            await handle_send_intent(
                websocket, wallet, message_id, parameters, db
            )

        else:
            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "error",
                "message": f"Action '{action}' not yet implemented",
            })
    
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "error",
            "message": str(e),
        })


async def handle_swap_intent(
    websocket: WebSocket,
    wallet: str,
    message_id: str,
    parameters: Dict[str, Any],
    db: AsyncSession,
):
    """Handle swap intent"""

    try:
        # Extract parameters
        source_token = parameters.get("source_token")
        dest_token = parameters.get("dest_token")
        amount = parameters.get("amount")
        slippage_bps = parameters.get("slippage_bps", 100)

        if not all([source_token, dest_token, amount]):
            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "error",
                "message": "Missing required parameters for swap",
            })
            return

        # Get user from database for transaction logging
        user = await transaction_service.get_user_by_wallet(db, wallet)

        # Plan transaction
        result = await plan_swap_transaction(
            user_wallet=wallet,
            source_token=source_token,
            dest_token=dest_token,
            amount=float(amount),
            slippage_bps=slippage_bps,
        )

        # Check for errors
        if result.get("error"):
            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "error",
                "message": result["error"],
            })
            return

        # Log pending transaction to database
        tx_record = None
        if user:
            tx_record = await transaction_service.create_pending_transaction(
                db=db,
                user_id=user.id,
                action="swap",
                source_token=source_token,
                dest_token=dest_token,
                amount_in=float(amount),
                ai_reasoning={
                    "selected_route": result.get("selected_route", {}),
                    "simulation": result.get("simulation_result", {}),
                    "slippage_bps": slippage_bps,
                },
            )

        # Send transaction preview with swap transaction for signing
        simulation = result.get("simulation_result", {})

        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "awaiting_approval",
            "action": "swap",
            "preview": {
                "from": f"{amount} {source_token}",
                "to": f"~{simulation.get('amount_out', 0):.6f} {dest_token}",
                "fromToken": source_token,
                "toToken": dest_token,
                "fromAmount": str(amount),
                "toAmount": str(simulation.get("amount_out", 0)),
                "route": result.get("selected_route", {}).get("route", "Best Route"),
                "price_impact": f"{simulation.get('price_impact', 0)}%",
                "priceImpact": str(simulation.get("price_impact", 0)),
                "gas_estimate": f"{simulation.get('gas_estimate', 0)} lamports",
                "fee": f"{simulation.get('gas_estimate', 0)} lamports",
                "riskLevel": "low" if float(simulation.get("price_impact", 0)) < 1 else "medium",
            },
            # Include the base64 encoded swap transaction for frontend signing
            "swapTransaction": result.get("swap_transaction"),
            "transaction_data": result,
            # Include transaction record ID for logging
            "transaction_record_id": str(tx_record.id) if tx_record else None,
        })
    
    except JupiterError as e:
        logger.error(f"Jupiter error handling swap: {e}", exc_info=True)
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "error",
            "message": get_user_friendly_error(e),
        })
    except Exception as e:
        logger.error(f"Error handling swap: {e}", exc_info=True)
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "error",
            "message": get_user_friendly_error(e),
        })


async def handle_analyze_intent(
    websocket: WebSocket,
    wallet: str,
    message_id: str,
    parameters: Dict[str, Any],
    db: AsyncSession,
):
    """Handle portfolio analysis intent"""
    
    try:
        # Get portfolio data (simplified)
        from app.integrations.solana.client import get_solana_client
        
        client = get_solana_client()
        balances = await client.get_all_token_balances(wallet)
        
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "success",
            "action": "analyze",
            "data": {
                "total_tokens": len(balances),
                "balances": balances,
                "message": "Portfolio analysis complete",
            },
        })
    
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}", exc_info=True)
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "error",
            "message": str(e),
        })


async def handle_query_intent(
    websocket: WebSocket,
    wallet: str,
    message_id: str,
    parameters: Dict[str, Any],
    db: AsyncSession,
):
    """Handle general query intent"""
    
    try:
        query_type = parameters.get("query_type", "general")
        
        # Simple query handling
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "success",
            "action": "query",
            "message": "Query processed. More features coming soon!",
        })
    
    except Exception as e:
        logger.error(f"Error handling query: {e}", exc_info=True)
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "error",
            "message": str(e),
        })


async def handle_automation_intent(
    websocket: WebSocket,
    wallet: str,
    message_id: str,
    parameters: Dict[str, Any],
    db: AsyncSession,
):
    """Handle DCA and automation creation intent"""

    try:
        automation_type = parameters.get("automation_type", "dca")
        source_token = parameters.get("source_token")
        dest_token = parameters.get("dest_token")
        amount = parameters.get("amount")
        frequency = parameters.get("frequency", "daily")

        # Validate required parameters
        if not all([source_token, dest_token, amount]):
            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "error",
                "message": "Please specify source token, destination token, and amount for your automation.",
            })
            return

        # Convert frequency to seconds
        frequency_map = {
            "hourly": 3600,
            "daily": 86400,
            "weekly": 604800,
            "monthly": 2592000,
        }
        frequency_seconds = frequency_map.get(frequency.lower(), 86400)

        # Get user from database
        user = await transaction_service.get_user_by_wallet(db, wallet)

        if not user:
            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "error",
                "message": "User not found. Please reconnect your wallet.",
            })
            return

        # Calculate next execution time
        from datetime import datetime, timedelta
        next_execution = datetime.utcnow() + timedelta(seconds=frequency_seconds)

        # Create automation in database
        automation = Automation(
            user_id=user.id,
            automation_type=automation_type,
            name=f"{automation_type.upper()}: {amount} {source_token} → {dest_token} ({frequency})",
            source_token=source_token,
            dest_token=dest_token,
            amount=amount,
            frequency_seconds=frequency_seconds,
            status="active",
            next_execution_at=next_execution,
            extra_data={
                "frequency_label": frequency,
                "created_via": "chat",
            },
        )

        db.add(automation)
        await db.commit()
        await db.refresh(automation)

        logger.info(f"Created automation {automation.id} for user {user.id}")

        # Send success response
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "success",
            "action": "create_automation",
            "message": f"I've set up your {automation_type.upper()} automation! It will swap {amount} {source_token} to {dest_token} {frequency}.",
            "automation": {
                "id": str(automation.id),
                "type": automation_type,
                "source_token": source_token,
                "dest_token": dest_token,
                "amount": str(amount),
                "frequency": frequency,
                "next_execution": next_execution.isoformat(),
                "status": "active",
            },
        })

    except Exception as e:
        logger.error(f"Error creating automation: {e}", exc_info=True)
        await db.rollback()
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "error",
            "message": f"Failed to create automation: {str(e)}",
        })


async def handle_send_intent(
    websocket: WebSocket,
    wallet: str,
    message_id: str,
    parameters: Dict[str, Any],
    db: AsyncSession,
):
    """Handle send/transfer token intent"""

    try:
        dest_wallet = parameters.get("dest_wallet")
        token = parameters.get("token", "SOL")
        amount = parameters.get("amount")

        # Validate required parameters
        if not dest_wallet:
            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "error",
                "message": "Please specify a destination wallet address.",
            })
            return

        if not amount:
            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "error",
                "message": "Please specify the amount to send.",
            })
            return

        # Validate destination wallet address format (basic check)
        if len(dest_wallet) < 32 or len(dest_wallet) > 44:
            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "error",
                "message": "Invalid destination wallet address format.",
            })
            return

        # Get user from database for transaction logging
        user = await transaction_service.get_user_by_wallet(db, wallet)

        # Log pending transaction
        tx_record = None
        if user:
            tx_record = await transaction_service.create_pending_transaction(
                db=db,
                user_id=user.id,
                action="send",
                source_token=token,
                dest_token=token,  # Same token for sends
                amount_in=float(amount),
                ai_reasoning={
                    "dest_wallet": dest_wallet,
                    "token": token,
                },
            )

        # Estimate transfer fee (SOL transfers use ~5000 lamports)
        estimated_fee = 0.000005  # ~5000 lamports in SOL

        # Send preview for user approval
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "awaiting_approval",
            "action": "send",
            "preview": {
                "type": "send",
                "token": token,
                "amount": str(amount),
                "from": wallet,
                "to": dest_wallet,
                "fee": f"~{estimated_fee} SOL",
                "riskLevel": "low",
            },
            "transaction_data": {
                "action": "send",
                "token": token,
                "amount": float(amount),
                "dest_wallet": dest_wallet,
            },
            "transaction_record_id": str(tx_record.id) if tx_record else None,
        })

    except Exception as e:
        logger.error(f"Error handling send: {e}", exc_info=True)
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "error",
            "message": f"Failed to prepare transfer: {str(e)}",
        })


async def handle_approval(
    websocket: WebSocket,
    wallet: str,
    data: Dict[str, Any],
    db: AsyncSession,
):
    """Handle transaction approval/rejection"""

    message_id = data.get("message_id")

    try:
        approved = data.get("approved", False)
        transaction_data = data.get("transaction_data", {})
        tx_signature = data.get("tx_signature")  # From frontend after signing
        transaction_record_id = data.get("transaction_record_id")

        if approved:
            # Update transaction record as approved
            if transaction_record_id:
                from uuid import UUID
                simulation = transaction_data.get("simulation_result", {})
                await transaction_service.update_transaction_approved(
                    db=db,
                    transaction_id=UUID(transaction_record_id),
                    amount_out=simulation.get("amount_out"),
                    gas_fee=simulation.get("gas_estimate"),
                )

            # If frontend sent a tx_signature, the transaction was executed on-chain
            if tx_signature:
                # Update transaction record as executed
                if transaction_record_id:
                    await transaction_service.update_transaction_executed(
                        db=db,
                        transaction_id=UUID(transaction_record_id),
                        tx_signature=tx_signature,
                    )

                await websocket.send_json({
                    "type": "response",
                    "id": message_id,
                    "status": "success",
                    "message": "Transaction executed successfully",
                    "tx_signature": tx_signature,
                })
            else:
                # Transaction approved but not yet executed (frontend will sign and send)
                await websocket.send_json({
                    "type": "response",
                    "id": message_id,
                    "status": "approved",
                    "message": "Transaction approved. Please sign with your wallet.",
                })
        else:
            # User rejected the transaction
            if transaction_record_id:
                from uuid import UUID
                await transaction_service.update_transaction_failed(
                    db=db,
                    transaction_id=UUID(transaction_record_id),
                    error_message="Transaction cancelled by user",
                )

            await websocket.send_json({
                "type": "response",
                "id": message_id,
                "status": "cancelled",
                "message": "Transaction cancelled by user",
            })

    except Exception as e:
        logger.error(f"Error handling approval: {e}", exc_info=True)
        await websocket.send_json({
            "type": "response",
            "id": message_id,
            "status": "error",
            "message": str(e),
        })


# ============================================
# HTTP Endpoints (Alternative to WebSocket)
# ============================================

@router.post("/send", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    HTTP endpoint for chat.
    """
    
    try:
        # Classify intent
        intent_result = await classify_intent(
            message.message,
            current_user.wallet_address
        )
        
        action = intent_result["action"]
        params = intent_result["parameters"]
        
        # Default response
        response = ChatResponse(
            id=str(uuid4()),
            status="success",
            action=action,
            message=f"I understood you want to {action}.",
            preview={
                "confidence": intent_result["confidence"],
                "parameters": params,
            }
        )
        
        if action == "swap":
            # Validate params
            if not all([params.get("source_token"), params.get("dest_token"), params.get("amount")]):
                response.status = "error"
                response.message = "Please specify source token, destination token, and amount."
                return response

            source_token = params.get("source_token")
            dest_token = params.get("dest_token")
            amount = float(params.get("amount", 0))
            slippage_bps = params.get("slippage_bps", 100)

            # Plan transaction
            result = await plan_swap_transaction(
                user_wallet=current_user.wallet_address,
                source_token=source_token,
                dest_token=dest_token,
                amount=amount,
                slippage_bps=slippage_bps,
            )

            if result.get("error"):
                response.status = "error"
                response.error = result["error"]
                response.message = f"Failed to plan swap: {result['error']}"
            else:
                simulation = result.get("simulation_result", {})
                amount_out = simulation.get("amount_out", 0)
                price_impact = simulation.get("price_impact", 0)

                # Log pending transaction to database
                tx_record = await transaction_service.create_pending_transaction(
                    db=db,
                    user_id=current_user.id,
                    action="swap",
                    source_token=source_token,
                    dest_token=dest_token,
                    amount_in=amount,
                    ai_reasoning={
                        "selected_route": result.get("selected_route", {}),
                        "simulation": simulation,
                        "slippage_bps": slippage_bps,
                    },
                )

                response.status = "awaiting_approval"
                response.message = f"I've prepared a swap for {amount} {source_token} to ~{amount_out:.6f} {dest_token}. Please review and approve."

                # Construct TransactionDetails for frontend signing
                response.transaction = {
                    "type": "swap",
                    "fromToken": source_token,
                    "fromAmount": str(amount),
                    "toToken": dest_token,
                    "toAmount": f"{amount_out:.6f}",
                    "priceImpact": f"{price_impact}%",
                    "fee": f"{simulation.get('gas_estimate', 0)} lamports",
                    "route": result.get("selected_route", {}).get("route", "Best Route"),
                    "riskLevel": "low" if float(price_impact) < 1 else "medium",
                    # Critical: Include swap transaction for frontend signing
                    "swapTransaction": result.get("swap_transaction"),
                    # Include transaction record ID for logging
                    "transactionRecordId": str(tx_record.id),
                }
        
        elif action == "analyze":
            response.message = "I'm analyzing your portfolio... (Analysis feature coming soon)"

        elif action == "create_automation":
            automation_type = params.get("automation_type", "dca")
            source_token = params.get("source_token")
            dest_token = params.get("dest_token")
            amount = params.get("amount")
            frequency = params.get("frequency", "daily")

            if not all([source_token, dest_token, amount]):
                response.status = "error"
                response.message = "Please specify source token, destination token, and amount for your automation."
                return response

            # Convert frequency to seconds
            frequency_map = {
                "hourly": 3600,
                "daily": 86400,
                "weekly": 604800,
                "monthly": 2592000,
            }
            frequency_seconds = frequency_map.get(frequency.lower(), 86400)

            from datetime import datetime, timedelta
            next_execution = datetime.utcnow() + timedelta(seconds=frequency_seconds)

            # Create automation in database
            automation = Automation(
                user_id=current_user.id,
                automation_type=automation_type,
                name=f"{automation_type.upper()}: {amount} {source_token} → {dest_token} ({frequency})",
                source_token=source_token,
                dest_token=dest_token,
                amount=amount,
                frequency_seconds=frequency_seconds,
                status="active",
                next_execution_at=next_execution,
                extra_data={
                    "frequency_label": frequency,
                    "created_via": "chat",
                },
            )

            db.add(automation)
            await db.commit()
            await db.refresh(automation)

            response.status = "success"
            response.message = f"I've set up your {automation_type.upper()} automation! It will swap {amount} {source_token} to {dest_token} {frequency}."
            response.preview = {
                "id": str(automation.id),
                "type": automation_type,
                "source_token": source_token,
                "dest_token": dest_token,
                "amount": str(amount),
                "frequency": frequency,
                "next_execution": next_execution.isoformat(),
                "status": "active",
            }

        elif action == "send":
            dest_wallet = params.get("dest_wallet")
            token = params.get("token", "SOL")
            amount = params.get("amount")

            if not dest_wallet or not amount:
                response.status = "error"
                response.message = "Please specify destination wallet and amount to send."
                return response

            # Log pending transaction
            tx_record = await transaction_service.create_pending_transaction(
                db=db,
                user_id=current_user.id,
                action="send",
                source_token=token,
                dest_token=token,
                amount_in=float(amount),
                ai_reasoning={
                    "dest_wallet": dest_wallet,
                    "token": token,
                },
            )

            response.status = "awaiting_approval"
            response.message = f"Ready to send {amount} {token} to {dest_wallet[:8]}...{dest_wallet[-4:]}. Please approve the transaction."
            response.transaction = {
                "type": "send",
                "token": token,
                "amount": str(amount),
                "fromWallet": current_user.wallet_address,
                "toWallet": dest_wallet,
                "fee": "~0.000005 SOL",
                "riskLevel": "low",
                "transactionRecordId": str(tx_record.id),
            }

        return response

    except JupiterError as e:
        logger.error(f"Jupiter error processing message: {e}", exc_info=True)
        return ChatResponse(
            id=str(uuid4()),
            status="error",
            error=str(e),
            message=get_user_friendly_error(e)
        )
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return ChatResponse(
            id=str(uuid4()),
            status="error",
            error=str(e),
            message=get_user_friendly_error(e)
        )


@router.post("/confirm-transaction")
async def confirm_transaction(
    transaction_record_id: str,
    tx_signature: str,
    success: bool = True,
    error_message: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm transaction execution from frontend.

    Called by frontend after signing and submitting a transaction.
    Updates the transaction record with the result.
    """
    from uuid import UUID

    try:
        tx_id = UUID(transaction_record_id)

        if success:
            await transaction_service.update_transaction_executed(
                db=db,
                transaction_id=tx_id,
                tx_signature=tx_signature,
            )
            return {
                "status": "success",
                "message": "Transaction recorded successfully",
                "tx_signature": tx_signature,
            }
        else:
            await transaction_service.update_transaction_failed(
                db=db,
                transaction_id=tx_id,
                error_message=error_message or "Transaction failed",
            )
            return {
                "status": "failed",
                "message": "Transaction failure recorded",
            }

    except Exception as e:
        logger.error(f"Error confirming transaction: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
        }


@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    action: str = None,
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get transaction history for the current user.
    """
    try:
        transactions = await transaction_service.get_user_transactions(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            action=action,
            status=status,
        )

        return {
            "status": "success",
            "transactions": [
                {
                    "id": str(tx.id),
                    "action": tx.action,
                    "source_token": tx.source_token,
                    "dest_token": tx.dest_token,
                    "amount_in": float(tx.amount_in) if tx.amount_in else None,
                    "amount_out": float(tx.amount_out) if tx.amount_out else None,
                    "status": tx.status,
                    "tx_signature": tx.tx_signature,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                    "execution_timestamp": tx.execution_timestamp.isoformat() if tx.execution_timestamp else None,
                }
                for tx in transactions
            ],
            "total": len(transactions),
        }

    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "transactions": [],
        }
