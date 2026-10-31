from __future__ import annotations
import json
import logging

logger = logging.getLogger(__name__)

def dispatch_tamper_alert(failed_ids: list[int]) -> None:
    """Dummy alert dispatcher.

    In a real deployment this could enqueue a Celery task that posts a webhook
    to a monitoring service. Here we simply log the alert for demonstration.
    """
    alert_payload = {
        "alert": "Ledger tampering detected",
        "failed_entry_ids": failed_ids,
    }
    # Log at warning level – in production this would be a high‑priority alert.
    logger.warning("Tamper alert dispatched: %s", json.dumps(alert_payload))
    # For visual feedback during local runs we also print.
    print("[ALERT] Tamper detection payload:", json.dumps(alert_payload))
