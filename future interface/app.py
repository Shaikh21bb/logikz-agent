from __future__ import annotations

import json
import time

import streamlit as st

from ui.components import render_agent_panel, render_results, render_timeline
from ui.demo_data import DEMO_RESULT
from ui.styles import inject_styles


st.set_page_config(page_title="LogiKz Agent", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
inject_styles()

COPY = {
    "RU": {
        "dashboard": "Обзор", "shipment": "Отправка", "customs": "Таможня", "tnved": "ТН ВЭД", "history": "История",
        "eyebrow": "ИНТЕЛЛЕКТУАЛЬНАЯ ЛОГИСТИКА", "title": "Новая отправка", "subtitle": "Рассчитайте маршрут, пошлины и налоги за пару секунд.",
        "from": "Откуда", "to": "Куда", "product": "Товар", "value": "Стоимость товара, USD", "weight": "Вес, тонн",
        "analyze": "Анализировать отправку", "demo": "🚀 Загрузить демо", "agent": "AI-АГЕНТ", "recent": "ПОСЛЕДНИЙ АНАЛИЗ",
        "placeholder": "Например, серверное оборудование", "waiting": "Агент готов к анализу", "ready": "Заполните данные или загрузите демо — отчёт появится здесь.",
        "error": "Не удалось обработать отправку. Проверьте данные и повторите попытку.", "status": "ДЕМО-СРЕДА · LIVE PREVIEW",
    },
    "KZ": {
        "dashboard": "Шолу", "shipment": "Жүк жөнелту", "customs": "Кеден", "tnved": "ТН ВЭД", "history": "Тарих",
        "eyebrow": "ЗИЯТКЕРЛІК ЛОГИСТИКА", "title": "Жаңа жүк жөнелту", "subtitle": "Бағытты, баждар мен салықтарды бірнеше секундта есептеңіз.",
        "from": "Қайдан", "to": "Қайда", "product": "Тауар", "value": "Тауар құны, USD", "weight": "Салмағы, тонна",
        "analyze": "Жөнелтуді талдау", "demo": "🚀 Демо жүктеу", "agent": "AI-АГЕНТ", "recent": "СОҢҒЫ ТАЛДАУ",
        "placeholder": "Мысалы, серверлік жабдық", "waiting": "Агент талдауға дайын", "ready": "Деректерді енгізіңіз немесе демоны жүктеңіз — есеп осында көрсетіледі.",
        "error": "Жөнелтуді өңдеу мүмкін болмады. Деректерді тексеріп, қайта көріңіз.", "status": "ДЕМО ОРТАСЫ · LIVE PREVIEW",
    },
}


def run_agent(query: str) -> dict:
    """Replace this adapter with Agent Core when its interface is ready.

    The UI consumes a plain dictionary, keeping it independent from the core's
    concrete classes. Current implementation returns a deterministic demo report.
    """
    try:
        payload = json.loads(query)
    except (TypeError, json.JSONDecodeError):
        payload = {}
    result = dict(DEMO_RESULT)
    result["shipment"] = {
        "origin": payload.get("origin", "China"),
        "destination": payload.get("destination", "Kazakhstan"),
    }
    result["product"] = payload.get("product", "Servers")
    result["weight"] = float(payload.get("weight", 10))
    return result


def load_demo_action() -> None:
    """Populate the demo fields from Streamlit's pre-rerun callback phase."""
    st.session_state.form_origin = "China"
    st.session_state.form_destination = "Kazakhstan"
    st.session_state.form_product = "Servers"
    st.session_state.form_value = 50000.0
    st.session_state.form_weight = 10.0
    st.session_state.run_demo = True


if "form_origin" not in st.session_state:
    st.session_state.form_origin = "China"
    st.session_state.form_destination = "Kazakhstan"
    st.session_state.form_product = ""
    st.session_state.form_value = 50000.0
    st.session_state.form_weight = 10.0
if "result" not in st.session_state:
    st.session_state.result = None
if "agent_error" not in st.session_state:
    st.session_state.agent_error = False

lang = st.sidebar.radio("", ["RU", "KZ"], horizontal=True, label_visibility="collapsed")
t = COPY[lang]
st.sidebar.markdown('<div class="brand-mark"><span class="brand-symbol">✦</span><span>LOGIKZ</span></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="brand-caption">AI LOGISTICS<br>&amp; CUSTOMS</div><div class="side-divider"></div>', unsafe_allow_html=True)
for icon, key in [("▦", "dashboard"), ("↗", "shipment"), ("⌘", "customs"), ("◎", "tnved"), ("◷", "history")]:
    st.sidebar.markdown(f'<div class="nav-item {"active" if key == "dashboard" else ""}"><span>{icon}</span>{t[key]}</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-spacer"></div><div class="sidebar-foot"><span class="online-dot"></span> SYSTEM OPERATIONAL<br><small>LogiKz AI · v0.9.4</small></div>', unsafe_allow_html=True)

top_left, top_right = st.columns([5, 2])
with top_left:
    st.markdown(f'<div class="topline">{t["eyebrow"]} <span> / </span> {t["status"]}</div>', unsafe_allow_html=True)
with top_right:
    st.markdown('<div class="secure-tag">● &nbsp; SECURE WORKSPACE</div>', unsafe_allow_html=True)

st.markdown(f'<div class="page-heading"><div><h1>{t["title"]}</h1><p>{t["subtitle"]}</p></div><div class="heading-index">01 <span>— 03</span></div></div>', unsafe_allow_html=True)

form_col, agent_col = st.columns([1.72, 1], gap="large")
with form_col:
    st.markdown('<div class="section-label"><span class="step-number">01</span> SHIPMENT DETAILS</div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            origin = st.text_input(t["from"], key="form_origin")
        with c2:
            destination = st.text_input(t["to"], key="form_destination")
        product = st.text_input(t["product"], placeholder=t["placeholder"], key="form_product")
        c3, c4 = st.columns(2)
        with c3:
            value = st.number_input(t["value"], min_value=0.0, step=1000.0, key="form_value")
        with c4:
            weight = st.number_input(t["weight"], min_value=0.0, step=0.5, key="form_weight")
        a, b = st.columns([1.15, 1])
        with a:
            analyze = st.button(t["analyze"], type="primary", use_container_width=True)
        with b:
            st.button(t["demo"], use_container_width=True, on_click=load_demo_action)

    run_demo = st.session_state.pop("run_demo", False)
    if analyze or run_demo:
        if not origin.strip() or not destination.strip() or not product.strip() or value <= 0 or weight <= 0:
            st.session_state.agent_error = True
            st.session_state.result = None
        else:
            st.session_state.agent_error = False
            query = json.dumps({"origin": origin, "destination": destination, "product": product,
                                "value": value, "weight": weight}, ensure_ascii=False)
            with st.spinner("✦  LogiKz Agent анализирует отправку…"):
                try:
                    time.sleep(0.65)
                    st.session_state.result = run_agent(query)
                except Exception:
                    st.session_state.result = None
                    st.session_state.agent_error = True
        st.rerun()

with agent_col:
    render_agent_panel(t, bool(st.session_state.result), st.session_state.agent_error)

if st.session_state.agent_error:
    st.error(t["error"])
if st.session_state.result:
    render_results(st.session_state.result, lang)
    render_timeline(lang)
else:
    st.markdown(f'<div class="empty-hint"><span class="hint-spark">✦</span><div><b>{t["waiting"]}</b><p>{t["ready"]}</p></div></div>', unsafe_allow_html=True)
