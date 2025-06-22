from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from services.llm_service import llm_service
from .logger_agent import logger_agent
from .coach_agent import coach_agent
import json
import asyncio
from datetime import datetime


# Using dictionary state instead of custom class for LangGraph compatibility


async def analyze_task(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze user request and break it down into manageable subtasks using chain of thought."""
    
    # Chain of thought prompt for task analysis
    cot_prompt = f"""You are an orchestration agent that coordinates specialized fitness agents with dynamic MCP tool capabilities.

CHAIN OF THINKING PROCESS:
1. First, analyze what the user is asking for
2. Determine if this is a simple or complex task
3. If complex, break it down into subtasks
4. Decide which specialized agents are needed
5. Plan the execution order

Available specialized agents:
- Logger Agent: Has dynamic access to MCP tools for logging activities, managing clubs, retrieving fitness data
- Coach Agent: Has dynamic access to MCP tools for analyzing progress, creating plans, providing coaching advice

Both agents now use LLM-based tool selection from available MCP server tools rather than predefined intents.

User message: "{state['message']}"
Conversation history: {state['conversation_history'][-5:] if state['conversation_history'] else "None"}

Think step by step and provide your analysis in JSON format:
{{
    "thinking_steps": [
        "Step 1: Understanding the request...",
        "Step 2: Complexity assessment...",
        "Step 3: Task breakdown...",
        "Step 4: Agent selection based on capabilities...",
        "Step 5: Execution planning..."
    ],
    "task_complexity": "simple" | "complex",
    "main_intent": "fitness_tracking" | "coaching_advice" | "data_analysis" | "general_help" | "unknown",
    "subtasks": [
        {{"id": 1, "description": "Handle fitness data operations", "agent": "logger", "priority": 1}},
        {{"id": 2, "description": "Provide coaching guidance", "agent": "coach", "priority": 2}}
    ],
    "execution_order": ["logger", "coach"] | ["coach"] | ["logger"] | ["logger", "coach"],
    "requires_coordination": true | false
}}"""

    try:
        # Get task analysis using LLM
        analysis_response = await llm_service.generate_response(
            "analyze_task", 
            state['message'], 
            cot_prompt,
            conversation_history=state['conversation_history']
        )
        
        # Parse the analysis
        try:
            analysis = json.loads(analysis_response)
            # Return updates including preserving essential state
            return {
                "user_id": state.get("user_id"),  # Preserve user_id
                "message": state.get("message"),  # Preserve message
                "conversation_history": state.get("conversation_history"),  # Preserve conversation
                "task_analysis": analysis,
                "chain_of_thought": analysis.get("thinking_steps", []),
                "subtasks": analysis.get("subtasks", []),
                "execution_plan": {
                    "order": analysis.get("execution_order", []),
                    "complexity": analysis.get("task_complexity", "simple"),
                    "main_intent": analysis.get("main_intent", "unknown"),
                    "requires_coordination": analysis.get("requires_coordination", False)
                }
            }
        except json.JSONDecodeError:
            # Fallback to simple analysis
            return {
                "user_id": state.get("user_id"),  # Preserve user_id
                "message": state.get("message"),  # Preserve message
                "conversation_history": state.get("conversation_history"),  # Preserve conversation
                "task_analysis": {"error": "Failed to parse LLM analysis"},
                "chain_of_thought": ["Analyzing user request...", "Determining appropriate response..."],
                "execution_plan": {"order": ["logger"], "complexity": "simple", "main_intent": "general_help"}
            }
            
    except Exception as e:
        print(f"Error in task analysis: {e}")
        # Fallback analysis
        return {
            "user_id": state.get("user_id"),  # Preserve user_id
            "message": state.get("message"),  # Preserve message
            "conversation_history": state.get("conversation_history"),  # Preserve conversation
            "chain_of_thought": ["Fallback analysis - determining best agent to handle request"],
            "execution_plan": {"order": ["logger"], "complexity": "simple", "main_intent": "general_help"}
        }


async def execute_subtasks(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execute subtasks using appropriate agents based on the execution plan."""
    
    # Safely get required state values
    user_id = state.get("user_id", "")
    message = state.get("message", "")
    
    if not user_id or not message:
        print(f"Warning: Missing required state values - user_id: {user_id}, message: {message}")
        print(f"Available state keys: {list(state.keys())}")
        return {
            "chain_of_thought": ["Error: Missing user_id or message in state"],
            "agent_results": {"error": "Missing required state values"}
        }
    
    chain_of_thought = state.get("chain_of_thought", []).copy()
    chain_of_thought.append("Executing planned subtasks...")
    
    execution_order = state.get("execution_plan", {}).get("order", ["logger"])
    agent_results = {}
    
    for agent_name in execution_order:
        chain_of_thought.append(f"Calling {agent_name} agent...")
        
        if agent_name == "logger":
            # Call logger agent
            logger_result = await logger_agent.handle_request(user_id, message)
            agent_results["logger"] = logger_result
            
        elif agent_name == "coach":
            # Call coach agent
            coach_result = await coach_agent.handle_request(user_id, message, agent_results.get("logger"))
            agent_results["coach"] = coach_result
    
    chain_of_thought.append("All subtasks completed, synthesizing response...")
    
    return {
        "user_id": user_id,  # Preserve user_id
        "message": message,  # Preserve message  
        "conversation_history": state.get("conversation_history"),  # Preserve conversation
        "chain_of_thought": chain_of_thought,
        "agent_results": agent_results
    }


async def synthesize_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize final response from agent results using chain of thought."""
    
    # Safely get message
    message = state.get('message', '')
    
    synthesis_prompt = f"""You are Pili, an enthusiastic fitness chatbot. 

CHAIN OF THINKING:
Your thinking process: {state.get('chain_of_thought', [])}

AGENT RESULTS:
{json.dumps(state.get('agent_results', {}), indent=2)}

USER REQUEST: "{message}"

Using the chain of thought process and agent results, provide a natural, coherent response that:
1. Addresses the user's request completely
2. Integrates information from multiple agents when applicable
3. Maintains Pili's encouraging and friendly personality
4. Uses fitness emojis appropriately

Your response should be conversational and engaging, not robotic. If multiple agents provided information, weave it together naturally.

Final response:"""

    try:
        final_response = await llm_service.generate_response(
            "synthesize_response",
            message,
            synthesis_prompt,
            conversation_history=state.get('conversation_history', [])
        )
        
    except Exception as e:
        print(f"Error in response synthesis: {e}")
        # Fallback: use the first available agent result
        agent_results = state.get('agent_results', {})
        if agent_results:
            final_response = next(iter(agent_results.values()))
        else:
            final_response = "I'm sorry, I couldn't process your request right now. Please try again!"
    
    # Prepare logs
    logs = [{
        "chain_of_thought": state.get('chain_of_thought', []),
        "task_analysis": state.get('task_analysis', {}),
        "execution_plan": state.get('execution_plan', {}),
        "agent_results": state.get('agent_results', {}),
        "orchestration_agent": "active"
    }]
    
    return {
        "user_id": state.get("user_id"),  # Preserve user_id
        "message": message,  # Preserve message
        "conversation_history": state.get("conversation_history"),  # Preserve conversation
        "final_response": final_response,
        "logs": logs
    }


def create_orchestration_agent():
    """Create the orchestration agent workflow."""
    
    workflow = StateGraph(dict)
    
    # Add nodes
    workflow.add_node("analyze_task", analyze_task)
    workflow.add_node("execute_subtasks", execute_subtasks)
    workflow.add_node("synthesize_response", synthesize_response)
    
    # Add edges
    workflow.set_entry_point("analyze_task")
    workflow.add_edge("analyze_task", "execute_subtasks")
    workflow.add_edge("execute_subtasks", "synthesize_response")
    workflow.add_edge("synthesize_response", END)
    
    return workflow.compile()


class SimpleMemory:
    """Simple conversation memory without external dependencies."""
    
    def __init__(self):
        self.messages = []
        self.max_messages = 20  # Keep last 20 messages
    
    def add_user_message(self, message: str):
        """Add user message to memory."""
        self.messages.append({
            "type": "human",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_messages()
    
    def add_ai_message(self, message: str):
        """Add AI message to memory."""
        self.messages.append({
            "type": "ai", 
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_messages()
    
    def _trim_messages(self):
        """Keep only the last max_messages."""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get recent messages for context."""
        return self.messages[-count:] if count > 0 else self.messages


class OrchestrationAgent:
    """Main orchestration agent that coordinates other agents."""
    
    def __init__(self):
        self.workflow = create_orchestration_agent()
        self.user_memories = {}
    
    def get_or_create_memory(self, user_id: str) -> SimpleMemory:
        """Get or create conversation memory for a specific user."""
        if user_id not in self.user_memories:
            self.user_memories[user_id] = SimpleMemory()
        return self.user_memories[user_id]
    
    async def process_request(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process user request using orchestration workflow."""
        
        # Get conversation history
        memory = self.get_or_create_memory(user_id)
        conversation_history = memory.get_recent_messages(10)
        
        # Initialize state as dictionary
        initial_state = {
            "user_id": user_id,
            "message": message,
            "conversation_history": conversation_history,
            "task_analysis": {},
            "subtasks": [],
            "execution_plan": {},
            "agent_results": {},
            "chain_of_thought": [],
            "final_response": "",
            "logs": []
        }
        
        # Run workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        # Save conversation to memory
        memory.add_user_message(message)
        memory.add_ai_message(final_state["final_response"])
        
        return {
            "response": final_state["final_response"],
            "logs": final_state["logs"],
            "chain_of_thought": final_state.get("chain_of_thought", [])
        }


# Create global instance
orchestration_agent = OrchestrationAgent() 