"""Input Optimization Service for Query Rephrasing and Enhancement.

This service processes user inputs before they reach specialist agents to:
- Rephrase unclear or ambiguous queries
- Extract and structure key information
- Add missing context from conversation history
- Optimize queries for better agent performance
- Standardize terminology and formats
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

from config.settings import get_configuration


class QueryType(Enum):
    """Types of queries that can be optimized."""
    ACTIVITY_LOGGING = "activity_logging"
    PROGRESS_INQUIRY = "progress_inquiry"
    WORKOUT_PLANNING = "workout_planning"
    COACHING_REQUEST = "coaching_request"
    GENERAL_FITNESS = "general_fitness"
    UNCLEAR = "unclear"


class OptimizationLevel(Enum):
    """Levels of optimization to apply."""
    MINIMAL = "minimal"      # Basic cleanup only
    STANDARD = "standard"    # Standard rephrasing
    ENHANCED = "enhanced"    # Full optimization with context


@dataclass
class QueryAnalysis:
    """Analysis of a user query."""
    original_query: str
    query_type: QueryType
    confidence: float
    key_entities: List[str] = field(default_factory=list)
    missing_info: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)
    context_needed: bool = False
    complexity_score: float = 0.0


@dataclass
class OptimizedQuery:
    """Optimized version of a user query."""
    original_query: str
    optimized_query: str
    query_type: QueryType
    optimization_level: OptimizationLevel
    improvements_made: List[str] = field(default_factory=list)
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    requires_clarification: bool = False
    clarification_questions: List[str] = field(default_factory=list)


class InputOptimizationService:
    """Service for optimizing user inputs before agent processing."""
    
    def __init__(self):
        self.rephrasing_patterns = self._load_rephrasing_patterns()
        self.entity_extractors = self._load_entity_extractors()
        self.context_enhancers = self._load_context_enhancers()
        self.clarification_rules = self._load_clarification_rules()
    
    def _load_rephrasing_patterns(self) -> Dict[QueryType, List[Dict[str, Any]]]:
        """Load patterns for rephrasing different types of queries."""
        return {
            QueryType.ACTIVITY_LOGGING: [
                {
                    "pattern": r"\b(ran|run)\s+(\d+(?:\.\d+)?)\s*(k|km|kilometers?|miles?)\b",
                    "template": "I completed a {distance} {unit} run",
                    "entities": ["distance", "unit", "activity_type"]
                },
                {
                    "pattern": r"\b(did|completed|finished)\s+(\d+)\s*(pushups?|push.?ups?)\b",
                    "template": "I completed {count} push-ups",
                    "entities": ["count", "exercise"]
                },
                {
                    "pattern": r"\b(went to|hit)\s+(?:the\s+)?gym\b",
                    "template": "I completed a gym workout session",
                    "entities": ["activity_type", "location"]
                },
                {
                    "pattern": r"\b(lifted|did)\s+weights?\b",
                    "template": "I completed a strength training workout",
                    "entities": ["activity_type"]
                },
                {
                    "pattern": r"\b(swam|swimming)\s+(?:for\s+)?(\d+)\s*(minutes?|mins?|laps?)\b",
                    "template": "I completed a swimming session for {duration} {unit}",
                    "entities": ["activity_type", "duration", "unit"]
                }
            ],
            QueryType.PROGRESS_INQUIRY: [
                {
                    "pattern": r"\b(?:how\s+am\s+i|how'm\s+i)\s+doing\b",
                    "template": "Show me my fitness progress and performance summary",
                    "entities": ["request_type"]
                },
                {
                    "pattern": r"\bshow\s+(?:me\s+)?(?:my\s+)?(?:progress|stats)\b",
                    "template": "Display my fitness progress and statistics",
                    "entities": ["request_type", "data_type"]
                },
                {
                    "pattern": r"\b(?:what's|whats)\s+my\s+(?:progress|improvement)\b",
                    "template": "What is my fitness progress and improvement over time?",
                    "entities": ["request_type", "time_frame"]
                },
                {
                    "pattern": r"\b(?:compare|comparison)\s+(?:to\s+)?(?:last\s+)?(\w+)\b",
                    "template": "Compare my current performance to {time_period}",
                    "entities": ["request_type", "comparison_period"]
                }
            ],
            QueryType.WORKOUT_PLANNING: [
                {
                    "pattern": r"\b(?:create|make|plan)\s+(?:a\s+|me\s+a\s+)?workout\b",
                    "template": "Create a personalized workout plan for me",
                    "entities": ["request_type"]
                },
                {
                    "pattern": r"\bneed\s+(?:a\s+)?(\d+)\s*(?:minute|min)\s+workout\b",
                    "template": "Create a {duration}-minute workout plan for me",
                    "entities": ["request_type", "duration"]
                },
                {
                    "pattern": r"\b(?:what\s+should\s+i|recommend)\s+(?:do\s+)?(?:for\s+)?workout\b",
                    "template": "What workout do you recommend for me based on my profile?",
                    "entities": ["request_type", "recommendation"]
                },
                {
                    "pattern": r"\b(?:home|at.?home)\s+workout\b",
                    "template": "Create a home workout plan without gym equipment",
                    "entities": ["request_type", "location", "equipment"]
                }
            ],
            QueryType.COACHING_REQUEST: [
                {
                    "pattern": r"\b(?:how\s+(?:do\s+i|to)|help\s+me)\s+(?:improve|get\s+better)\b",
                    "template": "How can I improve my fitness performance and results?",
                    "entities": ["request_type", "improvement_focus"]
                },
                {
                    "pattern": r"\b(?:motivate|motivation|encourage)\s+me\b",
                    "template": "I need motivation and encouragement for my fitness journey",
                    "entities": ["request_type", "support_type"]
                },
                {
                    "pattern": r"\b(?:advice|tips?)\s+(?:for|on)\s+(\w+)\b",
                    "template": "Give me fitness advice and tips for {topic}",
                    "entities": ["request_type", "advice_topic"]
                }
            ]
        }
    
    def _load_entity_extractors(self) -> Dict[str, Dict[str, Any]]:
        """Load entity extraction patterns."""
        return {
            "duration": {
                "patterns": [
                    r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b",
                    r"(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)\b",
                    r"(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|s)\b"
                ],
                "normalizer": self._normalize_duration
            },
            "distance": {
                "patterns": [
                    r"(\d+(?:\.\d+)?)\s*(?:kilometers?|km|k)\b",
                    r"(\d+(?:\.\d+)?)\s*(?:miles?|mi)\b",
                    r"(\d+(?:\.\d+)?)\s*(?:meters?|m)\b"
                ],
                "normalizer": self._normalize_distance
            },
            "count": {
                "patterns": [
                    r"(\d+)\s*(?:reps?|repetitions?)\b",
                    r"(\d+)\s*(?:sets?)\b",
                    r"(\d+)\s*(?:times?)\b"
                ],
                "normalizer": self._normalize_count
            },
            "intensity": {
                "patterns": [
                    r"\b(easy|light|low)\b",
                    r"\b(moderate|medium|normal)\b",
                    r"\b(hard|intense|high|vigorous)\b",
                    r"\b(max|maximum|all.?out)\b"
                ],
                "normalizer": self._normalize_intensity
            },
            "activity_type": {
                "patterns": [
                    r"\b(run|running|jog|jogging)\b",
                    r"\b(bike|biking|cycle|cycling)\b",
                    r"\b(swim|swimming)\b",
                    r"\b(walk|walking)\b",
                    r"\b(lift|lifting|weights?|strength)\b",
                    r"\b(yoga|stretching|flexibility)\b",
                    r"\b(hiit|interval|circuit)\b"
                ],
                "normalizer": self._normalize_activity_type
            }
        }
    
    def _load_context_enhancers(self) -> Dict[str, List[str]]:
        """Load context enhancement rules."""
        return {
            "time_context": [
                "today", "yesterday", "this morning", "this evening",
                "last night", "earlier", "just now", "recently"
            ],
            "location_context": [
                "at home", "at the gym", "outside", "on the treadmill",
                "in the park", "at the track", "in the pool"
            ],
            "mood_context": [
                "feeling good", "tired", "energized", "motivated",
                "struggling", "excited", "confident"
            ]
        }
    
    def _load_clarification_rules(self) -> Dict[QueryType, List[str]]:
        """Load clarification questions for different query types."""
        return {
            QueryType.ACTIVITY_LOGGING: [
                "What type of activity did you do?",
                "How long did the activity last?",
                "When did you do this activity?",
                "How intense was the workout?"
            ],
            QueryType.WORKOUT_PLANNING: [
                "How long do you want the workout to be?",
                "What type of workout are you looking for?",
                "Do you have any equipment available?",
                "What's your fitness goal for this workout?"
            ],
            QueryType.PROGRESS_INQUIRY: [
                "What specific progress metrics would you like to see?",
                "What time period should I analyze?",
                "Are you interested in a particular type of activity?"
            ]
        }
    
    async def analyze_query(self, user_query: str, 
                          conversation_context: Optional[List[str]] = None) -> QueryAnalysis:
        """
        Analyze a user query to understand its type and characteristics.
        
        Args:
            user_query: The user's input query
            conversation_context: Recent conversation messages for context
            
        Returns:
            QueryAnalysis with detailed analysis of the query
        """
        query_lower = user_query.lower().strip()
        
        # Determine query type
        query_type, confidence = await self._classify_query_type(query_lower)
        
        # Extract entities
        key_entities = await self._extract_entities(query_lower)
        
        # Identify missing information
        missing_info = await self._identify_missing_info(query_type, key_entities, query_lower)
        
        # Find ambiguities
        ambiguities = await self._find_ambiguities(query_lower)
        
        # Calculate complexity
        complexity_score = await self._calculate_complexity(query_lower, key_entities)
        
        # Check if context is needed
        context_needed = await self._needs_context(query_lower, conversation_context)
        
        return QueryAnalysis(
            original_query=user_query,
            query_type=query_type,
            confidence=confidence,
            key_entities=key_entities,
            missing_info=missing_info,
            ambiguities=ambiguities,
            context_needed=context_needed,
            complexity_score=complexity_score
        )
    
    async def optimize_query(self, user_query: str,
                           optimization_level: OptimizationLevel = OptimizationLevel.STANDARD,
                           conversation_context: Optional[List[str]] = None,
                           user_profile: Optional[Dict[str, Any]] = None) -> OptimizedQuery:
        """
        Optimize a user query for better agent processing.
        
        Args:
            user_query: Original user query
            optimization_level: Level of optimization to apply
            conversation_context: Recent conversation for context
            user_profile: User profile for personalization
            
        Returns:
            OptimizedQuery with improvements and extracted information
        """
        # Analyze the query first
        analysis = await self.analyze_query(user_query, conversation_context)
        
        # Start with the original query
        optimized_text = user_query.strip()
        improvements_made = []
        extracted_entities = {}
        
        # Apply optimizations based on level
        if optimization_level in [OptimizationLevel.STANDARD, OptimizationLevel.ENHANCED]:
            # Apply rephrasing patterns
            optimized_text, pattern_improvements = await self._apply_rephrasing_patterns(
                optimized_text, analysis.query_type
            )
            improvements_made.extend(pattern_improvements)
            
            # Extract and normalize entities
            extracted_entities = await self._extract_and_normalize_entities(optimized_text)
            
            # Fix common grammar and clarity issues
            optimized_text, grammar_improvements = await self._fix_grammar_and_clarity(optimized_text)
            improvements_made.extend(grammar_improvements)
        
        if optimization_level == OptimizationLevel.ENHANCED:
            # Add context from conversation history
            optimized_text, context_improvements = await self._add_contextual_information(
                optimized_text, conversation_context, user_profile
            )
            improvements_made.extend(context_improvements)
            
            # Expand abbreviations and standardize terminology
            optimized_text, terminology_improvements = await self._standardize_terminology(optimized_text)
            improvements_made.extend(terminology_improvements)
        
        # Determine if clarification is needed
        requires_clarification = len(analysis.missing_info) > 0 or len(analysis.ambiguities) > 0
        clarification_questions = []
        
        if requires_clarification:
            clarification_questions = await self._generate_clarification_questions(
                analysis.query_type, analysis.missing_info, analysis.ambiguities
            )
        
        # Calculate confidence score
        confidence_score = await self._calculate_optimization_confidence(
            analysis, improvements_made, extracted_entities
        )
        
        return OptimizedQuery(
            original_query=user_query,
            optimized_query=optimized_text,
            query_type=analysis.query_type,
            optimization_level=optimization_level,
            improvements_made=improvements_made,
            extracted_entities=extracted_entities,
            confidence_score=confidence_score,
            requires_clarification=requires_clarification,
            clarification_questions=clarification_questions
        )
    
    async def _classify_query_type(self, query: str) -> Tuple[QueryType, float]:
        """Classify the type of query and return confidence score."""
        # Activity logging patterns
        activity_patterns = [
            r"\b(ran|run|jogged|cycled|swam|lifted|did|completed|finished)\b",
            r"\b(workout|exercise|training|gym|activity)\b.*\b(today|yesterday|just|completed)\b",
            r"\d+\s*(km|miles|minutes|hours|reps|sets|laps)"
        ]
        
        # Progress inquiry patterns
        progress_patterns = [
            r"\b(how am i|progress|improvement|stats|statistics)\b",
            r"\b(show me|tell me|what about)\b.*\b(progress|stats|data)\b",
            r"\b(compare|comparison|trend|better|worse)\b"
        ]
        
        # Workout planning patterns
        planning_patterns = [
            r"\b(create|make|plan|design|generate)\b.*\b(workout|exercise|routine)\b",
            r"\b(what should i|recommend|suggest)\b.*\b(workout|exercise)\b",
            r"\b(need|want)\b.*\b(workout|exercise|plan)\b"
        ]
        
        # Coaching patterns
        coaching_patterns = [
            r"\b(help|advice|tips|guidance|coach)\b",
            r"\b(how to|how do i|how can i)\b.*\b(improve|get better|build|lose)\b",
            r"\b(motivate|motivation|encourage|support)\b"
        ]
        
        # Calculate scores
        activity_score = sum(1 for pattern in activity_patterns if re.search(pattern, query, re.IGNORECASE))
        progress_score = sum(1 for pattern in progress_patterns if re.search(pattern, query, re.IGNORECASE))
        planning_score = sum(1 for pattern in planning_patterns if re.search(pattern, query, re.IGNORECASE))
        coaching_score = sum(1 for pattern in coaching_patterns if re.search(pattern, query, re.IGNORECASE))
        
        # Determine type and confidence
        scores = {
            QueryType.ACTIVITY_LOGGING: activity_score,
            QueryType.PROGRESS_INQUIRY: progress_score,
            QueryType.WORKOUT_PLANNING: planning_score,
            QueryType.COACHING_REQUEST: coaching_score
        }
        
        max_score = max(scores.values())
        if max_score == 0:
            return QueryType.UNCLEAR, 0.0
        
        query_type = max(scores, key=scores.get)
        confidence = min(max_score / 3.0, 1.0)  # Normalize to 0-1
        
        return query_type, confidence
    
    async def _extract_entities(self, query: str) -> List[str]:
        """Extract key entities from the query."""
        entities = []
        
        for entity_type, config in self.entity_extractors.items():
            for pattern in config["patterns"]:
                matches = re.findall(pattern, query, re.IGNORECASE)
                if matches:
                    entities.extend([f"{entity_type}:{match}" for match in matches])
        
        return entities
    
    async def _identify_missing_info(self, query_type: QueryType, 
                                   entities: List[str], query: str) -> List[str]:
        """Identify missing information based on query type."""
        missing = []
        
        if query_type == QueryType.ACTIVITY_LOGGING:
            has_activity = any("activity_type:" in e for e in entities)
            has_duration = any("duration:" in e for e in entities)
            has_distance = any("distance:" in e for e in entities)
            
            if not has_activity:
                missing.append("activity_type")
            if not has_duration and not has_distance:
                missing.append("duration_or_distance")
        
        elif query_type == QueryType.WORKOUT_PLANNING:
            has_duration = any("duration:" in e for e in entities)
            has_goal = "goal" in query or "lose" in query or "build" in query
            
            if not has_duration:
                missing.append("workout_duration")
            if not has_goal:
                missing.append("fitness_goal")
        
        return missing
    
    async def _find_ambiguities(self, query: str) -> List[str]:
        """Find ambiguous terms or phrases in the query."""
        ambiguities = []
        
        # Ambiguous pronouns
        if re.search(r"\bit\b", query):
            ambiguities.append("unclear_pronoun_reference")
        
        # Vague time references
        if re.search(r"\bearlier\b|\blater\b|\bsoon\b", query):
            ambiguities.append("vague_time_reference")
        
        # Ambiguous quantities
        if re.search(r"\ba lot\b|\bsome\b|\ba bit\b|\bmuch\b", query):
            ambiguities.append("vague_quantity")
        
        return ambiguities
    
    async def _calculate_complexity(self, query: str, entities: List[str]) -> float:
        """Calculate complexity score of the query."""
        # Base complexity from length
        length_score = min(len(query.split()) / 20.0, 1.0)
        
        # Entity complexity
        entity_score = min(len(entities) / 10.0, 1.0)
        
        # Structural complexity (multiple clauses, questions, etc.)
        structure_score = 0.0
        if "and" in query:
            structure_score += 0.2
        if "?" in query:
            structure_score += 0.1
        if "," in query:
            structure_score += 0.1
        
        return min((length_score + entity_score + structure_score) / 3.0, 1.0)
    
    async def _needs_context(self, query: str, 
                           conversation_context: Optional[List[str]]) -> bool:
        """Determine if the query needs additional context."""
        # Check for context-dependent words
        context_indicators = [
            r"\bit\b", r"\bthat\b", r"\bthis\b", r"\bthey\b",
            r"\bagain\b", r"\btoo\b", r"\balso\b", r"\bmore\b"
        ]
        
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in context_indicators)
    
    async def _apply_rephrasing_patterns(self, query: str, 
                                       query_type: QueryType) -> Tuple[str, List[str]]:
        """Apply rephrasing patterns to improve query clarity."""
        improvements = []
        optimized_query = query
        
        patterns = self.rephrasing_patterns.get(query_type, [])
        
        for pattern_config in patterns:
            pattern = pattern_config["pattern"]
            template = pattern_config["template"]
            
            match = re.search(pattern, optimized_query, re.IGNORECASE)
            if match:
                # Extract groups and create replacement
                groups = match.groups()
                replacements = {}
                
                if query_type == QueryType.ACTIVITY_LOGGING:
                    if "distance" in template and len(groups) >= 2:
                        replacements["distance"] = groups[1]
                        replacements["unit"] = groups[2] if len(groups) > 2 else groups[1]
                    elif "count" in template and len(groups) >= 2:
                        replacements["count"] = groups[1]
                        replacements["exercise"] = "push-ups"
                    elif "duration" in template and len(groups) >= 2:
                        replacements["duration"] = groups[1]
                        replacements["unit"] = groups[2] if len(groups) > 2 else "minutes"
                
                elif query_type == QueryType.PROGRESS_INQUIRY:
                    if "time_period" in template and len(groups) >= 1:
                        replacements["time_period"] = groups[0]
                    elif "comparison_period" in template and len(groups) >= 1:
                        replacements["comparison_period"] = groups[0]
                
                elif query_type == QueryType.WORKOUT_PLANNING:
                    if "duration" in template and len(groups) >= 1:
                        replacements["duration"] = groups[0]
                
                # Apply template with replacements
                try:
                    new_text = template.format(**replacements)
                    optimized_query = re.sub(pattern, new_text, optimized_query, flags=re.IGNORECASE)
                    improvements.append(f"rephrased_{query_type.value}")
                except (KeyError, IndexError):
                    # If template formatting fails, keep original
                    pass
                
                break  # Only apply first matching pattern
        
        return optimized_query, improvements
    
    async def _extract_and_normalize_entities(self, query: str) -> Dict[str, Any]:
        """Extract and normalize entities from the query."""
        entities = {}
        
        for entity_type, config in self.entity_extractors.items():
            for pattern in config["patterns"]:
                matches = re.findall(pattern, query, re.IGNORECASE)
                if matches:
                    normalized = config["normalizer"](matches[0])
                    if normalized:
                        entities[entity_type] = normalized
                    break
        
        return entities
    
    async def _fix_grammar_and_clarity(self, query: str) -> Tuple[str, List[str]]:
        """Fix common grammar and clarity issues."""
        improvements = []
        fixed_query = query
        
        # Fix common contractions
        contractions = {
            r"\bim\b": "I am",
            r"\bive\b": "I have",
            r"\bill\b": "I will",
            r"\bwanna\b": "want to",
            r"\bgonna\b": "going to",
            r"\bcant\b": "cannot"
        }
        
        for pattern, replacement in contractions.items():
            if re.search(pattern, fixed_query, re.IGNORECASE):
                fixed_query = re.sub(pattern, replacement, fixed_query, flags=re.IGNORECASE)
                improvements.append("fixed_contractions")
        
        # Capitalize sentence beginnings
        fixed_query = '. '.join(s.strip().capitalize() for s in fixed_query.split('.'))
        
        # Remove extra whitespace
        fixed_query = re.sub(r'\s+', ' ', fixed_query).strip()
        
        if fixed_query != query:
            improvements.append("improved_grammar")
        
        return fixed_query, improvements
    
    async def _add_contextual_information(self, query: str,
                                        conversation_context: Optional[List[str]],
                                        user_profile: Optional[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Add contextual information to enhance the query."""
        improvements = []
        enhanced_query = query
        
        # Add time context if missing
        if not any(word in query.lower() for word in ["today", "yesterday", "now", "earlier"]):
            if conversation_context and any("today" in msg.lower() for msg in conversation_context[-3:]):
                enhanced_query = f"Today, {enhanced_query.lower()}"
                improvements.append("added_time_context")
        
        # Add user profile context for workout planning
        if user_profile and "workout" in query.lower():
            fitness_level = user_profile.get("fitness_level")
            if fitness_level and fitness_level not in query.lower():
                enhanced_query += f" (fitness level: {fitness_level})"
                improvements.append("added_profile_context")
        
        return enhanced_query, improvements
    
    async def _standardize_terminology(self, query: str) -> Tuple[str, List[str]]:
        """Standardize fitness terminology."""
        improvements = []
        standardized_query = query
        
        # Standardize activity terms
        activity_standardization = {
            r"\bgym\b": "strength training",
            r"\bcardio\b": "cardiovascular exercise",
            r"\blifts?\b": "strength training",
            r"\breps?\b": "repetitions",
            r"\bsets?\b": "sets"
        }
        
        for pattern, replacement in activity_standardization.items():
            if re.search(pattern, standardized_query, re.IGNORECASE):
                standardized_query = re.sub(pattern, replacement, standardized_query, flags=re.IGNORECASE)
                improvements.append("standardized_terminology")
        
        return standardized_query, improvements
    
    async def _generate_clarification_questions(self, query_type: QueryType,
                                              missing_info: List[str],
                                              ambiguities: List[str]) -> List[str]:
        """Generate clarification questions for unclear queries."""
        questions = []
        
        # Get base questions for query type
        base_questions = self.clarification_rules.get(query_type, [])
        
        # Add specific questions for missing info
        if "activity_type" in missing_info:
            questions.append("What type of exercise or activity did you do?")
        
        if "duration_or_distance" in missing_info:
            questions.append("How long did the activity last or what distance did you cover?")
        
        if "workout_duration" in missing_info:
            questions.append("How long should the workout be?")
        
        if "fitness_goal" in missing_info:
            questions.append("What is your main fitness goal for this workout?")
        
        # Add questions for ambiguities
        if "unclear_pronoun_reference" in ambiguities:
            questions.append("Could you clarify what 'it' refers to?")
        
        if "vague_time_reference" in ambiguities:
            questions.append("When exactly did this happen?")
        
        if "vague_quantity" in ambiguities:
            questions.append("Could you be more specific about the amount or quantity?")
        
        # Return top 3 most relevant questions
        return questions[:3]
    
    async def _calculate_optimization_confidence(self, analysis: QueryAnalysis,
                                               improvements: List[str],
                                               entities: Dict[str, Any]) -> float:
        """Calculate confidence score for the optimization."""
        base_confidence = analysis.confidence
        
        # Boost confidence based on improvements made
        improvement_boost = len(improvements) * 0.1
        
        # Boost confidence based on extracted entities
        entity_boost = len(entities) * 0.05
        
        # Reduce confidence for missing info and ambiguities
        missing_penalty = len(analysis.missing_info) * 0.1
        ambiguity_penalty = len(analysis.ambiguities) * 0.05
        
        final_confidence = base_confidence + improvement_boost + entity_boost - missing_penalty - ambiguity_penalty
        
        return max(0.0, min(1.0, final_confidence))
    
    # Normalization helper methods
    def _normalize_duration(self, duration_match: str) -> Optional[Dict[str, Any]]:
        """Normalize duration to minutes."""
        try:
            value = float(duration_match)
            if "h" in duration_match.lower():
                return {"value": value * 60, "unit": "minutes", "original": duration_match}
            elif "m" in duration_match.lower():
                return {"value": value, "unit": "minutes", "original": duration_match}
            elif "s" in duration_match.lower():
                return {"value": value / 60, "unit": "minutes", "original": duration_match}
        except ValueError:
            pass
        return None
    
    def _normalize_distance(self, distance_match: str) -> Optional[Dict[str, Any]]:
        """Normalize distance to kilometers."""
        try:
            value = float(distance_match)
            if "mi" in distance_match.lower():
                return {"value": value * 1.60934, "unit": "km", "original": distance_match}
            elif "m" in distance_match.lower() and "km" not in distance_match.lower():
                return {"value": value / 1000, "unit": "km", "original": distance_match}
            else:
                return {"value": value, "unit": "km", "original": distance_match}
        except ValueError:
            pass
        return None
    
    def _normalize_count(self, count_match: str) -> Optional[Dict[str, Any]]:
        """Normalize count values."""
        try:
            value = int(count_match)
            return {"value": value, "unit": "count", "original": count_match}
        except ValueError:
            pass
        return None
    
    def _normalize_intensity(self, intensity_match: str) -> Optional[Dict[str, Any]]:
        """Normalize intensity levels."""
        intensity_map = {
            "easy": 1, "light": 1, "low": 1,
            "moderate": 2, "medium": 2, "normal": 2,
            "hard": 3, "intense": 3, "high": 3, "vigorous": 3,
            "max": 4, "maximum": 4, "all-out": 4
        }
        
        normalized = intensity_map.get(intensity_match.lower())
        if normalized:
            return {"value": normalized, "unit": "level", "original": intensity_match}
        return None
    
    def _normalize_activity_type(self, activity_match: str) -> Optional[Dict[str, Any]]:
        """Normalize activity types."""
        activity_map = {
            "run": "running", "jog": "running",
            "bike": "cycling", "cycle": "cycling",
            "swim": "swimming",
            "walk": "walking",
            "lift": "strength_training", "weights": "strength_training",
            "yoga": "yoga", "stretch": "flexibility",
            "hiit": "hiit", "interval": "hiit", "circuit": "circuit_training"
        }
        
        normalized = activity_map.get(activity_match.lower())
        if normalized:
            return {"value": normalized, "unit": "activity", "original": activity_match}
        return None


# Global service instance
input_optimization_service = InputOptimizationService()
