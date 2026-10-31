"""Regression test of the focused DT declaration checker."""
from io import BytesIO
from zipfile import ZipFile
from check_datetime_declarations import check

project = BytesIO()
with ZipFile(project, 'w') as archive:
    archive.writestr('vars.xml', '++D=ARRAY[0..63] OF DT\tN=bad\tG=VAR\n'
                     '++D=ARRAY[0..63] OF DATE_AND_TIME\tN=good\tG=VAR\n'
                     '++D=DATE_AND_TIME\tN=literal\tIV=DT#2020-1-1-0:0:0\n')
project.seek(0)
findings = check(project)
assert [item['variable'] for item in findings] == ['bad'], findings
print('DT declaration regression passed; valid DATE_AND_TIME and DT# literal accepted')
