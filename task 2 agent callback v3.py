
import asyncio, os, logging
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

# --- 1. SETUP ---
os.environ["GOOGLE_API_KEY"] = "ADD_API_KEY_HERE"

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# --- 2. THE CALLBACKS   ---

def log_user_prompt(callback_context, llm_request):
    """
   Logs user and validates safety/US-location.
    """
    if llm_request.contents:
        user_text = llm_request.contents[-1].parts[0].text or ""
        
        # 3a. US-Only Validation
        if any(loc in user_text.lower() for loc in ["london", "paris", "tokyo"]):
            print("VALIDATION ERROR: Only US locations supported.")
            return None 

        # 3b. Malicious Check
        if any(risk in user_text.lower() for risk in ["admin", "bypass"]):
            print("SECURITY ERROR: Malicious input detected.")
            return None

        # 2. Audit Log (User)
        logger.info("[%s] USER » %s", callback_context.agent_name, user_text.strip())
    return None

def log_model_response(callback_context, llm_response):
    """  Logs the model output."""
    if llm_response.content and llm_response.content.parts:
        part = llm_response.content.parts[0]
        if hasattr(part, 'text') and part.text:
            logger.info("[%s] MODEL » %s", callback_context.agent_name, part.text.strip())
    return None

# --- 3. AGENT CONFIGURATION ---
def get_weather(location: str):
    return f"The weather in {location} is 72°F."

weather_agent = Agent(
    name="Pat",
    model="gemini-3-flash-preview",
    instruction="You are a weather specialist. Use get_weather.",
    tools=[get_weather],
    # Hooking the functions into the agent life-cycle
    before_model_callback=log_user_prompt,
    after_model_callback=log_model_response
)

# --- 4. EXECUTION ---
async def main():
    print("\n--- CHALLENGE 2  ---")
    async with InMemoryRunner(agent=weather_agent) as runner:
        while True:
            query = input("\nYou > ").strip()
            if query.lower() in ["exit", "quit"]: break
            
            # run_debug ensures we see the logger.info logs in real-time
            events = await runner.run_debug(query)
            for e in events:
                if hasattr(e, 'text') and e.text:
                    print(f"Pat » {e.text}")

if __name__ == "__main__":
    asyncio.run(main())