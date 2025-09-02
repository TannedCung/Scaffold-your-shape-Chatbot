"""Enhanced Logger Agent Tools with Smart Validation and Extraction.

This module provides advanced tools for the Logger Agent that integrate
intelligent activity validation and data extraction capabilities.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from services.activity_validation_service import (
    activity_validation_service, 
    ValidationResult,
    ValidationLevel
)
from services.activity_extraction_service import (
    activity_extraction_service,
    ExtractionResult
)


class SmartActivityLogInput(BaseModel):
    """Input for smart activity logging with validation."""
    user_input: str = Field(description="Natural language description of the activity")
    user_id: str = Field(description="User ID for the activity")
    force_log: bool = Field(
        default=False, 
        description="Force logging even with low confidence (use with caution)"
    )
    additional_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context like user profile or preferences"
    )


class ActivityValidationInput(BaseModel):
    """Input for activity validation only."""
    activity_data: Dict[str, Any] = Field(description="Raw activity data to validate")
    user_id: str = Field(description="User ID for context")
    user_profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User profile for historical pattern analysis"
    )


class SmartActivityLogTool(BaseTool):
    """Enhanced activity logging tool with smart extraction and validation."""
    
    name: str = "smart_activity_log"
    description: str = """
    Log activities using intelligent extraction and validation.
    
    This tool automatically:
    - Extracts structured data from natural language
    - Validates activity data for accuracy and completeness  
    - Enhances data with derived metrics (pace, calories, etc.)
    - Provides confidence scores and suggestions
    - Handles missing information gracefully
    
    Use this for any activity logging request from users.
    """
    args_schema: type = SmartActivityLogInput
    
    def _run(self, user_input: str, user_id: str, 
             force_log: bool = False,
             additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(user_input, user_id, force_log, additional_context))
    
    async def _arun(self, user_input: str, user_id: str, 
                   force_log: bool = False,
                   additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Execute smart activity logging with validation."""
        try:
            # Step 1: Extract structured data from natural language
            extraction_result = await activity_extraction_service.extract_activity_data(
                text=user_input,
                context=additional_context
            )
            
            # Step 2: Validate extracted data
            validation_result = await activity_validation_service.validate_activity(
                activity_data=extraction_result.structured_data,
                user_profile=additional_context.get('user_profile') if additional_context else None
            )
            
            # Step 3: Decide on action based on validation confidence
            response_parts = []
            
            if validation_result.validation_level == ValidationLevel.HIGH:
                # High confidence - log immediately
                enhanced_data = validation_result.enhanced_data
                enhanced_data["userId"] = user_id
                
                # Here you would call the actual MCP logging tool
                # For now, we'll simulate successful logging
                log_success = await self._log_to_mcp(enhanced_data)
                
                if log_success:
                    response_parts.append(
                        f"✅ Successfully logged your {enhanced_data.get('type', 'activity')}!"
                    )
                    
                    # Add enhancement details
                    if enhanced_data.get('pace_min_per_km'):
                        response_parts.append(
                            f"📊 Pace: {enhanced_data['pace_min_per_km']:.1f} min/km"
                        )
                    
                    if enhanced_data.get('estimated_calories'):
                        response_parts.append(
                            f"🔥 Estimated calories: {enhanced_data['estimated_calories']}"
                        )
                    
                    response_parts.append(
                        f"🎯 Data confidence: {validation_result.confidence:.0%}"
                    )
                else:
                    response_parts.append("❌ Failed to log activity to system")
                    
            elif validation_result.validation_level == ValidationLevel.MEDIUM:
                # Medium confidence - log with notes about assumptions
                if force_log or validation_result.confidence >= 0.75:
                    enhanced_data = validation_result.enhanced_data
                    enhanced_data["userId"] = user_id
                    
                    log_success = await self._log_to_mcp(enhanced_data)
                    
                    if log_success:
                        response_parts.append(
                            f"✅ Logged your {enhanced_data.get('type', 'activity')} "
                            f"(confidence: {validation_result.confidence:.0%})"
                        )
                        
                        # Mention any assumptions or issues
                        if validation_result.issues:
                            assumptions = [
                                issue.message for issue in validation_result.issues 
                                if issue.severity in ["warning", "info"]
                            ]
                            if assumptions:
                                response_parts.append(
                                    f"📝 Note: {'; '.join(assumptions[:2])}"
                                )
                    else:
                        response_parts.append("❌ Failed to log activity to system")
                else:
                    # Ask for clarification
                    response_parts.append(
                        "🤔 I need a bit more information to log this accurately."
                    )
                    
                    missing_info = [
                        issue.suggestion for issue in validation_result.issues 
                        if issue.suggestion and issue.severity == "warning"
                    ]
                    
                    if missing_info:
                        response_parts.append(f"Could you clarify: {missing_info[0]}")
                    
            else:
                # Low confidence or failed validation - ask for clarification
                response_parts.append(
                    "🤔 I'd like to help you log this activity, but I need more details."
                )
                
                # Provide specific suggestions
                if validation_result.suggestions:
                    response_parts.append(f"💡 {validation_result.suggestions[0]}")
                
                if extraction_result.missing_fields:
                    missing = ", ".join(extraction_result.missing_fields[:3])
                    response_parts.append(f"Missing: {missing}")
            
            # Add general suggestions if available
            if validation_result.suggestions and validation_result.validation_level != ValidationLevel.LOW:
                response_parts.append(f"💪 Tip: {validation_result.suggestions[0]}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error processing activity: {str(e)}. Please try again with more specific details."
    
    async def _log_to_mcp(self, activity_data: Dict[str, Any]) -> bool:
        """Log activity data to MCP server (placeholder for actual implementation)."""
        # This would integrate with the actual MCP client
        # For now, we'll simulate successful logging
        await asyncio.sleep(0.1)  # Simulate network call
        return True  # Assume success for now


class ActivityValidationTool(BaseTool):
    """Tool for validating activity data without logging."""
    
    name: str = "validate_activity_data"
    description: str = """
    Validate activity data for accuracy and completeness without logging it.
    
    Useful for:
    - Checking data quality before logging
    - Getting confidence scores for extracted data
    - Identifying missing or unusual information
    - Getting suggestions for improvement
    """
    args_schema: type = ActivityValidationInput
    
    def _run(self, activity_data: Dict[str, Any], user_id: str,
             user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(activity_data, user_id, user_profile))
    
    async def _arun(self, activity_data: Dict[str, Any], user_id: str,
                   user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Validate activity data and return detailed analysis."""
        try:
            validation_result = await activity_validation_service.validate_activity(
                activity_data=activity_data,
                user_profile=user_profile
            )
            
            response_parts = []
            
            # Confidence score
            confidence_emoji = {
                ValidationLevel.HIGH: "🟢",
                ValidationLevel.MEDIUM: "🟡", 
                ValidationLevel.LOW: "🟠",
                ValidationLevel.FAILED: "🔴"
            }
            
            emoji = confidence_emoji.get(validation_result.validation_level, "⚪")
            response_parts.append(
                f"{emoji} Validation confidence: {validation_result.confidence:.0%} "
                f"({validation_result.validation_level.value})"
            )
            
            # Issues found
            if validation_result.issues:
                response_parts.append("\n📋 Issues found:")
                for issue in validation_result.issues[:3]:  # Limit to top 3
                    severity_emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
                    emoji = severity_emoji.get(issue.severity, "•")
                    response_parts.append(f"  {emoji} {issue.message}")
            
            # Enhancements available
            if validation_result.enhanced_data:
                enhancements = []
                enhanced = validation_result.enhanced_data
                
                if enhanced.get('pace_min_per_km'):
                    enhancements.append(f"Pace: {enhanced['pace_min_per_km']:.1f} min/km")
                
                if enhanced.get('estimated_calories'):
                    enhancements.append(f"Calories: {enhanced['estimated_calories']}")
                
                if enhanced.get('standardized_distance_km'):
                    enhancements.append(f"Distance: {enhanced['standardized_distance_km']}km")
                
                if enhancements:
                    response_parts.append(f"\n📊 Enhanced metrics: {', '.join(enhancements[:3])}")
            
            # Suggestions
            if validation_result.suggestions:
                response_parts.append(f"\n💡 Suggestions:")
                for suggestion in validation_result.suggestions[:2]:
                    response_parts.append(f"  • {suggestion}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error validating activity: {str(e)}"


class SmartExtractionTool(BaseTool):
    """Tool for extracting structured data from natural language."""
    
    name: str = "extract_activity_data"
    description: str = """
    Extract structured activity data from natural language descriptions.
    
    This tool intelligently parses user input to identify:
    - Activity type (running, cycling, etc.)
    - Distance, duration, repetitions
    - Time/date information
    - Location details
    - Additional notes and context
    """
    
    class SmartExtractionInput(BaseModel):
        user_input: str = Field(description="Natural language description to parse")
        context: Optional[Dict[str, Any]] = Field(
            default=None,
            description="Additional context for better extraction"
        )
    
    args_schema: type = SmartExtractionInput
    
    def _run(self, user_input: str, 
             context: Optional[Dict[str, Any]] = None) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(user_input, context))
    
    async def _arun(self, user_input: str, 
                   context: Optional[Dict[str, Any]] = None) -> str:
        """Extract structured data from natural language."""
        try:
            extraction_result = await activity_extraction_service.extract_activity_data(
                text=user_input,
                context=context
            )
            
            response_parts = []
            
            # Overall confidence
            response_parts.append(
                f"🎯 Extraction confidence: {extraction_result.confidence_score:.0%}"
            )
            
            # Extracted data
            if extraction_result.structured_data:
                response_parts.append("\n📊 Extracted data:")
                data = extraction_result.structured_data
                
                if data.get('type'):
                    response_parts.append(f"  • Type: {data['type']}")
                
                if data.get('value') and data.get('unit'):
                    response_parts.append(f"  • Distance: {data['value']} {data['unit']}")
                
                if data.get('duration'):
                    response_parts.append(f"  • Duration: {data['duration']} minutes")
                
                if data.get('date'):
                    date_str = data['date'][:16].replace('T', ' ')  # Format datetime
                    response_parts.append(f"  • Date: {date_str}")
                
                if data.get('location'):
                    response_parts.append(f"  • Location: {data['location']}")
                
                if data.get('notes'):
                    response_parts.append(f"  • Notes: {data['notes']}")
            
            # Missing fields
            if extraction_result.missing_fields:
                response_parts.append(
                    f"\n❓ Missing: {', '.join(extraction_result.missing_fields)}"
                )
            
            # Extraction details
            if extraction_result.extracted_fields:
                high_confidence_fields = [
                    f.field_name for f in extraction_result.extracted_fields 
                    if f.confidence >= 0.8
                ]
                if high_confidence_fields:
                    response_parts.append(
                        f"\n✅ High confidence fields: {', '.join(high_confidence_fields)}"
                    )
            
            # Suggestions
            if extraction_result.suggestions:
                response_parts.append(f"\n💡 Suggestions:")
                for suggestion in extraction_result.suggestions[:2]:
                    response_parts.append(f"  • {suggestion}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error extracting data: {str(e)}"


# Tool instances for use in agents
smart_activity_log_tool = SmartActivityLogTool()
activity_validation_tool = ActivityValidationTool()
smart_extraction_tool = SmartExtractionTool()

class ProgressAnalyticsTool(BaseTool):
    """Tool for generating progress analytics and insights."""
    
    name: str = "generate_progress_analytics"
    description: str = """
    Generate comprehensive progress analytics and insights for a user.
    
    This tool provides:
    - Progress summary over specified period
    - Trend analysis (improving/declining/stable)
    - Achievement detection (PRs, streaks, milestones)
    - Personalized insights and recommendations
    - Consistency, variety, and improvement scores
    
    Use this when users ask about their progress, trends, or "how am I doing?"
    """
    
    class ProgressAnalyticsInput(BaseModel):
        user_id: str = Field(description="User ID to analyze")
        period_days: int = Field(
            default=30, 
            description="Number of days to analyze (default: 30)"
        )
        include_achievements: bool = Field(
            default=True,
            description="Whether to include achievement detection"
        )
        include_trends: bool = Field(
            default=True,
            description="Whether to include trend analysis"
        )
    
    args_schema: type = ProgressAnalyticsInput
    
    def _run(self, user_id: str, period_days: int = 30,
             include_achievements: bool = True,
             include_trends: bool = True) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(user_id, period_days, include_achievements, include_trends))
    
    async def _arun(self, user_id: str, period_days: int = 30,
                   include_achievements: bool = True,
                   include_trends: bool = True) -> str:
        """Generate progress analytics for a user."""
        try:
            from services.progress_analytics_service import progress_analytics_service
            
            # Generate comprehensive progress summary
            progress_summary = await progress_analytics_service.generate_progress_summary(
                user_id=user_id,
                period_days=period_days
            )
            
            response_parts = []
            
            # Header
            response_parts.append(f"📊 **Progress Report - Last {period_days} Days**")
            response_parts.append("=" * 40)
            
            # Basic metrics
            response_parts.append("📈 **Activity Summary:**")
            response_parts.append(f"  • Total activities: {progress_summary.total_activities}")
            response_parts.append(f"  • Active days: {progress_summary.active_days}/{period_days}")
            
            if progress_summary.total_distance_km > 0:
                response_parts.append(f"  • Total distance: {progress_summary.total_distance_km:.1f}km")
            
            if progress_summary.total_duration_minutes > 0:
                hours = progress_summary.total_duration_minutes / 60
                response_parts.append(f"  • Total duration: {hours:.1f} hours")
            
            if progress_summary.estimated_calories > 0:
                response_parts.append(f"  • Estimated calories: {progress_summary.estimated_calories}")
            
            if progress_summary.activity_types:
                types_str = ", ".join(progress_summary.activity_types)
                response_parts.append(f"  • Activity types: {types_str}")
            
            # Scores
            response_parts.append("\n🎯 **Performance Scores:**")
            response_parts.append(f"  • Consistency: {progress_summary.consistency_score:.0%}")
            response_parts.append(f"  • Variety: {progress_summary.variety_score:.0%}")
            response_parts.append(f"  • Improvement: {progress_summary.improvement_score:.0%}")
            
            # Achievements
            if include_achievements and progress_summary.achievements:
                response_parts.append("\n🏆 **Recent Achievements:**")
                for achievement in progress_summary.achievements[:3]:  # Show top 3
                    response_parts.append(f"  • {achievement.title}: {achievement.description}")
            
            # Trends
            if include_trends and progress_summary.trends:
                response_parts.append("\n📈 **Trends:**")
                for trend in progress_summary.trends[:3]:  # Show top 3
                    direction_emoji = {
                        "improving": "📈",
                        "stable": "➡️",
                        "declining": "📉",
                        "insufficient_data": "❓"
                    }
                    emoji = direction_emoji.get(trend.direction.value, "•")
                    response_parts.append(f"  {emoji} {trend.description}")
            
            # Key insights
            if progress_summary.insights:
                response_parts.append("\n💡 **Key Insights:**")
                for insight in progress_summary.insights[:2]:  # Show top 2
                    insight_emoji = {
                        "positive": "✅",
                        "neutral": "ℹ️",
                        "concern": "⚠️",
                        "celebration": "🎉",
                        "suggestion": "💭"
                    }
                    emoji = insight_emoji.get(insight.insight_type, "•")
                    response_parts.append(f"  {emoji} {insight.message}")
                    
                    if insight.recommendation:
                        response_parts.append(f"      💪 {insight.recommendation}")
            
            # Overall assessment
            response_parts.append("\n🎯 **Overall Assessment:**")
            
            avg_score = (progress_summary.consistency_score + 
                        progress_summary.variety_score + 
                        progress_summary.improvement_score) / 3
            
            if avg_score >= 0.8:
                response_parts.append("🌟 Excellent progress! You're doing fantastic!")
            elif avg_score >= 0.6:
                response_parts.append("👍 Good progress! Keep up the momentum!")
            elif avg_score >= 0.4:
                response_parts.append("📈 Making progress! Room for improvement.")
            else:
                response_parts.append("🚀 Great potential! Let's build some momentum!")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error generating progress analytics: {str(e)}"


# Create tool instance
progress_analytics_tool = ProgressAnalyticsTool()

# Export list of all enhanced logger tools
enhanced_logger_tools = [
    smart_activity_log_tool,
    activity_validation_tool,
    smart_extraction_tool,
    progress_analytics_tool
]
