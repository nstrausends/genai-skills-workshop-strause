"""Create the Model Armor templates for prompt filtering & response validation.

Requirement: "Prompt filtering and response validation." Two templates with
distinct policies:

  * INPUT  (ads-input-guardrails)  — screens user prompts for prompt-injection /
    jailbreak plus responsible-AI categories (hate, harassment, sexual, dangerous).
  * OUTPUT (ads-output-guardrails) — validates model responses for sensitive-data
    leakage (SDP), malicious URLs, and the same responsible-AI categories. This
    matters when answers are drawn from internal RAG documents.

The agent references these by name (see ads_agent/safety.py).

Idempotent: re-uses a template if it already exists.

Run:  uv run python scripts/03_create_model_armor.py
Then paste the printed values into .env.
"""

from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1 as ma

from ads_agent import config

parent = f"projects/{config.PROJECT}/locations/{config.LOCATION}"

client = ma.ModelArmorClient(
    client_options=ClientOptions(
        api_endpoint=f"modelarmor.{config.LOCATION}.rep.googleapis.com"
    )
)

# Responsible-AI categories — a safety baseline on both directions.
rai = ma.RaiFilterSettings(
    rai_filters=[
        ma.RaiFilterSettings.RaiFilter(
            filter_type=t, confidence_level=ma.DetectionConfidenceLevel.MEDIUM_AND_ABOVE
        )
        for t in (
            ma.RaiFilterType.HATE_SPEECH,
            ma.RaiFilterType.HARASSMENT,
            ma.RaiFilterType.SEXUALLY_EXPLICIT,
            ma.RaiFilterType.DANGEROUS,
        )
    ]
)

# INPUT policy: catch prompt injection / jailbreak attempts.
input_filter = ma.FilterConfig(
    rai_settings=rai,
    pi_and_jailbreak_filter_settings=ma.PiAndJailbreakFilterSettings(
        filter_enforcement=ma.PiAndJailbreakFilterSettings.PiAndJailbreakFilterEnforcement.ENABLED,
        confidence_level=ma.DetectionConfidenceLevel.MEDIUM_AND_ABOVE,
    ),
)

# OUTPUT policy: catch sensitive-data leakage and malicious URLs in responses.
output_filter = ma.FilterConfig(
    rai_settings=rai,
    sdp_settings=ma.SdpFilterSettings(
        basic_config=ma.SdpBasicConfig(
            filter_enforcement=ma.SdpBasicConfig.SdpBasicConfigEnforcement.ENABLED
        )
    ),
    malicious_uri_filter_settings=ma.MaliciousUriFilterSettings(
        filter_enforcement=ma.MaliciousUriFilterSettings.MaliciousUriFilterEnforcement.ENABLED,
    ),
)


def ensure_template(template_id: str, filter_config: ma.FilterConfig) -> str:
    try:
        created = client.create_template(
            parent=parent,
            template_id=template_id,
            template=ma.Template(filter_config=filter_config),
        )
        print(f"Created template: {created.name}")
        return created.name
    except Exception as exc:  # noqa: BLE001 - likely already exists
        name = f"{parent}/templates/{template_id}"
        print(f"create_template({template_id}) failed ({exc}); assuming it exists: {name}")
        return name


input_name = ensure_template("ads-input-guardrails", input_filter)
output_name = ensure_template("ads-output-guardrails", output_filter)

print("\n--- Paste into .env ---")
print(f"ADS_MODEL_ARMOR_INPUT_TEMPLATE={input_name}")
print(f"ADS_MODEL_ARMOR_OUTPUT_TEMPLATE={output_name}")
