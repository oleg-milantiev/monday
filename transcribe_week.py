#!/usr/bin/env python3
"""Transcribe voice messages for a specific week and update the result file."""

import json
import os
import sys
import argparse
import requests


def transcribe_audio(audio_path: str, base_url: str, model: str, api_key: str):
    """Transcribe audio file using LiteLLM proxy."""
    url = f"{base_url.rstrip('/')}/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(audio_path, 'rb') as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/ogg")}
        data = {"model": model}
        response = requests.post(url, headers=headers, files=files, data=data, proxies={'http': None, 'https': None})

    if response.status_code == 200:
        return response.json().get('text', '')
    else:
        raise Exception(f"Transcription failed: {response.status_code} - {response.text}")


def process_week(week_num: int, year: int, weeks_dir: str, voice_dir: str, base_url: str, model: str, api_key: str):
    """Process voice messages for a specific week."""
    week_file = os.path.join(weeks_dir, f'result-{year}-{week_num:02d}.json')

    if not os.path.exists(week_file):
        print(f"Week file not found: {week_file}")
        return False

    with open(week_file) as f:
        data = json.load(f)

    messages = data['messages']
    voice_messages = [msg for msg in messages if msg.get('media_type') == 'voice_message']

    if not voice_messages:
        print(f"No voice messages in week {year}-W{week_num:02d}")
        return True

    print(f"Week {year}-W{week_num:02d}: {len(voice_messages)} voice message(s)")

    updated = False
    for msg in voice_messages:
        # Check if already has transcription
        if msg.get('transcription'):
            print(f"  ID {msg['id']}: already has transcription, skipping")
            continue

        voice_file = msg.get('file', '')
        if not voice_file:
            print(f"  ID {msg['id']}: no file path, skipping")
            continue

        filename = os.path.basename(voice_file)
        audio_path = os.path.join(voice_dir, filename)

        if not os.path.exists(audio_path):
            print(f"  ID {msg['id']}: audio file not found at {audio_path}, skipping")
            continue

        print(f"  Transcribing ID {msg['id']} ({filename})...")
        try:
            text = transcribe_audio(audio_path, base_url, model, api_key)
            msg['transcription'] = text
            updated = True
            print(f"    Done: {text[:80]}{'...' if len(text) > 80 else ''}")
        except Exception as e:
            print(f"    Error: {e}")

    if updated:
        # Write back to file
        with open(week_file, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Updated {week_file}")
    else:
        print(f"  No updates needed")

    return True


def main():
    parser = argparse.ArgumentParser(description='Transcribe voice messages for a specific week')
    parser.add_argument('--week', type=int, required=True, help='Week number (1-53)')
    parser.add_argument('--year', type=int, default=2026, help='Year (default: 2026)')
    parser.add_argument('--weeks-dir', default='weeks', help='Directory with weekly JSON files')
    parser.add_argument('--voice-dir', default='voice_messages', help='Directory with voice message .ogg files')
    parser.add_argument('--model', default='whisper-large-v3', help='Transcription model name')
    args = parser.parse_args()

    api_key = os.environ.get('LLM_API_KEY')
    if not api_key:
        print("Error: LLM_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get('LLM_BASE_URL')
    if not base_url:
        print("Error: LLM_BASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    process_week(args.week, args.year, args.weeks_dir, args.voice_dir, base_url, args.model, api_key)


if __name__ == '__main__':
    main()