"""Conservative checks for unqualified FB types in IEC 61131-10 XML.

Checks delivered FB declarations and direct variable types; alias/namespace
resolution and vendor library interfaces require separate native validation.
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET

NS = '{www.iec.ch/public/TC65SC65BWG7TF10}'


def validate(root):
    blocks = {b.get('name').casefold(): b for b in root.iter(NS+'FunctionBlock')}
    errors = []

    def fb_type(v):
        typ = v.find(NS+'Type')
        if typ is not None:
            for t in typ.iter(NS+'TypeName'):
                if (t.text or '').casefold() in blocks:
                    return blocks[t.text.casefold()]
        return None

    for group in root.iter(NS+'GlobalVars'):
        for v in group.findall(NS+'Variable'):
            if fb_type(v) is not None:
                errors.append('GLOBAL_FB: '+v.get('name'))
    for pou in list(root.iter(NS+'Program')) + list(root.iter(NS+'FunctionBlock')):
        text = '\n'.join(''.join(st.itertext()) for st in pou.iter(NS+'ST'))
        # Do not flag examples in comments or strings.
        text = re.sub(r"\(\*.*?\*\)|//[^\n]*|'(?:''|[^'])*'", ' ', text, flags=re.S)
        for group_name in ('Vars', 'ExternalVars'):
            for group in pou.findall(NS+group_name):
                for v in group.findall(NS+'Variable'):
                    fb = fb_type(v)
                    if fb is None:
                        continue
                    for output in fb.findall('.//'+NS+'OutputVars/'+NS+'Variable'):
                        pattern = (r'\b'+re.escape(v.get('name'))+r'\s*(?:\[[^\]\n]+\]\s*)?'
                                   r'\.\s*'+re.escape(output.get('name'))+r'\s*[.\[]')
                        if re.search(pattern, text, re.I):
                            errors.append('FB_COMPOSITE_OUTPUT: '+pou.get('name')+'.'+v.get('name')+'.'+output.get('name'))
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('xml')
    args = parser.parse_args()
    errors = validate(ET.parse(args.xml).getroot())
    print(json.dumps({'errors': errors, 'scope': 'declared FB types; no alias/library resolution'}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))
