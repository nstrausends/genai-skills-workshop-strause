"""Run the ADS agent locally (in-process), no Agent Engine deployment needed.

Useful for smoke-testing the agent, tools, safety callbacks, and RAG grounding
before deploying. Uses ADK's in-memory runner.

Requires Google Cloud auth (`gcloud auth application-default login`) and, in .env:
GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION. Set ADS_RAG_CORPUS to test RAG
grounding and ADS_MODEL_ARMOR_TEMPLATE to test prompt/response filtering
(both are optional locally — the agent still runs without them).

Usage:
    uv run python local_run.py                       # interactive chat
    uv run python local_run.py "When is plowing?"    # one-shot question
"""

import asyncio
import sys

from google.adk.runners import InMemoryRunner
from google.genai import types

from ads_agent import config
from ads_agent.agent import root_agent

APP = "ads_agent"
USER = "local-user"


async def ask(runner: InMemoryRunner, session_id: str, question: str) -> str:
    message = types.Content(role="user", parts=[types.Part(text=question)])
    reply = ""
    async for event in runner.run_async(
        user_id=USER, session_id=session_id, new_message=message
    ):
        if event.get_function_calls():
            for call in event.get_function_calls():
                print(f"  [tool call] {call.name}({dict(call.args)})")
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(p.text for p in event.content.parts if p.text)
    return reply


async def main() -> None:
    if not config.PROJECT:
        raise SystemExit("Set GOOGLE_CLOUD_PROJECT in .env first.")
    print(f"Project: {config.PROJECT} | Location: {config.LOCATION} | Model: {config.MODEL}")
    print(f"RAG corpus: {'set' if config.RAG_CORPUS else 'NOT set (RAG disabled)'} | "
          f"Model Armor: {'set' if config.MODEL_ARMOR_TEMPLATE else 'NOT set (filtering disabled)'}\n")

    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)

    if len(sys.argv) > 1:  # one-shot
        question = " ".join(sys.argv[1:])
        print(f"> {question}")
        print(await ask(runner, session.id, question))
        return

    print("Interactive mode — type a question (Ctrl-C or 'exit' to quit).")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            print(await ask(runner, session.id, question))


if __name__ == "__main__":
    asyncio.run(main())
