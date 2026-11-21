"""
Сборка SCORM 1.2 пакета для Moodle из исходников веб-приложения (app/static).

Что делает:
  1. Берёт app/static/index.html и вырезает из него всё, что требует сервера:
     чат (ui-container, chat.js), переключатель AR-режима (mode-toggle-btn, app.js).
     Остаётся автономный 3D-просмотрщик: модель, панель деталей, подсветка, TTS.
  2. Инлайнит библиотеки (aframe, aframe-extras), CSS и common.js.
  3. Вшивает 3D-модель как base64 data-URI.
  4. Добавляет SCORM API-коннектор (LMSInitialize / lesson_status=completed / LMSFinish).
  5. Упаковывает в SCORM 1.2 zip вместе с imsmanifest.xml.

Запуск из корня репозитория:  python tools/build_scorm.py
Результат:                    stan_course_scorm12.zip
"""
import base64
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "app" / "static"
OUTPUT = ROOT / "stan_course_scorm12.zip"

COURSE_ID = "Stan_3D_Avatar_Course"
COURSE_TITLE = "3D-модель прокатного стана с ассистентом"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def cut_block(html: str, start_marker: str, end_marker: str) -> str:
    """Удаляет блок от start_marker до end_marker включительно."""
    i = html.find(start_marker)
    assert i != -1, f"NOT FOUND: {start_marker[:60]!r}"
    j = html.find(end_marker, i)
    assert j != -1, f"NOT FOUND end: {end_marker[:60]!r}"
    return html[:i] + html[j + len(end_marker):]


def drop_line_containing(html: str, marker: str) -> str:
    lines = html.splitlines(keepends=True)
    lines = [ln for ln in lines if marker not in ln]
    assert len(lines) < html.count("\n") + 1, f"NOT FOUND: {marker[:60]!r}"
    return "".join(lines)


def main() -> None:
    html = read(STATIC / "index.html")

    # --- 1. Вырезаем всё, что требует сервера / камеры ---
    html = drop_line_containing(html, "toggle-chat-btn")
    html = drop_line_containing(html, "mode-toggle-btn")
    html = cut_block(html, '<div id="ui-container">',
                     "(см. js/app.js). -->")
    html = drop_line_containing(html, "js/chat.js")
    html = drop_line_containing(html, "js/app.js")
    html = html.replace("<title>Ассистент Стана</title>", f"<title>{COURSE_TITLE}</title>")

    # --- 2. Инлайним CSS и библиотеки ---
    css = read(STATIC / "css" / "style.css")
    html = re.sub(r'<link rel="stylesheet"[^>]*>',
                  lambda _: f"<style>\n{css}\n</style>", html)
    for src in ("aframe.min.js", "aframe-extras.min.js"):
        js = read(STATIC / "vendor" / src)
        html = re.sub(rf'<script src="[^"]*{src}[^"]*"></script>',
                      lambda _m, js=js: f"<script>\n{js}\n</script>", html)
    js = read(STATIC / "js" / "common.js")
    html = re.sub(r'<script src="[^"]*js/common\.js[^"]*"></script>',
                  lambda _: f"<script>\n{js}\n</script>", html)

    # --- 3. Вшиваем 3D-модель как base64 ---
    glb_b64 = base64.b64encode((STATIC / "assets" / "StanNew.glb").read_bytes()).decode()
    html = re.sub(r'src="/static/assets/StanNew\.glb"',
                  f'src="data:model/gltf-binary;base64,{glb_b64}"', html)

    # --- 4. Инициализация просмотрщика (chat.js/app.js вырезаны) ---
    html = html.replace("</body>", """<script>
    document.addEventListener('DOMContentLoaded', function () {
        StanApp.initCommon();
        StanApp.initModelListeners();
    });
</script>
</body>""")

    # --- 5. SCORM API-коннектор ---
    scorm_injector = """<script>
    // Коннектор к API LMS (SCORM 1.2)
    var lmsAPI = null;

    function findAPI(win) {
        var tries = 0;
        while ((win.API == null) && (win.parent != null) && (win.parent != win)) {
            tries++;
            if (tries > 10) return null;
            win = win.parent;
        }
        return win.API;
    }

    window.addEventListener('load', function () {
        lmsAPI = findAPI(window);
        if (!lmsAPI && window.opener) lmsAPI = findAPI(window.opener);
        if (lmsAPI) {
            lmsAPI.LMSInitialize("");
            lmsAPI.LMSSetValue("cmi.core.lesson_status", "completed");
            lmsAPI.LMSCommit("");
            console.log("SCORM: статус 'completed' отправлен в LMS.");
        } else {
            console.log("SCORM: запущено локально (LMS API не обнаружено).");
        }
    });

    window.addEventListener('unload', function () {
        if (lmsAPI) lmsAPI.LMSFinish("");
    });
</script>
"""
    html = html.replace("</body>", f"{scorm_injector}\n</body>")

    # --- 6. Манифест SCORM 1.2 (структура проверена в Moodle) ---
    manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{COURSE_ID}" version="1.0"
          xmlns="http://www.imsproject.org"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
          xsi:schemaLocation="http://www.imsproject.org imscp_v1p2.xsd
                              http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="{COURSE_ID}_org">
    <organization identifier="{COURSE_ID}_org">
      <title>{COURSE_TITLE}</title>
      <item identifier="{COURSE_ID}_item" identifierref="{COURSE_ID}_res">
        <title>{COURSE_TITLE}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="{COURSE_ID}_res" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
    </resource>
  </resources>
</manifest>
"""

    # --- 7. Упаковка ---
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("imsmanifest.xml", manifest)
        zf.writestr("index.html", html)

    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"[OK] SCORM-пакет собран: {OUTPUT.name} ({size_mb:.1f} МБ)")
    print("Загружайте архив в Moodle как SCORM-курс (SCORM 1.2).")


if __name__ == "__main__":
    main()
