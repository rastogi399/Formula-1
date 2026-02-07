"""
Solana Copilot - Intent Classifier Agent
Classifies user intent from natural language input
"""

import json
import logging
from typing import Any, Dict, List, TypedDict, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from app.agents.base_agent import BaseAgent, BaseAgentState

logger = logging.getLogger(__name__)


# ============================================
# State Definition
# ============================================

class IntentState(BaseAgentState):
    """State for intent classification"""
    user_input: str
    classified_intent: Dict[str, Any]
    confidence: float
    action: str  # swap, send, stake, analyze, create_automation, etc.
    parameters: Dict[str, Any]


# ============================================
# Intent Classifier Agent
# ============================================

class IntentClassifierAgent(BaseAgent):
    """
    Classifies user intent from natural language.
    
    Supported intents:
    - swap: Token swaps
    - send: Token transfers
    - stake: Staking operations
    - analyze: Portfolio analysis
    - create_automation: DCA, recurring swaps
    - query: General queries
    
    Example:
        >>> agent = IntentClassifierAgent()
        >>> result = await agent.ainvoke({
        ...     "user_input": "Swap 20 USDC to SOL",
        ...     "user_wallet": "7ZJh..."
        ... })
        >>> print(result["action"])  # "swap"
        >>> print(result["parameters"])  # {"source_token": "USDC", ...}
    """
    
    SYSTEM_PROMPT = """You are an expert intent classifier for a Solana wallet AI assistant.

Your job is to analyze user messages and classify their intent with high accuracy.

Supported Actions:
1. **swap**: User wants to exchange one token for another
   - Examples: "swap 20 USDC to SOL", "exchange my ORCA for USDC", "sell 50% of my SOL"
   
2. **send**: User wants to transfer tokens to another wallet
   - Examples: "send 5 SOL to Alice.sol", "transfer 100 USDC to 7ZJh..."
   
3. **stake**: User wants to stake tokens
   - Examples: "stake 10 SOL", "unstake my MSOL", "delegate to validator X"
   
4. **analyze**: User wants portfolio analysis or risk assessment
   - Examples: "analyze my portfolio", "what's my risk score", "show my PnL"
   
5. **create_automation**: User wants to set up DCA or recurring swaps
   - Examples: "create a $100 daily DCA", "set up weekly SOL purchase", "automate USDC to SOL swap"
   
6. **query**: General questions about balances, prices, etc.
   - Examples: "what's my SOL balance", "current price of ORCA", "show my transactions"

Extract Parameters:
- For swaps: source_token, dest_token, amount, percentage
- For sends: dest_wallet, token, amount
- For stakes: token, amount, validator (optional)
- For automations: type (dca/recurring), amount, frequency, source_token, dest_token

Return JSON with:
{
  "action": "swap|send|stake|analyze|create_automation|query",
  "confidence": 0.0-1.0,
  "parameters": {...},
  "reasoning": "brief explanation"
}

Be precise and extract all relevant parameters."""

    def build_graph(self) -> StateGraph:
        """Build intent classification graph"""
        
        # Create graph
        graph = StateGraph(IntentState)
        
        # Add nodes
        graph.add_node("classify", self._classify_intent)
        graph.add_node("validate", self._validate_classification)
        
        # Add edges
        graph.set_entry_point("classify")
        graph.add_edge("classify", "validate")
        graph.add_edge("validate", END)
        
        return graph
    
    async def _classify_intent(self, state: IntentState) -> IntentState:
        """Classify user intent using LLM"""
        
        try:
            # Create prompt
            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=f"User message: {state['user_input']}")
            ]
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            try:
                result = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("Failed to parse LLM response as JSON")
            
            # Update state
            state["classified_intent"] = result
            state["action"] = result.get("action", "query")
            state["confidence"] = result.get("confidence", 0.0)
            state["parameters"] = result.get("parameters", {})
            state["metadata"]["reasoning"] = result.get("reasoning", "")
            
            logger.info(f"Classified intent: {state['action']} (confidence: {state['confidence']})")
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}", exc_info=True)
            state["error"] = f"Failed to classify intent: {str(e)}"
            state["action"] = "query"
            state["confidence"] = 0.0
        
        return state
    
    async def _validate_classification(self, state: IntentState) -> IntentState:
        """Validate and normalize classification"""
        
        # Check confidence threshold
        if state["confidence"] < 0.7:
            logger.warning(f"Low confidence classification: {state['confidence']}")
            state["metadata"]["low_confidence"] = True
        
        # Normalize action
        valid_actions = ["swap", "send", "stake", "analyze", "create_automation", "query"]
        if state["action"] not in valid_actions:
            logger.warning(f"Invalid action: {state['action']}, defaulting to 'query'")
            state["action"] = "query"
        
        # Normalize parameters
        state["parameters"] = self._normalize_parameters(
            state["action"],
            state["parameters"]
        )
        
        return state
    
    def _normalize_parameters(
        self,
        action: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Normalize and validate parameters based on action"""
        
        normalized = {}
        
        if action == "swap":
            normalized["source_token"] = parameters.get("source_token", "").upper()
            normalized["dest_token"] = parameters.get("dest_token", "").upper()
            normalized["amount"] = parameters.get("amount")
            normalized["percentage"] = parameters.get("percentage")
            normalized["slippage_bps"] = parameters.get("slippage_bps", 100)  # 1% default
        
        elif action == "send":
            normalized["dest_wallet"] = parameters.get("dest_wallet", "")
            normalized["token"] = parameters.get("token", "SOL").upper()
            normalized["amount"] = parameters.get("amount")
        
        elif action == "stake":
            normalized["token"] = parameters.get("token", "SOL").upper()
            normalized["amount"] = parameters.get("amount")
            normalized["validator"] = parameters.get("validator")
        
        elif action == "create_automation":
            normalized["automation_type"] = parameters.get("type", "dca")
            normalized["source_token"] = parameters.get("source_token", "").upper()
            normalized["dest_token"] = parameters.get("dest_token", "").upper()
            normalized["amount"] = parameters.get("amount")
            normalized["frequency"] = parameters.get("frequency", "daily")
        
        elif action == "analyze":
            normalized["analysis_type"] = parameters.get("type", "portfolio")
            normalized["timeframe"] = parameters.get("timeframe", "30d")
        
        elif action == "query":
            normalized["query_type"] = parameters.get("type", "general")
            normalized["token"] = parameters.get("token", "").upper() if parameters.get("token") else None
        
        return normalized


# ============================================
# Helper Functions
# ============================================

async def classify_intent(
    user_input: str,
    user_wallet: str,
) -> Dict[str, Any]:
    """
    Convenience function to classify intent.
    
    Args:
        user_input: User's message
        user_wallet: User's wallet address
    
    Returns:
        Classification result
    """
    agent = IntentClassifierAgent()
    
    result = await agent.ainvoke({
        "user_input": user_input,
        "user_wallet": user_wallet,
        "messages": [],
        "error": None,
        "metadata": {},
    })
    
    return {
        "action": result["action"],
        "confidence": result["confidence"],
        "parameters": result["parameters"],
        "reasoning": result["metadata"].get("reasoning", ""),
    }
