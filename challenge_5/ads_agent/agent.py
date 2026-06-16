"""Alaska Department of Snow (ADS) online agent.

A secure, grounded ADK agent that answers resident questions about snow services
(plowing, school/road closures, winter prep) using:
  * a RAG corpus built from official ADS documents (backend data store), and
  * live National Weather Service data (backend API).

Safety filtering (Model Armor) and prompt/response logging are wired via callbacks.
"""

from google.adk.agents import Agent

from . import callbacks, config
from .tools import get_weather_alerts, get_weather_forecast, retrieve_ads_docs

INSTRUCTION = """You are the Alaska Department of Snow (ADS) virtual assistant.
You help residents with snow plowing, road and school closures, winter
preparedness, and related ADS services.

Rules:
- For questions about ADS policies, services, or procedures, ALWAYS call
  `retrieve_ads_docs` first and base your answer only on what it returns.
- For current conditions (forecasts, active winter-storm warnings), use
  `get_weather_forecast` or `get_weather_alerts`.
- If the documents do not contain the answer, say you don't have that
  information and direct the resident to their regional ADS office. Never invent
  policies, phone numbers, or closure decisions.
- Be concise and plain-spoken. Do not request or repeat personal information.
- Only answer questions related to ADS and Alaska winter services.
"""


def _build_tools() -> list:
    tools = [get_weather_forecast, get_weather_alerts]
    if config.RAG_CORPUS:
        tools.insert(0, retrieve_ads_docs)
    return tools


root_agent = Agent(
    name="ads_agent",
    model=config.MODEL,
    instruction=INSTRUCTION,
    description="Answers Alaska Department of Snow resident questions.",
    tools=_build_tools(),
    before_model_callback=callbacks.before_model_callback,
    after_model_callback=callbacks.after_model_callback,
)
