/* =========================================================================
 * ЧАТ: обращается к серверному прокси /api/chat (ключ OpenRouter хранится
 * на сервере в .env и недоступен клиенту), история — в localStorage.
 * ========================================================================= */

const StanChat = (() => {
    const HISTORY_KEY = 'stan_chat_history';
    const MAX_HISTORY = 10;

    let chatHistory, textInput, micBtn, sendBtn, stopBtn, uiContainer, toggleChatBtn, closeChatBtn;
    let recognition = null;

    function getHistory() {
        try {
            return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
        } catch {
            return [];
        }
    }

    function saveHistory(messages) {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-MAX_HISTORY * 2)));
    }

    function addMessageToHistory(role, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg ${role}`;
        msgDiv.textContent = text;
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        saveHistory([...getHistory(), { role, text }]);
    }

    function loadChatHistory() {
        const saved = getHistory();
        if (saved.length) {
            saved.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.className = `msg ${msg.role}`;
                msgDiv.textContent = msg.text;
                chatHistory.appendChild(msgDiv);
            });
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }

    // ==========================================
    // ЗАПРОС К СЕРВЕРНОМУ ПРОКСИ
    // ==========================================
    async function processUserInput(text) {
        addMessageToHistory('user', text);
        textInput.value = '';
        sendBtn.disabled = true;
        sendBtn.textContent = '...';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    history: getHistory().slice(-MAX_HISTORY)
                })
            });

            if (!response.ok) {
                let detail = `Ошибка сервера: ${response.status}`;
                try {
                    const err = await response.json();
                    if (err.detail) detail = err.detail;
                } catch { /* тело не JSON */ }
                throw new Error(detail);
            }

            const data = await response.json();
            addMessageToHistory('assistant', data.text);
            StanApp.speakText(data.text, data.parts || []);

        } catch (error) {
            console.error('Ошибка чата:', error);
            addMessageToHistory('assistant', error.message || 'Ошибка соединения с сервером.');
        } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = '➤';
        }
    }

    // ==========================================
    // ГОЛОСОВОЙ ВВОД
    // ==========================================
    function initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            micBtn.style.display = 'none';
            return;
        }
        recognition = new SpeechRecognition();
        recognition.lang = 'ru-RU';
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.onstart = () => micBtn.classList.add('listening');
        recognition.onend = () => micBtn.classList.remove('listening');
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            textInput.value = transcript;
            processUserInput(transcript);
        };
    }

    // ==========================================
    // ИНИЦИАЛИЗАЦИЯ
    // ==========================================
    function init() {
        chatHistory = document.getElementById('chat-history');
        textInput = document.getElementById('text-input');
        micBtn = document.getElementById('mic-btn');
        sendBtn = document.getElementById('send-btn');
        stopBtn = document.getElementById('stop-btn');
        uiContainer = document.getElementById('ui-container');
        toggleChatBtn = document.getElementById('toggle-chat-btn');
        closeChatBtn = document.getElementById('close-chat-btn');

        const toggleChat = () => {
            uiContainer.classList.toggle('open');
            toggleChatBtn.classList.toggle('chat-open');
        };

        toggleChatBtn.addEventListener('click', toggleChat);
        closeChatBtn.addEventListener('click', toggleChat);

        micBtn.addEventListener('click', () => {
            if (recognition) { try { recognition.start(); } catch (e) { /* уже запущен */ } }
        });
        sendBtn.addEventListener('click', () => {
            const text = textInput.value.trim();
            if (text) processUserInput(text);
        });
        textInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendBtn.click(); });

        chatHistory.addEventListener('dblclick', () => {
            if (confirm('Очистить историю чата?')) {
                localStorage.removeItem(HISTORY_KEY);
                chatHistory.innerHTML = '<div class="msg assistant">История очищена.</div>';
            }
        });

        const greeting = document.querySelector('#chat-history .msg');
        if (!greeting) {
            chatHistory.innerHTML = '<div class="msg assistant">Привет! Я ассистент. Спросите о характеристиках оборудования или выберите деталь в меню слева.</div>';
        }

        initRecognition();
        loadChatHistory();
    }

    return { init, processUserInput };
})();

document.addEventListener('DOMContentLoaded', () => StanChat.init());
