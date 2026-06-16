"""Create the RAG Engine corpus (backend data store) and import ADS documents.

Requirement: "Backend data store for RAG." Builds a Vertex AI RAG Engine corpus
and ingests the ADS documents you staged with scripts/01_stage_data.sh.

Uses RAG Engine **Serverless mode** (available in us-central1 without an
allowlist, unlike Spanner mode) with its fully managed default vector database.

Idempotent: re-uses an existing corpus with the same display name and skips the
import if files are already present.

Run:  uv run python scripts/02_create_rag_corpus.py
Then paste the printed ADS_RAG_CORPUS value into .env.
"""

import vertexai
from vertexai.preview import rag

from ads_agent import config

DISPLAY_NAME = "alaska-dept-of-snow"
SOURCE = f"gs://{config.DATA_BUCKET}/alaska-dept-of-snow"

vertexai.init(project=config.PROJECT, location=config.LOCATION)

# Switch this region's RAG Engine to Serverless mode (idempotent). New projects
# can't use the default Spanner mode in us-central1 without an allowlist.
print("Setting RAG Engine to Serverless mode...")
rag.update_rag_engine_config(
    rag_engine_config=rag.RagEngineConfig(
        name=f"projects/{config.PROJECT}/locations/{config.LOCATION}/ragEngineConfig",
        rag_managed_db_config=rag.RagManagedDbConfig(mode=rag.Serverless()),
    )
)

# Re-use an existing corpus with this display name, else create one.
corpus = next(
    (c for c in rag.list_corpora() if c.display_name == DISPLAY_NAME), None
)
if corpus:
    print(f"Re-using existing corpus: {corpus.name}")
else:
    corpus = rag.create_corpus(
        display_name=DISPLAY_NAME,
        description="Official Alaska Department of Snow documents for resident Q&A.",
    )
    print(f"Created corpus: {corpus.name}")

# Skip the import if the corpus already has files.
if any(True for _ in rag.list_files(corpus.name)):
    print("Corpus already has files; skipping import.")
else:
    print(f"Importing files from {SOURCE} ...")
    response = rag.import_files(
        corpus.name,
        paths=[SOURCE],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
    )
    print(f"Imported {response.imported_rag_files_count} files.")

print("\n--- Paste into .env ---")
print(f"ADS_RAG_CORPUS={corpus.name}")
