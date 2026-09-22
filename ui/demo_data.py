"""Demo content and the interface contract for the LogiKz presentation UI.

The UI intentionally works with plain dictionaries.  The production agent can
be adapted in one place (``run_agent`` in app.py) without coupling any visual
component to its internal API.
"""

from __future__ import annotations

import json


DEMO_REQUEST = {
    "origin": "China",
    "destination": "Kazakhstan",
    "product": "Servers",
    "value": 50_000,
    "weight": 10.0,
}


COPY = {
    "RU": {
        "dashboard": "Панель",
        "shipment_nav": "Отправление",
        "customs_nav": "Таможня",
        "tnved_nav": "ТН ВЭД",
        "history": "История",
        "load_demo": "🚀 Загрузить демо",
        "new_shipment": "Новое отправление",
        "new_shipment_note": "Введите параметры — агент подготовит маршрут, код ТН ВЭД и расчёт платежей.",
        "origin": "Откуда",
        "destination": "Куда",
        "product": "Товар",
        "product_placeholder": "Например: серверное оборудование",
        "value": "Стоимость товара, USD",
        "weight": "Вес, тонн",
        "analyze": "Анализировать отправление",
        "ai_agent": "AI АГЕНТ",
        "ready": "ГОТОВ К АНАЛИЗУ",
        "searching": "Поиск ТН ВЭД",
        "customs_done": "Таможня рассчитана",
        "logistics_done": "Логистика рассчитана",
        "shipment": "Отправление",
        "product_result": "Товар",
        "tnved": "ТН ВЭД",
        "customs": "Таможенные платежи",
        "customs_value": "Таможенная стоимость",
        "duty": "Пошлина",
        "vat": "НДС",
        "total": "Итого",
        "logistics": "Логистика",
        "distance": "Расстояние",
        "weight_result": "Вес",
        "transport_cost": "Стоимость перевозки",
        "timeline": "Ход выполнения AI",
        "request_received": "Запрос получен",
        "product_classification": "Классификация товара",
        "tnved_search": "Поиск ТН ВЭД",
        "customs_calculation": "Расчёт таможенных платежей",
        "logistics_calculation": "Расчёт логистики",
        "final_report": "Финальный отчёт готов",
        "hero_eyebrow": "LOGISTICS INTELLIGENCE",
        "hero_title": "Превращаем сложную поставку в ясное решение.",
        "hero_note": "Маршрут, код ТН ВЭД и платежи — в одном AI-отчёте.",
        "error_required": "Укажите товар, стоимость и вес, чтобы начать анализ.",
        "error_title": "Не удалось выполнить анализ",
        "error_note": "Проверьте данные отправления и попробуйте ещё раз.",
        "live": "LIVE DEMO",
        "mock_note": "Демонстрационный расчёт · можно заменить на Agent Core",
        "origin_option": "Китай",
        "destination_option": "Казахстан",
    },
    "KZ": {
        "dashboard": "Басқару тақтасы",
        "shipment_nav": "Жөнелтілім",
        "customs_nav": "Кеден",
        "tnved_nav": "ТН ВЭД",
        "history": "Тарих",
        "load_demo": "🚀 Демоны жүктеу",
        "new_shipment": "Жаңа жөнелтілім",
        "new_shipment_note": "Параметрлерді енгізіңіз — агент бағытты, ТН ВЭД кодын және төлемдерді есептейді.",
        "origin": "Қайдан",
        "destination": "Қайда",
        "product": "Тауар",
        "product_placeholder": "Мысалы: серверлік жабдық",
        "value": "Тауар құны, USD",
        "weight": "Салмақ, тонна",
        "analyze": "Жөнелтілімді талдау",
        "ai_agent": "AI АГЕНТ",
        "ready": "ТАЛДАУҒА ДАЙЫН",
        "searching": "ТН ВЭД іздеу",
        "customs_done": "Кеден есептелді",
        "logistics_done": "Логистика есептелді",
        "shipment": "Жөнелтілім",
        "product_result": "Тауар",
        "tnved": "ТН ВЭД",
        "customs": "Кеден төлемдері",
        "customs_value": "Кедендік құн",
        "duty": "Баж",
        "vat": "ҚҚС",
        "total": "Барлығы",
        "logistics": "Логистика",
        "distance": "Қашықтық",
        "weight_result": "Салмақ",
        "transport_cost": "Тасымалдау құны",
        "timeline": "AI орындау барысы",
        "request_received": "Сұрау қабылданды",
        "product_classification": "Тауарды жіктеу",
        "tnved_search": "ТН ВЭД іздеу",
        "customs_calculation": "Кеден төлемдерін есептеу",
        "logistics_calculation": "Логистиканы есептеу",
        "final_report": "Қорытынды есеп дайын",
        "hero_eyebrow": "LOGISTICS INTELLIGENCE",
        "hero_title": "Күрделі жеткізуді анық шешімге айналдырамыз.",
        "hero_note": "Бағыт, ТН ВЭД коды және төлемдер — бір AI-есепте.",
        "error_required": "Талдауды бастау үшін тауарды, құнын және салмағын көрсетіңіз.",
        "error_title": "Талдауды орындау мүмкін болмады",
        "error_note": "Жөнелтілім деректерін тексеріп, әрекетті қайталаңыз.",
        "live": "LIVE DEMO",
        "mock_note": "Демонстрациялық есеп · кейін Agent Core қосылады",
        "origin_option": "Қытай",
        "destination_option": "Қазақстан",
    },
}


def build_query(payload: dict) -> str:
    """Serialize a UI request into an implementation-independent agent query."""

    return json.dumps(payload, ensure_ascii=False)


def mock_agent_response(query: str) -> dict:
    """Return a stable, jury-friendly response while Agent Core is unavailable."""

    request = json.loads(query)
    product = request.get("product", "Servers").strip() or "Servers"
    value = float(request.get("value", DEMO_REQUEST["value"]))
    weight = float(request.get("weight", DEMO_REQUEST["weight"]))

    # The demo deliberately presents the requested $55K customs value: the
    # illustrative route includes $5K freight in the customs base.
    freight = 5_000
    customs_value = value + freight
    duty = customs_value * 0.10
    vat = (customs_value + duty) * 0.12

    return {
        "shipment": f"{request.get('origin', 'China')} → {request.get('destination', 'Kazakhstan')}",
        "product": "Server Equipment" if product.lower() in {"servers", "server", "серверы"} else product.title(),
        "tnved": "8471",
        "customs": {
            "value": customs_value,
            "duty": duty,
            "vat": vat,
            "total": duty + vat,
        },
        "logistics": {
            "distance": "5,600 km",
            "weight": f"{weight:g} tons",
            "transport_cost": freight,
        },
        "source": "mock",
    }
