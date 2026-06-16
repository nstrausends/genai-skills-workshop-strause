"""Prompt filtering & response validation via Google Cloud Model Armor.

If no template is configured (local dev), screening is skipped (pass-through) so
the agent still runs without the cloud dependency.
"""

from dataclasses import dataclass
from functools import lru_cache

from google.api_core.client_options import ClientOptions

from . import config


@dataclass
class ScreenResult:
    blocked: bool
    reason: str = ""


@lru_cache(maxsize=1)
def _client():
    """Regional Model Armor client (endpoint is location-specific)."""
    from google.cloud import modelarmor_v1

    return modelarmor_v1.ModelArmorClient(
        client_options=ClientOptions(
            api_endpoint=f"modelarmor.{config.LOCATION}.rep.googleapis.com"
        )
    )


def _matched(sanitization_result) -> bool:
    from google.cloud import modelarmor_v1

    return (
        sanitization_result.filter_match_state
        == modelarmor_v1.FilterMatchState.MATCH_FOUND
    )


def screen_user_prompt(text: str) -> ScreenResult:
    """Screen an inbound user prompt (jailbreak/PI). blocked=True on violation."""
    if not config.MODEL_ARMOR_INPUT_TEMPLATE:
        return ScreenResult(blocked=False)
    from google.cloud import modelarmor_v1

    resp = _client().sanitize_user_prompt(
        modelarmor_v1.SanitizeUserPromptRequest(
            name=config.MODEL_ARMOR_INPUT_TEMPLATE,
            user_prompt_data=modelarmor_v1.DataItem(text=text),
        )
    )
    if _matched(resp.sanitization_result):
        return ScreenResult(
            blocked=True,
            reason="Your message was blocked by our safety filter. Please rephrase.",
        )
    return ScreenResult(blocked=False)


def screen_model_response(text: str) -> ScreenResult:
    """Screen an outbound response (sensitive data/URLs). blocked=True on violation."""
    if not config.MODEL_ARMOR_OUTPUT_TEMPLATE:
        return ScreenResult(blocked=False)
    from google.cloud import modelarmor_v1

    resp = _client().sanitize_model_response(
        modelarmor_v1.SanitizeModelResponseRequest(
            name=config.MODEL_ARMOR_OUTPUT_TEMPLATE,
            model_response_data=modelarmor_v1.DataItem(text=text),
        )
    )
    if _matched(resp.sanitization_result):
        return ScreenResult(
            blocked=True,
            reason="I can't share that response. Please contact your regional ADS office for help.",
        )
    return ScreenResult(blocked=False)
