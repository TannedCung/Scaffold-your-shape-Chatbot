"""Enhanced Coach Agent Tools with Adaptive Workout Generation and Behavioral Psychology.

This module provides advanced tools for the Coach Agent that integrate:
- Adaptive workout generation based on user profile
- Behavioral psychology interventions
- Personalized motivational messaging
- Habit formation strategies
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from services.adaptive_workout_service import (
    adaptive_workout_service,
    UserFitnessProfile,
    FitnessGoal,
    WorkoutType,
    IntensityLevel
)
from services.behavioral_psychology_service import (
    behavioral_psychology_service,
    BehavioralProfile,
    MotivationType,
    PersonalityType,
    BehaviorStage
)
from services.semantic_memory_service import semantic_memory_service


class AdaptiveWorkoutInput(BaseModel):
    """Input for adaptive workout generation."""
    user_id: str = Field(description="User ID for personalization")
    duration_minutes: int = Field(
        default=30,
        description="Desired workout duration in minutes"
    )
    fitness_goal: str = Field(
        default="general_fitness",
        description="Primary fitness goal (weight_loss, muscle_gain, endurance, etc.)"
    )
    fitness_level: str = Field(
        default="intermediate",
        description="User's fitness level (beginner, intermediate, advanced)"
    )
    available_equipment: List[str] = Field(
        default_factory=list,
        description="List of available equipment"
    )
    workout_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context (mood, energy, recent workouts, etc.)"
    )


class BehavioralAnalysisInput(BaseModel):
    """Input for behavioral psychology analysis."""
    user_id: str = Field(description="User ID for analysis")
    include_interventions: bool = Field(
        default=True,
        description="Whether to include intervention recommendations"
    )
    current_challenges: List[str] = Field(
        default_factory=list,
        description="Current challenges or barriers user is facing"
    )


class MotivationalMessageInput(BaseModel):
    """Input for generating motivational messages."""
    user_id: str = Field(description="User ID for personalization")
    context: str = Field(
        default="general",
        description="Message context (pre_workout, post_workout, milestone, etc.)"
    )
    current_mood: Optional[str] = Field(
        default=None,
        description="User's current mood or emotional state"
    )


class HabitFormationInput(BaseModel):
    """Input for habit formation planning."""
    user_id: str = Field(description="User ID for personalization")
    target_habit: str = Field(
        description="The habit to be formed (e.g., 'exercise 3 times per week')"
    )
    current_barriers: List[str] = Field(
        default_factory=list,
        description="Current barriers to forming this habit"
    )


class AdaptiveWorkoutTool(BaseTool):
    """Tool for generating personalized, adaptive workouts."""
    
    name: str = "generate_adaptive_workout"
    description: str = """
    Generate a personalized workout plan using advanced adaptation algorithms.
    
    This tool creates workouts that adapt to:
    - User's fitness level and goals
    - Available equipment and time constraints
    - Personal preferences and workout history
    - Current context (mood, energy, recent activities)
    
    The generated workout includes:
    - Warm-up, main exercises, and cool-down
    - Exercise modifications for different fitness levels
    - Coaching notes and progression suggestions
    - Estimated calories and duration
    """
    args_schema: type = AdaptiveWorkoutInput
    
    def _run(self, user_id: str, duration_minutes: int = 30,
             fitness_goal: str = "general_fitness", fitness_level: str = "intermediate",
             available_equipment: List[str] = None, 
             workout_context: Optional[Dict[str, Any]] = None) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(
            user_id, duration_minutes, fitness_goal, fitness_level, 
            available_equipment or [], workout_context
        ))
    
    async def _arun(self, user_id: str, duration_minutes: int = 30,
                   fitness_goal: str = "general_fitness", fitness_level: str = "intermediate",
                   available_equipment: List[str] = None,
                   workout_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate adaptive workout plan."""
        try:
            # Create user fitness profile
            user_profile = UserFitnessProfile(
                fitness_level=fitness_level,
                primary_goals=[FitnessGoal(fitness_goal)],
                available_equipment=available_equipment or [],
                time_constraints={"preferred_duration": duration_minutes},
                workout_frequency=3
            )
            
            # Get semantic context for personalization
            try:
                semantic_context = await semantic_memory_service.analyze_conversation_semantics(
                    user_id=user_id,
                    recent_messages=await self._get_recent_messages(user_id),
                    session_id="default"
                )
                
                # Update profile with semantic insights
                if semantic_context.preferred_activities:
                    user_profile.preferred_activities = semantic_context.preferred_activities
                
                if semantic_context.constraints:
                    user_profile.physical_limitations = semantic_context.constraints
                    
            except Exception as e:
                print(f"Warning: Could not get semantic context: {e}")
            
            # Generate adaptive workout
            workout_plan = await adaptive_workout_service.generate_adaptive_workout(
                user_profile=user_profile,
                workout_context=workout_context
            )
            
            # Format response
            response_parts = []
            
            # Header
            response_parts.append(f"🏋️ **{workout_plan.name}**")
            response_parts.append(f"⏱️ Duration: {workout_plan.total_duration_minutes} minutes")
            response_parts.append(f"🎯 Intensity: {workout_plan.intensity.value.title()}")
            response_parts.append(f"🔥 Estimated Calories: {workout_plan.estimated_calories}")
            
            if workout_plan.equipment_needed:
                equipment_str = ", ".join(workout_plan.equipment_needed)
                response_parts.append(f"🛠️ Equipment: {equipment_str}")
            
            # Warm-up
            if workout_plan.warm_up:
                response_parts.append(f"\n🔥 **Warm-up ({sum(e.duration_minutes or 0 for e in workout_plan.warm_up)} min):**")
                for exercise in workout_plan.warm_up:
                    response_parts.append(f"  • {exercise.name}: {exercise.instructions}")
            
            # Main workout
            response_parts.append(f"\n💪 **Main Workout:**")
            for i, exercise in enumerate(workout_plan.exercises, 1):
                exercise_desc = f"{i}. **{exercise.name}**"
                
                if exercise.sets and exercise.reps:
                    exercise_desc += f" - {exercise.sets} sets x {exercise.reps} reps"
                elif exercise.duration_minutes:
                    exercise_desc += f" - {exercise.duration_minutes} minutes"
                
                if exercise.rest_seconds:
                    exercise_desc += f" (Rest: {exercise.rest_seconds}s)"
                
                response_parts.append(exercise_desc)
                
                if exercise.instructions:
                    response_parts.append(f"   💡 {exercise.instructions}")
            
            # Cool-down
            if workout_plan.cool_down:
                response_parts.append(f"\n🧘 **Cool-down ({sum(e.duration_minutes or 0 for e in workout_plan.cool_down)} min):**")
                for exercise in workout_plan.cool_down:
                    response_parts.append(f"  • {exercise.name}: {exercise.instructions}")
            
            # Coaching notes
            if workout_plan.coaching_notes:
                response_parts.append(f"\n👨‍🏫 **Coaching Notes:**")
                for note in workout_plan.coaching_notes:
                    response_parts.append(f"  • {note}")
            
            # Progression suggestions
            if workout_plan.progression_suggestions:
                response_parts.append(f"\n📈 **Next Steps:**")
                for suggestion in workout_plan.progression_suggestions[:2]:
                    response_parts.append(f"  • {suggestion}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error generating workout plan: {str(e)}"
    
    async def _get_recent_messages(self, user_id: str):
        """Get recent messages for semantic analysis."""
        try:
            from services.langchain_memory_service import langchain_memory_service
            memory_vars = await langchain_memory_service.get_memory_variables(user_id, "default")
            return memory_vars.get('chat_history', [])[-10:]
        except:
            return []


class BehavioralAnalysisTool(BaseTool):
    """Tool for analyzing user behavior and recommending psychology-based interventions."""
    
    name: str = "analyze_user_behavior"
    description: str = """
    Analyze user's behavioral patterns and psychology to provide personalized coaching.
    
    This tool provides:
    - Behavioral profile analysis (motivation type, personality, confidence)
    - Evidence-based intervention recommendations
    - Habit formation strategies
    - Personalized coaching approaches
    
    Use this when users need motivation, have adherence issues, or want behavioral insights.
    """
    args_schema: type = BehavioralAnalysisInput
    
    def _run(self, user_id: str, include_interventions: bool = True,
             current_challenges: List[str] = None) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(user_id, include_interventions, current_challenges or []))
    
    async def _arun(self, user_id: str, include_interventions: bool = True,
                   current_challenges: List[str] = None) -> str:
        """Analyze user behavior and provide recommendations."""
        try:
            # Get user data from semantic memory
            try:
                semantic_context = await semantic_memory_service.analyze_conversation_semantics(
                    user_id=user_id,
                    recent_messages=await self._get_recent_messages(user_id),
                    session_id="default"
                )
                
                conversation_summary = await semantic_memory_service.generate_conversation_summary(
                    user_id=user_id,
                    session_id="default"
                )
                
                # Prepare user data for analysis
                user_data = {
                    "primary_goals": semantic_context.user_goals,
                    "preferred_activities": semantic_context.preferred_activities,
                    "fitness_level": semantic_context.fitness_level or "intermediate",
                    "constraints": semantic_context.constraints,
                    "workout_consistency": 0.7,  # Would come from actual data
                    "recent_activities": []  # Would come from activity history
                }
                
                # Get conversation history for analysis
                memory_vars = await langchain_memory_service.get_memory_variables(user_id, "default")
                conversation_history = [
                    msg.content for msg in memory_vars.get('chat_history', [])
                    if hasattr(msg, 'content')
                ]
                
            except Exception as e:
                print(f"Warning: Could not get semantic context: {e}")
                user_data = {"fitness_level": "intermediate"}
                conversation_history = []
            
            # Analyze behavioral profile
            behavioral_profile = await behavioral_psychology_service.analyze_behavioral_profile(
                user_data=user_data,
                conversation_history=conversation_history
            )
            
            response_parts = []
            
            # Profile summary
            response_parts.append("🧠 **Behavioral Profile Analysis**")
            response_parts.append("=" * 35)
            
            response_parts.append(f"🎯 **Motivation Type:** {behavioral_profile.motivation_type.value.title()}")
            response_parts.append(f"👤 **Personality Type:** {behavioral_profile.personality_type.value.title()}")
            response_parts.append(f"📊 **Behavior Stage:** {behavioral_profile.behavior_stage.value.title()}")
            response_parts.append(f"💪 **Confidence Level:** {behavioral_profile.confidence_level:.0%}")
            
            # Psychological metrics
            response_parts.append(f"\n📈 **Psychological Profile:**")
            response_parts.append(f"  • Autonomy Preference: {behavioral_profile.autonomy_preference:.0%}")
            response_parts.append(f"  • Social Support Need: {behavioral_profile.social_support_need:.0%}")
            response_parts.append(f"  • Routine Preference: {behavioral_profile.routine_preference:.0%}")
            response_parts.append(f"  • Challenge Tolerance: {behavioral_profile.challenge_tolerance:.0%}")
            
            # Barriers and motivators
            if behavioral_profile.barriers:
                response_parts.append(f"\n⚠️ **Identified Barriers:**")
                for barrier in behavioral_profile.barriers:
                    response_parts.append(f"  • {barrier.replace('_', ' ').title()}")
            
            if behavioral_profile.motivators:
                response_parts.append(f"\n✨ **Key Motivators:**")
                for motivator in behavioral_profile.motivators:
                    response_parts.append(f"  • {motivator.replace('_', ' ').title()}")
            
            # Intervention recommendations
            if include_interventions:
                interventions = await behavioral_psychology_service.recommend_interventions(
                    behavioral_profile=behavioral_profile,
                    current_challenges=current_challenges or []
                )
                
                if interventions:
                    response_parts.append(f"\n🎯 **Recommended Interventions:**")
                    for intervention in interventions[:3]:  # Top 3 recommendations
                        response_parts.append(f"**{intervention.technique}**")
                        response_parts.append(f"  • {intervention.description}")
                        response_parts.append(f"  • Implementation: {intervention.implementation}")
                        response_parts.append(f"  • Expected outcome: {intervention.expected_outcome}")
                        response_parts.append("")
            
            # Coaching recommendations
            response_parts.append(f"💡 **Personalized Coaching Approach:**")
            
            if behavioral_profile.personality_type == PersonalityType.COMPETITOR:
                response_parts.append("  • Use challenges and competition to drive motivation")
                response_parts.append("  • Set performance-based goals with clear metrics")
            elif behavioral_profile.personality_type == PersonalityType.SOCIALIZER:
                response_parts.append("  • Incorporate social elements and community support")
                response_parts.append("  • Share achievements and progress with others")
            elif behavioral_profile.personality_type == PersonalityType.ACHIEVER:
                response_parts.append("  • Focus on goal-setting and progress tracking")
                response_parts.append("  • Celebrate milestones and achievements")
            elif behavioral_profile.personality_type == PersonalityType.EXPLORER:
                response_parts.append("  • Provide variety and new experiences")
                response_parts.append("  • Encourage experimentation with different activities")
            elif behavioral_profile.personality_type == PersonalityType.SUPPORTER:
                response_parts.append("  • Offer encouragement and emotional support")
                response_parts.append("  • Provide clear guidance and step-by-step plans")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error analyzing behavior: {str(e)}"
    
    async def _get_recent_messages(self, user_id: str):
        """Get recent messages for analysis."""
        try:
            from services.langchain_memory_service import langchain_memory_service
            memory_vars = await langchain_memory_service.get_memory_variables(user_id, "default")
            return memory_vars.get('chat_history', [])[-15:]
        except:
            return []


class MotivationalMessageTool(BaseTool):
    """Tool for generating personalized motivational messages."""
    
    name: str = "generate_motivational_message"
    description: str = """
    Generate personalized motivational messages based on user psychology.
    
    This tool creates messages that:
    - Match user's personality type and motivation style
    - Consider current context and mood
    - Apply behavioral psychology principles
    - Adapt to user's confidence level and preferences
    
    Use this for encouragement, pre/post workout motivation, or overcoming barriers.
    """
    args_schema: type = MotivationalMessageInput
    
    def _run(self, user_id: str, context: str = "general", 
             current_mood: Optional[str] = None) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(user_id, context, current_mood))
    
    async def _arun(self, user_id: str, context: str = "general",
                   current_mood: Optional[str] = None) -> str:
        """Generate personalized motivational message."""
        try:
            # Get user's behavioral profile
            try:
                semantic_context = await semantic_memory_service.analyze_conversation_semantics(
                    user_id=user_id,
                    recent_messages=await self._get_recent_messages(user_id),
                    session_id="default"
                )
                
                user_data = {
                    "primary_goals": semantic_context.user_goals,
                    "fitness_level": semantic_context.fitness_level or "intermediate",
                    "current_mood": current_mood or semantic_context.current_mood
                }
                
                memory_vars = await langchain_memory_service.get_memory_variables(user_id, "default")
                conversation_history = [
                    msg.content for msg in memory_vars.get('chat_history', [])
                    if hasattr(msg, 'content')
                ]
                
            except Exception as e:
                print(f"Warning: Could not get user context: {e}")
                user_data = {"fitness_level": "intermediate"}
                conversation_history = []
            
            # Analyze behavioral profile
            behavioral_profile = await behavioral_psychology_service.analyze_behavioral_profile(
                user_data=user_data,
                conversation_history=conversation_history
            )
            
            # Prepare context for message generation
            message_context = {}
            if context == "pre_workout":
                message_context["pre_workout"] = True
            elif context == "post_workout":
                message_context["post_workout"] = True
            elif context == "missed_workout":
                message_context["missed_workout"] = True
            
            if current_mood:
                message_context["mood"] = current_mood
            
            # Generate motivational message
            motivational_message = await behavioral_psychology_service.generate_motivational_message(
                behavioral_profile=behavioral_profile,
                context=message_context
            )
            
            # Format response
            response_parts = []
            
            response_parts.append(f"💪 **Personalized Motivation**")
            response_parts.append(f"🎯 Message Type: {motivational_message.message_type.title()}")
            response_parts.append(f"⏰ Context: {motivational_message.timing.replace('_', ' ').title()}")
            response_parts.append("")
            response_parts.append(f"✨ **{motivational_message.message}**")
            response_parts.append("")
            response_parts.append(f"🧠 Psychology: {motivational_message.psychological_principle.replace('_', ' ').title()}")
            
            if motivational_message.personalization_factors:
                factors_str = ", ".join(motivational_message.personalization_factors)
                response_parts.append(f"🎨 Personalized for: {factors_str.replace('_', ' ').title()}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error generating motivational message: {str(e)}"
    
    async def _get_recent_messages(self, user_id: str):
        """Get recent messages for analysis."""
        try:
            from services.langchain_memory_service import langchain_memory_service
            memory_vars = await langchain_memory_service.get_memory_variables(user_id, "default")
            return memory_vars.get('chat_history', [])[-10:]
        except:
            return []


class HabitFormationTool(BaseTool):
    """Tool for creating personalized habit formation plans."""
    
    name: str = "create_habit_plan"
    description: str = """
    Create a personalized habit formation plan using behavioral psychology.
    
    This tool provides:
    - Evidence-based habit formation strategies
    - Implementation intentions (if-then plans)
    - Cue-routine-reward loops
    - Personalized approach based on user psychology
    
    Use this when users want to build sustainable exercise habits.
    """
    args_schema: type = HabitFormationInput
    
    def _run(self, user_id: str, target_habit: str,
             current_barriers: List[str] = None) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(user_id, target_habit, current_barriers or []))
    
    async def _arun(self, user_id: str, target_habit: str,
                   current_barriers: List[str] = None) -> str:
        """Create personalized habit formation plan."""
        try:
            # Get user's behavioral profile
            try:
                semantic_context = await semantic_memory_service.analyze_conversation_semantics(
                    user_id=user_id,
                    recent_messages=await self._get_recent_messages(user_id),
                    session_id="default"
                )
                
                user_data = {
                    "primary_goals": semantic_context.user_goals,
                    "preferred_activities": semantic_context.preferred_activities,
                    "fitness_level": semantic_context.fitness_level or "intermediate",
                    "constraints": semantic_context.constraints
                }
                
                memory_vars = await langchain_memory_service.get_memory_variables(user_id, "default")
                conversation_history = [
                    msg.content for msg in memory_vars.get('chat_history', [])
                    if hasattr(msg, 'content')
                ]
                
            except Exception as e:
                print(f"Warning: Could not get user context: {e}")
                user_data = {"fitness_level": "intermediate"}
                conversation_history = []
            
            # Analyze behavioral profile
            behavioral_profile = await behavioral_psychology_service.analyze_behavioral_profile(
                user_data=user_data,
                conversation_history=conversation_history
            )
            
            # Create habit formation plan
            habit_plan = await behavioral_psychology_service.create_habit_formation_plan(
                behavioral_profile=behavioral_profile,
                target_behavior=target_habit
            )
            
            # Format response
            response_parts = []
            
            response_parts.append(f"🎯 **Habit Formation Plan**")
            response_parts.append(f"Target: {target_habit}")
            response_parts.append("=" * 40)
            
            response_parts.append(f"🧠 **Recommended Approach:**")
            response_parts.append(f"{habit_plan['recommended_approach'].replace('_', ' ').title()}")
            
            response_parts.append(f"\n📋 **Implementation Strategies:**")
            for strategy in habit_plan['implementation_strategies']:
                response_parts.append(f"  • {strategy}")
            
            response_parts.append(f"\n🔔 **Cue Suggestions:**")
            for cue in habit_plan['cue_suggestions']:
                response_parts.append(f"  • {cue}")
            
            response_parts.append(f"\n🎁 **Reward Suggestions:**")
            for reward in habit_plan['reward_suggestions']:
                response_parts.append(f"  • {reward}")
            
            # Add specific implementation intentions
            response_parts.append(f"\n⚡ **Implementation Intentions (If-Then Plans):**")
            
            if behavioral_profile.routine_preference > 0.6:
                response_parts.append(f"  • If it's [specific time], then I will {target_habit.lower()}")
                response_parts.append(f"  • If I finish [existing routine], then I will {target_habit.lower()}")
            else:
                response_parts.append(f"  • If I have free time, then I will {target_habit.lower()}")
                response_parts.append(f"  • If I feel energized, then I will {target_habit.lower()}")
            
            # Address barriers
            if current_barriers:
                response_parts.append(f"\n🚧 **Addressing Current Barriers:**")
                for barrier in current_barriers:
                    if barrier == "time":
                        response_parts.append("  • Start with minimum viable habit (5-10 minutes)")
                        response_parts.append("  • Use habit stacking with existing routines")
                    elif barrier == "motivation":
                        response_parts.append("  • Focus on identity-based habits ('I am someone who exercises')")
                        response_parts.append("  • Track small wins and celebrate progress")
                    elif barrier == "consistency":
                        response_parts.append("  • Never miss twice in a row")
                        response_parts.append("  • Have a 'minimum' version for difficult days")
            
            # Success tips
            response_parts.append(f"\n✅ **Success Tips:**")
            response_parts.append("  • Start smaller than you think you need to")
            response_parts.append("  • Focus on consistency over intensity")
            response_parts.append("  • Track your habit for at least 30 days")
            response_parts.append("  • Celebrate small wins along the way")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error creating habit formation plan: {str(e)}"
    
    async def _get_recent_messages(self, user_id: str):
        """Get recent messages for analysis."""
        try:
            from services.langchain_memory_service import langchain_memory_service
            memory_vars = await langchain_memory_service.get_memory_variables(user_id, "default")
            return memory_vars.get('chat_history', [])[-10:]
        except:
            return []


# Tool instances for use in agents
adaptive_workout_tool = AdaptiveWorkoutTool()
behavioral_analysis_tool = BehavioralAnalysisTool()
motivational_message_tool = MotivationalMessageTool()
habit_formation_tool = HabitFormationTool()

# Export list of all enhanced coach tools
enhanced_coach_tools = [
    adaptive_workout_tool,
    behavioral_analysis_tool,
    motivational_message_tool,
    habit_formation_tool
]
