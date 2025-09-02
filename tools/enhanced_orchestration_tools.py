"""Enhanced Orchestration Tools with Multi-Intent Recognition and Dynamic Coordination.

This module provides advanced orchestration capabilities for handling complex,
multi-intent user requests with intelligent agent coordination.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from services.orchestration_intelligence_service import (
    orchestration_intelligence_service,
    IntentType,
    AgentType,
    ExecutionStrategy
)


class MultiIntentOrchestrationInput(BaseModel):
    """Input for multi-intent orchestration."""
    user_message: str = Field(description="User's complete message")
    user_id: str = Field(description="User ID for context")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (conversation history, user profile, etc.)"
    )
    max_intents: int = Field(
        default=3,
        description="Maximum number of intents to process simultaneously"
    )
    enable_parallel_execution: bool = Field(
        default=True,
        description="Whether to enable parallel execution of compatible intents"
    )


class MultiIntentOrchestrationTool(BaseTool):
    """Tool for handling complex multi-intent requests with intelligent coordination."""
    
    name: str = "multi_intent_orchestration"
    description: str = """
    Advanced orchestration tool for handling complex user requests with multiple intents.
    
    This tool can:
    - Recognize multiple intents in a single user message
    - Create optimal execution plans (sequential, parallel, or hybrid)
    - Coordinate between different agents dynamically
    - Synthesize responses from multiple agents into coherent output
    - Handle dependencies between different intents
    
    Use this for complex requests like:
    - "Log my 5km run and show me my progress this week"
    - "Create a workout plan and motivate me to do it"
    - "Analyze my performance and tell me what I should focus on"
    """
    args_schema: type = MultiIntentOrchestrationInput
    
    def _run(self, user_message: str, user_id: str, 
             context: Optional[Dict[str, Any]] = None,
             max_intents: int = 3, enable_parallel_execution: bool = True) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(
            user_message, user_id, context, max_intents, enable_parallel_execution
        ))
    
    async def _arun(self, user_message: str, user_id: str,
                   context: Optional[Dict[str, Any]] = None,
                   max_intents: int = 3, enable_parallel_execution: bool = True) -> str:
        """Execute multi-intent orchestration."""
        try:
            # Step 1: Analyze and recognize intents
            intents = await orchestration_intelligence_service.analyze_multi_intent(
                user_message=user_message,
                context=context
            )
            
            if not intents:
                return "I'm not sure how to help with that. Could you please rephrase your request?"
            
            # Limit number of intents processed
            intents = intents[:max_intents]
            
            # Step 2: Create execution plan
            execution_plan = await orchestration_intelligence_service.create_execution_plan(intents)
            
            # Override parallel execution if disabled
            if not enable_parallel_execution:
                execution_plan.strategy = ExecutionStrategy.SEQUENTIAL
                execution_plan.parallel_groups = []
            
            # Step 3: Execute the plan
            execution_results = await self._execute_plan(
                execution_plan, user_message, user_id, context
            )
            
            # Step 4: Synthesize responses
            orchestration_response = await orchestration_intelligence_service.synthesize_responses(
                execution_results, user_message
            )
            
            # Step 5: Format final response
            return await self._format_orchestration_response(
                orchestration_response, execution_plan
            )
            
        except Exception as e:
            return f"❌ Error processing your request: {str(e)}"
    
    async def _execute_plan(self, execution_plan, user_message: str, 
                          user_id: str, context: Optional[Dict[str, Any]]):
        """Execute the orchestration plan."""
        from services.orchestration_intelligence_service import ExecutionResult
        
        execution_results = []
        start_time = datetime.now()
        
        if execution_plan.strategy == ExecutionStrategy.SEQUENTIAL:
            # Execute intents sequentially
            for idx in execution_plan.execution_order:
                intent = execution_plan.intents[idx]
                result = await self._execute_single_intent(
                    intent, user_message, user_id, context
                )
                execution_results.append(result)
        
        elif execution_plan.strategy == ExecutionStrategy.PARALLEL:
            # Execute intents in parallel groups
            if execution_plan.parallel_groups:
                for group in execution_plan.parallel_groups:
                    # Execute group in parallel
                    tasks = []
                    for idx in group:
                        intent = execution_plan.intents[idx]
                        task = self._execute_single_intent(
                            intent, user_message, user_id, context
                        )
                        tasks.append(task)
                    
                    group_results = await asyncio.gather(*tasks)
                    execution_results.extend(group_results)
            else:
                # Execute all intents in parallel
                tasks = []
                for intent in execution_plan.intents:
                    task = self._execute_single_intent(
                        intent, user_message, user_id, context
                    )
                    tasks.append(task)
                
                execution_results = await asyncio.gather(*tasks)
        
        else:
            # Fallback to sequential
            for intent in execution_plan.intents:
                result = await self._execute_single_intent(
                    intent, user_message, user_id, context
                )
                execution_results.append(result)
        
        return execution_results
    
    async def _execute_single_intent(self, intent, user_message: str,
                                   user_id: str, context: Optional[Dict[str, Any]]):
        """Execute a single intent using the appropriate agent/tool."""
        from services.orchestration_intelligence_service import ExecutionResult
        
        start_time = datetime.now()
        
        try:
            # Determine which tool/agent to use
            if intent.type == IntentType.ACTIVITY_LOGGING:
                result = await self._execute_logger_intent(intent, user_message, user_id)
            elif intent.type in [IntentType.WORKOUT_PLANNING, IntentType.PERFORMANCE_ANALYSIS,
                               IntentType.BEHAVIORAL_ANALYSIS, IntentType.MOTIVATION_SEEKING,
                               IntentType.HABIT_FORMATION]:
                result = await self._execute_coach_intent(intent, user_message, user_id)
            elif intent.type == IntentType.PROGRESS_INQUIRY:
                result = await self._execute_progress_intent(intent, user_message, user_id)
            else:
                # Default orchestration response
                result = await self._execute_orchestration_intent(intent, user_message, user_id)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ExecutionResult(
                intent_type=intent.type,
                success=True,
                response=result,
                agent_used=intent.agent_preference or AgentType.ORCHESTRATION,
                execution_time=execution_time,
                confidence=intent.confidence,
                metadata={"parameters": intent.parameters}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ExecutionResult(
                intent_type=intent.type,
                success=False,
                response=f"Error executing {intent.type.value}: {str(e)}",
                agent_used=AgentType.ORCHESTRATION,
                execution_time=execution_time,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _execute_logger_intent(self, intent, user_message: str, user_id: str) -> str:
        """Execute logger-related intents."""
        # Import logger tools
        try:
            from tools.enhanced_logger_tools import smart_activity_log_tool
            
            # Use smart activity log tool
            result = await smart_activity_log_tool._arun(
                user_id=user_id,
                activity_description=intent.parameters.get("activity_description", user_message)
            )
            
            return result
            
        except Exception as e:
            return f"Error logging activity: {str(e)}"
    
    async def _execute_coach_intent(self, intent, user_message: str, user_id: str) -> str:
        """Execute coach-related intents."""
        try:
            if intent.type == IntentType.WORKOUT_PLANNING:
                from tools.enhanced_coach_tools import adaptive_workout_tool
                
                result = await adaptive_workout_tool._arun(
                    user_id=user_id,
                    duration_minutes=intent.parameters.get("duration", 30),
                    fitness_goal=intent.parameters.get("goals", ["general_fitness"])[0],
                    available_equipment=intent.parameters.get("equipment", [])
                )
                
                return result
            
            elif intent.type == IntentType.PERFORMANCE_ANALYSIS:
                from tools.enhanced_coach_tools import performance_analysis_tool
                
                result = await performance_analysis_tool._arun(
                    user_id=user_id,
                    analysis_period="monthly"
                )
                
                return result
            
            elif intent.type == IntentType.BEHAVIORAL_ANALYSIS:
                from tools.enhanced_coach_tools import behavioral_analysis_tool
                
                result = await behavioral_analysis_tool._arun(
                    user_id=user_id,
                    include_interventions=True
                )
                
                return result
            
            elif intent.type == IntentType.MOTIVATION_SEEKING:
                from tools.enhanced_coach_tools import motivational_message_tool
                
                result = await motivational_message_tool._arun(
                    user_id=user_id,
                    context=intent.parameters.get("context", "general")
                )
                
                return result
            
            elif intent.type == IntentType.HABIT_FORMATION:
                from tools.enhanced_coach_tools import habit_formation_tool
                
                result = await habit_formation_tool._arun(
                    user_id=user_id,
                    target_habit=intent.parameters.get("target_behavior", "exercise regularly")
                )
                
                return result
            
            else:
                return f"Coach intent {intent.type.value} not yet implemented"
                
        except Exception as e:
            return f"Error with coaching request: {str(e)}"
    
    async def _execute_progress_intent(self, intent, user_message: str, user_id: str) -> str:
        """Execute progress inquiry intents."""
        try:
            from tools.enhanced_logger_tools import progress_analytics_tool
            
            result = await progress_analytics_tool._arun(
                user_id=user_id,
                analysis_type="comprehensive",
                time_period="monthly"
            )
            
            return result
            
        except Exception as e:
            return f"Error retrieving progress: {str(e)}"
    
    async def _execute_orchestration_intent(self, intent, user_message: str, user_id: str) -> str:
        """Execute orchestration-level intents."""
        if intent.type == IntentType.CASUAL_CHAT:
            greetings = [
                "Hello! I'm Pili, your fitness companion. How can I help you today?",
                "Hi there! Ready to crush your fitness goals?",
                "Hey! Great to see you. What would you like to work on today?",
                "Hello! I'm here to help with all your fitness needs."
            ]
            
            import random
            return random.choice(greetings)
        
        elif intent.type == IntentType.GENERAL_FITNESS:
            return ("I'm here to help with all aspects of your fitness journey! "
                   "I can help you log activities, create workout plans, analyze your progress, "
                   "provide motivation, and much more. What would you like to focus on?")
        
        else:
            return f"I understand you're asking about {intent.type.value.replace('_', ' ')}, but I need more specific information to help you effectively."
    
    async def _format_orchestration_response(self, orchestration_response, execution_plan) -> str:
        """Format the final orchestration response."""
        response_parts = [orchestration_response.primary_response]
        
        # Add execution metadata if complex request
        if orchestration_response.intents_processed > 1:
            response_parts.append("")
            response_parts.append(f"📊 **Execution Summary:**")
            response_parts.append(f"  • Processed {orchestration_response.intents_processed} intents")
            response_parts.append(f"  • Strategy: {orchestration_response.strategy_used.value.title()}")
            response_parts.append(f"  • Total time: {orchestration_response.total_execution_time:.1f}s")
            response_parts.append(f"  • Confidence: {orchestration_response.synthesis_confidence:.0%}")
            
            if execution_plan.complexity_score > 2.0:
                response_parts.append(f"  • Complexity: High ({execution_plan.complexity_score:.1f})")
        
        return "\n".join(response_parts)


# Create tool instance
multi_intent_orchestration_tool = MultiIntentOrchestrationTool()
