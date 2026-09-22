"""LogiKz Agent — jury-ready Streamlit demo dashboard.

Run with: ``streamlit run app.py``
"""

from __future__ import annotations

import time

import streamlit as st

from ui.components import (
    render_agent_card,
    render_error,
    render_hero,
    render_results,
    render_sidebar,
    render_timeline,
)
from ui.demo_data import COPY, DEMO_REQUEST, build_query, mock_agent_response
from ui.styles import inject_styles


try:  # Agent Core is optional until the team integrates it.
    from agent_core import ProductionLogiKzAgent  # type: ignore
except ImportError:
    ProductionLogiKzAgent = None


def run_agent(query: str):
    """Run the current agent backend through one stable UI-facing contract.

    Replace only the body of this function when Agent Core is ready.  The
    Streamlit components deliberately consume the neutral dictionary shape
    returned by the mock.
    """

    if ProductionLogiKzAgent is not None:
        # Keep integration deliberately defensive: agent implementations often
        # expose either ``run`` or ``invoke``.  Normalize them at this edge.
        agent = ProductionLogiKzAgent()
        if hasattr(agent, "run"):
            return agent.run(query)
        if hasattr(agent, "invoke"):
            return agent.invoke(query)
        raise RuntimeError("Agent Core does not expose run() or invoke().")
    return mock_agent_response(query)


def _initialize_state() -> None:
    defaults = {
        "language": "RU",
        "origin": "China",
        "destination": "Kazakhstan",
        "product": "",
        "value": 0.0,
        "weight": 0.0,
        "result": None,
        "error": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _load_demo() -> None:
    st.session_state.update(DEMO_REQUEST)
    # One click gives the jury both a filled request and the finished report.
    # This preserves the normal Analyze button for an interactive walkthrough.
    st.session_state.result = run_agent(build_query(DEMO_REQUEST))
    st.session_state.error = None


def _analyze(text: dict) -> None:
    payload = {
        "origin": st.session_state.origin,
        "destination": st.session_state.destination,
        "product": st.session_state.product,
        "value": st.session_state.value,
        "weight": st.session_state.weight,
    }
    if not payload["product"].strip() or payload["value"] <= 0 or payload["weight"] <= 0:
        st.session_state.result = None
        st.session_state.error = text["error_required"]
        return

    st.session_state.error = None
    with st.spinner(f"{text['searching']}…"):
        # A short pause makes the agent hand-off legible during a live pitch.
        time.sleep(0.65)
        try:
            st.session_state.result = run_agent(build_query(payload))
        except Exception:
            st.session_state.result = None
            st.session_state.error = text["error_note"]


def main() -> None:
    st.set_page_config(page_title="LogiKz Agent", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
    _initialize_state()
    inject_styles(st)

    language = st.session_state.language
    text = COPY[language]
    with st.sidebar:
        demo_requested, desired_language = render_sidebar(st, text, language)

    if desired_language and desired_language != language:
        st.session_state.language = desired_language
        st.rerun()
    if demo_requested:
        _load_demo()
        st.rerun()

    render_hero(st, text)
    form_column, agent_column = st.columns((1.62, 0.92), gap="large")
    with form_column:
        with st.container(border=True):
            st.markdown(f'<h2 class="card-heading">{text["new_shipment"]}</h2>', unsafe_allow_html=True)
            st.markdown(f'<p class="card-copy">{text["new_shipment_note"]}</p>', unsafe_allow_html=True)
            route_left, route_right = st.columns(2)
            with route_left:
                st.selectbox(text["origin"], ["China", "Kazakhstan", "Turkey", "Germany"], key="origin")
            with route_right:
                st.selectbox(text["destination"], ["Kazakhstan", "China", "Uzbekistan", "Kyrgyzstan"], key="destination")
            st.text_input(text["product"], placeholder=text["product_placeholder"], key="product")
            value_column, weight_column = st.columns(2)
            with value_column:
                st.number_input(text["value"], min_value=0.0, step=1_000.0, format="%.0f", key="value")
            with weight_column:
                st.number_input(text["weight"], min_value=0.0, step=0.5, format="%.1f", key="weight")
            analyze_requested = st.button(f"✦  {text['analyze']}", type="primary", use_container_width=True)
        if analyze_requested:
            _analyze(text)
        if st.session_state.error:
            render_error(st, text)

    with agent_column:
        render_agent_card(st, text, analyzed=st.session_state.result is not None)

    if st.session_state.result:
        render_results(st, text, st.session_state.result)
        render_timeline(st, text)


if __name__ == "__main__":
    main()
