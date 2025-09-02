"""Behavioral Psychology Service for Pili Coach Agent.

This service applies behavioral psychology principles to improve user
motivation, adherence, and long-term fitness success through:
- Habit formation strategies
- Motivation enhancement techniques  
- Behavioral change interventions
- Personalized coaching approaches
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import random
from collections import defaultdict

from config.settings import get_configuration


class MotivationType(Enum):
    """Types of motivation based on Self-Determination Theory."""
    INTRINSIC = "intrinsic"  # Internal satisfaction, enjoyment
    IDENTIFIED = "identified"  # Personal goals and values
    INTROJECTED = "introjected"  # Guilt, shame, ego
    EXTERNAL = "external"  # Rewards, punishments


class BehaviorStage(Enum):
    """Stages of behavior change (Transtheoretical Model)."""
    PRECONTEMPLATION = "precontemplation"
    CONTEMPLATION = "contemplation" 
    PREPARATION = "preparation"
    ACTION = "action"
    MAINTENANCE = "maintenance"
    RELAPSE = "relapse"


class PersonalityType(Enum):
    """Simplified personality types for coaching adaptation."""
    COMPETITOR = "competitor"  # Thrives on challenges and competition
    SOCIALIZER = "socializer"  # Motivated by social connection
    ACHIEVER = "achiever"     # Goal-oriented, progress-focused
    EXPLORER = "explorer"     # Enjoys variety and new experiences
    SUPPORTER = "supporter"   # Needs encouragement and guidance


@dataclass
class BehavioralProfile:
    """User's behavioral and psychological profile."""
    motivation_type: MotivationType = MotivationType.IDENTIFIED
    behavior_stage: BehaviorStage = BehaviorStage.ACTION
    personality_type: PersonalityType = PersonalityType.ACHIEVER
    confidence_level: float = 0.7  # 0-1 scale
    autonomy_preference: float = 0.5  # 0-1 scale (low = needs guidance, high = independent)
    social_support_need: float = 0.5  # 0-1 scale
    routine_preference: float = 0.6  # 0-1 scale (low = variety, high = consistency)
    challenge_tolerance: float = 0.6  # 0-1 scale
    feedback_sensitivity: float = 0.5  # 0-1 scale
    past_adherence_rate: float = 0.6  # Historical adherence percentage
    barriers: List[str] = field(default_factory=list)
    motivators: List[str] = field(default_factory=list)
    preferred_rewards: List[str] = field(default_factory=list)


@dataclass
class BehavioralIntervention:
    """Specific behavioral intervention recommendation."""
    technique: str
    description: str
    implementation: str
    expected_outcome: str
    duration_weeks: int
    success_metrics: List[str]
    personalization_notes: str = ""


@dataclass
class MotivationalMessage:
    """Personalized motivational message."""
    message: str
    message_type: str  # encouragement, challenge, reminder, celebration
    timing: str  # pre_workout, post_workout, rest_day, milestone
    psychological_principle: str
    personalization_factors: List[str]


class BehavioralPsychologyService:
    """Service for applying behavioral psychology to fitness coaching."""
    
    def __init__(self):
        self.intervention_strategies = self._load_intervention_strategies()
        self.motivational_frameworks = self._load_motivational_frameworks()
        self.habit_formation_rules = self._load_habit_formation_rules()
        
    def _load_intervention_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load evidence-based behavioral intervention strategies."""
        return {
            "goal_setting": {
                "SMART_goals": {
                    "description": "Specific, Measurable, Achievable, Relevant, Time-bound goals",
                    "implementation": "Break down large goals into smaller, specific milestones",
                    "best_for": [PersonalityType.ACHIEVER, PersonalityType.COMPETITOR],
                    "effectiveness": 0.85
                },
                "process_goals": {
                    "description": "Focus on behaviors rather than outcomes",
                    "implementation": "Set goals like 'exercise 3x per week' vs 'lose 10 pounds'",
                    "best_for": [PersonalityType.SUPPORTER, PersonalityType.SOCIALIZER],
                    "effectiveness": 0.78
                }
            },
            "self_monitoring": {
                "activity_tracking": {
                    "description": "Regular logging of exercise activities",
                    "implementation": "Use app or journal to track workouts daily",
                    "best_for": [PersonalityType.ACHIEVER],
                    "effectiveness": 0.82
                },
                "mood_tracking": {
                    "description": "Monitor emotional responses to exercise",
                    "implementation": "Rate mood before/after workouts on 1-10 scale",
                    "best_for": [PersonalityType.EXPLORER, PersonalityType.SUPPORTER],
                    "effectiveness": 0.75
                }
            },
            "social_support": {
                "workout_buddy": {
                    "description": "Exercise with a partner for accountability",
                    "implementation": "Schedule regular workout sessions with friend/family",
                    "best_for": [PersonalityType.SOCIALIZER],
                    "effectiveness": 0.88
                },
                "online_community": {
                    "description": "Join virtual fitness groups for support",
                    "implementation": "Participate in online challenges and share progress",
                    "best_for": [PersonalityType.SOCIALIZER, PersonalityType.COMPETITOR],
                    "effectiveness": 0.72
                }
            },
            "environmental_design": {
                "cue_modification": {
                    "description": "Modify environment to trigger exercise behavior",
                    "implementation": "Lay out workout clothes night before, set up home gym space",
                    "best_for": "all_types",
                    "effectiveness": 0.79
                },
                "barrier_removal": {
                    "description": "Eliminate obstacles to exercise",
                    "implementation": "Choose gym close to home/work, prep workout gear in advance",
                    "best_for": "all_types", 
                    "effectiveness": 0.83
                }
            },
            "reward_systems": {
                "intrinsic_rewards": {
                    "description": "Focus on internal satisfaction and enjoyment",
                    "implementation": "Celebrate feelings of strength, energy, accomplishment",
                    "best_for": [PersonalityType.EXPLORER, PersonalityType.ACHIEVER],
                    "effectiveness": 0.86
                },
                "external_rewards": {
                    "description": "Use external incentives for motivation",
                    "implementation": "Reward workout milestones with non-food treats",
                    "best_for": [PersonalityType.COMPETITOR],
                    "effectiveness": 0.65  # Lower long-term effectiveness
                }
            }
        }
    
    def _load_motivational_frameworks(self) -> Dict[str, Any]:
        """Load motivational messaging frameworks."""
        return {
            "self_determination_theory": {
                "autonomy": {
                    "high_autonomy": [
                        "You have the power to choose your path to fitness",
                        "Trust your body and make decisions that feel right for you",
                        "You're in control of your fitness journey"
                    ],
                    "low_autonomy": [
                        "I'm here to guide you through each step",
                        "Let's work together to find what works best for you",
                        "Following this plan will help you reach your goals"
                    ]
                },
                "competence": {
                    "building": [
                        "You're getting stronger with every workout",
                        "Notice how much easier that felt than last week",
                        "Your form is improving - you should be proud"
                    ],
                    "challenging": [
                        "You're ready for the next level",
                        "I believe you can handle this challenge",
                        "Time to show yourself what you're capable of"
                    ]
                },
                "relatedness": {
                    "connection": [
                        "You're part of a community of people working toward better health",
                        "Many others have walked this path and succeeded",
                        "I'm here to support you every step of the way"
                    ]
                }
            },
            "personality_based": {
                PersonalityType.COMPETITOR: [
                    "Can you beat your personal record today?",
                    "You're stronger than your excuses",
                    "Champions are made in moments like this"
                ],
                PersonalityType.SOCIALIZER: [
                    "Your workout buddy is counting on you",
                    "Share your success with others who care about you",
                    "You inspire others when you show up"
                ],
                PersonalityType.ACHIEVER: [
                    "Every workout gets you closer to your goal",
                    "Progress is progress, no matter how small",
                    "You're building the life you want, one workout at a time"
                ],
                PersonalityType.EXPLORER: [
                    "Today's workout is a chance to discover something new about yourself",
                    "Every exercise is an experiment in what your body can do",
                    "Adventure awaits in this workout"
                ],
                PersonalityType.SUPPORTER: [
                    "You deserve to feel strong and healthy",
                    "Taking care of yourself helps you take care of others",
                    "You're worth the time and effort this takes"
                ]
            }
        }
    
    def _load_habit_formation_rules(self) -> Dict[str, Any]:
        """Load rules for effective habit formation."""
        return {
            "habit_loop": {
                "cue": "Environmental or internal trigger",
                "routine": "The behavior itself",
                "reward": "Positive outcome that reinforces behavior"
            },
            "implementation_intentions": {
                "format": "If [situation], then I will [behavior]",
                "examples": [
                    "If it's 7 AM on weekdays, then I will do my morning workout",
                    "If I feel stressed, then I will take a 10-minute walk",
                    "If I finish work, then I will go to the gym"
                ]
            },
            "habit_stacking": {
                "format": "After [existing habit], I will [new habit]",
                "examples": [
                    "After I brush my teeth, I will do 10 pushups",
                    "After I eat lunch, I will take a 5-minute walk",
                    "After I check my morning emails, I will review my workout plan"
                ]
            },
            "minimum_viable_habits": {
                "principle": "Start with the smallest possible version",
                "examples": [
                    "1 pushup instead of a full workout",
                    "Put on workout clothes instead of full exercise routine",
                    "Walk to the gym instead of full workout"
                ]
            }
        }
    
    async def analyze_behavioral_profile(self, user_data: Dict[str, Any],
                                       conversation_history: List[str] = None) -> BehavioralProfile:
        """
        Analyze user data to create behavioral profile.
        
        Args:
            user_data: User information including goals, preferences, history
            conversation_history: Recent conversation messages for analysis
            
        Returns:
            BehavioralProfile with psychological insights
        """
        profile = BehavioralProfile()
        
        # Analyze motivation type
        profile.motivation_type = await self._assess_motivation_type(user_data, conversation_history)
        
        # Determine behavior stage
        profile.behavior_stage = await self._assess_behavior_stage(user_data)
        
        # Identify personality type
        profile.personality_type = await self._assess_personality_type(user_data, conversation_history)
        
        # Calculate psychological metrics
        profile.confidence_level = await self._assess_confidence(user_data)
        profile.autonomy_preference = await self._assess_autonomy_preference(user_data, conversation_history)
        profile.social_support_need = await self._assess_social_support_need(user_data, conversation_history)
        profile.routine_preference = await self._assess_routine_preference(user_data)
        profile.challenge_tolerance = await self._assess_challenge_tolerance(user_data)
        
        # Identify barriers and motivators
        profile.barriers = await self._identify_barriers(user_data, conversation_history)
        profile.motivators = await self._identify_motivators(user_data, conversation_history)
        
        return profile
    
    async def _assess_motivation_type(self, user_data: Dict[str, Any], 
                                    conversation_history: List[str]) -> MotivationType:
        """Assess user's primary motivation type."""
        # Look for intrinsic motivation indicators
        intrinsic_keywords = ["enjoy", "fun", "love", "feel good", "energized", "strong"]
        identified_keywords = ["goal", "health", "important", "value", "meaningful"]
        external_keywords = ["reward", "competition", "others", "appearance", "impress"]
        
        text_to_analyze = " ".join(conversation_history or []).lower()
        
        intrinsic_score = sum(1 for keyword in intrinsic_keywords if keyword in text_to_analyze)
        identified_score = sum(1 for keyword in identified_keywords if keyword in text_to_analyze)
        external_score = sum(1 for keyword in external_keywords if keyword in text_to_analyze)
        
        if intrinsic_score >= max(identified_score, external_score):
            return MotivationType.INTRINSIC
        elif identified_score >= external_score:
            return MotivationType.IDENTIFIED
        else:
            return MotivationType.EXTERNAL
    
    async def _assess_behavior_stage(self, user_data: Dict[str, Any]) -> BehaviorStage:
        """Assess user's stage in behavior change process."""
        activity_history = user_data.get("recent_activities", [])
        consistency = user_data.get("workout_consistency", 0.5)
        
        if not activity_history:
            return BehaviorStage.PREPARATION
        elif len(activity_history) < 10:  # Less than ~3 weeks of activity
            return BehaviorStage.ACTION
        elif consistency >= 0.8:
            return BehaviorStage.MAINTENANCE
        elif consistency < 0.3:
            return BehaviorStage.RELAPSE
        else:
            return BehaviorStage.ACTION
    
    async def _assess_personality_type(self, user_data: Dict[str, Any],
                                     conversation_history: List[str]) -> PersonalityType:
        """Assess user's fitness personality type."""
        text_to_analyze = " ".join(conversation_history or []).lower()
        
        # Score each personality type
        competitor_score = sum(1 for word in ["compete", "challenge", "beat", "win", "record"] 
                              if word in text_to_analyze)
        socializer_score = sum(1 for word in ["friend", "group", "together", "partner", "share"]
                              if word in text_to_analyze)
        achiever_score = sum(1 for word in ["goal", "progress", "achieve", "accomplish", "target"]
                            if word in text_to_analyze)
        explorer_score = sum(1 for word in ["new", "different", "try", "variety", "explore"]
                            if word in text_to_analyze)
        supporter_score = sum(1 for word in ["help", "support", "guide", "encourage", "difficult"]
                             if word in text_to_analyze)
        
        scores = {
            PersonalityType.COMPETITOR: competitor_score,
            PersonalityType.SOCIALIZER: socializer_score,
            PersonalityType.ACHIEVER: achiever_score,
            PersonalityType.EXPLORER: explorer_score,
            PersonalityType.SUPPORTER: supporter_score
        }
        
        return max(scores, key=scores.get) or PersonalityType.ACHIEVER
    
    async def _assess_confidence(self, user_data: Dict[str, Any]) -> float:
        """Assess user's confidence level (0-1)."""
        fitness_level = user_data.get("fitness_level", "intermediate")
        past_success = user_data.get("past_adherence_rate", 0.5)
        
        base_confidence = {"beginner": 0.4, "intermediate": 0.6, "advanced": 0.8}.get(fitness_level, 0.6)
        
        # Adjust based on past success
        confidence = base_confidence + (past_success - 0.5) * 0.4
        
        return max(0.1, min(1.0, confidence))
    
    async def _assess_autonomy_preference(self, user_data: Dict[str, Any],
                                        conversation_history: List[str]) -> float:
        """Assess user's preference for autonomy vs guidance."""
        text_to_analyze = " ".join(conversation_history or []).lower()
        
        autonomy_indicators = ["decide", "choose", "control", "flexible", "customize"]
        guidance_indicators = ["help", "tell me", "guide", "plan for me", "what should"]
        
        autonomy_score = sum(1 for word in autonomy_indicators if word in text_to_analyze)
        guidance_score = sum(1 for word in guidance_indicators if word in text_to_analyze)
        
        if autonomy_score + guidance_score == 0:
            return 0.5  # Default middle ground
        
        return autonomy_score / (autonomy_score + guidance_score)
    
    async def _assess_social_support_need(self, user_data: Dict[str, Any],
                                         conversation_history: List[str]) -> float:
        """Assess user's need for social support."""
        text_to_analyze = " ".join(conversation_history or []).lower()
        
        social_indicators = ["lonely", "together", "friend", "partner", "group", "community", "support"]
        independent_indicators = ["alone", "myself", "independent", "solo", "private"]
        
        social_score = sum(1 for word in social_indicators if word in text_to_analyze)
        independent_score = sum(1 for word in independent_indicators if word in text_to_analyze)
        
        if social_score + independent_score == 0:
            return 0.5
        
        return social_score / (social_score + independent_score)
    
    async def _assess_routine_preference(self, user_data: Dict[str, Any]) -> float:
        """Assess user's preference for routine vs variety."""
        activity_variety = len(set(user_data.get("preferred_activities", [])))
        
        # More variety = lower routine preference
        if activity_variety >= 4:
            return 0.3  # Loves variety
        elif activity_variety <= 1:
            return 0.8  # Prefers routine
        else:
            return 0.5  # Balanced
    
    async def _assess_challenge_tolerance(self, user_data: Dict[str, Any]) -> float:
        """Assess user's tolerance for challenging workouts."""
        fitness_level = user_data.get("fitness_level", "intermediate")
        past_intensity = user_data.get("preferred_intensity", "moderate")
        
        base_tolerance = {"beginner": 0.4, "intermediate": 0.6, "advanced": 0.8}.get(fitness_level, 0.6)
        
        intensity_adjustment = {"low": -0.2, "moderate": 0, "high": 0.2, "very_high": 0.3}.get(past_intensity, 0)
        
        return max(0.1, min(1.0, base_tolerance + intensity_adjustment))
    
    async def _identify_barriers(self, user_data: Dict[str, Any],
                               conversation_history: List[str]) -> List[str]:
        """Identify potential barriers to exercise adherence."""
        barriers = []
        
        # Common barriers from user data
        if user_data.get("time_constraints", {}).get("max_duration", 60) < 30:
            barriers.append("time_constraints")
        
        if not user_data.get("available_equipment"):
            barriers.append("equipment_access")
        
        # Barriers from conversation
        if conversation_history:
            text = " ".join(conversation_history).lower()
            
            if any(word in text for word in ["busy", "time", "schedule"]):
                barriers.append("time_management")
            
            if any(word in text for word in ["tired", "energy", "exhausted"]):
                barriers.append("low_energy")
            
            if any(word in text for word in ["boring", "monotonous", "same"]):
                barriers.append("lack_of_variety")
            
            if any(word in text for word in ["difficult", "hard", "challenging"]):
                barriers.append("perceived_difficulty")
        
        return barriers
    
    async def _identify_motivators(self, user_data: Dict[str, Any],
                                 conversation_history: List[str]) -> List[str]:
        """Identify key motivators for the user."""
        motivators = []
        
        # Goal-based motivators
        goals = user_data.get("primary_goals", [])
        for goal in goals:
            if goal == "weight_loss":
                motivators.append("health_improvement")
            elif goal == "muscle_gain":
                motivators.append("strength_building")
            elif goal == "endurance":
                motivators.append("performance_enhancement")
        
        # Conversation-based motivators
        if conversation_history:
            text = " ".join(conversation_history).lower()
            
            if any(word in text for word in ["feel good", "energy", "mood"]):
                motivators.append("mood_enhancement")
            
            if any(word in text for word in ["strong", "powerful", "capable"]):
                motivators.append("empowerment")
            
            if any(word in text for word in ["health", "healthy", "wellness"]):
                motivators.append("health_focus")
        
        return motivators
    
    async def recommend_interventions(self, behavioral_profile: BehavioralProfile,
                                    current_challenges: List[str] = None) -> List[BehavioralIntervention]:
        """Recommend specific behavioral interventions based on profile."""
        interventions = []
        
        # Goal setting interventions
        if behavioral_profile.personality_type in [PersonalityType.ACHIEVER, PersonalityType.COMPETITOR]:
            interventions.append(BehavioralIntervention(
                technique="SMART Goal Setting",
                description="Create specific, measurable fitness goals",
                implementation="Set weekly and monthly targets with clear metrics",
                expected_outcome="Increased motivation and progress tracking",
                duration_weeks=4,
                success_metrics=["goal_achievement_rate", "workout_consistency"],
                personalization_notes=f"Tailored for {behavioral_profile.personality_type.value} personality"
            ))
        
        # Social support interventions
        if behavioral_profile.social_support_need > 0.6:
            interventions.append(BehavioralIntervention(
                technique="Social Accountability",
                description="Engage workout partner or fitness community",
                implementation="Schedule regular check-ins and shared activities",
                expected_outcome="Improved adherence through social connection",
                duration_weeks=8,
                success_metrics=["workout_attendance", "social_engagement"],
                personalization_notes="High social support need identified"
            ))
        
        # Habit formation interventions
        if behavioral_profile.behavior_stage == BehaviorStage.ACTION:
            interventions.append(BehavioralIntervention(
                technique="Implementation Intentions",
                description="Create if-then plans for workout execution",
                implementation="Define specific cues and responses for exercise",
                expected_outcome="Automated exercise behavior",
                duration_weeks=6,
                success_metrics=["habit_strength", "consistency_score"],
                personalization_notes="Focus on building sustainable routines"
            ))
        
        # Confidence building interventions
        if behavioral_profile.confidence_level < 0.5:
            interventions.append(BehavioralIntervention(
                technique="Mastery Experiences",
                description="Design achievable challenges to build confidence",
                implementation="Start with easier workouts and gradually progress",
                expected_outcome="Increased self-efficacy and motivation",
                duration_weeks=6,
                success_metrics=["confidence_rating", "workout_completion"],
                personalization_notes="Building confidence through success experiences"
            ))
        
        return interventions
    
    async def generate_motivational_message(self, behavioral_profile: BehavioralProfile,
                                          context: Dict[str, Any] = None) -> MotivationalMessage:
        """Generate personalized motivational message."""
        context = context or {}
        
        # Select appropriate message framework
        personality_messages = self.motivational_frameworks["personality_based"][behavioral_profile.personality_type]
        
        # Choose message based on context
        if context.get("pre_workout"):
            message_type = "encouragement"
            timing = "pre_workout"
        elif context.get("post_workout"):
            message_type = "celebration"
            timing = "post_workout"
        elif context.get("missed_workout"):
            message_type = "reminder"
            timing = "rest_day"
        else:
            message_type = "encouragement"
            timing = "general"
        
        # Select appropriate message
        base_message = random.choice(personality_messages)
        
        # Personalize based on profile
        personalization_factors = []
        
        if behavioral_profile.confidence_level < 0.5:
            base_message += " You're stronger than you think!"
            personalization_factors.append("confidence_building")
        
        if behavioral_profile.autonomy_preference > 0.7:
            base_message = f"Remember, {base_message.lower()}"
            personalization_factors.append("autonomy_support")
        
        return MotivationalMessage(
            message=base_message,
            message_type=message_type,
            timing=timing,
            psychological_principle=f"{behavioral_profile.personality_type.value}_motivation",
            personalization_factors=personalization_factors
        )
    
    async def create_habit_formation_plan(self, behavioral_profile: BehavioralProfile,
                                        target_behavior: str) -> Dict[str, Any]:
        """Create a personalized habit formation plan."""
        plan = {
            "target_behavior": target_behavior,
            "personality_type": behavioral_profile.personality_type.value,
            "recommended_approach": None,
            "implementation_strategies": [],
            "cue_suggestions": [],
            "reward_suggestions": [],
            "tracking_method": None
        }
        
        # Choose approach based on personality
        if behavioral_profile.personality_type == PersonalityType.ACHIEVER:
            plan["recommended_approach"] = "goal_oriented_habit_stacking"
            plan["implementation_strategies"] = [
                "Link new habit to existing routine",
                "Set measurable milestones",
                "Track progress visually"
            ]
        elif behavioral_profile.personality_type == PersonalityType.SOCIALIZER:
            plan["recommended_approach"] = "social_accountability_system"
            plan["implementation_strategies"] = [
                "Find workout buddy or group",
                "Share progress publicly",
                "Create social rewards"
            ]
        elif behavioral_profile.personality_type == PersonalityType.EXPLORER:
            plan["recommended_approach"] = "variety_based_habit_formation"
            plan["implementation_strategies"] = [
                "Build habit around exploration, not specific activities",
                "Create activity rotation schedule",
                "Track variety and new experiences"
            ]
        elif behavioral_profile.personality_type == PersonalityType.COMPETITOR:
            plan["recommended_approach"] = "challenge_based_habit_building"
            plan["implementation_strategies"] = [
                "Set progressive challenges",
                "Track personal records",
                "Create competitive elements"
            ]
        elif behavioral_profile.personality_type == PersonalityType.SUPPORTER:
            plan["recommended_approach"] = "supportive_habit_guidance"
            plan["implementation_strategies"] = [
                "Start with minimal viable habits",
                "Provide clear step-by-step guidance",
                "Focus on self-care motivation"
            ]
        else:
            plan["recommended_approach"] = "balanced_habit_formation"
            plan["implementation_strategies"] = [
                "Combine structure with flexibility",
                "Use multiple motivation sources",
                "Adapt approach based on progress"
            ]
        
        # Suggest cues based on routine preference
        if behavioral_profile.routine_preference > 0.6:
            plan["cue_suggestions"] = [
                "Same time every day",
                "Specific location setup",
                "Consistent pre-workout routine"
            ]
        else:
            plan["cue_suggestions"] = [
                "Flexible time windows",
                "Multiple location options",
                "Variety in approach"
            ]
        
        # Suggest rewards based on motivation type
        if behavioral_profile.motivation_type == MotivationType.INTRINSIC:
            plan["reward_suggestions"] = [
                "Focus on how good you feel",
                "Celebrate strength gains",
                "Enjoy the process"
            ]
        else:
            plan["reward_suggestions"] = [
                "Non-food treats after milestones",
                "Progress photos and measurements",
                "Social recognition"
            ]
        
        return plan


# Global service instance
behavioral_psychology_service = BehavioralPsychologyService()
