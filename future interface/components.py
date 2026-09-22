from __future__ import annotations

import streamlit as st


def render_agent_panel(t: dict, complete: bool, error: bool) -> None:
    state = "ERROR" if error else ("COMPLETE" if complete else "STANDBY")
    state_class = "error" if error else ("complete" if complete else "standby")
    st.markdown(f'<div class="agent-card"><div class="agent-head"><div class="agent-icon">✦</div><div><span class="agent-kicker">{t["agent"]}</span><div class="agent-name">LogiKz Copilot</div></div><span class="agent-state {state_class}"><i></i>{state}</span></div><div class="agent-rule"></div><div class="agent-label">EXECUTION STATUS</div>', unsafe_allow_html=True)
    lines = [
        ("⌕", "Searching TN VED", complete),
        ("✓", "Customs calculated", complete),
        ("✓", "Logistics calculated", complete),
    ]
    for icon, label, done in lines:
        cls = "task-done" if done else "task-pending"
        st.markdown(f'<div class="agent-task {cls}"><span class="task-icon">{icon}</span>{label}<span class="task-status">{"DONE" if done else "READY"}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="agent-footer"><span class="pulse"></span> AGENT SYSTEMS ONLINE <span class="latency">42 ms</span></div></div>', unsafe_allow_html=True)


def render_results(result: dict, lang: str) -> None:
    ru = lang == "RU"
    shipment = result.get("shipment", {})
    currency = result.get("currency", "USD")
    title = "Результат анализа" if ru else "Талдау нәтижесі"
    captions = ["ТАМОЖЕННАЯ СТОИМОСТЬ" if ru else "КЕДЕНДІК ҚҰН", "ПОШЛИНА" if ru else "БАЖ", "НДС" if ru else "ҚҚС", "ВСЕГО К ОПЛАТЕ" if ru else "ЖАЛПЫ ТӨЛЕМ"]
    st.markdown(f'<div class="results-title"><div><div class="section-label"><span class="step-number">02</span> {"ОТЧЁТ АГЕНТА" if ru else "АГЕНТ ЕСЕБІ"}</div><h2>{title}</h2></div><span class="report-badge">✦ AI REPORT</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown(f'<div class="result-overline">{"МАРШРУТ ОТПРАВКИ" if ru else "ЖӨНЕЛТУ БАҒЫТЫ"}</div><div class="route-line"><b>{shipment.get("origin", "—")}</b><span>→</span><b>{shipment.get("destination", "—")}</b></div><div class="product-line"><span>{"ТОВАР" if ru else "ТАУАР"}</span><b>{result.get("product", "—")}</b><span class="tnved-chip">ТН ВЭД &nbsp;{result.get("tnved", "—")}</span></div>', unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            st.markdown(f'<div class="result-overline">{"ЛОГИСТИКА" if ru else "ЛОГИСТИКА"}</div>', unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Расстояние" if ru else "Қашықтық", f'{result.get("distance_km", 0):,} km')
            m2.metric("Вес" if ru else "Салмақ", f'{result.get("weight", 0):g} t')
            m3.metric("Доставка" if ru else "Жеткізу", f'${result.get("transport_cost", 0):,.0f}')
    metrics = st.columns(4)
    keys = ["customs_value", "duty", "vat", "total"]
    for index, (col, key) in enumerate(zip(metrics, keys)):
        with col:
            value = float(result.get(key, 0))
            with st.container(border=True):
                st.markdown(f'<div class="metric-label">{captions[index]}</div><div class="money-value">${value:,.0f}<small> {currency}</small></div><div class="metric-accent accent-{index}"></div>', unsafe_allow_html=True)


def render_timeline(lang: str) -> None:
    steps = (["Запрос получен", "Классификация товара", "Поиск кода ТН ВЭД", "Расчёт таможни", "Расчёт логистики", "Итоговый отчёт"] if lang == "RU"
             else ["Сұрау қабылданды", "Тауарды жіктеу", "ТН ВЭД кодын іздеу", "Кеденді есептеу", "Логистиканы есептеу", "Қорытынды есеп"])
    st.markdown(f'<div class="timeline-title"><div class="section-label"><span class="step-number">03</span> {"ХОД ВЫПОЛНЕНИЯ AI" if lang == "RU" else "AI ОРЫНДАЛУ БАРЫСЫ"}</div></div><div class="timeline-row">' + ''.join(f'<div class="timeline-step"><span class="timeline-check">✓</span><span>{step}</span></div>' for step in steps) + '</div>', unsafe_allow_html=True)
