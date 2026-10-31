import json
from django.test import TestCase, Client, override_settings
from django.core.management import call_command
from django.utils import timezone
from io import StringIO

from ledger.models import LedgerEntry
from ledger.services.hashing import create_entry, compute_hash, GENESIS_HASH

class HashingServiceTests(TestCase):
    def test_genesis_entry(self):
        # First entry should have previous_hash = GENESIS_HASH
        payload = {'message': 'first'}
        entry = create_entry(payload)
        self.assertEqual(entry.previous_hash, GENESIS_HASH)
        expected_hash = compute_hash(payload, GENESIS_HASH)
        self.assertEqual(entry.chain_hash, expected_hash)

    def test_chain_continuity(self):
        # Create three entries and verify the chain
        data = [
            {'msg': 'one'},
            {'msg': 'two'},
            {'msg': 'three'},
        ]
        entries = []
        for d in data:
            entries.append(create_entry(d))
        # Verify each entry's chain_hash matches recomputed value
        for entry in entries:
            expected = compute_hash(entry.payload, entry.previous_hash)
            self.assertEqual(entry.chain_hash, expected)

    def test_tamper_detection(self):
        # Create entry, manually corrupt payload, then verify chain
        entry = create_entry({'key': 'value'})
        # Directly alter payload in DB to simulate tampering
        LedgerEntry.objects.filter(id=entry.id).update(payload={'key': 'tampered'})
        from ledger.services.hashing import verify_chain
        results = verify_chain()
        # Should detect failure for the altered entry
        self.assertTrue(any(not ok for _, ok in results))

class ApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.valid_token = 'testtoken123'
        self.headers = {
            'HTTP_AUTHORIZATION': f'Bearer {self.valid_token}'
        }

    @override_settings(API_TOKENS=['testtoken123'])
    def test_create_entry_success(self):
        payload = {'event': 'login', 'user': 'alice'}
        response = self.client.post('/api/v1/ledger/', data=json.dumps(payload), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)
        self.assertIn('chain_hash', data)
        self.assertIn('previous_hash', data)
        self.assertIn('created_at', data)

    @override_settings(API_TOKENS=['testtoken123'])
    def test_missing_token_returns_401(self):
        payload = {'event': 'logout'}
        response = self.client.post('/api/v1/ledger/', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get('error'), 'Missing or malformed Authorization header')

    @override_settings(API_TOKENS=['testtoken123'])
    def test_invalid_token_returns_401(self):
        payload = {'event': 'logout'}
        bad_headers = {'HTTP_AUTHORIZATION': 'Bearer wrongtoken'}
        response = self.client.post('/api/v1/ledger/', data=json.dumps(payload), content_type='application/json', **bad_headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get('error'), 'Invalid API token')

    @override_settings(API_TOKENS=['testtoken123'])
    def test_verify_chain_endpoint(self):
        # Create two entries
        for i in range(2):
            self.client.post('/api/v1/ledger/', data=json.dumps({'seq': i}), content_type='application/json', **self.headers)
        # Verify chain – should be valid
        resp = self.client.get('/api/v1/ledger/verify/', **self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get('valid'))
        self.assertEqual(resp.json().get('failures'), [])
        # Tamper with the first entry directly
        first = LedgerEntry.objects.first()
        LedgerEntry.objects.filter(id=first.id).update(payload={'seq': 999})
        resp2 = self.client.get('/api/v1/ledger/verify/', **self.headers)
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(resp2.json().get('valid'))
        self.assertIn(first.id, resp2.json().get('failures'))

class ManagementCommandTests(TestCase):
    def setUp(self):
        # Create a valid ledger chain
        for i in range(3):
            create_entry({'index': i})
        self.out = StringIO()

    def test_verify_ledger_success(self):
        call_command('verify_ledger', stdout=self.out)
        output = self.out.getvalue()
        self.assertIn('Ledger chain is valid', output)

    def test_verify_ledger_failure(self):
        # Tamper with middle entry
        middle = LedgerEntry.objects.get(payload__contains='"index": 1')
        LedgerEntry.objects.filter(id=middle.id).update(payload={'index': 'tampered'})
        self.out = StringIO()
        call_command('verify_ledger', stdout=self.out)
        output = self.out.getvalue()
        self.assertIn('Ledger chain broken', output)
        self.assertIn(str(middle.id), output)
