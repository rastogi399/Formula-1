"""
Solana Copilot - Transaction Planner Agent
Multi-step orchestration of swap transactions with route optimization
"""

import logging
from typing import Any, Dict, List, TypedDict, Optional

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agents.base_agent import BaseAgent, BaseAgentState
from app.agents.tools import (
    get_sol_balance,
    get_token_balance,
    get_swap_quote,
    get_best_swap_route,
    simulate_swap,
    SWAP_TOOLS,
    BALANCE_TOOLS,
    SIMULATION_TOOLS,
)

logger = logging.getLogger(__name__)


# ============================================
# State Definition
# ============================================

class TransactionPlannerState(BaseAgentState):
    """State for transaction planning"""
    # Input
    action: str  # "swap", "send", "stake"
    source_token: str
    dest_token: str
    amount: Optional[float]
    percentage: Optional[float]  # For "50% of my SOL" type commands
    slippage_bps: int
    
    # Balance check
    balance_check: Dict[str, Any]
    sufficient_balance: bool
    
    # Route optimization
    route_options: List[Dict[str, Any]]
    selected_route: Dict[str, Any]
    
    # Simulation
    simulation_result: Dict[str, Any]
    simulation_success: bool
    
    # Approval
    user_approved: bool
    approval_required: bool
    
    # Execution
    tx_signature: Optional[str]
    execution_result: Dict[str, Any]


# ============================================
# Transaction Planner Agent
# ============================================

class TransactionPlannerAgent(BaseAgent):
    """
    Plans and executes swap transactions with multi-step orchestration.
    
    Flow:
    1. Parse intent → Check balance → Fetch routes → Rank routes
    2. Simulate transaction → Get approval → Execute
    
    Example:
        >>> agent = TransactionPlannerAgent()
        >>> result = await agent.ainvoke({
        ...     "action": "swap",
        ...     "source_token": "USDC",
        ...     "dest_token": "SOL",
        ...     "amount": 20,
        ...     "user_wallet": "7ZJh...",
        ...     "slippage_bps": 100,
        ... })
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(
            BALANCE_TOOLS + SWAP_TOOLS + SIMULATION_TOOLS
        )
    
    def build_graph(self) -> StateGraph:
        """Build transaction planning graph"""
        
        # Create graph
        graph = StateGraph(TransactionPlannerState)
        
        # Add nodes
        graph.add_node("check_balance", self._check_balance)
        graph.add_node("fetch_routes", self._fetch_routes)
        graph.add_node("rank_routes", self._rank_routes)
        graph.add_node("simulate_tx", self._simulate_transaction)
        graph.add_node("await_approval", self._await_approval)
        graph.add_node("execute_tx", self._execute_transaction)
        graph.add_node("handle_error", self._handle_error)
        
        # Set entry point
        graph.set_entry_point("check_balance")
        
        # Add conditional edges
        graph.add_conditional_edges(
            "check_balance",
            self._route_after_balance_check,
            {
                "fetch_routes": "fetch_routes",
                "error": "handle_error",
            }
        )
        
        graph.add_edge("fetch_routes", "rank_routes")
        graph.add_edge("rank_routes", "simulate_tx")
        
        graph.add_conditional_edges(
            "simulate_tx",
            self._route_after_simulation,
            {
                "await_approval": "await_approval",
                "error": "handle_error",
            }
        )
        
        graph.add_conditional_edges(
            "await_approval",
            self._route_after_approval,
            {
                "execute": "execute_tx",
                "cancel": END,
            }
        )
        
        graph.add_edge("execute_tx", END)
        graph.add_edge("handle_error", END)
        
        return graph
    
    async def _check_balance(self, state: TransactionPlannerState) -> TransactionPlannerState:
        """Check if user has sufficient balance"""
        
        try:
            wallet = state["user_wallet"]
            source_token = state["source_token"]
            amount = state.get("amount")
            percentage = state.get("percentage")
            
            # Get balance
            if source_token.upper() == "SOL":
                balance_result = await get_sol_balance.ainvoke({"wallet_address": wallet})
                balance = balance_result["balance"]
            else:
                # Get token mint address (simplified - in production, use token registry)
                balance_result = await get_token_balance.ainvoke({
                    "wallet_address": wallet,
                    "token_mint": source_token,  # Should be mint address
                })
                balance = balance_result["ui_amount"]
            
            state["balance_check"] = balance_result
            
            # Calculate required amount
            if percentage:
                required_amount = balance * (percentage / 100)
                state["amount"] = required_amount
            else:
                required_amount = amount
            
            # Check sufficiency
            state["sufficient_balance"] = balance >= required_amount
            
            if not state["sufficient_balance"]:
                state["error"] = (
                    f"Insufficient balance. Have {balance} {source_token}, "
                    f"need {required_amount} {source_token}"
                )
            
            logger.info(
                f"Balance check: {balance} {source_token}, "
                f"required: {required_amount}, "
                f"sufficient: {state['sufficient_balance']}"
            )
        
        except Exception as e:
            logger.error(f"Balance check error: {e}", exc_info=True)
            state["error"] = f"Failed to check balance: {str(e)}"
            state["sufficient_balance"] = False
        
        return state
    
    async def _fetch_routes(self, state: TransactionPlannerState) -> TransactionPlannerState:
        """Fetch available swap routes"""
        
        try:
            # Get all routes from Jupiter
            routes_result = await get_best_swap_route.ainvoke({
                "source_token": state["source_token"],
                "dest_token": state["dest_token"],
                "amount": state["amount"],
            })
            
            if routes_result["success"]:
                state["route_options"] = routes_result["all_routes"]
                logger.info(f"Found {len(state['route_options'])} routes")
            else:
                state["error"] = f"Failed to fetch routes: {routes_result.get('error')}"
                state["route_options"] = []
        
        except Exception as e:
            logger.error(f"Route fetching error: {e}", exc_info=True)
            state["error"] = f"Failed to fetch routes: {str(e)}"
            state["route_options"] = []
        
        return state
    
    async def _rank_routes(self, state: TransactionPlannerState) -> TransactionPlannerState:
        """Rank routes and select the best one"""
        
        try:
            routes = state["route_options"]
            
            if not routes:
                state["error"] = "No routes available"
                return state
            
            # Rank by output amount and price impact
            # Best route = highest output with lowest price impact
            ranked_routes = sorted(
                routes,
                key=lambda r: (
                    float(r["amount_out"]) / (1 + abs(float(r["price_impact"]))),
                    -abs(float(r["price_impact"]))
                ),
                reverse=True
            )
            
            state["selected_route"] = ranked_routes[0]
            
            logger.info(
                f"Selected best route: {state['selected_route']['route']} "
                f"(output: {state['selected_route']['amount_out']}, "
                f"impact: {state['selected_route']['price_impact']}%)"
            )
        
        except Exception as e:
            logger.error(f"Route ranking error: {e}", exc_info=True)
            state["error"] = f"Failed to rank routes: {str(e)}"
        
        return state
    
    async def _simulate_transaction(self, state: TransactionPlannerState) -> TransactionPlannerState:
        """Simulate the transaction and build swap transaction for signing"""

        try:
            simulation = await simulate_swap.ainvoke({
                "wallet_address": state["user_wallet"],
                "source_token": state["source_token"],
                "dest_token": state["dest_token"],
                "amount": state["amount"],
                "slippage_bps": state["slippage_bps"],
            })

            state["simulation_result"] = simulation
            state["simulation_success"] = simulation.get("simulation_success", False)

            # Store the swap transaction for frontend signing
            if simulation.get("swap_transaction"):
                state["metadata"]["swap_transaction"] = simulation["swap_transaction"]

            if not state["simulation_success"]:
                state["error"] = f"Simulation failed: {simulation.get('error')}"

            logger.info(f"Simulation result: {state['simulation_success']}")

        except Exception as e:
            logger.error(f"Simulation error: {e}", exc_info=True)
            state["error"] = f"Failed to simulate transaction: {str(e)}"
            state["simulation_success"] = False

        return state
    
    async def _await_approval(self, state: TransactionPlannerState) -> TransactionPlannerState:
        """Wait for user approval"""
        
        # In production, this would:
        # 1. Send transaction preview to user via WebSocket
        # 2. Wait for approval/rejection
        # 3. Update state accordingly
        
        # For now, we'll mark as requiring approval
        state["approval_required"] = True
        
        # Auto-approve for low-risk transactions (< $100)
        simulation = state["simulation_result"]
        amount_out_usd = float(simulation.get("amount_out", 0))
        
        if amount_out_usd < 100:
            state["user_approved"] = True
            state["metadata"]["auto_approved"] = True
            logger.info("Auto-approved low-risk transaction")
        else:
            # In production, wait for user input
            state["user_approved"] = False
            state["metadata"]["awaiting_user_approval"] = True
            logger.info("Awaiting user approval for high-value transaction")
        
        return state
    
    async def _execute_transaction(self, state: TransactionPlannerState) -> TransactionPlannerState:
        """Execute the transaction on-chain"""
        
        try:
            # In production, this would:
            # 1. Build the actual transaction using Jupiter
            # 2. Sign with session key or request user signature
            # 3. Submit to Solana network
            # 4. Wait for confirmation
            # 5. Log to database
            
            # For now, we'll simulate execution
            state["execution_result"] = {
                "success": True,
                "tx_signature": "mock_signature_" + state["user_wallet"][:8],
                "amount_in": state["amount"],
                "amount_out": state["simulation_result"]["amount_out"],
                "timestamp": "2025-11-29T20:00:00Z",
            }
            
            state["tx_signature"] = state["execution_result"]["tx_signature"]
            
            logger.info(f"Transaction executed: {state['tx_signature']}")
        
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            state["error"] = f"Failed to execute transaction: {str(e)}"
        
        return state
    
    async def _handle_error(self, state: TransactionPlannerState) -> TransactionPlannerState:
        """Handle errors"""
        
        logger.error(f"Transaction planning failed: {state.get('error')}")
        
        # Add error metadata
        state["metadata"]["error_handled"] = True
        state["metadata"]["error_message"] = state.get("error")
        
        return state
    
    # ============================================
    # Routing Functions
    # ============================================
    
    def _route_after_balance_check(self, state: TransactionPlannerState) -> str:
        """Route after balance check"""
        if state.get("error") or not state.get("sufficient_balance"):
            return "error"
        return "fetch_routes"
    
    def _route_after_simulation(self, state: TransactionPlannerState) -> str:
        """Route after simulation"""
        if state.get("error") or not state.get("simulation_success"):
            return "error"
        return "await_approval"
    
    def _route_after_approval(self, state: TransactionPlannerState) -> str:
        """Route after approval"""
        if state.get("user_approved"):
            return "execute"
        return "cancel"


# ============================================
# Helper Functions
# ============================================

async def plan_swap_transaction(
    user_wallet: str,
    source_token: str,
    dest_token: str,
    amount: float,
    slippage_bps: int = 100,
) -> Dict[str, Any]:
    """
    Convenience function to plan a swap transaction.

    Args:
        user_wallet: User's wallet address
        source_token: Source token symbol
        dest_token: Destination token symbol
        amount: Amount to swap
        slippage_bps: Slippage tolerance in basis points

    Returns:
        Transaction plan result with swap_transaction for frontend signing
    """
    agent = TransactionPlannerAgent()

    result = await agent.ainvoke({
        "action": "swap",
        "source_token": source_token,
        "dest_token": dest_token,
        "amount": amount,
        "slippage_bps": slippage_bps,
        "user_wallet": user_wallet,
        "messages": [],
        "error": None,
        "metadata": {},
    })

    # Extract key information for the response
    response = {
        "success": not result.get("error"),
        "error": result.get("error"),
        "source_token": source_token,
        "dest_token": dest_token,
        "amount": amount,
        "selected_route": result.get("selected_route", {}),
        "simulation_result": result.get("simulation_result", {}),
        "approval_required": result.get("approval_required", True),
        # Critical: Include swap transaction for frontend signing
        "swap_transaction": result.get("metadata", {}).get("swap_transaction"),
    }

    return response
