#!/usr/bin/env python3
"""Split result.json into weekly files (Monday-Sunday)."""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import argparse


def split_weeks(input_file: str, output_dir: str):
    with open(input_file) as f:
        data = json.load(f)

    messages = data['messages']
    weeks = defaultdict(list)

    for msg in messages:
        if 'date' not in msg:
            continue
        dt = datetime.fromisoformat(msg['date'])
        year, week_num, _ = dt.isocalendar()
        week_key = f"{year}-W{week_num:02d}"
        weeks[week_key].append(msg)

    os.makedirs(output_dir, exist_ok=True)

    for week_key, msgs in sorted(weeks.items()):
        year, week_num = week_key.split('-W')
        week_num = int(week_num)

        week_data = {
            "name": data.get("name", ""),
            "type": data.get("type", ""),
            "id": data.get("id", 0),
            "messages": msgs
        }

        filename = os.path.join(output_dir, f'result-{year}-{week_num:02d}.json')
        if os.path.exists(filename):
            print(f'WARNING: {filename} already exists, skipping')
        else:
            with open(filename, 'w') as f:
                json.dump(week_data, f, ensure_ascii=False, indent=2)

            print(f'{filename}: {len(msgs)} messages')

    print(f'\nTotal weeks: {len(weeks)}')


def main():
    parser = argparse.ArgumentParser(description='Split result.json by weeks')
    parser.add_argument('--input', default='result.json', help='Input JSON file')
    parser.add_argument('--output-dir', default='weeks', help='Output directory')
    args = parser.parse_args()

    split_weeks(args.input, args.output_dir)


if __name__ == '__main__':
    main()