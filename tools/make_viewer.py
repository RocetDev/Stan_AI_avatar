"""
Одноразовая сборка viewer.html из all_in_one.html:
вырезает AR.js, маркер, тумблер режимов — остаётся только 3D-просмотрщик.
Результат viewer.html далее живёт как самостоятельный исходник (для SCORM/iframe).
"""
import re
import sys

SRC = 'all_in_one.html'
DST = 'viewer.html'

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

def cut(s, start_marker, end_marker_inclusive):
    """Удаляет фрагмент от start_marker до end_marker_inclusive (включительно)."""
    i = s.find(start_marker)
    assert i != -1, f'NOT FOUND: {start_marker[:60]!r}'
    j = s.find(end_marker_inclusive, i)
    assert j != -1, f'NOT FOUND end: {end_marker_inclusive[:60]!r}'
    return s[:i] + s[j + len(end_marker_inclusive):]

def sub_once(s, old, new):
    assert s.count(old) == 1, f'EXPECTED 1 OCCURRENCE, got {s.count(old)}: {old[:60]!r}'
    return s.replace(old, new)

# --- 1. Заголовок и подключение AR.js ---
html = sub_once(html, '<title>AR Просмотрщик Стана</title>',
                '<title>3D Просмотрщик Стана</title>')
html = sub_once(html, '    <script src="./aframe-ar.js"></script>\n', '')

# --- 2. CSS: тумблер режима ---
html = sub_once(html, """
        #mode-toggle-btn {
            top: 20px;
            right: 20px;
            font-size: 14px;
            font-weight: bold;
            width: auto;
            padding: 0 15px;
        }
""", '\n')
html = sub_once(html, """
            #mode-toggle-btn {
                font-size: 12px;
                padding: 0 10px;
            }

            #mode-toggle-btn.panel-shifted {
                top: 80px;
            }
""", '\n')

# --- 3. Кнопка тумблера в body ---
html = sub_once(html,
                '    <button id="mode-toggle-btn" class="control-btn" title="Переключить режим"> AR</button>\n',
                '')

# --- 4. Сцена: только 3D-просмотр ---
scene_start = html.find('    <a-scene embedded arjs=')
assert scene_start != -1, 'a-scene not found'
scene_end = html.find('</a-scene>', scene_start) + len('</a-scene>')
new_scene = """    <a-scene embedded
        renderer="physicallyCorrectLights: true; toneMapping: ACESFilmic; toneMappingExposure: 2.0; colorManagement: true;">

        <a-assets>
            <a-asset-item id="tank-model" src=""></a-asset-item>
        </a-assets>

        <a-light type="ambient" color="#ffffff" intensity="1.2"></a-light>
        <a-light type="directional" color="#ffffff" intensity="2.5" position="2 3 2"></a-light>
        <a-light type="directional" color="#ffffff" intensity="1.8" position="-2 2 -2"></a-light>
        <a-light type="point" color="#ffffff" intensity="2.0" distance="15" decay="1" position="0 4 0"></a-light>
        <a-light type="hemisphere" color="#ffffff" groundColor="#aaaaaa" intensity="0.8"></a-light>

        <!-- 3D Просмотр модели -->
        <a-entity id="target-object" gltf-model="#tank-model" position="-1 1.17 0" rotation="0 0 0"
            scale="0.8 0.8 0.8"></a-entity>

        <a-entity id="camera-rig" position="0 1.6 3">
            <a-entity camera look-controls="touchEnabled: true; mouseEnabled: true"
                wasd-controls="enabled: false"></a-entity>
        </a-entity>
    </a-scene>"""
html = html[:scene_start] + new_scene + html[scene_end:]

# --- 5. Base64: вырезаем чанки маркера ---
html = cut(html, 'const MARKER_BASE64_CHUNKS = [', '];')
html = sub_once(html, "const MARKER_BASE64 = MARKER_BASE64_CHUNKS.join('');\n", '')

# --- 6. JS: ссылки на AR-сущности и тумблер ---
html = sub_once(html,
"""        const modeToggleBtn = document.getElementById('mode-toggle-btn');
        const stopSpeechBtn = document.getElementById('stop-speech-btn');
        const arContainer = document.getElementById('ar-container');
        const viewerContainer = document.getElementById('viewer-container');
        const markerEl = document.querySelector('a-marker');
        const assetModel = document.getElementById('tank-model');
        const toast = document.getElementById('toast');
        const cameraRig = document.getElementById('camera-rig');

        let isARMode = true;
        let toastTimer = null;
""",
"""        const stopSpeechBtn = document.getElementById('stop-speech-btn');
        const assetModel = document.getElementById('tank-model');
        const toast = document.getElementById('toast');

        let toastTimer = null;
""")

html = sub_once(html,
"""            assetModel.setAttribute('src', MODEL_BASE64);
            if (markerEl) markerEl.setAttribute('url', MARKER_BASE64);
""",
"""            assetModel.setAttribute('src', MODEL_BASE64);
""")

html = sub_once(html,
"""            togglePanelBtn.addEventListener('click', () => {
                infoPanel.classList.toggle('open');
                togglePanelBtn.classList.toggle('panel-open');
                if (window.innerWidth <= 768) {
                    modeToggleBtn.classList.toggle('panel-shifted', infoPanel.classList.contains('open'));
                }
            });

            modeToggleBtn.addEventListener('click', () => {
                isARMode = !isARMode;
                if (isARMode) {
                    arContainer.setAttribute('visible', 'true');
                    viewerContainer.setAttribute('visible', 'false');
                    modeToggleBtn.textContent = '📷 AR';
                    cameraRig.setAttribute('position', '0 1.6 0');
                } else {
                    arContainer.setAttribute('visible', 'false');
                    viewerContainer.setAttribute('visible', 'true');
                    modeToggleBtn.textContent = ' 3D';
                    cameraRig.setAttribute('position', '0 1.6 3');
                }
                resetHighlights();
            });

""",
"""            togglePanelBtn.addEventListener('click', () => {
                infoPanel.classList.toggle('open');
                togglePanelBtn.classList.toggle('panel-open');
            });

""")

with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'OK: {DST} создан ({len(html)/1024/1024:.2f} MB)')
