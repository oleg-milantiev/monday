# ПоНедельник

Набор скриптов для обработки экспорта Telegram-чатов. Разделяет `result.json` на еженедельные файлы, транскрибирует голосовые сообщения через Whisper, описывает фотографии через Qwen-Vision и генерирует тематические саммаризации по неделям.

Разработан в Kilo Code 7.8.8 + Qwen3.5-35B-A3B-AWQ на A100.

[Пример саммаризации (неделя 2026-16)](summaries/summary-2026-16.md)

## Структура

```
ПоНедельник/
├── result.json              # Экспорт Telegram-чата
├── split_weeks.py           # Разделение на недели
├── split.sh                 # Shell-обёртка для сплита
├── transcribe_week.py       # Транскрипция голосовых (Whisper)
├── describe_images.py       # Описание фото (Qwen-Vision)
├── summary.py               # Тематическая саммаризация (Qwen-Coder)
├── week.sh                  # Обработка одной недели целиком
├── models.py                # Список доступных моделей через LiteLLM
├── .env.dist                # Пример .env
├── weeks/                   # Еженедельные result-файлы
├── voice_messages/          # Скачанные голосовые (.ogg)
├── photos/                  # Скачанные фото
└── summaries/               # Сгенерированные саммаризации (.md)
```

## Установка

1. Скопируйте шаблон `.env`:

```bash
cp .env.dist .env
```

2. Заполните `.env`:

```bash
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://your-litellm-proxy.url"
```

3. Положите экспорт Telegram-чата (`result.json`) в корень проекта.
4. Извлеките медиафайлы из чата: все `.ogg` в `voice_messages/`, все фото в `photos/`
   (это автоматически делает экспорт в Telegram с включёнными вложениями).

## Использование

### 1. Разделение на недели

Разбивает `result.json` на файлы `weeks/result-YYYY-WW.json`:

```bash
./split.sh
# или
python3 split_weeks.py [--input result.json] [--output-dir weeks]
```

### 2. Полная обработка недели

Запускает транскрипцию голосовых, описание фото и генерацию саммаризации для указанной недели:

```bash
./week.sh <номер_недели> [--year 2026]
```

### 3. Транскрипция голосовых

```bash
python3 transcribe_week.py --week 33 [--year 2026] [--model whisper-large-v3]
```

Обновляет поле `transcription` в `weeks/result-YYYY-WW.json`.
Если оно уже заполнено, пропускает расшифровку этого голосового.

### 4. Описание фотографий

```bash
python3 describe_images.py --week 33 [--year 2026] [--model qwen-vision]
```

Обновляет поле `image_description` в `weeks/result-YYYY-WW.json`.
Если оно уже заполнено, пропускает описание фото.

### 5. Тематическая саммаризация

```bash
python3 summary.py --week 33 [--year 2026] [--model qwen-coder]
```

Создаёт `summaries/summary-YYYY-WW.md` — связный документ, сгруппированный по 3-10 смысловым темам.

### 6. Проверка доступных моделей

```bash
python3 models.py
```

## Формат выходных данных

### weeks/result-YYYY-WW.json

```json
{
  "name": "имя_чата",
  "type": "chat",
  "id": 123,
  "messages": [
    {
      "id": 42,
      "date": "2026-08-15T14:30:00",
      "from": "user",
      "text": "привет",
      "media_type": "voice_message",
      "file": "voice_messages/audio_1.ogg",
      "transcription": "текст расшифровки"
    },
    {
      "id": 43,
      "date": "2026-08-15T15:00:00",
      "from": "user",
      "media_type": "photo",
      "photo": "photos/photo_1.jpg",
      "image_description": "описание фото"
    }
  ]
}
```

### summaries/summary-YYYY-WW.md

Markdown-файл с тематической сводкой по неделям:

```markdown
# Неделя 2026-33

## Тема 1
Связный текст по теме с хронологией событий...

## Тема 2
...

![описание](photos/photo_1.jpg)
```

## Зависимости

- Python 3.8+
- Библиотеки: `requests`
- LiteLLM proxy-сервер (бэкенд для Whisper и LLM)

## Установка зависимостей

```bash
pip install requests
```

## Workflow

1. `split.sh` — разделить `result.json` на недели
2. `week.sh N` — обработать неделю N целиком (голосовые + фото + саммаризация)
3. Повторять для каждой недели или пропускать уже обработанные

Скрипты пропускают файлы, для которых уже есть результат (транскрипция, описание, саммаризация), так что запуск безопасен многократно.

## Примечания

- Голосовые и фото нужно скачать из экспорта Telegram вручную в соответствующие директории
- Имена аудиофайлов должны совпадать с путями в `result.json`
- Промпт для описания фото требует описания на русском языке в 2-4 предложениях
- Саммаризация использует `max_tokens=15000` — для больших недель может потребоваться увеличение
