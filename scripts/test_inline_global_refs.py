"""Regression checks for inline global reference checker."""
from io import BytesIO
from zipfile import ZipFile
import json
from check_inline_global_refs import check

def make(local,source):
    result=BytesIO()
    oem='''<Entity type="Solution" id="s"><Entity type="Variables" subtype="Global" id="g"/>
    <Entity type="Program" name="Collect" id="p"><Entity type="Variables" id="v"/>
    <Entity type="PouBody" id="b"/></Entity></Entity>'''
    with ZipFile(result,'w') as z:
        z.writestr('s/s.oem',oem)
        z.writestr('s/g.xml','++D=BOOL\tN=Ready\tG=VAR_GLOBAL\n++D=UINT\tN=Count\tG=VAR_GLOBAL\n')
        z.writestr('s/v.xml',local)
        z.writestr('s/b.xml',json.dumps({'CLs':[{'__type':'IST','TXT':source}]}))
    result.seek(0)
    return result

source='IF Ready THEN Count := UINT#1; END_IF; // missing var in comment: Hidden'
bad=check(make('++D=UINT\tN=Count\tG=VAR_EXTERNAL\n',source),'Collect')
assert [x['name'] for x in bad['issues']]==['Ready'],bad
good=check(make('++D=UINT\tN=Count\tG=VAR_EXTERNAL\n++D=BOOL\tN=Ready\tG=VAR_EXTERNAL\n',source),'Collect')
assert not good['issues'],good
wrong=check(make('++D=UINT\tN=Count\tG=VAR_EXTERNAL\n++D=UINT\tN=Ready\tG=VAR_EXTERNAL\n',source),'Collect')
assert wrong['issues'][0]['reason']=='external/global types differ',wrong
print('inline global reference regression passed')
