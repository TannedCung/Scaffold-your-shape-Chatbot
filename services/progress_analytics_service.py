"""Progress Analytics Service for Pili Logger Agent.

This service provides comprehensive analytics and insights for user fitness
progress, including trends, achievements, and personalized recommendations.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict, Counter

from config.settings import get_configuration


class TrendDirection(Enum):
    """Direction of fitness trends."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class AchievementType(Enum):
    """Types of fitness achievements."""
    PERSONAL_RECORD = "personal_record"
    CONSISTENCY = "consistency"
    MILESTONE = "milestone"
    VARIETY = "variety"
    VOLUME = "volume"


@dataclass
class Achievement:
    """Represents a fitness achievement."""
    type: AchievementType
    title: str
    description: str
    date_earned: datetime
    activity_type: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None


@dataclass
class TrendAnalysis:
    """Analysis of fitness trends over time."""
    metric: str
    direction: TrendDirection
    change_percentage: float
    period_days: int
    confidence: float
    description: str
    data_points: int


@dataclass
class ProgressInsight:
    """Insights about user's fitness progress."""
    category: str
    insight_type: str
    message: str
    confidence: float
    recommendation: Optional[str] = None
    supporting_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressSummary:
    """Comprehensive progress summary for a user."""
    user_id: str
    period_start: datetime
    period_end: datetime
    total_activities: int
    total_duration_minutes: float
    total_distance_km: float
    estimated_calories: int
    active_days: int
    activity_types: List[str]
    achievements: List[Achievement]
    trends: List[TrendAnalysis]
    insights: List[ProgressInsight]
    consistency_score: float
    variety_score: float
    improvement_score: float


class ProgressAnalyticsService:
    """Service for analyzing user fitness progress and generating insights."""
    
    def __init__(self):
        self.achievement_thresholds = self._load_achievement_thresholds()
        self.trend_analysis_periods = [7, 14, 30, 90]  # Days to analyze
        
    def _load_achievement_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Load thresholds for different achievement types."""
        return {
            "distance_milestones": {
                "running": [5, 10, 21.1, 42.2],  # 5k, 10k, half marathon, marathon
                "cycling": [25, 50, 100, 200],    # km milestones
                "swimming": [1, 2.5, 5, 10]       # km milestones
            },
            "consistency_streaks": {
                "daily": [3, 7, 14, 30],          # Days in a row
                "weekly": [2, 4, 8, 12]           # Weeks in a row
            },
            "volume_achievements": {
                "monthly_distance": [50, 100, 200, 300],  # km per month
                "monthly_duration": [600, 1200, 1800, 2400]  # minutes per month
            }
        }
    
    async def generate_progress_summary(self, user_id: str, 
                                      period_days: int = 30,
                                      activity_history: Optional[List[Dict[str, Any]]] = None) -> ProgressSummary:
        """
        Generate comprehensive progress summary for a user.
        
        Args:
            user_id: User ID to analyze
            period_days: Number of days to analyze (default: 30)
            activity_history: List of user activities (if not provided, will fetch from MCP)
            
        Returns:
            ProgressSummary with comprehensive analytics
        """
        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)
        period_end = datetime.now(timezone.utc)
        
        # Get activity history if not provided
        if activity_history is None:
            activity_history = await self._fetch_user_activities(user_id, period_start, period_end)
        
        # Filter activities for the period
        period_activities = [
            activity for activity in activity_history
            if self._parse_activity_date(activity.get('date')) >= period_start
        ]
        
        # Calculate basic metrics
        basic_metrics = await self._calculate_basic_metrics(period_activities)
        
        # Analyze trends
        trends = await self._analyze_trends(activity_history, period_days)
        
        # Detect achievements
        achievements = await self._detect_achievements(user_id, activity_history)
        
        # Generate insights
        insights = await self._generate_insights(period_activities, trends, achievements)
        
        # Calculate scores
        consistency_score = await self._calculate_consistency_score(period_activities, period_days)
        variety_score = await self._calculate_variety_score(period_activities)
        improvement_score = await self._calculate_improvement_score(trends)
        
        return ProgressSummary(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            total_activities=basic_metrics['total_activities'],
            total_duration_minutes=basic_metrics['total_duration'],
            total_distance_km=basic_metrics['total_distance'],
            estimated_calories=basic_metrics['estimated_calories'],
            active_days=basic_metrics['active_days'],
            activity_types=basic_metrics['activity_types'],
            achievements=achievements,
            trends=trends,
            insights=insights,
            consistency_score=consistency_score,
            variety_score=variety_score,
            improvement_score=improvement_score
        )
    
    async def _fetch_user_activities(self, user_id: str, 
                                   start_date: datetime, 
                                   end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch user activities from MCP server or database."""
        # This would integrate with the actual data source
        # For now, return empty list as placeholder
        return []
    
    async def _calculate_basic_metrics(self, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic activity metrics."""
        total_activities = len(activities)
        total_duration = sum(
            self._parse_duration(activity.get('duration', 0)) 
            for activity in activities
        )
        total_distance = sum(
            self._parse_distance_to_km(
                activity.get('value', 0), 
                activity.get('unit', 'km')
            ) 
            for activity in activities
            if activity.get('unit') in ['km', 'miles', 'meters']
        )
        estimated_calories = sum(
            activity.get('estimated_calories', 0) 
            for activity in activities
        )
        
        # Count active days
        activity_dates = set()
        for activity in activities:
            date = self._parse_activity_date(activity.get('date'))
            if date:
                activity_dates.add(date.date())
        
        active_days = len(activity_dates)
        
        # Get activity types
        activity_types = list(set(
            activity.get('type', '').lower() 
            for activity in activities
            if activity.get('type')
        ))
        
        return {
            'total_activities': total_activities,
            'total_duration': total_duration,
            'total_distance': total_distance,
            'estimated_calories': int(estimated_calories),
            'active_days': active_days,
            'activity_types': activity_types
        }
    
    async def _analyze_trends(self, activities: List[Dict[str, Any]], 
                            period_days: int) -> List[TrendAnalysis]:
        """Analyze trends in user's fitness activities."""
        trends = []
        
        # Analyze different metrics
        metrics_to_analyze = [
            ('weekly_distance', 'Distance per week'),
            ('weekly_duration', 'Duration per week'),
            ('weekly_frequency', 'Activities per week'),
            ('average_pace', 'Average pace')
        ]
        
        for metric_key, metric_name in metrics_to_analyze:
            trend = await self._analyze_metric_trend(activities, metric_key, metric_name, period_days)
            if trend:
                trends.append(trend)
        
        return trends
    
    async def _analyze_metric_trend(self, activities: List[Dict[str, Any]], 
                                  metric_key: str, metric_name: str, 
                                  period_days: int) -> Optional[TrendAnalysis]:
        """Analyze trend for a specific metric."""
        if not activities:
            return None
        
        # Group activities by week
        weekly_data = defaultdict(list)
        
        for activity in activities:
            date = self._parse_activity_date(activity.get('date'))
            if not date:
                continue
                
            # Get week number
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.strftime('%Y-%W')
            
            weekly_data[week_key].append(activity)
        
        if len(weekly_data) < 2:
            return TrendAnalysis(
                metric=metric_name,
                direction=TrendDirection.INSUFFICIENT_DATA,
                change_percentage=0.0,
                period_days=period_days,
                confidence=0.0,
                description="Not enough data to determine trend",
                data_points=len(weekly_data)
            )
        
        # Calculate weekly values for the metric
        weekly_values = []
        
        for week_activities in weekly_data.values():
            if metric_key == 'weekly_distance':
                value = sum(
                    self._parse_distance_to_km(a.get('value', 0), a.get('unit', 'km'))
                    for a in week_activities
                    if a.get('unit') in ['km', 'miles', 'meters']
                )
            elif metric_key == 'weekly_duration':
                value = sum(
                    self._parse_duration(a.get('duration', 0))
                    for a in week_activities
                )
            elif metric_key == 'weekly_frequency':
                value = len(week_activities)
            elif metric_key == 'average_pace':
                paces = []
                for a in week_activities:
                    if a.get('pace_min_per_km'):
                        paces.append(a['pace_min_per_km'])
                value = statistics.mean(paces) if paces else 0
            else:
                value = 0
            
            weekly_values.append(value)
        
        if not weekly_values or all(v == 0 for v in weekly_values):
            return None
        
        # Calculate trend
        if len(weekly_values) >= 2:
            recent_avg = statistics.mean(weekly_values[-2:])  # Last 2 weeks
            earlier_avg = statistics.mean(weekly_values[:-2]) if len(weekly_values) > 2 else weekly_values[0]
            
            if earlier_avg > 0:
                change_percentage = ((recent_avg - earlier_avg) / earlier_avg) * 100
            else:
                change_percentage = 0
            
            # Determine direction
            if abs(change_percentage) < 5:
                direction = TrendDirection.STABLE
            elif change_percentage > 0:
                direction = TrendDirection.IMPROVING
            else:
                direction = TrendDirection.DECLINING
            
            # Calculate confidence based on data consistency
            if len(weekly_values) >= 4:
                confidence = min(0.9, len(weekly_values) * 0.15)
            else:
                confidence = 0.5
            
            # Generate description
            if direction == TrendDirection.IMPROVING:
                description = f"{metric_name} is improving by {abs(change_percentage):.1f}%"
            elif direction == TrendDirection.DECLINING:
                description = f"{metric_name} is declining by {abs(change_percentage):.1f}%"
            else:
                description = f"{metric_name} remains stable"
            
            return TrendAnalysis(
                metric=metric_name,
                direction=direction,
                change_percentage=change_percentage,
                period_days=period_days,
                confidence=confidence,
                description=description,
                data_points=len(weekly_values)
            )
        
        return None
    
    async def _detect_achievements(self, user_id: str, 
                                 activities: List[Dict[str, Any]]) -> List[Achievement]:
        """Detect new achievements based on activity history."""
        achievements = []
        
        # Personal Records
        pr_achievements = await self._detect_personal_records(activities)
        achievements.extend(pr_achievements)
        
        # Consistency achievements
        consistency_achievements = await self._detect_consistency_achievements(activities)
        achievements.extend(consistency_achievements)
        
        # Distance milestones
        milestone_achievements = await self._detect_milestone_achievements(activities)
        achievements.extend(milestone_achievements)
        
        # Volume achievements
        volume_achievements = await self._detect_volume_achievements(activities)
        achievements.extend(volume_achievements)
        
        return achievements
    
    async def _detect_personal_records(self, activities: List[Dict[str, Any]]) -> List[Achievement]:
        """Detect personal record achievements."""
        achievements = []
        
        # Group activities by type
        activities_by_type = defaultdict(list)
        for activity in activities:
            activity_type = activity.get('type', '').lower()
            if activity_type:
                activities_by_type[activity_type].append(activity)
        
        # Check for PRs in each activity type
        for activity_type, type_activities in activities_by_type.items():
            # Sort by date
            type_activities.sort(key=lambda x: self._parse_activity_date(x.get('date', '')))
            
            # Check distance PRs
            max_distance = 0
            for activity in type_activities:
                distance = self._parse_distance_to_km(
                    activity.get('value', 0), 
                    activity.get('unit', 'km')
                )
                if distance > max_distance:
                    max_distance = distance
                    # This is a PR - would check if it's recent
                    activity_date = self._parse_activity_date(activity.get('date'))
                    if activity_date and (datetime.now(timezone.utc) - activity_date).days <= 7:
                        achievements.append(Achievement(
                            type=AchievementType.PERSONAL_RECORD,
                            title=f"{activity_type.title()} Distance PR!",
                            description=f"New personal record: {distance:.1f}km",
                            date_earned=activity_date,
                            activity_type=activity_type,
                            value=distance,
                            unit="km"
                        ))
        
        return achievements
    
    async def _detect_consistency_achievements(self, activities: List[Dict[str, Any]]) -> List[Achievement]:
        """Detect consistency-based achievements."""
        achievements = []
        
        # Get activity dates
        activity_dates = []
        for activity in activities:
            date = self._parse_activity_date(activity.get('date'))
            if date:
                activity_dates.append(date.date())
        
        activity_dates = sorted(set(activity_dates))
        
        if not activity_dates:
            return achievements
        
        # Find current streak
        current_streak = 0
        today = datetime.now().date()
        
        # Check if there's activity today or yesterday
        if activity_dates and (activity_dates[-1] == today or activity_dates[-1] == today - timedelta(days=1)):
            current_streak = 1
            check_date = activity_dates[-1] - timedelta(days=1)
            
            # Count consecutive days backwards
            for i in range(len(activity_dates) - 2, -1, -1):
                if activity_dates[i] == check_date:
                    current_streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break
        
        # Check for streak achievements
        streak_thresholds = self.achievement_thresholds["consistency_streaks"]["daily"]
        for threshold in streak_thresholds:
            if current_streak >= threshold:
                # Check if this is a new achievement (would need to track previous achievements)
                achievements.append(Achievement(
                    type=AchievementType.CONSISTENCY,
                    title=f"{threshold}-Day Streak!",
                    description=f"Completed activities for {current_streak} days in a row",
                    date_earned=datetime.now(timezone.utc),
                    value=current_streak,
                    unit="days"
                ))
        
        return achievements
    
    async def _detect_milestone_achievements(self, activities: List[Dict[str, Any]]) -> List[Achievement]:
        """Detect distance milestone achievements."""
        achievements = []
        
        # Group by activity type and check cumulative distances
        activities_by_type = defaultdict(list)
        for activity in activities:
            activity_type = activity.get('type', '').lower()
            if activity_type in self.achievement_thresholds["distance_milestones"]:
                activities_by_type[activity_type].append(activity)
        
        for activity_type, type_activities in activities_by_type.items():
            cumulative_distance = 0
            milestones = self.achievement_thresholds["distance_milestones"][activity_type]
            
            for activity in sorted(type_activities, key=lambda x: self._parse_activity_date(x.get('date', ''))):
                distance = self._parse_distance_to_km(
                    activity.get('value', 0),
                    activity.get('unit', 'km')
                )
                cumulative_distance += distance
                
                # Check if we've crossed any milestones
                for milestone in milestones:
                    if cumulative_distance >= milestone:
                        activity_date = self._parse_activity_date(activity.get('date'))
                        if activity_date and (datetime.now(timezone.utc) - activity_date).days <= 30:
                            achievements.append(Achievement(
                                type=AchievementType.MILESTONE,
                                title=f"{milestone}km {activity_type.title()} Milestone!",
                                description=f"Reached {milestone}km total distance in {activity_type}",
                                date_earned=activity_date,
                                activity_type=activity_type,
                                value=milestone,
                                unit="km"
                            ))
        
        return achievements
    
    async def _detect_volume_achievements(self, activities: List[Dict[str, Any]]) -> List[Achievement]:
        """Detect volume-based achievements (monthly totals)."""
        achievements = []
        
        # Calculate monthly totals
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_activities = [
            activity for activity in activities
            if self._parse_activity_date(activity.get('date', '')) >= current_month
        ]
        
        if not month_activities:
            return achievements
        
        # Calculate monthly distance
        monthly_distance = sum(
            self._parse_distance_to_km(
                activity.get('value', 0),
                activity.get('unit', 'km')
            )
            for activity in month_activities
            if activity.get('unit') in ['km', 'miles', 'meters']
        )
        
        # Calculate monthly duration
        monthly_duration = sum(
            self._parse_duration(activity.get('duration', 0))
            for activity in month_activities
        )
        
        # Check distance achievements
        distance_thresholds = self.achievement_thresholds["volume_achievements"]["monthly_distance"]
        for threshold in distance_thresholds:
            if monthly_distance >= threshold:
                achievements.append(Achievement(
                    type=AchievementType.VOLUME,
                    title=f"{threshold}km Month!",
                    description=f"Completed {monthly_distance:.1f}km this month",
                    date_earned=datetime.now(timezone.utc),
                    value=monthly_distance,
                    unit="km"
                ))
        
        # Check duration achievements
        duration_thresholds = self.achievement_thresholds["volume_achievements"]["monthly_duration"]
        for threshold in duration_thresholds:
            if monthly_duration >= threshold:
                hours = threshold / 60
                achievements.append(Achievement(
                    type=AchievementType.VOLUME,
                    title=f"{hours:.0f}h Month!",
                    description=f"Completed {monthly_duration/60:.1f} hours of activity this month",
                    date_earned=datetime.now(timezone.utc),
                    value=monthly_duration,
                    unit="minutes"
                ))
        
        return achievements
    
    async def _generate_insights(self, activities: List[Dict[str, Any]], 
                               trends: List[TrendAnalysis],
                               achievements: List[Achievement]) -> List[ProgressInsight]:
        """Generate personalized insights based on activity data."""
        insights = []
        
        if not activities:
            return insights
        
        # Activity frequency insight
        active_days = len(set(
            self._parse_activity_date(a.get('date')).date() 
            for a in activities 
            if self._parse_activity_date(a.get('date'))
        ))
        
        if active_days >= 20:  # Assuming 30-day period
            insights.append(ProgressInsight(
                category="consistency",
                insight_type="positive",
                message="Excellent consistency! You're active most days.",
                confidence=0.9,
                recommendation="Keep up the great routine!"
            ))
        elif active_days >= 10:
            insights.append(ProgressInsight(
                category="consistency",
                insight_type="neutral",
                message="Good activity frequency with room for improvement.",
                confidence=0.8,
                recommendation="Try to add 1-2 more active days per week."
            ))
        
        # Variety insight
        activity_types = set(a.get('type', '').lower() for a in activities if a.get('type'))
        if len(activity_types) >= 3:
            insights.append(ProgressInsight(
                category="variety",
                insight_type="positive",
                message="Great variety in your workouts!",
                confidence=0.85,
                recommendation="This variety helps prevent overuse injuries and keeps workouts interesting."
            ))
        elif len(activity_types) == 1:
            activity_type = list(activity_types)[0]
            insights.append(ProgressInsight(
                category="variety",
                insight_type="suggestion",
                message=f"You're focused on {activity_type}. Consider adding variety.",
                confidence=0.8,
                recommendation="Try adding some cross-training activities like swimming or cycling."
            ))
        
        # Trend-based insights
        for trend in trends:
            if trend.direction == TrendDirection.IMPROVING and trend.confidence > 0.7:
                insights.append(ProgressInsight(
                    category="progress",
                    insight_type="positive",
                    message=f"Your {trend.metric.lower()} is improving!",
                    confidence=trend.confidence,
                    recommendation="Keep up the great work!",
                    supporting_data={"change_percentage": trend.change_percentage}
                ))
            elif trend.direction == TrendDirection.DECLINING and trend.confidence > 0.7:
                insights.append(ProgressInsight(
                    category="progress",
                    insight_type="concern",
                    message=f"Your {trend.metric.lower()} has been declining recently.",
                    confidence=trend.confidence,
                    recommendation="Consider adjusting your training plan or checking if you need more recovery.",
                    supporting_data={"change_percentage": trend.change_percentage}
                ))
        
        # Achievement-based insights
        if achievements:
            recent_achievements = [a for a in achievements if (datetime.now(timezone.utc) - a.date_earned).days <= 7]
            if recent_achievements:
                insights.append(ProgressInsight(
                    category="achievements",
                    insight_type="celebration",
                    message=f"Congratulations on your recent achievements!",
                    confidence=1.0,
                    recommendation="Celebrate your progress and set new goals!",
                    supporting_data={"achievement_count": len(recent_achievements)}
                ))
        
        return insights
    
    async def _calculate_consistency_score(self, activities: List[Dict[str, Any]], 
                                         period_days: int) -> float:
        """Calculate consistency score (0-1) based on activity distribution."""
        if not activities:
            return 0.0
        
        # Count active days
        active_dates = set()
        for activity in activities:
            date = self._parse_activity_date(activity.get('date'))
            if date:
                active_dates.add(date.date())
        
        active_days = len(active_dates)
        max_possible_days = min(period_days, 30)  # Cap at 30 days for scoring
        
        # Base consistency score
        consistency = active_days / max_possible_days
        
        # Bonus for regular distribution (not all activities on few days)
        if active_days > 0:
            activities_per_day = len(activities) / active_days
            if 1 <= activities_per_day <= 2:  # Ideal range
                consistency *= 1.1
            elif activities_per_day > 3:  # Too many on same days
                consistency *= 0.9
        
        return min(consistency, 1.0)
    
    async def _calculate_variety_score(self, activities: List[Dict[str, Any]]) -> float:
        """Calculate variety score (0-1) based on activity type diversity."""
        if not activities:
            return 0.0
        
        activity_types = [a.get('type', '').lower() for a in activities if a.get('type')]
        unique_types = set(activity_types)
        
        if not unique_types:
            return 0.0
        
        # Base score from number of unique types
        variety_score = min(len(unique_types) / 5, 1.0)  # Max score at 5+ types
        
        # Bonus for balanced distribution
        if len(unique_types) > 1:
            type_counts = Counter(activity_types)
            total_activities = len(activity_types)
            
            # Calculate distribution balance (closer to even = better)
            expected_per_type = total_activities / len(unique_types)
            balance_score = 1.0
            
            for count in type_counts.values():
                deviation = abs(count - expected_per_type) / expected_per_type
                balance_score -= deviation * 0.1
            
            variety_score *= max(balance_score, 0.5)
        
        return min(variety_score, 1.0)
    
    async def _calculate_improvement_score(self, trends: List[TrendAnalysis]) -> float:
        """Calculate improvement score (0-1) based on trend analysis."""
        if not trends:
            return 0.5  # Neutral score
        
        improvement_score = 0.5  # Start neutral
        
        for trend in trends:
            if trend.confidence < 0.5:
                continue  # Skip low-confidence trends
            
            weight = trend.confidence
            
            if trend.direction == TrendDirection.IMPROVING:
                improvement_score += 0.1 * weight
            elif trend.direction == TrendDirection.DECLINING:
                improvement_score -= 0.1 * weight
            # Stable trends don't change the score
        
        return max(0.0, min(improvement_score, 1.0))
    
    def _parse_activity_date(self, date_str: Any) -> Optional[datetime]:
        """Parse activity date string to datetime object."""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        try:
            if isinstance(date_str, str):
                # Handle ISO format
                if 'T' in date_str:
                    parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    # Ensure timezone aware
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
    
    def _parse_duration(self, duration: Any) -> float:
        """Parse duration to minutes."""
        if isinstance(duration, (int, float)):
            return float(duration)
        
        if isinstance(duration, str):
            try:
                return float(duration)
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _parse_distance_to_km(self, value: Any, unit: str) -> float:
        """Parse distance value to kilometers."""
        try:
            value = float(value)
            unit = unit.lower()
            
            if unit in ['km', 'kilometers']:
                return value
            elif unit in ['miles', 'mi']:
                return value * 1.60934
            elif unit in ['meters', 'm']:
                return value / 1000
            else:
                return value  # Assume km
        except (ValueError, TypeError):
            return 0.0


# Global service instance
progress_analytics_service = ProgressAnalyticsService()
