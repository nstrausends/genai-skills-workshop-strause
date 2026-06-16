"""Unit tests for the backend-API weather tools (deterministic, network mocked)."""

from types import SimpleNamespace

import ads_agent.tools as tools


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_forecast_unknown_city_returns_error():
    result = tools.get_weather_forecast("Atlantis")
    assert result["status"] == "error"
    assert "Unknown city" in result["error"]


def test_forecast_success(monkeypatch):
    def fake_get(url, **kwargs):
        if "/points/" in url:
            return _Resp({"properties": {"forecast": "https://api.weather.gov/fc"}})
        return _Resp(
            {"properties": {"periods": [{"name": "Tonight", "detailedForecast": "Snow."}]}}
        )

    monkeypatch.setattr(tools.requests, "get", fake_get)
    result = tools.get_weather_forecast("Anchorage")
    assert result["status"] == "success"
    assert result["forecast"][0]["name"] == "Tonight"


def test_alerts_success(monkeypatch):
    payload = {
        "features": [
            {
                "properties": {
                    "event": "Winter Storm Warning",
                    "headline": "Heavy snow expected",
                    "severity": "Severe",
                    "areaDesc": "Anchorage",
                }
            }
        ]
    }
    monkeypatch.setattr(tools.requests, "get", lambda url, **kw: _Resp(payload))
    result = tools.get_weather_alerts("AK")
    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["alerts"][0]["event"] == "Winter Storm Warning"


def test_alerts_handles_service_error(monkeypatch):
    def boom(url, **kwargs):
        raise tools.requests.RequestException("down")

    monkeypatch.setattr(tools.requests, "get", boom)
    result = tools.get_weather_alerts("AK")
    assert result["status"] == "error"


def test_retrieve_ads_docs(monkeypatch):
    from vertexai.preview import rag

    fake = SimpleNamespace(
        contexts=SimpleNamespace(
            contexts=[
                SimpleNamespace(text="Plowing starts on primary routes.",
                                source_display_name="plowing.pdf", source_uri="gs://x")
            ]
        )
    )
    monkeypatch.setattr(tools.config, "RAG_CORPUS", "projects/p/locations/l/ragCorpora/1")
    monkeypatch.setattr(rag, "retrieval_query", lambda **kw: fake)
    result = tools.retrieve_ads_docs("when does plowing start")
    assert result["status"] == "success"
    assert result["contexts"][0]["text"].startswith("Plowing")
    assert result["contexts"][0]["source"] == "plowing.pdf"
