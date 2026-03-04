

import asyncio, os, logging
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search, AgentTool

# --- 1. SETUP ---
os.environ["GOOGLE_API_KEY"] = "ADD_API_KEY_HERE"

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# --- 2. THE SPECIALISTS ---

# Weather Specialist
def get_weather(location: str):
    return f"The weather in {location} is 72°F and sunny."

weather_agent = Agent(
    name="WeatherBot",
    model="gemini-3-flash-preview",
    instruction="You are a weather specialist. Use get_weather.",
    tools=[get_weather]
)

# Search Specialist
search_agent = Agent(
    name="SearchBot",
    model="gemini-3-flash-preview",
    instruction="You are a research specialist. Use Google Search for facts.",
    tools=[google_search] 
)

# --- 3. THE COORDINATOR (Root Agent) ---
root_agent = Agent(
    name="Coordinator",
    model="gemini-3-flash-preview",
    instruction="""Delegate current weather tasks to WeatherBot and weather history to the SearchBot.
    Always provide a combined, helpful summary to the user.""",
    tools=[AgentTool(agent=weather_agent), AgentTool(agent=search_agent)]
)

# --- 4. EXECUTION LOOP ---
async def main():
    print("\n" + "="*40 + "\nTASK 3: COORDINATOR ACTIVE\n" + "="*40)
    async with InMemoryRunner(agent=root_agent) as runner:
        # One query requiring both specialized sub-agents
        query = "What is the weather in Miami and who created the National Weather Service"
        
        events = await runner.run_debug(query)
        for e in events:
            # Highlight the handoff to sub-agents
            if hasattr(e, 'agent_name') and e.agent_name != "Coordinator":
                print(f"⚙️ [HANDOFF] Active Agent: {e.agent_name}")
            
            if hasattr(e, 'text') and e.text:
                print(f"Response: {e.text}")

if __name__ == "__main__":
    asyncio.run(main())