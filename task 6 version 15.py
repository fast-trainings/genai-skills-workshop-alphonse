import requests
from typing import Optional
from google.adk.agents import Agent
from vertexai.preview.reasoning_engines import AdkApp

# ==========================================
# 1. THE TOOLS (Weather, Alerts, Routes)
# ==========================================
def _geocode_us_city(city_name: str):
    """Helper function to cleanly get coordinates for US cities."""
    url = f"https://nominatim.openstreetmap.org/search?q={city_name},+USA&format=json&limit=1"
    headers = {'User-Agent': 'FEMA_App/1.0'}
    res = requests.get(url, headers=headers).json()
    if not res: return None, None
    return res[0]['lat'], res[0]['lon']

def get_current_weather(city_name: str) -> str:
    """1. Fetches the current live weather forecast from the NWS."""
    try:
        lat, lon = _geocode_us_city(city_name)
        if not lat: return f"Could not locate {city_name}."
        
        headers = {'User-Agent': 'FEMA_App/1.0'}
        points_res = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers=headers)
        if points_res.status_code != 200: return "NWS forecast unavailable."

        forecast_url = points_res.json()['properties']['forecast']
        forecast_res = requests.get(forecast_url, headers=headers).json()

        periods = forecast_res['properties']['periods'][:2]
        result = f"Forecast for {city_name}:\n"
        for p in periods:
            result += f"- {p['name']}: {p['detailedForecast']}\n"
        return result
    except Exception as e:
        return f"Weather error: {e}"

def get_weather_alerts(city_name: str) -> str:
    """2. Fetches active weather alerts and emergency warnings from the NWS."""
    try:
        lat, lon = _geocode_us_city(city_name)
        if not lat: return f"Could not locate {city_name}."
        
        headers = {'User-Agent': 'FEMA_App/1.0'}
        alerts_url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
        alerts_res = requests.get(alerts_url, headers=headers).json()
        
        features = alerts_res.get('features', [])
        if not features:
            return f" No active weather alerts or emergency warnings for {city_name}."
            
        result = f"Active NWS Alerts for {city_name}:\n"
        for alert in features:
            props = alert.get('properties', {})
            result += f"- {props.get('event', 'Alert')}: {props.get('headline', 'No details provided.')}\n"
        return result
    except Exception as e:
        return f"Alerts error: {e}"

def get_evacuation_routes(city_name: str) -> str:
    """3. Provides evacuation paths and safety routes for the city."""
    city = city_name.lower()
    if "orlando" in city:
        return "Evacuation Path: Head North on Florida's Turnpike or East on FL-408. Avoid I-4 Westbound due to extreme congestion."
    elif "miami" in city:
        return "Evacuation Path: Head North on I-95 or Florida's Turnpike. If storm surge is expected, evacuate Zone A immediately."
    elif "debary" in city:
        return "Evacuation Path: Head East on High St. towards designated high-ground shelters. Avoid US-17 during heavy rains."
    else:
        return f"Evacuation Path for {city_name}: Follow local emergency management signs to the nearest interstate heading inland or to higher ground."

# ==========================================
# 2. INPUT VALIDATION CALLBACK
# ==========================================
def review_input_callback(callback_context, llm_request) -> Optional[dict]:
    """Blocks non-FEMA questions so the agent stays on mission."""
    if llm_request.contents:
        last = llm_request.contents[-1]
        if last.role == "user" and last.parts and last.parts[0].text:
            text = last.parts[0].text.lower()
            # Allowed keywords
            valid_keywords = ['weather', 'evac', 'storm', 'rain', 'hurricane', 'route', 'path', 'emergency', 'alert', 'miami', 'orlando', 'debary']
            
            if not any(word in text for word in valid_keywords):
                return {
                    "content": {
                        "role": "model", 
                        "parts": [{"text": " I am a FEMA assistant. I can only answer questions related to weather, storms, alerts, and evacuation routes in the US."}]
                    }
                }
    return None

# ==========================================
# 3. THE AGENT SETUP
# ==========================================
fema_agent = Agent(
    name="ReadyNow",
    model="gemini-2.5-flash",
    instruction="""You are a FEMA emergency assistant. When a user asks for an update on a city, you MUST ALWAYS provide all three of these:
    1. Current Weather (Use get_current_weather tool)
    2. Active Alerts (Use get_weather_alerts tool)
    3. Evacuation Paths (Use get_evacuation_routes tool)
    Format the response clearly using bullet points and maintain a calm, authoritative tone.""",
    tools=[get_current_weather, get_weather_alerts, get_evacuation_routes],
    before_model_callback=review_input_callback
)

fema_app = AdkApp(agent=fema_agent)

# ==========================================
# 4. CRASH-PROOF COMMAND LINE LOOP
# ==========================================
if __name__ == "__main__":
    print("🇺🇸 FEMA Assistant Ready. (Type 'exit' to quit)")
    session = fema_app.create_session(user_id="cli-user")
    
    while True:
        query = input("\n Enter request: ")
        if query.lower() in ['exit', 'quit']:
            break
            
        print("⏳ Processing...")
        try:
            for event in fema_app.stream_query(user_id="cli-user", session_id=session.id, message=query):
                if isinstance(event, dict) and "content" in event:
                    parts = event["content"].get("parts", [])
                    for part in parts:
                        if "text" in part:
                            print(part["text"], end="", flush=True)
                        elif "functionCall" in part:
                            tool_name = part["functionCall"].get("name", "tool")
                            print(f"\n[📡 Triggering tool: {tool_name}...] \n", end="", flush=True)
            print("\n")
            
        except Exception as e:
            print(f"\n Error: {e}")