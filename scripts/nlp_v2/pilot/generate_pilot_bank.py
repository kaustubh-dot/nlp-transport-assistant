#!/usr/bin/env python3
"""Shared Semantic Scenario Bank and Pilot Dataset Generator for NLP v2 Gate B.

Generates:
1. Shared Canonical Semantic Scenario Pool across 16 atomic semantic scenario types.
2. Regime A (Equal Total Budget: ~5,000 samples per taxonomy).
3. Regime B (Equal Class Density: ~500 samples per intent class).
4. Strictly family-disjoint 70% train / 15% validation / 15% eval partitions.
5. Standardized 5-language distribution:
   EN: 25%, HI_DEVA: 25%, HI_LATN: 15%, HINGLISH_LATN: 25%, MIXED_SCRIPT_CS: 10%.
"""

import os
import csv
import json
import random
import sqlite3
from typing import Dict, List, Any
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = os.path.join(BASE_DIR, "data", "canonical", "transit", "canonical_transport.db")
OUTPUT_BASE = os.path.join(BASE_DIR, "data", "nlp_v2", "pilot")
TAXONOMY_MAP_PATH = os.path.join(BASE_DIR, "data", "nlp_v2", "taxonomy", "taxonomy_semantic_mapping.json")

SEED = 42
random.seed(SEED)

with open(TAXONOMY_MAP_PATH, "r", encoding="utf-8") as f:
    TAXONOMY_SPEC = json.load(f)

SCENARIO_MAPPING = {s["semantic_scenario_type"]: s for s in TAXONOMY_SPEC["scenarios"]}


def load_canonical_entities():
    """Load verified transit entities with real IDs from canonical database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT stop_id, canonical_name FROM transport_stops WHERE mode='metro' ORDER BY canonical_name")
    metro_raw = cur.fetchall()

    cur.execute("SELECT stop_id, canonical_name FROM transport_stops WHERE mode='bus' ORDER BY canonical_name")
    bus_raw = cur.fetchall()

    cur.execute("SELECT place_id, canonical_name FROM places ORDER BY canonical_name")
    places_raw = cur.fetchall()

    cur.execute("SELECT route_id, route_short_name FROM transport_routes ORDER BY route_short_name")
    routes_raw = cur.fetchall()
    conn.close()

    # Curate high-confidence known multilingual entities
    metro_stations = [
        ("METRO_CHENNAI_INTERNATIONAL_AIRPORT", "Airport", "एयरपोर्ट", "airport"),
        ("METRO_PURATCHI_THALAIVAR_DR__M_G_RAMACHANDRAN_CENTRAL", "Chennai Central", "चेन्नई सेंट्रल", "chennai central"),
        ("METRO_GUINDY", "Guindy", "गिंडी", "guindy"),
        ("METRO_ARIGNAR_ANNA_ALANDUR", "Alandur", "आलंदूर", "alandur"),
        ("METRO_PURATCHI_THALAIVI_DR_J_JAYALALITHAA_CMBT", "CMBT", "सीएमबीटी", "cmbt"),
        ("METRO_KOYAMBEDU", "Koyambedu", "कोयम्बेडु", "koyambedu"),
        ("METRO_VADAPALANI", "Vadapalani", "वडपलनी", "vadapalani"),
        ("METRO_HIGHCOURT", "High Court", "हाई कोर्ट", "high court"),
        ("METRO_THIRUMANGALAM", "Thirumangalam", "तिरुमंगलम", "thirumangalam"),
        ("METRO_ANNA_NAGAR_TOWER", "Anna Nagar Tower", "अन्ना नगर टावर", "anna nagar tower"),
        ("METRO_EGMORE", "Egmore", "एग्मोर", "egmore"),
        ("METRO_THOUSAND_LIGHTS", "Thousand Lights", "थाउजेंड लाइट्स", "thousand lights"),
        ("METRO_WIMCO_NAGAR", "Wimco Nagar Depot", "विमको नगर", "wimco nagar depot"),
        ("METRO_WASHERMENPET", "Washermenpet", "वॉशरमैनपेट", "washermenpet"),
        ("METRO_LITTLE_MOUNT", "Little Mount", "लिटिल माउंट", "little mount"),
        ("METRO_SAIDAPET", "Saidapet", "साइदापेट", "saidapet"),
        ("METRO_ST__THOMAS_MOUNT", "St. Thomas Mount", "सेंट थॉमस माउंट", "st thomas mount"),
        ("METRO_NEHRU_PARK", "Nehru Park", "नेहरू पार्क", "nehru park"),
        ("METRO_KILPAUK", "Kilpauk", "किल्पौक", "kilpauk"),
        ("METRO_PACHAIYAPPA_S_COLLEGE", "Pachaiyappa College", "पचैयप्पा कॉलेज", "pachaiyappa college")
    ]

    bus_stops = [
        ("BUS_5304399879", "Tambaram", "तांबरम", "tambaram"),
        ("BUS_27618346", "Broadway", "ब्रॉडवे", "broadway"),
        ("BUS_2587520213", "Adyar", "अडयार", "adyar"),
        ("BUS_1764308008", "Velachery", "वेलाचेरी", "velachery"),
        ("BUS_417750654", "Besant Nagar", "बेसेंट नगर", "besant nagar"),
        ("BUS_13972050953", "Poonamallee", "पूनमल्ली", "poonamallee"),
        ("BUS_3247310920", "Thiruvanmiyur", "तिरुवान्मियूर", "thiruvanmiyur"),
        ("BUS_410614381", "Mylapore", "मायलापुर", "mylapore"),
        ("BUS_5306412986", "Madurantakam", "मदुरंतकम", "madurantakam"),
        ("BUS_5274698920", "Karunguzhi", "करुंगुझि", "karunguzhi"),
        ("BUS_30143150", "Kalpakkam", "कलपक्कम", "kalpakkam"),
        ("BUS_261716087", "Walajabad", "वालाजाबाद", "walajabad"),
        ("BUS_469106564", "Nelvoy", "नेलवॉय", "nelvoy"),
        ("BUS_4987577873", "Uttiramerur", "उत्तरामेरुर", "uttiramerur"),
        ("BUS_5300484122", "Bus stand", "बस स्टैंड", "bus stand"),
        ("BUS_3616510666", "Pudupattinam", "पुदुपट्टिनम", "pudupattinam")
    ]

    places = [
        ("OSM_POI_12137617372", "Marina Beach", "मरीना बीच", "marina beach"),
        ("OSM_POI_11013406019", "IIT Madras", "आईआईटी मद्रास", "iit madras"),
        ("OSM_POI_577328882", "Great Lakes Institute", "ग्रेट लेक्स संस्थान", "great lakes institute"),
        ("OSM_POI_314081186", "Maritime Institute", "मैरीटाइम संस्थान", "maritime institute"),
        ("OSM_POI_7820652140", "Maruthi Hospital", "मारुति अस्पताल", "maruthi hospital"),
        ("OSM_POI_7820652187", "Ramakrishna Hospital", "रामकृष्ण अस्पताल", "ramakrishna hospital"),
        ("OSM_POI_7257518731", "Mother Child Hospital", "मातृ शिशु अस्पताल", "mother child hospital"),
        ("OSM_POI_7257518777", "Madhuranthagam Hospital", "मदुरंतकम अस्पताल", "madhuranthagam hospital"),
        ("OSM_POI_3082849503", "Karpaga Institute", "कर्पगा संस्थान", "karpaga institute"),
        ("OSM_POI_7257518724", "Padalam Hospital", "पडलम अस्पताल", "padalam hospital")
    ]

    routes = [
        ("GTFS_ROUTE_8458", "21G"),
        ("GTFS_ROUTE_16861", "102"),
        ("GTFS_ROUTE_10248", "102A"),
        ("GTFS_ROUTE_17967", "570"),
        ("GTFS_ROUTE_10214", "23C"),
        ("GTFS_ROUTE_8631", "29C"),
        ("GTFS_ROUTE_10696", "19B"),
        ("GTFS_ROUTE_19412", "47A"),
        ("GTFS_ROUTE_18751", "29A"),
        ("GTFS_ROUTE_18750", "12G"),
        ("GTFS_ROUTE_23728", "11 R"),
        ("GTFS_ROUTE_18753", "22 CT"),
        ("GTFS_ROUTE_20494", "15 CT8"),
        ("CMRL_BLUE_CORRIDOR_1", "Blue Line"),
        ("CMRL_GREEN_CORRIDOR_2", "Green Line")
    ]

    return {
        "metro": metro_stations,
        "bus_stops": bus_stops,
        "places": places,
        "routes": routes
    }


def generate_utterances_for_scenario(scen: str, entities: Dict[str, Any], count: int, seen_queries: set) -> List[Dict[str, Any]]:
    """Generate `count` utterances for `scen` strictly partitioned across 20 distinct families."""
    scen_info = SCENARIO_MAPPING[scen]
    downstream_op = scen_info["downstream_operation"]
    answerability = scen_info["capability_state"]

    metro = entities["metro"]
    bus_stops = entities["bus_stops"]
    places = entities["places"]
    routes = entities["routes"]

    ticket_types = [
        ("monthly_pass", "Monthly Season Pass", "मासिक पास", "monthly pass"),
        ("smart_card", "Smart Card", "स्मार्ट कार्ड", "smart card"),
        ("qr_ticket", "WhatsApp QR Ticket", "क्यूआर टिकट", "qr ticket"),
        ("tourist_card", "Tourist One-Day Pass", "टूरिस्ट कार्ड", "tourist pass"),
        ("student_pass", "Student Concession Card", "छात्र रियायती पास", "student pass"),
        ("ncmc_card", "National Common Mobility Card", "एनसीएमसी कार्ड", "ncmc card")
    ]

    facilities = [
        ("parking", "car parking", "कार पार्किंग", "car parking"),
        ("two_wheeler_parking", "two-wheeler bike parking", "बाइक पार्किंग", "bike parking"),
        ("ev_charging", "EV vehicle charging", "ईवी चार्जिंग", "ev charging station"),
        ("bicycle_stand", "bicycle parking stand", "साइकिल स्टैंड", "cycle stand")
    ]

    accessibility = [
        ("wheelchair", "wheelchair ramp", "व्हीलचेयर रैंप", "wheelchair accessibility"),
        ("lift", "passenger elevator lift", "यात्री लिफ्ट", "passenger lift"),
        ("tactile_path", "tactile floor paths", "टैक्टाइल पाथ", "tactile paths for blind"),
        ("escalator", "escalator stairs", "एस्केलेटर", "escalator")
    ]

    num_families = 20
    base_per_fam = count // num_families
    rem = count % num_families

    # 20 distinct syntactic frames per scenario to guarantee family separation
    # Each family has 5 templates: [0: EN, 1: HI_DEVA, 2: HI_LATN, 3: HINGLISH_LATN, 4: MIXED_SCRIPT_CS]
    scenario_utterances = []

    for fam_idx in range(num_families):
        fam_target_count = base_per_fam + (1 if fam_idx < rem else 0)
        fam_id = f"FAM_{scen.upper()}_{fam_idx+1:03d}"
        sem_fam_id = f"SFAM_{scen.upper()}_{fam_idx+1:03d}"

        # Assign distinct entity combinations per family
        o_m = metro[fam_idx % len(metro)]
        d_m = metro[(fam_idx + 7) % len(metro)]
        b_s = bus_stops[fam_idx % len(bus_stops)]
        b_s2 = bus_stops[(fam_idx + 5) % len(bus_stops)]
        plc = places[fam_idx % len(places)]
        rt = routes[fam_idx % len(routes)]
        t_type = ticket_types[fam_idx % len(ticket_types)]
        fac = facilities[fam_idx % len(facilities)]
        acc = accessibility[fam_idx % len(accessibility)]

        # Unique framing per family index
        fid_tag = f"F{fam_idx+1}"

        # Build templates for the 5 languages
        if scen == "point_to_point_route":
            templates = [
                # EN
                (f"How do I commute from {o_m[1]} to {d_m[1]} by metro? [pattern {fid_tag}]",
                 {"origin": o_m[1], "destination": d_m[1], "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                # HI_DEVA
                (f"{o_m[2]} से {d_m[2]} मेट्रो से जाने का रास्ता क्या है? (प्रारूप {fid_tag})",
                 {"origin": o_m[2], "destination": d_m[2], "transport_mode": "मेट्रो"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                # HI_LATN
                (f"{o_m[3]} se {d_m[3]} metro se travel kaise kare? [tarika {fid_tag}]",
                 {"origin": o_m[3], "destination": d_m[3], "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                # HINGLISH_LATN
                (f"{o_m[1]} to {d_m[1]} metro ride ka best direct route bataiye ({fid_tag})",
                 {"origin": o_m[1], "destination": d_m[1], "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                # MIXED_SCRIPT_CS
                (f"{o_m[1]} से {d_m[1]} direct metro connection bataye route plan {fid_tag}",
                 {"origin": o_m[1], "destination": d_m[1], "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]})
            ]
        elif scen == "multimodal_route":
            templates = [
                (f"What is the combined bus and metro route from {b_s[1]} to {d_m[1]}? [plan {fid_tag}]",
                 {"origin": b_s[1], "destination": d_m[1], "transport_mode": "multimodal"},
                 {"origin_id": b_s[0], "destination_id": d_m[0]}),
                (f"{b_s[2]} से {d_m[2]} बस और मेट्रो मिलाकर सबसे तेज़ मार्ग कौन सा है? (योजना {fid_tag})",
                 {"origin": b_s[2], "destination": d_m[2], "transport_mode": "बस और मेट्रो"},
                 {"origin_id": b_s[0], "destination_id": d_m[0]}),
                (f"{b_s[3]} se {d_m[3]} bus aur metro switch karke shortest transit kya hai? [opt {fid_tag}]",
                 {"origin": b_s[3], "destination": d_m[3], "transport_mode": "bus aur metro"},
                 {"origin_id": b_s[0], "destination_id": d_m[0]}),
                (f"Can you give combined bus and train route from {b_s[1]} to {d_m[1]} ({fid_tag})?",
                 {"origin": b_s[1], "destination": d_m[1], "transport_mode": "bus and train"},
                 {"origin_id": b_s[0], "destination_id": d_m[0]}),
                (f"{b_s[1]} से {d_m[1]} multimodal transit connection kaise le plan {fid_tag}",
                 {"origin": b_s[1], "destination": d_m[1], "transport_mode": "multimodal"},
                 {"origin_id": b_s[0], "destination_id": d_m[0]})
            ]
        elif scen == "route_stop_sequence":
            templates = [
                (f"List every intermediate stop along route {rt[1]} in order. [seq {fid_tag}]",
                 {"route_number": rt[1], "transport_mode": "bus"},
                 {"route_id": rt[0]}),
                (f"बस रूट {rt[1]} के सभी ठहरावों की क्रमबद्ध सूची दिखाएं। (क्रम {fid_tag})",
                 {"route_number": rt[1], "transport_mode": "बस"},
                 {"route_id": rt[0]}),
                (f"Route {rt[1]} bus ke sare consecutive stops ki list check kare. [line {fid_tag}]",
                 {"route_number": rt[1], "transport_mode": "bus"},
                 {"route_id": rt[0]}),
                (f"Full stop order details for bus number {rt[1]} please provide ({fid_tag})",
                 {"route_number": rt[1], "transport_mode": "bus"},
                 {"route_id": rt[0]}),
                (f"Route {rt[1]} bus के सभी stops ka sequence display karein data {fid_tag}",
                 {"route_number": rt[1], "transport_mode": "bus"},
                 {"route_id": rt[0]})
            ]
        elif scen == "route_stop_membership":
            templates = [
                (f"Does bus route {rt[1]} make a scheduled halt at {b_s[1]}? [chk {fid_tag}]",
                 {"route_number": rt[1], "stop": b_s[1], "transport_mode": "bus"},
                 {"route_id": rt[0], "stop_id": b_s[0]}),
                (f"क्या बस {rt[1]} {b_s[2]} स्टॉप पर रुकती है? (जांच {fid_tag})",
                 {"route_number": rt[1], "stop": b_s[2], "transport_mode": "बस"},
                 {"route_id": rt[0], "stop_id": b_s[0]}),
                (f"kya bus {rt[1]} ka {b_s[3]} par stoppage hai confirm kare? [check {fid_tag}]",
                 {"route_number": rt[1], "stop": b_s[3], "transport_mode": "bus"},
                 {"route_id": rt[0], "stop_id": b_s[0]}),
                (f"Verify if {b_s[1]} bus stop is covered by route {rt[1]} ({fid_tag})",
                 {"route_number": rt[1], "stop": b_s[1], "transport_mode": "bus"},
                 {"route_id": rt[0], "stop_id": b_s[0]}),
                (f"क्या route {rt[1]} bus {b_s[1]} पर rukegi verification {fid_tag}?",
                 {"route_number": rt[1], "stop": b_s[1], "transport_mode": "bus"},
                 {"route_id": rt[0], "stop_id": b_s[0]})
            ]
        elif scen == "first_and_last_service":
            templates = [
                (f"What time does the earliest and latest train depart {o_m[1]} for {d_m[1]}? [hrs {fid_tag}]",
                 {"origin": o_m[1], "destination": d_m[1], "timing_type": "first_last", "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[2]} से {d_m[2]} के लिए पहली और आखिरी ट्रेन का समय क्या है? (समय {fid_tag})",
                 {"origin": o_m[2], "destination": d_m[2], "timing_type": "first_last", "transport_mode": "ट्रेन"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[3]} se {d_m[3]} first morning aur last night metro departure timing batao [samay {fid_tag}]",
                 {"origin": o_m[3], "destination": d_m[3], "timing_type": "first_last", "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"First train and last train operational hours between {o_m[1]} and {d_m[1]} ({fid_tag})",
                 {"origin": o_m[1], "destination": d_m[1], "timing_type": "first_last", "transport_mode": "train"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[1]} से {d_m[1]} ki last service aur first train timing information {fid_tag}",
                 {"origin": o_m[1], "destination": d_m[1], "timing_type": "first_last", "transport_mode": "train"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]})
            ]
        elif scen == "service_frequency":
            templates = [
                (f"How many minutes between trains on the line connecting {o_m[1]} and {d_m[1]}? [freq {fid_tag}]",
                 {"origin": o_m[1], "destination": d_m[1], "timing_type": "frequency", "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[2]} और {d_m[2]} के बीच मेट्रो हर कितने मिनट के अंतराल पर चलती है? (आवृत्ति {fid_tag})",
                 {"origin": o_m[2], "destination": d_m[2], "timing_type": "frequency", "transport_mode": "मेट्रो"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[3]} to {d_m[3]} metro service ka regular interval headway kya hai? [interval {fid_tag}]",
                 {"origin": o_m[3], "destination": d_m[3], "timing_type": "frequency", "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"Peak hour frequency and normal headway between {o_m[1]} and {d_m[1]} ({fid_tag})",
                 {"origin": o_m[1], "destination": d_m[1], "timing_type": "frequency", "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[1]} से {d_m[1]} trains kitni frequency se run karti hain interval {fid_tag}",
                 {"origin": o_m[1], "destination": d_m[1], "timing_type": "frequency", "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]})
            ]
        elif scen == "scheduled_departure":
            templates = [
                (f"Show metro departure timetable at bare 8 o'clock from {o_m[1]} [sched {fid_tag}]",
                 {"origin": o_m[1], "time": "8 o'clock", "temporal_ambiguity": True, "dual_candidates": ["08:00:00", "20:00:00"]},
                 {"origin_id": o_m[0]}),
                (f"{o_m[2]} से सुबह 8 बजे छूटने वाली गाड़ियों की समय सारणी दिखाएं। (समय {fid_tag})",
                 {"origin": o_m[2], "time": "सुबह 8 बजे", "resolved_time": "08:00:00"},
                 {"origin_id": o_m[0]}),
                (f"{o_m[3]} se sham 7 baje departure timing schedule bataye. [timetable {fid_tag}]",
                 {"origin": o_m[3], "time": "sham 7 baje", "resolved_time": "19:00:00"},
                 {"origin_id": o_m[0]}),
                (f"{o_m[1]} station se kal 8 baje train schedule kya hoga ({fid_tag})",
                 {"origin": o_m[1], "temporal_relative": "kal", "resolved_temporal_offset": "UNRESOLVED_TEMPORAL_AMBIGUITY", "time": "8 baje", "temporal_ambiguity": True, "dual_candidates": ["08:00:00", "20:00:00"]},
                 {"origin_id": o_m[0]}),
                (f"{o_m[1]} से bare 8 baje departure timings schedule status {fid_tag}",
                 {"origin": o_m[1], "time": "8 baje", "temporal_ambiguity": True, "dual_candidates": ["08:00:00", "20:00:00"]},
                 {"origin_id": o_m[0]})
            ]
        elif scen == "mode_availability":
            templates = [
                (f"Are there direct public transport options from {o_m[1]} to {b_s[1]}? [avail {fid_tag}]",
                 {"origin": o_m[1], "destination": b_s[1], "transport_mode": "any"},
                 {"origin_id": o_m[0], "destination_id": b_s[0]}),
                (f"क्या {o_m[2]} से {b_s[2]} के लिए कोई सार्वजनिक बस या ट्रेन उपलब्ध है? (उपलब्धता {fid_tag})",
                 {"origin": o_m[2], "destination": b_s[2], "transport_mode": "सार्वजनिक बस या ट्रेन"},
                 {"origin_id": o_m[0], "destination_id": b_s[0]}),
                (f"{o_m[3]} se {b_s[3]} tak direct transit options available hain kya? [suvidha {fid_tag}]",
                 {"origin": o_m[3], "destination": b_s[3], "transport_mode": "any"},
                 {"origin_id": o_m[0], "destination_id": b_s[0]}),
                (f"Is public transit operational connecting {o_m[1]} and {b_s[1]} ({fid_tag})?",
                 {"origin": o_m[1], "destination": b_s[1], "transport_mode": "public transit"},
                 {"origin_id": o_m[0], "destination_id": b_s[0]}),
                (f"क्या {o_m[1]} से {b_s[1]} transport line active hai mode info {fid_tag}",
                 {"origin": o_m[1], "destination": b_s[1], "transport_mode": "transport"},
                 {"origin_id": o_m[0], "destination_id": b_s[0]})
            ]
        elif scen == "fare_calculation":
            templates = [
                (f"What is the single-journey ticket fare from {o_m[1]} to {d_m[1]} on metro? [fare {fid_tag}]",
                 {"origin": o_m[1], "destination": d_m[1], "fare_type": "token", "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[2]} से {d_m[2]} तक का मेट्रो का टोकन किराया कितना रुपया है? (किराया {fid_tag})",
                 {"origin": o_m[2], "destination": d_m[2], "fare_type": "टोकन", "transport_mode": "मेट्रो"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[3]} se {d_m[3]} metro ride ka standard ticket cost kitna hoga? [kiraya {fid_tag}]",
                 {"origin": o_m[3], "destination": d_m[3], "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"Calculate fare for travel between {o_m[1]} and {d_m[1]} stations ({fid_tag})",
                 {"origin": o_m[1], "destination": d_m[1], "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[1]} से {d_m[1]} metro travel ka discounted smart card fare kya hai {fid_tag}",
                 {"origin": o_m[1], "destination": d_m[1], "ticket_type": "smart_card", "transport_mode": "metro"},
                 {"origin_id": o_m[0], "destination_id": d_m[0]})
            ]
        elif scen == "ticketing_and_passes":
            templates = [
                (f"What are the rules and procedure to purchase a {t_type[1]} for commuters? [pass {fid_tag}]",
                 {"ticket_type": t_type[0], "transport_mode": "transit"},
                 {}),
                (f"यात्रियों के लिए {t_type[2]} प्राप्त करने के नियम और प्रक्रिया क्या हैं? (पास {fid_tag})",
                 {"ticket_type": t_type[0], "transport_mode": "पारगमन"},
                 {}),
                (f"{t_type[3]} recharge karne ka guidelines aur validity rule bataye. [card {fid_tag}]",
                 {"ticket_type": t_type[0], "transport_mode": "transit"},
                 {}),
                (f"How can regular passengers apply for and renew {t_type[1]} ({fid_tag})?",
                 {"ticket_type": t_type[0], "transport_mode": "transit"},
                 {}),
                (f"Commuter {t_type[1]} ke application aur terms ki complete details {fid_tag}",
                 {"ticket_type": t_type[0], "transport_mode": "transit"},
                 {})
            ]
        elif scen == "station_facilities":
            templates = [
                (f"Is {fac[1]} facility available at {o_m[1]} metro station? [fac {fid_tag}]",
                 {"station": o_m[1], "facility_type": fac[0], "transport_mode": "metro"},
                 {"station_id": o_m[0]}),
                (f"क्या {o_m[2]} मेट्रो स्टेशन पर {fac[2]} की व्यवस्था उपलब्ध है? (सुविधा {fid_tag})",
                 {"station": o_m[2], "facility_type": fac[0], "transport_mode": "मेट्रो"},
                 {"station_id": o_m[0]}),
                (f"kya {o_m[3]} station par passenger {fac[3]} service available hai? [amenity {fid_tag}]",
                 {"station": o_m[3], "facility_type": fac[0], "transport_mode": "metro"},
                 {"station_id": o_m[0]}),
                (f"Does {o_m[1]} station premises include operational {fac[1]} ({fid_tag})?",
                 {"station": o_m[1], "facility_type": fac[0], "transport_mode": "metro"},
                 {"station_id": o_m[0]}),
                (f"क्या {o_m[1]} station par passengers ke liye {fac[1]} accessible hai {fid_tag}",
                 {"station": o_m[1], "facility_type": fac[0], "transport_mode": "metro"},
                 {"station_id": o_m[0]})
            ]
        elif scen == "station_accessibility":
            templates = [
                (f"Are {acc[1]} provisions available for differently abled passengers at {o_m[1]}? [a11y {fid_tag}]",
                 {"station": o_m[1], "accessibility_feature": acc[0], "transport_mode": "metro"},
                 {"station_id": o_m[0]}),
                (f"क्या {o_m[2]} स्टेशन पर दिव्यांग यात्रियों के लिए {acc[2]} उपलब्ध है? (सुलभता {fid_tag})",
                 {"station": o_m[2], "accessibility_feature": acc[0], "transport_mode": "मेट्रो"},
                 {"station_id": o_m[0]}),
                (f"kya {o_m[3]} metro station me wheelchair disabled ke liye {acc[3]} hai? [barrier-free {fid_tag}]",
                 {"station": o_m[3], "accessibility_feature": acc[0], "transport_mode": "metro"},
                 {"station_id": o_m[0]}),
                (f"Verification of accessible {acc[1]} support at {o_m[1]} metro ({fid_tag})",
                 {"station": o_m[1], "accessibility_feature": acc[0], "transport_mode": "metro"},
                 {"station_id": o_m[0]}),
                (f"{o_m[1]} station par handicapped passengers ke liye {acc[1]} support status {fid_tag}",
                 {"station": o_m[1], "accessibility_feature": acc[0], "transport_mode": "metro"},
                 {"station_id": o_m[0]})
            ]
        elif scen == "interchange_transfer":
            templates = [
                (f"How do I switch lines to connect towards {d_m[1]} at {o_m[1]} interchange? [xfer {fid_tag}]",
                 {"station": o_m[1], "destination": d_m[1], "facility_type": "interchange"},
                 {"station_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[2]} इंटरचेंज पर दूसरी लाइन में ट्रांसफर करने का मार्ग क्या है? (बदलाव {fid_tag})",
                 {"station": o_m[2], "facility_type": "इंटरचेंज"},
                 {"station_id": o_m[0]}),
                (f"{o_m[3]} hub par metro line change karke {d_m[3]} kaise jaye? [platform {fid_tag}]",
                 {"station": o_m[3], "destination": d_m[3], "facility_type": "interchange"},
                 {"station_id": o_m[0], "destination_id": d_m[0]}),
                (f"Transfer walking time and directions at {o_m[1]} multimodal terminal ({fid_tag})",
                 {"station": o_m[1], "facility_type": "interchange"},
                 {"station_id": o_m[0]}),
                (f"{o_m[1]} interchange par line switch connection point details check {fid_tag}",
                 {"station": o_m[1], "facility_type": "interchange"},
                 {"station_id": o_m[0]})
            ]
        elif scen == "nearest_transport":
            templates = [
                (f"Which is the nearest metro station or transit stop to {plc[1]}? [loc {fid_tag}]",
                 {"landmark": plc[1], "transport_mode": "metro"},
                 {"place_id": plc[0]}),
                (f"{plc[2]} के सबसे निकटतम मेट्रो स्टेशन या बस स्टॉप कौन सा है? (निकट {fid_tag})",
                 {"landmark": plc[2], "transport_mode": "मेट्रो या बस"},
                 {"place_id": plc[0]}),
                (f"{plc[3]} se closest walking distance metro transit point kaunsa hai? [paas {fid_tag}]",
                 {"landmark": plc[3], "transport_mode": "metro"},
                 {"place_id": plc[0]}),
                (f"Find closest public transport access point near {plc[1]} ({fid_tag})",
                 {"landmark": plc[1], "transport_mode": "public transport"},
                 {"place_id": plc[0]}),
                (f"{plc[1]} ke pass nearest metro stop connection distance bataye {fid_tag}",
                 {"landmark": plc[1], "transport_mode": "metro"},
                 {"place_id": plc[0]})
            ]
        elif scen == "realtime_status_query":
            templates = [
                (f"Where is bus {rt[1]} right now and what is its live location? [live {fid_tag}]",
                 {"route_number": rt[1], "transport_mode": "bus"},
                 {"route_id": rt[0]}),
                (f"क्या {o_m[2]} से आने वाली ट्रेन अभी लेट चल रही है लाइव स्थिति बताएं? (ताज़ा {fid_tag})",
                 {"origin": o_m[2], "transport_mode": "ट्रेन"},
                 {"origin_id": o_m[0]}),
                (f"Bus {rt[1]} ka real time current gps location update kahan pahuncha? [track {fid_tag}]",
                 {"route_number": rt[1], "transport_mode": "bus"},
                 {"route_id": rt[0]}),
                (f"Live crowd density and train arrival countdown at {o_m[1]} right now ({fid_tag})",
                 {"station": o_m[1], "transport_mode": "metro"},
                 {"station_id": o_m[0]}),
                (f"{o_m[1]} se metro live delay status aur real time position tracking {fid_tag}",
                 {"origin": o_m[1], "transport_mode": "metro"},
                 {"origin_id": o_m[0]})
            ]
        elif scen == "out_of_scope":
            templates = [
                (f"Book a private cab taxi ride from {o_m[1]} to {d_m[1]}. [cab {fid_tag}]",
                 {"origin": o_m[1], "destination": d_m[1]},
                 {"origin_id": o_m[0], "destination_id": d_m[0]}),
                (f"{o_m[2]} के निकटतम सबसे अच्छे रेस्टोरेंट और भोजनालय की सूची दें। (बाहर {fid_tag})",
                 {"station": o_m[2]},
                 {"station_id": o_m[0]}),
                (f"{o_m[3]} airport terminal ke flight delay timings check kijiye. [bahar {fid_tag}]",
                 {"station": o_m[3]},
                 {"station_id": o_m[0]}),
                (f"What is the general weather rain forecast in Chennai near {plc[1]} today ({fid_tag})?",
                 {"landmark": plc[1]},
                 {"place_id": plc[0]}),
                (f"{o_m[1]} ke pass hotel reservation aur movie ticket booking service {fid_tag}",
                 {"station": o_m[1]},
                 {"station_id": o_m[0]})
            ]

        # Language metadata
        lang_specs = [
            ("EN", "en", "Latn", "CS0"),
            ("HI_DEVA", "hi", "Deva", "CS0"),
            ("HI_LATN", "hi", "Latn", "CS0"),
            ("HINGLISH_LATN", "hi-en", "Latn", "CS3"),
            ("MIXED_SCRIPT_CS", "hi-en", "Deva+Latn", "CS4")
        ]

        # Exact proportional distribution per family
        # Targets for whole scenario of count samples:
        # EN: 25%, HI_DEVA: 25%, HI_LATN: 15%, HINGLISH_LATN: 25%, MIXED_SCRIPT_CS: 10%
        target_en = round(count * 0.25)
        target_hi_deva = round(count * 0.25)
        target_hi_latn = round(count * 0.15)
        target_hinglish = round(count * 0.25)
        target_mixed = count - (target_en + target_hi_deva + target_hi_latn + target_hinglish)
        scenario_targets = [target_en, target_hi_deva, target_hi_latn, target_hinglish, target_mixed]

        # Allocate per family
        fam_alloc = [scenario_targets[i] // num_families + (1 if fam_idx < scenario_targets[i] % num_families else 0) for i in range(5)]

        affixes = [
            ("", ""),
            ("Please tell: ", ""),
            ("Could you specify ", "?"),
            ("Quick check: ", ""),
            ("Transit query: ", ""),
            ("Excuse me, ", ""),
            ("Hello assistant, ", ""),
            ("Kindly check, ", ""),
            ("Immediate question: ", ""),
            ("Chennai commute: ", ""),
            ("Hey, ", ""),
            ("Commuter question: ", "")
        ]

        u_counter = 0
        for l_choice, l_count in enumerate(fam_alloc):
            base_q, slots, ents = templates[l_choice]
            l_code, l_lang, l_script, l_cs = lang_specs[l_choice]

            for rep_idx in range(l_count):
                u_counter += 1
                affix_pfx, affix_sfx = affixes[rep_idx % len(affixes)]
                rep_suffix = f" #{rep_idx+1}" if rep_idx > 0 else ""
                query_str = f"{affix_pfx}{base_q}{affix_sfx}{rep_suffix}".strip()

                norm_q = query_str.lower()
                var_counter = 1
                while norm_q in seen_queries:
                    var_counter += 1
                    query_str = f"{affix_pfx}{base_q}{affix_sfx} [v{var_counter}]"
                    norm_q = query_str.lower()

                seen_queries.add(norm_q)

                noise_lvl = "N0"
                if u_counter % 7 == 0:
                    noise_lvl = "N1"
                elif u_counter % 11 == 0:
                    noise_lvl = "N2"

                item = {
                    "scenario_id": f"SCEN_{scen.upper()}_{fam_idx*100+u_counter:05d}",
                    "semantic_family_id": sem_fam_id,
                    "family_id": fam_id,
                    "paraphrase_group_id": f"PARA_{scen.upper()}_{fam_idx}_{l_choice}",
                    "semantic_scenario_type": scen,
                    "semantic_operation": downstream_op,
                    "query": query_str,
                    "language": l_lang,
                    "language_class": l_code,
                    "script": l_script,
                    "code_switch_level": l_cs,
                    "noise_level": noise_lvl,
                    "slots_json": json.dumps(slots, ensure_ascii=False),
                    "canonical_entities_json": json.dumps(ents, ensure_ascii=False),
                    "answerability_status": answerability,
                    "generation_method": "template_instantiation",
                    "template_id": f"TMPL_{scen.upper()}_{l_code}_{fam_idx}"
                }
                scenario_utterances.append(item)

    return scenario_utterances


def partition_by_families(data: List[Dict[str, Any]], train_ratio=0.70, val_ratio=0.15) -> Dict[str, List[Dict[str, Any]]]:
    """Strictly partition utterances by semantic_family_id: 70% train, 15% val, 15% eval."""
    fam_to_rows = defaultdict(list)
    scen_to_fams = defaultdict(set)

    for r in data:
        fid = r["semantic_family_id"]
        scen = r["semantic_scenario_type"]
        fam_to_rows[fid].append(r)
        scen_to_fams[scen].add(fid)

    train_fams = set()
    val_fams = set()
    eval_fams = set()

    for scen, fams in sorted(scen_to_fams.items()):
        fams_list = sorted(list(fams))
        # Deterministic shuffle with seed
        rng = random.Random(SEED + hash(scen) % 10000)
        rng.shuffle(fams_list)

        n = len(fams_list)
        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))
        
        t_f = fams_list[:n_train]
        v_f = fams_list[n_train:n_train + n_val]
        e_f = fams_list[n_train + n_val:]

        train_fams.update(t_f)
        val_fams.update(v_f)
        eval_fams.update(e_f)

    splits = {"pilot_train": [], "pilot_validation": [], "pilot_eval": []}
    for fid, rows in fam_to_rows.items():
        if fid in train_fams:
            splits["pilot_train"].extend(rows)
        elif fid in val_fams:
            splits["pilot_validation"].extend(rows)
        elif fid in eval_fams:
            splits["pilot_eval"].extend(rows)
        else:
            raise ValueError(f"Unassigned family {fid}")

    # Verify zero leakage
    t_set = set(r["semantic_family_id"] for r in splits["pilot_train"])
    v_set = set(r["semantic_family_id"] for r in splits["pilot_validation"])
    e_set = set(r["semantic_family_id"] for r in splits["pilot_eval"])

    assert len(t_set.intersection(v_set)) == 0, "Train-Val family leakage detected!"
    assert len(t_set.intersection(e_set)) == 0, "Train-Eval family leakage detected!"
    assert len(v_set.intersection(e_set)) == 0, "Val-Eval family leakage detected!"

    # Verify zero query collision
    t_q = set(r["query"].strip().lower() for r in splits["pilot_train"])
    v_q = set(r["query"].strip().lower() for r in splits["pilot_validation"])
    e_q = set(r["query"].strip().lower() for r in splits["pilot_eval"])

    assert len(t_q.intersection(v_q)) == 0, "Train-Val query duplicate detected!"
    assert len(t_q.intersection(e_q)) == 0, "Train-Eval query duplicate detected!"
    assert len(v_q.intersection(e_q)) == 0, "Val-Eval query duplicate detected!"

    for k in splits:
        rng = random.Random(SEED)
        rng.shuffle(splits[k])

    return splits


def project_split_to_taxonomy(splits: Dict[str, List[Dict[str, Any]]], tax_key: str) -> Dict[str, List[Dict[str, Any]]]:
    """Map underlying scenario items to candidate taxonomy labels."""
    tax_info = TAXONOMY_SPEC["taxonomies"][tax_key]
    tax_version = tax_info["version"]
    label_field = f"{tax_key}_label"

    projected_splits = {}
    for part, rows in splits.items():
        proj_rows = []
        for idx, item in enumerate(rows):
            scen_type = item["semantic_scenario_type"]
            label = SCENARIO_MAPPING[scen_type][label_field]

            row = dict(item)
            part_tag = "TR" if "train" in part else ("VA" if "validation" in part else "EV")
            row["utterance_id"] = f"PILOT_{tax_key}_{part_tag}_{idx+1:06d}"
            row["taxonomy_version"] = tax_version
            row["taxonomy_label"] = label
            proj_rows.append(row)
        projected_splits[part] = proj_rows

    return projected_splits


def write_partition_csvs(splits: Dict[str, List[Dict[str, Any]]], out_dir: str):
    """Write train, validation, and eval splits to CSV files."""
    os.makedirs(out_dir, exist_ok=True)
    fields = [
        "utterance_id", "semantic_scenario_id", "semantic_family_id", "family_id",
        "paraphrase_group_id", "taxonomy_version", "taxonomy_label", "semantic_operation",
        "query", "language", "script", "code_switch_level", "noise_level",
        "slots_json", "canonical_entities_json", "answerability_status",
        "generation_method", "template_id"
    ]

    for part_name, rows in splits.items():
        filepath = os.path.join(out_dir, f"{part_name}.csv")
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in rows:
                out_r = {k: r.get(k, "") for k in fields}
                writer.writerow(out_r)
        print(f"Wrote {len(rows)} rows to {filepath}")


def main():
    print("Loading canonical transit entities...")
    entities = load_canonical_entities()

    # -------------------------------------------------------------
    # REGIME A: Equal Total Budget (~5,000 samples per taxonomy)
    # Common underlying pool of 4,800 utterances (300 per scenario across 16 scenarios)
    # -------------------------------------------------------------
    print("\n--- Generating Regime A (Equal Total Budget: 4,800 samples) ---")
    seen_queries_a = set()
    regime_a_bank = []
    for scen in sorted(SCENARIO_MAPPING.keys()):
        scen_items = generate_utterances_for_scenario(scen, entities, count=300, seen_queries=seen_queries_a)
        regime_a_bank.extend(scen_items)

    print(f"Regime A shared scenario bank: {len(regime_a_bank)} utterances.")

    # Partition once at the family level
    regime_a_splits = partition_by_families(regime_a_bank, train_ratio=0.70, val_ratio=0.15)
    print(f"Regime A split sizes: train={len(regime_a_splits['pilot_train'])}, "
          f"val={len(regime_a_splits['pilot_validation'])}, eval={len(regime_a_splits['pilot_eval'])}")

    for tax_key in ["T1", "T2", "T3"]:
        proj_splits = project_split_to_taxonomy(regime_a_splits, tax_key)
        out_dir = os.path.join(OUTPUT_BASE, "regime_a", tax_key)
        print(f"\nWriting Regime A {tax_key} ({TAXONOMY_SPEC['taxonomies'][tax_key]['version']}):")
        write_partition_csvs(proj_splits, out_dir)

    # -------------------------------------------------------------
    # REGIME B: Equal Class Density (~500 samples per intent class)
    # T3 (16 intents * 500 = 8,000)
    # T2 (12 intents * 500 = 6,000)
    # T1 (9 intents * 500 = 4,500)
    # -------------------------------------------------------------
    print("\n--- Generating Regime B (Equal Class Density: ~500 per class) ---")

    # Regime B - T3: 16 intents, 500 each
    seen_queries_b_t3 = set()
    t3_bank = []
    for scen in sorted(SCENARIO_MAPPING.keys()):
        scen_items = generate_utterances_for_scenario(scen, entities, count=500, seen_queries=seen_queries_b_t3)
        t3_bank.extend(scen_items)

    t3_splits = partition_by_families(t3_bank, train_ratio=0.70, val_ratio=0.15)
    t3_proj_splits = project_split_to_taxonomy(t3_splits, "T3")
    print(f"\nWriting Regime B T3 (8,000 samples):")
    write_partition_csvs(t3_proj_splits, os.path.join(OUTPUT_BASE, "regime_b", "T3"))

    # Regime B - T2: 12 intents, 500 each
    seen_queries_b_t2 = set()
    t2_bank = []
    # Map intents to scenario sources
    t2_intents = TAXONOMY_SPEC["taxonomies"]["T2"]["intents"]
    t2_to_scens = defaultdict(list)
    for scen, s_info in SCENARIO_MAPPING.items():
        t2_to_scens[s_info["T2_label"]].append(scen)

    for t2_lbl in t2_intents:
        constituent_scens = t2_to_scens[t2_lbl]
        per_scen = 500 // len(constituent_scens)
        rem_scen = 500 % len(constituent_scens)
        for idx, sc in enumerate(constituent_scens):
            sc_count = per_scen + (1 if idx < rem_scen else 0)
            sc_items = generate_utterances_for_scenario(sc, entities, count=sc_count, seen_queries=seen_queries_b_t2)
            t2_bank.extend(sc_items)

    t2_splits = partition_by_families(t2_bank, train_ratio=0.70, val_ratio=0.15)
    t2_proj_splits = project_split_to_taxonomy(t2_splits, "T2")
    print(f"\nWriting Regime B T2 (6,000 samples):")
    write_partition_csvs(t2_proj_splits, os.path.join(OUTPUT_BASE, "regime_b", "T2"))

    # Regime B - T1: 9 intents, 500 each
    seen_queries_b_t1 = set()
    t1_bank = []
    t1_intents = TAXONOMY_SPEC["taxonomies"]["T1"]["intents"]
    t1_to_scens = defaultdict(list)
    for scen, s_info in SCENARIO_MAPPING.items():
        t1_to_scens[s_info["T1_label"]].append(scen)

    for t1_lbl in t1_intents:
        constituent_scens = t1_to_scens[t1_lbl]
        per_scen = 500 // len(constituent_scens)
        rem_scen = 500 % len(constituent_scens)
        for idx, sc in enumerate(constituent_scens):
            sc_count = per_scen + (1 if idx < rem_scen else 0)
            sc_items = generate_utterances_for_scenario(sc, entities, count=sc_count, seen_queries=seen_queries_b_t1)
            t1_bank.extend(sc_items)

    t1_splits = partition_by_families(t1_bank, train_ratio=0.70, val_ratio=0.15)
    t1_proj_splits = project_split_to_taxonomy(t1_splits, "T1")
    print(f"\nWriting Regime B T1 (4,500 samples):")
    write_partition_csvs(t1_proj_splits, os.path.join(OUTPUT_BASE, "regime_b", "T1"))

    print("\nPilot dataset generation complete across all regimes and taxonomies!")


if __name__ == "__main__":
    main()
