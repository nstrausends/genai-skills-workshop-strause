"""Central configuration, read from environment (.env).

Every value is parameterized so the same code runs locally and on Agent Engine.
"""

import os

from dotenv import load_dotenv

load_dotenv()

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

# Tell the google-genai / ADK stack to use Vertex AI (not AI Studio).
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Use a concrete Vertex model version; the "-latest" aliases don't always
# resolve on Vertex AI in every project/region.
MODEL = os.environ.get("ADS_MODEL", "gemini-2.5-flash")

# Full resource name of the RAG corpus, produced by scripts/01_create_rag_corpus.py
# e.g. projects/<num>/locations/us-central1/ragCorpora/<id>
RAG_CORPUS = os.environ.get("ADS_RAG_CORPUS", "")

# Full resource names of the Model Armor templates, produced by
# scripts/03_create_model_armor.py. INPUT screens prompts (jailbreak/PI);
# OUTPUT validates responses (sensitive-data leakage, malicious URLs).
MODEL_ARMOR_INPUT_TEMPLATE = os.environ.get("ADS_MODEL_ARMOR_INPUT_TEMPLATE", "")
MODEL_ARMOR_OUTPUT_TEMPLATE = os.environ.get("ADS_MODEL_ARMOR_OUTPUT_TEMPLATE", "")

# Cloud Logging log name that captures every prompt and response.
LOG_NAME = os.environ.get("ADS_LOG_NAME", "ads-agent-interactions")

# Deployed Agent Engine resource name (used by the Streamlit frontend).
AGENT_ENGINE_RESOURCE = os.environ.get("ADS_AGENT_ENGINE_RESOURCE", "")

# GCS staging bucket for Agent Engine deployment artifacts (no gs:// prefix).
STAGING_BUCKET = os.environ.get("ADS_STAGING_BUCKET", f"{PROJECT}-ads-staging")

# GCS bucket holding the staged ADS documents for RAG ingestion (no gs:// prefix).
DATA_BUCKET = os.environ.get("ADS_DATA_BUCKET", f"{PROJECT}-ads-data")
