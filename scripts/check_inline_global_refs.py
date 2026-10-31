"""Check known global names used in inline ST against a program's variable table.

Scope: readable ZIP Sysmac projects with XML entity trees and JSON ladder rows.
This is a targeted static check, not a Sysmac parser or compiler.
"""
import argparse,json,re,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path

def declarations(text):
    result={}
    for line in text.splitlines():
        if not line.startswith('++D='):continue
        fields=dict(x.split('=',1) for x in line[2:].split('\t') if '=' in x)
        if 'N' in fields and 'D' in fields:
            result[fields['N'].casefold()] = fields
    return result

def records(text):
    decoder=json.JSONDecoder();pos=0
    while pos<len(text):
        if text[pos].isspace():pos+=1;continue
        obj,pos=decoder.raw_decode(text,pos);yield obj

def check(project,program_name,restrict=None):
    with zipfile.ZipFile(project) as z:
        oem=next(n for n in z.namelist() if n.endswith('.oem'));prefix=oem.rsplit('/',1)[0]+'/'
        root=ET.fromstring(z.read(oem))
        global_vars={}
        for e in root.iter('Entity'):
            if e.get('type')=='Variables' and e.get('subtype')=='Global':
                name=prefix+e.get('id')+'.xml'
                if name in z.namelist():global_vars.update(declarations(z.read(name).decode('utf-8-sig')))
        programs=[e for e in root.iter('Entity') if e.get('type')=='Program' and e.get('name')==program_name]
        if len(programs)!=1:raise ValueError('Expected exactly one matching program')
        program=programs[0]
        var=next(e for e in program.iter('Entity') if e.get('type')=='Variables')
        local=declarations(z.read(prefix+var.get('id')+'.xml').decode('utf-8-sig'))
        sources=[]
        for body in program.iter('Entity'):
            if body.get('type')!='PouBody':continue
            path=prefix+body.get('id')+'.xml'
            if path not in z.namelist():continue
            try: rows=list(records(z.read(path).decode('utf-8-sig')))
            except (UnicodeDecodeError,json.JSONDecodeError):continue
            for row in rows:
                sources.extend(c.get('TXT','') for c in row.get('CLs',[]) if c.get('__type')=='IST')
        if not sources:raise ValueError('No readable inline ST found')
        text='\n'.join(sources)
        text=re.sub(r"\(\*.*?\*\)|//[^\n]*|'(?:''|[^'])*'",' ',text,flags=re.S)
        tokens={m.group(1).casefold() for m in re.finditer(r'(?<![\w.])([\w]+)',text,flags=re.UNICODE)}
        names=sorted(tokens & global_vars.keys())
        if restrict is not None:names=[n for n in names if n in restrict]
        issues=[]
        for name in names:
            glob=global_vars[name];decl=local.get(name)
            if decl is None:
                issues.append({'name':glob['N'],'reason':'global used in inline ST without program declaration'})
            elif decl.get('G')=='VAR_EXTERNAL' and decl['D'].casefold()!=glob['D'].casefold():
                issues.append({'name':glob['N'],'reason':'external/global types differ','external':decl['D'],'global':glob['D']})
        return {'program':program_name,'checked_global_names':[global_vars[n]['N'] for n in names],
                'issues':issues,'scope':'Inline ST token check only; may include false positives, does not validate library, ladder, shadowing or Sysmac compilation.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('project',type=Path);p.add_argument('--program',required=True)
    p.add_argument('--names',nargs='*',help='Optional known global variable names to check')
    a=p.parse_args()
    try: result=check(a.project,a.program,{n.casefold() for n in a.names} if a.names is not None else None)
    except (OSError,StopIteration,ValueError,zipfile.BadZipFile,ET.ParseError) as exc:
        p.exit(2,'Cannot inspect project: '+str(exc)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return int(bool(result['issues']))

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
