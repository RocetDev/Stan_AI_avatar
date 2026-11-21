# Stan AI

Интерактивное приложение про стан для пластической деформации металла с ИИ-ассистентом.

## Структура

```
app/                          # Веб-приложение (FastAPI + uv)
├── main.py                   # Точка входа: роуты, статика, no-cache для статики
├── api/chat.py               # POST /api/chat — прокси к OpenRouter
├── api/health.py             # GET /api/health
├── core/config.py            # Настройки из .env (pydantic-settings)
├── schemas/chat.py           # Pydantic-модели запроса/ответа
├── services/llm.py           # HTTP-клиент OpenRouter, system prompt, парсинг {parts, text}
└── static/
    ├── index.html            # Единая страница: 3D-сцена + кнопка «📷 AR»
    ├── js/app.js             # Переключение 3D ⇄ AR, ленивая инициализация AR-сцены
    ├── js/common.js          # Панель деталей, подсветка модели, озвучка, toast
    ├── js/chat.js            # ИИ-чат (история в localStorage, голосовой ввод)
    ├── css/style.css
    ├── vendor/               # aframe.min.js, aframe-extras.min.js, aframe-ar.js
    └── assets/               # StanNew.glb, паттерн маркера

tools/
└── build_scorm.py            # Сборка автономного SCORM 1.2 из app/static

docs/marker-Stan_pattern.png  # Распечатать для AR-режима
```

## Запуск веб-приложения

```bash
uv sync                 # установка зависимостей
cp .env.example .env    # и вписать ключ OpenRouter в OPENROUTER_API_KEY
uv run uvicorn app.main:app --reload
```

Приложение: http://localhost:8000

- **3D-режим** — работает всегда, камера не нужна.
- **AR-режим** — кнопка «📷 AR»: сначала проверяется доступ к камере; если камера
  недоступна, показывается тост и приложение остаётся в 3D. Для AR распечатайте
  `docs/marker-Stan_pattern.png`.
- API-ключ хранится только на сервере (`.env`), клиент его не видит.

## Сборка SCORM для Moodle

```bash
python tools/build_scorm.py
```

Создаёт `stan_course_scorm12.zip` — автономный 3D-просмотрщик (модель вшита в base64,
камера не нужна): панель деталей, подсветка, озвучка + SCORM-коннектор
(LMSInitialize → lesson_status=completed → LMSFinish). Архив загружается в Moodle
как SCORM 1.2 курс.

## ИИ-ассистент

Модель задаётся в `.env` (`MODEL_NAME`, по умолчанию `nvidia/nemotron-3.5-lightning:free`).
Ассистент отвечает строгим JSON `{"parts": [...], "text": "..."}`: `parts` — имена
мешей для подсветки на 3D-модели, `text` — текст ответа (озвучивается через TTS).
Бесплатные модели OpenRouter имеют rate-limit — при упоре в лимит смените `MODEL_NAME`.
