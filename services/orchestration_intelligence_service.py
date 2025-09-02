"""Orchestration Intelligence Service for Multi-Intent Recognition and Dynamic Coordination.

This service provides advanced orchestration capabilities including:
- Multi-intent recognition and parsing
- Dynamic agent coordination and parallel execution
- Context-aware request routing
- Response synthesis and aggregation
- Intelligent workflow management
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import json

from config.settings import get_configuration


class IntentType(Enum):
    """Types of user intents that can be recognized."""
    ACTIVITY_LOGGING = "activity_logging"
    PROGRESS_INQUIRY = "progress_inquiry"
    WORKOUT_PLANNING = "workout_planning"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    MOTIVATION_SEEKING = "motivation_seeking"
    HABIT_FORMATION = "habit_formation"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    GENERAL_FITNESS = "general_fitness"
    GOAL_SETTING = "goal_setting"
    CASUAL_CHAT = "casual_chat"


class AgentType(Enum):
    """Types of agents available for task execution."""
    LOGGER = "logger_agent"
    COACH = "coach_agent"
    ORCHESTRATION = "orchestration_agent"


class ExecutionStrategy(Enum):
    """Strategies for executing multi-intent requests."""
    SEQUENTIAL = "sequential"  # Execute intents one after another
    PARALLEL = "parallel"     # Execute intents simultaneously
    CONDITIONAL = "conditional"  # Execute based on conditions
    HYBRID = "hybrid"         # Mix of sequential and parallel


@dataclass
class Intent:
    """Represents a single user intent."""
    type: IntentType
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1 = highest priority
    dependencies: List[str] = field(default_factory=list)  # Other intents this depends on
    agent_preference: Optional[AgentType] = None


@dataclass
class ExecutionPlan:
    """Plan for executing multiple intents."""
    intents: List[Intent]
    strategy: ExecutionStrategy
    execution_order: List[int]  # Indices of intents in execution order
    parallel_groups: List[List[int]] = field(default_factory=list)  # Groups that can run in parallel
    estimated_duration: float = 0.0
    complexity_score: float = 0.0


@dataclass
class ExecutionResult:
    """Result of executing an intent or plan."""
    intent_type: IntentType
    success: bool
    response: str
    agent_used: AgentType
    execution_time: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResponse:
    """Complete orchestration response with synthesis."""
    primary_response: str
    execution_results: List[ExecutionResult]
    synthesis_confidence: float
    total_execution_time: float
    intents_processed: int
    strategy_used: ExecutionStrategy


class OrchestrationIntelligenceService:
    """Advanced service for intelligent orchestration and multi-intent handling."""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.execution_strategies = self._load_execution_strategies()
        self.agent_capabilities = self._load_agent_capabilities()
        self.synthesis_rules = self._load_synthesis_rules()
        
    def _load_intent_patterns(self) -> Dict[IntentType, List[Dict[str, Any]]]:
        """Load patterns for recognizing different intents."""
        return {
            IntentType.ACTIVITY_LOGGING: [
                {
                    "patterns": [
                        r"\b(ran|run|jogged|cycled|swam|lifted|did|completed|finished)\b.*\b(today|yesterday|this morning|last night)\b",
                        r"\b(workout|exercise|activity|training)\b.*\b(log|record|track)\b",
                        r"\d+\s*(km|miles|minutes|hours|reps|sets)",
                        r"\b(just|finished|completed|did)\b.*\b(workout|run|gym|exercise)\b"
                    ],
                    "confidence_boost": 0.2,
                    "required_params": ["activity_description"],
                    "agent_preference": AgentType.LOGGER
                }
            ],
            IntentType.PROGRESS_INQUIRY: [
                {
                    "patterns": [
                        r"\b(how am i doing|progress|improvement|better|worse)\b",
                        r"\b(show me|tell me about|what about)\s+.*\b(progress|performance|stats)\b",
                        r"\b(compare|comparison|trend|trending)\b",
                        r"\b(stats|statistics|numbers|data|results)\b"
                    ],
                    "confidence_boost": 0.25,
                    "required_params": [],
                    "agent_preference": AgentType.LOGGER
                }
            ],
            IntentType.WORKOUT_PLANNING: [
                {
                    "patterns": [
                        r"\b(plan|schedule|routine|program)\b.*\b(workout|exercise)\b",
                        r"\b(create|make|design|generate)\b.*\b(workout|plan|routine)\b",
                        r"\b(what should i|recommend|suggest)\b.*\b(workout|exercise)\b",
                        r"\b(next workout|tomorrow|this week)\b"
                    ],
                    "confidence_boost": 0.3,
                    "required_params": ["duration", "goals"],
                    "agent_preference": AgentType.COACH
                }
            ],
            IntentType.PERFORMANCE_ANALYSIS: [
                {
                    "patterns": [
                        r"\b(analyze|analysis|insights|trends)\b.*\b(performance|progress)\b",
                        r"\b(detailed|comprehensive|deep)\b.*\b(analysis|report)\b",
                        r"\b(strengths|weaknesses|improvement)\b",
                        r"\b(benchmar|compar).*\b(peers|others|average)\b"
                    ],
                    "confidence_boost": 0.25,
                    "required_params": [],
                    "agent_preference": AgentType.COACH
                }
            ],
            IntentType.MOTIVATION_SEEKING: [
                {
                    "patterns": [
                        r"\b(motivation|motivate|encourage|support)\b",
                        r"\b(tired|exhausted|don't want to|not feeling|unmotivated)\b",
                        r"\b(give up|quit|stop|struggling)\b",
                        r"\b(inspire|inspiration|push|drive|boost)\b"
                    ],
                    "confidence_boost": 0.2,
                    "required_params": ["context"],
                    "agent_preference": AgentType.COACH
                }
            ],
            IntentType.HABIT_FORMATION: [
                {
                    "patterns": [
                        r"\b(habit|routine|consistency|regularly)\b",
                        r"\b(build|form|create|establish)\b.*\b(habit|routine)\b",
                        r"\b(stick to|maintain|keep up)\b.*\b(routine|schedule)\b",
                        r"\b(make it a habit|turn into routine)\b"
                    ],
                    "confidence_boost": 0.25,
                    "required_params": ["target_behavior"],
                    "agent_preference": AgentType.COACH
                }
            ],
            IntentType.BEHAVIORAL_ANALYSIS: [
                {
                    "patterns": [
                        r"\b(why do i|what's wrong|psychology|behavior)\b",
                        r"\b(personality|type|style|approach)\b.*\b(fitness|exercise)\b",
                        r"\b(motivation|mindset|mental|psychological)\b",
                        r"\b(struggle with|difficulty|challenge|barrier)\b"
                    ],
                    "confidence_boost": 0.2,
                    "required_params": [],
                    "agent_preference": AgentType.COACH
                }
            ],
            IntentType.CASUAL_CHAT: [
                {
                    "patterns": [
                        r"\b(hi|hello|hey|good morning|good evening)\b",
                        r"\b(thank|thanks|appreciate)\b",
                        r"\b(how are you|what's up|how's it going)\b",
                        r"\b(great|awesome|cool|nice|good)\b$"
                    ],
                    "confidence_boost": 0.1,
                    "required_params": [],
                    "agent_preference": AgentType.ORCHESTRATION
                }
            ]
        }
    
    def _load_execution_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load strategies for executing different intent combinations."""
        return {
            "single_intent": {
                "strategy": ExecutionStrategy.SEQUENTIAL,
                "description": "Single intent execution",
                "complexity": 1.0
            },
            "logging_and_analysis": {
                "strategy": ExecutionStrategy.SEQUENTIAL,
                "description": "Log activity first, then analyze",
                "complexity": 2.0,
                "dependencies": ["activity_logging", "progress_inquiry"]
            },
            "planning_and_motivation": {
                "strategy": ExecutionStrategy.PARALLEL,
                "description": "Generate workout and motivation simultaneously",
                "complexity": 2.5,
                "parallel_groups": [["workout_planning", "motivation_seeking"]]
            },
            "comprehensive_analysis": {
                "strategy": ExecutionStrategy.HYBRID,
                "description": "Complex multi-step analysis with dependencies",
                "complexity": 3.5,
                "sequential_first": ["progress_inquiry"],
                "then_parallel": [["performance_analysis", "behavioral_analysis"]]
            }
        }
    
    def _load_agent_capabilities(self) -> Dict[AgentType, Dict[str, Any]]:
        """Load capabilities and specializations of each agent."""
        return {
            AgentType.LOGGER: {
                "primary_intents": [
                    IntentType.ACTIVITY_LOGGING,
                    IntentType.PROGRESS_INQUIRY
                ],
                "secondary_intents": [],
                "average_response_time": 2.0,
                "parallel_capable": True,
                "tools": [
                    "smart_activity_log",
                    "activity_validation",
                    "progress_analytics"
                ]
            },
            AgentType.COACH: {
                "primary_intents": [
                    IntentType.WORKOUT_PLANNING,
                    IntentType.PERFORMANCE_ANALYSIS,
                    IntentType.MOTIVATION_SEEKING,
                    IntentType.HABIT_FORMATION,
                    IntentType.BEHAVIORAL_ANALYSIS
                ],
                "secondary_intents": [
                    IntentType.GENERAL_FITNESS
                ],
                "average_response_time": 3.5,
                "parallel_capable": True,
                "tools": [
                    "generate_adaptive_workout",
                    "analyze_performance",
                    "analyze_user_behavior",
                    "generate_motivational_message",
                    "create_habit_plan"
                ]
            },
            AgentType.ORCHESTRATION: {
                "primary_intents": [
                    IntentType.CASUAL_CHAT,
                    IntentType.GENERAL_FITNESS
                ],
                "secondary_intents": [],
                "average_response_time": 1.0,
                "parallel_capable": False,
                "tools": [
                    "quick_response"
                ]
            }
        }
    
    def _load_synthesis_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load rules for synthesizing responses from multiple agents."""
        return {
            "logging_with_analysis": {
                "primary_response": "logging_result",
                "secondary_context": "analysis_insights",
                "synthesis_template": "{logging_result}\n\n📊 **Insights**: {analysis_insights}"
            },
            "workout_with_motivation": {
                "primary_response": "workout_plan",
                "secondary_context": "motivational_message",
                "synthesis_template": "{workout_plan}\n\n💪 **Motivation**: {motivational_message}"
            },
            "comprehensive_coaching": {
                "primary_response": "main_analysis",
                "secondary_context": ["behavioral_insights", "recommendations"],
                "synthesis_template": "{main_analysis}\n\n🧠 **Psychology**: {behavioral_insights}\n\n🎯 **Action Plan**: {recommendations}"
            }
        }
    
    async def analyze_multi_intent(self, user_message: str, 
                                 context: Optional[Dict[str, Any]] = None) -> List[Intent]:
        """
        Analyze user message for multiple intents.
        
        Args:
            user_message: User's input message
            context: Additional context (conversation history, user profile, etc.)
            
        Returns:
            List of recognized intents with confidence scores
        """
        message_lower = user_message.lower()
        recognized_intents = []
        
        # Analyze each intent type
        for intent_type, patterns_list in self.intent_patterns.items():
            for pattern_config in patterns_list:
                confidence = 0.0
                matches = 0
                
                # Check pattern matches
                for pattern in pattern_config["patterns"]:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        matches += 1
                        confidence += 0.2
                
                # Apply confidence boost if patterns matched
                if matches > 0:
                    confidence += pattern_config.get("confidence_boost", 0.0)
                    confidence = min(confidence, 1.0)
                    
                    # Extract parameters based on intent type
                    parameters = await self._extract_intent_parameters(
                        intent_type, user_message, pattern_config
                    )
                    
                    # Create intent
                    intent = Intent(
                        type=intent_type,
                        confidence=confidence,
                        parameters=parameters,
                        context=context or {},
                        agent_preference=pattern_config.get("agent_preference")
                    )
                    
                    recognized_intents.append(intent)
                    break  # Only match first pattern config per intent type
        
        # Filter and rank intents
        filtered_intents = [i for i in recognized_intents if i.confidence >= 0.3]
        filtered_intents.sort(key=lambda x: x.confidence, reverse=True)
        
        # Handle special cases and dependencies
        filtered_intents = await self._resolve_intent_dependencies(filtered_intents, user_message)
        
        return filtered_intents[:5]  # Return top 5 intents max
    
    async def _extract_intent_parameters(self, intent_type: IntentType, 
                                       message: str, 
                                       pattern_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters specific to each intent type."""
        parameters = {}
        
        if intent_type == IntentType.ACTIVITY_LOGGING:
            parameters["activity_description"] = message
            
            # Extract specific details if present
            duration_match = re.search(r"(\d+)\s*(minutes?|mins?|hours?)", message, re.IGNORECASE)
            if duration_match:
                duration = int(duration_match.group(1))
                unit = duration_match.group(2).lower()
                if "hour" in unit:
                    duration *= 60
                parameters["duration"] = duration
            
            distance_match = re.search(r"(\d+(?:\.\d+)?)\s*(km|miles?|k)", message, re.IGNORECASE)
            if distance_match:
                parameters["distance"] = float(distance_match.group(1))
                parameters["unit"] = distance_match.group(2)
        
        elif intent_type == IntentType.WORKOUT_PLANNING:
            # Extract duration
            duration_match = re.search(r"(\d+)\s*(minute|min|hour)", message, re.IGNORECASE)
            if duration_match:
                duration = int(duration_match.group(1))
                if "hour" in duration_match.group(2):
                    duration *= 60
                parameters["duration"] = duration
            else:
                parameters["duration"] = 30  # Default
            
            # Extract goals
            goal_keywords = {
                "weight loss": ["lose weight", "weight loss", "slim down", "cut"],
                "muscle gain": ["build muscle", "gain muscle", "bulk", "strength"],
                "endurance": ["endurance", "cardio", "stamina", "marathon"],
                "general fitness": ["fit", "health", "general", "overall"]
            }
            
            for goal, keywords in goal_keywords.items():
                if any(keyword in message.lower() for keyword in keywords):
                    parameters["goals"] = [goal]
                    break
            else:
                parameters["goals"] = ["general_fitness"]
        
        elif intent_type == IntentType.MOTIVATION_SEEKING:
            # Determine context
            if any(word in message.lower() for word in ["before", "pre", "about to"]):
                parameters["context"] = "pre_workout"
            elif any(word in message.lower() for word in ["after", "post", "finished", "completed"]):
                parameters["context"] = "post_workout"
            elif any(word in message.lower() for word in ["missed", "skipped", "didn't"]):
                parameters["context"] = "missed_workout"
            else:
                parameters["context"] = "general"
        
        elif intent_type == IntentType.HABIT_FORMATION:
            # Extract target behavior
            if "exercise" in message.lower() or "workout" in message.lower():
                if re.search(r"(\d+)\s*times?\s*(week|per week)", message, re.IGNORECASE):
                    freq_match = re.search(r"(\d+)\s*times?\s*(week|per week)", message, re.IGNORECASE)
                    frequency = int(freq_match.group(1))
                    parameters["target_behavior"] = f"exercise {frequency} times per week"
                else:
                    parameters["target_behavior"] = "exercise regularly"
            else:
                parameters["target_behavior"] = "maintain healthy habits"
        
        return parameters
    
    async def _resolve_intent_dependencies(self, intents: List[Intent], 
                                         message: str) -> List[Intent]:
        """Resolve dependencies and conflicts between intents."""
        if len(intents) <= 1:
            return intents
        
        resolved_intents = intents.copy()
        
        # Handle specific combinations
        intent_types = [i.type for i in intents]
        
        # If both logging and progress inquiry are present, logging should come first
        if (IntentType.ACTIVITY_LOGGING in intent_types and 
            IntentType.PROGRESS_INQUIRY in intent_types):
            
            for intent in resolved_intents:
                if intent.type == IntentType.PROGRESS_INQUIRY:
                    intent.dependencies = ["activity_logging"]
                    intent.priority = 2
        
        # If workout planning and motivation are both present, they can run parallel
        if (IntentType.WORKOUT_PLANNING in intent_types and 
            IntentType.MOTIVATION_SEEKING in intent_types):
            
            for intent in resolved_intents:
                if intent.type in [IntentType.WORKOUT_PLANNING, IntentType.MOTIVATION_SEEKING]:
                    intent.priority = 1  # Same priority for parallel execution
        
        # Performance analysis should come after progress inquiry
        if (IntentType.PROGRESS_INQUIRY in intent_types and 
            IntentType.PERFORMANCE_ANALYSIS in intent_types):
            
            for intent in resolved_intents:
                if intent.type == IntentType.PERFORMANCE_ANALYSIS:
                    intent.dependencies = ["progress_inquiry"]
                    intent.priority = 2
        
        return resolved_intents
    
    async def create_execution_plan(self, intents: List[Intent]) -> ExecutionPlan:
        """
        Create an execution plan for multiple intents.
        
        Args:
            intents: List of intents to execute
            
        Returns:
            ExecutionPlan with strategy and execution order
        """
        if not intents:
            return ExecutionPlan(
                intents=[],
                strategy=ExecutionStrategy.SEQUENTIAL,
                execution_order=[]
            )
        
        if len(intents) == 1:
            return ExecutionPlan(
                intents=intents,
                strategy=ExecutionStrategy.SEQUENTIAL,
                execution_order=[0],
                estimated_duration=2.0,
                complexity_score=1.0
            )
        
        # Analyze intent combination for strategy selection
        strategy, execution_order, parallel_groups = await self._determine_execution_strategy(intents)
        
        # Calculate estimated duration and complexity
        estimated_duration = await self._estimate_execution_time(intents, strategy, parallel_groups)
        complexity_score = await self._calculate_complexity_score(intents, strategy)
        
        return ExecutionPlan(
            intents=intents,
            strategy=strategy,
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            estimated_duration=estimated_duration,
            complexity_score=complexity_score
        )
    
    async def _determine_execution_strategy(self, intents: List[Intent]) -> Tuple[ExecutionStrategy, List[int], List[List[int]]]:
        """Determine the best execution strategy for the given intents."""
        intent_types = [i.type for i in intents]
        
        # Check for known patterns
        if (IntentType.ACTIVITY_LOGGING in intent_types and 
            IntentType.PROGRESS_INQUIRY in intent_types):
            # Sequential: log first, then analyze
            return ExecutionStrategy.SEQUENTIAL, [0, 1], []
        
        if (IntentType.WORKOUT_PLANNING in intent_types and 
            IntentType.MOTIVATION_SEEKING in intent_types):
            # Parallel: can generate workout and motivation simultaneously
            return ExecutionStrategy.PARALLEL, [0, 1], [[0, 1]]
        
        if (IntentType.PERFORMANCE_ANALYSIS in intent_types and 
            IntentType.BEHAVIORAL_ANALYSIS in intent_types):
            # Parallel: both are analysis tasks that can run simultaneously
            return ExecutionStrategy.PARALLEL, [0, 1], [[0, 1]]
        
        # Check for dependencies
        has_dependencies = any(i.dependencies for i in intents)
        if has_dependencies:
            # Sort by priority and dependencies
            sorted_intents = sorted(enumerate(intents), key=lambda x: (x[1].priority, len(x[1].dependencies)))
            execution_order = [i[0] for i in sorted_intents]
            return ExecutionStrategy.SEQUENTIAL, execution_order, []
        
        # Check if all intents can use the same agent (parallel execution possible)
        agent_preferences = [i.agent_preference for i in intents if i.agent_preference]
        if len(set(agent_preferences)) == 1 and len(agent_preferences) == len(intents):
            # All intents prefer the same agent - can potentially run in parallel
            return ExecutionStrategy.PARALLEL, list(range(len(intents))), [list(range(len(intents)))]
        
        # Default to sequential execution
        return ExecutionStrategy.SEQUENTIAL, list(range(len(intents))), []
    
    async def _estimate_execution_time(self, intents: List[Intent], 
                                     strategy: ExecutionStrategy,
                                     parallel_groups: List[List[int]]) -> float:
        """Estimate total execution time for the plan."""
        total_time = 0.0
        
        if strategy == ExecutionStrategy.SEQUENTIAL:
            for intent in intents:
                agent = intent.agent_preference or AgentType.ORCHESTRATION
                agent_time = self.agent_capabilities[agent]["average_response_time"]
                total_time += agent_time
        
        elif strategy == ExecutionStrategy.PARALLEL:
            if parallel_groups:
                for group in parallel_groups:
                    group_times = []
                    for idx in group:
                        intent = intents[idx]
                        agent = intent.agent_preference or AgentType.ORCHESTRATION
                        agent_time = self.agent_capabilities[agent]["average_response_time"]
                        group_times.append(agent_time)
                    total_time += max(group_times)  # Parallel execution takes max time
            else:
                # All parallel
                max_time = 0.0
                for intent in intents:
                    agent = intent.agent_preference or AgentType.ORCHESTRATION
                    agent_time = self.agent_capabilities[agent]["average_response_time"]
                    max_time = max(max_time, agent_time)
                total_time = max_time
        
        return total_time
    
    async def _calculate_complexity_score(self, intents: List[Intent], 
                                        strategy: ExecutionStrategy) -> float:
        """Calculate complexity score for the execution plan."""
        base_complexity = len(intents)
        
        # Strategy complexity multiplier
        strategy_multipliers = {
            ExecutionStrategy.SEQUENTIAL: 1.0,
            ExecutionStrategy.PARALLEL: 1.5,
            ExecutionStrategy.CONDITIONAL: 2.0,
            ExecutionStrategy.HYBRID: 2.5
        }
        
        strategy_multiplier = strategy_multipliers.get(strategy, 1.0)
        
        # Intent complexity
        intent_complexities = {
            IntentType.CASUAL_CHAT: 0.5,
            IntentType.ACTIVITY_LOGGING: 1.0,
            IntentType.PROGRESS_INQUIRY: 1.5,
            IntentType.WORKOUT_PLANNING: 2.0,
            IntentType.PERFORMANCE_ANALYSIS: 2.5,
            IntentType.BEHAVIORAL_ANALYSIS: 2.0,
            IntentType.MOTIVATION_SEEKING: 1.0,
            IntentType.HABIT_FORMATION: 1.5
        }
        
        avg_intent_complexity = sum(
            intent_complexities.get(intent.type, 1.0) for intent in intents
        ) / len(intents)
        
        return base_complexity * strategy_multiplier * avg_intent_complexity
    
    async def synthesize_responses(self, execution_results: List[ExecutionResult],
                                 original_message: str) -> OrchestrationResponse:
        """
        Synthesize multiple execution results into a coherent response.
        
        Args:
            execution_results: Results from executing multiple intents
            original_message: Original user message for context
            
        Returns:
            OrchestrationResponse with synthesized content
        """
        if not execution_results:
            return OrchestrationResponse(
                primary_response="I couldn't process your request. Please try again.",
                execution_results=[],
                synthesis_confidence=0.0,
                total_execution_time=0.0,
                intents_processed=0,
                strategy_used=ExecutionStrategy.SEQUENTIAL
            )
        
        if len(execution_results) == 1:
            # Single result - return as-is
            result = execution_results[0]
            return OrchestrationResponse(
                primary_response=result.response,
                execution_results=execution_results,
                synthesis_confidence=result.confidence,
                total_execution_time=result.execution_time,
                intents_processed=1,
                strategy_used=ExecutionStrategy.SEQUENTIAL
            )
        
        # Multiple results - synthesize
        primary_response = await self._synthesize_multiple_responses(execution_results, original_message)
        
        # Calculate metrics
        total_time = sum(r.execution_time for r in execution_results)
        avg_confidence = sum(r.confidence for r in execution_results) / len(execution_results)
        
        # Determine strategy used
        strategy = ExecutionStrategy.PARALLEL if total_time < sum(r.execution_time for r in execution_results) else ExecutionStrategy.SEQUENTIAL
        
        return OrchestrationResponse(
            primary_response=primary_response,
            execution_results=execution_results,
            synthesis_confidence=avg_confidence,
            total_execution_time=total_time,
            intents_processed=len(execution_results),
            strategy_used=strategy
        )
    
    async def _synthesize_multiple_responses(self, results: List[ExecutionResult], 
                                           original_message: str) -> str:
        """Synthesize multiple execution results into a coherent response."""
        # Group results by type
        result_types = [r.intent_type for r in results]
        
        # Check for known synthesis patterns
        if (IntentType.ACTIVITY_LOGGING in result_types and 
            IntentType.PROGRESS_INQUIRY in result_types):
            
            logging_result = next(r for r in results if r.intent_type == IntentType.ACTIVITY_LOGGING)
            progress_result = next(r for r in results if r.intent_type == IntentType.PROGRESS_INQUIRY)
            
            return f"{logging_result.response}\n\n📊 **Progress Update**: {progress_result.response}"
        
        if (IntentType.WORKOUT_PLANNING in result_types and 
            IntentType.MOTIVATION_SEEKING in result_types):
            
            workout_result = next(r for r in results if r.intent_type == IntentType.WORKOUT_PLANNING)
            motivation_result = next(r for r in results if r.intent_type == IntentType.MOTIVATION_SEEKING)
            
            return f"{workout_result.response}\n\n{motivation_result.response}"
        
        if (IntentType.PERFORMANCE_ANALYSIS in result_types and 
            IntentType.BEHAVIORAL_ANALYSIS in result_types):
            
            performance_result = next(r for r in results if r.intent_type == IntentType.PERFORMANCE_ANALYSIS)
            behavioral_result = next(r for r in results if r.intent_type == IntentType.BEHAVIORAL_ANALYSIS)
            
            return f"{performance_result.response}\n\n🧠 **Behavioral Insights**: {behavioral_result.response}"
        
        # Default synthesis - combine responses with clear sections
        synthesized_parts = []
        
        for i, result in enumerate(results, 1):
            if len(results) > 1:
                intent_name = result.intent_type.value.replace('_', ' ').title()
                synthesized_parts.append(f"## {intent_name}")
            
            synthesized_parts.append(result.response)
            
            if i < len(results):
                synthesized_parts.append("")  # Add spacing between sections
        
        return "\n".join(synthesized_parts)


# Global service instance
orchestration_intelligence_service = OrchestrationIntelligenceService()
