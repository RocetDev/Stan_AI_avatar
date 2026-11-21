/* =========================================================================
 * РЕЖИМЫ 3D / AR (единая страница)
 * - 3D-сцена статична (в index.html) и работает всегда — камера не нужна
 * - AR-сцена строится лениво: только после успешной проверки камеры.
 *   Если камеры нет — остаёмся в 3D с тостом, приложение не падает.
 * - Кнопка #mode-toggle-btn переключает режимы на месте.
 *   Выбранный режим запоминается в localStorage.
 * ========================================================================= */

const StanModes = (() => {
    const MODE_KEY = 'stan-mode';
    const CAMERA_CHECK_TIMEOUT = 15000;

    let currentMode = '3d';
    let arSceneEl = null;
    let arLibsLoaded = false;
    let switching = false;

    // ---------- Проверка камеры ----------
    function isSecure() {
        return window.isSecureContext === true;
    }

    function checkCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            return Promise.resolve({ ok: false, reason: 'unsupported' });
        }
        if (!isSecure()) {
            return Promise.resolve({ ok: false, reason: 'insecure' });
        }

        return new Promise((resolve) => {
            const timer = setTimeout(() => resolve({ ok: false, reason: 'timeout' }), CAMERA_CHECK_TIMEOUT);
            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(stream => {
                    stream.getTracks().forEach(t => t.stop());
                    clearTimeout(timer);
                    resolve({ ok: true });
                })
                .catch(err => {
                    clearTimeout(timer);
                    resolve({ ok: false, reason: err && err.name === 'NotFoundError' ? 'notfound' : 'denied' });
                });
        });
    }

    // ---------- Загрузка AR.js (ленивая, один раз) ----------
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = () => reject(new Error(`Не удалось загрузить ${src}`));
            document.head.appendChild(s);
        });
    }

    // ---------- Управление 3D-сценой ----------
    function getScene3d() {
        return document.getElementById('scene-3d');
    }

    function hide3D() {
        const s = getScene3d();
        if (!s) return;
        s.pause();
        s.style.visibility = 'hidden';
    }

    function show3D() {
        const s = getScene3d();
        if (!s) return;
        s.style.visibility = '';
        s.play();
    }

    // ---------- Построение AR-сцены ----------
    function buildARScene() {
        const scene = document.createElement('a-scene');
        scene.setAttribute('embedded', '');
        scene.setAttribute('arjs', 'sourceType: webcam; debugUIEnabled: false;');
        scene.setAttribute('renderer', 'physicallyCorrectLights: true; colorManagement: true;');

        // Свет — как в оригинальном index.html (свет жил внутри маркера)
        const lightSpecs = [
            { type: 'ambient', color: '#ffffff', intensity: '1.2' },
            { type: 'directional', color: '#ffffff', intensity: '2.5', position: '2 3 2' },
            { type: 'directional', color: '#ffffff', intensity: '1.8', position: '-2 2 -2' },
            { type: 'directional', color: '#ffffff', intensity: '1.5', position: '0 3 -3' },
            { type: 'directional', color: '#ffffff', intensity: '1.2', position: '1 -1 2' },
            { type: 'point', color: '#ffffff', intensity: '2.0', position: '0 4 0', distance: '15', decay: '1' },
            { type: 'hemisphere', color: '#ffffff', groundColor: '#aaaaaa', intensity: '0.8' }
        ];
        lightSpecs.forEach(spec => {
            const l = document.createElement('a-light');
            Object.entries(spec).forEach(([k, v]) => l.setAttribute(k, v));
            scene.appendChild(l);
        });

        // Маркер. ВАЖНО: gltf-model задаём прямым URL, а не ссылкой на a-assets —
        // при динамическом создании сцены A-Frame не успевает связать ассет по id
        // ("#tank-model asset not found" и пустой маркер).
        const marker = document.createElement('a-marker');
        marker.setAttribute('type', 'pattern');
        marker.setAttribute('url', '/static/assets/pattern-Stan_pattern.patt?v=2');

        const obj = document.createElement('a-entity');
        obj.id = 'target-object-ar';
        obj.setAttribute('gltf-model', '/static/assets/StanNew.glb?v=2');
        // Трансформы — ТОЧНО как в рабочем all_in_one.html. Модель крупная
        // (~2.5 м): при position 0 0 0 камера телефона оказывается внутри
        // модели (backface-culling -> невидима), поэтому вынесена за маркер
        // и увеличена.
        obj.setAttribute('position', '-1 0 -2');
        obj.setAttribute('rotation', '0 0 0');
        obj.setAttribute('scale', '1.8 1.8 1.8');
        obj.addEventListener('model-error', (e) => {
            console.error('AR: ошибка загрузки модели:', e.detail);
            StanApp.showToast('⚠️ Ошибка загрузки 3D-модели');
        });
        marker.appendChild(obj);
        scene.appendChild(marker);

        const camera = document.createElement('a-entity');
        camera.setAttribute('camera', '');
        scene.appendChild(camera);

        // Диагностика: якорь arjs-anchor эмитит markerFound/markerLost на элемент
        marker.addEventListener('markerFound', () => {
            console.log('AR: маркер найден');
            StanApp.showToast('✅ Маркер найден');
        });
        marker.addEventListener('markerLost', () => {
            console.log('AR: маркер потерян');
        });
        scene.addEventListener('loaded', () => console.log('AR: сцена инициализирована'));

        // ВАЖНО: сцена — прямой ребёнок body, как в оригинальном index.html.
        // Обёртка-div без высоты обнуляет размер embedded-сцены (canvas 0x0),
        // из-за чего модель не отображалась, хотя видеопоток шёл.
        document.body.appendChild(scene);
        arSceneEl = scene;

        // Подсветка деталей: слушатели model-loaded уже после создания сущностей
        StanApp.initModelListeners();
    }

    // ---------- Разборка AR-сцены ----------
    function teardownAR() {
        if (arSceneEl) {
            arSceneEl.parentNode && arSceneEl.parentNode.removeChild(arSceneEl);
            arSceneEl = null;
        }
        // Останавливаем видеопоток, оставленный AR.js
        document.querySelectorAll('video').forEach(v => {
            if (v.srcObject) v.srcObject.getTracks().forEach(t => t.stop());
            v.remove();
        });
    }

    // ---------- Кнопка-переключатель ----------
    function updateToggleBtn() {
        const btn = document.getElementById('mode-toggle-btn');
        if (!btn) return;
        btn.disabled = switching;
        btn.textContent = currentMode === '3d' ? '📷 AR' : '🖥 3D';
        btn.title = currentMode === '3d' ? 'Переключить в AR-режим' : 'Переключить в 3D-режим';
    }

    function setMode(mode) {
        currentMode = mode;
        localStorage.setItem(MODE_KEY, mode);
        updateToggleBtn();
    }

    // ---------- Переключение 3D → AR ----------
    async function switchToAR() {
        if (currentMode === 'ar' || switching) return;
        switching = true;
        updateToggleBtn();

        const check = await checkCamera();
        if (!check.ok) {
            switching = false;
            updateToggleBtn();
            localStorage.setItem(MODE_KEY, '3d');
            StanApp.showToast('📷 Камера недоступна — остаёмся в 3D-режиме');
            return;
        }

        try {
            if (!arLibsLoaded) {
                await loadScript('/static/vendor/aframe-ar.js?v=2');
                arLibsLoaded = true;
            }
            teardownAR(); // на случай остатков от прошлой попытки
            hide3D();
            buildARScene();
            setMode('ar');
        } catch (e) {
            console.error('Ошибка инициализации AR:', e);
            teardownAR();
            show3D();
            localStorage.setItem(MODE_KEY, '3d');
            StanApp.showToast('⚠️ Не удалось запустить AR-режим');
        }
        switching = false;
        updateToggleBtn();
    }

    // ---------- Переключение AR → 3D ----------
    function switchTo3D() {
        if (currentMode === '3d' || switching) return;
        switching = true;
        updateToggleBtn();

        teardownAR();
        show3D();
        setMode('3d');

        switching = false;
        updateToggleBtn();
    }

    // ---------- Инициализация ----------
    function init() {
        StanApp.initCommon();
        StanApp.initModelListeners();

        const btn = document.getElementById('mode-toggle-btn');
        if (btn) {
            btn.addEventListener('click', () => {
                if (currentMode === '3d') switchToAR();
                else switchTo3D();
            });
        }

        // Восстановление режима: если последний раз был AR — пробуем снова.
        // Если камера недоступна — тихо остаёмся в 3D.
        if (localStorage.getItem(MODE_KEY) === 'ar') {
            switchToAR();
        }
        updateToggleBtn();
    }

    document.addEventListener('DOMContentLoaded', init);

    return { switchToAR, switchTo3D };
})();
