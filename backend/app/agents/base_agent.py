"""
Schumacher - Base Agent Class
Foundation for all LangGraph agents with common functionality
"""

import logging
from typing import Any, Dict, List, Optional, TypedDict
from abc import ABC, abstractmethod

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================
# Base State Definition
# ============================================

class BaseAgentState(TypedDict):
    """Base state for all agents"""
    messages: List[BaseMessage]
    user_wallet: str
    error: Optional[str]
    metadata: Dict[str, Any]


# ============================================
# Base Agent Class
# ============================================

class BaseAgent(ABC):
    """
    Base class for all LangGraph agents.
    
    Provides common functionality:
    - LLM initialization
    - State management
    - Error handling
    - Logging
    - Graph compilation
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_openai: bool = False,
    ):
        """
        Initialize base agent.
        
        Args:
            model_name: LLM model name (defaults from settings)
            temperature: LLM temperature
            max_tokens: Maximum tokens
            use_openai: Use OpenAI instead of Anthropic
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_openai = use_openai
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize graph
        self.graph = None
        self.compiled_graph = None
        
        # Memory saver for checkpointing
        self.memory = MemorySaver()
        
        logger.info(f"Initialized {self.__class__.__name__}")
    
    def _initialize_llm(self):
        """Initialize LLM based on configuration"""
        if self.use_openai or not settings.ANTHROPIC_API_KEY:
            # Use OpenAI
            return ChatOpenAI(
                model=self.model_name or settings.OPENAI_MODEL,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=settings.OPENAI_API_KEY,
            )
        else:
            # Use Anthropic (Claude)
            return ChatAnthropic(
                model=self.model_name or settings.ANTHROPIC_MODEL,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
            )
    
    @abstractmethod
    def build_graph(self) -> StateGraph:
        """
        Build the agent's graph.
        Must be implemented by subclasses.
        
        Returns:
            StateGraph instance
        """
        pass
    
    def compile(self):
        """Compile the graph for execution"""
        if self.graph is None:
            self.graph = self.build_graph()
        
        self.compiled_graph = self.graph.compile(
            checkpointer=self.memory
        )
        
        logger.info(f"{self.__class__.__name__} graph compiled")
        return self.compiled_graph
    
    async def ainvoke(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Async invoke the agent.
        
        Args:
            state: Initial state
            config: Optional configuration
        
        Returns:
            Final state after execution
        """
        if self.compiled_graph is None:
            self.compile()
        
        try:
            result = await self.compiled_graph.ainvoke(state, config)
            return result
        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            return {
                **state,
                "error": str(e),
            }
    
    def invoke(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Sync invoke the agent.
        
        Args:
            state: Initial state
            config: Optional configuration
        
        Returns:
            Final state after execution
        """
        if self.compiled_graph is None:
            self.compile()
        
        try:
            result = self.compiled_graph.invoke(state, config)
            return result
        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            return {
                **state,
                "error": str(e),
            }
    
    async def astream(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream agent execution (for real-time updates).
        
        Args:
            state: Initial state
            config: Optional configuration
        
        Yields:
            State updates during execution
        """
        if self.compiled_graph is None:
            self.compile()
        
        async for chunk in self.compiled_graph.astream(state, config):
            yield chunk
    
    def get_graph_visualization(self) -> str:
        """
        Get Mermaid diagram of the graph.
        Useful for debugging and documentation.
        
        Returns:
            Mermaid diagram string
        """
        if self.compiled_graph is None:
            self.compile()
        
        try:
            return self.compiled_graph.get_graph().draw_mermaid()
        except Exception as e:
            logger.error(f"Failed to generate graph visualization: {e}")
            return ""
    
    def _create_system_message(self, content: str) -> SystemMessage:
        """Create system message"""
        return SystemMessage(content=content)
    
    def _create_human_message(self, content: str) -> HumanMessage:
        """Create human message"""
        return HumanMessage(content=content)
    
    def _create_ai_message(self, content: str) -> AIMessage:
        """Create AI message"""
        return AIMessage(content=content)
    
    def _log_state(self, state: Dict[str, Any], step: str):
        """Log current state for debugging"""
        logger.debug(f"[{self.__class__.__name__}] {step}: {state}")


# ============================================
# Helper Functions
# ============================================

def create_agent_config(
    thread_id: str,
    user_wallet: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Create configuration for agent execution.
    
    Args:
        thread_id: Unique thread ID for conversation
        user_wallet: User's wallet address
        **kwargs: Additional config options
    
    Returns:
        Configuration dictionary
    """
    return {
        "configurable": {
            "thread_id": thread_id,
            "user_wallet": user_wallet,
            **kwargs,
        }
    }


def format_agent_response(
    state: Dict[str, Any],
    success: bool = True,
) -> Dict[str, Any]:
    """
    Format agent response for API.
    
    Args:
        state: Final agent state
        success: Whether execution was successful
    
    Returns:
        Formatted response
    """
    return {
        "success": success and not state.get("error"),
        "error": state.get("error"),
        "result": state.get("result"),
        "metadata": state.get("metadata", {}),
    }
