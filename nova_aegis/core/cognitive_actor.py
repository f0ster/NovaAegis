"""
CognitiveActor: Core entity that learns through structured reasoning.
Uses LangChain ReAct pattern for reasoning cycles.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
from datetime import datetime
import structlog

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool, BaseTool
from langchain.agents import AgentExecutor, AgentType
from langchain.agents import initialize_agent
from langchain_community.chat_message_histories import ChatMessageHistory

from ..knowledge_store import KnowledgeStore
from ..llm_interface import LLMInterface
from .tools.browser_tool import BrowserTool
from ..database import AsyncDatabaseManager

logger = structlog.get_logger()

@dataclass
class Perception:
    """What the actor perceives."""
    stimulus: Any
    context: Dict[str, Any]
    timestamp: datetime

@dataclass
class Understanding:
    """Actor's current understanding state."""
    knowledge_state: Dict[str, Any]
    certainty_levels: Dict[str, float]
    feedback_history: List[Dict[str, Any]]
    graph_refinements: List[Dict[str, Any]]

@dataclass
class Action:
    """Actor's response to perception."""
    response_type: str
    content: Any
    confidence: float
    reasoning: List[Dict[str, Any]]
    timestamp: datetime
    knowledge_snapshot: Dict[str, Any]

class CognitiveActor:
    """A conscious entity guided by structured reasoning."""
    
    def __init__(self):
        # Initialize database
        self.db = AsyncDatabaseManager()
        
        # Core capabilities
        self.knowledge = KnowledgeStore(lambda: self.db.get_async_db())
        self.communication = LLMInterface()
        
        # LangChain components
        chat_history = ChatMessageHistory()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=chat_history
        )
        
        # Tools will be initialized with service config
        self.tools: List[BaseTool] = []
        
        # Agent setup will happen after tools are configured
        self.agent = None
        self.executor = None
        
        # Processing streams
        self.perception_stream = asyncio.Queue()
        self.processing_stream = asyncio.Queue()
        self.action_stream = asyncio.Queue()
        self.feedback_stream = asyncio.Queue()
        
        # Understanding state
        self.understanding = Understanding(
            knowledge_state={},
            certainty_levels={},
            feedback_history=[],
            graph_refinements=[]
        )
        
        self.logger = logger.bind(component="actor")
    
    async def initialize_services(self, services: Dict[str, Dict[str, Any]]):
        """Initialize services from profile configuration."""
        # Initialize knowledge store
        await self.knowledge.initialize()
        
        # Initialize tools based on service config
        self.tools = []
        
        for name, config in services.items():
            if name == "browser":
                self.tools.append(BrowserTool(config.get("settings", {})))
        
        # Add default tools if none configured
        if not self.tools:
            self.tools = [
                Tool(
                    name="Search",
                    func=lambda x: "Search result for: " + x,
                    description="Search for information"
                ),
                Tool(
                    name="Analyze",
                    func=lambda x: "Analysis of: " + x,
                    description="Analyze information"
                )
            ]
                
        # Initialize agent with tools
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.communication.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True
        )
        
        self.executor = self.agent
    
    async def perceive(self, stimulus: Any, context: Optional[Dict[str, Any]] = None):
        """Perceive new input."""
        if isinstance(stimulus, dict) and stimulus.get("type") == "initialization":
            await self.initialize_services(stimulus["services"])
            return
            
        perception = Perception(
            stimulus=stimulus,
            context=context or {},
            timestamp=datetime.now()
        )
        await self.perception_stream.put(perception)
    
    async def process(self):
        """Process perceptions using ReAct pattern."""
        while True:
            perception = await self.perception_stream.get()
            
            try:
                # Get knowledge context
                current_state = await self.knowledge.get_current_state()
                
                # Run through ReAct agent
                result = await self.executor.ainvoke({
                    "input": f"Process and act on: {perception.stimulus}\n" +
                            f"Context: {perception.context}\n" +
                            f"Knowledge: {current_state}"
                })
                
                # Process results
                processed = await self._process_results(
                    perception,
                    result["output"],
                    current_state
                )
                
                await self.processing_stream.put(processed)
                
            except Exception as e:
                self.logger.error("processing_failed", error=str(e))
                await self.action_stream.put(Action(
                    response_type="error",
                    content=str(e),
                    confidence=0.0,
                    reasoning=[{"error": str(e)}],
                    knowledge_snapshot={},
                    timestamp=datetime.now()
                ))
    
    async def _process_results(
        self,
        perception: Perception,
        result: str,
        kg_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process agent results."""
        # Extract insights
        insights = []
        for line in result.split("\n"):
            if line.startswith("Thought:"):
                insights.append({
                    "type": "thought",
                    "content": line[8:].strip()
                })
            elif line.startswith("Action:"):
                insights.append({
                    "type": "action",
                    "content": line[7:].strip()
                })
                
        # Update understanding
        self.understanding.knowledge_state = await self.knowledge.get_current_state()
        
        return {
            "perception": perception,
            "result": result,
            "insights": insights,
            "kg_context": kg_context
        }
    
    async def act(self):
        """Generate actions based on processing."""
        while True:
            processed = await self.processing_stream.get()
            
            try:
                # Generate action through ReAct
                result = await self.executor.ainvoke({
                    "input": f"Determine appropriate action for:\n{processed['result']}"
                })
                
                # Parse action
                action = Action(
                    response_type=self._parse_action_type(result["output"]),
                    content=self._parse_action_content(result["output"]),
                    confidence=self._calculate_confidence(processed["insights"]),
                    reasoning=processed["insights"],
                    knowledge_snapshot=self.understanding.knowledge_state,
                    timestamp=datetime.now()
                )
                
                # Track for feedback
                self.understanding.feedback_history.append({
                    "action": action,
                    "context": processed,
                    "timestamp": datetime.now().isoformat()
                })
                
                await self.action_stream.put(action)
                
            except Exception as e:
                self.logger.error("action_failed", error=str(e))
                await self.action_stream.put(Action(
                    response_type="error",
                    content=str(e),
                    confidence=0.0,
                    reasoning=[{"error": str(e)}],
                    knowledge_snapshot={},
                    timestamp=datetime.now()
                ))
    
    def _parse_action_type(self, result: str) -> str:
        """Parse action type from ReAct result."""
        if "investigate" in result.lower():
            return "investigate"
        elif "verify" in result.lower():
            return "verify"
        elif "explore" in result.lower():
            return "explore"
        else:
            return "insight"
    
    def _parse_action_content(self, result: str) -> str:
        """Parse action content from ReAct result."""
        parts = result.split(":", 1)
        if len(parts) > 1:
            return parts[1].strip()
        return result.strip()
    
    def _calculate_confidence(self, insights: List[Dict[str, Any]]) -> float:
        """Calculate confidence from insights."""
        if not insights:
            return 0.0
            
        # Count supporting insights
        support = sum(1 for i in insights if i["type"] == "thought")
        return min(1.0, support / len(insights))
    
    async def awaken(self):
        """Start cognitive cycles."""
        asyncio.create_task(self.process())
        asyncio.create_task(self.act())
        self.logger.info("actor_awakened")
    
    async def rest(self):
        """Allow actor to rest and integrate knowledge."""
        await self.knowledge.save_state()