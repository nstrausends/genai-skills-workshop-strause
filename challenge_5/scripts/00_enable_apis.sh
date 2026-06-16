#!/usr/bin/env bash
# Enable every Google Cloud API the ADS agent needs, and create the staging
# bucket used by Agent Engine. Run once per project.
#
# Prereqs: gcloud installed + `gcloud auth login` + `gcloud auth application-default login`.
set -euo pipefail

source "$(dirname "$0")/../.env"
ADS_STAGING_BUCKET="${ADS_STAGING_BUCKET:-${GOOGLE_CLOUD_PROJECT}-ads-staging}"

gcloud config set project "$GOOGLE_CLOUD_PROJECT"

gcloud services enable \
  aiplatform.googleapis.com \
  vectorsearch.googleapis.com \
  modelarmor.googleapis.com \
  logging.googleapis.com \
  storage.googleapis.com \
  cloudresourcemanager.googleapis.com

# Staging bucket for Agent Engine deployment artifacts (idempotent).
gcloud storage buckets create "gs://${ADS_STAGING_BUCKET}" \
  --location="$GOOGLE_CLOUD_LOCATION" 2>/dev/null || \
  echo "Bucket gs://${ADS_STAGING_BUCKET} already exists, skipping."

echo "APIs enabled and staging bucket ready."
