import json
import logging

import httpx

from app.core.config import Settings
from app.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)

# Известные имена мешей модели — используется для подсветки деталей на клиенте
KNOWN_PARTS = {
    "Platform", "MillStand", "MillStone", "ElecMotor", "PinionStand", "Rolls",
    "Spindel", "MotorCoupling", "MasterCoupling", "Gearbox", "BalancingDevice",
    "ScrewdownMechanism", "Pillows", "Bearings",
}

SYSTEM_PROMPT = """Ты — лаконичный AR-ассистент оператора прокатного стана. Отвечай СТРОГО на основе технических характеристик.

ПРАВИЛА:
1. Отвечай кратко: 1-2 предложения.
2. На вопрос "Что такое стан?" отвечай ТОЛЬКО: "Это оборудование для пластической деформации металла".
3. Если информации нет: "В моей базе данных нет информации об этом".
4. Пиши текст без markdown (без **, без -), готовый для голосовой озвучки.

ФОРМАТ ОТВЕТА — СТРОГО JSON:
{
  "parts": ["ИмяЧасти1", "ИмяЧасти2"],
  "text": "Твой текстовый ответ пользователю"
}

Правила для "parts":
- Указывай ТОЛЬКО те части, о которых идёт речь.
- Используй ТОЧНЫЕ имена: Platform, MillStand, MillStone, ElecMotor, PinionStand, Rolls, Spindel, MotorCoupling, MasterCoupling, Gearbox, BalancingDevice, ScrewdownMechanism, Pillows, Bearings.
- ВАЖНО: Если вопрос касается "подушек" или "подшипников", ОБЯЗАТЕЛЬНО добавь "MillStand" (или "MillStone") в массив parts, так как в 3D-модели они не имеют отдельных мешей и являются частью рабочей клети.
- Если вопрос общий, оставь массив пустым: "parts": []

ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ СТАНА:
1. Рабочая клеть (MillStand): Основной узел стана, внутри которого расположены подушки и подшипники. Предназначена для установки валков и обеспечения процесса прокатки.
2. Валки: Назначение: Пластическая деформация металла. Материал: Чугун. Состояние: Гладкие. Обработка: Шлифование. Диаметр бочки: 200 мм. Длина бочки: 450 мм. Диаметр шейки: 75 мм. Длина шейки: 100 мм.
3. Привод стана (двигатель): Род тока: Переменный. Тип: Асинхронный. Напряжение: 380 В. Мощность: 4,2 кВт. Обороты: 1450 об/мин. Реверсивность: Не реверсивный. Регулировка оборотов: Отсутствует. Пусковое устройство: Кнопочное.
4. Коренная муфта: Назначение: Соединение от валов редуктора к шестеренной клети. Тип: Жесткая. Диаметр: 350 мм. Длина: 270 мм.
5. Моторная муфта: Назначение: Соединение от двигателя к редуктору. Тип: Жесткая. Диаметр: 150 мм. Длина: 200 мм.
6. Нажимное устройство: Назначение: Регулировка зазора между валками. Тип: Винтовое. Шаг нарезки: 6 мм. Диаметр винта: внутренний 61 мм, внешний 68 мм. Привод: Штурвал, редуктор. Передаточное число редуктора: 1,2. Значение одного оборота штурвала: 5 мм. Макс. высота подъёма верхнего валка: 80 мм. Смазка: Солидол.
7. Редуктор: Количество: 1. Назначение: Снижение оборотов двигателя. Тип: Двухступенчатый червячный. Тип зубьев: Шевронный. Общее передаточное число: 525. Смазка: Автол.
8. Станина: Назначение: Установка и фиксация валков и арматуры. Материал: Сталь. Ширина окна: 240 мм. Высота окна: 570 мм. Общая высота: 820 мм. Расстояние между станинами: 530 мм. Расстояние от пола до линии прокатки: 900 мм.
9. Уравновешивающее устройство: Назначение: Удержание подушек верхнего валка, прижатие верхнего валка к нажимному устройству. Тип: Пружинный.
10. Шпиндель: Назначение: Передача крутящего момента. Тип: Универсальный. Диаметр: 50 мм. Длина: 400 мм.
11. Шестеренная клеть: Назначение: Передача крутящего момента на 2 вала. Тип: ДУО. Станина: Литая. Диаметр начальной окружности: 220 мм. Тип зуба: Прямой. Подшипники шестеренных валков: Качения. Смазка зубьев и подшипников: Автол.
12. Подушки: Назначение: Установка подшипников. Материал: Сталь. Высота: 210 мм. Ширина: 200 мм. Осевая регулировка: Болтовая. Находятся внутри рабочей клети.
13. Подшипники: Установлены внутри подушек в рабочей клети. Обеспечивают вращение валков."""


class LLMError(Exception):
    """Ошибка обращения к LLM-провайдеру."""


class LLMService:
    def __init__(self, settings: Settings, client: httpx.AsyncClient):
        self._settings = settings
        self._client = client

    async def ask(self, message: str, history: list[ChatMessage]) -> tuple[str, list[str]]:
        """Возвращает (текст ответа, список частей для подсветки)."""
        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [{"role": m.role, "content": m.text} for m in history]
        messages.append({"role": "user", "content": message})

        try:
            response = await self._client.post(
                f"{self._settings.openrouter_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._settings.openrouter_api_key}",
                    "X-Title": "AR Stan Assistant",
                },
                json={
                    "model": self._settings.model_name,
                    "messages": messages,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("OpenRouter HTTP %s: %s", e.response.status_code, e.response.text[:500])
            raise LLMError(f"LLM API вернула статус {e.response.status_code}") from e
        except httpx.HTTPError as e:
            logger.error("OpenRouter connection error: %s", e)
            raise LLMError("Не удалось соединиться с LLM API") from e

        content = response.json()["choices"][0]["message"]["content"]
        return self._parse(content)

    @staticmethod
    def _parse(content: str) -> tuple[str, list[str]]:
        """Парсит JSON-ответ модели, при сбое возвращает сырой текст."""
        cleaned = content.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(cleaned)
            text = str(data.get("text", "")).strip() or content.strip()
            parts = [p for p in data.get("parts", []) if p in KNOWN_PARTS]
            return text, parts
        except (json.JSONDecodeError, AttributeError):
            logger.warning("LLM вернул не-JSON ответ, отдаю сырой текст")
            return content.strip(), []
