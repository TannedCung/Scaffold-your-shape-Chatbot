"""Semantic Memory Service for Enhanced Conversation Understanding.

This service extends the basic memory system with semantic understanding,
context analysis, and intelligent conversation management.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from collections import defaultdict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from services.langchain_memory_service import langchain_memory_service
from config.settings import get_configuration


class ConversationIntent(Enum):
    """Types of conversation intents."""
    ACTIVITY_LOGGING = "activity_logging"
    PROGRESS_INQUIRY = "progress_inquiry"
    WORKOUT_PLANNING = "workout_planning"
    MOTIVATION_SEEKING = "motivation_seeking"
    GENERAL_FITNESS = "general_fitness"
    GOAL_SETTING = "goal_setting"
    PROBLEM_SOLVING = "problem_solving"
    CASUAL_CHAT = "casual_chat"


class ConversationContext(Enum):
    """Context categories for conversations."""
    FIRST_TIME_USER = "first_time_user"
    RETURNING_USER = "returning_user"
    STRUGGLING_USER = "struggling_user"
    MOTIVATED_USER = "motivated_user"
    GOAL_ORIENTED = "goal_oriented"
    CASUAL_FITNESS = "casual_fitness"


@dataclass
class SemanticContext:
    """Semantic context extracted from conversations."""
    user_goals: List[str] = field(default_factory=list)
    fitness_level: Optional[str] = None
    preferred_activities: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)  # time, equipment, physical
    motivations: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    personality_traits: List[str] = field(default_factory=list)
    recent_achievements: List[str] = field(default_factory=list)
    current_mood: Optional[str] = None
    conversation_context: Optional[ConversationContext] = None


@dataclass
class ConversationSummary:
    """Summary of conversation patterns and insights."""
    user_id: str
    total_conversations: int
    most_common_intents: List[str]
    engagement_level: float
    consistency_pattern: str
    key_topics: List[str]
    semantic_context: SemanticContext
    last_updated: datetime


class SemanticMemoryService:
    """Enhanced memory service with semantic understanding."""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.context_analyzers = self._load_context_analyzers()
        self.semantic_cache = {}  # Cache for semantic analysis
        
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for intent recognition."""
        return {
            ConversationIntent.ACTIVITY_LOGGING.value: [
                r"\b(ran|run|jogged|cycled|swam|lifted|did|completed|finished)\b",
                r"\b(workout|exercise|activity|training)\b",
                r"\d+\s*(km|miles|minutes|hours|reps|sets)",
                r"\b(today|yesterday|this morning|last night)\b"
            ],
            ConversationIntent.PROGRESS_INQUIRY.value: [
                r"\b(how am i doing|progress|improvement|better|worse)\b",
                r"\b(stats|statistics|numbers|data|results)\b",
                r"\b(compare|comparison|trend|trending)\b",
                r"\b(show me|tell me about|what about)\s+.*\b(progress|performance)\b"
            ],
            ConversationIntent.WORKOUT_PLANNING.value: [
                r"\b(plan|schedule|routine|program)\b",
                r"\b(what should i|recommend|suggest|advice)\b",
                r"\b(next workout|tomorrow|this week)\b",
                r"\b(create|make|design)\s+.*\b(workout|plan|routine)\b"
            ],
            ConversationIntent.MOTIVATION_SEEKING.value: [
                r"\b(motivation|motivate|encourage|support)\b",
                r"\b(tired|exhausted|don't want to|not feeling)\b",
                r"\b(give up|quit|stop|lazy)\b",
                r"\b(inspire|inspiration|push|drive)\b"
            ],
            ConversationIntent.GOAL_SETTING.value: [
                r"\b(goal|target|aim|objective)\b",
                r"\b(want to|hoping to|trying to|plan to)\b",
                r"\b(achieve|reach|hit|accomplish)\b",
                r"\b(lose weight|gain muscle|get fit|marathon)\b"
            ]
        }
    
    def _load_context_analyzers(self) -> Dict[str, Any]:
        """Load context analysis patterns."""
        return {
            "fitness_level": {
                "beginner": [r"\b(new to|just started|beginner|first time)\b"],
                "intermediate": [r"\b(been doing|few months|getting back)\b"],
                "advanced": [r"\b(years|experienced|competitive|athlete)\b"]
            },
            "constraints": {
                "time": [r"\b(busy|no time|quick|short|limited time)\b"],
                "equipment": [r"\b(no gym|home|bodyweight|no equipment)\b"],
                "injury": [r"\b(hurt|pain|injury|sore|recovering)\b"],
                "weather": [r"\b(rain|cold|hot|weather|outside)\b"]
            },
            "mood_indicators": {
                "positive": [r"\b(great|awesome|fantastic|love|excited)\b"],
                "neutral": [r"\b(okay|fine|alright|normal)\b"],
                "negative": [r"\b(tired|frustrated|difficult|hard|struggling)\b"]
            }
        }
    
    async def analyze_conversation_semantics(self, user_id: str, 
                                           recent_messages: List[BaseMessage],
                                           session_id: str = "default") -> SemanticContext:
        """
        Analyze conversation semantics to extract deeper context.
        
        Args:
            user_id: User ID
            recent_messages: Recent conversation messages
            session_id: Session ID
            
        Returns:
            SemanticContext with extracted insights
        """
        # Get or create cached context
        cache_key = f"{user_id}_{session_id}"
        if cache_key in self.semantic_cache:
            context = self.semantic_cache[cache_key]
        else:
            context = SemanticContext()
        
        # Analyze recent messages for semantic content
        message_texts = []
        for message in recent_messages[-10:]:  # Analyze last 10 messages
            if isinstance(message, (HumanMessage, AIMessage)):
                message_texts.append(message.content)
        
        combined_text = " ".join(message_texts).lower()
        
        # Extract goals
        goals = await self._extract_goals(combined_text)
        context.user_goals.extend(goals)
        context.user_goals = list(set(context.user_goals))  # Remove duplicates
        
        # Determine fitness level
        fitness_level = await self._determine_fitness_level(combined_text)
        if fitness_level:
            context.fitness_level = fitness_level
        
        # Extract preferred activities
        activities = await self._extract_preferred_activities(combined_text)
        context.preferred_activities.extend(activities)
        context.preferred_activities = list(set(context.preferred_activities))
        
        # Identify constraints
        constraints = await self._identify_constraints(combined_text)
        context.constraints.extend(constraints)
        context.constraints = list(set(context.constraints))
        
        # Analyze mood
        mood = await self._analyze_current_mood(combined_text)
        if mood:
            context.current_mood = mood
        
        # Determine conversation context
        conv_context = await self._determine_conversation_context(
            user_id, recent_messages, context
        )
        context.conversation_context = conv_context
        
        # Cache the updated context
        self.semantic_cache[cache_key] = context
        
        return context
    
    async def _extract_goals(self, text: str) -> List[str]:
        """Extract fitness goals from conversation text."""
        goals = []
        
        goal_patterns = {
            "weight_loss": [r"\b(lose weight|slim down|get leaner|cut|shred)\b"],
            "muscle_gain": [r"\b(gain muscle|bulk up|build muscle|get stronger|strength)\b"],
            "endurance": [r"\b(endurance|stamina|cardio|marathon|distance)\b"],
            "general_fitness": [r"\b(get fit|stay healthy|improve fitness|overall health)\b"],
            "sport_specific": [r"\b(basketball|soccer|tennis|swimming|cycling|running)\b.*\b(better|improve|compete)\b"]
        }
        
        for goal_type, patterns in goal_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    goals.append(goal_type)
                    break
        
        return goals
    
    async def _determine_fitness_level(self, text: str) -> Optional[str]:
        """Determine user's fitness level from conversation."""
        level_indicators = self.context_analyzers["fitness_level"]
        
        for level, patterns in level_indicators.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return level
        
        return None
    
    async def _extract_preferred_activities(self, text: str) -> List[str]:
        """Extract preferred activities from conversation."""
        activities = []
        
        activity_patterns = [
            r"\b(love|enjoy|like|prefer|favorite)\s+.*\b(running|cycling|swimming|yoga|lifting|gym)\b",
            r"\b(running|cycling|swimming|yoga|lifting|gym)\b.*\b(fun|enjoy|great|love)\b"
        ]
        
        common_activities = ["running", "cycling", "swimming", "yoga", "lifting", "gym", "walking", "hiking"]
        
        for pattern in activity_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                for activity in common_activities:
                    if activity in match.group(0).lower():
                        activities.append(activity)
        
        # Also check for direct mentions
        for activity in common_activities:
            if re.search(rf"\b{activity}\b", text, re.IGNORECASE):
                activities.append(activity)
        
        return list(set(activities))
    
    async def _identify_constraints(self, text: str) -> List[str]:
        """Identify user constraints from conversation."""
        constraints = []
        
        constraint_patterns = self.context_analyzers["constraints"]
        
        for constraint_type, patterns in constraint_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    constraints.append(constraint_type)
                    break
        
        return constraints
    
    async def _analyze_current_mood(self, text: str) -> Optional[str]:
        """Analyze current mood from conversation."""
        mood_patterns = self.context_analyzers["mood_indicators"]
        
        # Weight recent messages more heavily
        for mood, patterns in mood_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return mood
        
        return None
    
    async def _determine_conversation_context(self, user_id: str, 
                                            recent_messages: List[BaseMessage],
                                            semantic_context: SemanticContext) -> ConversationContext:
        """Determine the overall conversation context."""
        # Get conversation history length
        try:
            memory_stats = await langchain_memory_service.get_user_memory_stats(user_id)
            message_count = memory_stats.get('message_count', 0)
        except:
            message_count = len(recent_messages)
        
        # Determine context based on various factors
        if message_count <= 10:
            return ConversationContext.FIRST_TIME_USER
        
        if semantic_context.current_mood == "negative":
            return ConversationContext.STRUGGLING_USER
        
        if semantic_context.current_mood == "positive" and semantic_context.user_goals:
            return ConversationContext.MOTIVATED_USER
        
        if len(semantic_context.user_goals) >= 2:
            return ConversationContext.GOAL_ORIENTED
        
        return ConversationContext.RETURNING_USER
    
    async def generate_contextual_prompt_enhancement(self, user_id: str, 
                                                   base_prompt: str,
                                                   session_id: str = "default") -> str:
        """
        Enhance agent prompts with semantic context.
        
        Args:
            user_id: User ID
            base_prompt: Base agent prompt
            session_id: Session ID
            
        Returns:
            Enhanced prompt with contextual information
        """
        # Get recent conversation history
        try:
            memory_variables = await langchain_memory_service.get_memory_variables(user_id, session_id)
            recent_messages = memory_variables.get('chat_history', [])[-10:]
        except:
            recent_messages = []
        
        if not recent_messages:
            return base_prompt
        
        # Analyze semantic context
        semantic_context = await self.analyze_conversation_semantics(
            user_id, recent_messages, session_id
        )
        
        # Generate context enhancement
        context_parts = []
        
        if semantic_context.user_goals:
            goals_str = ", ".join(semantic_context.user_goals)
            context_parts.append(f"User's fitness goals: {goals_str}")
        
        if semantic_context.fitness_level:
            context_parts.append(f"Fitness level: {semantic_context.fitness_level}")
        
        if semantic_context.preferred_activities:
            activities_str = ", ".join(semantic_context.preferred_activities[:3])
            context_parts.append(f"Preferred activities: {activities_str}")
        
        if semantic_context.constraints:
            constraints_str = ", ".join(semantic_context.constraints)
            context_parts.append(f"Known constraints: {constraints_str}")
        
        if semantic_context.current_mood:
            context_parts.append(f"Current mood: {semantic_context.current_mood}")
        
        if semantic_context.conversation_context:
            context_parts.append(f"Context: {semantic_context.conversation_context.value}")
        
        if context_parts:
            context_enhancement = "\n## User Context:\n" + "\n".join(f"- {part}" for part in context_parts)
            
            # Add personalization instructions
            personalization = """
## Personalization Instructions:
- Reference the user's goals and preferences when relevant
- Adapt your communication style to their current mood and context
- Consider their constraints when making recommendations
- Build on their preferred activities when suggesting workouts
- Acknowledge their fitness level in your advice
"""
            
            enhanced_prompt = base_prompt + context_enhancement + personalization
            return enhanced_prompt
        
        return base_prompt
    
    async def analyze_conversation_intent(self, message: str) -> List[ConversationIntent]:
        """Analyze the intent of a conversation message."""
        intents = []
        message_lower = message.lower()
        
        for intent_name, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    intents.append(ConversationIntent(intent_name))
                    break
        
        # If no specific intent found, default to casual chat
        if not intents:
            intents.append(ConversationIntent.CASUAL_CHAT)
        
        return intents
    
    async def generate_conversation_summary(self, user_id: str, 
                                          session_id: str = "default") -> ConversationSummary:
        """Generate a comprehensive conversation summary."""
        try:
            # Get conversation history
            memory_variables = await langchain_memory_service.get_memory_variables(user_id, session_id)
            messages = memory_variables.get('chat_history', [])
            
            # Analyze all messages for patterns
            user_messages = [msg.content for msg in messages if isinstance(msg, HumanMessage)]
            
            # Count intents
            intent_counter = defaultdict(int)
            for message in user_messages:
                intents = await self.analyze_conversation_intent(message)
                for intent in intents:
                    intent_counter[intent.value] += 1
            
            most_common_intents = [
                intent for intent, count in 
                sorted(intent_counter.items(), key=lambda x: x[1], reverse=True)[:3]
            ]
            
            # Calculate engagement level
            if messages:
                avg_message_length = sum(len(msg.content) for msg in user_messages) / len(user_messages) if user_messages else 0
                engagement_level = min(avg_message_length / 50, 1.0)  # Normalize to 0-1
            else:
                engagement_level = 0.0
            
            # Analyze semantic context
            semantic_context = await self.analyze_conversation_semantics(user_id, messages, session_id)
            
            # Determine consistency pattern
            # This would analyze timing patterns in a real implementation
            consistency_pattern = "regular" if len(messages) > 20 else "sporadic"
            
            # Extract key topics (simplified)
            key_topics = list(set(semantic_context.preferred_activities + semantic_context.user_goals))
            
            return ConversationSummary(
                user_id=user_id,
                total_conversations=len(user_messages),
                most_common_intents=most_common_intents,
                engagement_level=engagement_level,
                consistency_pattern=consistency_pattern,
                key_topics=key_topics,
                semantic_context=semantic_context,
                last_updated=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            # Return minimal summary on error
            return ConversationSummary(
                user_id=user_id,
                total_conversations=0,
                most_common_intents=[],
                engagement_level=0.0,
                consistency_pattern="unknown",
                key_topics=[],
                semantic_context=SemanticContext(),
                last_updated=datetime.now(timezone.utc)
            )
    
    async def get_personalized_suggestions(self, user_id: str, 
                                         context: str = "general",
                                         session_id: str = "default") -> List[str]:
        """Generate personalized suggestions based on semantic context."""
        semantic_context = await self.analyze_conversation_semantics(
            user_id, 
            await self._get_recent_messages(user_id, session_id), 
            session_id
        )
        
        suggestions = []
        
        # Goal-based suggestions
        if "weight_loss" in semantic_context.user_goals:
            suggestions.append("Consider adding more cardio activities to support your weight loss goal")
        
        if "muscle_gain" in semantic_context.user_goals:
            suggestions.append("Focus on progressive strength training with adequate protein intake")
        
        # Constraint-based suggestions
        if "time" in semantic_context.constraints:
            suggestions.append("Try high-intensity interval training (HIIT) for time-efficient workouts")
        
        if "equipment" in semantic_context.constraints:
            suggestions.append("Bodyweight exercises can be very effective for home workouts")
        
        # Mood-based suggestions
        if semantic_context.current_mood == "negative":
            suggestions.append("Start with a gentle activity you enjoy to build momentum")
        elif semantic_context.current_mood == "positive":
            suggestions.append("Great energy! This might be a good time to try something challenging")
        
        # Context-based suggestions
        if semantic_context.conversation_context == ConversationContext.FIRST_TIME_USER:
            suggestions.append("Start with 2-3 activities per week and gradually increase")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    async def _get_recent_messages(self, user_id: str, session_id: str) -> List[BaseMessage]:
        """Get recent messages for a user."""
        try:
            memory_variables = await langchain_memory_service.get_memory_variables(user_id, session_id)
            return memory_variables.get('chat_history', [])[-10:]
        except:
            return []
    
    def clear_semantic_cache(self, user_id: str = None):
        """Clear semantic cache for a user or all users."""
        if user_id:
            keys_to_remove = [key for key in self.semantic_cache.keys() if key.startswith(f"{user_id}_")]
            for key in keys_to_remove:
                del self.semantic_cache[key]
        else:
            self.semantic_cache.clear()


# Global service instance
semantic_memory_service = SemanticMemoryService()
