from django.core.management.base import BaseCommand
from ledger.services.hashing import verify_chain
from django.utils import timezone
import json

class Command(BaseCommand):
    help = 'Verify the integrity of the ledger chain and report any broken entries.'

    def handle(self, *args, **options):
        results = verify_chain()
        failures = [record_id for record_id, ok in results if not ok]
        if not failures:
            self.stdout.write(self.style.SUCCESS('Ledger chain is valid – no tampering detected.'))
        else:
            # Trigger tamper alert (dummy Celery task or function)
            from ledger.tasks import dispatch_tamper_alert
            dispatch_tamper_alert(failures)
            self.stdout.write(self.style.ERROR(f'Ledger chain broken. Failed entries: {failures}'))
            # Output JSON payload for tooling
            payload = {
                'valid': False,
                'failures': failures,
                'checked_at': timezone.now().isoformat(),
            }
            self.stdout.write(json.dumps(payload))
