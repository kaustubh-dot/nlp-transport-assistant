"""Independently authored product QA; no prediction or corpus imports."""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
OPS = {
    'point_to_point_route': 'PLAN_ROUTE', 'multimodal_route': 'PLAN_MULTIMODAL_ROUTE',
    'route_stop_sequence': 'LIST_ROUTE_STOPS', 'route_stop_membership': 'CHECK_STOP_ON_ROUTE',
    'first_and_last_service': 'GET_FIRST_LAST_SERVICE', 'service_frequency': 'GET_SERVICE_FREQUENCY',
    'scheduled_departure': 'GET_SCHEDULED_DEPARTURES', 'mode_availability': 'CHECK_SERVICE_AVAILABILITY',
    'fare_calculation': 'CALCULATE_FARE', 'ticketing_and_passes': 'GET_TICKETING_POLICY',
    'station_facilities': 'GET_STATION_FACILITY', 'station_accessibility': 'GET_ACCESSIBILITY_INFO',
    'interchange_transfer': 'GET_INTERCHANGE_DETAILS', 'nearest_transport': 'FIND_NEAREST_STATION',
    'realtime_status_query': 'REJECT_UNSUPPORTED_REALTIME', 'out_of_scope': 'REJECT_OUT_OF_SCOPE',
}
C = []
def add(intent, query, slots=None, kind='colloquial', behavior=None, guard=False):
    C.append(dict(id=f'HG200_{len(C)+1:03}', query=query, expected_intent=intent,
                  expected_operation=None if guard else OPS.get(intent), expected_slots=slots or {},
                  test_type=kind, expected_behavior=behavior))

# 001-012: Single-mode journey goals, not questions about timetable or route membership.
I='point_to_point_route'
add(I, 'Vadapalani metro se Teynampet metro pahunchne ka tareeka samjha do yaar', {'transport_mode':'metro'}, behavior='Preserve Vadapalani origin and Teynampet destination; return only source-backed metro journey information or a precise source limitation.')
add(I, 'Mujhe Alandur se High Court sirf metro me jaana hai, kaise jaun?', {'transport_mode':'metro'}, 'single_mode_constraint', 'Preserve both endpoints and metro-only constraint; do not silently substitute bus.')
add(I, 'Broadway se Adyar bus se kaun sa raasta pakdu, ticket rate nahi pooch raha', {'transport_mode':'bus'}, 'negated_distractor', 'Plan bus travel, not fare; any published directional route evidence must carry its source/provisional caveat.')
add(I, 'Airport metro tk jana h, starting jagah main bhool gaya likhna', {'transport_mode':'metro'}, 'missing_origin', 'Ask for the absent origin instead of guessing the current location.')
add(I, 'Egmore metro se nikalunga; kidhar jana hai abhi nahi bataya, route help chahiye', {'transport_mode':'metro'}, 'missing_destination', 'Ask for destination and preserve the supplied origin.')
add(I, 'Guindy se Chennai Central metro rasta dikha, change jitna kam ho utna better', {'transport_mode':'metro','preference':'least_transfers'}, 'preference', 'Retain least-transfer preference; report inability to honor it if the route service cannot optimize.')
add(I, 'Poonamallee Bus Terminus se CMBT ka bus rasta bta sakte ho?', {'transport_mode':'bus'}, 'spelling_variant', 'Preserve two bus journey endpoints; give directional sourced connection evidence or a limitation.')
add(I, 'Ashok Nagar metro se Saidapet metro jaane ka quickest route kya padega?', {'transport_mode':'metro','preference':'fastest'}, 'optimization_constraint', 'Do not ignore quickest constraint or invent a travel-time optimum.')
add(I, 'Anna Nagar Tower metro se Airport jana hai via Alandur metro, poora route batana', {'transport_mode':'metro'}, 'waypoint', 'Retain Alandur as an intermediate waypoint and Airport as destination; clarify or limit if waypoint routing is unsupported.')
add(I, 'Nandanam metro se LIC metro direct hi jaana hai, interchange avoid karna', {'transport_mode':'metro','preference':'direct_only'}, 'constraint_negation', 'Preserve direct-only restriction; do not present an interchange journey as fulfillment.')
add(I, 'Local train se Tambaram to Chennai Beach kaise niklu, pura safar bata do', {'transport_mode':'suburban_rail'}, 'mixed_english', 'Recognize local-train journey planning; preserve Tambaram to Chennai Beach direction.')
add(I, 'Thirumangalam metro se Nehru Park metro ka raasta chahiye, bus bilkul nahi', {'transport_mode':'metro'}, 'excluded_mode', 'Plan the explicitly requested metro journey and honor exclusion of bus.')

# 013-024: Explicit journeys combining modes.
I='multimodal_route'
add(I, 'Tambaram se Anna Nagar jana h, pehle local fir metro ka combo batao', {}, 'mode_chain', 'Recognize an explicit suburban-rail then metro journey; do not claim verified multimodal routing without confirmed transfer evidence.')
add(I, 'Velachery se High Court bus aur metro mila ke kaise pahuchu?', {}, 'mixed_modes', 'Retain both endpoints and combined bus/metro request; report source limits if no verified itinerary can be built.')
add(I, 'Avadi se Airport ka route chahiye local train plus metro me, steps me samjhao', {}, 'mode_chain', 'Recognize multimodal route rather than an interchange-only or fare goal.')
add(I, 'Mylapore se Koyambedu bus se nikal kar metro change karu to kya journey banegi?', {}, 'colloquial', 'Preserve Mylapore origin, Koyambedu destination and requested bus/metro combination.')
add(I, 'Bus aur metro dono use kar lunga, destination Teynampet hai; start kaha se bolna bhool gaya', {}, 'missing_origin', 'Ask for starting point for the combined-mode journey.')
add(I, 'Chromepet se bus+metro travel karna hai, destination likha hi nahi maine', {}, 'missing_destination', 'Ask for destination and do not invent a second endpoint.')
add(I, 'Guindy se Washermenpet tak metro ke saath bus connect karke sabse sasta way?', {'preference':'cheapest'}, 'optimization_constraint', 'Retain cheapest multimodal preference; do not present an unoptimized partial connection as cheapest.')
add(I, 'Perambur se Chennai Airport local aur metro se jaana hai, Central hote hue', {}, 'waypoint', 'Retain Central waypoint and Airport destination with explicit multimodal request; unsupported constraint requires limitation or clarification.')
add(I, 'Thiruvanmiyur se Egmore, MRTS utar ke bus lena chahta hu; travel chain bta', {}, 'mode_chain', 'Recognize MRTS/bus journey planning rather than service availability.')
add(I, 'Bus se metro pakad ke Marina Beach jana h from Porur, shortest plan milega?', {'preference':'fastest'}, 'mixed_english', 'Preserve requested mode chain and optimization; do not invent confirmed walking legs.')
add(I, 'Sirf metro nahi, Ambattur se Saidapet bus bhi jodna padega; route explain karo', {}, 'negation', 'Do not read negated metro-only phrase as a single-mode route; preserve combined-mode goal.')
add(I, 'Kya tum local aur bus ka combined journey Chennai Beach se Madipakkam ke liye samjha sakte ho?', {}, 'indirect_request', 'Interpret the modal phrasing as a request for an itinerary, retaining both travel modes.')

# 025-036: Ordered stop lists and route-code normalization contrasts.
I='route_stop_sequence'
add(I, '570S bus ka start se end tk har stop naam order me likh do', {'route_number':'570S','transport_mode':'bus'}, 'suffix', 'List sourced ordered stop sequences for 570S without truncating its S suffix; disclose incomplete variants.')
add(I, '21 G bus raste me konse-konse stops leti hai? bas poori list chahiye', {'route_number':'21G','transport_mode':'bus'}, 'split_suffix', 'Normalize separated route suffix while retaining 21G and list its sequence.')
add(I, '102-A bus ke saare stoppage ek ek krke btao', {'route_number':'102A','transport_mode':'bus'}, 'hyphen_suffix', 'Retain route 102A after delimiter normalization; do not return 102 as an equivalent.')
add(I, 'Blue Line metro me stations ka sequence first se last kya hai?', {'line_name':'Blue Line','transport_mode':'metro'}, 'line_sequence', 'Return only sourced Blue Line ordered topology or the matching source limitation.')
add(I, 'Green Line wali metro kahan kahan rukti h, station order bhejo', {'line_name':'Green Line','transport_mode':'metro'}, 'roman_spelling', 'Recognize ordered Green Line stations, not journey planning or live status.')
add(I, 'Bus no 29C ke poore stop chain dikha do; kiraya nahi chahiye', {'route_number':'29C','transport_mode':'bus'}, 'negated_distractor', 'List 29C stops and ignore explicitly negated fare goal.')
add(I, 'M1 bus ka route-stop list nikal doge?', {'route_number':'M1','transport_mode':'bus'}, 'alphanumeric_prefix', 'Preserve M1 as the route code rather than dropping the letter.')
add(I, '१०२A bus kaha kaha rukti hai, ordered list chahiye mujhe', {'route_number':'102A','transport_mode':'bus'}, 'native_digit_contrast', 'Normalize Devanagari route numerals to 102A while preserving the suffix.')
add(I, '२५R ki stops wali list do, bus number Hindi digits me likha hai', {'route_number':'25R','transport_mode':'bus'}, 'native_digit_contrast', 'Preserve 25R route identity after digit normalization; do not ask for an already supplied route.')
add(I, 'Ek bus ka saara stops sequence jaana hai, number abhi mere paas nahi', {'transport_mode':'bus'}, 'missing_route', 'Ask for route number or line name; do not pick a default bus.')
add(I, '102K# ka stop order kya hai? hash wala variant hi batana', {'route_number':'102K#'}, 'express_variant', 'Keep the meaningful # suffix and do not answer another route variant.')
add(I, 'Bus route 27D me dono direction ke stop order alag hote to dono dikhao', {'route_number':'27D','transport_mode':'bus'}, 'directional_variants', 'Return separate sourced directional sequences with provisional/completeness qualifications.')

# 037-048: A single named stop membership goal.
I='route_stop_membership'
add(I, '29C bus T Nagar par rukti hai ya bypass kar deti h?', {'route_number':'29C','transport_mode':'bus'}, behavior='Check the requested stop on 29C; negative membership requires complete consistent route evidence.')
add(I, '21G bus me Guindy stop aata h kya bhai?', {'route_number':'21G','transport_mode':'bus'}, 'roman_spelling', 'Recognize membership, retain Guindy stop and 21G route; ambiguity may require an explicit stop choice.')
add(I, '102A me Adyar included hai ki nahi, sirf ye confirm karna', {'route_number':'102A'}, 'suffix', 'Check Adyar membership on exactly 102A; do not give full route advice.')
add(I, '570 S bus Sholinganallur pe halt karti hai?', {'route_number':'570S','transport_mode':'bus'}, 'split_suffix', 'Normalize route suffix and check Sholinganallur membership without inferring current running service.')
add(I, 'Green Line me Guindy station padta hai kya?', {'line_name':'Green Line'}, 'line_membership', 'Check the named station against Green Line topology; do not assume membership from location alone.')
add(I, 'Blue Line ke stops me Egmore bhi hai kya?', {'line_name':'Blue Line'}, 'line_membership', 'Recognize one-station line membership rather than nearest or route planning.')
add(I, '२१G bus Saidapet par rukti hai kya? Hindi digits ko bus number samjho', {'route_number':'21G','transport_mode':'bus'}, 'native_digit_contrast', 'Interpret २१G as 21G route and preserve Saidapet stop.')
add(I, '१०२-C Thiruvanmiyur cover karti h kya?', {'route_number':'102C'}, 'native_digit_suffix', 'Normalize native digits and hyphen, preserve C suffix and stop scope.')
add(I, 'Guindy par ye bus rukti h kya, route number main abhi nahi de sakta', {'transport_mode':'bus'}, 'missing_route', 'Request the missing route identifier while retaining the named stop.')
add(I, 'Bus 25R kisi stop par rukti hai kya? stop ka naam nahi likha maine', {'route_number':'25R','transport_mode':'bus'}, 'missing_stop', 'Ask which stop should be checked instead of returning arbitrary membership.')
add(I, '27D Ashok Pillar se guzarti hai? timing nahi, stop confirm chahiye', {'route_number':'27D'}, 'negated_distractor', 'Check stop coverage only; do not answer a timing question.')
add(I, '102K# Kannagi Nagar pe rukne wali variant hai na, stop record check karo', {'route_number':'102K#'}, 'express_variant', 'Check source-backed membership for the exact # variant and clarify ambiguous stop aliases.')

# 049-060: Boundary services, with missing/ambiguous/unsupported temporal shapes.
I='first_and_last_service'
add(I, 'Guindy metro se roz sabse pehli train kitne baje nikalti hai?', {'transport_mode':'metro','timing_type':'first'}, behavior='Recognize first-service goal; current production has no valid metro timetable, so give a source-specific limitation.')
add(I, 'Poonamallee Bus Terminus se 25R ki aakhri bus ka schedule time?', {'route_number':'25R','transport_mode':'bus','timing_type':'last'}, 'scheduled_boundary', 'Use published route/physical-stop service bounds if unambiguous; distinguish schedule from live departure.')
add(I, 'Chennai Beach se Tambaram last local ka time bata dijiye', {'transport_mode':'suburban_rail','timing_type':'last'}, 'polite_roman', 'Retain Chennai Beach origin and Tambaram destination, give source-backed bounds or missing-source limitation.')
add(I, 'CMBT par 27D ka subah wala first trip kab start hota h?', {'route_number':'27D','timing_type':'first'}, 'colloquial', 'Recognize earliest scheduled service for supplied route and station; clarify alias ambiguity only if real.')
add(I, '102 bus Broadway se pehli aur aakhri service ki timings dono de do', {'route_number':'102','transport_mode':'bus'}, 'two_bounds_same_goal', 'Treat first and last bounds as one supported family and preserve Broadway origin.')
add(I, 'First metro kab hai bhai? station ka naam maine nahi diya', {'transport_mode':'metro','timing_type':'first'}, 'missing_station', 'Ask for a station/origin to identify the requested first service.')
add(I, '21G ki last bus ka timing chahiye, kis stop se woh nahi likha', {'route_number':'21G','timing_type':'last'}, 'missing_station', 'Request the missing stop/origin; do not treat the route alone as a particular physical-stop schedule.')
add(I, 'Alandur metro ki aakhri train kal, matlab kis din ki poochu samajh nahi aa raha', {'transport_mode':'metro','timing_type':'last','temporal_relative':'kal'}, 'ambiguous_day', 'Ask whether kal means yesterday or tomorrow; do not default the date or execute a dated timetable.', True)
add(I, 'Last bus from Broadway raat 10 baje ke baad kab hogi, route 102 hai', {'route_number':'102','timing_type':'last','time':'22:00:00'}, 'unsupported_clock_bound', 'Retain clock filter; first/last service with clock constraints must state unsupported scope rather than ignore 22:00.')
add(I, '५७०S ki pehli bus Kelambakkam se kb nikalti h?', {'route_number':'570S','timing_type':'first'}, 'native_digit_contrast', 'Preserve native-numeral route 570S and explicit origin for the first-service query.')
add(I, 'Guindy se Airport ki first metro aaj ka published schedule batao, live nahi', {'transport_mode':'metro','timing_type':'first','temporal_relative':'aaj'}, 'negated_live', 'Recognize static first service despite live word being negated; do not claim unsupported metro timetable.')
add(I, 'Pehli bus Broadway se Adyar ke liye Saidapet hote hue, 21G ka timing?', {'route_number':'21G','transport_mode':'bus','timing_type':'first'}, 'waypoint', 'Preserve Broadway origin, Adyar destination and Saidapet waypoint; explicitly limit unsupported timetable waypoint filtering.')

# 061-072: Scheduled headways, not next live arrival.
I='service_frequency'
add(I, '25R Poonamallee Bus Terminus se average kitne minute gap me chalti hai schedule me?', {'route_number':'25R','timing_type':'frequency'}, behavior='Compute only a source-backed single route/direction/physical-stop scheduled headway or request genuine disambiguation.')
add(I, '102 bus Broadway par timetable ke mutabik kitni der der me milti hai?', {'route_number':'102','transport_mode':'bus','timing_type':'frequency'}, 'roman_reduplication', 'Interpret repeated der as headway, not a live countdown.')
add(I, 'Green Line metro Nehru Park pe scheduled frequency kya rehti hai?', {'line_name':'Green Line','transport_mode':'metro','timing_type':'frequency'}, 'line_headway', 'Preserve line and station; refuse missing valid metro schedule instead of inventing frequency.')
add(I, 'Blue Line Guindy station pe trains ka normal interval btao', {'line_name':'Blue Line','timing_type':'frequency'}, 'colloquial', 'Recognize headway goal for Blue Line at Guindy; qualify unsupported source.')
add(I, '21 G buses Saidapet stop se kitne-kitne min ke gap pe hain?', {'route_number':'21G','timing_type':'frequency'}, 'split_suffix', 'Retain 21G identifier and requested physical stop; do not mix schedule directions.')
add(I, '१०२A Broadway pe kitni der ke antaral me scheduled bus deti hai?', {'route_number':'102A','transport_mode':'bus','timing_type':'frequency'}, 'native_digit_contrast', 'Normalize native digits with A suffix and retain headway family.')
add(I, 'Bus frequency janna h at CMBT, route ka number nahi malum', {'transport_mode':'bus','timing_type':'frequency'}, 'missing_route', 'Ask which route/line; do not average unrelated routes together.')
add(I, '27D ka average gap batao, stop ka naam main bhool gaya', {'route_number':'27D','timing_type':'frequency'}, 'missing_station', 'Ask for the missing physical stop or origin instead of selecting a schedule group arbitrarily.')
add(I, '570S Kelambakkam se timetable gap kya hai, aaj live wait nahi pooch rha', {'route_number':'570S','timing_type':'frequency'}, 'negated_live', 'Recognize scheduled frequency despite negated live wait wording.')
add(I, 'M1 Thiruvanmiyur se evening me kitne minute par ek bus scheduled hoti h?', {'route_number':'M1','transport_mode':'bus','timing_type':'frequency'}, 'period_constraint', 'Honor requested evening scope if represented; otherwise explicitly disclose unsupported period filtering rather than claim it.')
add(I, '102 Broadway se Adyar via Guindy buses ka schedule interval kya h?', {'route_number':'102','timing_type':'frequency'}, 'waypoint', 'Preserve endpoints and via Guindy; unsupported frequency waypoint filtering must be limited before partial execution.')
add(I, '25R ka Poonamallee Bus Terminus pe kal ka frequency schedule', {'route_number':'25R','timing_type':'frequency','temporal_relative':'kal'}, 'ambiguous_day', 'Ask whether kal is yesterday or tomorrow instead of choosing a date.', True)

# 073-084: Departures with explicit clocks; temporal malformed and ambiguity safeguards.
I='scheduled_departure'
add(I, 'Poonamallee Bus Terminus se subah 7:15 baje ke baad departures dikhao', {'time':'07:15:00'}, 'explicit_am', 'Return only published departures at/after 07:15 for requested stop, qualified as static schedule.')
add(I, 'Bus 25R Poonamallee Bus Terminus se 18:40 par scheduled departure list milegi?', {'route_number':'25R','transport_mode':'bus','time':'18:40:00'}, '24h_clock', 'Retain route, origin and explicit 24-hour clock; do not convert it into live ETA.')
add(I, 'Broadway pe 102 ke 9:30 AM se aage wale timetable departures bta do', {'route_number':'102','time':'09:30:00'}, 'explicit_am', 'Filter published departures at/after the explicit AM clock, subject to genuine physical-stop ambiguity.')
add(I, 'Guindy metro ka timetable shaam 6:20 ke baad chahiye mujhe', {'transport_mode':'metro','time':'18:20:00'}, 'hindi_daypart', 'Recognize departures and preserve evening clock; explicitly report invalid/missing metro timetable source.')
add(I, '२१G bus Saidapet se रात ९:१० baje ka schedule dikhana', {'route_number':'21G','transport_mode':'bus','time':'21:10:00'}, 'native_digit_mixed_script', 'Normalize native route/time digits with the explicit night daypart; preserve Saidapet station scope.')
add(I, 'Departures batao 6 PM par, station maine mention nahi kiya', {'time':'18:00:00'}, 'missing_station', 'Ask which station/stop instead of picking a transit node.')
add(I, 'Poonamallee Bus Terminus pe bus schedule 9 baje wala chahiye', {'transport_mode':'bus'}, 'ambiguous_clock', 'Ask AM or PM for bare 9 baje; no silent morning default.', True)
add(I, 'CMBT se departure 26:75 pe kab hai? typo lag raha par check karo', {}, 'invalid_clock', 'Reject/clarify invalid clock without removing it and answering an unconstrained timetable.', True)
add(I, 'Poonamallee Bus Terminus se 25R departures kal ka schedule dikhao', {'route_number':'25R','temporal_relative':'kal'}, 'ambiguous_day', 'Clarify ambiguous kal before schedule execution; never assume tomorrow.', True)
add(I, 'Broadway se Adyar via Guindy, 102 ke 08:15 AM departures chahiye', {'route_number':'102','time':'08:15:00'}, 'waypoint', 'Retain all three location roles; explain unsupported timetable waypoint filter rather than drop Guindy.')
add(I, '25R Poonamallee Bus Terminus se 5 PM se pehle ki departure list do', {'route_number':'25R','time':'17:00:00'}, 'unsupported_before_filter', 'Preserve before constraint and state unsupported query shape; do not return at/after 17:00 as fulfillment.')
add(I, 'CMBT pe 27D departures 14:05 ka published chart, current arrival mat bta', {'route_number':'27D','time':'14:05:00'}, 'negated_live', 'Use static departures at explicit clock; do not misread negated current-arrival language as realtime.')

# 085-096: Connectivity existence, not full itinerary.
I='mode_availability'
add(I, 'Saidapet se Guindy direct bus service hai bhi ya nahi?', {'transport_mode':'bus'}, behavior='Check sourced service connectivity; negative availability cannot be proven from partial topology.')
add(I, 'Alandur aur Airport ke beech metro chalti h kya?', {'transport_mode':'metro'}, 'existence', 'Recognize connectivity existence without treating it as a route instruction request.')
add(I, 'Tambaram se Chennai Beach local train milti hai kya generally?', {'transport_mode':'suburban_rail'}, 'colloquial', 'Check only published suburban connectivity, distinguishing static evidence from current service.')
add(I, 'Velachery to Thirumayilai MRTS connection available hai?', {'transport_mode':'mrts'}, 'mixed_english', 'Preserve MRTS mode and endpoints; do not replace with other modes silently.')
add(I, 'Porur se CMBT bus aati jaati hai ki route hi nahi hai?', {'transport_mode':'bus'}, 'existence_negation', 'Recognize bus availability and avoid a definite no from incomplete records.')
add(I, 'Nehru Park se Anna Nagar Tower metro connection hoga na?', {'transport_mode':'metro'}, 'informal', 'Recognize mode connectivity rather than fare or nearest transport.')
add(I, 'Airport ke liye bus service h kya? meri starting locality nahi di', {'transport_mode':'bus'}, 'missing_origin', 'Ask for origin while retaining Airport destination.')
add(I, 'Pallavaram se local available h kya, destination batana reh gaya', {'transport_mode':'suburban_rail'}, 'missing_destination', 'Request the missing destination rather than check generic station existence.')
add(I, 'Guindy se Central metro connection check karo, route directions abhi nahi chahiye', {'transport_mode':'metro'}, 'negated_distractor', 'Answer connectivity/source scope only; route instructions are explicitly not requested.')
add(I, 'Broadway se Adyar bus kal chalti hai kya, future trip plan kar raha hu', {'transport_mode':'bus'}, 'dated_availability', 'Recognize future-oriented connectivity goal; current/dated bus trip availability requires an explicit limitation, not topology proof.')
add(I, 'Guindy se Airport aaj 11 PM metro available hai kya?', {'transport_mode':'metro','time':'23:00:00','temporal_relative':'aaj'}, 'time_specific_availability', 'Retain time/day availability constraints; no valid metro timetable means a source limitation instead of claiming operation today.')
add(I, 'Chennai Beach se Tambaram sirf local train hai kya, bus ki availability mat ginna', {'transport_mode':'suburban_rail'}, 'excluded_mode', 'Check the explicitly requested local mode and preserve excluded bus constraint.')

# 097-108: Numeric fare stage and point-pair, with class/scope guards elsewhere.
I='fare_calculation'
add(I, 'Ordinary MTC bus stage 6 ka kiraya kitna baithega?', {'transport_mode':'bus','stage_number':6,'service_type':'Ordinary Services'}, 'stage_fare', 'Return the sourced dated Ordinary stage-6 tariff if present; disclose effective date and source.')
add(I, 'Express service me 11 stages ka ticket amount bta do', {'stage_number':11,'service_type':'Express Services'}, 'service_class', 'Use exactly Express stage-11 tariff; no silent substitution with Ordinary.')
add(I, 'Deluxe bus ka 8 stage fare kya hai bhai?', {'transport_mode':'bus','stage_number':8,'service_type':'Deluxe Services'}, 'service_class', 'Return the sourced dated Deluxe stage-8 amount if available.')
add(I, 'Night service stage 3 ke paise kitne lagenge?', {'stage_number':3,'service_type':'Night Services'}, 'service_class', 'Honor Night tariff class; disclose lack of requested class if source absent.')
add(I, 'AC bus me stage 7 ka cost bataoge?', {'transport_mode':'bus','stage_number':7,'service_type':'Air Conditioned Services'}, 'unsupported_class_source', 'Do not substitute an available non-AC tariff for the requested AC class.')
add(I, 'Ordinary bus me ६ stage ka किराया kitna h?', {'transport_mode':'bus','stage_number':6,'service_type':'Ordinary Services'}, 'native_digit_contrast', 'Normalize Devanagari stage ६ to 6 and preserve Ordinary class.')
add(I, 'Guindy metro se High Court metro token ticket kitne ka?', {'transport_mode':'metro','ticket_type':'token'}, 'metro_pair', 'Return dated source-backed metro pair token fare or genuine entity ambiguity; do not invent amount.')
add(I, 'Airport se Alandur metro smart card fare kya padega?', {'transport_mode':'metro','ticket_type':'smart_card'}, 'unsupported_discount', 'Retain smart-card request; unverified discount policy must be limited rather than applying a guessed discount.')
add(I, 'Broadway se Adyar bus ka kiraya nikal do, stage ka mujhe nahi pata', {'transport_mode':'bus'}, 'unsupported_bus_od', 'Explain unsupported bus OD stage arithmetic; do not invent fare from a guessed stage delta.')
add(I, 'Bus fare kitna hai? start end dono nahi diye aur stage bhi nahi', {'transport_mode':'bus'}, 'missing_fare_scope', 'Ask for origin/destination pair or fare stage.')
add(I, 'MTC stage 12 ka amount chahiye, bus class specify nahi ki maine', {'transport_mode':'bus','stage_number':12}, 'disclosed_default_class', 'Ordinary default is acceptable only if explicitly disclosed with recorded fare source and date.')
add(I, 'Egmore metro se Central metro ka amount, route mat samjhana abhi', {'transport_mode':'metro'}, 'negated_distractor', 'Recognize fare goal rather than route and return only sourced dated token fare or limitation.')

# 109-120: Policy/source-limited tickets, not fare amount computations.
I='ticketing_and_passes'
add(I, 'Metro smart card recharge ka process kya h, thoda easy samjhao', {'transport_mode':'metro','ticket_type':'smart_card'}, behavior='Recognize recharge policy goal; say authoritative policy source is absent rather than invent steps.')
add(I, 'MTC monthly pass banwane ke rules aur documents kya honge?', {'transport_mode':'bus','ticket_type':'monthly_pass'}, 'policy_requirements', 'Give a source-specific ticket/pass policy limitation; do not invent requirements.')
add(I, 'NCMC card Chennai metro me use karne ka niyam bata do', {'transport_mode':'metro','ticket_type':'ncmc_card'}, 'policy_usage', 'Retain NCMC policy goal; no unverified acceptance assertion.')
add(I, 'QR ticket ka validity rule kya rehta h metro me?', {'transport_mode':'metro','ticket_type':'qr_ticket'}, 'policy_validity', 'Do not invent QR expiry or refund policy without authoritative source.')
add(I, 'Token ticket return ho sakta hai kya? metro wala pooch raha hu', {'transport_mode':'metro','ticket_type':'token'}, 'policy_refund', 'Recognize token refund policy, distinguish it from token fare calculation.')
add(I, 'Suburban season pass renew kaise hota hai, rule batao', {'transport_mode':'suburban_rail','ticket_type':'season_pass'}, 'policy_renewal', 'Retain suburban season-pass policy question and report missing source.')
add(I, 'Tourist pass lena ho to kya conditions hoti hain Chennai metro me?', {'transport_mode':'metro','ticket_type':'tourist_pass'}, 'policy_conditions', 'No fabricated tourist-pass availability/conditions; source limitation is appropriate.')
add(I, 'Monthly pass kisi aur ko deke travel karwa sakte hai kya?', {'ticket_type':'monthly_pass'}, 'policy_transferability', 'Recognize pass transferability policy without inventing an authoritative rule.')
add(I, 'Bus monthly pass ke rules bolna, per ride kiraya nahi puch raha', {'transport_mode':'bus','ticket_type':'monthly_pass'}, 'negated_fare', 'Choose ticket/pass policy despite explicit negated fare distractor.')
add(I, 'Metro smartcard kho gayi to replace ka process kya rahega?', {'transport_mode':'metro','ticket_type':'smart_card'}, 'roman_spelling', 'Recognize replacement policy and report no verified policy data.')
add(I, 'Chennai local ka season pass online apply karne ka tarika?', {'transport_mode':'suburban_rail','ticket_type':'season_pass'}, 'mixed_english', 'Do not invent booking links or application flow; report policy-source limit.')
add(I, 'Ticket policy help chahiye, QR ticket ko cancel karna ho to?', {'ticket_type':'qr_ticket'}, 'policy_cancellation', 'Recognize ticket policy with unspecified mode; clarify mode if necessary or state missing policy source.')

# 121-132: Source-limited amenities, including absent station and negation.
I='station_facilities'
add(I, 'Nandanam metro pe bike parking ki suvidha hai kya?', {'transport_mode':'metro','facility_type':'parking'}, behavior='Recognize parking amenity; unverified facility source must be disclosed instead of asserting availability.')
add(I, 'Guindy metro me paani peene ka point milta hai?', {'transport_mode':'metro','facility_type':'drinking_water'}, 'colloquial_facility', 'Recognize drinking-water facility and explain no verified amenity inventory.')
add(I, 'Egmore station par cloak room h kya luggage rakhne ke liye?', {'facility_type':'cloak_room'}, 'amenity_purpose', 'Recognize cloak-room facility, not route or accessibility; do not claim unsupported storage.')
add(I, 'High Court metro me ATM mil jayega kya?', {'transport_mode':'metro','facility_type':'atm'}, 'mixed_english', 'Give specific absence of verified ATM records rather than assert yes/no.')
add(I, 'Vadapalani metro pe toilet facility ka info chahiye', {'transport_mode':'metro','facility_type':'restroom'}, 'facility_synonym', 'Recognize general restroom facility; do not conflate with accessible toilet request.')
add(I, 'Chennai Central metro me free wifi hai kya yaar?', {'transport_mode':'metro','facility_type':'wifi'}, 'colloquial', 'Recognize Wi-Fi facility and state missing verified source without inventing service.')
add(I, 'CMBT bus stand me waiting room ka record hai?', {'transport_mode':'bus','facility_type':'waiting_room'}, 'bus_facility', 'Source-limited facility goal remains in station_facilities even for bus station.')
add(I, 'Parking kaha hai station pe? station ka naam main nahi bol paya', {'facility_type':'parking'}, 'missing_station', 'Ask which station instead of assuming a nearby/current one.')
add(I, 'Metro station me drinking water h kya, kaunsa station nahi likha', {'transport_mode':'metro','facility_type':'drinking_water'}, 'missing_station', 'Request station for the supplied drinking-water amenity.')
add(I, 'Alandur metro me parking pooch raha hu, lift nahi', {'transport_mode':'metro','facility_type':'parking'}, 'negated_accessibility', 'Recognize parking only; negated lift does not create an accessibility goal.')
add(I, 'Saidapet metro par washroom ka available data bataiye', {'transport_mode':'metro','facility_type':'restroom'}, 'polite_roman', 'Retain station and requested restroom; respond with source-qualified information or limitation.')
add(I, 'Tambaram railway station me waiting hall hai ki nahi?', {'transport_mode':'suburban_rail','facility_type':'waiting_room'}, 'local_station_facility', 'Do not mistake railway station amenity for intercity out-of-scope; report absent facility inventory.')

# 133-144: Assistive access as distinct from amenities and general mobility.
I='station_accessibility'
add(I, 'Guindy metro pe wheelchair access ka record btao', {'transport_mode':'metro','accessibility_feature':'wheelchair'}, behavior='Recognize wheelchair accessibility; canonical values are null, so do not assert availability.')
add(I, 'Alandur metro me lift lagi hai kya, stairs mushkil hain mere liye', {'transport_mode':'metro','accessibility_feature':'lift'}, 'assistive_context', 'Recognize lift feature and source limitation; do not infer from generic station facts.')
add(I, 'Airport metro station pe ramp available hai wheelchair ke liye?', {'transport_mode':'metro','accessibility_feature':'ramp'}, 'assistive_context', 'Retain explicitly asked ramp and avoid inventing accessibility status.')
add(I, 'Nehru Park metro me escalator ka verified info h kya?', {'transport_mode':'metro','accessibility_feature':'escalator'}, 'verified_source_request', 'Recognize escalator accessibility; no availability claim without verified record.')
add(I, 'Central metro me accessible toilet ka status kya hai?', {'transport_mode':'metro','accessibility_feature':'accessible_toilet'}, 'specific_assistive_feature', 'Distinguish accessible toilet from general restroom facility and state missing verification.')
add(I, 'Blind passengers ke liye Vadapalani metro me tactile paths hain?', {'transport_mode':'metro','accessibility_feature':'tactile_paths'}, 'assistive_context', 'Recognize tactile-path accessibility, not general facility or route advice.')
add(I, 'Tambaram local station par ramp ka data mil sakta h?', {'transport_mode':'suburban_rail','accessibility_feature':'ramp'}, 'nonmetro_source_limit', 'State absent suburban accessibility records; do not invent a negative or positive feature value.')
add(I, 'CMBT bus stand wheelchair friendly hai kya?', {'transport_mode':'bus','accessibility_feature':'wheelchair'}, 'nonmetro_source_limit', 'Recognize accessibility despite bus stand; specify missing bus accessibility source.')
add(I, 'Lift ka status batao please, kis station ki woh bolna reh gaya', {'accessibility_feature':'lift'}, 'missing_station', 'Ask which station while preserving lift feature.')
add(I, 'Metro me accessible toilet chahiye, station naam abhi nahi diya', {'transport_mode':'metro','accessibility_feature':'accessible_toilet'}, 'missing_station', 'Request missing station without guessing a physical node.')
add(I, 'High Court metro pe lift ka info chahiye, parking nahi', {'transport_mode':'metro','accessibility_feature':'lift'}, 'negated_facility', 'Recognize lift accessibility while ignoring explicitly negated parking.')
add(I, 'Saidapet metro me chalne me dikkat wale passenger ke liye accessibility kya hai?', {'transport_mode':'metro'}, 'general_accessibility', 'Recognize overall assistive-access goal and source limitation; do not invent a default specific feature.')

# 145-156: Transfers, no fabricated gates or walking paths.
I='interchange_transfer'
add(I, 'Central par metro se local train switch karne ka interchange info?', {'mode_from':'metro','mode_to':'suburban_rail'}, behavior='Recognize metro-to-suburban transfer; unconfirmed hub/transfer records cannot prove a verified connection.')
add(I, 'Guindy me local se metro badalne ka tarika btao, station transfer wala', {'mode_from':'suburban_rail','mode_to':'metro'}, 'mode_direction', 'Preserve source/destination mode order; give source-specific transfer limitation without inventing a path.')
add(I, 'Alandur pe Blue Line se Green Line interchange kaisa hota hai?', {'transport_mode':'metro'}, 'line_transfer', 'Recognize intra-metro interchange as transfer goal, not full endpoint journey.')
add(I, 'CMBT me bus se metro connect karna ho to transfer info milega?', {'mode_from':'bus','mode_to':'metro'}, 'mode_direction', 'Recognize bus-to-metro transfer at CMBT; only confirmed evidence may support walking instruction.')
add(I, 'St Thomas Mount metro se suburban platform jana, connection kaise?', {'mode_from':'metro','mode_to':'suburban_rail'}, 'platform_source_limit', 'Recognize transfer while explicitly limiting absent platform/gate/verified-walking data.')
add(I, 'Metro se bus interchange possible hai kya? station main mention nahi kar raha', {'mode_from':'metro','mode_to':'bus'}, 'mode_pair_only', 'Treat supplied mode pair as recognized transfer scope; avoid claiming a specific unmentioned station.')
add(I, 'Train badalni hai, interchange help chahiye par kaunse station pe nahi bataya', {}, 'missing_transfer_scope', 'Ask for station or from/to modes before a transfer operation.')
add(I, 'High Court metro se bus stop tak paidal transfer ka info chahiye', {'mode_from':'metro','mode_to':'bus'}, 'walking_transfer', 'Do not invent a verified walking route from geometric/candidate transfer evidence.')
add(I, 'Chennai Beach local se MRTS switch ho sakta hai, transfer data?', {'mode_from':'suburban_rail','mode_to':'mrts'}, 'rail_mode_pair', 'Recognize suburban-to-MRTS transfer and disclose source confirmation limits.')
add(I, 'Guindy bus stand se metro pakadne ke liye badalna kahan padega?', {'mode_from':'bus','mode_to':'metro'}, 'colloquial', 'Treat as local transfer query with Guindy context rather than nearest transport.')
add(I, 'Central metro me line change ka info, fare nahi chahiye abhi', {'transport_mode':'metro'}, 'negated_fare', 'Recognize line transfer and ignore explicitly negated fare request.')
add(I, 'Koyambedu par bus utar ke metro chadhne ka walking connection verified hai?', {'mode_from':'bus','mode_to':'metro'}, 'verified_source_request', 'Answer evidence status honestly; do not describe unverified interchange as confirmed.')

# 157-168: Spatial nearest, no current location, walking or mode substitution.
I='nearest_transport'
add(I, 'Marina Beach ke sabse kareeb metro station konsa h?', {'transport_mode':'metro'}, behavior='Find geometric nearest requested-mode stop from canonical Marina Beach coordinates; include straight-line/walking caveat.')
add(I, 'IIT Madras ke aas paas nearest bus stop ka naam btao', {'transport_mode':'bus'}, 'landmark', 'Find nearest bus stop to the explicit landmark; do not silently return metro.')
add(I, 'Apollo Hospital ke closest metro ka coordinate distance chahiye', {'transport_mode':'metro'}, 'geometric_distance', 'Recognize geometric nearest request and state source/distance basis.')
add(I, 'T Nagar me sabse paas wala local train station dhund do', {'transport_mode':'suburban_rail'}, 'locality', 'Use T Nagar reference and local-train mode; clarify genuine locality aliases rather than infer user coordinates.')
add(I, 'Besant Nagar ke near bus stop milega? sabse nazdeek ka', {'transport_mode':'bus'}, 'mixed_english', 'Recognize proximity despite milega phrasing, not a point-to-point bus route.')
add(I, 'Mylapore ke najdeek MRTS station bata sakte ho?', {'transport_mode':'mrts'}, 'roman_spelling', 'Preserve explicitly requested MRTS mode in spatial result.')
add(I, 'Nearest metro station kaunsa hai? meri location aapko di nahi', {'transport_mode':'metro'}, 'missing_location', 'Request landmark/locality because user location is absent; do not infer GPS.')
add(I, 'Paas ka bus stop bata na, aas paas kis jagah ki woh abhi nahi bataya', {'transport_mode':'bus'}, 'missing_location', 'Ask for reference location, preserving bus mode.')
add(I, 'Anna Nagar Tower metro ke closest bus stop kaun sa padega?', {'transport_mode':'bus'}, 'stop_as_reference', 'Use the named metro station as reference point, while returning only bus candidates.')
add(I, 'Marina Beach ke paas metro chahiye, bus stop nahi', {'transport_mode':'metro'}, 'negated_mode', 'Honor requested metro and excluded bus; no mixed-mode nearest response.')
add(I, 'Fort St George se sabse kam walking distance wala metro kaunsa?', {'transport_mode':'metro'}, 'unsupported_walk_metric', 'Do not substitute geometric nearest for walking optimum without explicitly stating unsupported pedestrian network metric.')
add(I, 'Thiruvanmiyur ke paas public transport me closest station btao, koi mode fixed nahi', {}, 'unconstrained_mode', 'Find geometric nearest canonical transport stop or clarify reference ambiguity; do not invent mode constraint.')

# 169-180: Live requests require a distinct semantic family and clear source refusal.
I='realtime_status_query'
add(I, 'Bus 25R iss waqt GPS pe kidhar chal rahi h?', {'route_number':'25R','transport_mode':'bus'}, 'live_gps', 'Return realtime source unavailable under the realtime intent; no live vehicle location invention.')
add(I, 'Guindy metro pe abhi train late hai kya?', {'transport_mode':'metro'}, 'live_delay', 'Refuse absent live delay feed; do not substitute a static schedule as current running status.')
add(I, 'Central metro me filhaal crowd kitni h, bheed avoid karni hai', {'transport_mode':'metro'}, 'live_crowd', 'No live crowd/occupancy assertion; recognize realtime crowd goal.')
add(I, '102A bus ka real time arrival Adyar par kitne minute me hoga?', {'route_number':'102A','transport_mode':'bus'}, 'live_eta', 'Retain exact A suffix and refuse live ETA without realtime feed.')
add(I, '570S abhi Kelambakkam pahuchi kya, tracking karke bolo', {'route_number':'570S'}, 'live_position', 'Recognize live progress question and state missing telemetry.')
add(I, 'MRTS Thirumayilai pe aaj abhi disruption chal raha h kya?', {'transport_mode':'mrts'}, 'live_disruption', 'Do not invent current disruption or operational status; external live source required.')
add(I, '२१G bus right now kaha hai bhai?', {'route_number':'21G','transport_mode':'bus'}, 'native_digit_contrast', 'Normalize route identity and select realtime family before source refusal.')
add(I, 'Guindy local abhi on time hai ya delay? timetable nahi pucha', {'transport_mode':'suburban_rail'}, 'negated_schedule', 'Recognize live delay and ignore negated timetable distractor.')
add(I, 'Airport metro ki iss pal crowd level check kar do', {'transport_mode':'metro'}, 'live_crowd', 'No invented crowd data; correct realtime refusal is a safe limitation, not full travel goal fulfillment.')
add(I, '27D ka current location share karo, route stops mat bhejna', {'route_number':'27D'}, 'negated_sequence', 'Recognize live position; do not provide route stops as requested location.')
add(I, 'Bus kab live aayegi? stop ya route mere message me nahi hai', {'transport_mode':'bus'}, 'missing_context_live', 'Realtime source refusal remains appropriate even when context is absent; do not pretend clarification enables live tracking.')
add(I, 'Blue Line me abhi service suspended hai kya, latest status chahiye', {'line_name':'Blue Line'}, 'current_service_status', 'Recognize live disruption/status rather than static mode availability; refuse without current feed.')

# 181-192: Out-of-scope despite transit entities and action-like wording.
I='out_of_scope'
add(I, 'Guindy station ke paas dosa ghar tak order kar do', {}, 'food_order_transit_entity', 'Reject food-ordering domain; transit location does not convert it to nearest transport.')
add(I, 'Airport jana hai, mere liye Ola cab book karo abhi', {}, 'cab_booking', 'Reject ride-hailing request; do not present public-transit itinerary as fulfillment.')
add(I, 'Chennai Central ke pass budget hotel book karna h', {}, 'hotel_booking_transit_entity', 'Reject hotel booking while preserving scope boundary.')
add(I, 'Aaj Chennai me baarish hogi kya, weather batao yaar', {}, 'weather', 'Reject weather question; do not misclassify live transport because of aaj wording.')
add(I, 'Delhi wali flight ka ticket cost kya padega Chennai se?', {}, 'intercity_flight', 'Reject non-CMA flight fare query instead of calculating metro/bus fare.')
add(I, 'Bangalore ke liye private sleeper bus reserve kar do', {}, 'intercity_private_bus', 'Reject intercity private booking; bus word alone must not trigger local public transit.')
add(I, 'Central ke restaurant me table reserve karwana hai', {}, 'restaurant_transit_entity', 'Reject restaurant reservation even with canonical station name.')
add(I, 'Nandanam flat ka rent kitna chalega, broker se baat karao', {}, 'housing', 'Reject housing/broker request, not transit fare.')
add(I, 'T Nagar ke nearby cinema showtime bta doge?', {}, 'cinema_schedule', 'Reject cinema schedule despite location and timing semantics.')
add(I, '21G ka bus route nahi chahiye, mujhe cricket score batao', {'route_number':'21G'}, 'negated_transit_distractor', 'Reject cricket goal while ignoring explicitly negated route request.')
add(I, 'Metro ke baare me nahi; laptop slow hai kaise repair karu?', {}, 'negated_transit_distractor', 'Reject computer repair as out of scope, not station facilities.')
add(I, 'Mumbai local ka monthly pass rule samjhao, Chennai wala nahi', {'ticket_type':'monthly_pass'}, 'other_city', 'Reject out-of-geography local-pass question; do not supply Chennai policy.')

# 193-200: Independently authored clarification/safety guards; no executable operation.
add(None, '25R aur 102 dono bus routes ke stops ek saath dikha do bhai', {}, 'competing_routes', 'Ask user to choose one route scope; do not silently drop either requested route.', True)
add(None, 'Ordinary stage 5 aur stage 9 ka fare dono nikal do', {'service_type':'Ordinary Services'}, 'competing_stages', 'Clarify competing stage scopes; do not execute only one stage.', True)
add(None, 'Broadway se 102 bus departures 7 AM ya 9 PM dono options me batao', {'route_number':'102'}, 'competing_clocks', 'Clarify multiple explicit clocks; no silent selection of one time.', True)
add(None, 'Marina Beach aur IIT Madras dono ke closest metro station batao', {'transport_mode':'metro'}, 'competing_nearest_locations', 'Request one reference location or explicit separate questions; do not pick one locality silently.', True)
add(None, 'Guindy se Airport metro ka rasta aur ticket ka kiraya dono btao', {'transport_mode':'metro'}, 'multiple_goals_route_fare', 'Clarify two distinct goals (route and fare) with both candidate families; no single-family partial answer.', True)
add(None, 'Alandur metro me parking bhi hai aur lift bhi? dono info chahiye', {'transport_mode':'metro'}, 'multiple_goals_facility_accessibility', 'Clarify station facilities plus accessibility goals; do not mistake them for one feature.', True)
add(None, '102A Guindy pe rukti hai kya aur abhi GPS pe kahan hai?', {'route_number':'102A'}, 'multiple_goals_membership_live', 'Clarify membership and live-location goals; a one-family safe refusal must not count as understanding both.', True)
add(None, 'Broadway se Adyar aur Tambaram tak bus route bta do, dono jagah jana h', {'transport_mode':'bus'}, 'competing_destinations', 'Clarify destination/itinerary scope rather than silently discarding one endpoint.', True)

assert len(C)==200, len(C)
assert len({c['query'] for c in C})==200
counts=Counter(c['expected_intent'] for c in C)
assert all(counts[i]>=8 for i in OPS), counts
(ROOT/'cases.json').write_text(json.dumps(C, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(ROOT/'authoring_manifest.json').write_text(json.dumps({
    'language':'Roman Hindi/Hinglish', 'case_count':len(C),
    'intent_counts': {k:v for k,v in counts.items() if k is not None},
    'guard_count': counts[None],
    'expectations_authored_before_predictions':True,
    'expectation_sources':['src/nlp_v2/contracts.py','data/nlp_v2/taxonomy/taxonomy_semantic_mapping.json','docs/nlp_v2/slot_schema.md','docs/nlp_v2/entity_resolution_contract.md','docs/nlp_v2/known_limitations.md','docs/nlp_v2/answerability_matrix.md'],
    'factual_values':'No expected fare amounts, timetables, facility flags, route-membership results or nearest names invented.',
    'corpus_isolation':'No individual frozen/development/held-out examples inspected; prior campaign queries read programmatically only for exact duplicate check after authoring.'
},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'total':len(C),'counts':dict((str(k),v) for k,v in counts.items())},ensure_ascii=False))
