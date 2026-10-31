"""Find suspicious DT type declarations in readable ZIP-style Sysmac projects.

DT#... is a date-time literal and is deliberately ignored. The check recognizes
native variable-table records only; it is not a Sysmac compiler.
"""
import argparse
import json
import re
import zipfile
from pathlib import Path

TYPE_FIELD = re.compile(r'^\+\+D=([^\t\r\n]+)\tN=([^\t\r\n]+)', re.I | re.M)
BAD_DT = re.compile(r'(?:^|\bOF\s+)DT\s*$', re.I)


def check(path):
    findings = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith('.xml'):
                continue
            text = archive.read(info).decode('utf-8-sig', errors='replace')
            for match in TYPE_FIELD.finditer(text):
                if BAD_DT.search(match.group(1)):
                    findings.append({'member': info.filename, 'variable': match.group(2),
                                     'declared_type': match.group(1)})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    args = parser.parse_args()
    try:
        findings = check(args.project)
    except (OSError, zipfile.BadZipFile) as exc:
        parser.exit(2, f'Cannot inspect project: {exc}\n')
    print(json.dumps({'findings': findings, 'scope': 'Known DT declaration pattern only; not native compilation'}, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
