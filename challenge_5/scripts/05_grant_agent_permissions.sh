#!/usr/bin/env bash
# Grant the Agent Engine runtime service account the permissions the deployed
# agent needs at request time:
#   - aiplatform.user   -> query the RAG corpus + invoke Gemini
#   - modelarmor.user   -> sanitize prompts/responses
#   - logging.logWriter -> write the prompt/response audit log
#
# Agent Engine runs as the AI Platform Reasoning Engine service agent
# (service-<PROJECT_NUMBER>@gcp-sa-aiplatform-re.iam.gserviceaccount.com).
# Run this once after the first deploy; IAM changes propagate within ~1-2 min.
# Idempotent.
set -euo pipefail

source "$(dirname "$0")/../.env"

PROJECT_NUMBER="$(gcloud projects describe "$GOOGLE_CLOUD_PROJECT" --format='value(projectNumber)')"
SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

for role in roles/aiplatform.user roles/modelarmor.user roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$GOOGLE_CLOUD_PROJECT" \
    --member="serviceAccount:${SA}" \
    --role="$role" --condition=None >/dev/null
  echo "Granted ${role} to ${SA}"
done

echo "Done. Wait ~1-2 minutes for IAM to propagate."
