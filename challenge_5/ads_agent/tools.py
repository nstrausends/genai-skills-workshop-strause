"""Backend API tool: live weather + alerts from the National Weather Service.

Requirement: "Access to backend API functionality." The agent uses these to
answer real-time questions (snow forecasts, winter-storm alerts) that the static
RAG corpus cannot, e.g. "is there a snow warning for Anchorage right now?".

api.weather.gov is a free, no-key US government API. It requires a descriptive
User-Agent header.
"""

import requests

from . import config

_NWS = "https://api.weather.gov"
_HEADERS = {"User-Agent": "AlaskaDeptOfSnow-Agent (contact: ads-it@alaska.gov)"}
_TIMEOUT = 10

# A few Alaska population centers so residents can ask by name, not lat/lon.
ALASKA_CITIES = {
    "anchorage": (61.2181, -149.9003),
    "fairbanks": (64.8378, -147.7164),
    "juneau": (58.3019, -134.4197),
    "wasilla": (61.5814, -149.4394),
    "nome": (64.5011, -165.4064),
}


def retrieve_ads_docs(query: str) -> dict:
    """Retrieve official Alaska Department of Snow documentation about plowing,
    closures, services, and winter procedures.

    Args:
        query: The resident's question or search terms.

    Returns:
        dict with 'status' and a 'contexts' list of relevant document snippets.
    """
    # Plain function tool (not the VertexAiRagRetrieval grounding tool) so it
    # coexists with the weather function tools without disabling function calling.
    from vertexai.preview import rag

    try:
        response = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=config.RAG_CORPUS)],
            similarity_top_k=5,
            vector_distance_threshold=0.6,
        )
        contexts = [
            {"text": c.text, "source": c.source_display_name or c.source_uri}
            for c in response.contexts.contexts
        ]
        return {"status": "success", "contexts": contexts}
    except Exception as exc:  # noqa: BLE001 - surface retrieval errors to the model
        return {"status": "error", "error": f"Document retrieval failed: {exc}"}


def get_weather_forecast(city: str) -> dict:
    """Get the short-term weather forecast for an Alaska city.

    Args:
        city: An Alaska city name, e.g. "Anchorage", "Fairbanks", "Juneau".

    Returns:
        dict with 'status' and, on success, a 'forecast' list of upcoming periods.
    """
    coords = ALASKA_CITIES.get(city.strip().lower())
    if not coords:
        return {
            "status": "error",
            "error": f"Unknown city '{city}'. Known cities: {', '.join(sorted(ALASKA_CITIES))}.",
        }
    lat, lon = coords
    try:
        points = requests.get(
            f"{_NWS}/points/{lat},{lon}", headers=_HEADERS, timeout=_TIMEOUT
        )
        points.raise_for_status()
        forecast_url = points.json()["properties"]["forecast"]
        forecast = requests.get(forecast_url, headers=_HEADERS, timeout=_TIMEOUT)
        forecast.raise_for_status()
        periods = forecast.json()["properties"]["periods"][:4]
        return {
            "status": "success",
            "city": city,
            "forecast": [
                {"name": p["name"], "forecast": p["detailedForecast"]} for p in periods
            ],
        }
    except (requests.RequestException, KeyError, ValueError) as exc:
        return {"status": "error", "error": f"Weather service unavailable: {exc}"}


def get_weather_alerts(area: str) -> dict:
    """Get active National Weather Service alerts (e.g. winter storm warnings).

    Args:
        area: Two-letter US state code, e.g. "AK" for Alaska.

    Returns:
        dict with 'status' and, on success, an 'alerts' list (empty if none active).
    """
    try:
        resp = requests.get(
            f"{_NWS}/alerts/active",
            params={"area": area.strip().upper()},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        alerts = [
            {
                "event": f["properties"]["event"],
                "headline": f["properties"].get("headline", ""),
                "severity": f["properties"].get("severity", ""),
                "area": f["properties"].get("areaDesc", ""),
            }
            for f in features[:10]
        ]
        return {"status": "success", "area": area, "count": len(alerts), "alerts": alerts}
    except (requests.RequestException, KeyError, ValueError) as exc:
        return {"status": "error", "error": f"Weather service unavailable: {exc}"}
