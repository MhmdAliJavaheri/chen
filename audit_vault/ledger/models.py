from django.db import models
from django.core.exceptions import ValidationError


class LedgerEntry(models.Model):
    """Immutable ledger entry linking to the previous hash.

    Each entry stores the raw JSON payload, the hash of the previous entry,
    and the computed chain hash (SHA‑256 over payload + previous_hash).
    """

    payload = models.JSONField(help_text="Original log content as JSON.")
    previous_hash = models.CharField(
        max_length=64,
        help_text="Hex‑encoded SHA‑256 of the previous entry's chain_hash. "
        "For the first entry use a constant of 64 zeros.",
    )
    chain_hash = models.CharField(
        max_length=64,
        unique=True,
        help_text="Hex‑encoded SHA‑256 of payload + previous_hash.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"

    def save(self, *args, **kwargs):
        """Prevent updates – entries are immutable once created.

        If the instance already has a primary key, we raise an error to
        enforce write‑once semantics.
        """
        if self.pk is not None:
            raise ValidationError("LedgerEntry instances are immutable and cannot be updated.")
        super().save(*args, **kwargs)
