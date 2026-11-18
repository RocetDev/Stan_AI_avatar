/* =========================================================================
 * AR-СТРАНИЦА (/ar)
 * Ключевое отличие от старой версии: AR.js и сцена инициализируются ЛЕНИВО —
 * только после успешной проверки камеры. Если камеры нет / доступ запрещён /
 * страница открыта не по https — показываем fallback, приложение не падает.
 * ========================================================================= */

const StanAR = (() => {
    const CAMERA_CHECK_TIMEOUT = 15000;

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
                    // NotAllowedError / NotFoundError и др.
                    resolve({ ok: false, reason: err && err.name === 'NotFoundError' ? 'notfound' : 'denied' });
                });
        });
    }

    // ---------- Fallback ----------
    function showFallback(reason) {
        const el = document.getElementById('camera-fallback');
        const text = document.getElementById('fallback-text');
        const hints = {
            denied: 'Доступ к камере запрещён. Разрешите камеру в настройках браузера (иконка замка в адресной строке) и попробуйте снова.',
            notfound: 'Камера не найдена на этом устройстве. AR-режим недоступен, но вы можете посмотреть модель в 3D.',
            insecure: 'AR-режим работает только по защищённому соединению (https) или на localhost. Откройте страницу по https или перейдите в 3D-режим.',
            unsupported: 'Этот браузер не поддерживает доступ к камере. Попробуйте современный браузер или перейдите в 3D-режим.',
            timeout: 'Не удалось получить доступ к камере за отведённое время. Проверьте, не занята ли камера другим приложением.'
        };
        if (text) text.textContent = hints[reason] || hints.denied;
        if (el) el.classList.add('visible');
    }

    // ---------- Динамическая загрузка библиотек ----------
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = () => reject(new Error(`Не удалось загрузить ${src}`));
            document.head.appendChild(s);
        });
    }

    // ---------- Построение AR-сцены (после загрузки AFRAME + AR.js) ----------
    function buildScene() {
        const root = document.getElementById('scene-root');

        const scene = document.createElement('a-scene');
        scene.setAttribute('embedded', '');
        scene.setAttribute('arjs', 'sourceType: webcam; debugUIEnabled: false; detectionMode: mono_and_matrix;');
        scene.setAttribute('renderer',
            'physicallyCorrectLights: true; toneMapping: ACESFilmic; toneMappingExposure: 2.0; colorManagement: true;');

        const assets = document.createElement('a-assets');
        const modelItem = document.createElement('a-asset-item');
        modelItem.id = 'tank-model';
        modelItem.setAttribute('src', '/static/assets/StanNew.glb');
        assets.appendChild(modelItem);
        scene.appendChild(assets);

        const lights = [
            ['ambient', '#ffffff', '1.2', null],
            ['directional', '#ffffff', '2.5', '2 3 2'],
            ['directional', '#ffffff', '1.8', '-2 2 -2'],
            ['point', '#ffffff', '2.0', '0 4 0']
        ];
        lights.forEach(([type, color, intensity, position]) => {
            const l = document.createElement('a-light');
            l.setAttribute('type', type);
            l.setAttribute('color', color);
            l.setAttribute('intensity', intensity);
            if (position) l.setAttribute('position', position);
            scene.appendChild(l);
        });
        const hemi = document.createElement('a-light');
        hemi.setAttribute('type', 'hemisphere');
        hemi.setAttribute('color', '#ffffff');
        hemi.setAttribute('groundColor', '#aaaaaa');
        hemi.setAttribute('intensity', '0.8');
        scene.appendChild(hemi);

        const marker = document.createElement('a-marker');
        marker.setAttribute('type', 'pattern');
        marker.setAttribute('url', '/static/assets/pattern-Stan_pattern.patt');
        const obj = document.createElement('a-entity');
        obj.id = 'target-object-ar';
        obj.setAttribute('gltf-model', '#tank-model');
        obj.setAttribute('position', '-1 0 -2');
        obj.setAttribute('rotation', '0 0 0');
        obj.setAttribute('scale', '1.8 1.8 1.8');
        marker.appendChild(obj);
        scene.appendChild(marker);

        const rig = document.createElement('a-entity');
        rig.setAttribute('position', '0 1.6 0');
        const camera = document.createElement('a-entity');
        camera.setAttribute('camera', '');
        rig.appendChild(camera);
        scene.appendChild(rig);

        root.appendChild(scene);

        // Подсветка деталей: слушатели model-loaded уже после создания сущностей
        StanApp.initModelListeners();
    }

    // ---------- Точка входа ----------
    async function start() {
        StanApp.initCommon(); // панель деталей и озвучка работают независимо от камеры

        const check = await checkCamera();
        if (!check.ok) {
            showFallback(check.reason);
            return;
        }

        try {
            await loadScript('/static/vendor/aframe.min.js');
            await loadScript('/static/vendor/aframe-ar.js');
            buildScene();
        } catch (e) {
            console.error('Ошибка инициализации AR:', e);
            showFallback('unsupported');
        }
    }

    document.addEventListener('DOMContentLoaded', start);

    return { start };
})();
