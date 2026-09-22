"""Small, reusable Streamlit views for the LogiKz demo dashboard."""

from __future__ import annotations

import html


def money(value: float) -> str:
    return f"${value:,.0f}"


def render_brand(st) -> None:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-mark"><span class="brand-orb">↗</span>LOGI<b>KZ</b></div>
          <p class="brand-sub">AI LOGISTICS<br>&amp; CUSTOMS</p>
        </div>
        <div class="sidebar-rule"></div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(st, text: dict, language: str) -> tuple[bool, str | None]:
    """Render nav and return (demo_requested, requested_language)."""

    render_brand(st)
    st.markdown('<div class="sidebar-active"><i></i>' + html.escape(text["dashboard"]) + "</div>", unsafe_allow_html=True)
    for label, icon in (
        (text["shipment_nav"], "▣"),
        (text["customs_nav"], "◇"),
        (text["tnved_nav"], "⌘"),
        (text["history"], "◷"),
    ):
        st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True)

    st.markdown('<div class="side-demo">', unsafe_allow_html=True)
    demo_requested = st.button(text["load_demo"], key="load_demo", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="lang-label">LANGUAGE</div>', unsafe_allow_html=True)
    ru, kz = st.columns(2)
    with ru:
        ru_clicked = st.button("RU", key="language_ru", use_container_width=True)
    with kz:
        kz_clicked = st.button("KZ", key="language_kz", use_container_width=True)

    desired_language = "RU" if ru_clicked else "KZ" if kz_clicked else None
    return demo_requested, desired_language


def render_hero(st, text: dict) -> None:
    st.markdown(
        f"""
        <div class="hero">
          <div>
            <div class="eyebrow">{html.escape(text['hero_eyebrow'])}</div>
            <h1>{html.escape(text['hero_title'])}</h1>
            <p>{html.escape(text['hero_note'])}</p>
          </div>
          <div class="live-pill"><span></span>{html.escape(text['live'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_card(st, text: dict, analyzed: bool) -> None:
    first_icon = "✓" if analyzed else "⌕"
    first_class = "status-check" if analyzed else "status-search"
    st.markdown(
        f"""
        <div class="glass-card agent-card">
          <div class="agent-head"><span class="agent-title">{html.escape(text['ai_agent'])}</span><span class="agent-ready">● {html.escape(text['ready'])}</span></div>
          <div class="agent-status"><span class="{first_class}">{first_icon}</span>{html.escape(text['searching'])}</div>
          <div class="agent-status"><span class="status-check">✓</span>{html.escape(text['customs_done'])}</div>
          <div class="agent-status"><span class="status-check">✓</span>{html.escape(text['logistics_done'])}</div>
          <div class="agent-footer">{html.escape(text['mock_note'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _info(label: str, value: str) -> str:
    return (
        '<div class="result-info"><span class="result-label">'
        + html.escape(label)
        + '</span><span class="result-value">'
        + html.escape(value)
        + "</span></div>"
    )


def _metric(label: str, value: str, accent: bool = False) -> str:
    return (
        f'<div class="metric{" accent" if accent else ""}"><span class="metric-label">{html.escape(label)}</span>'
        f'<span class="metric-value">{html.escape(value)}</span></div>'
    )


def render_results(st, text: dict, result: dict) -> None:
    customs = result["customs"]
    logistics = result["logistics"]
    st.markdown(
        f"""
        <div class="results-gap"></div>
        <div class="glass-card results-shell">
          <h2 class="card-heading">{html.escape(text['shipment'])}</h2>
          <div class="results-top">
            {_info(text['shipment'], result['shipment'])}
            {_info(text['product_result'], result['product'])}
            {_info(text['tnved'], result['tnved'])}
          </div>
          <div class="section-title">{html.escape(text['customs'])}</div>
          <div class="metric-grid">
            {_metric(text['customs_value'], money(customs['value']))}
            {_metric(text['duty'], money(customs['duty']))}
            {_metric(text['vat'], money(customs['vat']))}
            {_metric(text['total'], money(customs['total']), True)}
          </div>
          <div class="section-title">{html.escape(text['logistics'])}</div>
          <div class="metric-grid logistics">
            {_metric(text['distance'], logistics['distance'])}
            {_metric(text['weight_result'], logistics['weight'])}
            {_metric(text['transport_cost'], money(logistics['transport_cost']), True)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_timeline(st, text: dict) -> None:
    steps = (
        text["request_received"],
        text["product_classification"],
        text["tnved_search"],
        text["customs_calculation"],
        text["logistics_calculation"],
        text["final_report"],
    )
    items = "".join(
        f'<div class="timeline-item"><span class="timeline-dot">✓</span><span>{html.escape(step)}</span></div>'
        for step in steps
    )
    st.markdown(
        f'<div class="glass-card timeline-card"><h2 class="card-heading">{html.escape(text["timeline"])}</h2><div class="timeline">{items}</div></div>',
        unsafe_allow_html=True,
    )


def render_error(st, text: dict) -> None:
    st.markdown(
        f'<div class="error-card"><strong>⚠ {html.escape(text["error_title"])}</strong><p>{html.escape(text["error_note"])}</p></div>',
        unsafe_allow_html=True,
    )
