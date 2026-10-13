import os
import zipfile

# Настройки курса
COURSE_ID = "Stan_AR_Avatar_Course"
COURSE_TITLE = "Дополненная реальность: Аватар Стан"

# 1. Генерируем манифест (imsmanifest.xml) - главный файл, без которого LMS не примет курс
manifest_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{COURSE_ID}" version="1.0"
          xmlns="http://imsglobal.org"
          xmlns:xsi="http://w3.org"
          xmlns:adlcp="http://adlnet.org"
          xsi:schemaLocation="http://imsglobal.org imscp_v1p1n1.xsd
                              http://adlnet.org adlcp_v1p3.xsd">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="stan_ar_org">
    <organization identifier="stan_ar_org">
      <title>{COURSE_TITLE}</title>
      <item identifier="item_1" identifierref="resource_1">
        <title>{COURSE_TITLE}</title>
      </item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="resource_1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html"/>
    </resource>
  </resources>
</manifest>
"""

# 2. Читаем ваш автономный HTML-код
try:
    with open('ar_app_standalone.html', 'r', encoding='utf-8') as f:
        standalone_html = f.read()
except FileNotFoundError:
    print("Ошибка: Сначала запустите предыдущий скрипт, чтобы создать 'ar_app_standalone.html'!")
    exit()

# 3. Вшиваем SCORM API трекинг прямо перед закрывающим тегом </body> в приложении.
# Это нужно, чтобы СДО понимала, что пользователь зашел в курс и прошел его.
scorm_js_injector = """
<script>
    // Простейший коннектор к API СДО (LMS)
    var lmsAPI = null;
    
    function findAPI(win) {
        var maxTries = 10, tries = 0;
        while ((win.API == null) && (win.parent != null) && (win.parent != win)) {
            tries++;
            if (tries > maxTries) return null;
            win = win.parent;
        }
        return win.API;
    }

    window.addEventListener('load', function() {
        lmsAPI = findAPI(window);
        if (!lmsAPI && window.opener) {
            lmsAPI = findAPI(window.opener);
        }
        
        if (lmsAPI) {
            lmsAPI.LMSInitialize("");
            // Передаем статус "Пройдено" сразу при успешной загрузке AR
            lmsAPI.LMSSetValue("cmi.core.lesson_status", "completed");
            lmsAPI.LMSCommit("");
            console.log("SCORM: Статус 'completed' успешно отправлен в LMS.");
        } else {
            console.log("SCORM: Запущено локально (LMS API не обнаружено).");
        }
    });

    window.addEventListener('unload', function() {
        if (lmsAPI) {
            lmsAPI.LMSFinish("");
        }
    });
</script>
"""

# Вставляем скрипт трекинга перед </body>
if "</body>" in standalone_html:
    scorm_html = standalone_html.replace("</body>", f"{scorm_js_injector}\n</body>")
else:
    scorm_html = standalone_html + scorm_js_injector

# 4. Создаем SCORM ZIP-архив
zip_filename = 'ar_course_scorm12.zip'

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as scorm_zip:
    # Записываем файл манифеста в корень архива
    scorm_zip.writestr('imsmanifest.xml', manifest_content)
    # Записываем сам плеер, переименовав его в index.html (стандарт для SCORM)
    scorm_zip.writestr('index.html', scorm_html)

print(f"\n[УСПЕХ] SCORM-пакет успешно собран: '{zip_filename}'")
print("Этот архив теперь можно загружать в любую СДО (Moodle, iSpring и т.д.).")
