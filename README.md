# Stan AI

Интерактивное приложение про стан для пластической деформации металла с ИИ-ассистентом.
Состоит из двух частей:

1. **Веб-приложение (FastAPI + uv)** — единая страница (`/`) с кнопкой-переключателем
   3D ⇄ AR, ИИ-чатом и озвучкой.
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
| `/` | 3D-просмотрщик + кнопка «📷 AR» для переключения в AR-режим на месте.
      Для AR распечатайте маркер `app/static/assets/pattern-Stan_pattern.png` |
| `/ar` | Редирект на `/` (AR встроен в главную страницу) |
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

1. 3D-сцена статична и работает всегда — камера ей не нужна.
2. Кнопка «📷 AR» → явная проверка `getUserMedia` (таймаут 15 сек).
3. Камера есть → подгружается `aframe-ar.js`, 3D-сцена ставится на паузу и
   скрывается, строится AR-сцена. Кнопка превращается в «🖥 3D» — обратное
   переключение останавливает видеопоток и возвращает 3D.
4. Камеры нет / доступ запрещён / нет https → тост «Камера недоступна»,
   остаёмся в 3D-режиме. Приложение не падает.
5. Выбранный режим запоминается в `localStorage`.

Структура фронтенда: `app/static/` — `js/common.js` (детали, подсветка, озвучка),
`js/chat.js` (чат), `js/app.js` (переключение 3D ⇄ AR, ленивая сборка AR-сцены).

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
