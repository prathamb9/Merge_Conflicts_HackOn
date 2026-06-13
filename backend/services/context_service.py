"""
Contextual Triggers Service
Provides live real-world context to enhance shopping recommendations
(weather, time of day, special events, IPL season detection, etc.)
"""
from datetime import datetime
import requests
from config import settings


def get_weather_context() -> str:
    """
    Fetch current weather from WeatherAPI.com.
    Falls back to time-based heuristic if API is unavailable.
    """
    if settings.weather_api_key:
        try:
            url = (
                f"https://api.weatherapi.com/v1/current.json"
                f"?key={settings.weather_api_key}"
                f"&q={settings.weather_api_city}"
                f"&aqi=no"
            )
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})
                temp_c = current.get("temp_c", 0)
                condition = current.get("condition", {}).get("text", "").lower()
                humidity = current.get("humidity", 0)
                feelslike = current.get("feelslike_c", temp_c)
                
                # Build actionable context for the LLM
                context_parts = [f"Weather in {settings.weather_api_city}: {condition}, {temp_c}°C (feels like {feelslike}°C), humidity {humidity}%"]
                
                # Rain context
                if any(w in condition for w in ("rain", "drizzle", "shower", "thunder", "storm")):
                    context_parts.append(
                        "🌧️ It's RAINING — strongly prioritize hot snacks (pakoda, samosa), "
                        "chai/tea ingredients, soups, maggi noodles, and comfort food. "
                        "Users crave warm, cozy food during rain."
                    )
                # Hot weather
                elif temp_c >= 35:
                    context_parts.append(
                        "🥵 It's very HOT — prioritize cold drinks, ice cream, juices, "
                        "water, lassi, buttermilk, watermelon, and cooling items."
                    )
                elif temp_c >= 28:
                    context_parts.append(
                        "☀️ It's warm — suggest refreshing beverages, fruits, salads, "
                        "and light snacks."
                    )
                # Cold weather
                elif temp_c <= 15:
                    context_parts.append(
                        "🥶 It's COLD — suggest hot beverages (coffee, tea, hot chocolate), "
                        "soups, warm snacks, and comfort food."
                    )
                
                return " | ".join(context_parts)
        except Exception as e:
            print(f"WeatherAPI.com request failed: {e}")
    
    # Fallback: mock weather based on time
    hour = datetime.now().hour
    if hour < 10:
        return "Cool morning weather — suggest breakfast items and hot beverages"
    elif hour < 16:
        return "Hot afternoon (30°C+) — suggest cold drinks, ice cream, and light snacks"
    elif hour < 20:
        return "Pleasant evening — suggest evening snacks and tea-time items"
    else:
        return "Cool night — suggest comfort food and warm beverages"


def get_time_context() -> str:
    """
    Return time-based shopping hints with specific product-category mapping.
    """
    now = datetime.now()
    hour = now.hour
    day = now.strftime("%A")
    
    if hour < 7:
        return f"It's very early {day} morning. Late-night/early-morning orders: suggest instant noodles, milk, bread, or midnight snacks."
    elif hour < 10:
        return f"It's {day} morning — BREAKFAST TIME! Prioritize: eggs, milk, bread, butter, coffee, tea, cereal, oats, fruits, juice."
    elif hour < 13:
        return f"It's {day} late morning. Users may be planning LUNCH. Suggest: rice, dal, vegetables, cooking oil, spices, ready meals."
    elif hour < 16:
        return f"It's {day} afternoon. Suggest SNACKS and refreshments: biscuits, chips, cold drinks, fruits, juice, ice cream."
    elif hour < 19:
        return f"It's {day} EVENING — TEA TIME! Strongly suggest: tea, coffee, cookies, biscuits, pakoda ingredients, samosa, namkeen."
    elif hour < 21:
        return f"It's {day} evening — DINNER TIME. Suggest dinner ingredients: vegetables, paneer, chicken, rice, roti/atta, cooking essentials."
    else:
        return f"It's {day} NIGHT. Late-night cravings: ice cream, chips, instant noodles, chocolate, cold drinks, comfort food."


def get_event_context() -> str:
    """
    Detect special events based on date/time:
    - IPL season (March-May, evenings)
    - Weekends
    - Festival season hints
    """
    now = datetime.now()
    day = now.strftime("%A")
    month = now.month
    hour = now.hour
    
    events = []
    
    # IPL Cricket Season: March to May, matches typically at 7:30 PM
    if 3 <= month <= 5 and hour >= 18:
        events.append(
            "🏏 IPL CRICKET SEASON — evening match time! "
            "Strongly suggest: party snacks, chips, cold drinks, soft drinks, "
            "ice cream, pizza ingredients, nachos, popcorn, beer snacks. "
            "Users often order party food during IPL matches."
        )
    elif 3 <= month <= 5 and hour >= 14:
        events.append(
            "🏏 IPL season — afternoon match possibility. "
            "Suggest snacks and beverages for match watching."
        )
    
    # Weekend
    if day in ["Saturday", "Sunday"]:
        events.append(
            "🎉 It's the WEEKEND! Families stock up on: "
            "snacks, beverages, party supplies, breakfast ingredients, "
            "baking items, and groceries for the week ahead."
        )
    
    # Friday evening = party time
    if day == "Friday" and hour >= 17:
        events.append(
            "🎊 FRIDAY EVENING! Weekend is starting — suggest party snacks, "
            "cold drinks, ice cream, and celebration food."
        )
    
    # Festival season hints (broad ranges)
    if month in [10, 11]:  # Diwali/Navratri season
        events.append(
            "🪔 Festival season! Suggest: sweets, dry fruits, chocolates, "
            "gift packs, decorations, and festive snacks."
        )
    
    return " | ".join(events) if events else ""


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
