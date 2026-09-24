"""Validate fixed binary field layouts; no third-party dependencies."""
import argparse
import json
from pathlib import Path

WIDTHS = {'BYTE': 1, 'USINT': 1, 'SINT': 1, 'UINT': 2, 'INT': 2,
          'UDINT': 4, 'DINT': 4, 'ULINT': 8, 'LINT': 8, 'REAL': 4,
          'LREAL': 8, 'STRING': 1}

def validate(packet, capacity=None):
    errors = []
    cursor = 0
    names = set()
    for field in packet['fields']:
        name = field['name']
        if name in names:
            errors.append(f'duplicate field {name}')
        names.add(name)
        count = int(field.get('count', 1))
        width = WIDTHS.get(field['type'])
        if count < 1 or width is None:
            errors.append(f'{name}: unsupported type/count')
            continue
        size = width * count
        if int(field['offset']) != cursor:
            errors.append(f'{name}: expected offset {cursor}, got {field["offset"]}')
        if int(field['bytes']) != size:
            errors.append(f'{name}: expected {size} bytes, got {field["bytes"]}')
        dimensions = field.get('dimensions')
        if dimensions:
            product = 1
            for dimension in dimensions:
                product *= int(dimension)
            if product != count:
                errors.append(f'{name}: dimensions do not match count')
        cursor = int(field['offset']) + size
    if cursor != int(packet['fixed_bytes']):
        errors.append(f'length: fields end at {cursor}, declared {packet["fixed_bytes"]}')
    if capacity is not None and int(packet['fixed_bytes']) > capacity:
        errors.append(f'transport capacity {capacity} < payload {packet["fixed_bytes"]}')
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract', type=Path)
    parser.add_argument('--capacity', type=int)
    args = parser.parse_args()
    data = json.loads(args.contract.read_text(encoding='utf-8'))
    packets = data if isinstance(data, list) else [data]
    failures = {p['topic']: validate(p, args.capacity) for p in packets}
    print(json.dumps(failures, ensure_ascii=True, indent=2))
    return int(any(failures.values()))

if __name__ == '__main__':
    raise SystemExit(main())
