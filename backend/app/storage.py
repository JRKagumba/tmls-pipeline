"""Best-effort persistence of chat interactions to a GCS bucket (JSON).

Storage is intentionally non-fatal: if the bucket isn't configured or the write
fails, we log and return None so the chat reply is still delivered to the user.

Config (env vars):
- GCS_BUCKET                      bucket name (no write happens if unset)
- GCS_PREFIX                      object key prefix (default "interactions")
- GOOGLE_APPLICATION_CREDENTIALS  path to a service-account JSON key (local dev).
                                  On Cloud Run, omit it — the runtime service
                                  account is used automatically.
"""

import datetime
import json
import logging
import os
import uuid

from google.cloud import storage

logger = logging.getLogger("pipeline.storage")

_client = None


def _get_client():
    global _client
    if _client is None:
        # Picks up GOOGLE_APPLICATION_CREDENTIALS, or ADC on Cloud Run.
        _client = storage.Client()
    return _client


def store_interaction(record: dict) -> str | None:
    """Write one interaction record as a JSON object. Returns gs:// path or None."""
    bucket_name = os.getenv("GCS_BUCKET")
    if not bucket_name:
        logger.warning("GCS_BUCKET not set — skipping interaction storage")
        return None

    try:
        prefix = os.getenv("GCS_PREFIX", "interactions").strip("/")
        ts = datetime.datetime.now(datetime.timezone.utc)
        blob_path = (
            f"{prefix}/{ts:%Y/%m/%d}/{ts:%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:8]}.json"
        )
        blob = _get_client().bucket(bucket_name).blob(blob_path)
        blob.upload_from_string(
            json.dumps(record, ensure_ascii=False, indent=2),
            content_type="application/json",
        )
        return f"gs://{bucket_name}/{blob_path}"
    except Exception:
        logger.exception("Failed to store interaction in GCS")
        return None
