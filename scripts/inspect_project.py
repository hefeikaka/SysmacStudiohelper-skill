"""Bounded, read-only inventory of ZIP-based Sysmac files, not a full parser."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

def inspect(path, max_bytes=64*1024*1024, max_total=256*1024*1024):
    path = Path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    report = {'sha256': digest, 'source_name': path.name, 'format': 'unsupported',
              'entities': [], 'xml_inventory': [], 'limitations': [
                  'No binary deserialization, decryption, complete ladder topology or native save',
                  'Entity attributes and source paths are clues; resolve associations before reuse']}
    if not zipfile.is_zipfile(path):
        return report
    report['format'] = 'zip'; total = 0
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > 20000:
            raise ValueError('Too many archive members')
        report['member_count'] = len(infos)
        for info in infos:
            if not info.filename.lower().endswith(('.xml', '.oem', '.manifest', '.manifest2')):
                continue
            row = {'member': info.filename, 'bytes': info.file_size}
            report['xml_inventory'].append(row)
            if info.file_size > max_bytes or total + info.file_size > max_total:
                row['status'] = 'skipped_size_limit'; continue
            with archive.open(info) as stream:
                data = stream.read(min(max_bytes, max_total-total)+1)
            total += len(data)
            if len(data) > max_bytes or total > max_total:
                row['status'] = 'skipped_size_limit'; continue
            # ElementTree does not fetch external entities; reject DTDs as well.
            probe = data.replace(b'\x00', b'').upper()
            if b'<!DOCTYPE' in probe or b'<!ENTITY' in probe:
                row['status'] = 'skipped_dtd'; continue
            try:
                root = ET.fromstring(data)
            except ET.ParseError:
                row['status'] = 'not_parseable_xml'; continue
            tags = [e.tag.split('}')[-1] for e in root.iter()]
            row.update(status='parsed_xml', root=root.tag, protected='EncryptedFile' in tags,
                       inline_st=tags.count('InlineStructuredTextModel'),
                       ladder=tags.count('LadderDiagram'))
            def walk(node, parents):
                current = parents
                if node.tag.split('}')[-1] == 'Entity':
                    report['entities'].append({'source': info.filename,
                        'attributes': dict(node.attrib), 'ancestor_entities': parents})
                    current = parents + [dict(node.attrib)]
                for child in node:
                    walk(child, current)
            walk(root, [])
    return report

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('project', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.project.resolve() == a.output.resolve():
        p.error('Output must not overwrite source project')
    a.output.write_text(json.dumps(inspect(a.project), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
