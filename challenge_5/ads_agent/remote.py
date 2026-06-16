"""Thin client for querying the deployed Agent Engine app.

Shared by the Streamlit frontend and the evaluation script so both talk to the
same deployed agent the same way.
"""

from functools import lru_cache

import vertexai
from vertexai import agent_engines

from . import config


@lru_cache(maxsize=1)
def _remote_app():
    vertexai.init(project=config.PROJECT, location=config.LOCATION)
    return agent_engines.get(config.AGENT_ENGINE_RESOURCE)


def query_agent(message: str, user_id: str = "web-user") -> str:
    """Send one message to the deployed agent and return its final text reply."""
    app = _remote_app()
    session = app.create_session(user_id=user_id)
    session_id = session["id"] if isinstance(session, dict) else session.id

    chunks: list[str] = []
    for event in app.stream_query(
        user_id=user_id, session_id=session_id, message=message
    ):
        if not isinstance(event, dict):
            continue
        # Surface runtime errors instead of silently returning an empty reply.
        if event.get("error_code") or event.get("error_message"):
            raise RuntimeError(
                f"Agent error [{event.get('error_code')}]: {event.get('error_message')}"
            )
        for part in (event.get("content") or {}).get("parts", []):
            if part.get("text"):
                chunks.append(part["text"])
    return "".join(chunks).strip()
