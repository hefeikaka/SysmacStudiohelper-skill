"""Expand already-interpreted device lists. This is not a free-text NLP parser."""
import argparse
import copy
import json
from pathlib import Path

DEFAULTS = {
    'cylinder': {'valve': 'dual_coil', 'positions': ['Home', 'Work'],
        'inputs': ['HomeSensor', 'WorkSensor'], 'outputs': ['HomeValve', 'WorkValve'],
        'commands': ['CmdHome', 'CmdWork'], 'permits': ['PermitHome', 'PermitWork'],
        'status': ['AtHome', 'AtWork', 'Busy', 'Fault', 'FaultID'],
        'process_steps_owner': 'program_section', 'physical_mapping': None},
    'belt': {'inputs': ['DestinationSensor'], 'outputs': ['Run'],
        'arrival_policy': 'stop_and_request_next_action_same_scan',
        'wait_sensor_clear_before_next_action': False, 'stop_delay': None,
        'process_steps_owner': 'program_section', 'physical_mapping': None},
}

def expand(data):
    devices, names = [], set()
    for item in data['devices']:
        name, kind = item['name'], item['kind']
        if not isinstance(name, str) or not name or name in names:
            raise ValueError('Device names must be nonempty and unique')
        names.add(name)
        if kind not in DEFAULTS:
            raise ValueError('Unsupported default profile: ' + kind)
        values = copy.deepcopy(DEFAULTS[kind])
        overrides = item.get('overrides', {})
        unknown = set(overrides) - set(values)
        if unknown:
            raise ValueError('Unknown overrides: ' + ', '.join(sorted(unknown)))
        values.update(overrides)
        if kind == 'cylinder' and values['valve'] != 'dual_coil':
            if not all(k in overrides for k in ['inputs', 'outputs']):
                raise ValueError('Non-default valve needs explicit input/output interfaces')
        devices.append({'name': name, 'kind': kind, **values,
                        'default_source': 'user-authorized engineering convention',
                        'explicit_overrides': overrides})
    return {'devices': devices, 'note': 'Design assumptions; not detected physical hardware'}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path); p.add_argument('output', type=Path)
    args = p.parse_args()
    args.output.write_text(json.dumps(expand(json.loads(args.input.read_text(encoding='utf-8'))), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
