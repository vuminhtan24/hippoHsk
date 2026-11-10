"""Load project JSONL inputs; validate offline by default, index only with --index."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent


def project_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def load_records(folder: Path, names: list[str] | None = None) -> tuple[list[dict[str, Any]], int]:
    """Read only top-level JSONL. Merge identical text without losing source metadata."""
    if not folder.is_dir():
        raise ValueError(f"Input directory does not exist: {folder}")
    if names:
        for name in names:
            if Path(name).name != name or not name.endswith('.jsonl'):
                raise ValueError('--file must be a JSONL filename in the input directory.')
        files = [folder / name for name in dict.fromkeys(names)]
    else:
        files = sorted(folder.glob('*.jsonl'))
    if not files:
        raise ValueError('No top-level JSONL inputs found.')
    records: dict[str, dict[str, Any]] = {}
    source_count = 0
    for file in files:
        if not file.is_file():
            raise ValueError(f"Input file does not exist: {file.name}")
        with file.open(encoding='utf-8-sig') as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                location = f'{file.name}:{line_number}'
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    raise ValueError(f'{location}: invalid JSON.') from None
                if not isinstance(row, dict) or not isinstance(row.get('content'), str) or not row['content'].strip():
                    raise ValueError(f'{location}: content must be a non-empty string.')
                if not isinstance(row.get('metadata'), dict):
                    raise ValueError(f'{location}: metadata must be an object.')
                content = row['content']
                metadata = dict(row['metadata'])
                metadata.update(input_file=file.name, input_line=line_number)
                source_count += 1
                if content in records:
                    current = records[content]['metadata']
                    if 'source_records' not in current:
                        current['source_records'] = [dict(current)]
                    current['source_records'].append(metadata)
                else:
                    records[content] = {'content': content, 'metadata': metadata}
    if not records:
        raise ValueError('Inputs contain no passages.')
    return list(records.values()), source_count


def read_settings(env_path: Path) -> dict[str, str]:
    from dotenv import load_dotenv

    if not env_path.is_file():
        raise ValueError(f'Environment file not found: {env_path}')
    # Exported shell variables take precedence over .env; never print secret values.
    load_dotenv(env_path, override=False)
    names = [
        'LLM_MODEL_NAME', 'LLM_BASE_URL', 'LLM_API_KEY_ENV',
        'EMBEDDING_MODEL_NAME', 'EMBEDDING_PROVIDER', 'EMBEDDING_BASE_URL',
        'EMBEDDING_API_KEY_ENV', 'HIPPO_INPUT_DIR', 'HIPPO_SAVE_DIR',
    ]
    settings = {name: os.getenv(name, '').strip() for name in names}
    settings['LLM_API_KEY_ENV'] = settings['LLM_API_KEY_ENV'] or 'DEEPSEEK_API_KEY'
    settings['EMBEDDING_API_KEY_ENV'] = settings['EMBEDDING_API_KEY_ENV'] or 'EMBEDDING_API_KEY'
    settings['EMBEDDING_PROVIDER'] = settings['EMBEDDING_PROVIDER'] or 'openai'
    settings['HIPPO_INPUT_DIR'] = settings['HIPPO_INPUT_DIR'] or 'hipporag_input'
    settings['HIPPO_SAVE_DIR'] = settings['HIPPO_SAVE_DIR'] or 'outputs/hsk-deepseek'
    required = ['LLM_MODEL_NAME', 'LLM_BASE_URL', 'EMBEDDING_MODEL_NAME']
    if settings['EMBEDDING_PROVIDER'] == 'openai':
        required.append('EMBEDDING_BASE_URL')
    missing = [name for name in required if not settings[name]]
    for parameter in ['LLM_API_KEY_ENV', 'EMBEDDING_API_KEY_ENV']:
        if parameter.startswith('EMBEDDING') and settings['EMBEDDING_PROVIDER'] != 'openai':
            continue
        name = settings[parameter]
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
            raise ValueError(f'{parameter} must contain an environment variable name, not a key.')
        if not os.getenv(name, '').strip():
            missing.append(name)
    if missing:
        raise ValueError('Missing settings: ' + ', '.join(missing))
    return settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true', help='Validate locally without API calls (default).')
    mode.add_argument('--index', action='store_true', help='Call configured APIs and write the index; API charges can apply.')
    parser.add_argument('--env-file', default='.env')
    parser.add_argument('--input-dir', help='Override HIPPO_INPUT_DIR; relative paths use the project directory.')
    parser.add_argument('--file', action='append', help='Select a top-level JSONL filename; repeat to select several.')
    parser.add_argument('--limit', type=int, help='Index only the first N unique passages; validates all selected inputs first.')
    parser.add_argument('--save-dir', help='Override HIPPO_SAVE_DIR.')
    parser.add_argument('--workers', type=int, default=2, help='Concurrent OpenIE workers (default: 2).')
    parser.add_argument('--rebuild-graph', action='store_true', help='Explicitly rebuild graph state while reusing compatible embeddings and OpenIE results; use after an interrupted initial index.')
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive.')
    if args.workers < 1:
        parser.error('--workers must be positive.')
    settings = read_settings(project_path(args.env_file))
    records, source_count = load_records(project_path(args.input_dir or settings['HIPPO_INPUT_DIR']), args.file)
    selected = records[:args.limit] if args.limit else records
    save_dir = project_path(args.save_dir or settings['HIPPO_SAVE_DIR'])
    if args.limit and not args.save_dir:
        save_dir = save_dir.with_name(save_dir.name + f'_sample_{args.limit}')

    # Build config only: do not instantiate HippoRAG in the offline validation path.
    from hipporag import Chunk, HippoRAG
    from hipporag.utils.config_utils import BaseConfig
    from hipporag.utils.openai_utils import validate_openai_base_url

    validate_openai_base_url(settings['LLM_BASE_URL'], 'chat/completions', 'LLM_BASE_URL')
    if settings['EMBEDDING_PROVIDER'] == 'openai':
        validate_openai_base_url(settings['EMBEDDING_BASE_URL'], 'embeddings', 'EMBEDDING_BASE_URL')
    config = BaseConfig(
        save_dir=str(save_dir),
        llm_name=settings['LLM_MODEL_NAME'],
        llm_base_url=settings['LLM_BASE_URL'],
        llm_api_key_env=settings['LLM_API_KEY_ENV'],
        embedding_model_name=settings['EMBEDDING_MODEL_NAME'],
        embedding_provider=settings['EMBEDDING_PROVIDER'],
        embedding_base_url=settings['EMBEDDING_BASE_URL'] or None,
        embedding_api_key_env=settings['EMBEDDING_API_KEY_ENV'] if settings['EMBEDDING_PROVIDER'] == 'openai' else None,
        openie_max_workers=args.workers,
        force_index_from_scratch=args.rebuild_graph,
        llm_extra_body=(
            {'thinking': {'type': 'disabled'}}
            if urlparse(settings['LLM_BASE_URL']).hostname == 'api.deepseek.com'
            and settings['LLM_MODEL_NAME'] in {'deepseek-flash', 'deepseek-v4-flash', 'deepseek-v4-pro'}
            else None
        ),
    )
    print(f'Input: {source_count} records, {len(records)} unique passages; selected: {len(selected)}.')
    print(f'LLM: {config.llm_name}; embedding: {config.embedding_model_name}.')
    if config.llm_extra_body:
        print('DeepSeek thinking: disabled for extraction.')
    print(f'Index directory: {save_dir}')
    if not args.index:
        print('DRY RUN OK: no API requests, no model downloads, no index created. Keys and provider responses are not verified.')
        return 0
    docs = [Chunk(content=r['content'], metadata=r['metadata']) for r in selected]
    print('Indexing selected passages using configured models; this can incur API charges.', flush=True)
    with HippoRAG(global_config=config) as rag:
        rag.index(docs=docs)
    print(f'Indexing complete: {save_dir}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, ImportError, RuntimeError) as exc:
        message = str(exc)
        for name, value in os.environ.items():
            if ('KEY' in name or 'TOKEN' in name or 'SECRET' in name) and len(value) >= 8:
                message = message.replace(value, '[REDACTED]')
        print(f'Error: {message}', file=sys.stderr)
        if 'Graph state is missing while embedding stores are non-empty' in message:
            print('Recovery: rerun with --rebuild-graph to explicitly rebuild the missing graph and reuse saved embeddings.', file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        # Provider exceptions may contain credentials in their request details.
        print(f'Indexing failed ({type(exc).__name__}). Check model access, quota and endpoint compatibility. Rerun with the same configuration to reuse persisted work.', file=sys.stderr)
        raise SystemExit(1)
