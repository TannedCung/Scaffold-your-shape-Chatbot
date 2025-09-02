"""Smart Activity Validation Service for Pili Logger Agent.

This service provides intelligent validation, enhancement, and analysis
of user activity data to improve data quality and user experience.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from config.settings import get_configuration


class ActivityType(Enum):
    """Supported activity types with validation rules."""
    RUNNING = "running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    WALKING = "walking"
    STRENGTH = "strength"
    YOGA = "yoga"
    CARDIO = "cardio"
    SPORTS = "sports"
    OTHER = "other"


class ValidationLevel(Enum):
    """Validation confidence levels."""
    HIGH = "high"      # >90% confidence
    MEDIUM = "medium"  # 70-90% confidence
    LOW = "low"        # 50-70% confidence
    FAILED = "failed"  # <50% confidence


@dataclass
class ValidationIssue:
    """Represents a validation concern."""
    field: str
    issue_type: str
    message: str
    severity: str  # "error", "warning", "info"
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of activity validation."""
    is_valid: bool
    confidence: float
    validation_level: ValidationLevel
    issues: List[ValidationIssue] = field(default_factory=list)
    enhanced_data: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


class ActivityValidationService:
    """Service for validating and enhancing activity data."""
    
    def __init__(self):
        self.activity_patterns = self._load_activity_patterns()
        self.validation_rules = self._load_validation_rules()
        self.unit_conversions = self._load_unit_conversions()
        
    def _load_activity_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load activity recognition patterns."""
        return {
            "running": {
                "keywords": ["run", "jog", "sprint", "marathon", "5k", "10k"],
                "units": ["km", "miles", "minutes", "hours"],
                "typical_duration": (15, 300),  # 15 minutes to 5 hours
                "typical_distance": (1, 50),    # 1-50 km
                "pace_range": (3, 15),          # 3-15 min/km
            },
            "cycling": {
                "keywords": ["bike", "cycle", "cycling", "ride", "bicycle"],
                "units": ["km", "miles", "minutes", "hours"],
                "typical_duration": (20, 480),  # 20 minutes to 8 hours
                "typical_distance": (5, 200),   # 5-200 km
                "pace_range": (1, 5),           # 1-5 min/km
            },
            "swimming": {
                "keywords": ["swim", "pool", "laps", "freestyle", "backstroke"],
                "units": ["meters", "laps", "minutes", "hours"],
                "typical_duration": (15, 120),  # 15 minutes to 2 hours
                "typical_distance": (100, 5000), # 100m to 5km
            },
            "strength": {
                "keywords": ["lift", "weights", "gym", "bench", "squat", "deadlift", "reps", "sets"],
                "units": ["kg", "lbs", "reps", "sets"],
                "typical_duration": (20, 120),  # 20 minutes to 2 hours
            },
            "yoga": {
                "keywords": ["yoga", "meditation", "stretch", "flexibility", "poses"],
                "units": ["minutes", "hours"],
                "typical_duration": (15, 90),   # 15-90 minutes
            }
        }
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for different activity types."""
        return {
            "distance_speed_consistency": {
                "running": {"min_pace": 3, "max_pace": 15},  # min/km
                "cycling": {"min_pace": 1, "max_pace": 5},
                "walking": {"min_pace": 8, "max_pace": 20},
            },
            "duration_limits": {
                "max_daily_duration": 720,  # 12 hours max per day
                "min_activity_duration": 1,  # 1 minute minimum
            },
            "frequency_patterns": {
                "max_activities_per_day": 10,
                "unusual_frequency_threshold": 5,
            }
        }
    
    def _load_unit_conversions(self) -> Dict[str, Dict[str, float]]:
        """Load unit conversion factors."""
        return {
            "distance": {
                "km_to_miles": 0.621371,
                "miles_to_km": 1.60934,
                "meters_to_km": 0.001,
                "km_to_meters": 1000,
            },
            "weight": {
                "kg_to_lbs": 2.20462,
                "lbs_to_kg": 0.453592,
            }
        }
    
    async def validate_activity(self, activity_data: Dict[str, Any], 
                              user_profile: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate activity data with intelligent analysis.
        
        Args:
            activity_data: Raw activity data from user input
            user_profile: User's fitness profile and history
            
        Returns:
            ValidationResult with confidence score and issues
        """
        issues = []
        enhanced_data = activity_data.copy()
        suggestions = []
        confidence = 1.0
        
        # Step 1: Activity Type Recognition
        activity_type = await self._recognize_activity_type(activity_data)
        if activity_type:
            enhanced_data["recognized_type"] = activity_type.value
            enhanced_data["type_confidence"] = enhanced_data.get("type_confidence", 0.8)
        else:
            issues.append(ValidationIssue(
                field="type",
                issue_type="recognition_failed",
                message="Could not recognize activity type",
                severity="warning",
                suggestion="Please specify the type of activity (running, cycling, etc.)"
            ))
            confidence *= 0.7
        
        # Step 2: Data Completeness Check
        completeness_score = await self._check_data_completeness(activity_data)
        confidence *= completeness_score
        
        if completeness_score < 0.8:
            missing_fields = await self._identify_missing_fields(activity_data, activity_type)
            for field in missing_fields:
                issues.append(ValidationIssue(
                    field=field,
                    issue_type="missing_data",
                    message=f"Missing {field} information",
                    severity="info",
                    suggestion=f"Consider adding {field} for better tracking"
                ))
        
        # Step 3: Value Range Validation
        range_validation = await self._validate_value_ranges(activity_data, activity_type)
        confidence *= range_validation["confidence"]
        issues.extend(range_validation["issues"])
        
        # Step 4: Consistency Checks
        consistency_result = await self._check_data_consistency(activity_data, activity_type)
        confidence *= consistency_result["confidence"]
        issues.extend(consistency_result["issues"])
        
        # Step 5: Historical Pattern Analysis
        if user_profile:
            pattern_analysis = await self._analyze_historical_patterns(
                activity_data, user_profile
            )
            confidence *= pattern_analysis["confidence"]
            issues.extend(pattern_analysis["issues"])
            suggestions.extend(pattern_analysis["suggestions"])
        
        # Step 6: Data Enhancement
        enhanced_data.update(await self._enhance_activity_data(activity_data, activity_type))
        
        # Determine validation level
        validation_level = self._determine_validation_level(confidence)
        
        return ValidationResult(
            is_valid=confidence >= 0.5,
            confidence=confidence,
            validation_level=validation_level,
            issues=issues,
            enhanced_data=enhanced_data,
            suggestions=suggestions
        )
    
    async def _recognize_activity_type(self, activity_data: Dict[str, Any]) -> Optional[ActivityType]:
        """Recognize activity type from data using NLP and pattern matching."""
        text_content = " ".join([
            str(activity_data.get("name", "")),
            str(activity_data.get("notes", "")),
            str(activity_data.get("description", ""))
        ]).lower()
        
        # Score each activity type
        type_scores = {}
        
        for activity_name, patterns in self.activity_patterns.items():
            score = 0
            
            # Keyword matching
            for keyword in patterns["keywords"]:
                if keyword in text_content:
                    score += 1
            
            # Unit matching
            for unit in patterns.get("units", []):
                if unit in text_content or unit in str(activity_data.get("unit", "")):
                    score += 0.5
            
            if score > 0:
                type_scores[activity_name] = score
        
        # Return highest scoring type if above threshold
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            if type_scores[best_type] >= 1:  # Minimum confidence threshold
                return ActivityType(best_type)
        
        return None
    
    async def _check_data_completeness(self, activity_data: Dict[str, Any]) -> float:
        """Check how complete the activity data is."""
        required_fields = ["name", "type", "date"]
        optional_fields = ["value", "unit", "duration", "notes", "location"]
        
        required_score = sum(1 for field in required_fields 
                           if activity_data.get(field))
        optional_score = sum(0.5 for field in optional_fields 
                           if activity_data.get(field))
        
        total_possible = len(required_fields) + len(optional_fields) * 0.5
        actual_score = required_score + optional_score
        
        return min(actual_score / total_possible, 1.0)
    
    async def _identify_missing_fields(self, activity_data: Dict[str, Any], 
                                     activity_type: Optional[ActivityType]) -> List[str]:
        """Identify missing fields based on activity type."""
        missing = []
        
        # Common missing fields
        if not activity_data.get("duration") and not activity_data.get("value"):
            missing.append("duration or distance")
        
        if activity_type in [ActivityType.RUNNING, ActivityType.CYCLING, ActivityType.SWIMMING]:
            if not activity_data.get("value"):
                missing.append("distance")
        
        if activity_type == ActivityType.STRENGTH:
            if not activity_data.get("notes"):
                missing.append("exercise details (sets/reps/weight)")
        
        return missing
    
    async def _validate_value_ranges(self, activity_data: Dict[str, Any], 
                                   activity_type: Optional[ActivityType]) -> Dict[str, Any]:
        """Validate that values are within reasonable ranges."""
        issues = []
        confidence = 1.0
        
        if not activity_type:
            return {"confidence": confidence, "issues": issues}
        
        patterns = self.activity_patterns.get(activity_type.value, {})
        
        # Duration validation
        duration = activity_data.get("duration")
        if duration:
            duration_minutes = self._parse_duration_to_minutes(duration)
            if duration_minutes:
                duration_range = patterns.get("typical_duration", (1, 480))
                if not (duration_range[0] <= duration_minutes <= duration_range[1]):
                    severity = "warning" if duration_minutes > 0 else "error"
                    issues.append(ValidationIssue(
                        field="duration",
                        issue_type="unusual_value",
                        message=f"Duration of {duration_minutes} minutes seems unusual for {activity_type.value}",
                        severity=severity,
                        suggestion=f"Typical range: {duration_range[0]}-{duration_range[1]} minutes"
                    ))
                    confidence *= 0.8
        
        # Distance validation
        distance = activity_data.get("value")
        if distance and activity_data.get("unit") in ["km", "miles", "meters"]:
            distance_km = self._convert_to_km(distance, activity_data.get("unit", "km"))
            if distance_km:
                distance_range = patterns.get("typical_distance", (0.1, 100))
                if not (distance_range[0] <= distance_km <= distance_range[1]):
                    issues.append(ValidationIssue(
                        field="distance",
                        issue_type="unusual_value",
                        message=f"Distance of {distance_km:.1f}km seems unusual for {activity_type.value}",
                        severity="warning",
                        suggestion=f"Typical range: {distance_range[0]}-{distance_range[1]}km"
                    ))
                    confidence *= 0.8
        
        return {"confidence": confidence, "issues": issues}
    
    async def _check_data_consistency(self, activity_data: Dict[str, Any], 
                                    activity_type: Optional[ActivityType]) -> Dict[str, Any]:
        """Check internal consistency of the data."""
        issues = []
        confidence = 1.0
        
        # Check distance/duration consistency
        distance = activity_data.get("value")
        duration = activity_data.get("duration")
        
        if distance and duration and activity_type:
            distance_km = self._convert_to_km(distance, activity_data.get("unit", "km"))
            duration_minutes = self._parse_duration_to_minutes(duration)
            
            if distance_km and duration_minutes and duration_minutes > 0:
                pace_min_per_km = duration_minutes / distance_km
                
                # Check if pace is reasonable
                patterns = self.activity_patterns.get(activity_type.value, {})
                pace_range = patterns.get("pace_range")
                
                if pace_range and not (pace_range[0] <= pace_min_per_km <= pace_range[1]):
                    issues.append(ValidationIssue(
                        field="pace",
                        issue_type="inconsistent_data",
                        message=f"Calculated pace ({pace_min_per_km:.1f} min/km) seems unusual",
                        severity="warning",
                        suggestion=f"Expected pace range: {pace_range[0]}-{pace_range[1]} min/km"
                    ))
                    confidence *= 0.7
        
        return {"confidence": confidence, "issues": issues}
    
    async def _analyze_historical_patterns(self, activity_data: Dict[str, Any], 
                                         user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze activity against user's historical patterns."""
        issues = []
        suggestions = []
        confidence = 1.0
        
        # This would integrate with user's historical data
        # For now, we'll implement basic pattern recognition
        
        # Check for unusual frequency
        activity_date = activity_data.get("date", datetime.now().isoformat())
        # In a real implementation, we'd check against recent activities
        
        # Placeholder for historical analysis
        suggestions.append("Great job staying active! Keep up the consistency.")
        
        return {
            "confidence": confidence,
            "issues": issues,
            "suggestions": suggestions
        }
    
    async def _enhance_activity_data(self, activity_data: Dict[str, Any], 
                                   activity_type: Optional[ActivityType]) -> Dict[str, Any]:
        """Enhance activity data with derived metrics and standardization."""
        enhanced = {}
        
        # Standardize units
        if activity_data.get("value") and activity_data.get("unit"):
            enhanced["standardized_distance_km"] = self._convert_to_km(
                activity_data["value"], activity_data["unit"]
            )
        
        # Calculate derived metrics
        distance_km = enhanced.get("standardized_distance_km")
        duration = activity_data.get("duration")
        duration_minutes = self._parse_duration_to_minutes(duration) if duration else None
        
        if distance_km and duration_minutes and duration_minutes > 0:
            enhanced["pace_min_per_km"] = duration_minutes / distance_km
            enhanced["speed_kmh"] = (distance_km / duration_minutes) * 60
        
        # Add activity category
        if activity_type:
            enhanced["category"] = self._get_activity_category(activity_type)
        
        # Add estimated calories (basic calculation)
        if duration_minutes:
            enhanced["estimated_calories"] = self._estimate_calories(
                activity_type, duration_minutes, distance_km
            )
        
        return enhanced
    
    def _parse_duration_to_minutes(self, duration: Any) -> Optional[float]:
        """Parse duration string to minutes."""
        if isinstance(duration, (int, float)):
            return float(duration)
        
        if isinstance(duration, str):
            # Handle various formats: "30", "30min", "1h30m", "1:30"
            duration = duration.lower().strip()
            
            # Simple number (assume minutes)
            if duration.isdigit():
                return float(duration)
            
            # Hours and minutes: "1h30m" or "1:30"
            if "h" in duration or ":" in duration:
                hours = 0
                minutes = 0
                
                if "h" in duration:
                    parts = duration.split("h")
                    hours = float(parts[0]) if parts[0] else 0
                    if len(parts) > 1 and parts[1]:
                        minutes = float(parts[1].replace("m", "")) if parts[1].replace("m", "") else 0
                elif ":" in duration:
                    parts = duration.split(":")
                    hours = float(parts[0]) if len(parts) > 0 else 0
                    minutes = float(parts[1]) if len(parts) > 1 else 0
                
                return hours * 60 + minutes
            
            # Just minutes: "30min" or "30m"
            if "min" in duration or "m" in duration:
                return float(re.sub(r'[^\d.]', '', duration))
        
        return None
    
    def _convert_to_km(self, value: Any, unit: str) -> Optional[float]:
        """Convert distance to kilometers."""
        try:
            value = float(value)
            unit = unit.lower()
            
            if unit in ["km", "kilometers"]:
                return value
            elif unit in ["miles", "mi"]:
                return value * self.unit_conversions["distance"]["miles_to_km"]
            elif unit in ["meters", "m"]:
                return value * self.unit_conversions["distance"]["meters_to_km"]
            else:
                return value  # Assume km if unknown
        except (ValueError, TypeError):
            return None
    
    def _get_activity_category(self, activity_type: ActivityType) -> str:
        """Get broad category for activity type."""
        categories = {
            ActivityType.RUNNING: "cardio",
            ActivityType.CYCLING: "cardio",
            ActivityType.SWIMMING: "cardio",
            ActivityType.WALKING: "cardio",
            ActivityType.STRENGTH: "strength",
            ActivityType.YOGA: "flexibility",
            ActivityType.CARDIO: "cardio",
            ActivityType.SPORTS: "sports",
            ActivityType.OTHER: "other"
        }
        return categories.get(activity_type, "other")
    
    def _estimate_calories(self, activity_type: Optional[ActivityType], 
                          duration_minutes: float, distance_km: Optional[float] = None) -> int:
        """Estimate calories burned (basic calculation)."""
        if not activity_type:
            return int(duration_minutes * 5)  # Basic estimate
        
        # Basic MET values (metabolic equivalent)
        met_values = {
            ActivityType.RUNNING: 10,
            ActivityType.CYCLING: 8,
            ActivityType.SWIMMING: 11,
            ActivityType.WALKING: 4,
            ActivityType.STRENGTH: 6,
            ActivityType.YOGA: 3,
            ActivityType.CARDIO: 7,
            ActivityType.SPORTS: 8,
            ActivityType.OTHER: 5
        }
        
        met = met_values.get(activity_type, 5)
        # Assuming average weight of 70kg for basic calculation
        calories = int((met * 70 * duration_minutes) / 60)
        
        return calories
    
    def _determine_validation_level(self, confidence: float) -> ValidationLevel:
        """Determine validation level based on confidence score."""
        if confidence >= 0.9:
            return ValidationLevel.HIGH
        elif confidence >= 0.7:
            return ValidationLevel.MEDIUM
        elif confidence >= 0.5:
            return ValidationLevel.LOW
        else:
            return ValidationLevel.FAILED


# Global service instance
activity_validation_service = ActivityValidationService()
