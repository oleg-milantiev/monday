#!/usr/bin/env python3
"""Get list of available models from LiteLLM proxy."""

import os
import sys
import argparse
import requests


def get_models(base_url: str, api_key: str):
    """Fetch available models from LiteLLM proxy."""
    url = f"{base_url.rstrip('/')}/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url, headers=headers, proxies={'http': None, 'https': None})

    if response.status_code == 200:
        data = response.json()
        return data.get('data', [])
    else:
        raise Exception(f"Failed to get models: {response.status_code} - {response.text}")


def main():
    parser = argparse.ArgumentParser(description='List available models from LiteLLM proxy')
    args = parser.parse_args()

    api_key = os.environ.get('LLM_API_KEY')
    if not api_key:
        print("Error: LLM_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get('LLM_BASE_URL')
    if not base_url:
        print("Error: LLM_BASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        models = get_models(base_url, api_key)
        if models:
            print(f"Available models ({len(models)}):")
            for m in models:
                print(f"  - {m.get('id', 'unknown')}")
        else:
            print("No models available")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()