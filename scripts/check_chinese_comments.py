"""Check readable Chinese IEC XML documentation style, not its correctness."""
import argparse
import json
import re
import xml.etree.ElementTree as E

N = '{www.iec.ch/public/TC65SC65BWG7TF10}'
HAN = re.compile('[\u3400-\u9fff]')


def style_errors(text):
    """Require useful sectioning, not a comment before every line of ST."""
    lines=text.splitlines()
    headings=[]
    chinese_comments=0
    inline_comments=0
    for number,line in enumerate(lines,1):
        stripped=line.strip()
        if stripped.startswith('//') and HAN.search(stripped):
            chinese_comments+=1
            if re.match(r'//\s*=====',stripped):
                headings.append(number)
                before_is_code = number > 1 and bool(lines[number-2].strip())
                after_is_code = number < len(lines) and bool(lines[number].strip())
                if before_is_code or after_is_code:
                    return ['SECTION_SPACING: ST line '+str(number)]
        # Ignore quoted ST literals before locating an end-of-line comment.
        unquoted = re.sub(r"'(?:\$[\s\S]|''|[^'])*'|\"(?:\$[\s\S]|\"\"|[^\"])*\"", "''", stripped)
        code, marker, comment = unquoted.partition('//')
        if marker and code.strip() and HAN.search(comment):
            inline_comments+=1
    errors=[]
    if not headings: errors.append('NO_CHINESE_SECTION_TITLE')
    if chinese_comments + inline_comments < 2: errors.append('TOO_FEW_CHINESE_ST_COMMENTS')
    if inline_comments == 0: errors.append('NO_INLINE_SIMPLE_STATEMENT_COMMENT')
    return errors


def validate(root):
    errors=[]
    for tag in ('Variable','Member'):
        for v in root.iter(N+tag):
            doc=v.find(N+'Documentation')
            if doc is None or not HAN.search(''.join(doc.itertext())):
                errors.append('NO_CHINESE_VARIABLE_COMMENT: '+str(v.get('name')))
    for st in root.iter(N+'ST'):
        errors.extend(style_errors(''.join(st.itertext())))
    return errors


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('xml');a=p.parse_args()
    errors=validate(E.parse(a.xml).getroot())
    print(json.dumps({'errors':errors,'note':'Readability style only; semantic/native review required'},ensure_ascii=False,indent=2))
    raise SystemExit(bool(errors))
