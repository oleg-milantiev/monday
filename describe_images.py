#!/usr/bin/env python3
"""Describe images for a specific week using qwen-vision model and update the result file."""

import json
import os
import sys
import argparse
import base64
import requests


def describe_image(image_path: str, base_url: str, model: str, api_key: str):
    """Describe image using LiteLLM proxy with vision model."""
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    mime_type = "image/jpeg"
    if image_path.lower().endswith('.png'):
        mime_type = "image/png"
    elif image_path.lower().endswith('.webp'):
        mime_type = "image/webp"

    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Опиши изображение в 2-4 предложениях на русском языке."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 800,
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=data, proxies={'http': None, 'https': None})

    if response.status_code == 200:
        result = response.json()
        choice = result.get('choices', [{}])[0]
        message = choice.get('message', {})
        content = message.get('content')
        reasoning = message.get('reasoning_content')

        if content:
            return content.strip()
        elif reasoning:
            # Model put description in reasoning_content instead of content
            return reasoning.strip()
        else:
            raise Exception(f"Empty content in response: {result}")
    else:
        raise Exception(f"Description failed: {response.status_code} - {response.text}")


def process_week(week_num: int, year: int, weeks_dir: str, photos_dir: str, base_url: str, model: str, api_key: str):
    """Process images for a specific week."""
    week_file = os.path.join(weeks_dir, f'result-{year}-{week_num:02d}.json')

    if not os.path.exists(week_file):
        print(f"Week file not found: {week_file}")
        return False

    with open(week_file) as f:
        data = json.load(f)

    messages = data['messages']
    image_messages = [msg for msg in messages if msg.get('photo')]

    if not image_messages:
        print(f"No images in week {year}-W{week_num:02d}")
        return True

    print(f"Week {year}-W{week_num:02d}: {len(image_messages)} image(s)")

    updated = False
    for msg in image_messages:
        if msg.get('image_description'):
            print(f"  ID {msg['id']}: already has description, skipping")
            continue

        image_file = msg.get('photo', '')
        if not image_file:
            print(f"  ID {msg['id']}: no file path, skipping")
            continue

        filename = os.path.basename(image_file)
        image_path = os.path.join(photos_dir, filename)

        if not os.path.exists(image_path):
            print(f"  ID {msg['id']}: image file not found at {image_path}, skipping")
            continue

        print(f"  Describing ID {msg['id']} ({filename})...")
        try:
            description = describe_image(image_path, base_url, model, api_key)
            msg['image_description'] = description
            updated = True
            print(f"    Done: {description[:80]}{'...' if len(description) > 80 else ''}")
        except Exception as e:
            print(f"    Error: {e}")

    if updated:
        with open(week_file, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Updated {week_file}")
    else:
        print(f"  No updates needed")

    return True


def main():
    parser = argparse.ArgumentParser(description='Describe images for a specific week using qwen-vision')
    parser.add_argument('--week', type=int, required=True, help='Week number (1-53)')
    parser.add_argument('--year', type=int, default=2026, help='Year (default: 2026)')
    parser.add_argument('--weeks-dir', default='weeks', help='Directory with weekly JSON files')
    parser.add_argument('--photos-dir', default='photos', help='Directory with photo files')
    parser.add_argument('--model', default='qwen-vision', help='Vision model name')
    args = parser.parse_args()

    api_key = os.environ.get('LLM_API_KEY')
    if not api_key:
        print("Error: LLM_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get('LLM_BASE_URL')
    if not base_url:
        print("Error: LLM_BASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    process_week(args.week, args.year, args.weeks_dir, args.photos_dir, base_url, args.model, api_key)


if __name__ == '__main__':
    main()