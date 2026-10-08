"""Presentation translations preserve facts, provenance, and refusal scope."""

from copy import deepcopy
import importlib
from string import Formatter

import pytest


def catalog():
    # A missing implementation must be a test failure rather than collection error.
    try:
        return importlib.import_module("app.frontend_language")
    except ModuleNotFoundError as exc:
        pytest.fail(f"The pure frontend language catalog is missing: {exc}")


def test_english_reply_is_byte_for_byte_unchanged():
    text = "  Published fare: INR 17.\n未知 source / MTC_2018.  "
    assert catalog().reply_text({"status": "ok", "response_text": text}, "en") == text


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_unknown_reply_with_structured_mode_cannot_break_localization(language):
    from app.frontend_contract import valid_reply

    reply = {"status": "ok", "operation": "PLAN_ROUTE",
             "response_text": "Unknown source qualification; no confirmation.",
             "data": {"routes": [{"route_name": "QA_ROUTE", "mode": {"unexpected": "object"}}]}}
    assert valid_reply(reply)
    before = deepcopy(reply)
    assert catalog().reply_text(reply, language).endswith(reply["response_text"])
    assert reply == before


@pytest.mark.parametrize("language,heading", [("hi", "प्रकाशित किराया"), ("hinglish", "Prakashit kiraya")])
def test_display_translation_formats_values_without_translating_provenance(language, heading):
    module = catalog()
    assert module.tr("Published fare", language) == heading
    result = module.tr("Effective date: {date} · Source: {source}", language,
                       date="2018-01-29", source="MTC_OFFICIAL_2018")
    assert "2018-01-29" in result and "MTC_OFFICIAL_2018" in result
    assert result != "Effective date: 2018-01-29 · Source: MTC_OFFICIAL_2018"


DYNAMIC_TEMPLATES = [
    "Source: {source}", "Effective date: {date} · Source: {source}",
    "Service class: {service}", "{route} · published sequence {index}",
    "Estimated from the {minutes} minutes after {time}.",
    "Omitted: {links} unusable links and {variants} route variant(s).",
    "The snapshot contains up to {count} route-sequence candidates; current operation is unconfirmed.",
    "Needed: {slots}", "Question types: {intents}.", "Question types: {intents}",
    "Original explanation: {message}.", "Original explanation: {message}",
]


@pytest.mark.parametrize("template", DYNAMIC_TEMPLATES)
@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_all_dynamic_values_survive_localized_templates(template, language):
    fields = [field for _, field, _, _ in Formatter().parse(template) if field]
    values = {field: f"KEEP_{field}_41" for field in fields}
    translated = catalog().tr(template, language, **values)
    assert translated != template.format(**values)
    for value in values.values():
        assert translated.count(value) == 1


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_unknown_reply_retains_qualification_even_with_known_panel_data(language):
    reply = {"status": "unavailable", "operation": "CALCULATE_FARE",
             "response_text": "Unfamiliar source says only 2027-03-19; service not confirmed.",
             "data": {"amount": 17, "currency": "INR", "effective_date": "2018-01-29"}}
    before = deepcopy(reply)
    text = catalog().reply_text(reply, language)
    assert text.endswith(reply["response_text"])
    assert text != reply["response_text"]
    assert "INR 17" not in text
    assert reply == before


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_curated_unavailability_stays_unavailable(language):
    module = catalog()
    text = module.reply_text({"status": "unavailable", "response_text":
                             "Live transport status is unavailable; please verify with the operator."}, language)
    assert "अनुपलब्ध" in text if language == "hi" else "unavailable" in text
    assert "पुष्टि" in text if language == "hi" else "verify" in text
    assert "Original explanation" not in text and "मूल विवरण" not in text


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_data_derived_fare_preserves_amount_date_and_confirmation(language):
    reply = {"status": "ok", "operation": "CALCULATE_FARE",
             "response_text": "Published fare (Deluxe Services): INR 17 (record effective 2018-01-29). Published stage fare found; confirm the current fare before travel.",
             "data": {"amount": 17, "currency": "INR", "service_type": "Deluxe Services",
                      "effective_date": "2018-01-29", "source": "MTC_OFFICIAL"}}
    text = catalog().reply_text(reply, language)
    assert "INR 17" in text and "2018-01-29" in text
    assert "पुष्टि" in text if language == "hi" else "confirm" in text
    assert "Original explanation" not in text and "मूल विवरण" not in text


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_unknown_tail_after_known_fact_is_explicitly_preserved(language):
    reply = {"status": "ok", "operation": "CALCULATE_FARE",
             "response_text": "Published fare: INR 17 (record effective 2018-01-29). Valid only for SOURCE_ID_X.",
             "data": {"amount": 17, "currency": "INR", "effective_date": "2018-01-29"}}
    text = catalog().reply_text(reply, language)
    assert "INR 17" in text and text.endswith("Valid only for SOURCE_ID_X.")
    assert "Original explanation" in text if language == "hinglish" else "मूल विवरण" in text


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_gtfs_extended_time_and_canonical_names_are_not_rewritten(language):
    reply = {"status": "ok", "operation": "GET_FIRST_LAST_SERVICE",
             "response_text": "Published first departure: 05:30:00; last: 25:10:00 (service-day time). Published schedule bounds; verify current operation with the operator.",
             "data": {"first_departure": "05:30:00", "last_departure": "25:10:00"}}
    text = catalog().reply_text(reply, language)
    assert "05:30:00" in text and "25:10:00" in text
    for name in ("Marina Bus Stand", "HUB_CENTRAL", "SOURCE_METRO_24", "Ordinary Services Station"):
        assert catalog().field_label(name, language) == name


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_missing_execution_prompt_localizes_only_its_exact_known_shape(language):
    reply = {"status": "clarification", "missing_slots": ["origin", "destination"],
             "response_text": "Please provide the starting stop, the destination stop."}
    text = catalog().reply_text(reply, language)
    assert text != reply["response_text"] and "Original explanation" not in text and "मूल विवरण" not in text
    reply["response_text"] = "Please provide the starting stop only if SOURCE_X confirms it."
    assert catalog().reply_text(reply, language).endswith(reply["response_text"])


def test_examples_have_explicit_questions_in_each_language_and_english_is_compatible():
    module = catalog()
    assert module.examples("en") == [
        ("Nearby metro", "Where is the nearest metro station to Marina Beach?"),
        ("Bus route stops", "List stops on bus route 102"),
        ("Published fare", "What is the deluxe bus fare for stage 4?"),
    ]
    hi, hinglish = module.examples("hi"), module.examples("hinglish")
    assert len(hi) == len(hinglish) == 3
    assert "Marina Beach" in hi[0][1] and "102" in hi[1][1] and "4" in hi[2][1]
    assert any("\u0900" <= char <= "\u097f" for char in hi[0][1])
    assert all(not any("\u0900" <= char <= "\u097f" for char in query) for _, query in hinglish)
    assert module.examples("unknown") == module.examples("en")


def test_unknown_language_uses_english_and_field_codes_remain_readable():
    module = catalog()
    assert module.tr("Source: {source}", "unknown", source="SOURCE_X") == "Source: SOURCE_X"
    assert module.field_label("point_to_point_route", "en") == "point to point route"
    assert module.field_label("transport_mode", "en") == "transport mode"
    assert module.field_label("lift", "hi") == "लिफ्ट"
    assert module.field_label("Deluxe Services", "en") == "Deluxe Services"
    assert module.field_label("Deluxe Services", "hi") != "Deluxe Services"


@pytest.mark.parametrize("key,want", [
    ("name", "नाम"), ("mode", "माध्यम"), ("source", "स्रोत"),
    ("route_name", "रूट का नाम"), ("time", "समय"), ("sequence", "क्रम"),
    ("distance_m", "दूरी (m)"), ("lift", "लिफ्ट"),
    ("Deluxe Services", "डीलक्स सेवाएँ"), ("min", "मिनट"),
])
def test_ui_exact_header_and_enum_keys_translate_without_changing_english(key, want):
    assert catalog().tr(key, "hi") == want
    assert catalog().tr(key, "en") == key


@pytest.mark.parametrize("operation,data,message,retained", [
    ("PLAN_ROUTE", {"routes": [{"route_name": "Marina Bus Stand 102", "mode": "bus"}]},
     "Published route candidate: Marina Bus Stand 102 (bus). Published route-sequence candidates are available; verify service and transfers before travel. Partial published topology: unusable intermediate links are not verified.",
     ["Marina Bus Stand 102"]),
    ("LIST_ROUTE_STOPS", {"sequences": [{"route_name": "102", "stops": [{"name": "Marina Bus Stand"}, {"name": "Ordinary Services Station"}]}]},
     "102 stops: Marina Bus Stand, Ordinary Services Station. Published stop sequences found. Service operation is not confirmed.",
     ["102", "Marina Bus Stand", "Ordinary Services Station"]),
    ("CHECK_STOP_ON_ROUTE", {"on_route": False},
     "The stop does not appear on the published route sequence. Published route-stop sequence checked; current service is not confirmed.", []),
    ("GET_SERVICE_FREQUENCY", {"median_headway_minutes": 7.5},
     "Published median interval: 7.5 minutes. Median interval estimated from a published timetable, not live service.", ["7.5"]),
    ("GET_SCHEDULED_DEPARTURES", {"departures": [{"route_name": "Blue Line", "time": "25:10:00"}]},
     "Published departures: Blue Line at 25:10:00 (service-day time). Published departures only; times are not live predictions.", ["Blue Line", "25:10:00"]),
    ("GET_ACCESSIBILITY_INFO", {"feature": "lift", "available": False},
     "lift is recorded as unavailable. Recorded accessibility feature; confirm current working status with the operator.", []),
    ("FIND_NEAREST_STATION", {"stops": [{"name": "Marina Bus Stand", "distance_m": 143}]},
     "Nearest by straight line: Marina Bus Stand (143 m). Nearest by straight-line distance only; walking access is not verified.", ["Marina Bus Stand", "143"]),
])
@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_each_backend_factual_prefix_localizes_without_changing_names_or_limits(operation, data, message, retained, language):
    text = catalog().reply_text({"status": "ok", "operation": operation, "data": data, "response_text": message}, language)
    assert "Original explanation" not in text and "मूल विवरण" not in text
    assert text != message
    for value in retained:
        assert value in text
    if operation == "CHECK_STOP_ON_ROUTE":
        assert "नहीं" in text if language == "hi" else "nahi" in text
    if operation == "GET_ACCESSIBILITY_INFO":
        assert "अनुपलब्ध" in text if language == "hi" else "unavailable" in text
    if operation == "PLAN_ROUTE":
        assert "अधूरा" in text if language == "hi" else "partial" in text


KNOWN_EXPLANATIONS = [
    "Please enter a transport question.",
    "Please provide a fare stage number, or the starting and destination stops.",
    "Please clarify which stop or location you mean.", "Please clarify the time or day you mean.",
    "Please clarify the intended time or day.", "Please choose which transport question to answer first.",
    "Please clarify which transport question you mean.", "Please ask one transport question at a time.",
    "Please choose one transport mode for this question.",
    "Please ask about one route, stop, fare stage or time at a time.",
    "Please provide the missing journey information.",
    "Please specify the destination to narrow the departure direction.",
    "Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.",
    "Before-time and time-range requests are not supported by this operation.",
    "The assistant could not process this question. Please try again.",
    "The transport information is unavailable.", "The transport service could not complete the request.",
    "The transport service could not complete this request.", "The transport service returned an invalid state.",
    "Verified transport data is unavailable for this operation.",
    "I can help with Chennai public transport questions.",
    "This assistant covers Chennai public transport questions only.",
    "Live transport status is unavailable; please verify with the operator.",
    "Live transport status is unavailable; verify with the operator.",
    "The canonical transit database could not complete the request.",
    "No mode-consistent published topology is available for the requested transport mode.",
    "No mode-consistent published schedule is available for the requested transport mode.",
    "This snapshot contains no authoritative ticket or pass policy table.",
    "Facility availability is not verified in this snapshot.",
    "No confirmed cross-mode transfer graph is available in this snapshot.",
    "The snapshot has no confirmed interchange records.",
    "The snapshot contains no verified accessibility feature values.",
    "Published route sequences cannot confirm travel at the requested date or time.",
    "Verified optimization for that route preference is unavailable.",
    "No directionally valid published route sequence was found for these stops.",
    "Published route-sequence candidates are available; verify service and transfers before travel.",
    "No mode-consistent published stop sequence is available for that route.",
    "Published stop sequences found. Service operation is not confirmed.",
    "Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.",
    "Route or stop is absent from the canonical snapshot.",
    "The route has no published stop sequence in this snapshot.",
    "Incomplete mode-consistent route coverage cannot establish that the stop is absent.",
    "Published route-stop sequence checked; current service is not confirmed.",
    "First/last service cannot interpret this clock constraint as before, after or at a time.",
    "Too many schedule rows to report a reliable first or last time.",
    "No mode-consistent published schedule was found for this stop.",
    "Published schedule bounds; verify current operation with the operator.",
    "A specific route or line is needed for a meaningful frequency estimate.",
    "Insufficient published departures for a schedule-based frequency estimate.",
    "Specify a destination or unique physical stop to isolate a published departure direction.",
    "Published departures do not support a reliable frequency estimate.",
    "Median interval estimated from a published timetable, not live service.",
    "No mode-consistent published departures were found for this stop.",
    "No published departures were found after the requested time.",
    "Published departures only; times are not live predictions.",
    "Static connectivity cannot confirm operating availability on the requested date or time.",
    "No mode-consistent directional connection is recorded; this does not establish that service is absent.",
    "A published directional connection is recorded; current operation is not confirmed. Verify before travel.",
    "The snapshot does not verify fare rules for that ticket type.",
    "Bus service-class tariffs are unavailable for the requested mode.",
    "The canonical origin-destination fare table covers metro journeys only.",
    "The requested fare type is not verified for a metro origin-destination fare.",
    "The canonical stage fare table covers bus journeys only.",
    "The requested fare or ticket type is not verified for a bus stage fare.",
    "Published fare record found; confirm the current fare before travel.",
    "Published stage fare found; confirm the current fare before travel.",
    "No verified fare record covers the requested journey or stage.",
    "No verified accessibility feature was requested.",
    "That accessibility feature is not recorded in the snapshot.",
    "A single verified physical station is required for accessibility data.",
    "The accessibility record does not verify this feature.",
    "Recorded accessibility feature; confirm current working status with the operator.",
    "No confirmed interchange is available for this location.",
    "The snapshot has no confirmed interchange for this location.",
    "Confirmed interchange records found.",
    "The requested location has no usable canonical coordinates.",
    "No located transport stops match the requested mode.",
    "Nearest by straight-line distance only; walking access is not verified.",
    "The local T3 API is unavailable. Start the API and try again.",
    "The T3 API returned an invalid response.", "The T3 API could not complete this request.",
]


@pytest.mark.parametrize("message", KNOWN_EXPLANATIONS)
@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_known_backend_explanations_have_curated_localized_rendering(message, language):
    text = catalog().reply_text({"status": "unavailable", "response_text": message}, language)
    assert text != message
    assert "Original explanation" not in text and "मूल विवरण" not in text


@pytest.mark.parametrize("language", ["en", "hi", "hinglish"])
def test_unknown_literal_ui_value_with_braces_is_not_treated_as_a_template(language):
    assert catalog().tr("Marina {Bus} Stand", language) == "Marina {Bus} Stand"


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_malformed_optional_fact_data_falls_back_without_changing_original_text(language):
    reply = {"status": "ok", "operation": "LIST_ROUTE_STOPS", "data": {"sequences": [None]},
             "response_text": "Unfamiliar service record: SOURCE_X {unchanged}."}
    assert catalog().reply_text(reply, language).endswith(reply["response_text"])


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_localized_stop_summary_preserves_backend_eight_stop_limit(language):
    stops = [{"name": f"Canonical Stop {index}"} for index in range(9)]
    message = "R102 stops: Canonical Stop 0, Canonical Stop 1, Canonical Stop 2, Canonical Stop 3, Canonical Stop 4, Canonical Stop 5, Canonical Stop 6, Canonical Stop 7, …. Published stop sequences found. Service operation is not confirmed."
    text = catalog().reply_text({"status": "ok", "operation": "LIST_ROUTE_STOPS", "response_text": message,
                                "data": {"sequences": [{"route_name": "R102", "stops": stops}]}}, language)
    assert "Canonical Stop 0" in text and "Canonical Stop 7" in text and "…" in text
    assert "Canonical Stop 8" not in text
    assert "Original explanation" not in text and "मूल विवरण" not in text


@pytest.mark.parametrize("mode", [{"unexpected": "bus"}, ["bus"], None])
@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_contract_valid_route_row_with_nontext_mode_preserves_original_reply(mode, language):
    from app.frontend_contract import valid_reply

    reply = {"status": "ok", "operation": "PLAN_ROUTE", "slots": {},
             "data": {"routes": [{"route_name": "Canonical R102", "mode": mode, "source": "SOURCE_X"}]},
             "response_text": "Published candidates exist; unusual mode metadata needs verification."}
    assert valid_reply(reply)
    before = deepcopy(reply)
    text = catalog().reply_text(reply, language)
    assert text.endswith(reply["response_text"])
    assert reply == before


@pytest.mark.parametrize("mode", [{"unexpected": "bus"}, ["bus"], None])
@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_matching_backend_shaped_prefix_does_not_turn_nontext_mode_into_localized_fact(mode, language):
    reply = {"status": "ok", "operation": "PLAN_ROUTE",
             "data": {"routes": [{"route_name": "Canonical R102", "mode": mode}]},
             "response_text": f"Published route candidate: Canonical R102 ({mode}). Unusual metadata is not verified."}
    text = catalog().reply_text(reply, language)
    assert text.endswith(reply["response_text"])


@pytest.mark.parametrize("value", ["Special {class}", "Lift {A}", "Station {{name}}"])
@pytest.mark.parametrize("language", ["en", "hi", "hinglish"])
def test_literal_braces_in_service_feature_and_canonical_values_survive_lookup(value, language):
    assert catalog().tr(value, language) == value
    assert catalog().field_label(value, language) == value


@pytest.mark.parametrize("language", ["hi", "hinglish"])
def test_factual_service_and_feature_values_with_braces_are_preserved(language):
    fare = {"status": "ok", "operation": "CALCULATE_FARE",
            "data": {"amount": 17, "currency": "INR", "service_type": "Special {class}", "effective_date": "2018-01-29"},
            "response_text": "Published fare (Special {class}): INR 17 (record effective 2018-01-29). Published fare record found; confirm the current fare before travel."}
    feature = {"status": "ok", "operation": "GET_ACCESSIBILITY_INFO",
               "data": {"feature": "Lift {A}", "available": False},
               "response_text": "Lift {A} is recorded as unavailable. Recorded accessibility feature; confirm current working status with the operator."}
    assert "Special {class}" in catalog().reply_text(fare, language)
    assert "Lift {A}" in catalog().reply_text(feature, language)
