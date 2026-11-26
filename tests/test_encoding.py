from pathlib import Path

TEXT_SUFFIXES={'.md','.py','.js','.html','.css','.yml','.yaml','.txt'}
MOJIBAKE=('Ã','Â','ðŸ','â€','â€“','â†','âœ','â','ï¸','�')

def test_repository_text_is_utf8_without_known_mojibake():
    problems=[]
    for path in Path('.').rglob('*'):
        if not path.is_file() or '.git' in path.parts or path.resolve() == Path(__file__).resolve():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {'.env.example','.gitignore','.dockerignore','Dockerfile'}:
            continue
        try:
            text=path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            problems.append(f'{path}: not UTF-8')
            continue
        hits=[token for token in MOJIBAKE if token in text]
        if hits:
            problems.append(f'{path}: {hits}')
    assert not problems, '\n'.join(problems)
