import asyncio
import os
import requests
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

# --- AUTH SETUP ---
os.environ["GOOGLE_API_KEY"] = "ADD_THE_API_KEY_HERE"

# --- 1. DEFINE REAL TOOLS ---
def get_lat_lon(city_state: str) -> tuple[float, float]:
    """
    Converts a city and state to latitude and longitude using OpenStreetMap.
    Args:
        city_state (str): The name of the city and state (e.g., "Austin, TX").
    Returns:
        tuple[float, float]: The latitude and longitude.
    """
    try:
        # Nominatim requires a User-Agent header
        headers = {"User-Agent": "GoogleADK-WeatherAgent/1.0"}
        url = f"https://nominatim.openstreetmap.org/search?q={city_state}&format=json&limit=1"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return 0.0, 0.0
    except Exception as e:
        print(f"Geocoding error: {e}")
        return 0.0, 0.0

def get_nws_weather(lat: float, lon: float) -> str:
    """
    Fetches the live weather forecast from the National Weather Service (NWS) API.
    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    Returns:
        str: A detailed weather summary.
    """
    if lat == 0.0 and lon == 0.0:
        return "Error: Invalid coordinates provided."

    headers = {"User-Agent": "GoogleADK-WeatherAgent/1.0"}
    
    try:
        # Step 1: Get the Grid endpoints for the provided Lat/Lon
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_response = requests.get(points_url, headers=headers)
        points_response.raise_for_status()
        
        # Extract the specific forecast URL for this grid
        forecast_url = points_response.json()["properties"]["forecast"]

        # Step 2: Call the forecast URL to get the actual weather data
        forecast_response = requests.get(forecast_url, headers=headers)
        forecast_response.raise_for_status()
        
        # Grab the most current period (usually 'Today' or 'Tonight')
        periods = forecast_response.json()["properties"]["periods"]
        current = periods[0]
        
        return f"{current['name']}: {current['detailedForecast']} (Temperature: {current['temperature']} {current['temperatureUnit']})"
        
    except requests.exceptions.HTTPError as e:
        return f"NWS API Error: {e.response.status_code}. (Note: NWS only supports US locations)."
    except Exception as e:
        return f"Failed to retrieve weather: {str(e)}"

# --- 2. DEFINE AGENT ---
live_weather_agent = Agent(
    name="LivePat",
    model="gemini-3-flash-preview",
    description="A weather assistant hooked up to live NWS data.",
    instruction="""You are a weather assistant. When a user asks for weather:
    1. Use the get_lat_lon tool to find the coordinates of their requested city.
    2. Pass those coordinates into the get_nws_weather tool.
    3. Summarize the resulting forecast for the user in a friendly way.""",
    tools=[get_lat_lon, get_nws_weather]
)

# --- 3. EXECUTION LOOP ---
async def main():
    async with InMemoryRunner(agent=live_weather_agent) as runner:
        # Feel free to change this city to test different locations!
        query = "What is the weather like in Orlando, FL right now?"
        print(f"User: {query}\n")
        
        events = await runner.run_debug(query)
        
        for event in events:
            # Show the agent's thought process as it calls the APIs
            if hasattr(event, 'function_calls') and event.function_calls:
                for call in event.function_calls:
                    print(f"⚙️ [Tool Execution] Running {call.name} with {call.args}")
            
            # Show the final text response
            elif hasattr(event, 'text') and event.text:
                print(f"\nAgent: {event.text}")

if __name__ == "__main__":
    asyncio.run(main())