# AGENTS.md — PoPonedel'nik Project Guidelines

## Project Overview

PoPonedel'nik (ПоНедельник) is a toolkit for processing Telegram chat exports. It splits `result.json` into weekly files, transcribes voice messages via Whisper, describes images via Qwen-Vision, and generates thematic weekly summaries via Qwen-Coder.

Developed with Kilo Code 7.8.8 + Qwen3.5-35B-A3B-AWQ on A100.

## Repository Layout

```
result.json              # Telegram chat export (input)
split_weeks.py           # Split result.json into weekly chunks
split.sh                 # Shell wrapper for split_weeks.py
transcribe_week.py       # Whisper transcription of voice messages
describe_images.py       # Qwen-Vision image description
summary.py               # Qwen-Coder thematic weekly summaries
week.sh                  # All-in-one: transcribe + describe + summarize a week
models.py                # Query available models via LiteLLM proxy
.env.dist                # Environment variable template
.env                     # Your local config (gitignored)

weeks/                   # Weekly JSON files: result-YYYY-WW.json
voice_messages/          # Downloaded voice messages (.ogg)
photos/                  # Downloaded photos (.jpg, .png, .webp)
summaries/               # Generated markdown: summary-YYYY-WW.md
```

## Environment Variables

All scripts source `.env` (via `./week.sh` and `./split.sh`) or read directly. Required:

```bash
export LLM_API_KEY="your-key"
export LLM_BASE_URL="https://your-litellm-proxy.example"
```

## Data Model

### Input: `result.json` (Telegram chat export)

Each message has: `id`, `date`, `from`, `text`, `media_type`, `file`, `photo`, etc.

### Output: `weeks/result-YYYY-WW.json`

```json
{
  "name": "chat_name",
  "type": "chat",
  "id": 123,
  "messages": [
    {
      "id": 42,
      "date": "2026-08-15T14:30:00",
      "from": "user",
      "text": "hello",
      "media_type": "voice_message",
      "file": "voice_messages/audio_1.ogg",
      "transcription": "transcribed text"
    },
    {
      "id": 43,
      "date": "2026-08-15T15:00:00",
      "photo": "photos/photo_1.jpg",
      "image_description": "description of the image"
    }
  ]
}
```

### Output: `summaries/summary-YYYY-WW.md`

Markdown document grouped into 3-10 thematic sections, written in Russian, preserving conversational tone and chronology within themes.

## Workflow

1. **Split**: `./split.sh` — split `result.json` into `weeks/result-YYYY-WW.json`
2. **Process each week**: `./week.sh N [--year YYYY]` — runs all three LLM tasks
3. **Or run individually**:
   - `python3 transcribe_week.py --week N [--year YYYY]`
   - `python3 describe_images.py --week N [--year YYYY]`
   - `python3 summary.py --week N [--year YYYY]`

Scripts are idempotent: they skip messages that already have `transcription`, `image_description`, or existing summary files.

## LLM Endpoints

All LLM calls go through a LiteLLM proxy. Models and their default names:

| Task | Model | API Endpoint |
|------|-------|-------------|
| Voice transcription | `whisper-large-v3` | `/v1/audio/transcriptions` |
| Image description | `qwen-vision` | `/v1/chat/completions` |
| Weekly summary | `qwen-coder` | `/v1/chat/completions` |

Override with `--model` flag on individual scripts.

## Coding Conventions

- Python 3.8+, no external deps beyond `requests` and stdlib
- All scripts are `#!/usr/bin/env python3` with `argparse` CLI
- Use `ensure_ascii=False, indent=2` for JSON output
- All prompts inside scripts are in Russian (Llama output language)
- `.env` is gitignored; `.env.dist` is the template
- Media files must be manually downloaded and placed in `voice_messages/` or `photos/`
- Filenames in `result.json` must match actual files in those directories

## Common Agent Tasks

### "Process all weeks"

1. Run `./split.sh` if not already done
2. Check `ls weeks/` to see which week files exist
3. Run `for w in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41; do ./week.sh $w; done` (adjust range)
4. Check `ls summaries/` for generated markdown files

### "Fix a broken week"

1. Inspect `weeks/result-YYYY-WW.json` for missing fields
2. Check if `voice_messages/` and `photos/` have the required files
3. Run the specific script again: `python3 transcribe_week.py --week N` (will skip already-transcribed messages)

### "Edit a prompt"

Prompts live inside the Python scripts:
- Image prompt: `describe_images.py` line ~35 — "Опиши изображение в 2-4 предложениях на русском языке."
- Summary prompt: `summary.py` lines 15-89 — the full `build_prompt` function
- System prompt: `summary.py` line 104 — system message for qwen-coder

### "Add a new LLM task"

1. Create a new Python script following the pattern of existing ones
2. Use `argparse` with `--week`, `--year`, `--model` args
3. Source `.env` for `LLM_API_KEY` and `LLM_BASE_URL`
4. Call the LiteLLM proxy endpoint
5. Add to `week.sh` if it should run as part of the weekly pipeline

## Safety Notes

- Never commit `.env` or actual API keys
- Voice messages and photos are not in git (`.gitkeep` + `gitignore`)
- The proxy URL and API key are user-provided; do not hardcode
- All LLM calls use `proxies={'http': None, 'https': None}` to avoid system proxy interference
- `summary.py` has `timeout=300` for long generation windows
