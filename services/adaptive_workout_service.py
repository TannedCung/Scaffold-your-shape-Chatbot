"""Adaptive Workout Generation Service for Pili Coach Agent.

This service provides intelligent, personalized workout generation based on:
- User fitness goals and preferences
- Current fitness level and progress
- Available time and equipment constraints
- Historical performance data
- Behavioral psychology principles
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import random
from collections import defaultdict

from config.settings import get_configuration


class WorkoutType(Enum):
    """Types of workouts that can be generated."""
    CARDIO = "cardio"
    STRENGTH = "strength"
    HIIT = "hiit"
    YOGA = "yoga"
    FLEXIBILITY = "flexibility"
    SPORTS = "sports"
    RECOVERY = "recovery"
    MIXED = "mixed"


class IntensityLevel(Enum):
    """Workout intensity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FitnessGoal(Enum):
    """User fitness goals."""
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    GENERAL_FITNESS = "general_fitness"
    FLEXIBILITY = "flexibility"
    SPORT_SPECIFIC = "sport_specific"


@dataclass
class Exercise:
    """Individual exercise specification."""
    name: str
    type: str  # cardio, strength, flexibility, etc.
    muscle_groups: List[str] = field(default_factory=list)
    equipment_needed: List[str] = field(default_factory=list)
    duration_minutes: Optional[int] = None
    sets: Optional[int] = None
    reps: Optional[str] = None  # Can be range like "8-12"
    rest_seconds: Optional[int] = None
    intensity: IntensityLevel = IntensityLevel.MODERATE
    instructions: str = ""
    modifications: Dict[str, str] = field(default_factory=dict)  # beginner/advanced variations
    calories_per_minute: float = 5.0
    
    def __hash__(self):
        """Make Exercise hashable based on name and type."""
        return hash((self.name, self.type))
    
    def __eq__(self, other):
        """Equality based on name and type."""
        if not isinstance(other, Exercise):
            return False
        return self.name == other.name and self.type == other.type


@dataclass
class WorkoutPlan:
    """Complete workout plan specification."""
    name: str
    type: WorkoutType
    total_duration_minutes: int
    intensity: IntensityLevel
    exercises: List[Exercise]
    warm_up: List[Exercise] = field(default_factory=list)
    cool_down: List[Exercise] = field(default_factory=list)
    equipment_needed: List[str] = field(default_factory=list)
    target_goals: List[FitnessGoal] = field(default_factory=list)
    difficulty_level: str = "intermediate"
    estimated_calories: int = 0
    coaching_notes: List[str] = field(default_factory=list)
    progression_suggestions: List[str] = field(default_factory=list)


@dataclass
class UserFitnessProfile:
    """User's fitness profile for workout adaptation."""
    fitness_level: str = "intermediate"  # beginner, intermediate, advanced
    primary_goals: List[FitnessGoal] = field(default_factory=list)
    available_equipment: List[str] = field(default_factory=list)
    time_constraints: Dict[str, int] = field(default_factory=dict)  # max_duration, preferred_duration
    physical_limitations: List[str] = field(default_factory=list)
    preferred_activities: List[str] = field(default_factory=list)
    workout_frequency: int = 3  # times per week
    current_activity_level: str = "moderate"
    injury_history: List[str] = field(default_factory=list)
    motivation_level: str = "medium"  # low, medium, high


class AdaptiveWorkoutService:
    """Service for generating personalized, adaptive workouts."""
    
    def __init__(self):
        self.exercise_database = self._load_exercise_database()
        self.workout_templates = self._load_workout_templates()
        self.adaptation_rules = self._load_adaptation_rules()
        
    def _load_exercise_database(self) -> Dict[str, List[Exercise]]:
        """Load comprehensive exercise database organized by type."""
        return {
            "cardio": [
                Exercise(
                    name="Running",
                    type="cardio",
                    muscle_groups=["legs", "core"],
                    duration_minutes=30,
                    intensity=IntensityLevel.MODERATE,
                    instructions="Maintain steady pace, focus on breathing",
                    modifications={
                        "beginner": "Start with walk-run intervals",
                        "advanced": "Add hill intervals or speed work"
                    },
                    calories_per_minute=10.0
                ),
                Exercise(
                    name="Cycling",
                    type="cardio",
                    muscle_groups=["legs", "glutes"],
                    equipment_needed=["bike"],
                    duration_minutes=45,
                    intensity=IntensityLevel.MODERATE,
                    instructions="Keep steady cadence, adjust resistance as needed",
                    modifications={
                        "beginner": "Flat terrain, comfortable pace",
                        "advanced": "Hill climbs and interval training"
                    },
                    calories_per_minute=8.0
                ),
                Exercise(
                    name="Jump Rope",
                    type="cardio",
                    muscle_groups=["legs", "shoulders", "core"],
                    equipment_needed=["jump rope"],
                    duration_minutes=15,
                    intensity=IntensityLevel.HIGH,
                    instructions="Light on feet, maintain rhythm",
                    modifications={
                        "beginner": "30 seconds on, 30 seconds rest",
                        "advanced": "Double unders and complex patterns"
                    },
                    calories_per_minute=12.0
                )
            ],
            "strength": [
                Exercise(
                    name="Push-ups",
                    type="strength",
                    muscle_groups=["chest", "shoulders", "triceps", "core"],
                    sets=3,
                    reps="8-15",
                    rest_seconds=60,
                    intensity=IntensityLevel.MODERATE,
                    instructions="Keep body straight, full range of motion",
                    modifications={
                        "beginner": "Knee push-ups or wall push-ups",
                        "advanced": "Diamond push-ups or weighted push-ups"
                    },
                    calories_per_minute=6.0
                ),
                Exercise(
                    name="Squats",
                    type="strength",
                    muscle_groups=["quads", "glutes", "hamstrings", "core"],
                    sets=3,
                    reps="12-20",
                    rest_seconds=60,
                    intensity=IntensityLevel.MODERATE,
                    instructions="Feet shoulder-width apart, knees track over toes",
                    modifications={
                        "beginner": "Chair-assisted squats",
                        "advanced": "Jump squats or weighted squats"
                    },
                    calories_per_minute=7.0
                ),
                Exercise(
                    name="Deadlifts",
                    type="strength",
                    muscle_groups=["hamstrings", "glutes", "back", "core"],
                    equipment_needed=["weights"],
                    sets=3,
                    reps="6-10",
                    rest_seconds=90,
                    intensity=IntensityLevel.HIGH,
                    instructions="Keep back straight, hinge at hips",
                    modifications={
                        "beginner": "Romanian deadlifts with light weight",
                        "advanced": "Single-leg deadlifts or deficit deadlifts"
                    },
                    calories_per_minute=8.0
                )
            ],
            "hiit": [
                Exercise(
                    name="Burpees",
                    type="hiit",
                    muscle_groups=["full body"],
                    duration_minutes=1,
                    intensity=IntensityLevel.VERY_HIGH,
                    instructions="Explosive movement, maintain form under fatigue",
                    modifications={
                        "beginner": "Step back instead of jump back",
                        "advanced": "Add push-up and tuck jump"
                    },
                    calories_per_minute=15.0
                ),
                Exercise(
                    name="Mountain Climbers",
                    type="hiit",
                    muscle_groups=["core", "shoulders", "legs"],
                    duration_minutes=1,
                    intensity=IntensityLevel.HIGH,
                    instructions="Keep hips level, drive knees to chest",
                    modifications={
                        "beginner": "Slower pace, hands on elevated surface",
                        "advanced": "Cross-body mountain climbers"
                    },
                    calories_per_minute=12.0
                )
            ],
            "yoga": [
                Exercise(
                    name="Sun Salutation",
                    type="yoga",
                    muscle_groups=["full body"],
                    duration_minutes=10,
                    intensity=IntensityLevel.LOW,
                    instructions="Flow smoothly between poses, focus on breath",
                    modifications={
                        "beginner": "Hold poses longer, skip advanced transitions",
                        "advanced": "Add arm balances and deeper backbends"
                    },
                    calories_per_minute=3.0
                ),
                Exercise(
                    name="Warrior Sequence",
                    type="yoga",
                    muscle_groups=["legs", "core", "shoulders"],
                    duration_minutes=8,
                    intensity=IntensityLevel.LOW,
                    instructions="Hold poses for 5-8 breaths, maintain alignment",
                    modifications={
                        "beginner": "Use blocks for support",
                        "advanced": "Add twists and binds"
                    },
                    calories_per_minute=3.5
                )
            ],
            "flexibility": [
                Exercise(
                    name="Dynamic Stretching",
                    type="flexibility",
                    muscle_groups=["full body"],
                    duration_minutes=10,
                    intensity=IntensityLevel.LOW,
                    instructions="Controlled movements through range of motion",
                    modifications={
                        "beginner": "Smaller range of motion, slower pace",
                        "advanced": "Larger range, sport-specific movements"
                    },
                    calories_per_minute=2.0
                ),
                Exercise(
                    name="Static Stretching",
                    type="flexibility",
                    muscle_groups=["full body"],
                    duration_minutes=15,
                    intensity=IntensityLevel.LOW,
                    instructions="Hold stretches for 30-60 seconds, breathe deeply",
                    modifications={
                        "beginner": "Use props for support",
                        "advanced": "PNF stretching techniques"
                    },
                    calories_per_minute=1.5
                )
            ]
        }
    
    def _load_workout_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load workout templates for different goals and durations."""
        return {
            "weight_loss_30min": {
                "type": WorkoutType.HIIT,
                "structure": {
                    "warm_up": 5,
                    "main_work": 20,
                    "cool_down": 5
                },
                "exercise_types": ["hiit", "cardio"],
                "intensity_distribution": {
                    IntensityLevel.HIGH: 0.6,
                    IntensityLevel.MODERATE: 0.4
                }
            },
            "muscle_gain_45min": {
                "type": WorkoutType.STRENGTH,
                "structure": {
                    "warm_up": 5,
                    "main_work": 35,
                    "cool_down": 5
                },
                "exercise_types": ["strength"],
                "intensity_distribution": {
                    IntensityLevel.HIGH: 0.7,
                    IntensityLevel.MODERATE: 0.3
                }
            },
            "general_fitness_30min": {
                "type": WorkoutType.MIXED,
                "structure": {
                    "warm_up": 5,
                    "main_work": 20,
                    "cool_down": 5
                },
                "exercise_types": ["cardio", "strength", "flexibility"],
                "intensity_distribution": {
                    IntensityLevel.MODERATE: 0.7,
                    IntensityLevel.HIGH: 0.3
                }
            },
            "flexibility_20min": {
                "type": WorkoutType.YOGA,
                "structure": {
                    "warm_up": 3,
                    "main_work": 14,
                    "cool_down": 3
                },
                "exercise_types": ["yoga", "flexibility"],
                "intensity_distribution": {
                    IntensityLevel.LOW: 1.0
                }
            }
        }
    
    def _load_adaptation_rules(self) -> Dict[str, Any]:
        """Load rules for adapting workouts to user characteristics."""
        return {
            "fitness_level_adjustments": {
                "beginner": {
                    "intensity_multiplier": 0.7,
                    "duration_multiplier": 0.8,
                    "rest_multiplier": 1.5,
                    "complexity_reduction": True
                },
                "intermediate": {
                    "intensity_multiplier": 1.0,
                    "duration_multiplier": 1.0,
                    "rest_multiplier": 1.0,
                    "complexity_reduction": False
                },
                "advanced": {
                    "intensity_multiplier": 1.2,
                    "duration_multiplier": 1.1,
                    "rest_multiplier": 0.8,
                    "complexity_reduction": False
                }
            },
            "goal_priorities": {
                FitnessGoal.WEIGHT_LOSS: {
                    "cardio_weight": 0.4,
                    "hiit_weight": 0.4,
                    "strength_weight": 0.2,
                    "preferred_intensity": IntensityLevel.HIGH
                },
                FitnessGoal.MUSCLE_GAIN: {
                    "strength_weight": 0.7,
                    "cardio_weight": 0.1,
                    "hiit_weight": 0.2,
                    "preferred_intensity": IntensityLevel.HIGH
                },
                FitnessGoal.ENDURANCE: {
                    "cardio_weight": 0.6,
                    "hiit_weight": 0.3,
                    "strength_weight": 0.1,
                    "preferred_intensity": IntensityLevel.MODERATE
                },
                FitnessGoal.GENERAL_FITNESS: {
                    "cardio_weight": 0.3,
                    "strength_weight": 0.3,
                    "hiit_weight": 0.2,
                    "flexibility_weight": 0.2,
                    "preferred_intensity": IntensityLevel.MODERATE
                }
            },
            "equipment_substitutions": {
                "weights": ["resistance_bands", "bodyweight"],
                "bike": ["running", "jump_rope"],
                "gym": ["bodyweight", "minimal_equipment"]
            },
            "time_constraints": {
                15: {"focus": "hiit", "intensity": IntensityLevel.VERY_HIGH},
                30: {"focus": "mixed", "intensity": IntensityLevel.HIGH},
                45: {"focus": "comprehensive", "intensity": IntensityLevel.MODERATE},
                60: {"focus": "detailed", "intensity": IntensityLevel.MODERATE}
            }
        }
    
    async def generate_adaptive_workout(self, user_profile: UserFitnessProfile,
                                      workout_context: Optional[Dict[str, Any]] = None) -> WorkoutPlan:
        """
        Generate a personalized workout based on user profile and context.
        
        Args:
            user_profile: User's fitness profile and preferences
            workout_context: Additional context (recent workouts, mood, etc.)
            
        Returns:
            WorkoutPlan tailored to the user's needs
        """
        # Determine workout parameters
        workout_params = await self._determine_workout_parameters(user_profile, workout_context)
        
        # Select appropriate template
        template = await self._select_workout_template(workout_params)
        
        # Generate exercises
        exercises = await self._generate_exercises(template, workout_params, user_profile)
        
        # Create warm-up and cool-down
        warm_up = await self._generate_warm_up(workout_params, user_profile)
        cool_down = await self._generate_cool_down(workout_params, user_profile)
        
        # Adapt for user's fitness level
        adapted_exercises = await self._adapt_exercises_for_user(exercises, user_profile)
        
        # Calculate total duration and calories
        total_duration = sum([
            sum(e.duration_minutes or 0 for e in warm_up),
            sum(e.duration_minutes or (e.sets * 2) if e.sets else 0 for e in adapted_exercises),
            sum(e.duration_minutes or 0 for e in cool_down)
        ])
        
        estimated_calories = await self._calculate_estimated_calories(
            adapted_exercises + warm_up + cool_down, user_profile
        )
        
        # Generate coaching notes and progression suggestions
        coaching_notes = await self._generate_coaching_notes(workout_params, user_profile)
        progression_suggestions = await self._generate_progression_suggestions(
            adapted_exercises, user_profile
        )
        
        # Create final workout plan
        workout_plan = WorkoutPlan(
            name=await self._generate_workout_name(workout_params),
            type=template["type"],
            total_duration_minutes=total_duration,
            intensity=workout_params["intensity"],
            exercises=adapted_exercises,
            warm_up=warm_up,
            cool_down=cool_down,
            equipment_needed=list(set(
                eq for exercise in adapted_exercises + warm_up + cool_down
                for eq in exercise.equipment_needed
            )),
            target_goals=user_profile.primary_goals,
            difficulty_level=user_profile.fitness_level,
            estimated_calories=estimated_calories,
            coaching_notes=coaching_notes,
            progression_suggestions=progression_suggestions
        )
        
        return workout_plan
    
    async def _determine_workout_parameters(self, user_profile: UserFitnessProfile,
                                          workout_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Determine key workout parameters based on user profile and context."""
        params = {
            "duration": user_profile.time_constraints.get("preferred_duration", 30),
            "primary_goal": user_profile.primary_goals[0] if user_profile.primary_goals else FitnessGoal.GENERAL_FITNESS,
            "intensity": IntensityLevel.MODERATE,
            "equipment_available": user_profile.available_equipment,
            "fitness_level": user_profile.fitness_level
        }
        
        # Adjust based on context
        if workout_context:
            # Consider recent workout history
            if workout_context.get("recent_high_intensity"):
                params["intensity"] = IntensityLevel.LOW  # Recovery day
            elif workout_context.get("high_motivation"):
                params["intensity"] = IntensityLevel.HIGH
            
            # Consider time of day, energy level, etc.
            if workout_context.get("morning_workout"):
                params["include_energizing"] = True
            elif workout_context.get("evening_workout"):
                params["include_relaxing"] = True
        
        # Apply goal-based intensity preferences
        goal_rules = self.adaptation_rules["goal_priorities"].get(params["primary_goal"], {})
        if "preferred_intensity" in goal_rules:
            params["intensity"] = goal_rules["preferred_intensity"]
        
        return params
    
    async def _select_workout_template(self, workout_params: Dict[str, Any]) -> Dict[str, Any]:
        """Select the most appropriate workout template."""
        duration = workout_params["duration"]
        goal = workout_params["primary_goal"]
        
        # Create template key
        template_key = f"{goal.value}_{duration}min"
        
        # Try exact match first
        if template_key in self.workout_templates:
            return self.workout_templates[template_key]
        
        # Find closest match by duration and goal
        best_template = None
        best_score = float('inf')
        
        for template_name, template in self.workout_templates.items():
            # Parse template name (format: goal_duration)
            parts = template_name.split('_')
            if len(parts) >= 2:
                template_goal = parts[0]
                duration_part = parts[1]
                
                # Extract duration number
                try:
                    template_duration = int(duration_part.replace('min', ''))
                except ValueError:
                    # Skip templates with invalid duration format
                    continue
                
                # Calculate match score
                goal_match = 1.0 if template_goal == goal.value else 0.5
                duration_diff = abs(template_duration - duration) / duration
                score = duration_diff + (1 - goal_match)
                
                if score < best_score:
                    best_score = score
                    best_template = template
        
        return best_template or self.workout_templates["general_fitness_30min"]
    
    async def _generate_exercises(self, template: Dict[str, Any], 
                                workout_params: Dict[str, Any],
                                user_profile: UserFitnessProfile) -> List[Exercise]:
        """Generate main workout exercises based on template and parameters."""
        exercises = []
        main_work_duration = template["structure"]["main_work"]
        exercise_types = template["exercise_types"]
        
        # Calculate how many exercises we need
        target_exercise_count = max(3, main_work_duration // 8)  # Roughly 8 minutes per exercise
        
        # Get exercises from each type
        available_exercises = []
        for exercise_type in exercise_types:
            type_exercises = self.exercise_database.get(exercise_type, [])
            # Filter by equipment availability
            filtered_exercises = [
                ex for ex in type_exercises
                if not ex.equipment_needed or 
                any(eq in user_profile.available_equipment for eq in ex.equipment_needed) or
                not user_profile.available_equipment  # If no equipment specified, include all
            ]
            available_exercises.extend(filtered_exercises)
        
        # Remove duplicates and shuffle
        available_exercises = list(set(available_exercises))
        random.shuffle(available_exercises)
        
        # Select exercises ensuring variety
        selected_exercises = []
        used_muscle_groups = set()
        
        for exercise in available_exercises:
            if len(selected_exercises) >= target_exercise_count:
                break
            
            # Check for muscle group overlap (avoid too much repetition)
            overlap = set(exercise.muscle_groups) & used_muscle_groups
            if len(overlap) < len(exercise.muscle_groups) // 2 or len(selected_exercises) < 2:
                selected_exercises.append(exercise)
                used_muscle_groups.update(exercise.muscle_groups)
        
        # Ensure we have enough exercises
        while len(selected_exercises) < target_exercise_count and available_exercises:
            remaining = [ex for ex in available_exercises if ex not in selected_exercises]
            if remaining:
                selected_exercises.append(random.choice(remaining))
            else:
                break
        
        return selected_exercises[:target_exercise_count]
    
    async def _generate_warm_up(self, workout_params: Dict[str, Any],
                              user_profile: UserFitnessProfile) -> List[Exercise]:
        """Generate appropriate warm-up exercises."""
        warm_up_exercises = [
            Exercise(
                name="Dynamic Warm-up",
                type="flexibility",
                muscle_groups=["full body"],
                duration_minutes=workout_params.get("warm_up_duration", 5),
                intensity=IntensityLevel.LOW,
                instructions="Gradually increase heart rate and mobility",
                calories_per_minute=3.0
            )
        ]
        return warm_up_exercises
    
    async def _generate_cool_down(self, workout_params: Dict[str, Any],
                                user_profile: UserFitnessProfile) -> List[Exercise]:
        """Generate appropriate cool-down exercises."""
        cool_down_exercises = [
            Exercise(
                name="Cool-down Stretching",
                type="flexibility",
                muscle_groups=["full body"],
                duration_minutes=workout_params.get("cool_down_duration", 5),
                intensity=IntensityLevel.LOW,
                instructions="Focus on muscles worked during main workout",
                calories_per_minute=2.0
            )
        ]
        return cool_down_exercises
    
    async def _adapt_exercises_for_user(self, exercises: List[Exercise],
                                      user_profile: UserFitnessProfile) -> List[Exercise]:
        """Adapt exercises based on user's fitness level and limitations."""
        adapted_exercises = []
        
        fitness_adjustments = self.adaptation_rules["fitness_level_adjustments"][user_profile.fitness_level]
        
        for exercise in exercises:
            adapted_exercise = Exercise(
                name=exercise.name,
                type=exercise.type,
                muscle_groups=exercise.muscle_groups.copy(),
                equipment_needed=exercise.equipment_needed.copy(),
                duration_minutes=exercise.duration_minutes,
                sets=exercise.sets,
                reps=exercise.reps,
                rest_seconds=exercise.rest_seconds,
                intensity=exercise.intensity,
                instructions=exercise.instructions,
                modifications=exercise.modifications.copy(),
                calories_per_minute=exercise.calories_per_minute
            )
            
            # Apply fitness level adjustments
            if adapted_exercise.duration_minutes:
                adapted_exercise.duration_minutes = int(
                    adapted_exercise.duration_minutes * fitness_adjustments["duration_multiplier"]
                )
            
            if adapted_exercise.rest_seconds:
                adapted_exercise.rest_seconds = int(
                    adapted_exercise.rest_seconds * fitness_adjustments["rest_multiplier"]
                )
            
            # Apply modifications based on fitness level
            if user_profile.fitness_level in adapted_exercise.modifications:
                adapted_exercise.instructions += f" ({adapted_exercise.modifications[user_profile.fitness_level]})"
            
            adapted_exercises.append(adapted_exercise)
        
        return adapted_exercises
    
    async def _calculate_estimated_calories(self, exercises: List[Exercise],
                                          user_profile: UserFitnessProfile) -> int:
        """Calculate estimated calories burned for the workout."""
        total_calories = 0
        
        for exercise in exercises:
            if exercise.duration_minutes:
                calories = exercise.duration_minutes * exercise.calories_per_minute
            elif exercise.sets:
                # Estimate duration for strength exercises
                estimated_minutes = exercise.sets * 2  # 2 minutes per set average
                calories = estimated_minutes * exercise.calories_per_minute
            else:
                calories = 10 * exercise.calories_per_minute  # Default 10 minutes
            
            total_calories += calories
        
        # Adjust for fitness level (more fit = more efficient = fewer calories)
        fitness_multipliers = {"beginner": 1.2, "intermediate": 1.0, "advanced": 0.9}
        multiplier = fitness_multipliers.get(user_profile.fitness_level, 1.0)
        
        return int(total_calories * multiplier)
    
    async def _generate_coaching_notes(self, workout_params: Dict[str, Any],
                                     user_profile: UserFitnessProfile) -> List[str]:
        """Generate personalized coaching notes."""
        notes = []
        
        # Goal-specific notes
        primary_goal = workout_params["primary_goal"]
        if primary_goal == FitnessGoal.WEIGHT_LOSS:
            notes.append("Focus on maintaining intensity to maximize calorie burn")
            notes.append("Remember, consistency is key for weight loss results")
        elif primary_goal == FitnessGoal.MUSCLE_GAIN:
            notes.append("Focus on proper form and progressive overload")
            notes.append("Rest adequately between sets to maintain strength")
        elif primary_goal == FitnessGoal.ENDURANCE:
            notes.append("Pace yourself to maintain steady effort throughout")
            notes.append("Focus on breathing rhythm and efficient movement")
        
        # Fitness level specific notes
        if user_profile.fitness_level == "beginner":
            notes.append("Listen to your body and rest when needed")
            notes.append("Focus on learning proper form before increasing intensity")
        elif user_profile.fitness_level == "advanced":
            notes.append("Challenge yourself while maintaining perfect form")
            notes.append("Consider adding complexity or resistance as you progress")
        
        # Motivation level adjustments
        if user_profile.motivation_level == "low":
            notes.append("Remember why you started - every workout counts!")
            notes.append("Celebrate small wins and progress made")
        elif user_profile.motivation_level == "high":
            notes.append("Great energy! Channel it into focused, quality movement")
        
        return notes
    
    async def _generate_progression_suggestions(self, exercises: List[Exercise],
                                              user_profile: UserFitnessProfile) -> List[str]:
        """Generate suggestions for workout progression."""
        suggestions = []
        
        # General progression principles
        suggestions.append("Increase intensity by 5-10% when current level feels easy")
        
        # Exercise-specific progressions
        has_strength = any(ex.type == "strength" for ex in exercises)
        has_cardio = any(ex.type == "cardio" for ex in exercises)
        
        if has_strength:
            suggestions.append("For strength exercises: add reps, sets, or resistance")
        
        if has_cardio:
            suggestions.append("For cardio: increase duration, speed, or add intervals")
        
        # Time-based progressions
        if user_profile.time_constraints.get("preferred_duration", 30) < 45:
            suggestions.append("Try extending workout duration by 5 minutes next week")
        
        # Frequency progressions
        if user_profile.workout_frequency < 4:
            suggestions.append("Consider adding one more workout day per week")
        
        return suggestions
    
    async def _generate_workout_name(self, workout_params: Dict[str, Any]) -> str:
        """Generate a descriptive name for the workout."""
        goal = workout_params["primary_goal"].value.replace("_", " ").title()
        duration = workout_params["duration"]
        intensity = workout_params["intensity"].value.title()
        
        name_templates = [
            f"{duration}-min {goal} {intensity} Workout",
            f"{intensity} {goal} Session ({duration} min)",
            f"Power {duration}: {goal} Focus"
        ]
        
        return random.choice(name_templates)


# Global service instance
adaptive_workout_service = AdaptiveWorkoutService()
