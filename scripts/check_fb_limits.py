"""Read-only NJ/NX POU parameter-count check (W501 sections 6-2-5/6-2-6).

Checks direct declared InputVars, OutputVars and InoutVars independently.
Array/structure members are not additional pins. This is not native compilation.
"""
import argparse
import json
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

NS='{www.iec.ch/public/TC65SC65BWG7TF10}'
GROUPS={'VAR_INPUT':'InputVars','VAR_OUTPUT':'OutputVars','VAR_IN_OUT':'InoutVars'}
LIMIT=64

def summarize(name,kind,groups):
    counts={g:len(groups.get(g,[])) for g in GROUPS}
    errors=[]
    for group,count in counts.items():
        if count>LIMIT:
            errors.append({'code':'POU_PARAMETER_LIMIT','pou':name,'kind':kind,'group':group,
                'count':count,'limit':LIMIT,'firstOverLimit':groups[group][LIMIT]})
    return {'name':name,'kind':kind,'counts':counts},errors

def check_xml(root):
    pous=[];errors=[]
    for kind in ('FunctionBlock','Function'):
        for node in root.iter(NS+kind):
            groups={g:[] for g in GROUPS}
            params=node.find(NS+'Parameters')
            if params is not None:
                for group,tag in GROUPS.items():
                    for section in params.findall(NS+tag):
                        groups[group].extend(v.get('name','') for v in section.findall(NS+'Variable'))
            info,bad=summarize(node.get('name',''),kind,groups);pous.append(info);errors.extend(bad)
    return pous,errors

def check_iec(text):
    # Parse declarations only, remove ST bodies/comments so examples, nested
    # STRUCT members, inactive code and unrelated names cannot inflate pins.
    text=re.sub(r'//\{st\}.*?//\{end\}', '',text,flags=re.S|re.I)
    text=re.sub(r"\(\*.*?\*\)|//[^\n]*|'(?:''|[^'])*'",' ',text,flags=re.S)
    pous=[];errors=[]
    for m in re.finditer(r'\b(FUNCTION_BLOCK|FUNCTION)\s+(\w+)\b(.*?)\bEND_(?:FUNCTION_BLOCK|FUNCTION)\b',text,re.S|re.I):
        groups={g:[] for g in GROUPS}
        for v in re.finditer(r'\b(VAR_INPUT|VAR_OUTPUT|VAR_IN_OUT)\b(?:\s+(?:RETAIN|NON_RETAIN|CONSTANT))?\s*(.*?)\bEND_VAR\b',m[3],re.S|re.I):
            group=v[1].upper()
            for line in v[2].split(';'):
                decl=re.match(r'\s*([\w\s,]+)\s*:',line)
                if decl:groups[group].extend(x.strip() for x in decl[1].split(',') if x.strip())
        info,bad=summarize(m[2],m[1].upper(),groups);pous.append(info);errors.extend(bad)
    return pous,errors

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths',nargs='+',type=Path)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args();files=[];errors=[]
    for path in args.paths:
        if path.suffix.lower()=='.xml':pous,bad=check_xml(ET.parse(path).getroot())
        elif path.suffix.lower() in ('.iec','.st'):pous,bad=check_iec(path.read_text(encoding='utf-8-sig'))
        else:raise SystemExit('Unsupported format: use IEC declaration file or IEC61131-10 XML')
        # Empty bodies/patches cannot certify limits for missing definitions.
        files.append({'path':str(path),'pous':pous,'definitionCount':len(pous)})
        errors.extend(dict(e,file=str(path)) for e in bad)
    report={'passed':not errors,'limitPerParameterGroup':64,'files':files,'errors':errors,
        'scope':'NJ/NX declared FB/FUN parameter groups; separate groups, no array expansion, aliases/library internals/native compilation not checked'}
    encoded=json.dumps(report,ensure_ascii=False,indent=2)
    if args.report:args.report.write_text(encoded,encoding='utf-8')
    print(encoded)
    return int(bool(errors))

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
