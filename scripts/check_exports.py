"""Read-only targeted checks for Sysmac exports. Python standard library only.

Not an IEC/ST compiler, CAEX XSD validator, or native Sysmac simulator.
"""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET

NS = {'p': 'www.iec.ch/public/TC65SC65BWG7TF10'}
ORDER = {name: index for index, name in enumerate([
    'Description', 'Version', 'Revision', 'Copyright', 'AdditionalInformation',
    'Attribute', 'ExternalInterface', 'InternalElement', 'SupportedRoleClass',
    'InternalLink', 'RoleRequirements', 'MappingObject',
])}

def result(errors, warnings=None):
    return {'passed': not errors, 'errors': errors, 'warnings': warnings or [],
            'scope': 'Targeted static checks only; NOT native import/compile/simulation or full XSD validation'}

def check_aml(root):
    errors = []
    if root.tag != 'CAEXFile' or root.get('SchemaVersion') != '2.15':
        return result(['Only namespace-free CAEX 2.15 is supported by this checker'])
    ids = set()
    for elem in root.iter():
        ident = elem.get('ID')
        if ident:
            if ident in ids:
                errors.append('Duplicate ID: ' + ident)
            ids.add(ident)
    for parent in root.iter('InternalElement'):
        prev = -1
        for child in parent:
            rank = ORDER.get(child.tag)
            if rank is None:
                errors.append(f"{parent.get('Name')}: unsupported child {child.tag}")
                continue
            if rank < prev:
                errors.append(f"{parent.get('Name')}: invalid child order at {child.tag}")
            prev = max(prev, rank)
    endpoints = {parent.get('ID') + ':' + child.get('Name')
                 for parent in root.iter() if parent.get('ID')
                 for child in parent.findall('ExternalInterface') if child.get('Name')}
    for link in root.iter('InternalLink'):
        for attr in ['RefPartnerSideA', 'RefPartnerSideB']:
            if link.get(attr) not in endpoints:
                errors.append(f"{link.get('Name')}: unresolved {attr}={link.get(attr)}")
    return result(errors)

def check_axis(root, pulse_velocity_limit=None):
    errors, warnings = [], []
    axes = root.findall('./Data/AxisSettings/AxisSetting')
    if root.tag != 'AxisSettings' or not axes:
        return result(['Expected a supported AxisSettings file containing axes'])
    limit = Decimal(str(pulse_velocity_limit)) if pulse_velocity_limit is not None else None
    if limit is not None and (not limit.is_finite() or limit <= 0):
        return result(['pulse_velocity_limit must be finite and positive'])
    for axis in axes:
        def value(name):
            node = axis.find('.//' + name)
            if node is None or node.get('CurrentValue') is None:
                raise ValueError('Missing ' + name)
            return node.get('CurrentValue')
        def number(name):
            n = Decimal(value(name))
            if not n.is_finite():
                raise ValueError('Non-finite ' + name)
            return n
        try:
            name = value('NexAxisName')
            if value('NexAxisReducerUse') != 'NotUse':
                errors.append(f'{name}: reducer conversion requires a separate verified calculation')
                continue
            numerator = number('NexAxisUnitsNumerator')
            denominator = number('NexAxisUnitsDenominator')
            if numerator <= 0 or denominator <= 0:
                raise ValueError('Unit conversion numerator/denominator must be positive')
            ratio = numerator / denominator
            vmax = number('NexAxisMaxVelocity')
            start = number('NexAxisStartVelocity')
            jog = number('NexAxisMaxJogVelocity')
            if vmax <= 0 or not (0 <= start <= vmax and 0 <= jog <= vmax):
                errors.append(f'{name}: invalid start/jog/maximum velocity relationship')
            if number('NexAxisMaxAcceleration') < 0 or number('NexAxisMaxDeceleration') < 0:
                errors.append(f'{name}: negative acceleration/deceleration limit')
            if limit is None:
                warnings.append(f'{name}: pulse velocity range NOT checked; provide the target-specific limit')
            elif vmax * ratio > limit:
                errors.append(f'{name}: maximum velocity converts to {vmax * ratio} pulse/s > {limit}')
        except (ValueError, InvalidOperation) as exc:
            errors.append(str(exc))
    return result(errors, warnings)

def check_bindings(root, contract):
    """Contract is a verified target snapshot, NOT metadata inferred from this XML.

    programs: {POU: {required_external_name: {type, constant, at}}}
    at is required for a required axis reference; bool constant must be explicit.
    """
    errors = []
    programs = contract.get('programs', {})
    if not programs:
        return result(['Contract must contain at least one program and required axis reference'])
    for program_name, expected_vars in programs.items():
        matches = [p for p in root.findall('.//p:Program', NS) if p.get('name') == program_name]
        if len(matches) != 1:
            errors.append(f'{program_name}: expected exactly one Program, found {len(matches)}')
            continue
        declarations = {}
        for group in matches[0].findall('p:ExternalVars', NS):
            flag = group.get('constant', 'false')
            if flag not in ('true', 'false', '1', '0'):
                errors.append(f'{program_name}: invalid constant attribute {flag}')
            for var in group.findall('p:Variable', NS):
                name = var.get('name')
                if name in declarations:
                    errors.append(f'{program_name}: duplicate external {name}')
                declarations[name] = (var.findtext('p:Type/p:TypeName', namespaces=NS), flag in ('true', '1'))
        if not expected_vars:
            errors.append(f'{program_name}: no required references in contract')
        for name, expected in expected_vars.items():
            prefix = f'{program_name}.{name}'
            if not expected.get('type') or type(expected.get('constant')) is not bool or not expected.get('at'):
                errors.append(f'{prefix}: target contract needs type, boolean constant and confirmed axis AT binding')
                continue
            actual = declarations.get(name)
            if actual is None:
                errors.append(f'{prefix}: required external declaration missing')
            elif actual != (expected['type'], expected['constant']):
                errors.append(f"{prefix}: external type/constant {actual} does not match target {(expected['type'], expected['constant'])}")
    return result(errors, ['Target AT bindings come from the supplied contract; this tool does not inspect a running Sysmac project'])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['aml', 'axis', 'bindings'])
    parser.add_argument('xml', type=Path)
    parser.add_argument('--contract', type=Path)
    parser.add_argument('--pulse-velocity-limit', type=Decimal)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.mode == 'bindings' and not args.contract:
        parser.error('bindings requires --contract with verified target axis metadata')
    try:
        root = ET.parse(args.xml).getroot()
        if args.mode == 'aml':
            report = check_aml(root)
        elif args.mode == 'axis':
            report = check_axis(root, args.pulse_velocity_limit)
        else:
            report = check_bindings(root, json.loads(args.contract.read_text(encoding='utf-8')))
    except (OSError, ET.ParseError, ValueError, TypeError, AttributeError) as exc:
        report = result([str(exc)])
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.write_text(text + '\n', encoding='utf-8')
    print(text)
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
