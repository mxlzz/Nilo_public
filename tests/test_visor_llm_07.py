"""Regression for real-sized provenance loss, bounded decoding and read-only history."""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zlib

from nilo_runtime.agent import provenance, provenance_codec as codec
from nilo_runtime.agent.trace_context import capture_call, observe_context, transport_started
from nilo_runtime.labs.llm_read import LocalLLMReadAPI, ReadError
from nilo_runtime.storage.llm_requests import RequestTraceStore


def fixture(count=450):
    # Synthetic data only. Comparable path count/size to the uploaded run.
    original = {'necesidades': {'energia': 'con energía'},
                'memorias_relevantes': [{'id': str(i), 'detalle': {'lugar': i, 'estado': 'previo'}}
                                       for i in range(count)],
                'oculto': {'valor': 'PRIVATE_VALUE_NEVER_PERSIST'}}
    final = {'necesidades': original['necesidades'],
             'memorias_relevantes': original['memorias_relevantes'][-3:]}
    body = json.dumps({'messages': [{'role': 'user', 'content': json.dumps(final)}]}).encode()
    return [('percepcion', original), ('proyeccion', final), ('solicitud_preparada', final)], body


class Provenance07(unittest.TestCase):
    def test_large_metadata_survives_lossless_roundtrip(self):
        snapshots, body = fixture()
        before = deepcopy(snapshots)
        meta = provenance.build_metadata(snapshots, body, 'groq', 'deliberacion')
        raw = json.dumps(meta, ensure_ascii=False, separators=(',', ':')).encode()
        self.assertGreater(len(raw), 583425)
        stored = codec.encode_metadata(meta)
        self.assertLess(len(stored.encode()), 400000)
        self.assertEqual(codec.decode_metadata(stored), meta)
        self.assertEqual(meta['trace_status'], 'complete')
        self.assertEqual(snapshots, before)
        self.assertNotIn('PRIVATE_VALUE_NEVER_PERSIST', raw.decode())
        self.assertIn('oculto', meta['omitted_roots'])

    def test_over_field_budget_preserves_root_origins_and_changes(self):
        snapshots, body = fixture(2500)
        meta = provenance.build_metadata(snapshots, body, 'groq', 'deliberacion')
        self.assertEqual(meta['trace_status'], 'partial')
        self.assertEqual(meta['coverage']['max_depth'], 1)
        self.assertIn('/memorias_relevantes', meta['coverage']['unexpanded_paths'])
        self.assertIn('/oculto', meta['transitions'][0]['removed'])
        self.assertIn('/memorias_relevantes', meta['transitions'][0]['modified'])
        self.assertTrue(meta['origins']['necesidades']['references'])
        self.assertEqual(codec.decode_metadata(codec.encode_metadata(meta)), meta)

    def test_compressed_byte_budget_also_degrades_explicitly(self):
        snapshots, body = fixture()
        with patch.object(codec, 'MAX_STORED_BYTES', 2500):
            meta = provenance.build_metadata(snapshots, body, 'groq', 'deliberacion')
            self.assertEqual(meta['trace_status'], 'partial')
            self.assertIn('origins', meta)
            self.assertEqual(codec.decode_metadata(codec.encode_metadata(meta)), meta)

    def test_depth_limit_names_unexpanded_subtrees(self):
        original = {'raiz': {}}
        node = original['raiz']
        for _ in range(14):
            node['child'] = {}; node = node['child']
        body = json.dumps({'messages': [{'role': 'user', 'content': json.dumps(original)}]}).encode()
        meta = provenance.build_metadata([('solicitud_preparada', original)], body, 'groq', 'deliberacion')
        self.assertEqual(meta['trace_status'], 'partial')
        self.assertTrue(meta['coverage']['unexpanded_paths'])

    def test_mismatch_large_metadata_does_not_claim_presence(self):
        snapshots, _ = fixture()
        body = b'{"messages":[{"role":"user","content":"{}"}]}'
        meta = provenance.build_metadata(snapshots, body, 'groq', 'deliberacion')
        self.assertEqual(meta['payload_verification'], 'no_verificado_con_el_payload')
        self.assertTrue(all(f['in_http_payload'] is None for f in meta['fields']))

    def test_codec_rejects_tampering_truncation_trailing_and_oversize(self):
        snapshots, body = fixture()
        meta = provenance.build_metadata(snapshots, body, 'groq', 'deliberacion')
        original = json.loads(codec.encode_metadata(meta))
        for change in ('checksum', 'truncated', 'trailing', 'declared_small', 'declared_large', 'encoding'):
            with self.subTest(change=change):
                item = deepcopy(original)
                if change == 'checksum': item['sha256'] = '0' * 64
                if change == 'declared_small': item['decoded_bytes'] = 20
                if change == 'declared_large': item['decoded_bytes'] = codec.MAX_DECODED_BYTES + 1
                if change == 'encoding': item['storage_encoding'] = 'unknown'
                if change in ('truncated', 'trailing'):
                    data = base64.b64decode(item['data'])
                    item['data'] = base64.b64encode(data[:-3] if change == 'truncated' else data + b'extra').decode()
                with self.assertRaises(ValueError): codec.decode_metadata(json.dumps(item))
        bomb = dict(original, decoded_bytes=100, data=base64.b64encode(zlib.compress(b'x' * 1000000)).decode())
        with self.assertRaises(ValueError): codec.decode_metadata(json.dumps(bomb))

    def test_api_and_storage_read_compressed_legacy_partial_without_mutation(self):
        snapshots, body = fixture()
        meta = provenance.build_metadata(snapshots, body, 'groq', 'deliberacion')
        with tempfile.TemporaryDirectory() as temp:
            world = Path(temp) / 'world.sqlite3'
            store = RequestTraceStore.for_world(world)
            api = LocalLLMReadAPI(world)
            records = [meta, {'schema_version': 1, 'trace_status': 'excede_limite'},
                       provenance.build_metadata(*fixture(2500), 'groq', 'deliberacion')]
            ids = [store.begin(body=body, call_id='a'*32, session_id=1,
                               purpose='deliberacion', source_id=None, simulated_at=None,
                               ordinal=i+1, provider='groq', model='synthetic', provenance=m)
                   for i,m in enumerate(records)]
            # Force a true pre-upgrade JSON row, not a newly encoded envelope.
            with sqlite3.connect(store.path) as db:
                db.execute('update llm_request_provenance set metadata_json=? where attempt_id=?',
                           (json.dumps(records[1]), ids[1]))
            digest = hashlib.sha256(store.path.read_bytes()).hexdigest()
            for ident,m,status in zip(ids, records, ('available','partial','partial')):
                self.assertEqual(store.provenance_for(ident), m)
                entry = api.get_attempt('id='+ident)
                self.assertEqual(entry['provenance'], m)
                self.assertEqual(entry['provenance_status'], status)
                self.assertEqual(entry['body_utf8'].encode(), body)
                self.assertIsNone(entry['linked_record'])
                for message in entry['messages']:
                    self.assertEqual(''.join(s['literal'] for s in message['segments']), message['text'])
            self.assertEqual(hashlib.sha256(store.path.read_bytes()).hexdigest(), digest)
            self.assertFalse(world.exists())
            with sqlite3.connect(store.path) as db:
                item = json.loads(codec.encode_metadata(meta));item['sha256']='0'*64
                db.execute('update llm_request_provenance set metadata_json=? where attempt_id=?',
                           (json.dumps(item), ids[0]))
            with self.assertRaises(ReadError) as error: api.get_attempt('id='+ids[0])
            self.assertEqual(error.exception.status, 409)

    def test_transport_captures_large_metadata_without_network_or_body_changes(self):
        snapshots, body = fixture()
        with tempfile.TemporaryDirectory() as temp:
            store = RequestTraceStore.for_world(Path(temp)/'world.sqlite3')
            with capture_call(store, purpose='deliberacion'):
                for stage, value in snapshots: observe_context(stage, value)
                ident = transport_started(body, 'groq')
            self.assertIsNotNone(ident)
            self.assertEqual(store.recent()[0]['body'], body)
            self.assertEqual(store.provenance_for(ident)['trace_status'], 'complete')

    def test_metadata_failure_is_explicit_without_losing_literal_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            world = Path(temp)/'world.sqlite3'
            store = RequestTraceStore.for_world(world)
            _, body = fixture(2)
            with patch.object(provenance, 'build_metadata', side_effect=ValueError('SECRET')):
                with capture_call(store, purpose='deliberacion'):
                    ident = transport_started(body, 'groq')
            self.assertIsNotNone(ident)
            self.assertEqual(store.recent()[0]['body'], body)
            meta = store.provenance_for(ident)
            self.assertEqual(meta['trace_status'], 'unavailable')
            self.assertNotIn('SECRET', json.dumps(meta))
            self.assertEqual(LocalLLMReadAPI(world).get_attempt('id='+ident)['provenance_status'],
                             'unavailable')


if __name__ == '__main__': unittest.main()
