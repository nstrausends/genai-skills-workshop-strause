"""Unit tests for the secure-workflow callbacks (safety + logging mocked)."""

from types import SimpleNamespace

from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types as genai_types

import ads_agent.callbacks as cb
from ads_agent.safety import ScreenResult

_CTX = SimpleNamespace(invocation_id="inv-1")


def _user_req(text):
    return LlmRequest(
        contents=[genai_types.Content(role="user", parts=[genai_types.Part(text=text)])]
    )


def _model_resp(text):
    return LlmResponse(
        content=genai_types.Content(role="model", parts=[genai_types.Part(text=text)])
    )


def test_extract_helpers():
    assert cb._last_user_text(_user_req("hello")) == "hello"
    assert cb._response_text(_model_resp("world")) == "world"


def test_before_model_logs_and_passes(monkeypatch):
    logged = []
    monkeypatch.setattr(cb.observability, "log_interaction", lambda *a, **k: logged.append(a))
    monkeypatch.setattr(cb.safety, "screen_user_prompt", lambda t: ScreenResult(blocked=False))
    assert cb.before_model_callback(_CTX, _user_req("when is plowing?")) is None
    assert logged and logged[0][0] == "prompt"


def test_before_model_blocks_bad_prompt(monkeypatch):
    monkeypatch.setattr(cb.observability, "log_interaction", lambda *a, **k: None)
    monkeypatch.setattr(
        cb.safety, "screen_user_prompt", lambda t: ScreenResult(blocked=True, reason="nope")
    )
    out = cb.before_model_callback(_CTX, _user_req("do something evil"))
    assert isinstance(out, LlmResponse)
    assert out.content.parts[0].text == "nope"


def test_after_model_replaces_bad_response(monkeypatch):
    monkeypatch.setattr(cb.observability, "log_interaction", lambda *a, **k: None)
    monkeypatch.setattr(
        cb.safety, "screen_model_response", lambda t: ScreenResult(blocked=True, reason="redacted")
    )
    out = cb.after_model_callback(_CTX, _model_resp("leaked secret"))
    assert isinstance(out, LlmResponse)
    assert out.content.parts[0].text == "redacted"


def test_after_model_ignores_empty_response(monkeypatch):
    monkeypatch.setattr(cb.observability, "log_interaction", lambda *a, **k: None)
    monkeypatch.setattr(cb.safety, "screen_model_response", lambda t: ScreenResult(blocked=False))
    assert cb.after_model_callback(_CTX, LlmResponse()) is None
