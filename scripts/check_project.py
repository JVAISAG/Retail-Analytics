"""Check the Git file set, documentation links and publication size."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    required = ['README.md', 'LICENSE', 'DATA_LICENSE.md', 'requirements.txt',
                '.gitignore', '.github/workflows/ci.yml', 'src/pipeline.py',
                'sql/01_build.sql', 'sql/02_analysis.sql', 'tests/test_pipeline.py',
                'scripts/run_tests.py', 'index.html', 'reports/FINDINGS.md']
    errors = [f'Missing required file: {p}' for p in required if not (ROOT/p).is_file()]
    result = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'], capture_output=True, check=False)
    if result.returncode:
        print('Git index unavailable; checking exported files instead.')
        files = [p for p in ROOT.rglob('*') if p.is_file()
                 and not any(x in p.parts for x in ['.git', '.venv', '__pycache__'])
                 and p.suffix not in ['.sqlite', '.pyc']
                 and not str(p.relative_to(ROOT)).replace('\\','/').startswith('data/raw/')
                 and p.name != 'ledger.csv.gz']
    else:
        files = [ROOT/p.decode('utf-8') for p in result.stdout.split(b'\0') if p]
        if not files:
            errors.append('Git index is empty; add the project files before checking publication readiness.')
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if p.stat().st_size >= 25*1024*1024:
            errors.append(f'File exceeds the 25 MiB publication budget: {rel}')
        if p.name == '.env' or p.name.startswith('.env.') and p.name != '.env.example':
            errors.append(f'Environment file must not be tracked: {rel}')
        if rel.startswith('data/raw/') or p.suffix == '.sqlite' or p.name == 'ledger.csv.gz':
            errors.append(f'Regenerated source or bulk export must not be tracked: {rel}')
    for doc in [ROOT/'README.md', ROOT/'docs/GITHUB.md']:
        if not doc.is_file():
            continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            if not (doc.parent/target.split('#',1)[0]).is_file():
                errors.append(f'Broken relative link in {doc.name}: {target}')
    payload = {'passed': not errors, 'checked_files': len(files),
               'largest_file_mib': round(max((p.stat().st_size for p in files), default=0)/1024/1024, 2),
               'errors': errors}
    print(json.dumps(payload, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
