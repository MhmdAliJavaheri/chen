import json
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.http import require_http_methods
from django.utils.timezone import utc

from ledger.services.hashing import create_entry, get_last_chain_hash, verify_chain, GENESIS_HASH
from ledger.models import LedgerEntry


def _parse_json_body(request):
    """Parse and validate that the request body is a JSON object.

    Returns the parsed dict or raises ``HttpResponseBadRequest``.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponseBadRequest(json.dumps({"error": "Invalid JSON payload"}), content_type="application/json")
    if not isinstance(data, dict):
        return HttpResponseBadRequest(json.dumps({"error": "Payload must be a JSON object"}), content_type="application/json")
    return data


@require_http_methods(["POST"])
def create_entry_view(request):
    """Create a new ledger entry.

    Expected request body: JSON object representing the log payload.
    Response (201): {
        "id": <int>,
        "chain_hash": <str>,
        "previous_hash": <str>,
        "created_at": <ISO‑8601 string>
    }
    """
    parsed = _parse_json_body(request)
    if isinstance(parsed, HttpResponseBadRequest):
        return parsed

    entry = create_entry(parsed)
    response_data = {
        "id": entry.id,
        "chain_hash": entry.chain_hash,
        "previous_hash": entry.previous_hash,
        "created_at": entry.created_at.astimezone(utc).isoformat(),
    }
    return JsonResponse(response_data, status=201)


@require_http_methods(["GET"])
def retrieve_entry_view(request, entry_id):
    """Return a single ledger entry by ID.

    Response (200): {
        "id": <int>,
        "payload": <object>,
        "previous_hash": <str>,
        "chain_hash": <str>,
        "created_at": <ISO‑8601 string>
    }
    """
    try:
        entry = LedgerEntry.objects.get(pk=entry_id)
    except LedgerEntry.DoesNotExist:
        return HttpResponseNotFound(json.dumps({"error": "Entry not found"}), content_type="application/json")

    data = {
        "id": entry.id,
        "payload": entry.payload,
        "previous_hash": entry.previous_hash,
        "chain_hash": entry.chain_hash,
        "created_at": entry.created_at.astimezone(utc).isoformat(),
    }
    return JsonResponse(data)


@require_http_methods(["GET"])
def latest_entry_view(request):
    """Return the most recent ledger entry.
    If no entries exist, returns 404.
    """
    try:
        entry = LedgerEntry.objects.latest("created_at")
    except LedgerEntry.DoesNotExist:
        return HttpResponseNotFound(json.dumps({"error": "No entries found"}), content_type="application/json")
    data = {
        "id": entry.id,
        "payload": entry.payload,
        "previous_hash": entry.previous_hash,
        "chain_hash": entry.chain_hash,
        "created_at": entry.created_at.astimezone(utc).isoformat(),
    }
    return JsonResponse(data)


@require_http_methods(["GET"])
def verify_chain_view(request):
    """Verify the whole ledger chain.

    Returns {
        "valid": <bool>,
        "failures": [<int>, ...]
    }
    """
    results = verify_chain()
    failures = [record_id for record_id, ok in results if not ok]
    return JsonResponse({"valid": len(failures) == 0, "failures": failures})
