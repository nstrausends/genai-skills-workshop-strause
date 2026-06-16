#!/usr/bin/env bash
# Stage the ADS documents into your own bucket so Vertex RAG can ingest them.
#
# The workshop source bucket (gs://labs.roitraining.com) belongs to ROI Training,
# and the Vertex RAG service agent has no access to it. We copy the data into a
# bucket in your project and grant the RAG service agent read access there.
#
# Idempotent: safe to re-run (bucket create + copy + IAM binding all no-op if
# already done).
set -euo pipefail

source "$(dirname "$0")/../.env"
ADS_DATA_BUCKET="${ADS_DATA_BUCKET:-${GOOGLE_CLOUD_PROJECT}-ads-data}"

SOURCE="gs://labs.roitraining.com/alaska-dept-of-snow"
DEST="gs://${ADS_DATA_BUCKET}/alaska-dept-of-snow"

PROJECT_NUMBER="$(gcloud projects describe "$GOOGLE_CLOUD_PROJECT" --format='value(projectNumber)')"
RAG_SA="service-${PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com"

# 1. Data bucket in your project (idempotent).
gcloud storage buckets create "gs://${ADS_DATA_BUCKET}" \
  --location="$GOOGLE_CLOUD_LOCATION" 2>/dev/null || \
  echo "Bucket gs://${ADS_DATA_BUCKET} already exists, skipping."

# 2. Copy the ADS documents from the workshop bucket into yours.
echo "Copying ${SOURCE} -> ${DEST} ..."
gcloud storage cp -r "$SOURCE" "gs://${ADS_DATA_BUCKET}/"

# 3. Let the Vertex RAG service agent read the staged data.
gcloud storage buckets add-iam-policy-binding "gs://${ADS_DATA_BUCKET}" \
  --member="serviceAccount:${RAG_SA}" \
  --role="roles/storage.objectViewer" >/dev/null
echo "Granted ${RAG_SA} read access to gs://${ADS_DATA_BUCKET}."

echo "Done. Data staged at ${DEST}."
