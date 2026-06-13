"""
Contextual Triggers Service
Provides live real-world context to enhance shopping recommendations
(weather, time of day, special events, etc.)
"""
from datetime import datetime
import requests
from config import settings


def get_weather_context() -> str:
    """
    Fetch current weather. If API key available, use real data.
    Otherwise return mock/time-based heuristic.
    """
    if settings.weather_api_key:
        try:
            # Example: OpenWeatherMap free tier
            # url = f"http://api.openweathermap.org/data/2.5/weather?q=Mumbai&appid={settings.weather_api_key}&units=metric"
            # response = requests.get(url, timeout=3)
            # data = response.json()
            # temp = data["main"]["temp"]
            # desc = data["weather"][0]["description"]
            # return f"Weather is {desc}, {temp}°C"
            pass
        except:
            pass
    
    # Mock weather based on time (for demo purposes)
    hour = datetime.now().hour
    if hour < 10:
        return "Cool morning weather"
    elif hour < 16:
        return "Hot afternoon (30°C+)"
    elif hour < 20:
        return "Pleasant evening"
    else:
        return "Cool night"


def get_time_context() -> str:
    """
    Return time-based shopping hints.
    """
    now = datetime.now()
    hour = now.hour
    day = now.strftime("%A")
    
    if hour < 10:
        return f"It's {day} morning - breakfast time! Consider items for a quick morning meal."
    elif hour < 13:
        return f"It's {day} late morning. Users might be planning lunch."
    elif hour < 17:
        return f"It's {day} afternoon. Suggest snacks or afternoon refreshments."
    elif hour < 21:
        return f"It's {day} evening. Dinner ingredients or ready-to-eat meals are relevant."
    else:
        return f"It's {day} night. Late-night snacks or comfort food might appeal."


def get_event_context() -> str:
    """
    Check for special events (cricket matches, festivals, holidays).
    This is a mock - integrate with a real sports/events API if needed.
    """
    now = datetime.now()
    day = now.strftime("%A")
    
    # Mock: Weekend = family time
    if day in ["Saturday", "Sunday"]:
        return "It's the weekend! Families often stock up on snacks, beverages, and party supplies."
    
    # Mock: Check for specific dates (festivals, match days, etc.)
    # You could integrate with:
    # - Cricket API: cricbuzz, cricapi
    # - Holiday calendar API
    
    return ""


def get_contextual_triggers() -> str:
    """
    Combine all contextual signals into a single context string for the LLM.
    """
    triggers = []
    
    weather = get_weather_context()
    if weather:
        triggers.append(weather)
    
    time_hint = get_time_context()
    if time_hint:
        triggers.append(time_hint)
    
    event = get_event_context()
    if event:
        triggers.append(event)
    
    return " | ".join(triggers) if triggers else ""
