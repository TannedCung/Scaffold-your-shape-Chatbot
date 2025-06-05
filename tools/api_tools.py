import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from models.api_models import CreateActivityRequest, CreateClubRequest, CreateChallengeRequest
from services.mock_api_service import mock_api_service

def parse_activity_from_message(message: str) -> Dict[str, Any]:
    """Parse activity information from natural language message."""
    message = message.lower()
    
    # Activity type mapping
    activity_types = {
        'run': 'running',
        'ran': 'running',
        'running': 'running',
        'jog': 'running',
        'jogged': 'running',
        'jogging': 'running',
        'cycle': 'cycling',
        'cycled': 'cycling',
        'cycling': 'cycling',
        'bike': 'cycling',
        'biked': 'cycling',
        'biking': 'cycling',
        'swim': 'swimming',
        'swam': 'swimming',
        'swimming': 'swimming',
        'walk': 'walking',
        'walked': 'walking',
        'walking': 'walking',
        'yoga': 'yoga',
        'weights': 'strength_training',
        'lifting': 'strength_training',
        'lifted': 'strength_training',
        'strength': 'strength_training',
        'gym': 'strength_training'
    }
    
    # Detect activity type
    detected_type = "other"
    for keyword, activity_type in activity_types.items():
        if keyword in message:
            detected_type = activity_type
            break
    
    # Extract numbers for distance and duration
    numbers = re.findall(r'\d+(?:\.\d+)?', message)
    
    # Extract distance (km, miles, meters)
    distance = None
    distance_match = re.search(r'(\d+(?:\.\d+)?)\s*(km|kilometers?|miles?|m\b)', message)
    if distance_match:
        value = float(distance_match.group(1))
        unit = distance_match.group(2)
        if 'mile' in unit:
            distance = value * 1.609344  # Convert miles to km
        elif unit == 'm' and value > 100:  # Assume meters if > 100
            distance = value / 1000  # Convert meters to km
        else:
            distance = value
    
    # Extract duration (minutes, hours, seconds)
    duration = None
    duration_match = re.search(r'(\d+(?:\.\d+)?)\s*(min|minutes?|hr|hours?|sec|seconds?)', message)
    if duration_match:
        value = float(duration_match.group(1))
        unit = duration_match.group(2)
        if 'hr' in unit or 'hour' in unit:
            duration = int(value * 3600)  # Convert to seconds
        elif 'min' in unit:
            duration = int(value * 60)  # Convert to seconds
        else:
            duration = int(value)
    
    # Extract location
    location = None
    location_match = re.search(r'(?:at|in|on)\s+([a-zA-Z\s]+)', message)
    if location_match:
        location = location_match.group(1).strip()
    
    return {
        "type": detected_type,
        "distance": distance,
        "duration": duration,
        "location": location,
        "notes": message
    }

async def log_activity_tool(user_id: str, message: str) -> str:
    """Tool to log an activity using the API."""
    try:
        activity_info = parse_activity_from_message(message)
        
        # Create activity request
        activity_request = CreateActivityRequest(
            type=activity_info["type"],
            distance=activity_info["distance"],
            duration=activity_info["duration"],
            date=datetime.now().isoformat(),
            location=activity_info["location"],
            notes=activity_info["notes"]
        )
        
        # Call API to create activity
        result = await mock_api_service.create_activity(activity_request)
        
        if "error" in result:
            return f"Failed to log activity: {result['error']}"
        
        # Format success response
        activity_type = activity_info["type"].replace("_", " ").title()
        details = []
        if activity_info["distance"]:
            details.append(f"{activity_info['distance']} km")
        if activity_info["duration"]:
            mins = activity_info["duration"] // 60
            details.append(f"{mins} minutes")
        
        detail_str = " - " + ", ".join(details) if details else ""
        return f"Great job! I've logged your {activity_type} activity{detail_str}."
        
    except Exception as e:
        return f"Sorry, I couldn't log your activity: {str(e)}"

async def get_user_activities_tool(user_id: str) -> Dict[str, Any]:
    """Tool to get user's activities."""
    try:
        result = await mock_api_service.get_activities()
        
        if "error" in result:
            return {"error": result["error"]}
        
        activities = result.get("data", [])
        return {
            "activities": activities,
            "count": len(activities),
            "summary": f"Found {len(activities)} activities"
        }
        
    except Exception as e:
        return {"error": str(e)}

def parse_club_from_message(message: str) -> Dict[str, Any]:
    """Parse club information from natural language message."""
    message_lower = message.lower()
    
    # Extract club name (after "club" keyword)
    club_match = re.search(r'club\s+([a-zA-Z0-9\s]+)', message_lower)
    club_name = club_match.group(1).strip() if club_match else None
    
    # Determine if it's create, join, or search
    if any(word in message_lower for word in ["create", "start", "make", "new"]):
        action = "create"
    elif any(word in message_lower for word in ["join", "enter"]):
        action = "join"
    elif any(word in message_lower for word in ["leave", "exit", "quit"]):
        action = "leave"
    else:
        action = "search"
    
    # Extract description for club creation
    description = None
    if action == "create":
        desc_match = re.search(r'(?:for|about)\s+([^.!?]+)', message)
        description = desc_match.group(1).strip() if desc_match else f"A fitness club for {club_name}"
    
    return {
        "action": action,
        "name": club_name,
        "description": description
    }

async def manage_club_tool(user_id: str, message: str) -> str:
    """Tool to manage clubs (create, join, search)."""
    try:
        club_info = parse_club_from_message(message)
        
        if club_info["action"] == "create":
            if not club_info["name"] or not club_info["description"]:
                return "To create a club, please specify a name and description. Example: 'Create club runners for people who love running'"
            
            club_request = CreateClubRequest(
                name=club_info["name"],
                description=club_info["description"],
                is_private=False
            )
            
            result = await mock_api_service.create_club(club_request)
            
            if "error" in result:
                return f"Failed to create club: {result['error']}"
            
            return f"Great! I've created the '{club_info['name']}' club for you."
        
        elif club_info["action"] == "search" or club_info["action"] == "join":
            # Get all clubs to search
            result = await mock_api_service.get_clubs()
            
            if "error" in result:
                return f"Failed to get clubs: {result['error']}"
            
            clubs = result.get("data", [])
            
            if not clubs:
                return "No clubs found. You can create one with 'Create club [name] for [description]'"
            
            # Search for clubs by name if specified
            if club_info["name"]:
                matching_clubs = [club for club in clubs if club_info["name"].lower() in club["name"].lower()]
                if matching_clubs:
                    club_list = "\n".join([f"• {club['name']} - {club['description']} ({club['member_count']} members)" for club in matching_clubs[:5]])
                    return f"Found matching clubs:\n{club_list}"
                else:
                    return f"No clubs found matching '{club_info['name']}'. Available clubs: {', '.join([club['name'] for club in clubs[:5]])}"
            else:
                # List all clubs
                club_list = "\n".join([f"• {club['name']} - {club['description']} ({club['member_count']} members)" for club in clubs[:5]])
                return f"Available clubs:\n{club_list}"
        
        else:
            return "I can help you create clubs, search for clubs, or join clubs. What would you like to do?"
            
    except Exception as e:
        return f"Sorry, I couldn't process your club request: {str(e)}"

def parse_challenge_from_message(message: str) -> Dict[str, Any]:
    """Parse challenge information from natural language message."""
    message_lower = message.lower()
    
    # Determine action
    if any(word in message_lower for word in ["create", "start", "make", "new"]):
        action = "create"
    elif any(word in message_lower for word in ["join", "participate", "enter"]):
        action = "join"
    else:
        action = "search"
    
    # Extract challenge details for creation
    target_value = None
    unit = None
    
    # Look for target patterns like "100 km", "30 days", "50 activities"
    target_match = re.search(r'(\d+(?:\.\d+)?)\s*(km|miles?|activities?|days?|hours?|minutes?)', message_lower)
    if target_match:
        target_value = float(target_match.group(1))
        unit = target_match.group(2)
    
    # Extract challenge name/title
    title = None
    title_patterns = [
        r'challenge\s+([a-zA-Z0-9\s]+?)(?:\s+for|\s+with|\s*$)',
        r'(?:create|start)\s+([a-zA-Z0-9\s]+?)\s+challenge'
    ]
    
    for pattern in title_patterns:
        title_match = re.search(pattern, message_lower)
        if title_match:
            title = title_match.group(1).strip()
            break
    
    return {
        "action": action,
        "title": title,
        "target_value": target_value,
        "unit": unit
    }

async def manage_challenge_tool(user_id: str, message: str) -> str:
    """Tool to manage challenges (create, join, search)."""
    try:
        challenge_info = parse_challenge_from_message(message)
        
        if challenge_info["action"] == "create":
            if not all([challenge_info["title"], challenge_info["target_value"], challenge_info["unit"]]):
                return "To create a challenge, please specify a title, target value, and unit. Example: 'Create running challenge for 100 km this month'"
            
            # Set challenge dates (default to 1 month)
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)
            
            challenge_request = CreateChallengeRequest(
                title=challenge_info["title"],
                description=f"Complete {challenge_info['target_value']} {challenge_info['unit']} in this challenge!",
                target_value=challenge_info["target_value"],
                unit=challenge_info["unit"],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                is_public=True
            )
            
            result = await mock_api_service.create_challenge(challenge_request)
            
            if "error" in result:
                return f"Failed to create challenge: {result['error']}"
            
            return f"Awesome! I've created the '{challenge_info['title']}' challenge with a target of {challenge_info['target_value']} {challenge_info['unit']}."
        
        else:
            # Get all challenges
            result = await mock_api_service.get_challenges()
            
            if "error" in result:
                return f"Failed to get challenges: {result['error']}"
            
            challenges = result.get("data", [])
            
            if not challenges:
                return "No challenges found. You can create one with 'Create [name] challenge for [target] [unit]'"
            
            # List challenges
            challenge_list = "\n".join([
                f"• {challenge['title']} - {challenge['target_value']} {challenge['unit']} ({challenge['participant_count']} participants)"
                for challenge in challenges[:5]
            ])
            return f"Available challenges:\n{challenge_list}"
            
    except Exception as e:
        return f"Sorry, I couldn't process your challenge request: {str(e)}"

async def get_user_stats_tool(user_id: str) -> str:
    """Tool to get user statistics and progress."""
    try:
        # Get user activities
        activities_result = await mock_api_service.get_activities()
        
        if "error" in activities_result:
            return f"Failed to get your stats: {activities_result['error']}"
        
        activities = activities_result.get("data", [])
        
        if not activities:
            return "You haven't logged any activities yet. Start by telling me about your workout: 'I ran 5 km today'"
        
        # Calculate basic stats
        total_activities = len(activities)
        total_distance = sum(activity.get("distance", 0) for activity in activities if activity.get("distance"))
        total_duration = sum(activity.get("duration", 0) for activity in activities if activity.get("duration"))
        
        # Get activity types
        activity_types = {}
        for activity in activities:
            activity_type = activity.get("type", "other")
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        # Format stats
        stats = [
            f"📊 Your Fitness Stats:",
            f"• Total Activities: {total_activities}",
            f"• Total Distance: {total_distance:.1f} km",
            f"• Total Time: {total_duration // 3600:.0f}h {(total_duration % 3600) // 60:.0f}m"
        ]
        
        if activity_types:
            most_common = max(activity_types.items(), key=lambda x: x[1])
            stats.append(f"• Favorite Activity: {most_common[0].replace('_', ' ').title()} ({most_common[1]} times)")
        
        return "\n".join(stats)
        
    except Exception as e:
        return f"Sorry, I couldn't get your stats: {str(e)}" 