# Architecture — Alaska Department of Snow Online Agent

```mermaid
flowchart TB
    user([Resident]) -->|question| web["Streamlit website<br/>(frontend/app.py)"]
    web -->|stream_query| ae

    subgraph AE["Vertex AI Agent Engine (managed runtime)"]
        ae["ADK agent: ads_agent"]
        bm{{"before_model callback"}}
        gem["Gemini (gemini-2.5-flash)"]
        am{{"after_model callback"}}

        ae --> bm
        bm -->|"log prompt + Model Armor screen"| gem
        gem -->|tool calls| tools
        gem --> am
        am -->|"Model Armor validate + log response"| ae

        subgraph tools["Tools"]
            rag["retrieve_ads_docs<br/>(rag.retrieval_query)"]
            wx["get_weather_forecast / get_weather_alerts"]
        end
    end

    rag --> corpus[("RAG Engine corpus<br/>backend data store")]
    wx --> nws["api.weather.gov<br/>(backend API)"]
    bm -. screen .-> armorin["Model Armor INPUT<br/>jailbreak / PI"]
    am -. validate .-> armorout["Model Armor OUTPUT<br/>sensitive data / URLs"]
    bm --> logs[["Cloud Logging<br/>ads-agent-interactions"]]
    am --> logs

    gcs[("workshop bucket<br/>gs://labs.roitraining.com")] -.->|"01_stage_data.sh"| databkt[("project bucket<br/>gs://PROJECT-ads-data")]
    databkt -.->|"02_create_rag_corpus.py (ingest)"| corpus
```

## Secure request/response flow

1. Resident asks a question on the website.
2. **Log** the prompt to Cloud Logging.
3. **Model Armor (input template)** screens the prompt for prompt-injection /
   jailbreak / harmful content. On a match, the model call is skipped and a safe
   message is returned.
4. Gemini answers, **grounded** in the RAG corpus (`retrieve_ads_docs`) and live
   National Weather Service data (`get_weather_*`).
5. **Model Armor (output template)** validates the response for sensitive-data
   leakage and malicious URLs; violating output is replaced.
6. **Log** the response and return it to the resident.
