# Stan AI

Интерактивное приложение про стан для пластической деформации металла с ИИ-ассистентом.
Состоит из двух частей:

1. **Веб-приложение (FastAPI + uv)** — 3D-просмотрщик с ИИ-чатом (`/`) и AR-режим (`/ar`).
2. **Сборка автономных/SCORM-экспортов** — 3D-версия без камеры для Moodle и офлайн-демо.

## 🚀 Веб-приложение (FastAPI + uv)

### Запуск

```bash
# 1. Установить зависимости (создаст .venv и uv.lock)
uv sync

# 2. Создать .env (по образцу .env.example) и вписать ключ OpenRouter
cp .env.example .env

# 3. Запустить
uv run uvicorn app.main:app --reload
```

Приложение: http://localhost:8000

| Роут | Описание |
|---|---|
| `/` | 3D-просмотрщик: вращение модели мышью/тачем, панель деталей, ИИ-чат, озвучка |
| `/ar` | AR-режим с маркером: печатайте маркер `app/static/assets/pattern-Stan_pattern.png` |
| `/api/chat` | POST — прокси к OpenRouter (ключ хранится только на сервере в `.env`) |
| `/api/health` | GET — статус и конфигурация LLM |
| `/docs` | Автодокументация API (Swagger UI) |

### 🔒 Безопасность

* Ключ OpenRouter хранится **только на сервере** (`.env`, в git не попадает).
  Клиент шлёт лишь текст вопроса — системный промпт и ключ живут в `app/services/llm.py` и `.env`.
* Старый `env.json` в корне больше не используется (его содержимое затёрто; в git он
  никогда не коммитился — был в `.gitignore` с самого начала).

### Устойчивость AR-режима к камере

В отличие от старой версии, AR-сцена инициализируется **лениво**:

1. Сначала явная проверка `getUserMedia` (с таймаутом 15 сек).
2. Камера есть → подгружаются `aframe.min.js` + `aframe-ar.js` и создаётся AR-сцена.
3. Камеры нет / доступ запрещён / нет https → экран «Камера недоступна»
   с кнопками «Перейти в 3D-режим» и «Повторить попытку». Приложение не падает.

Структура фронтенда: `app/static/` — `js/common.js` (детали, подсветка, озвучка),
`js/chat.js` (чат), `js/viewer.js` (3D-страница), `js/ar.js` (AR-страница с fallback).

## 🛠️ Сборка экспортов (SCORM для Moodle)

Исходник 3D-версии — `viewer.html` (модель в base64, **без AR.js и маркера** —
работает на любом ПК без камеры). Конвейер:

```bash
# 1. (опционально) Пересобрать viewer.html из AR-версии all_in_one.html
python tools/make_viewer.py

# 2. Автономные файлы: app_standalone.html, iframe_snippet.html, preview_page.html
python iframe_conventor.py

# 3. SCORM 1.2 пакет -> ar_course_scorm12.zip
python make_scorm.py
```

* **`ar_course_scorm12.zip`** — курс для Moodle/iSpring/WebTutor (SCORM 1.2,
  автостатус «completed» при открытии). Не требует камеры и интернета.
* **`app_standalone.html`** — автономная страница, можно открыть локально или на хостинге.
* **`iframe_snippet.html`** / **`preview_page.html`** — вставка сцены iframe'ом на сторонний сайт.

## 📁 Структура репозитория

```
app/                  # FastAPI-приложение (этап 2)
├── main.py           # роуты /, /ar, /api, mount static
├── api/              # chat.py, health.py
├── core/config.py    # настройки из .env (pydantic-settings)
├── schemas/chat.py   # pydantic-модели
├── services/llm.py   # клиент OpenRouter + системный промпт
└── static/           # фронтенд (js/css/vendor/assets)

viewer.html           # ИСХОДНИК 3D-версии для экспортов (без AR)
all_in_one.html       # AR-версия с маркером (для телефонов)
index.html            # legacy: исходная AR-страница с чатом (CDN + env.json)
models/, pattern-*    # исходные ассеты

iframe_conventor.py   # вшивание библиотек -> standalone/iframe/preview
make_scorm.py         # упаковка SCORM 1.2
tools/make_viewer.py  # (одноразово) генерация viewer.html из all_in_one.html
```
