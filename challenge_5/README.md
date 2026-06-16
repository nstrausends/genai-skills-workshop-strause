# Challenge 5 — Alaska Department of Snow Online Agent

A secure, accurate, production-quality generative-AI agent for the Alaska
Department of Snow (ADS), built on **Google ADK** and deployed to **Vertex AI
Agent Engine**. It answers resident questions about plowing, school/road
closures, and winter preparedness — grounded in official ADS documents (RAG)
and live National Weather Service data.

See [`architecture.md`](architecture.md) for the diagram and request/response flow.

## Requirement checklist

| Challenge 5 requirement | Implementation |
|---|---|
| ✅ Backend data store for RAG | Vertex AI RAG Engine corpus (Serverless mode), ingested from `gs://labs.roitraining.com/alaska-dept-of-snow` — `scripts/01_stage_data.sh` + `scripts/02_create_rag_corpus.py`; queried by the `retrieve_ads_docs` function tool (`rag.retrieval_query`) in `ads_agent/tools.py` |
| ✅ Access to backend API functionality | `ads_agent/tools.py` — National Weather Service (`api.weather.gov`) forecasts + active alerts |
| ✅ Unit tests for agent functionality | `tests/` — tools, Model Armor screening, and callbacks (deterministic, network/clients mocked) |
| ✅ Evaluation via the Google Evaluation service API | `eval/run_eval.py` + `eval/eval_dataset.json` — Vertex AI GenAI Evaluation Service, in code |
| ✅ Prompt filtering & response validation | Model Armor in `ads_agent/safety.py`, wired through `ads_agent/callbacks.py`; two templates (input: jailbreak/PI; output: sensitive-data/SDP + malicious URLs) created by `scripts/03_create_model_armor.py` |
| ✅ Log all prompts and responses | `ads_agent/observability.py` → Cloud Logging, called from the callbacks |
| ✅ Agent deployed to a website | Agent Engine (`scripts/03_deploy_agent_engine.py`) + Streamlit chat UI (`frontend/app.py`) |

## Prerequisites

- A GCP project with billing enabled.
- [`uv`](https://docs.astral.sh/uv/) and the `gcloud` CLI installed.
- Authenticate:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  ```

## Run it

```bash
cd challenge_5
cp .env.example .env          # then set GOOGLE_CLOUD_PROJECT (and bucket name)
uv sync --extra dev --extra frontend

# 1. Enable APIs + create the deployment staging bucket
bash scripts/00_enable_apis.sh

# 2. Stage the ADS documents into your own bucket (RAG can't read the workshop bucket)
bash scripts/01_stage_data.sh

# 3. Build the RAG corpus from the staged data          -> paste ADS_RAG_CORPUS into .env
uv run python scripts/02_create_rag_corpus.py

# 4. Create the Model Armor guardrail template          -> paste ADS_MODEL_ARMOR_TEMPLATE into .env
uv run python scripts/03_create_model_armor.py

# 5. Deploy the agent to Agent Engine                   -> paste ADS_AGENT_ENGINE_RESOURCE into .env
uv run python scripts/04_deploy_agent_engine.py

# 6. Grant the Agent Engine runtime SA access to RAG, Model Armor, and Logging
bash scripts/05_grant_agent_permissions.sh

# 7. Evaluate the deployed agent with the Google Eval Service
uv run python eval/run_eval.py

# 8. Launch the demo website
uv run streamlit run frontend/app.py
```

## Run unit tests

Run the unit tests any time with `uv run pytest`.

## Run locally

Try the agent locally without deploying with `uv run python local_run.py`.
