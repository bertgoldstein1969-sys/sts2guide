#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = root / 'data'

FILES = ['cards','relics','characters','keywords','builds']
REQUIRED = [
    'id','name','type','tags','shortSummary','howToUse','synergies','countersOrRisks',
    'unlockOrAvailability','updatedAt','sources','tier','synergyTags','winRateEstimate',
    'difficulty','actScaling','bestWith','worstWith'
]


def load(name):
    p = data / f'{name}.json'
    return json.loads(p.read_text()) if p.exists() else []


def fail(msg):
    print('VALIDATION_ERROR:', msg)
    sys.exit(1)


def main():
    all_ids = set()
    all_items = []

    for f in FILES:
        arr = load(f)
        if not arr:
            fail(f'{f}.json is empty')
        for item in arr:
            for k in REQUIRED:
                if k not in item:
                    fail(f'{f}: missing {k} in {item.get("id")}')
            if item['id'] in all_ids:
                fail(f'duplicate slug/id: {item["id"]}')
            all_ids.add(item['id'])
            all_items.append((f, item))

    # reference checks
    for f, item in all_items:
        for ref in item.get('synergies', []):
            if ref not in all_ids:
                fail(f'{f}:{item["id"]} broken synergy ref -> {ref}')
        for ref in item.get('bestWith', []):
            if ref not in all_ids:
                fail(f'{f}:{item["id"]} broken bestWith ref -> {ref}')
        for ref in item.get('worstWith', []):
            if ref not in all_ids:
                fail(f'{f}:{item["id"]} broken worstWith ref -> {ref}')

    print('VALIDATION_OK', len(all_ids))


if __name__ == '__main__':
    main()
