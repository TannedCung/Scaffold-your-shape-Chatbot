"""Advanced Activity Data Extraction Service for Pili Logger Agent.

This service provides intelligent extraction and parsing of activity data
from natural language input using NLP techniques and pattern matching.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from config.settings import get_configuration


class ExtractionConfidence(Enum):
    """Confidence levels for extracted data."""
    HIGH = "high"      # >90% confidence
    MEDIUM = "medium"  # 70-90% confidence
    LOW = "low"        # 50-70% confidence
    UNCERTAIN = "uncertain"  # <50% confidence


@dataclass
class ExtractedField:
    """Represents an extracted data field."""
    field_name: str
    value: Any
    confidence: float
    source_text: str
    extraction_method: str


@dataclass
class ExtractionResult:
    """Result of activity data extraction."""
    extracted_fields: List[ExtractedField]
    structured_data: Dict[str, Any]
    confidence_score: float
    missing_fields: List[str]
    suggestions: List[str]


class ActivityExtractionService:
    """Service for extracting structured activity data from natural language."""
    
    def __init__(self):
        self.patterns = self._load_extraction_patterns()
        self.time_patterns = self._load_time_patterns()
        self.unit_patterns = self._load_unit_patterns()
        
    def _load_extraction_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load regex patterns for extracting different types of data."""
        return {
            "distance": [
                {
                    "pattern": r"(\d+(?:\.\d+)?)\s*(km|kilometers?|k)\b",
                    "unit": "km",
                    "confidence": 0.95
                },
                {
                    "pattern": r"(\d+(?:\.\d+)?)\s*(miles?|mi)\b",
                    "unit": "miles",
                    "confidence": 0.95
                },
                {
                    "pattern": r"(\d+(?:\.\d+)?)\s*(meters?|m)\b",
                    "unit": "meters",
                    "confidence": 0.9
                },
                {
                    "pattern": r"(\d+)\s*k\b",  # "5k run"
                    "unit": "km",
                    "confidence": 0.85
                }
            ],
            "duration": [
                {
                    "pattern": r"(\d+)\s*hours?\s*(?:and\s*)?(\d+)?\s*(?:minutes?|mins?|m)\b",
                    "format": "hours_minutes",
                    "confidence": 0.95
                },
                {
                    "pattern": r"(\d+):(\d+)(?::(\d+))?",  # HH:MM or HH:MM:SS
                    "format": "time_format",
                    "confidence": 0.9
                },
                {
                    "pattern": r"(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)\b",
                    "format": "minutes",
                    "confidence": 0.85
                },
                {
                    "pattern": r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b",
                    "format": "hours",
                    "confidence": 0.85
                }
            ],
            "repetitions": [
                {
                    "pattern": r"(\d+)\s*(?:reps?|repetitions?)\b",
                    "confidence": 0.9
                },
                {
                    "pattern": r"(\d+)\s*x\s*(\d+)",  # "3x10" format
                    "format": "sets_reps",
                    "confidence": 0.85
                }
            ],
            "weight": [
                {
                    "pattern": r"(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)\b",
                    "unit": "kg",
                    "confidence": 0.95
                },
                {
                    "pattern": r"(\d+(?:\.\d+)?)\s*(?:lbs?|pounds?)\b",
                    "unit": "lbs",
                    "confidence": 0.95
                }
            ],
            "activity_type": [
                {
                    "pattern": r"\b(ran|running|jog|jogging)\b",
                    "type": "running",
                    "confidence": 0.9
                },
                {
                    "pattern": r"\b(cycl|bike|biking|bicycle)\b",
                    "type": "cycling",
                    "confidence": 0.9
                },
                {
                    "pattern": r"\b(swim|swimming)\b",
                    "type": "swimming",
                    "confidence": 0.9
                },
                {
                    "pattern": r"\b(walk|walking)\b",
                    "type": "walking",
                    "confidence": 0.85
                },
                {
                    "pattern": r"\b(lift|lifting|weights?|gym)\b",
                    "type": "strength",
                    "confidence": 0.8
                },
                {
                    "pattern": r"\b(yoga|stretch|stretching)\b",
                    "type": "yoga",
                    "confidence": 0.85
                }
            ]
        }
    
    def _load_time_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load patterns for extracting time/date information."""
        return {
            "relative_time": [
                {
                    "pattern": r"\b(today|this morning|this afternoon|this evening)\b",
                    "offset": 0,
                    "confidence": 0.9
                },
                {
                    "pattern": r"\b(yesterday|last night)\b",
                    "offset": -1,
                    "confidence": 0.9
                },
                {
                    "pattern": r"\b(\d+)\s*days?\s*ago\b",
                    "offset": "days_ago",
                    "confidence": 0.85
                }
            ],
            "specific_time": [
                {
                    "pattern": r"\bat\s*(\d+):(\d+)\s*(am|pm)?\b",
                    "format": "time_12h",
                    "confidence": 0.9
                },
                {
                    "pattern": r"\b(\d+):(\d+)\b",
                    "format": "time_24h",
                    "confidence": 0.8
                }
            ]
        }
    
    def _load_unit_patterns(self) -> Dict[str, str]:
        """Load unit standardization patterns."""
        return {
            "km": ["km", "kilometers", "k"],
            "miles": ["miles", "mi"],
            "meters": ["meters", "m"],
            "kg": ["kg", "kilograms"],
            "lbs": ["lbs", "pounds"],
            "minutes": ["minutes", "mins", "min", "m"],
            "hours": ["hours", "hrs", "h"]
        }
    
    async def extract_activity_data(self, text: str, 
                                  context: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        """
        Extract structured activity data from natural language text.
        
        Args:
            text: Natural language description of activity
            context: Additional context (user profile, previous activities, etc.)
            
        Returns:
            ExtractionResult with extracted fields and structured data
        """
        text_lower = text.lower()
        extracted_fields = []
        structured_data = {}
        missing_fields = []
        suggestions = []
        
        # Extract activity type
        activity_type = await self._extract_activity_type(text_lower)
        if activity_type:
            extracted_fields.append(activity_type)
            structured_data["type"] = activity_type.value
        else:
            missing_fields.append("activity_type")
            suggestions.append("Please specify what type of activity you did (running, cycling, etc.)")
        
        # Extract distance
        distance = await self._extract_distance(text_lower)
        if distance:
            extracted_fields.append(distance)
            structured_data["value"] = distance.value["distance"]
            structured_data["unit"] = distance.value["unit"]
        
        # Extract duration
        duration = await self._extract_duration(text_lower)
        if duration:
            extracted_fields.append(duration)
            structured_data["duration"] = duration.value
        
        # Extract repetitions/sets (for strength training)
        reps = await self._extract_repetitions(text_lower)
        if reps:
            extracted_fields.append(reps)
            if "notes" not in structured_data:
                structured_data["notes"] = ""
            structured_data["notes"] += f" {reps.value}"
        
        # Extract weight
        weight = await self._extract_weight(text_lower)
        if weight:
            extracted_fields.append(weight)
            if "notes" not in structured_data:
                structured_data["notes"] = ""
            structured_data["notes"] += f" {weight.value['weight']} {weight.value['unit']}"
        
        # Extract time/date
        time_info = await self._extract_time_information(text_lower)
        if time_info:
            extracted_fields.append(time_info)
            structured_data["date"] = time_info.value
        else:
            # Default to current time
            structured_data["date"] = datetime.now().isoformat()
        
        # Extract location
        location = await self._extract_location(text_lower)
        if location:
            extracted_fields.append(location)
            structured_data["location"] = location.value
        
        # Generate activity name
        activity_name = await self._generate_activity_name(structured_data, text)
        structured_data["name"] = activity_name
        
        # Extract additional notes
        notes = await self._extract_additional_notes(text, structured_data)
        if notes:
            structured_data["notes"] = structured_data.get("notes", "") + " " + notes
        
        # Calculate overall confidence
        confidence_score = self._calculate_overall_confidence(extracted_fields)
        
        # Identify missing critical fields
        missing_fields.extend(await self._identify_missing_critical_fields(structured_data))
        
        # Generate suggestions for improvement
        suggestions.extend(await self._generate_improvement_suggestions(
            structured_data, missing_fields, confidence_score
        ))
        
        return ExtractionResult(
            extracted_fields=extracted_fields,
            structured_data=structured_data,
            confidence_score=confidence_score,
            missing_fields=missing_fields,
            suggestions=suggestions
        )
    
    async def _extract_activity_type(self, text: str) -> Optional[ExtractedField]:
        """Extract activity type from text."""
        for pattern_info in self.patterns["activity_type"]:
            match = re.search(pattern_info["pattern"], text, re.IGNORECASE)
            if match:
                return ExtractedField(
                    field_name="activity_type",
                    value=pattern_info["type"],
                    confidence=pattern_info["confidence"],
                    source_text=match.group(0),
                    extraction_method="regex_pattern"
                )
        return None
    
    async def _extract_distance(self, text: str) -> Optional[ExtractedField]:
        """Extract distance information from text."""
        for pattern_info in self.patterns["distance"]:
            match = re.search(pattern_info["pattern"], text, re.IGNORECASE)
            if match:
                distance_value = float(match.group(1))
                return ExtractedField(
                    field_name="distance",
                    value={
                        "distance": distance_value,
                        "unit": pattern_info["unit"]
                    },
                    confidence=pattern_info["confidence"],
                    source_text=match.group(0),
                    extraction_method="regex_pattern"
                )
        return None
    
    async def _extract_duration(self, text: str) -> Optional[ExtractedField]:
        """Extract duration information from text."""
        for pattern_info in self.patterns["duration"]:
            match = re.search(pattern_info["pattern"], text, re.IGNORECASE)
            if match:
                duration_minutes = self._parse_duration_match(match, pattern_info["format"])
                if duration_minutes:
                    return ExtractedField(
                        field_name="duration",
                        value=duration_minutes,
                        confidence=pattern_info["confidence"],
                        source_text=match.group(0),
                        extraction_method="regex_pattern"
                    )
        return None
    
    async def _extract_repetitions(self, text: str) -> Optional[ExtractedField]:
        """Extract repetition/sets information from text."""
        for pattern_info in self.patterns["repetitions"]:
            match = re.search(pattern_info["pattern"], text, re.IGNORECASE)
            if match:
                if pattern_info.get("format") == "sets_reps":
                    sets = int(match.group(1))
                    reps = int(match.group(2))
                    value = f"{sets} sets x {reps} reps"
                else:
                    reps = int(match.group(1))
                    value = f"{reps} reps"
                
                return ExtractedField(
                    field_name="repetitions",
                    value=value,
                    confidence=pattern_info["confidence"],
                    source_text=match.group(0),
                    extraction_method="regex_pattern"
                )
        return None
    
    async def _extract_weight(self, text: str) -> Optional[ExtractedField]:
        """Extract weight information from text."""
        for pattern_info in self.patterns["weight"]:
            match = re.search(pattern_info["pattern"], text, re.IGNORECASE)
            if match:
                weight_value = float(match.group(1))
                return ExtractedField(
                    field_name="weight",
                    value={
                        "weight": weight_value,
                        "unit": pattern_info["unit"]
                    },
                    confidence=pattern_info["confidence"],
                    source_text=match.group(0),
                    extraction_method="regex_pattern"
                )
        return None
    
    async def _extract_time_information(self, text: str) -> Optional[ExtractedField]:
        """Extract time/date information from text."""
        # Check for relative time first
        for pattern_info in self.time_patterns["relative_time"]:
            match = re.search(pattern_info["pattern"], text, re.IGNORECASE)
            if match:
                if pattern_info["offset"] == "days_ago":
                    days_ago = int(match.group(1))
                    date = datetime.now() - timedelta(days=days_ago)
                else:
                    date = datetime.now() + timedelta(days=pattern_info["offset"])
                
                return ExtractedField(
                    field_name="date",
                    value=date.isoformat(),
                    confidence=pattern_info["confidence"],
                    source_text=match.group(0),
                    extraction_method="relative_time_pattern"
                )
        
        # Check for specific time
        for pattern_info in self.time_patterns["specific_time"]:
            match = re.search(pattern_info["pattern"], text, re.IGNORECASE)
            if match:
                # For now, assume today with the specified time
                today = datetime.now().date()
                hour = int(match.group(1))
                minute = int(match.group(2))
                
                # Handle AM/PM if present
                if len(match.groups()) > 2 and match.group(3):
                    if match.group(3).lower() == "pm" and hour < 12:
                        hour += 12
                    elif match.group(3).lower() == "am" and hour == 12:
                        hour = 0
                
                activity_datetime = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
                
                return ExtractedField(
                    field_name="date",
                    value=activity_datetime.isoformat(),
                    confidence=pattern_info["confidence"],
                    source_text=match.group(0),
                    extraction_method="specific_time_pattern"
                )
        
        return None
    
    async def _extract_location(self, text: str) -> Optional[ExtractedField]:
        """Extract location information from text."""
        # Simple location patterns
        location_patterns = [
            r"\bat\s+([A-Za-z\s]+(?:gym|park|pool|track|beach|home))\b",
            r"\bin\s+([A-Za-z\s]+)\b",
            r"\bon\s+([A-Za-z\s]+(?:trail|road|track))\b"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                return ExtractedField(
                    field_name="location",
                    value=location,
                    confidence=0.7,
                    source_text=match.group(0),
                    extraction_method="location_pattern"
                )
        
        return None
    
    async def _generate_activity_name(self, structured_data: Dict[str, Any], original_text: str) -> str:
        """Generate a descriptive name for the activity."""
        activity_type = structured_data.get("type", "Activity")
        distance = structured_data.get("value")
        unit = structured_data.get("unit")
        duration = structured_data.get("duration")
        
        name_parts = []
        
        # Add distance if available
        if distance and unit:
            name_parts.append(f"{distance}{unit}")
        
        # Add activity type
        name_parts.append(activity_type.capitalize() if activity_type else "Activity")
        
        # Add duration if available and no distance
        if duration and not distance:
            name_parts.append(f"({duration} min)")
        
        # If we have a very short original text, use it as is
        if len(original_text.split()) <= 4:
            return original_text.title()
        
        return " ".join(name_parts) if name_parts else "Activity"
    
    async def _extract_additional_notes(self, text: str, structured_data: Dict[str, Any]) -> str:
        """Extract additional notes that weren't captured in structured fields."""
        # Remove already extracted information
        remaining_text = text.lower()
        
        # Remove extracted patterns
        for field in structured_data:
            if field in ["type", "value", "unit", "duration"]:
                # This is a simplified approach - in practice, we'd track what was extracted
                continue
        
        # Look for descriptive words and phrases
        descriptive_patterns = [
            r"\b(easy|hard|difficult|challenging|intense|light|moderate)\b",
            r"\b(felt\s+\w+)\b",
            r"\b(with\s+\w+)\b",
            r"\b(beautiful|sunny|rainy|cold|hot)\s+\w*\b"
        ]
        
        notes = []
        for pattern in descriptive_patterns:
            matches = re.findall(pattern, remaining_text, re.IGNORECASE)
            notes.extend(matches)
        
        return " ".join(notes) if notes else ""
    
    def _parse_duration_match(self, match, format_type: str) -> Optional[float]:
        """Parse duration from regex match based on format type."""
        try:
            if format_type == "hours_minutes":
                hours = int(match.group(1))
                minutes = int(match.group(2)) if match.group(2) else 0
                return hours * 60 + minutes
            elif format_type == "time_format":
                hours = int(match.group(1))
                minutes = int(match.group(2))
                return hours * 60 + minutes
            elif format_type == "minutes":
                return float(match.group(1))
            elif format_type == "hours":
                return float(match.group(1)) * 60
        except (ValueError, IndexError):
            return None
        
        return None
    
    def _calculate_overall_confidence(self, extracted_fields: List[ExtractedField]) -> float:
        """Calculate overall confidence score for the extraction."""
        if not extracted_fields:
            return 0.0
        
        total_confidence = sum(field.confidence for field in extracted_fields)
        return min(total_confidence / len(extracted_fields), 1.0)
    
    async def _identify_missing_critical_fields(self, structured_data: Dict[str, Any]) -> List[str]:
        """Identify missing critical fields based on activity type."""
        missing = []
        
        if not structured_data.get("type"):
            missing.append("activity_type")
        
        # For cardio activities, distance or duration is important
        activity_type = structured_data.get("type")
        if activity_type in ["running", "cycling", "swimming", "walking"]:
            if not structured_data.get("value") and not structured_data.get("duration"):
                missing.append("distance_or_duration")
        
        return missing
    
    async def _generate_improvement_suggestions(self, structured_data: Dict[str, Any], 
                                              missing_fields: List[str], 
                                              confidence_score: float) -> List[str]:
        """Generate suggestions to improve data quality."""
        suggestions = []
        
        if confidence_score < 0.7:
            suggestions.append("Try to be more specific about your activity details")
        
        if "activity_type" in missing_fields:
            suggestions.append("Please specify what type of exercise you did (e.g., running, cycling, swimming)")
        
        if "distance_or_duration" in missing_fields:
            suggestions.append("Adding distance or duration will help track your progress better")
        
        if not structured_data.get("duration") and structured_data.get("value"):
            suggestions.append("Including how long the activity took would provide better insights")
        
        return suggestions


# Global service instance
activity_extraction_service = ActivityExtractionService()
