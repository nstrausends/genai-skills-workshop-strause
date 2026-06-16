"""ADK callbacks wiring the secure request/response workflow.

`before_model_callback` returning an LlmResponse short-circuits the model call;
`after_model_callback` returning an LlmResponse replaces the model output.
"""

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types as genai_types

from . import observability, safety


def _last_user_text(llm_request: LlmRequest) -> str:
    for content in reversed(llm_request.contents or []):
        if content.role == "user" and content.parts:
            text = " ".join(p.text for p in content.parts if p.text)
            if text:
                return text
    return ""


def _response_text(llm_response: LlmResponse) -> str:
    if llm_response.content and llm_response.content.parts:
        return " ".join(p.text for p in llm_response.content.parts if p.text)
    return ""


def _blocked_response(message: str) -> LlmResponse:
    return LlmResponse(
        content=genai_types.Content(role="model", parts=[genai_types.Part(text=message)])
    )


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """Log + screen the inbound prompt; block the model call on a policy violation."""
    prompt = _last_user_text(llm_request)
    if not prompt:
        return None
    result = safety.screen_user_prompt(prompt)
    observability.log_interaction(
        "prompt",
        prompt,
        invocation_id=callback_context.invocation_id,
        blocked=result.blocked,
    )
    if result.blocked:
        return _blocked_response(result.reason)
    return None


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse | None:
    """Screen + log the outbound response; replace it on a policy violation."""
    text = _response_text(llm_response)
    if not text:
        return None  # tool-call / partial event, nothing to validate
    result = safety.screen_model_response(text)
    observability.log_interaction(
        "response",
        text,
        invocation_id=callback_context.invocation_id,
        blocked=result.blocked,
    )
    if result.blocked:
        return _blocked_response(result.reason)
    return None
