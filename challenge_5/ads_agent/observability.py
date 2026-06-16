"""Structured logging of every prompt and response to Cloud Logging.

Falls back to stdlib logging if the Cloud Logging client is unavailable
(e.g. local dev without credentials).
"""

import logging
from functools import lru_cache

from . import config

_stdlib = logging.getLogger("ads-agent")


@lru_cache(maxsize=1)
def _cloud_logger():
    try:
        import google.cloud.logging

        client = google.cloud.logging.Client(project=config.PROJECT or None)
        return client.logger(config.LOG_NAME)
    except Exception:  # noqa: BLE001 - degrade gracefully off-cloud
        return None


def log_interaction(kind: str, text: str, **fields) -> None:
    """Write one structured interaction entry (kind = 'prompt' | 'response')."""
    payload = {"kind": kind, "text": text, "log": config.LOG_NAME, **fields}
    logger = _cloud_logger()
    if logger is not None:
        logger.log_struct(payload, severity="INFO")
    else:
        _stdlib.info("%s: %s", kind, payload)
