"""Input Optimization Tools for Query Rephrasing and Enhancement.

This module provides tools for optimizing user inputs before they reach specialist agents,
ensuring better understanding and more accurate responses.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from services.input_optimization_service import (
    input_optimization_service,
    OptimizationLevel,
    QueryType
)


class QueryOptimizationInput(BaseModel):
    """Input for query optimization and rephrasing."""
    user_query: str = Field(description="Original user query to optimize")
    user_id: str = Field(description="User ID for personalization context")
    optimization_level: str = Field(
        default="standard",
        description="Level of optimization (minimal, standard, enhanced)"
    )
    target_agent: str = Field(
        default="auto",
        description="Target agent (logger, coach, auto) for optimization focus"
    )
    include_clarification: bool = Field(
        default=True,
        description="Whether to generate clarification questions if needed"
    )


class QueryRephraseAndOptimizeTool(BaseTool):
    """Tool for rephrasing and optimizing user queries before agent processing."""
    
    name: str = "rephrase_and_optimize_query"
    description: str = """
    Rephrase and optimize user queries for better agent understanding and processing.
    
    This tool:
    - Clarifies ambiguous or unclear user inputs
    - Extracts and structures key information
    - Standardizes terminology and formats
    - Adds missing context from conversation history
    - Generates clarification questions when needed
    - Optimizes queries for specific agent types
    
    Use this BEFORE transferring to Logger or Coach agents to ensure optimal results.
    
    Examples of improvements:
    - "ran 5k" → "I completed a 5 kilometer run today"
    - "show stats" → "Display my fitness progress and statistics"
    - "need workout" → "Create a personalized workout plan for me"
    """
    args_schema: type = QueryOptimizationInput
    
    def _run(self, user_query: str, user_id: str, optimization_level: str = "standard",
             target_agent: str = "auto", include_clarification: bool = True) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(user_query, user_id, optimization_level, target_agent, include_clarification))
    
    async def _arun(self, user_query: str, user_id: str, optimization_level: str = "standard",
                   target_agent: str = "auto", include_clarification: bool = True) -> str:
        """Optimize and rephrase a user query."""
        try:
            # Convert string optimization level to enum
            try:
                opt_level = OptimizationLevel(optimization_level.lower())
            except ValueError:
                opt_level = OptimizationLevel.STANDARD
            
            # Get conversation context (placeholder - would integrate with actual memory)
            conversation_context = await self._get_conversation_context(user_id)
            
            # Get user profile (placeholder - would integrate with actual profile)
            user_profile = await self._get_user_profile(user_id)
            
            # Analyze the query first
            analysis = await input_optimization_service.analyze_query(
                user_query, conversation_context
            )
            
            # Optimize the query
            optimization_result = await input_optimization_service.optimize_query(
                user_query=user_query,
                optimization_level=opt_level,
                conversation_context=conversation_context,
                user_profile=user_profile
            )
            
            # Format the response
            response_parts = []
            
            # Show analysis results
            response_parts.append("🔍 **Query Analysis & Optimization**")
            response_parts.append("=" * 45)
            
            # Original query
            response_parts.append(f"📝 **Original Query:** \"{user_query}\"")
            
            # Query type and confidence
            query_type_name = analysis.query_type.value.replace("_", " ").title()
            response_parts.append(f"🎯 **Query Type:** {query_type_name} ({analysis.confidence:.0%} confidence)")
            
            # Optimized query
            if optimization_result.optimized_query != user_query:
                response_parts.append(f"✨ **Optimized Query:** \"{optimization_result.optimized_query}\"")
            else:
                response_parts.append(f"✅ **Query already well-formed** (no changes needed)")
            
            # Show improvements made
            if optimization_result.improvements_made:
                response_parts.append(f"\n🛠️ **Improvements Made:**")
                improvement_descriptions = {
                    "rephrased_activity_logging": "Standardized activity logging format",
                    "rephrased_progress_inquiry": "Clarified progress request",
                    "rephrased_workout_planning": "Enhanced workout planning request",
                    "rephrased_coaching_request": "Improved coaching request structure",
                    "fixed_contractions": "Expanded contractions for clarity",
                    "improved_grammar": "Fixed grammar and capitalization",
                    "added_time_context": "Added time context",
                    "added_profile_context": "Added user profile context",
                    "standardized_terminology": "Standardized fitness terminology"
                }
                
                for improvement in optimization_result.improvements_made:
                    description = improvement_descriptions.get(improvement, improvement.replace("_", " ").title())
                    response_parts.append(f"  • {description}")
            
            # Show extracted entities
            if optimization_result.extracted_entities:
                response_parts.append(f"\n📊 **Extracted Information:**")
                for entity_type, entity_data in optimization_result.extracted_entities.items():
                    if isinstance(entity_data, dict) and "value" in entity_data:
                        value = entity_data["value"]
                        unit = entity_data.get("unit", "")
                        response_parts.append(f"  • {entity_type.title()}: {value} {unit}".strip())
                    else:
                        response_parts.append(f"  • {entity_type.title()}: {entity_data}")
            
            # Show clarification questions if needed
            if include_clarification and optimization_result.requires_clarification:
                response_parts.append(f"\n❓ **Clarification Needed:**")
                for question in optimization_result.clarification_questions:
                    response_parts.append(f"  • {question}")
                
                response_parts.append(f"\n💡 **Suggestion:** Please provide the missing information for better results.")
            
            # Recommendation for next steps
            response_parts.append(f"\n🎯 **Recommended Next Step:**")
            
            if target_agent == "auto":
                if analysis.query_type == QueryType.ACTIVITY_LOGGING:
                    response_parts.append(f"  → Transfer to **Logger Agent** for activity processing")
                elif analysis.query_type in [QueryType.WORKOUT_PLANNING, QueryType.COACHING_REQUEST]:
                    response_parts.append(f"  → Transfer to **Coach Agent** for personalized coaching")
                elif analysis.query_type == QueryType.PROGRESS_INQUIRY:
                    response_parts.append(f"  → Transfer to **Logger Agent** for progress analysis")
                else:
                    response_parts.append(f"  → Continue with **Orchestration Agent** for general assistance")
            else:
                response_parts.append(f"  → Transfer to **{target_agent.title()} Agent** as specified")
            
            # Confidence and quality metrics
            response_parts.append(f"\n📈 **Optimization Quality:**")
            response_parts.append(f"  • Confidence Score: {optimization_result.confidence_score:.0%}")
            response_parts.append(f"  • Query Complexity: {analysis.complexity_score:.1f}/1.0")
            response_parts.append(f"  • Optimization Level: {opt_level.value.title()}")
            
            # Usage instructions
            if optimization_result.optimized_query != user_query:
                response_parts.append(f"\n🚀 **Usage:** Use the optimized query for agent processing to get better results!")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error optimizing query: {str(e)}"
    
    async def _get_conversation_context(self, user_id: str) -> List[str]:
        """Get recent conversation context for the user."""
        # Placeholder - would integrate with actual conversation memory
        # For now, return empty context
        return []
    
    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile for personalization."""
        # Placeholder - would integrate with actual user profile storage
        # For now, return basic profile
        return {
            "fitness_level": "intermediate",
            "preferred_activities": ["running", "strength_training"],
            "goals": ["general_fitness"]
        }


class QueryAnalysisTool(BaseTool):
    """Tool for analyzing user queries without optimization."""
    
    name: str = "analyze_user_query"
    description: str = """
    Analyze user queries to understand their type, complexity, and characteristics.
    
    This tool provides:
    - Query type classification (logging, planning, coaching, etc.)
    - Confidence scores for classification
    - Entity extraction (duration, distance, activity type, etc.)
    - Complexity assessment
    - Missing information identification
    - Ambiguity detection
    
    Use this for understanding user intent before processing or optimization.
    """
    
    class QueryAnalysisInput(BaseModel):
        user_query: str = Field(description="User query to analyze")
        user_id: str = Field(description="User ID for context")
        include_suggestions: bool = Field(
            default=True,
            description="Whether to include improvement suggestions"
        )
    
    args_schema: type = QueryAnalysisInput
    
    def _run(self, user_query: str, user_id: str, include_suggestions: bool = True) -> str:
        """Synchronous wrapper for async implementation."""
        import asyncio
        return asyncio.run(self._arun(user_query, user_id, include_suggestions))
    
    async def _arun(self, user_query: str, user_id: str, include_suggestions: bool = True) -> str:
        """Analyze a user query without optimization."""
        try:
            # Get conversation context
            conversation_context = await self._get_conversation_context(user_id)
            
            # Analyze the query
            analysis = await input_optimization_service.analyze_query(
                user_query, conversation_context
            )
            
            # Format response
            response_parts = []
            
            response_parts.append("🔍 **Query Analysis Report**")
            response_parts.append("=" * 35)
            
            # Basic info
            response_parts.append(f"📝 **Query:** \"{user_query}\"")
            
            # Classification
            query_type_name = analysis.query_type.value.replace("_", " ").title()
            confidence_bar = "█" * int(analysis.confidence * 10) + "░" * (10 - int(analysis.confidence * 10))
            response_parts.append(f"🎯 **Type:** {query_type_name}")
            response_parts.append(f"📊 **Confidence:** {analysis.confidence:.0%} [{confidence_bar}]")
            
            # Complexity
            complexity_bar = "█" * int(analysis.complexity_score * 10) + "░" * (10 - int(analysis.complexity_score * 10))
            response_parts.append(f"⚡ **Complexity:** {analysis.complexity_score:.1f}/1.0 [{complexity_bar}]")
            
            # Extracted entities
            if analysis.key_entities:
                response_parts.append(f"\n📊 **Extracted Entities:**")
                for entity in analysis.key_entities:
                    entity_type, entity_value = entity.split(":", 1) if ":" in entity else (entity, "")
                    response_parts.append(f"  • {entity_type.title()}: {entity_value}")
            else:
                response_parts.append(f"\n📊 **Extracted Entities:** None detected")
            
            # Missing information
            if analysis.missing_info:
                response_parts.append(f"\n⚠️ **Missing Information:**")
                for missing in analysis.missing_info:
                    missing_name = missing.replace("_", " ").title()
                    response_parts.append(f"  • {missing_name}")
            
            # Ambiguities
            if analysis.ambiguities:
                response_parts.append(f"\n❓ **Ambiguities Detected:**")
                ambiguity_descriptions = {
                    "unclear_pronoun_reference": "Unclear pronoun reference (it, that, this)",
                    "vague_time_reference": "Vague time reference (earlier, later, soon)",
                    "vague_quantity": "Vague quantity (a lot, some, much)"
                }
                
                for ambiguity in analysis.ambiguities:
                    description = ambiguity_descriptions.get(ambiguity, ambiguity.replace("_", " ").title())
                    response_parts.append(f"  • {description}")
            
            # Context needs
            if analysis.context_needed:
                response_parts.append(f"\n🔗 **Context Required:** Yes - query references previous conversation")
            else:
                response_parts.append(f"\n🔗 **Context Required:** No - query is self-contained")
            
            # Suggestions
            if include_suggestions:
                response_parts.append(f"\n💡 **Suggestions:**")
                
                if analysis.query_type == QueryType.UNCLEAR:
                    response_parts.append(f"  • Query type unclear - consider asking for clarification")
                elif analysis.confidence < 0.7:
                    response_parts.append(f"  • Low confidence classification - may need rephrasing")
                
                if analysis.missing_info:
                    response_parts.append(f"  • Missing key information - consider asking follow-up questions")
                
                if analysis.ambiguities:
                    response_parts.append(f"  • Contains ambiguities - optimization recommended")
                
                if analysis.complexity_score > 0.7:
                    response_parts.append(f"  • High complexity - consider breaking into simpler parts")
                
                if not analysis.missing_info and not analysis.ambiguities and analysis.confidence > 0.8:
                    response_parts.append(f"  • Query is well-formed and ready for processing")
            
            # Recommended agent
            response_parts.append(f"\n🎯 **Recommended Agent:**")
            if analysis.query_type == QueryType.ACTIVITY_LOGGING:
                response_parts.append(f"  → **Logger Agent** (activity logging and data management)")
            elif analysis.query_type == QueryType.PROGRESS_INQUIRY:
                response_parts.append(f"  → **Logger Agent** (progress analysis and statistics)")
            elif analysis.query_type in [QueryType.WORKOUT_PLANNING, QueryType.COACHING_REQUEST]:
                response_parts.append(f"  → **Coach Agent** (personalized coaching and planning)")
            elif analysis.query_type == QueryType.GENERAL_FITNESS:
                response_parts.append(f"  → **Coach Agent** (general fitness guidance)")
            else:
                response_parts.append(f"  → **Orchestration Agent** (general assistance)")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"❌ Error analyzing query: {str(e)}"
    
    async def _get_conversation_context(self, user_id: str) -> List[str]:
        """Get recent conversation context."""
        # Placeholder implementation
        return []


# Tool instances
query_rephrase_and_optimize_tool = QueryRephraseAndOptimizeTool()
query_analysis_tool = QueryAnalysisTool()

# Export list of input optimization tools
input_optimization_tools = [
    query_rephrase_and_optimize_tool,
    query_analysis_tool
]
