"""Hashing service for the tamper‑proof ledger.

All cryptographic operations are isolated here so the rest of the codebase
remains agnostic of the underlying algorithm.
"""
import json
import hashlib
from typing import Dict, List, Tuple

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from ledger.models import LedgerEntry

GENESIS_HASH = "0" * 64  # 64‑character hex string of zeros


class HashingError(Exception):
    """Raised for unexpected errors in the hashing workflow."""


def _deterministic_json(payload: Dict) -> str:
    """Serialize *payload* to a deterministic JSON string.

    - ``sort_keys=True`` ensures consistent key ordering.
    - ``separators`` removes whitespace that would otherwise affect the hash.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_hash(payload: Dict, previous_hash: str) -> str:
    """Return the SHA‑256 hex digest of ``payload`` + ``previous_hash``.

    The function first serialises the payload deterministically, concatenates
    the resulting string with ``previous_hash`` and hashes the bytes using
    SHA‑256.
    """
    deterministic = _deterministic_json(payload)
    combined = deterministic + previous_hash
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def get_last_chain_hash() -> str:
    """Fetch the ``chain_hash`` of the most recent ledger entry.

    If no entry exists, the *genesis* hash is returned.
    """
    try:
        return LedgerEntry.objects.latest("created_at").chain_hash
    except LedgerEntry.DoesNotExist:
        return GENESIS_HASH


@transaction.atomic
def create_entry(payload: Dict) -> LedgerEntry:
    """Create a new immutable :class:`LedgerEntry`.

    The function:
    1. Retrieves the hash of the previous record.
    2. Computes the new ``chain_hash``.
    3. Persists the entry atomically.
    """
    previous_hash = get_last_chain_hash()
    chain_hash = compute_hash(payload, previous_hash)
    try:
        entry = LedgerEntry.objects.create(
            payload=payload,
            previous_hash=previous_hash,
            chain_hash=chain_hash,
        )
        return entry
    except Exception as exc:
        raise HashingError(f"Failed to create ledger entry: {exc}") from exc


def verify_chain() -> List[Tuple[int, bool]]:
    """Verify the integrity of the entire ledger chain.

    Returns a list of ``(record_id, is_valid)`` tuples. ``is_valid`` is ``True``
    when the stored ``chain_hash`` matches the recomputed hash using the stored
    ``previous_hash``.
    """
    results: List[Tuple[int, bool]] = []
    entries = LedgerEntry.objects.all().order_by("created_at")
    for entry in entries:
        expected = compute_hash(entry.payload, entry.previous_hash)
        results.append((entry.id, expected == entry.chain_hash))
    return results
