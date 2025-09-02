"""Advanced Performance Analysis Engine for Pili Coach Agent.

This service provides sophisticated performance analysis including:
- Multi-dimensional fitness assessment
- Predictive performance modeling
- Comparative benchmarking
- Weakness identification and improvement recommendations
- Performance optimization strategies
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import statistics
import numpy as np
from collections import defaultdict

from config.settings import get_configuration


class PerformanceMetric(Enum):
    """Types of performance metrics to analyze."""
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    POWER = "power"
    SPEED = "speed"
    FLEXIBILITY = "flexibility"
    CONSISTENCY = "consistency"
    VOLUME = "volume"
    INTENSITY = "intensity"
    RECOVERY = "recovery"


class AnalysisPeriod(Enum):
    """Time periods for performance analysis."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL_TIME = "all_time"


class PerformanceLevel(Enum):
    """Performance level classifications."""
    ELITE = "elite"
    ADVANCED = "advanced"
    INTERMEDIATE = "intermediate"
    BEGINNER = "beginner"
    NOVICE = "novice"


@dataclass
class PerformanceScore:
    """Individual performance score for a specific metric."""
    metric: PerformanceMetric
    current_score: float
    percentile_rank: float  # 0-100, where 100 is top performer
    trend_direction: str  # "improving", "stable", "declining"
    trend_magnitude: float  # Rate of change
    confidence_interval: Tuple[float, float]
    benchmark_comparison: Dict[str, float]  # vs peers, vs personal best, etc.


@dataclass
class PerformanceInsight:
    """Actionable insight about performance."""
    category: str
    insight_type: str  # "strength", "weakness", "opportunity", "risk"
    title: str
    description: str
    impact_level: str  # "high", "medium", "low"
    actionable_steps: List[str]
    expected_improvement: str
    confidence: float
    supporting_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceReport:
    """Comprehensive performance analysis report."""
    user_id: str
    analysis_period: AnalysisPeriod
    report_date: datetime
    overall_performance_score: float
    performance_level: PerformanceLevel
    metric_scores: List[PerformanceScore]
    key_insights: List[PerformanceInsight]
    strengths: List[str]
    weaknesses: List[str]
    improvement_opportunities: List[str]
    risk_factors: List[str]
    recommended_focus_areas: List[str]
    predicted_outcomes: Dict[str, Any]
    benchmarking_data: Dict[str, Any]


class PerformanceAnalysisEngine:
    """Advanced engine for analyzing fitness performance."""
    
    def __init__(self):
        self.benchmarks = self._load_performance_benchmarks()
        self.analysis_models = self._load_analysis_models()
        self.insight_rules = self._load_insight_rules()
        
    def _load_performance_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """Load performance benchmarks for different demographics."""
        return {
            "running": {
                "5k_times": {
                    "elite": {"male": 15.0, "female": 17.0},
                    "advanced": {"male": 18.0, "female": 20.0},
                    "intermediate": {"male": 22.0, "female": 25.0},
                    "beginner": {"male": 30.0, "female": 35.0}
                },
                "10k_times": {
                    "elite": {"male": 32.0, "female": 36.0},
                    "advanced": {"male": 38.0, "female": 42.0},
                    "intermediate": {"male": 45.0, "female": 50.0},
                    "beginner": {"male": 60.0, "female": 70.0}
                },
                "weekly_distance": {
                    "elite": {"male": 80, "female": 70},
                    "advanced": {"male": 50, "female": 40},
                    "intermediate": {"male": 25, "female": 20},
                    "beginner": {"male": 10, "female": 8}
                }
            },
            "strength": {
                "bench_press_ratio": {  # Bodyweight ratio
                    "elite": {"male": 1.5, "female": 1.0},
                    "advanced": {"male": 1.25, "female": 0.8},
                    "intermediate": {"male": 1.0, "female": 0.6},
                    "beginner": {"male": 0.75, "female": 0.4}
                },
                "squat_ratio": {
                    "elite": {"male": 2.0, "female": 1.5},
                    "advanced": {"male": 1.75, "female": 1.25},
                    "intermediate": {"male": 1.5, "female": 1.0},
                    "beginner": {"male": 1.0, "female": 0.75}
                },
                "deadlift_ratio": {
                    "elite": {"male": 2.5, "female": 2.0},
                    "advanced": {"male": 2.0, "female": 1.5},
                    "intermediate": {"male": 1.75, "female": 1.25},
                    "beginner": {"male": 1.25, "female": 1.0}
                }
            },
            "consistency": {
                "weekly_frequency": {
                    "elite": 6,
                    "advanced": 5,
                    "intermediate": 4,
                    "beginner": 3
                },
                "adherence_rate": {
                    "elite": 0.95,
                    "advanced": 0.85,
                    "intermediate": 0.75,
                    "beginner": 0.60
                }
            }
        }
    
    def _load_analysis_models(self) -> Dict[str, Any]:
        """Load predictive models and analysis algorithms."""
        return {
            "trend_analysis": {
                "min_data_points": 5,
                "significance_threshold": 0.05,
                "confidence_levels": [0.68, 0.95, 0.99]
            },
            "performance_prediction": {
                "forecast_horizon_days": 90,
                "model_types": ["linear", "exponential", "polynomial"],
                "validation_split": 0.2
            },
            "anomaly_detection": {
                "outlier_threshold": 2.0,  # Standard deviations
                "plateau_detection_window": 14,  # Days
                "decline_alert_threshold": -0.1  # 10% decline
            }
        }
    
    def _load_insight_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load rules for generating performance insights."""
        return {
            "strength_patterns": [
                {
                    "condition": "consistency_score > 0.8 and volume_trend > 0.1",
                    "insight": "High consistency is driving steady volume improvements",
                    "recommendation": "Maintain current schedule and consider progressive overload",
                    "impact": "high"
                },
                {
                    "condition": "strength_gains > 0.15 and endurance_decline < -0.05",
                    "insight": "Strength gains may be compromising endurance",
                    "recommendation": "Add cardiovascular work to balance training",
                    "impact": "medium"
                }
            ],
            "weakness_patterns": [
                {
                    "condition": "consistency_score < 0.6",
                    "insight": "Inconsistent training is limiting progress potential",
                    "recommendation": "Focus on habit formation and schedule optimization",
                    "impact": "high"
                },
                {
                    "condition": "plateau_duration > 21",
                    "insight": "Performance plateau indicates need for program variation",
                    "recommendation": "Introduce new exercises or training methods",
                    "impact": "medium"
                }
            ],
            "opportunity_patterns": [
                {
                    "condition": "recovery_score > 0.8 and intensity_average < 0.7",
                    "insight": "Good recovery allows for higher training intensity",
                    "recommendation": "Gradually increase workout intensity or frequency",
                    "impact": "high"
                },
                {
                    "condition": "single_sport_focus and variety_score < 0.3",
                    "insight": "Cross-training could improve overall fitness and prevent injury",
                    "recommendation": "Add complementary activities to training routine",
                    "impact": "medium"
                }
            ]
        }
    
    async def generate_performance_report(self, user_id: str,
                                        activity_history: List[Dict[str, Any]],
                                        analysis_period: AnalysisPeriod = AnalysisPeriod.MONTHLY,
                                        user_demographics: Optional[Dict[str, Any]] = None) -> PerformanceReport:
        """
        Generate comprehensive performance analysis report.
        
        Args:
            user_id: User ID for the analysis
            activity_history: Historical activity data
            analysis_period: Time period to analyze
            user_demographics: Age, gender, experience level, etc.
            
        Returns:
            PerformanceReport with detailed analysis and insights
        """
        # Filter activities for analysis period
        period_activities = await self._filter_activities_by_period(
            activity_history, analysis_period
        )
        
        if not period_activities:
            return self._create_empty_report(user_id, analysis_period)
        
        # Calculate performance scores for each metric
        metric_scores = []
        for metric in PerformanceMetric:
            score = await self._calculate_performance_score(
                metric, period_activities, user_demographics
            )
            if score:
                metric_scores.append(score)
        
        # Calculate overall performance score
        overall_score = await self._calculate_overall_performance(metric_scores)
        
        # Determine performance level
        performance_level = await self._determine_performance_level(
            overall_score, metric_scores, user_demographics
        )
        
        # Generate insights
        insights = await self._generate_performance_insights(
            metric_scores, period_activities, user_demographics
        )
        
        # Categorize insights
        strengths, weaknesses, opportunities, risks = await self._categorize_insights(insights)
        
        # Generate recommendations
        focus_areas = await self._recommend_focus_areas(
            metric_scores, insights, performance_level
        )
        
        # Create predictions
        predictions = await self._generate_performance_predictions(
            period_activities, metric_scores
        )
        
        # Generate benchmarking data
        benchmarking = await self._generate_benchmarking_data(
            metric_scores, user_demographics
        )
        
        return PerformanceReport(
            user_id=user_id,
            analysis_period=analysis_period,
            report_date=datetime.now(timezone.utc),
            overall_performance_score=overall_score,
            performance_level=performance_level,
            metric_scores=metric_scores,
            key_insights=insights[:5],  # Top 5 insights
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_opportunities=opportunities,
            risk_factors=risks,
            recommended_focus_areas=focus_areas,
            predicted_outcomes=predictions,
            benchmarking_data=benchmarking
        )
    
    async def _filter_activities_by_period(self, activities: List[Dict[str, Any]],
                                         period: AnalysisPeriod) -> List[Dict[str, Any]]:
        """Filter activities based on analysis period."""
        now = datetime.now(timezone.utc)
        
        if period == AnalysisPeriod.WEEKLY:
            cutoff = now - timedelta(weeks=1)
        elif period == AnalysisPeriod.MONTHLY:
            cutoff = now - timedelta(days=30)
        elif period == AnalysisPeriod.QUARTERLY:
            cutoff = now - timedelta(days=90)
        elif period == AnalysisPeriod.YEARLY:
            cutoff = now - timedelta(days=365)
        else:  # ALL_TIME
            return activities
        
        filtered_activities = []
        for activity in activities:
            activity_date = self._parse_activity_date(activity.get('date'))
            if activity_date and activity_date >= cutoff:
                filtered_activities.append(activity)
        
        return filtered_activities
    
    async def _calculate_performance_score(self, metric: PerformanceMetric,
                                         activities: List[Dict[str, Any]],
                                         demographics: Optional[Dict[str, Any]]) -> Optional[PerformanceScore]:
        """Calculate performance score for a specific metric."""
        if metric == PerformanceMetric.ENDURANCE:
            return await self._calculate_endurance_score(activities, demographics)
        elif metric == PerformanceMetric.STRENGTH:
            return await self._calculate_strength_score(activities, demographics)
        elif metric == PerformanceMetric.CONSISTENCY:
            return await self._calculate_consistency_score(activities, demographics)
        elif metric == PerformanceMetric.VOLUME:
            return await self._calculate_volume_score(activities, demographics)
        elif metric == PerformanceMetric.INTENSITY:
            return await self._calculate_intensity_score(activities, demographics)
        # Add more metrics as needed
        return None
    
    async def _calculate_endurance_score(self, activities: List[Dict[str, Any]],
                                       demographics: Optional[Dict[str, Any]]) -> Optional[PerformanceScore]:
        """Calculate endurance performance score."""
        # Filter for endurance activities
        endurance_activities = [
            a for a in activities 
            if a.get('type', '').lower() in ['running', 'cycling', 'swimming', 'cardio']
        ]
        
        if not endurance_activities:
            return None
        
        # Calculate metrics
        distances = []
        durations = []
        
        for activity in endurance_activities:
            if activity.get('value') and activity.get('unit') in ['km', 'miles']:
                distance_km = self._convert_to_km(activity['value'], activity['unit'])
                distances.append(distance_km)
            
            if activity.get('duration'):
                duration_min = self._parse_duration_to_minutes(activity['duration'])
                if duration_min:
                    durations.append(duration_min)
        
        if not distances and not durations:
            return None
        
        # Calculate current performance metrics
        avg_distance = statistics.mean(distances) if distances else 0
        max_distance = max(distances) if distances else 0
        avg_duration = statistics.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Calculate trend
        if len(distances) >= 5:
            recent_avg = statistics.mean(distances[-3:])
            earlier_avg = statistics.mean(distances[:-3])
            trend_direction = "improving" if recent_avg > earlier_avg * 1.05 else \
                            "declining" if recent_avg < earlier_avg * 0.95 else "stable"
            trend_magnitude = (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0
        else:
            trend_direction = "stable"
            trend_magnitude = 0
        
        # Calculate score (simplified scoring system)
        base_score = min(avg_distance * 10 + max_distance * 5, 100)
        
        # Compare to benchmarks
        benchmarks = self._get_demographic_benchmarks("running", demographics)
        percentile = self._calculate_percentile_rank(avg_distance, benchmarks.get("weekly_distance", {}))
        
        return PerformanceScore(
            metric=PerformanceMetric.ENDURANCE,
            current_score=base_score,
            percentile_rank=percentile,
            trend_direction=trend_direction,
            trend_magnitude=trend_magnitude,
            confidence_interval=(base_score * 0.9, base_score * 1.1),
            benchmark_comparison={
                "vs_peers": percentile,
                "vs_personal_best": (avg_distance / max_distance) * 100 if max_distance > 0 else 50
            }
        )
    
    async def _calculate_consistency_score(self, activities: List[Dict[str, Any]],
                                         demographics: Optional[Dict[str, Any]]) -> PerformanceScore:
        """Calculate consistency performance score."""
        if not activities:
            return PerformanceScore(
                metric=PerformanceMetric.CONSISTENCY,
                current_score=0,
                percentile_rank=0,
                trend_direction="stable",
                trend_magnitude=0,
                confidence_interval=(0, 0),
                benchmark_comparison={}
            )
        
        # Calculate consistency metrics
        activity_dates = []
        for activity in activities:
            date = self._parse_activity_date(activity.get('date'))
            if date:
                activity_dates.append(date.date())
        
        unique_dates = set(activity_dates)
        total_days = (max(activity_dates) - min(activity_dates)).days + 1 if activity_dates else 1
        
        # Calculate scores
        frequency_score = len(unique_dates) / max(total_days / 7, 1)  # Activities per week
        adherence_rate = len(unique_dates) / total_days if total_days > 0 else 0
        
        # Weekly consistency
        weekly_counts = defaultdict(int)
        for date in activity_dates:
            week_key = date.strftime("%Y-W%U")
            weekly_counts[week_key] += 1
        
        weekly_consistency = statistics.stdev(weekly_counts.values()) if len(weekly_counts) > 1 else 0
        consistency_score = max(0, 100 - weekly_consistency * 10)
        
        # Trend analysis
        if len(weekly_counts) >= 4:
            recent_weeks = list(weekly_counts.values())[-2:]
            earlier_weeks = list(weekly_counts.values())[:-2]
            recent_avg = statistics.mean(recent_weeks)
            earlier_avg = statistics.mean(earlier_weeks)
            
            trend_direction = "improving" if recent_avg > earlier_avg * 1.1 else \
                            "declining" if recent_avg < earlier_avg * 0.9 else "stable"
            trend_magnitude = (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0
        else:
            trend_direction = "stable"
            trend_magnitude = 0
        
        # Benchmarking
        benchmarks = self.benchmarks["consistency"]
        percentile = 0
        for level, freq in benchmarks["weekly_frequency"].items():
            if frequency_score >= freq:
                percentile += 20
        
        return PerformanceScore(
            metric=PerformanceMetric.CONSISTENCY,
            current_score=consistency_score,
            percentile_rank=percentile,
            trend_direction=trend_direction,
            trend_magnitude=trend_magnitude,
            confidence_interval=(consistency_score * 0.85, consistency_score * 1.15),
            benchmark_comparison={
                "frequency_vs_peers": percentile,
                "adherence_rate": adherence_rate * 100
            }
        )
    
    async def _calculate_volume_score(self, activities: List[Dict[str, Any]],
                                    demographics: Optional[Dict[str, Any]]) -> PerformanceScore:
        """Calculate training volume score."""
        if not activities:
            return self._create_empty_score(PerformanceMetric.VOLUME)
        
        # Calculate total volume metrics
        total_duration = 0
        total_distance = 0
        total_activities = len(activities)
        
        for activity in activities:
            # Duration
            if activity.get('duration'):
                duration = self._parse_duration_to_minutes(activity['duration'])
                if duration:
                    total_duration += duration
            
            # Distance
            if activity.get('value') and activity.get('unit') in ['km', 'miles']:
                distance_km = self._convert_to_km(activity['value'], activity['unit'])
                total_distance += distance_km
        
        # Calculate weekly averages
        if activities:
            date_range = self._get_date_range(activities)
            weeks = max(date_range.days / 7, 1)
            
            weekly_duration = total_duration / weeks
            weekly_distance = total_distance / weeks
            weekly_frequency = total_activities / weeks
        else:
            weekly_duration = weekly_distance = weekly_frequency = 0
        
        # Score calculation (weighted combination)
        duration_score = min(weekly_duration / 5, 20)  # Up to 20 points for duration
        distance_score = min(weekly_distance * 2, 30)  # Up to 30 points for distance
        frequency_score = min(weekly_frequency * 10, 50)  # Up to 50 points for frequency
        
        volume_score = duration_score + distance_score + frequency_score
        
        # Trend analysis
        trend_direction, trend_magnitude = await self._calculate_volume_trend(activities)
        
        # Percentile ranking (simplified)
        percentile = min(volume_score, 100)
        
        return PerformanceScore(
            metric=PerformanceMetric.VOLUME,
            current_score=volume_score,
            percentile_rank=percentile,
            trend_direction=trend_direction,
            trend_magnitude=trend_magnitude,
            confidence_interval=(volume_score * 0.9, volume_score * 1.1),
            benchmark_comparison={
                "weekly_duration": weekly_duration,
                "weekly_distance": weekly_distance,
                "weekly_frequency": weekly_frequency
            }
        )
    
    async def _calculate_intensity_score(self, activities: List[Dict[str, Any]],
                                       demographics: Optional[Dict[str, Any]]) -> PerformanceScore:
        """Calculate training intensity score."""
        if not activities:
            return self._create_empty_score(PerformanceMetric.INTENSITY)
        
        intensity_scores = []
        
        for activity in activities:
            # Estimate intensity from pace if available
            if (activity.get('value') and activity.get('duration') and 
                activity.get('unit') in ['km', 'miles']):
                
                distance_km = self._convert_to_km(activity['value'], activity['unit'])
                duration_min = self._parse_duration_to_minutes(activity['duration'])
                
                if distance_km > 0 and duration_min > 0:
                    pace_min_per_km = duration_min / distance_km
                    
                    # Intensity based on pace (lower pace = higher intensity)
                    if pace_min_per_km <= 4:  # Very fast
                        intensity_scores.append(90)
                    elif pace_min_per_km <= 5:  # Fast
                        intensity_scores.append(75)
                    elif pace_min_per_km <= 6:  # Moderate-fast
                        intensity_scores.append(60)
                    elif pace_min_per_km <= 8:  # Moderate
                        intensity_scores.append(45)
                    else:  # Easy
                        intensity_scores.append(30)
            
            # Estimate from activity type if no pace available
            elif activity.get('type'):
                activity_type = activity.get('type', '').lower()
                if activity_type in ['hiit', 'sprint', 'interval']:
                    intensity_scores.append(85)
                elif activity_type in ['running', 'cycling']:
                    intensity_scores.append(60)
                elif activity_type in ['strength', 'weightlifting']:
                    intensity_scores.append(70)
                elif activity_type in ['yoga', 'stretching']:
                    intensity_scores.append(25)
                else:
                    intensity_scores.append(50)
        
        if not intensity_scores:
            return self._create_empty_score(PerformanceMetric.INTENSITY)
        
        avg_intensity = statistics.mean(intensity_scores)
        max_intensity = max(intensity_scores)
        
        # Trend analysis
        if len(intensity_scores) >= 5:
            recent_avg = statistics.mean(intensity_scores[-3:])
            earlier_avg = statistics.mean(intensity_scores[:-3])
            trend_direction = "improving" if recent_avg > earlier_avg * 1.05 else \
                            "declining" if recent_avg < earlier_avg * 0.95 else "stable"
            trend_magnitude = (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0
        else:
            trend_direction = "stable"
            trend_magnitude = 0
        
        return PerformanceScore(
            metric=PerformanceMetric.INTENSITY,
            current_score=avg_intensity,
            percentile_rank=min(avg_intensity, 100),
            trend_direction=trend_direction,
            trend_magnitude=trend_magnitude,
            confidence_interval=(avg_intensity * 0.9, avg_intensity * 1.1),
            benchmark_comparison={
                "average_intensity": avg_intensity,
                "peak_intensity": max_intensity,
                "intensity_variability": statistics.stdev(intensity_scores) if len(intensity_scores) > 1 else 0
            }
        )
    
    async def _calculate_overall_performance(self, metric_scores: List[PerformanceScore]) -> float:
        """Calculate overall performance score from individual metrics."""
        if not metric_scores:
            return 0.0
        
        # Weighted average of metric scores
        weights = {
            PerformanceMetric.CONSISTENCY: 0.3,
            PerformanceMetric.VOLUME: 0.25,
            PerformanceMetric.ENDURANCE: 0.2,
            PerformanceMetric.INTENSITY: 0.15,
            PerformanceMetric.STRENGTH: 0.1
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for score in metric_scores:
            weight = weights.get(score.metric, 0.1)
            weighted_sum += score.current_score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0
    
    async def _determine_performance_level(self, overall_score: float,
                                         metric_scores: List[PerformanceScore],
                                         demographics: Optional[Dict[str, Any]]) -> PerformanceLevel:
        """Determine user's performance level."""
        if overall_score >= 85:
            return PerformanceLevel.ELITE
        elif overall_score >= 70:
            return PerformanceLevel.ADVANCED
        elif overall_score >= 50:
            return PerformanceLevel.INTERMEDIATE
        elif overall_score >= 25:
            return PerformanceLevel.BEGINNER
        else:
            return PerformanceLevel.NOVICE
    
    async def _generate_performance_insights(self, metric_scores: List[PerformanceScore],
                                           activities: List[Dict[str, Any]],
                                           demographics: Optional[Dict[str, Any]]) -> List[PerformanceInsight]:
        """Generate actionable performance insights."""
        insights = []
        
        # Analyze each metric for insights
        for score in metric_scores:
            # Strength insights
            if score.percentile_rank >= 75:
                insights.append(PerformanceInsight(
                    category=score.metric.value,
                    insight_type="strength",
                    title=f"Excellent {score.metric.value.title()} Performance",
                    description=f"Your {score.metric.value} ranks in the top 25% of users",
                    impact_level="high",
                    actionable_steps=[
                        f"Maintain current {score.metric.value} training approach",
                        f"Consider mentoring others in {score.metric.value}",
                        f"Use {score.metric.value} strength to support weaker areas"
                    ],
                    expected_improvement="Sustained high performance",
                    confidence=0.85
                ))
            
            # Weakness insights
            elif score.percentile_rank <= 25:
                insights.append(PerformanceInsight(
                    category=score.metric.value,
                    insight_type="weakness",
                    title=f"{score.metric.value.title()} Needs Attention",
                    description=f"Your {score.metric.value} is below average and limiting overall progress",
                    impact_level="high",
                    actionable_steps=[
                        f"Increase focus on {score.metric.value} training",
                        f"Consider working with a specialist in {score.metric.value}",
                        f"Set specific {score.metric.value} improvement goals"
                    ],
                    expected_improvement="20-30% improvement possible in 8-12 weeks",
                    confidence=0.8
                ))
            
            # Trend insights
            if score.trend_direction == "improving" and score.trend_magnitude > 0.1:
                insights.append(PerformanceInsight(
                    category=score.metric.value,
                    insight_type="opportunity",
                    title=f"Strong {score.metric.value.title()} Momentum",
                    description=f"Your {score.metric.value} is improving at {score.trend_magnitude:.1%} rate",
                    impact_level="medium",
                    actionable_steps=[
                        "Continue current training approach",
                        "Gradually increase training load",
                        "Monitor for signs of overtraining"
                    ],
                    expected_improvement="Continued upward trend",
                    confidence=0.75
                ))
            elif score.trend_direction == "declining" and score.trend_magnitude < -0.1:
                insights.append(PerformanceInsight(
                    category=score.metric.value,
                    insight_type="risk",
                    title=f"{score.metric.value.title()} Declining",
                    description=f"Your {score.metric.value} has declined by {abs(score.trend_magnitude):.1%}",
                    impact_level="medium",
                    actionable_steps=[
                        "Review recent training changes",
                        "Check for overtraining or burnout",
                        "Consider deload week or rest"
                    ],
                    expected_improvement="Trend reversal with appropriate adjustments",
                    confidence=0.7
                ))
        
        # Cross-metric insights
        consistency_score = next((s for s in metric_scores if s.metric == PerformanceMetric.CONSISTENCY), None)
        volume_score = next((s for s in metric_scores if s.metric == PerformanceMetric.VOLUME), None)
        
        if consistency_score and volume_score:
            if consistency_score.current_score < 60 and volume_score.current_score > 70:
                insights.append(PerformanceInsight(
                    category="training_balance",
                    insight_type="opportunity",
                    title="High Volume, Low Consistency Pattern",
                    description="You train hard when you do train, but inconsistently",
                    impact_level="high",
                    actionable_steps=[
                        "Reduce individual workout intensity",
                        "Increase workout frequency",
                        "Focus on habit formation strategies"
                    ],
                    expected_improvement="Better overall progress with more consistent training",
                    confidence=0.8
                ))
        
        return sorted(insights, key=lambda x: (x.impact_level == "high", x.confidence), reverse=True)
    
    async def _categorize_insights(self, insights: List[PerformanceInsight]) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Categorize insights into strengths, weaknesses, opportunities, and risks."""
        strengths = [i.title for i in insights if i.insight_type == "strength"]
        weaknesses = [i.title for i in insights if i.insight_type == "weakness"]
        opportunities = [i.title for i in insights if i.insight_type == "opportunity"]
        risks = [i.title for i in insights if i.insight_type == "risk"]
        
        return strengths, weaknesses, opportunities, risks
    
    async def _recommend_focus_areas(self, metric_scores: List[PerformanceScore],
                                   insights: List[PerformanceInsight],
                                   performance_level: PerformanceLevel) -> List[str]:
        """Recommend focus areas for improvement."""
        focus_areas = []
        
        # Priority 1: Address major weaknesses
        weak_metrics = [s for s in metric_scores if s.percentile_rank <= 25]
        if weak_metrics:
            weakest = min(weak_metrics, key=lambda x: x.percentile_rank)
            focus_areas.append(f"Priority: Improve {weakest.metric.value}")
        
        # Priority 2: Leverage declining strengths
        declining_strengths = [
            s for s in metric_scores 
            if s.percentile_rank >= 60 and s.trend_direction == "declining"
        ]
        if declining_strengths:
            focus_areas.append(f"Maintain: {declining_strengths[0].metric.value} performance")
        
        # Priority 3: Build on improving areas
        improving_metrics = [
            s for s in metric_scores 
            if s.trend_direction == "improving" and s.trend_magnitude > 0.05
        ]
        if improving_metrics:
            best_improving = max(improving_metrics, key=lambda x: x.trend_magnitude)
            focus_areas.append(f"Accelerate: {best_improving.metric.value} gains")
        
        return focus_areas[:3]  # Top 3 focus areas
    
    async def _generate_performance_predictions(self, activities: List[Dict[str, Any]],
                                              metric_scores: List[PerformanceScore]) -> Dict[str, Any]:
        """Generate performance predictions."""
        predictions = {}
        
        # Simple linear trend prediction
        for score in metric_scores:
            if score.trend_magnitude != 0:
                predicted_4_weeks = score.current_score * (1 + score.trend_magnitude * 4)
                predicted_12_weeks = score.current_score * (1 + score.trend_magnitude * 12)
                
                predictions[f"{score.metric.value}_4_weeks"] = max(0, min(100, predicted_4_weeks))
                predictions[f"{score.metric.value}_12_weeks"] = max(0, min(100, predicted_12_weeks))
        
        return predictions
    
    async def _generate_benchmarking_data(self, metric_scores: List[PerformanceScore],
                                        demographics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate benchmarking comparison data."""
        benchmarking = {}
        
        for score in metric_scores:
            benchmarking[score.metric.value] = {
                "current_percentile": score.percentile_rank,
                "vs_peers": score.benchmark_comparison,
                "performance_gap": 75 - score.percentile_rank  # Gap to 75th percentile
            }
        
        return benchmarking
    
    # Helper methods
    def _create_empty_report(self, user_id: str, period: AnalysisPeriod) -> PerformanceReport:
        """Create empty report for users with no data."""
        return PerformanceReport(
            user_id=user_id,
            analysis_period=period,
            report_date=datetime.now(timezone.utc),
            overall_performance_score=0,
            performance_level=PerformanceLevel.NOVICE,
            metric_scores=[],
            key_insights=[],
            strengths=[],
            weaknesses=["Insufficient data for analysis"],
            improvement_opportunities=["Start logging activities consistently"],
            risk_factors=[],
            recommended_focus_areas=["Begin with basic activity tracking"],
            predicted_outcomes={},
            benchmarking_data={}
        )
    
    def _create_empty_score(self, metric: PerformanceMetric) -> PerformanceScore:
        """Create empty score for missing metrics."""
        return PerformanceScore(
            metric=metric,
            current_score=0,
            percentile_rank=0,
            trend_direction="stable",
            trend_magnitude=0,
            confidence_interval=(0, 0),
            benchmark_comparison={}
        )
    
    def _parse_activity_date(self, date_str: Any) -> Optional[datetime]:
        """Parse activity date string to datetime object."""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        try:
            if isinstance(date_str, str):
                if 'T' in date_str:
                    parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
                else:
                    parsed = datetime.fromisoformat(date_str)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
        except (ValueError, TypeError):
            return None
        
        return None
    
    def _parse_duration_to_minutes(self, duration: Any) -> Optional[float]:
        """Parse duration to minutes."""
        if isinstance(duration, (int, float)):
            return float(duration)
        
        if isinstance(duration, str):
            try:
                return float(duration)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _convert_to_km(self, value: Any, unit: str) -> float:
        """Convert distance to kilometers."""
        try:
            value = float(value)
            unit = unit.lower()
            
            if unit in ["km", "kilometers"]:
                return value
            elif unit in ["miles", "mi"]:
                return value * 1.60934
            elif unit in ["meters", "m"]:
                return value / 1000
            else:
                return value
        except (ValueError, TypeError):
            return 0.0
    
    def _get_date_range(self, activities: List[Dict[str, Any]]) -> timedelta:
        """Get date range of activities."""
        dates = []
        for activity in activities:
            date = self._parse_activity_date(activity.get('date'))
            if date:
                dates.append(date)
        
        if len(dates) >= 2:
            return max(dates) - min(dates)
        else:
            return timedelta(days=1)
    
    async def _calculate_volume_trend(self, activities: List[Dict[str, Any]]) -> Tuple[str, float]:
        """Calculate volume trend direction and magnitude."""
        if len(activities) < 6:
            return "stable", 0.0
        
        # Group by weeks
        weekly_volumes = defaultdict(float)
        for activity in activities:
            date = self._parse_activity_date(activity.get('date'))
            if date:
                week_key = date.strftime("%Y-W%U")
                duration = self._parse_duration_to_minutes(activity.get('duration', 0))
                weekly_volumes[week_key] += duration
        
        volumes = list(weekly_volumes.values())
        if len(volumes) < 3:
            return "stable", 0.0
        
        recent_avg = statistics.mean(volumes[-2:])
        earlier_avg = statistics.mean(volumes[:-2])
        
        if earlier_avg > 0:
            change = (recent_avg - earlier_avg) / earlier_avg
            
            if change > 0.1:
                return "improving", change
            elif change < -0.1:
                return "declining", change
            else:
                return "stable", change
        
        return "stable", 0.0
    
    def _get_demographic_benchmarks(self, activity_type: str, demographics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get benchmarks for specific demographics."""
        if not demographics:
            return self.benchmarks.get(activity_type, {})
        
        # This would be more sophisticated in a real implementation
        return self.benchmarks.get(activity_type, {})
    
    def _calculate_percentile_rank(self, value: float, benchmark_dict: Dict[str, Any]) -> float:
        """Calculate percentile rank against benchmarks."""
        if not benchmark_dict:
            return 50.0  # Default to median
        
        # Simplified percentile calculation
        # In reality, this would use proper statistical distributions
        levels = ["novice", "beginner", "intermediate", "advanced", "elite"]
        
        for i, level in enumerate(levels):
            if level in benchmark_dict:
                benchmark_value = benchmark_dict[level]
                if isinstance(benchmark_value, dict):
                    benchmark_value = benchmark_value.get("male", benchmark_value.get("female", 0))
                
                if value >= benchmark_value:
                    return min(100, (i + 1) * 20 + 10)  # Rough percentile mapping
        
        return 10  # Below all benchmarks


# Global service instance
performance_analysis_engine = PerformanceAnalysisEngine()
