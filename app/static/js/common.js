/* =========================================================================
 * ОБЩАЯ ЛОГИКА: панель деталей, подсветка модели, озвучка, toast
 * Используется главной страницей (3D и AR-режимы) и SCORM-сборкой.
 * ========================================================================= */

const StanApp = (() => {
    // ==========================================
    // ДАННЫЕ ДЕТАЛЕЙ
    // ==========================================
    const PARTS_DATA = [
        { id: 'MillStand', name: 'Рабочая клеть', desc: 'Основной узел стана. Внутри находятся подушки и подшипники. Предназначена для установки валков и обеспечения процесса прокатки.' },
        { id: 'Platform', name: 'Станина', desc: 'Установка и фиксация валков и арматуры. Материал: Сталь. Ширина окна: 240 мм. Высота окна: 570 мм. Общая высота: 820 мм.' },
        { id: 'ElecMotor', name: 'Электродвигатель', desc: 'Род тока: Переменный. Тип: Асинхронный. Напряжение: 380 В. Мощность: 4,2 кВт. Обороты: 1450 об/мин. Не реверсивный.' },
        { id: 'PinionStand', name: 'Шестеренная клеть', desc: 'Передача крутящего момента на 2 вала. Тип: ДУО. Станина литая. Диаметр начальной окружности: 220 мм.' },
        { id: 'Rolls', name: 'Валки', desc: 'Пластическая деформация металла. Материал: Чугун. Гладкие, шлифованные. Диаметр бочки: 200 мм, длина: 450 мм.' },
        { id: 'Spindel', name: 'Шпиндель', desc: 'Передача крутящего момента. Тип: Универсальный. Диаметр: 50 мм. Длина: 400 мм.' },
        { id: 'MotorCoupling', name: 'Моторная муфта', desc: 'Соединение от двигателя к редуктору. Тип: Жесткая. Диаметр: 150 мм. Длина: 200 мм.' },
        { id: 'MasterCoupling', name: 'Коренная муфта', desc: 'Соединение от валов редуктора к шестеренной клети. Тип: Жесткая. Диаметр: 350 мм. Длина: 270 мм.' },
        { id: 'Gearbox', name: 'Редуктор', desc: 'Снижение оборотов двигателя. Двухступенчатый червячный, зубья шевронные. Передаточное число: 525. Смазка: Автол.' },
        { id: 'BalancingDevice', name: 'Уравновешивающее устройство', desc: 'Удержание подушек верхнего валка, прижатие к нажимному устройству. Тип: Пружинный.' },
        { id: 'ScrewdownMechanism', name: 'Нажимное устройство', desc: 'Регулировка зазора между валками. Тип: Винтовое. Один оборот штурвала = 5 мм. Макс. подъём: 80 мм.' },
        { id: 'Pillows', name: 'Подушки', desc: 'Установка подшипников. Материал: Сталь. Высота: 210 мм. Ширина: 200 мм. Расположены внутри рабочей клети (MillStand).' },
        { id: 'Bearings', name: 'Подшипники', desc: 'Установлены внутри подушек в рабочей клети. Обеспечивают вращение валков. Смазка: Автол.' }
    ];

    // Сопутствующая подсветка: у подушек/подшипников нет отдельных мешей —
    // подсвечиваем вместе с ними рабочую клеть
    const PART_RELATIONS = {
        Pillows: ['MillStand', 'MillStone'],
        Bearings: ['MillStand', 'MillStone']
    };

    // ==========================================
    // СОСТОЯНИЕ ПОДСВЕТКИ
    // ==========================================
    const originalMaterials = new Map();  // mesh.uuid -> оригинальный материал
    const highlightMaterials = new Map(); // mesh.uuid -> жёлтый клон (переиспользуется)
    let resetTimer = null;                // ЕДИНСТВЕННЫЙ таймер авто-сброса
    let highlightToken = 0;               // счётчик сессий подсветки
    let activeUtterance = null;           // активная озвучка (для отсечения устаревших onend)
    let toastTimer = null;

    // ==========================================
    // UI: TOAST
    // ==========================================
    function showToast(message) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('show');
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
    }

    // ==========================================
    // ПОДСВЕТКА МОДЕЛИ
    // ==========================================
    function expandNames(partId) {
        const names = [partId];
        (PART_RELATIONS[partId] || []).forEach(n => names.push(n));
        return names;
    }

    // Сохраняем оригинальные материалы один раз — до того как подменили на жёлтый клон
    function ensureOriginals(model) {
        model.traverse(child => {
            if (child.isMesh && child.material && !originalMaterials.has(child.uuid)) {
                originalMaterials.set(child.uuid, child.material);
            }
        });
    }

    function makeYellow(mat) {
        if (!mat) return mat;
        const c = mat.clone();
        if (c.color) c.color.setHex(0xFFFF00);
        if (c.emissive) { c.emissive.setHex(0xFFFF00); c.emissiveIntensity = 0.8; }
        c.needsUpdate = true;
        return c;
    }

    // Клон создаётся ОДИН раз на меш и кэшируется — повторное выделение
    // не пересоздаёт материалы (нет мерцания и утечек)
    function getHighlightMaterial(mesh) {
        let hl = highlightMaterials.get(mesh.uuid);
        if (!hl) {
            const src = originalMaterials.get(mesh.uuid);
            hl = Array.isArray(src) ? src.map(makeYellow) : makeYellow(src);
            highlightMaterials.set(mesh.uuid, hl);
        }
        return hl;
    }

    // Отменяет отложенный сброс и "закрывает" текущую сессию подсветки
    function invalidatePendingReset() {
        if (resetTimer) { clearTimeout(resetTimer); resetTimer = null; }
        highlightToken++;
    }

    // Единственная точка планирования авто-сброса.
    // Старый таймер всегда отменяется, новый привязан к актуальной сессии.
    function scheduleAutoReset(delay) {
        if (resetTimer) clearTimeout(resetTimer);
        const token = highlightToken;
        resetTimer = setTimeout(() => {
            resetTimer = null;
            if (token === highlightToken) resetHighlights();
        }, delay);
    }

    // Активная сцена: при AR-режиме 3D-сцена скрыта (visibility: hidden),
    // подсветка должна идти по видимой сцене
    function getActiveScene() {
        const scenes = document.querySelectorAll('a-scene');
        for (const s of scenes) {
            if (s.style.visibility !== 'hidden') return s;
        }
        return scenes[0] || null;
    }

    function highlightPart(partId) {
        invalidatePendingReset();

        const scene = getActiveScene();
        if (!scene || !scene.object3D) return;

        const lowerNames = expandNames(partId).map(n => n.toLowerCase());
        scene.object3D.traverse((child) => {
            if (!child.isMesh || !child.name || !child.material) return;
            const childLowerName = child.name.toLowerCase();
            if (!lowerNames.some(name => childLowerName.includes(name))) return;
            if (!originalMaterials.has(child.uuid)) originalMaterials.set(child.uuid, child.material);
            child.material = getHighlightMaterial(child);
        });
    }

    function resetHighlights() {
        invalidatePendingReset();

        const scene = getActiveScene();
        if (scene && scene.object3D) {
            scene.object3D.traverse((child) => {
                if (child.isMesh && originalMaterials.has(child.uuid)) {
                    const orig = originalMaterials.get(child.uuid);
                    if (child.material !== orig) child.material = orig;
                }
            });
        }
        document.querySelectorAll('.part-card.highlighted').forEach(c => c.classList.remove('highlighted'));
    }

    // Слушатели model-loaded на всех сущностях с gltf-model.
    // Если модель уже загружена (динамическая сцена) — обрабатываем сразу
    function initModelListeners() {
        document.querySelectorAll('[gltf-model]').forEach(modelEl => {
            const attach = () => {
                if (modelEl.object3D) ensureOriginals(modelEl.object3D);
            };
            modelEl.addEventListener('model-loaded', attach);
            if (modelEl.hasLoaded) attach();
        });
    }

    // ==========================================
    // ОЗВУЧКА
    // ==========================================
    function cleanMarkdown(text) {
        return text.replace(/\*\*/g, '').replace(/\*/g, '').replace(/`/g, '').replace(/#/g, '').replace(/\n/g, ' ');
    }

    function setSpeakingUI(on) {
        const stopBtn = document.getElementById('stop-btn');
        const sendBtn = document.getElementById('send-btn');
        if (stopBtn) stopBtn.classList.toggle('visible', on);
        if (sendBtn) sendBtn.disabled = on;
    }

    function speakText(text, partsToHighlight = []) {
        if (!('speechSynthesis' in window)) {
            showToast('Озвучка не поддерживается браузером');
            return;
        }
        window.speechSynthesis.cancel();
        activeUtterance = null;

        const utterance = new SpeechSynthesisUtterance(cleanMarkdown(text));
        utterance.lang = 'ru-RU';
        utterance.rate = 1.0;
        activeUtterance = utterance;

        utterance.onstart = () => {
            if (activeUtterance !== utterance) return;
            setSpeakingUI(true);
            partsToHighlight.forEach(p => highlightPart(p));
        };
        const finish = () => {
            if (activeUtterance !== utterance) return;
            activeUtterance = null;
            setSpeakingUI(false);
            scheduleAutoReset(1500);
        };
        utterance.onend = finish;
        utterance.onerror = finish;

        window.speechSynthesis.speak(utterance);
    }

    function speakPartOnly(text, partId) {
        if (!('speechSynthesis' in window)) {
            showToast('Озвучка не поддерживается браузером');
            return;
        }
        window.speechSynthesis.cancel();
        activeUtterance = null;

        highlightPart(partId);
        document.querySelectorAll('.part-card').forEach(c => c.classList.remove('highlighted'));
        const card = document.querySelector(`.part-card[data-id="${partId}"]`);
        if (card) card.classList.add('highlighted');

        const utterance = new SpeechSynthesisUtterance(cleanMarkdown(text));
        utterance.lang = 'ru-RU';
        utterance.rate = 1.0;
        activeUtterance = utterance;

        utterance.onstart = () => { if (activeUtterance === utterance) setSpeakingUI(true); };
        const finish = () => {
            if (activeUtterance !== utterance) return;
            activeUtterance = null;
            setSpeakingUI(false);
            scheduleAutoReset(1000);
        };
        utterance.onend = finish;
        utterance.onerror = finish;

        window.speechSynthesis.speak(utterance);
    }

    function stopSpeech() {
        activeUtterance = null;
        window.speechSynthesis.cancel();
        setSpeakingUI(false);
        resetHighlights();
    }

    // ==========================================
    // ПАНЕЛЬ ДЕТАЛЕЙ
    // ==========================================
    function renderPartsList() {
        const partsList = document.getElementById('parts-list');
        if (!partsList) return;

        PARTS_DATA.forEach(part => {
            const card = document.createElement('div');
            card.className = 'part-card';
            card.dataset.id = part.id;
            card.innerHTML = `
                <div class="part-header">
                    <span>${part.name}</span>
                    <button class="speak-btn" title="Озвучить" data-id="${part.id}">🔊</button>
                </div>
                <div class="part-desc">${part.desc}</div>
            `;
            card.addEventListener('click', (e) => {
                if (e.target.classList.contains('speak-btn')) return;
                document.querySelectorAll('.part-card').forEach(c => c.classList.remove('highlighted'));
                card.classList.add('highlighted');
                highlightPart(part.id);
                scheduleAutoReset(5000);
                showToast(`Выделено: ${part.name}`);
            });
            partsList.appendChild(card);
        });

        document.querySelectorAll('.speak-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const part = PARTS_DATA.find(p => p.id === btn.dataset.id);
                if (part) speakPartOnly(part.desc, part.id);
            });
        });
    }

    function initPanelToggle() {
        const infoPanel = document.getElementById('info-panel');
        const togglePanelBtn = document.getElementById('toggle-panel-btn');
        if (!infoPanel || !togglePanelBtn) return;
        togglePanelBtn.addEventListener('click', () => {
            infoPanel.classList.toggle('open');
            togglePanelBtn.classList.toggle('panel-open');
        });
    }

    // ==========================================
    // ОБЩАЯ ИНИЦИАЛИЗАЦИЯ (без сцены)
    // ==========================================
    function initCommon() {
        renderPartsList();
        initPanelToggle();
        const stopBtn = document.getElementById('stop-btn');
        if (stopBtn) stopBtn.addEventListener('click', stopSpeech);
    }

    return {
        PARTS_DATA,
        PART_RELATIONS,
        initCommon,
        initModelListeners,
        showToast,
        highlightPart,
        resetHighlights,
        scheduleAutoReset,
        speakText,
        speakPartOnly,
        stopSpeech,
        cleanMarkdown
    };
})();
