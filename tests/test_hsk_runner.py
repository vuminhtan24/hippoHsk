import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('hsk_runner', Path(__file__).resolve().parents[1] / 'run_hsk.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerTests(unittest.TestCase):
    def test_ignores_review_and_merges_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / '_review').mkdir()
            (folder / '_review' / 'bad.jsonl').write_text('invalid', encoding='utf-8')
            rows = [{'content': 'same text', 'metadata': {'document': name}} for name in ['one.pdf', 'two.pdf']]
            (folder / 'one.jsonl').write_text('\n'.join(json.dumps(row) for row in rows), encoding='utf-8')
            records, count = runner.load_records(folder)
            self.assertEqual((count, len(records)), (2, 1))
            self.assertEqual([s['document'] for s in records[0]['metadata']['source_records']], ['one.pdf', 'two.pdf'])

    def test_reports_invalid_json_without_echoing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'bad.jsonl').write_text('private invalid payload', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, r'bad.jsonl:1: invalid JSON\.'):
                runner.load_records(folder)

    def test_rejects_bad_metadata_and_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'one.jsonl').write_text('{"content":"text","metadata":[]}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'metadata must be an object'):
                runner.load_records(folder)
            with self.assertRaisesRegex(ValueError, 'JSONL filename'):
                runner.load_records(folder, ['../other.jsonl'])

    def test_deepseek_thinking_is_disabled_only_for_supported_official_models(self):
        import hipporag
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'one.jsonl').write_text('{"content":"text","metadata":{}}', encoding='utf-8')
            for endpoint, model, expected in [
                ('https://api.deepseek.com', 'deepseek-flash', {'thinking': {'type': 'disabled'}}),
                ('https://api.deepseek.com/v1', 'deepseek-v4-pro', {'thinking': {'type': 'disabled'}}),
                ('https://api.openai.com/v1', 'gpt-offline', None),
                ('https://api.deepseek.com', 'deepseek-reasoner', None),
            ]:
                with self.subTest(endpoint=endpoint, model=model):
                    settings = {
                        'LLM_MODEL_NAME': model, 'LLM_BASE_URL': endpoint,
                        'LLM_API_KEY_ENV': 'TEST_LLM_KEY', 'EMBEDDING_MODEL_NAME': 'BAAI/bge-m3',
                        'EMBEDDING_PROVIDER': 'transformers', 'EMBEDDING_BASE_URL': '',
                        'EMBEDDING_API_KEY_ENV': '', 'HIPPO_INPUT_DIR': str(folder),
                        'HIPPO_SAVE_DIR': str(folder / 'index'),
                    }
                    with patch.object(runner, 'read_settings', return_value=settings), patch.object(hipporag, 'HippoRAG') as constructor:
                        self.assertEqual(runner.main(['--index', '--limit', '1', '--rebuild-graph']), 0)
                        self.assertEqual(constructor.call_args.kwargs['global_config'].llm_extra_body, expected)
                        self.assertTrue(constructor.call_args.kwargs['global_config'].force_index_from_scratch)
                        constructor.return_value.__enter__.return_value.index.assert_called_once()

    def test_default_mode_never_initializes_paid_clients_or_index(self):
        import hipporag
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / 'one.jsonl').write_text('{"content":"text","metadata":{}}', encoding='utf-8')
            settings = {
                'LLM_MODEL_NAME': 'test-model', 'LLM_BASE_URL': 'http://localhost:8000/v1',
                'LLM_API_KEY_ENV': 'TEST_LLM_KEY', 'EMBEDDING_MODEL_NAME': 'test-embedding',
                'EMBEDDING_PROVIDER': 'openai', 'EMBEDDING_BASE_URL': 'http://localhost:8001/v1',
                'EMBEDDING_API_KEY_ENV': 'TEST_EMBED_KEY', 'HIPPO_INPUT_DIR': str(folder),
                'HIPPO_SAVE_DIR': str(folder / 'index'),
            }
            with patch.object(runner, 'read_settings', return_value=settings), patch.object(hipporag, 'HippoRAG') as constructor:
                self.assertEqual(runner.main([]), 0)
                constructor.assert_not_called()
            self.assertFalse((folder / 'index').exists())


if __name__ == '__main__':
    unittest.main()
