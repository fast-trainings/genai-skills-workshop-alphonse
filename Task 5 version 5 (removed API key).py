import asyncio
import os
import subprocess
import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp
from google.adk.agents import Agent
from google.adk.tools import google_search

# --- 1. AUTH SETUP ---
os.environ["GOOGLE_API_KEY"] = "ADD_API_KEY_HERE"

# --- CREATE PROJECT ---
# NOTE: The project ID MUST be globally unique. Change the numbers below!
NEW_PROJECT_ID = "adk-workshop-9988776655" 

print(f"Creating project {NEW_PROJECT_ID}...")
# We added shell=True and formatted it as one string for Windows
subprocess.run(f"gcloud projects create {NEW_PROJECT_ID} --name=\"ADK Workshop\"", shell=True, check=False)

# --- 2. CLOUD CONFIGURATION ---
PROJECT_ID = NEW_PROJECT_ID  
LOCATION = "us-central1"
# The bucket name also must be globally unique, so we just append your unique Project ID to it
STAGING_BUCKET = f"gs://staging-bucket-{NEW_PROJECT_ID}" 

# --- 3. AGENT SETUP ---
cloud_agent = Agent(
    name="CloudSearcher",
    model="gemini-3-flash-preview",
    instruction="You are a helpful chatbot deployed on Google Cloud. Use the google_search tool to answer questions with up-to-date facts.",
    tools=[google_search]
)

# --- 4. DEPLOYMENT & EXECUTION ---
async def main():
    try:
        print(f"\nInitializing Vertex AI in project: {PROJECT_ID}...")
        
        vertexai.init(
            project=PROJECT_ID, 
            location=LOCATION, 
            staging_bucket=STAGING_BUCKET
        )

        app = AdkApp(agent=cloud_agent, enable_tracing=True)

        print("\nDeploying agent to Agent Engine... (This usually takes 2-5 minutes)")
        remote_agent = agent_engines.create(
            app,
            requirements=["google-cloud-aiplatform[agent_engines,adk]"],
            display_name="Workshop Remote Agent"
        )
        print("✅ Deployment Successful!")

        print("\n--- Testing Remote Agent ---")
        query = "What is the latest news regarding space exploration?"
        print(f"User: {query}")
        
        for event in remote_agent.stream_query(
            user_id="test-user-001",
            message=query
        ):
            print(event)
            
    except Exception as e:
        print(f"\n❌ Deployment failed.")
        print(f"Error details: {e}")
        print("\nNote: If it says Vertex AI isn't enabled, you will need to manually link a billing account to your new project.")

if __name__ == "__main__":
    asyncio.run(main())