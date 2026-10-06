"""Production T3 Chennai transit chat, backed exclusively by the local JSON API."""

from __future__ import annotations

import os
from pathlib import Path
import sys

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.frontend_contract import DEFAULT_API_URL, ask_api, result_panel  # noqa: E402


API_URL = (os.environ.get("NLP_V2_API_URL") or DEFAULT_API_URL).rstrip("/")

st.set_page_config(page_title="Chennai Transit Assistant", page_icon="🚇", layout="centered")
st.markdown("""
<style>
  .block-container { max-width: 900px; padding-top: 2rem; padding-bottom: 5rem; }
  [data-testid="stAppViewContainer"] { background: #f7f9fc; color: #17314b; }
  [data-testid="stChatMessage"] { border: 1px solid #d9e3ee; border-radius: 14px; background: white; }
  h1, h2, h3 { color: #143654; }
  .transit-kicker { color: #236b82; font-weight: 700; letter-spacing: .12em; font-size: .76rem; text-transform: uppercase; }
  .transit-subtitle { color: #53677b; margin: -.4rem 0 1.2rem; }
  @media (max-width: 640px) { .block-container { padding: 1rem .8rem 5rem; } }
</style>
""", unsafe_allow_html=True)


def _api_ready() -> bool:
    try:
        response = requests.get(API_URL + "/health", timeout=2)
        body = response.json()
        return response.status_code == 200 and body.get("taxonomy") == "T3"
    except (requests.RequestException, ValueError, TypeError):
        return False


def _submit(query: str) -> None:
    if not query.strip():
        return
    st.session_state.messages.append({"role": "user", "text": query})
    with st.spinner("Checking the transit snapshot…"):
        reply = ask_api(query, base_url=API_URL)
    st.session_state.messages.append({"role": "assistant", "reply": reply})
    st.session_state.pending_query = query if reply.get("status") == "clarification" else None


def _table(rows: list[dict], columns: list[str] | None = None) -> None:
    if not rows:
        return
    if columns:
        rows = [{column: row.get(column) for column in columns} for row in rows]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _show_source(value) -> None:
    if value:
        sources = value if isinstance(value, list) else [value]
        st.caption("Source: " + ", ".join(str(item) for item in sources))


def _render_panel(reply: dict) -> None:
    panel = result_panel(reply)
    if not panel:
        if reply.get("status") == "unavailable":
            count = reply.get("data", {}).get("published_directional_route_candidates")
            if count:
                st.caption(f"The snapshot contains up to {count} route-sequence candidates; current operation is unconfirmed.")
        return
    kind, data = panel["kind"], panel["data"]
    with st.container(border=True):
        if kind == "routes":
            st.subheader("Journey candidates")
            _table(data.get("routes", []), ["route_name", "mode", "origin_stop_id", "destination_stop_id", "source"])
        elif kind == "stops":
            st.subheader("Route stops")
            for sequence in data.get("sequences", []):
                with st.expander(f"{sequence.get('route_name', 'Route')} · direction {sequence.get('direction_id', '?')}", expanded=False):
                    _table(sequence.get("stops", []), ["sequence", "name", "stop_id"])
                    _show_source(sequence.get("source"))
            if data.get("truncated"):
                st.caption("Additional published sequences are not shown here.")
        elif kind == "membership":
            st.metric("On published route sequence", "Yes" if data["on_route"] else "No")
        elif kind == "service_bounds":
            st.subheader("Published service times")
            first, last = st.columns(2)
            first.metric("First departure", data.get("first_departure", "—"))
            last.metric("Last departure", data.get("last_departure", "—"))
            st.caption("GTFS service-day times may continue past 24:00.")
            _show_source(data.get("source"))
        elif kind == "frequency":
            st.metric("Median scheduled interval", f"{data['median_headway_minutes']:g} min")
            if data.get("window_start"):
                st.caption(f"Estimated from the {data.get('window_minutes', 120)} minutes after {data['window_start']}.")
            _show_source(data.get("source"))
        elif kind == "departures":
            st.subheader("Published departures")
            _table(data.get("departures", []), ["route_name", "time", "source"])
            st.caption("Times are schedule records, not live predictions.")
        elif kind == "fare":
            st.metric("Published fare", f"{data.get('currency', 'INR')} {data['amount']:g}")
            st.caption(f"Effective date: {data.get('effective_date', 'unknown')} · Source: {data.get('source', 'unknown')}")
        elif kind == "nearest":
            st.subheader("Nearest by straight line")
            _table(data.get("stops", []), ["name", "mode", "distance_m", "source"])
            st.caption("Walking access and current operation are not verified.")
        elif kind == "interchange":
            st.subheader("Interchange details")
            _table(data.get("transfers", []))
        elif kind == "accessibility":
            st.metric(data.get("feature", "Accessibility"), "Recorded available" if data.get("available") else "Recorded unavailable")
        elif kind in {"facility", "ticketing"}:
            st.subheader("Published information")
            st.write(data)
        if data.get("provisional"):
            st.caption("Snapshot-derived information. Verify current service and conditions with the operator.")


def _render_reply(reply: dict) -> None:
    status = reply.get("status", "error")
    message = reply.get("response_text", "The assistant returned no response.")
    if status == "error":
        st.error(message)
    elif status == "unavailable":
        st.warning(message)
    elif status in {"clarification", "out_of_scope"}:
        st.info(message)
    else:
        st.write(message)
    if status == "clarification":
        missing = reply.get("missing_slots") or []
        if missing:
            st.caption("Needed: " + ", ".join(str(item).replace("_", " ") for item in missing))
        choices = reply.get("candidate_intents") or []
        if len(choices) > 1:
            st.caption("Question types: " + ", ".join(item.replace("_", " ") for item in choices))
        entities = reply.get("candidate_entities") or []
        if entities:
            st.caption("Possible canonical locations: " + ", ".join(entities) + ". Use a specific stop name in the revised question.")
    _render_panel(reply)


st.markdown('<div class="transit-kicker">Chennai · Public transport</div>', unsafe_allow_html=True)
st.title("Transit Assistant")
st.markdown('<div class="transit-subtitle">Ask about routes, stops, schedules, fares, or nearby transit.</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if not _api_ready():
    st.warning("The local T3 API is offline. Start it with `python -m app.api` to answer questions.")

if not st.session_state.messages:
    st.info("Start with a complete question. Route and fare answers use the published snapshot; live status is unavailable.")
    examples = [
        ("Nearby metro", "Where is the nearest metro station to Marina Beach?"),
        ("Bus route stops", "List stops on bus route 102"),
        ("Published fare", "What is the metro fare from Central to Airport?"),
    ]
    columns = st.columns(3)
    for column, (label, query) in zip(columns, examples):
        if column.button(label, use_container_width=True):
            _submit(query)
            st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["text"])
        else:
            _render_reply(message["reply"])

if st.session_state.pending_query:
    with st.form("revise_question"):
        revised = st.text_input("Revise your full question", value=st.session_state.pending_query)
        submitted = st.form_submit_button("Ask revised question", use_container_width=True)
    if submitted:
        _submit(revised)
        st.rerun()

new_query = st.chat_input("Ask about Chennai public transport…")
if new_query:
    _submit(new_query)
    st.rerun()
