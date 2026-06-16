"""Evaluate the deployed ADS agent with the Vertex AI GenAI Evaluation Service.

Requirement: "Evaluation data using the Google Evaluation service API." This is
written in code (not the CLI): it loads eval_dataset.json, gets a real response
from the deployed agent for each prompt, then scores responses with the managed
evaluation service across quality, instruction-following, and safety metrics.

Run:  uv run python eval/run_eval.py   (requires ADS_AGENT_ENGINE_RESOURCE in .env)
"""

import json
from pathlib import Path

import pandas as pd
import vertexai
from vertexai.preview.evaluation import EvalTask, MetricPromptTemplateExamples

from ads_agent import config, remote

HERE = Path(__file__).parent
DATASET = HERE / "eval_dataset.json"
RESULTS = HERE / "results"

METRICS = [
    MetricPromptTemplateExamples.Pointwise.QUESTION_ANSWERING_QUALITY,
    MetricPromptTemplateExamples.Pointwise.INSTRUCTION_FOLLOWING,
    MetricPromptTemplateExamples.Pointwise.SAFETY,
]


def main() -> None:
    if not config.AGENT_ENGINE_RESOURCE:
        raise SystemExit("Set ADS_AGENT_ENGINE_RESOURCE in .env (deploy the agent first).")

    vertexai.init(project=config.PROJECT, location=config.LOCATION)
    cases = json.loads(DATASET.read_text())

    print(f"Querying deployed agent for {len(cases)} eval prompts...")
    rows = []
    for case in cases:
        response = remote.query_agent(case["prompt"], user_id="eval-user")
        rows.append(
            {
                "prompt": case["prompt"],
                "response": response,
                "reference": case.get("reference", ""),
            }
        )

    eval_dataset = pd.DataFrame(rows)
    eval_task = EvalTask(
        dataset=eval_dataset, metrics=METRICS, experiment="ads-agent-eval"
    )
    result = eval_task.evaluate()

    print("\n=== Summary metrics ===")
    for metric, score in result.summary_metrics.items():
        print(f"  {metric}: {score}")

    RESULTS.mkdir(exist_ok=True)
    result.metrics_table.to_csv(RESULTS / "metrics_table.csv", index=False)
    with open(RESULTS / "summary_metrics.json", "w") as f:
        json.dump(result.summary_metrics, f, indent=2, default=str)
    print(f"\nSaved detailed results to {RESULTS}/")


if __name__ == "__main__":
    main()
