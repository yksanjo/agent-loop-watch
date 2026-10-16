"""Offline repeated-suffix detector for synthetic or locally captured agent traces."""
import argparse
import hashlib
import json

MAX_BYTES = 1048576
MAX_RECORDS = 1000


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def inspect(records, repeats=3, max_period=8):
    if type(repeats) is not int or not 2 <= repeats <= 20:
        raise ValueError('repeats must be 2..20')
    if type(max_period) is not int or not 1 <= max_period <= 32:
        raise ValueError('max_period must be 1..32')
    if type(records) is not list or len(records) > MAX_RECORDS:
        raise ValueError('expected at most 1000 records')
    fingerprints = []
    for record in records:
        if (type(record) is not dict or set(record) != {'tool', 'arguments', 'result'}
                or type(record['tool']) is not str or not record['tool'].strip()
                or type(record['arguments']) is not dict):
            raise ValueError('each record needs tool, arguments object and result')
        fingerprints.append(hashlib.sha256(canonical(record).encode()).hexdigest())
    for period in range(1, min(max_period, len(records) // repeats) + 1):
        pattern = fingerprints[-period:]
        if all(fingerprints[-period * (n + 1):len(records) - period * n] == pattern
               for n in range(repeats)):
            count = repeats
            while (count + 1) * period <= len(records):
                start = len(records) - (count + 1) * period
                if fingerprints[start:start + period] != pattern:
                    break
                count += 1
            return {'review_required': True, 'reason': 'repeated_suffix',
                    'period': period, 'repetitions': count,
                    'start_index': len(records) - count * period,
                    'end_index_exclusive': len(records),
                    'pattern_sha256': pattern}
    return {'review_required': False, 'reason': 'no_repeated_suffix',
            'records_checked': len(records)}


def load(path):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError('duplicate JSON key')
            obj[key] = value
        return obj
    with open(path, 'rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('trace exceeds 1 MiB')
    obj = json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    # Bound nesting before canonical serialization. Parser recursion is handled by CLI.
    pending = [(obj, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > 64:
            raise ValueError('nesting exceeds 64')
        if isinstance(value, dict):
            pending.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list):
            pending.extend((v, depth + 1) for v in value)
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--max-period', type=int, default=8)
    args = parser.parse_args()
    try:
        result = inspect(load(args.trace), args.repeats, args.max_period)
    except (OSError, ValueError, TypeError, RecursionError):
        print(json.dumps({'review_required': True, 'error': 'invalid or unreadable trace'}))
        return 2
    print(json.dumps(result, indent=2))
    return 1 if result['review_required'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
