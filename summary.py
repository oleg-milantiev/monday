#!/usr/bin/env python3
"""Generate weekly summary markdown from messages using qwen-coder."""

import json
import os
import sys
import argparse
import requests


def build_prompt(data: dict, week_num: int, year: int) -> str:
    """Build prompt from weekly messages."""
    messages = data.get('messages', [])

    prompt_parts = [
        "Ты — ассистент, создающий еженедельную тематическую сводку (summary) по личному дневнику/чату.",
        f"Входные данные — сообщения за неделю {year}-W{week_num:02d} в хронологическом порядке.",
        "Твоя задача: проанализировать все сообщения и написать связный документ на русском языке,",
        "сгруппировав материалы по 3-10 смысловым темам (не по дням!).",
        "",
        "Требования к выводу:",
        "1. Формат: Markdown (.md)",
        "2. Заголовок: `# Неделя YYYY-WW` (используй переданные year и week_num)",
        "3. Структура: 3-10 разделов с заголовками ## Тема, раскрывающими суть темы",
        "4. Голоса (voice_message) — равнозначны тексту, используй их транскрипции (поле transcription)",
        "5. Фото — вставляй ссылки вида `![описание](photos/file.ext)` по смыслу, согласно image_description",
        "6. Сохраняй живой стиль, интонацию, детали, эмоции. Не делай сухой отчёт.",
        "7. Внутри темы сохраняй хронологию событий",
        "8. Объединяй связанные сообщения в единое повествование по теме",
        "",
        "Примеры тем (адаптируй под содержимое):",
        "- Поиск работы / собеседования / этическая дилемма",
        "- Война / дроны / экологические катастрофы",
        "- Собственный проект / платёжные шлюзы / юр. вопросы",
        "- Железо / Raspberry Pi / ремонт / электроника",
        "- Здоровье / антидепрессанты / настроение",
        "- Личное / семья / рыбалка / отдых",
        "- Политика / прогнозы / социальные процессы",
        "",
        "---",
        "СООБЩЕНИЯ:",
        ""
    ]

    for msg in messages:
        msg_id = msg.get('id')
        date = msg.get('date', '')
        from_name = msg.get('from', '')
        text = msg.get('text', '')

        # Format date nicely
        date_short = date[:10] if date else ''

        prompt_parts.append(f"### Сообщение {msg_id} ({date_short})")
        prompt_parts.append(f"Автор: {from_name}")

        # Handle text (can be string or array of entities)
        if isinstance(text, list):
            text_parts = []
            for ent in text:
                if isinstance(ent, str):
                    text_parts.append(ent)
                elif isinstance(ent, dict) and ent.get('text'):
                    text_parts.append(ent['text'])
            text = ''.join(text_parts)

        if text and text.strip():
            prompt_parts.append(f"Текст: {text.strip()}")

        # Photo with description
        if msg.get('photo') and msg.get('image_description'):
            photo_path = msg['photo']
            desc = msg['image_description']
            prompt_parts.append(f"Фото: {photo_path}")
            prompt_parts.append(f"Описание фото: {desc}")
            prompt_parts.append(f"[Вставь в итоговый markdown: ![]({photo_path})]")

        # Voice message with transcription
        if msg.get('media_type') == 'voice_message' and msg.get('transcription'):
            voice_file = msg.get('file', '')
            transcription = msg['transcription']
            prompt_parts.append(f"Голосовое: {voice_file}")
            prompt_parts.append(f"Транскрипция: {transcription}")

        prompt_parts.append("")

    prompt_parts.append("---")
    prompt_parts.append(f"СОЗДАЙ MARKDOWN СВОДКУ НЕДЕЛИ {year}-W{week_num:02d} ПО ТЕМАМ:")

    return '\n'.join(prompt_parts)


def generate_summary(prompt: str, base_url: str, model: str, api_key: str) -> str:
    """Generate summary using LiteLLM proxy."""
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Ты пишешь живые, детальные тематические еженедельные сводки из личного чата. Группируй по 3-10 темам (не по дням!). Сохраняй интонацию, детали, эмоции. Используй markdown. Вставляй фото по смыслу. Заголовок: # Неделя YYYY-WW. Разделы: ## Тема."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 15000,
        "temperature": 0.4
    }

    response = requests.post(url, headers=headers, json=data, proxies={'http': None, 'https': None}, timeout=300)

    if response.status_code == 200:
        result = response.json()
        content = result.get('choices', [{}])[0].get('message', {}).get('content')
        if content:
            return content.strip()
        else:
            reasoning = result.get('choices', [{}])[0].get('message', {}).get('reasoning_content')
            if reasoning:
                return reasoning.strip()
            raise Exception(f"Empty content in response: {result}")
    else:
        raise Exception(f"Generation failed: {response.status_code} - {response.text}")


def process_week(week_num: int, year: int, weeks_dir: str, output_dir: str, base_url: str, model: str, api_key: str):
    """Process week and generate summary."""
    week_file = os.path.join(weeks_dir, f'result-{year}-{week_num:02d}.json')

    if not os.path.exists(week_file):
        print(f"Week file not found: {week_file}")
        return False

    with open(week_file) as f:
        data = json.load(f)

    print(f"Loaded week {year}-W{week_num:02d}: {len(data.get('messages', []))} messages")

    prompt = build_prompt(data, week_num, year)
    print(f"Prompt length: ~{len(prompt)//1000}k chars")

    print("Generating summary...")
    try:
        summary = generate_summary(prompt, base_url, model, api_key)
    except Exception as e:
        print(f"Error: {e}")
        return False

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'summary-{year}-{week_num:02d}.md')

    with open(output_file, 'w') as f:
        f.write(summary)

    print(f"Summary saved to {output_file}")
    print(f"Length: {len(summary)} chars")

    return True


def main():
    parser = argparse.ArgumentParser(description='Generate weekly summary markdown using qwen-coder')
    parser.add_argument('--week', type=int, required=True, help='Week number (1-53)')
    parser.add_argument('--year', type=int, default=2026, help='Year (default: 2026)')
    parser.add_argument('--weeks-dir', default='weeks', help='Directory with weekly JSON files')
    parser.add_argument('--output-dir', default='summaries', help='Output directory for markdown files')
    parser.add_argument('--model', default='qwen-coder', help='Model name (200k context)')
    args = parser.parse_args()

    api_key = os.environ.get('LLM_API_KEY')
    if not api_key:
        print("Error: LLM_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    base_url = os.environ.get('LLM_BASE_URL')
    if not base_url:
        print("Error: LLM_BASE_URL environment variable not set", file=sys.stderr)
        sys.exit(1)

    process_week(args.week, args.year, args.weeks_dir, args.output_dir, base_url, args.model, api_key)


if __name__ == '__main__':
    main()