"""Deploy the ADS agent to Vertex AI Agent Engine.

Requirement: "Generative AI agent deployed to a website." Agent Engine hosts the
agent as a managed, autoscaling runtime; the Streamlit frontend (frontend/app.py)
calls it. Run this after the corpus and Model Armor template exist and are in .env.

Idempotent: if ADS_AGENT_ENGINE_RESOURCE is already set in .env, the existing
deployment is updated in place instead of creating a new one.

Run:  uv run python scripts/04_deploy_agent_engine.py
Then paste the printed ADS_AGENT_ENGINE_RESOURCE value into .env.
"""

import vertexai
from vertexai import agent_engines

from ads_agent import config
from ads_agent.agent import root_agent

vertexai.init(
    project=config.PROJECT,
    location=config.LOCATION,
    staging_bucket=f"gs://{config.STAGING_BUCKET}",
)

# Our app config travels with the deployment. NOTE: GOOGLE_CLOUD_PROJECT,
# GOOGLE_CLOUD_LOCATION, and GOOGLE_GENAI_USE_VERTEXAI are reserved by the Agent
# Engine runtime (it sets them automatically) — do not pass them here.
env_vars = {
    "ADS_MODEL": config.MODEL,
    "ADS_RAG_CORPUS": config.RAG_CORPUS,
    "ADS_MODEL_ARMOR_INPUT_TEMPLATE": config.MODEL_ARMOR_INPUT_TEMPLATE,
    "ADS_MODEL_ARMOR_OUTPUT_TEMPLATE": config.MODEL_ARMOR_OUTPUT_TEMPLATE,
    "ADS_LOG_NAME": config.LOG_NAME,
}

common = dict(
    agent_engine=root_agent,
    display_name="Alaska Department of Snow Agent",
    description="Secure, RAG-grounded resident assistant for the Alaska Dept. of Snow.",
    requirements=[
        "google-adk>=1.0.0",
        "google-cloud-aiplatform[adk,agent_engines]>=1.95.0",
        "google-cloud-logging>=3.10.0",
        "google-cloud-modelarmor>=0.2.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    extra_packages=["ads_agent"],
    env_vars=env_vars,
)

if config.AGENT_ENGINE_RESOURCE:
    print(f"Updating existing deployment {config.AGENT_ENGINE_RESOURCE} ...")
    remote_app = agent_engines.update(
        resource_name=config.AGENT_ENGINE_RESOURCE, **common
    )
else:
    print("Deploying to Agent Engine (this takes several minutes)...")
    remote_app = agent_engines.create(**common)

print(f"\nDeployed: {remote_app.resource_name}")
print("\n--- Paste into .env ---")
print(f"ADS_AGENT_ENGINE_RESOURCE={remote_app.resource_name}")
