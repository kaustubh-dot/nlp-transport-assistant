"""Production T3 Chennai transit chat, backed exclusively by the local JSON API."""

from __future__ import annotations

import os
from pathlib import Path
import sys

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.frontend_contract import DEFAULT_API_URL, ask_api, result_panel  # noqa: E402
from app.frontend_language import LANGUAGE_NAMES, examples, field_label, reply_text, tr  # noqa: E402


API_URL = (os.environ.get("NLP_V2_API_URL") or DEFAULT_API_URL).rstrip("/")
STATUS_LABELS = {
    'ok': 'Published information', 'clarification': 'More information needed',
    'unavailable': 'Information unavailable', 'out_of_scope': 'Outside transport scope',
    'error': 'Request could not be completed',
}

st.set_page_config(page_title="Chennai Transit Assistant", page_icon="🚆", layout="wide")
# Restore the original MandiPulse / Quiet Exchange visual language, preserved in
# legacy_streamlit_app.py. Presentation remains independent of the T3 API.
st.markdown((Path(__file__).with_name("transit_theme.html")).read_text(encoding="utf-8"),
            unsafe_allow_html=True)
UI_LANGUAGE = st.radio(
    "Language / भाषा", list(LANGUAGE_NAMES), format_func=LANGUAGE_NAMES.get,
    horizontal=True, key="ui_language",
)


def _t(text: str, **values) -> str:
    return tr(text, UI_LANGUAGE, **values)


def _api_ready() -> bool:
    try:
        response = requests.get(API_URL + "/health", timeout=2)
        body = response.json()
        return response.status_code == 200 and isinstance(body, dict) and body.get("taxonomy") == "T3"
    except (requests.RequestException, ValueError, TypeError):
        return False


def _submit(query: str) -> None:
    if not query.strip():
        return
    default_mode = st.session_state.get('selected_transport_mode', 'auto')
    default_mode = None if default_mode == 'auto' else default_mode
    st.session_state.messages.append({"role": "user", "text": query, "default_transport_mode": default_mode})
    with st.spinner(_t("Checking the transit snapshot…")):
        reply = ask_api(query, base_url=API_URL, transport_mode=default_mode)
    st.session_state.messages.append({"role": "assistant", "reply": reply})
    st.session_state.pending_query = query if reply.get("status") == "clarification" else None


def _save_mode_selection() -> None:
    st.session_state.selected_transport_mode = st.session_state.transport_mode


def _toggle_records() -> None:
    st.session_state.records_open = not st.session_state.get('records_open', False)


def _table(rows: list[dict], columns: list[str] | None = None) -> None:
    if not rows:
        return
    if columns:
        rows = [{_t(column): field_label(row.get(column), UI_LANGUAGE)
                 if column in {'mode', 'mode_from', 'mode_to'} and UI_LANGUAGE != 'en'
                 else row.get(column) for column in columns} for row in rows]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _show_source(value) -> None:
    if value:
        sources = value if isinstance(value, list) else [value]
        st.caption(_t("Source: {source}", source=", ".join(str(item) for item in sources)))


def _render_panel(reply: dict) -> None:
    panel = result_panel(reply)
    if not panel:
        if reply.get("status") == "unavailable":
            count = reply.get("data", {}).get("published_directional_route_candidates")
            if count:
                st.caption(_t("The snapshot contains up to {count} route-sequence candidates; current operation is unconfirmed.", count=count))
        return
    kind, data = panel["kind"], panel["data"]
    with st.container(border=True):
        if kind == "routes":
            st.subheader(_t("Published route candidates"))
            _table(data.get("routes", []), ["route_name", "mode", "source"])
            st.caption(_t('Stop-sequence connectivity only. A current trip or transfer plan is not confirmed.'))
        elif kind == "stops":
            st.subheader(_t("Route stops"))
            for index, sequence in enumerate(data.get("sequences", []), 1):
                with st.expander(_t("{route} · published sequence {index}", route=sequence.get('route_name', _t('Route')), index=index), expanded=False):
                    _table(sequence.get("stops", []), ["sequence", "name"])
                    _show_source(sequence.get("source"))
            if data.get("truncated"):
                st.caption(_t("Additional published sequences are not shown here."))
        elif kind == "membership":
            st.metric(_t("On published route sequence"), _t("Yes" if data["on_route"] else "No"))
            _show_source(data.get('source'))
        elif kind == "service_bounds":
            st.subheader(_t("Published service times"))
            first, last = st.columns(2)
            first.metric(_t("First departure"), data.get("first_departure", "—"))
            last.metric(_t("Last departure"), data.get("last_departure", "—"))
            st.caption(_t("GTFS service-day times may continue past 24:00."))
            _show_source(data.get("source"))
        elif kind == "frequency":
            st.metric(_t("Median scheduled interval"), f"{data['median_headway_minutes']:g} " + _t('min'))
            if data.get("window_start"):
                st.caption(_t("Estimated from the {minutes} minutes after {time}.", minutes=data.get('window_minutes', 120), time=data['window_start']))
            _show_source(data.get("source"))
        elif kind == "departures":
            st.subheader(_t("Published departures"))
            _table(data.get("departures", []), ["route_name", "time", "source"])
            st.caption(_t("Times are schedule records, not live predictions."))
        elif kind == "fare":
            st.metric(_t("Published fare"), f"{data.get('currency', 'INR')} {data['amount']:g}")
            if data.get("service_type"):
                st.caption(_t("Service class: {service}", service=field_label(data['service_type'], UI_LANGUAGE)))
            st.caption(_t("Effective date: {date} · Source: {source}", date=data.get('effective_date', _t('unknown')), source=data.get('source', _t('unknown'))))
        elif kind == "nearest":
            st.subheader(_t("Nearest by straight line"))
            _table(data.get("stops", []), ["name", "mode", "distance_m", "source"])
            st.caption(_t("Walking access and current operation are not verified."))
        elif kind == "interchange":
            st.subheader(_t("Interchange details"))
            _table(data.get("transfers", []))
        elif kind == "accessibility":
            st.metric(field_label(data.get("feature", _t("Accessibility")), UI_LANGUAGE), _t("Recorded available" if data.get("available") else "Recorded unavailable"))
        elif kind in {"facility", "ticketing"}:
            st.subheader(_t("Published information"))
            st.write(data.get('policy') if kind == 'ticketing' else data.get('facility'))
            _show_source(data.get('source'))
        routes = data.get('routes')
        partial = data.get('partial_topology') is True or (isinstance(routes, list) and any(
            isinstance(row, dict) and row.get('partial_topology') is True for row in routes))
        if partial:
            st.caption(_t('Partial published coverage: some links or route variants cannot be verified.'))
            excluded = data.get('excluded_unusable_rows')
            excluded = excluded if type(excluded) is int and excluded >= 0 else 0
            uncovered = data.get('uncovered_route_ids')
            variant_count = len(uncovered) if isinstance(uncovered, list) else 0
            if excluded or variant_count:
                st.caption(_t('Omitted: {links} unusable links and {variants} route variant(s).', links=excluded, variants=variant_count))
        if data.get('hub_membership_unverified'):
            st.caption(_t('Hub-to-stop membership is provisional; the exact boarding location needs verification.'))
        if data.get("provisional"):
            st.caption(_t("Snapshot-derived information. Verify current service and conditions with the operator."))


def _render_reply(reply: dict) -> None:
    status = reply.get("status", "error")
    st.caption(_t(STATUS_LABELS.get(status, STATUS_LABELS['error'])))
    message = reply_text(reply, UI_LANGUAGE)
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
            st.caption(_t("Needed: {slots}", slots=", ".join(field_label(item, UI_LANGUAGE) for item in missing)))
        choices = reply.get("candidate_intents") or []
        if len(choices) > 1:
            st.caption(_t("Question types: {intents}", intents=", ".join(field_label(item, UI_LANGUAGE) for item in choices)))
        entities = reply.get("candidate_entities") or []
        if entities:
            st.caption(_t('More than one stop or location matches. Include the route number, transport mode '
                          'or precise stop name in your revised full question.'))
    _render_panel(reply)


with st.sidebar:
    st.markdown(f"""
    <div class="rail-brand">
        <h2 class="rail-brand-title">{_t('Chennai Transit')}</h2>
        <p class="rail-brand-sub">{_t('Multilingual transport assistant')}</p>
    </div>
    """, unsafe_allow_html=True)
    st.subheader(_t("Ask in your own words"))
    st.caption("English · हिन्दी · Hinglish")
    st.write(_t("Routes, stops, published schedules, fares and nearby transport."))
    st.divider()
    st.subheader(_t("Published snapshot"))
    st.caption(_t("No live updates. Confirm current service and fares with the operator."))
    st.caption(_t("Transfer, accessibility and facility information is shown only when supported by the source."))
    st.markdown(f'<div class="snapshot-evidence">{_t("Chennai · Public transport")}</div>', unsafe_allow_html=True)

st.markdown(f"""
<header class="mp-masthead">
    <h1 class="mp-title">{_t('Chennai Multimodal Transit Assistant')}</h1>
    <p class="mp-subtitle">{_t('Ask about routes, stops, schedules, fares, or nearby transit.')}</p>
</header>
""", unsafe_allow_html=True)

# Keep a separate persistent selection: translated widget option labels change
# Streamlit's widget identity, but must never reset a user's chosen mode.
MODE_NAMES = {'auto': 'Any mode', 'bus': 'Bus', 'metro': 'Metro',
              'suburban_rail': 'Rail (suburban)', 'mrts': 'MRTS'}
st.session_state.transport_mode = st.session_state.get('selected_transport_mode', 'auto')
with st.container(key='transport_controls'):
    mode_column, records_column = st.columns([4, 1.5])
    with mode_column:
        st.radio('Transport / परिवहन', list(MODE_NAMES), format_func=lambda mode: _t(MODE_NAMES[mode]),
                 horizontal=True, key='transport_mode', on_change=_save_mode_selection,
                 label_visibility='collapsed')
    with records_column:
        st.button(_t('Published records'), key='published_records', use_container_width=True,
                  type='primary' if st.session_state.get('records_open') else 'secondary', on_click=_toggle_records)
    st.caption(_t('A mode written in your question takes priority. Select Any mode to clear the default.'))
if st.session_state.get('records_open'):
    with st.container(border=True):
        st.subheader(_t('Source coverage'))
        st.write(_t('Published stop sequences, schedule records and dated fares. Coverage varies by transport mode.'))
        st.caption(_t('No live updates. Confirm current service and fares with the operator.'))
        st.caption(_t('Transfer, accessibility and facility information is shown only when supported by the source.'))
st.caption(_t('Published snapshot · No live updates · Verify current service with the operator'))

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

if not _api_ready():
    st.warning(_t("The local T3 API is offline. Start it with `python -m app.api` to answer questions."))

if not st.session_state.messages:
    st.info(_t("Start with a complete question. Route and fare answers use the published snapshot; live status is unavailable."))
    starter_examples = examples(UI_LANGUAGE)
    columns = st.columns(3)
    for index, (column, (label, query)) in enumerate(zip(columns, starter_examples)):
        if column.button(label, use_container_width=True, key=f'starter_example_{index}'):
            _submit(query)
            st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["text"])
            if message.get('default_transport_mode'):
                st.caption(_t('Default mode: {mode}', mode=field_label(message['default_transport_mode'], UI_LANGUAGE)))
        else:
            _render_reply(message["reply"])

if st.session_state.pending_query:
    # A form's unsubmitted value lives in the browser. The turn-specific key
    # preserves that draft across language changes, then resets for a new query.
    revision_key = f"revision_text_{len(st.session_state.messages)}"
    with st.form("revise_question"):
        st.caption(_t("Revise your full question"))
        revised = st.text_input("Revise / संशोधित करें / Badlein", value=st.session_state.pending_query,
                                key=revision_key, label_visibility='collapsed')
        submitted = st.form_submit_button(_t("Ask revised question"), use_container_width=True)
    if submitted:
        _submit(revised)
        st.rerun()

# Streamlit 1.44 includes the placeholder in widget identity. A stable trilingual
# placeholder preserves browser-only drafts when the language radio reruns.
new_query = st.chat_input("Ask / पूछें / Pooch")
if new_query:
    _submit(new_query)
    st.rerun()
