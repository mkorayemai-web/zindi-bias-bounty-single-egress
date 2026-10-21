"""Regenerate/check the repository's sorted SHA-256 release manifest.

Usage: python egress/manifest.py --write
       python egress/manifest.py --check
Verify independently from the repository root: sha256sum -c MANIFEST.sha256
(or shasum -a 256 -c MANIFEST.sha256).

The original checkout contained the manifest but no generator. This codifies its
observed method/scope: SHA-256, two spaces, sorted repository-relative paths,
tracked non-hidden release files, excluding the manifest itself. Hidden metadata
(.gitignore, work/.gitkeep) were not in the original manifest and remain excluded.
Stage new release files before --write; ignored scratch/data files are never added.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'MANIFEST.sha256'


def release_paths():
    raw = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z'])
    paths = [p.decode() for p in raw.split(b'\0') if p]
    return sorted(p for p in paths if p != MANIFEST.name and not any(part.startswith('.') for part in Path(p).parts))


def content(paths):
    rows = []
    for name in paths:
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'missing/non-regular release file: {name}')
        h = hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                h.update(block)
        rows.append(f'{h.hexdigest()}  {name}\n')
    return ''.join(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--write', action='store_true')
    g.add_argument('--check', action='store_true')
    args = p.parse_args()
    paths = release_paths()
    expected = content(paths)
    if args.write:
        MANIFEST.write_text(expected)
        print(f'MANIFEST written: {len(paths)} SHA-256 entries; sorted tracked release files, original hidden-file exclusions retained')
        return 0
    ok = MANIFEST.read_text() == expected
    print(f'MANIFEST {"PASS" if ok else "FAIL"}: {len(paths)} entries; content AND coverage checked')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
