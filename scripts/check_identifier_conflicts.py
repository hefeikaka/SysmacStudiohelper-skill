"""Check known instruction and referenced-library namespace name collisions.

This is a bounded regression check, not a complete Sysmac symbol resolver.
"""
import argparse
import json
import xml.etree.ElementTree as E

N='{www.iec.ch/public/TC65SC65BWG7TF10}'
KNOWN_INSTRUCTIONS={'limit'}

def validate(root, namespaces=()):
    reserved={n.casefold() for n in namespaces}
    for t in root.iter(N+'TypeName'):
        parts=(t.text or '').lstrip('\\').split('\\')
        if len(parts)>1:
            reserved.add(parts[0].casefold())
    errors=[]
    # InterfaceVariable and Member are declarations too. ExternalVars may legally
    # reference an existing vendor system variable; that is not a new user name.
    external_ids={id(v) for g in root.iter(N+'ExternalVars') for v in g}
    for v in root.iter():
        if v.tag not in {N+x for x in ['Variable','InterfaceVariable','Member','Program','FunctionBlock','Function','DataTypeDecl','Enumerator','Task','Namespace']}:
            continue
        name=v.get('name','')
        if id(v) not in external_ids and name.casefold().startswith('p_'):
            errors.append('RESERVED_SYSTEM_PREFIX: '+name)
        if name.casefold() in reserved:
            errors.append('NAMESPACE_NAME_CONFLICT: '+name)
        if name.casefold() in KNOWN_INSTRUCTIONS:
            errors.append('INSTRUCTION_NAME_CONFLICT: '+name)
    return sorted(set(errors))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('xml');p.add_argument('--namespace',action='append',default=[])
    a=p.parse_args();errors=validate(E.parse(a.xml).getroot(),a.namespace)
    print(json.dumps({'errors':errors,'scope':'user P_ prefix; known LIMIT instruction; supplied/inferred library namespaces; not a complete compiler'},ensure_ascii=False,indent=2))
    raise SystemExit(bool(errors))
