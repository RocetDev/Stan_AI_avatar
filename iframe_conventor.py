import html
import re

# 1. Читаем исходный HTML-файл (теперь all_in_one.html)
source_file = 'all_in_one.html'

try:
    with open(source_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
except FileNotFoundError:
    print(f"Ошибка: Исходный файл '{source_file}' не найден!")
    exit()

# 2. Функция для поиска тегов <script src="..."></script> и вшивания кода библиотек
def inline_scripts(match):
    src = match.group(1)
    try:
        with open(src, 'r', encoding='utf-8') as script_file:
            # Обертываем чистый код библиотеки в теги <script>
            return f'<script>\n{script_file.read()}\n</script>'
    except FileNotFoundError:
        print(f"Предупреждение: Локальный файл библиотеки '{src}' не найден!")
        return match.group(0)  # Если файл потерялся, оставляем тег как был

# Заменяем ссылки на файлы реальным JS-кодом внутри тегов
standalone_html = re.sub(r'<script\s+src="([^"]+)"></script>', inline_scripts, html_content)

# 3. ФАЙЛ 1: Создаем полностью автономное AR-приложение (все библиотеки внутри)
file_standalone = 'ar_app_standalone.html'
with open(file_standalone, 'w', encoding='utf-8') as f:
    f.write(standalone_html)
print(f"1. Создан автономный файл: '{file_standalone}'")

# 4. Экранируем полученный код для безопасной вставки в атрибут srcdoc
escaped_srcdoc = html.escape(standalone_html)

# Чистый тег iframe для копирования разработчиками
iframe_node = (
    f'<iframe allow="camera; microphone; autoplay" allowfullscreen \n'
    f'        style="width:100%;height:100vh;border:0;" \n'
    f'        srcdoc="{escaped_srcdoc}"></iframe>'
)

# 5. ФАЙЛ 3: Создаем сниппет (только тег iframe для быстрой вставки на сторонние сайты)
file_snippet = 'ar_iframe_snippet.html'
with open(file_snippet, 'w', encoding='utf-8') as f:
    f.write(iframe_node)
print(f"2. Создан сниппет для вставки на сайт: '{file_snippet}'")

# 6. ФАЙЛ 2: Создаем готовую страницу предпросмотра (iframe внутри правильного DOCTYPE)
preview_page = (
    f'<!DOCTYPE html>\n<html lang="ru">\n<head>\n'
    f'    <meta charset="UTF-8">\n'
    f'    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    f'    <title>AR Preview</title>\n'
    f'</head>\n<body style="margin:0;padding:0;overflow:hidden;">\n'
    f'    {iframe_node}\n'
    f'</body>\n</html>'
)

file_preview = 'ar_preview_page.html'
with open(file_preview, 'w', encoding='utf-8') as f:
    f.write(preview_page)
print(f"3. Создана страница предпросмотра: '{file_preview}'")

print("\nСборка успешно завершена! Все три файла готовы к использованию.")
