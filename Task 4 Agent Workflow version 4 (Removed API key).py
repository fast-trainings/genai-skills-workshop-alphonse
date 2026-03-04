import asyncio
import os
import logging
from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search

# --- 1. SETUP ---
os.environ["GOOGLE_API_KEY"] = "API_KEY_GOES_HERE" 

logging.basicConfig(level=logging.INFO, format='%(message)s')


# --- 2. SPECIALIZED AGENTS ---

searcher = Agent(
    name="Searcher",
    model="gemini-3-flash-preview",
    instruction="Step 1: Use Google Search to find top 5 differences technical differences between C and Python.",
    tools=[google_search]
)

critic = Agent(
    name="Critic",
    model="gemini-3-flash-preview",
    instruction="Step 2: Review data for jargon and suggest beginner-friendly simplifications.You are an expert in Programming lanagues. Limit your responce to two lines"
)

refiner = Agent(
    name="Refiner",
    model="gemini-3-flash-preview",
    instruction="Step 3: Write a polished, easy-to-read comparison based on the data and critique. You are an expert in Programming langues.Limit your responce to two lines"
)

# --- 3. THE WORKFLOW ---
qa_pipeline = SequentialAgent(
    name="ProgrammingEducationTeam",
    description="A pipeline that researches, critiques, and explains programming concepts.",
    sub_agents=[searcher, critic, refiner]
)

# THE FIX: Use 'sub_agents' instead of 'agents' to satisfy Pydantic
coordinator = Agent(
    name="Coordinator",
    model="gemini-3-flash-preview",
    instruction="Pass the user's programming question directly to the ProgrammingEducationTeam.",
    sub_agents=[qa_pipeline] 
)

# --- 4. EXECUTION ---
async def main():
    async with InMemoryRunner(agent=coordinator) as runner:
        print("\n" + "="*50 + "\nTASK 4: PIPELINE ACTIVE\n" + "="*50)
        
        query = "What is the difference between C and Python programming languages?"
        
        # Using run_debug to see the transition between the sub-agents
        events = await runner.run_debug(query)
        for e in events:
            if hasattr(e, 'agent_name'):
                print(f"⚙️ [PIPELINE] Current Agent: {e.agent_name}")
            
            if hasattr(e, 'text') and e.text:
                print(f"\n[{getattr(e, 'agent_name', 'System')}] Output:\n{e.text}")

if __name__ == "__main__":
    asyncio.run(main())