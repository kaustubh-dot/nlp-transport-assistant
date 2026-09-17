#!/usr/bin/env python3
"""Builds the SQLite transport database (data/processed/transport.db)

and exports the multilingual alias lookup gazetteer (data/processed/aliases.csv).

Contains unverified demonstration fixtures for:
  - Chennai Metro Rail (Blue Line & Green Line)
  - Chennai Suburban Rail (South Line & Beach-Velachery MRTS)
  - Major Multimodal Interchange Hubs (Chennai Central, Egmore, Guindy, Airport, Koyambedu)
  - Station facilities, accessibility features, and service timings
"""

import os
import csv
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(DATA_PROCESSED_DIR, "transport.db")
ALIASES_CSV_PATH = os.path.join(DATA_PROCESSED_DIR, "aliases.csv")


# Core Chennai Stations Catalog
STATIONS = [
    # Metro Line 1 (Blue Line) & Interchanges
    {
        "station_id": "WIMCO_NAGAR",
        "name_en": "Wimco Nagar",
        "name_hi": "विमको नगर",
        "name_ta": "விம்கோ நகர்",
        "type": "metro",
        "lat": 13.1672,
        "lon": 80.3015
    },
    {
        "station_id": "WASHERMANPET",
        "name_en": "Washermanpet",
        "name_hi": "वाशरमैनपेट",
        "name_ta": "வண்ணாரப்பேட்டை",
        "type": "metro",
        "lat": 13.1098,
        "lon": 80.2825
    },
    {
        "station_id": "CHENNAI_CENTRAL",
        "name_en": "Chennai Central",
        "name_hi": "चेन्नई सेंट्रल",
        "name_ta": "சென்னை சென்ட்ரல்",
        "type": "railway_metro_interchange",
        "lat": 13.0827,
        "lon": 80.2755
    },
    {
        "station_id": "GOVERNMENT_ESTATE",
        "name_en": "Government Estate",
        "name_hi": "गवर्नमेंट एस्टेट",
        "name_ta": "அரசினர் தோட்டம்",
        "type": "metro",
        "lat": 13.0694,
        "lon": 80.2728
    },
    {
        "station_id": "AGS_DMS",
        "name_en": "AG-DMS",
        "name_hi": "एजी-डीएमएस",
        "name_ta": "ஏ.ஜி - டி.எம்.எஸ்",
        "type": "metro",
        "lat": 13.0441,
        "lon": 80.2483
    },
    {
        "station_id": "T_NAGAR",
        "name_en": "T. Nagar (Nandanam Metro)",
        "name_hi": "टी नगर",
        "name_ta": "தி. நகர்",
        "type": "metro_bus_hub",
        "lat": 13.0315,
        "lon": 80.2405
    },
    {
        "station_id": "GUINDY",
        "name_en": "Guindy",
        "name_hi": "गिंडी",
        "name_ta": "கிண்டி",
        "type": "metro_suburban_interchange",
        "lat": 13.0093,
        "lon": 80.2131
    },
    {
        "station_id": "ALANDUR",
        "name_en": "Alandur",
        "name_hi": "आलंदूर",
        "name_ta": "ஆலந்தூர்",
        "type": "metro_interchange",
        "lat": 13.0039,
        "lon": 80.2014
    },
    {
        "station_id": "CHENNAI_AIRPORT",
        "name_en": "Chennai Airport (Meenambakkam)",
        "name_hi": "चेन्नई एयरपोर्ट",
        "name_ta": "சென்னை விமான நிலையம்",
        "type": "metro_airport_interchange",
        "lat": 12.9808,
        "lon": 80.1639
    },

    # Metro Line 2 (Green Line)
    {
        "station_id": "CHENNAI_EGMORE",
        "name_en": "Chennai Egmore",
        "name_hi": "चेन्नई एग्मोर",
        "name_ta": "சென்னை எழும்பூர்",
        "type": "railway_metro_interchange",
        "lat": 13.0784,
        "lon": 80.2612
    },
    {
        "station_id": "KILPAUK",
        "name_en": "Kilpauk",
        "name_hi": "कीलपॉक",
        "name_ta": "கீழ்ப்பாக்கம்",
        "type": "metro",
        "lat": 13.0781,
        "lon": 80.2428
    },
    {
        "station_id": "SHENOY_NAGAR",
        "name_en": "Shenoy Nagar",
        "name_hi": "शेनॉय नगर",
        "name_ta": "செனாய் நகர்",
        "type": "metro",
        "lat": 13.0789,
        "lon": 80.2269
    },
    {
        "station_id": "KOYAMBEDU",
        "name_en": "Koyambedu (CMBT)",
        "name_hi": "कोयम्बेडु",
        "name_ta": "கோயம்பேடு",
        "type": "metro_bus_interchange",
        "lat": 13.0716,
        "lon": 80.1944
    },
    {
        "station_id": "VADAPALANI",
        "name_en": "Vadapalani",
        "name_hi": "वडापलानी",
        "name_ta": "வடபழனி",
        "type": "metro",
        "lat": 13.0514,
        "lon": 80.2117
    },
    {
        "station_id": "ST_THOMAS_MOUNT",
        "name_en": "St. Thomas Mount",
        "name_hi": "सेंट थॉमस माउंट",
        "name_ta": "பரங்கிமலை",
        "type": "metro_suburban_interchange",
        "lat": 12.9953,
        "lon": 80.1989
    },

    # Suburban & MRTS Stations
    {
        "station_id": "CHENNAI_BEACH",
        "name_en": "Chennai Beach",
        "name_hi": "चेन्नई बीच",
        "name_ta": "சென்னை கடற்கரை",
        "type": "suburban_terminal",
        "lat": 13.0924,
        "lon": 80.2934
    },
    {
        "station_id": "TAMBARAM",
        "name_en": "Tambaram",
        "name_hi": "ताम्बरम",
        "name_ta": "தாம்பரம்",
        "type": "suburban_railway_hub",
        "lat": 12.9249,
        "lon": 80.1165
    },
    {
        "station_id": "VELACHERY",
        "name_en": "Velachery",
        "name_hi": "वेलाचेरी",
        "name_ta": "வேளச்சேரி",
        "type": "mrts_terminal",
        "lat": 12.9790,
        "lon": 80.2185
    }
]

# Multilingual and Transliteration Aliases
ALIASES = [
    # Chennai Central
    ("CHENNAI_CENTRAL", "चेन्नई सेंट्रल", "hi", "Deva"),
    ("CHENNAI_CENTRAL", "सेंट्रल", "hi", "Deva"),
    ("CHENNAI_CENTRAL", "एमजीआर सेंट्रल", "hi", "Deva"),
    ("CHENNAI_CENTRAL", "मद्रास सेंट्रल", "hi", "Deva"),
    ("CHENNAI_CENTRAL", "chennai central", "en", "Latn"),
    ("CHENNAI_CENTRAL", "central", "en", "Latn"),
    ("CHENNAI_CENTRAL", "mgr central", "en", "Latn"),
    ("CHENNAI_CENTRAL", "chennai sentral", "hinglish", "Latn"),

    # Egmore
    ("CHENNAI_EGMORE", "चेन्नई एग्मोर", "hi", "Deva"),
    ("CHENNAI_EGMORE", "एग्मोर", "hi", "Deva"),
    ("CHENNAI_EGMORE", "एगमोर", "hi", "Deva"),
    ("CHENNAI_EGMORE", "chennai egmore", "en", "Latn"),
    ("CHENNAI_EGMORE", "egmore", "en", "Latn"),
    ("CHENNAI_EGMORE", "egmore station", "en", "Latn"),

    # Airport
    ("CHENNAI_AIRPORT", "चेन्नई एयरपोर्ट", "hi", "Deva"),
    ("CHENNAI_AIRPORT", "एयरपोर्ट", "hi", "Deva"),
    ("CHENNAI_AIRPORT", "हवाई अड्डा", "hi", "Deva"),
    ("CHENNAI_AIRPORT", "मीनम्बाक्कम", "hi", "Deva"),
    ("CHENNAI_AIRPORT", "chennai airport", "en", "Latn"),
    ("CHENNAI_AIRPORT", "airport", "en", "Latn"),
    ("CHENNAI_AIRPORT", "meenambakkam airport", "en", "Latn"),

    # Koyambedu
    ("KOYAMBEDU", "कोयम्बेडु", "hi", "Deva"),
    ("KOYAMBEDU", "कोयम्बेडू", "hi", "Deva"),
    ("KOYAMBEDU", "सीएमबीटी", "hi", "Deva"),
    ("KOYAMBEDU", "कोयम्बेडु बस स्टैंड", "hi", "Deva"),
    ("KOYAMBEDU", "koyambedu", "en", "Latn"),
    ("KOYAMBEDU", "cmbt", "en", "Latn"),

    # Guindy
    ("GUINDY", "गिंडी", "hi", "Deva"),
    ("GUINDY", "गुइंडी", "hi", "Deva"),
    ("GUINDY", "गिंडी स्टेशन", "hi", "Deva"),
    ("GUINDY", "guindy", "en", "Latn"),
    ("GUINDY", "guindy station", "en", "Latn"),

    # Tambaram
    ("TAMBARAM", "ताम्बरम", "hi", "Deva"),
    ("TAMBARAM", "तांबरम", "hi", "Deva"),
    ("TAMBARAM", "ताम्बरम स्टेशन", "hi", "Deva"),
    ("TAMBARAM", "tambaram", "en", "Latn"),
    ("TAMBARAM", "tambaram station", "en", "Latn"),

    # Alandur
    ("ALANDUR", "आलंदूर", "hi", "Deva"),
    ("ALANDUR", "अलनदूर", "hi", "Deva"),
    ("ALANDUR", "alandur", "en", "Latn"),
    ("ALANDUR", "alandur metro", "en", "Latn"),

    # Beach
    ("CHENNAI_BEACH", "चेन्नई बीच", "hi", "Deva"),
    ("CHENNAI_BEACH", "बीच स्टेशन", "hi", "Deva"),
    ("CHENNAI_BEACH", "chennai beach", "en", "Latn"),
    ("CHENNAI_BEACH", "beach", "en", "Latn"),

    # T Nagar
    ("T_NAGAR", "टी नगर", "hi", "Deva"),
    ("T_NAGAR", "टी. नगर", "hi", "Deva"),
    ("T_NAGAR", "त्यागराया नगर", "hi", "Deva"),
    ("T_NAGAR", "t nagar", "en", "Latn"),
    ("T_NAGAR", "t. nagar", "en", "Latn"),

    # Velachery
    ("VELACHERY", "वेलाचेरी", "hi", "Deva"),
    ("VELACHERY", "velachery", "en", "Latn"),

    # Wimco Nagar
    ("WIMCO_NAGAR", "विमको नगर", "hi", "Deva"),
    ("WIMCO_NAGAR", "wimco nagar", "en", "Latn"),

    # St Thomas Mount
    ("ST_THOMAS_MOUNT", "सेंट थॉमस माउंट", "hi", "Deva"),
    ("ST_THOMAS_MOUNT", "थॉमस माउंट", "hi", "Deva"),
    ("ST_THOMAS_MOUNT", "st thomas mount", "en", "Latn")
]

# Transit Connections (Direct Routes)
CONNECTIONS = [
    # Metro Blue Line: Central <-> Airport (Via Guindy, Alandur)
    ("CHENNAI_CENTRAL", "CHENNAI_AIRPORT", "metro", "Blue Line (विमको नगर - एयरपोर्ट)", 40, 20.0, 1),
    ("CHENNAI_AIRPORT", "CHENNAI_CENTRAL", "metro", "Blue Line (विमको नगर - एयरपोर्ट)", 40, 20.0, 1),
    ("CHENNAI_CENTRAL", "GUINDY", "metro", "Blue Line", 25, 12.0, 1),
    ("GUINDY", "CHENNAI_CENTRAL", "metro", "Blue Line", 25, 12.0, 1),
    ("GUINDY", "CHENNAI_AIRPORT", "metro", "Blue Line", 15, 8.0, 1),
    ("CHENNAI_AIRPORT", "GUINDY", "metro", "Blue Line", 15, 8.0, 1),
    ("CHENNAI_CENTRAL", "ALANDUR", "metro", "Blue Line", 28, 14.0, 1),
    ("ALANDUR", "CHENNAI_CENTRAL", "metro", "Blue Line", 28, 14.0, 1),
    ("ALANDUR", "CHENNAI_AIRPORT", "metro", "Blue Line", 12, 6.0, 1),
    ("CHENNAI_AIRPORT", "ALANDUR", "metro", "Blue Line", 12, 6.0, 1),

    # Metro Green Line: Central <-> Egmore <-> Koyambedu <-> St Thomas Mount
    ("CHENNAI_CENTRAL", "CHENNAI_EGMORE", "metro", "Green Line (सेंट्रल - सेंट थॉमस माउंट)", 5, 2.5, 1),
    ("CHENNAI_EGMORE", "CHENNAI_CENTRAL", "metro", "Green Line", 5, 2.5, 1),
    ("CHENNAI_CENTRAL", "KOYAMBEDU", "metro", "Green Line", 22, 10.5, 1),
    ("KOYAMBEDU", "CHENNAI_CENTRAL", "metro", "Green Line", 22, 10.5, 1),
    ("CHENNAI_EGMORE", "KOYAMBEDU", "metro", "Green Line", 18, 8.5, 1),
    ("KOYAMBEDU", "CHENNAI_EGMORE", "metro", "Green Line", 18, 8.5, 1),
    ("KOYAMBEDU", "ALANDUR", "metro", "Green Line", 15, 7.5, 1),
    ("ALANDUR", "KOYAMBEDU", "metro", "Green Line", 15, 7.5, 1),
    ("KOYAMBEDU", "CHENNAI_AIRPORT", "metro", "Green Line -> Blue Line (आलंदूर पर बदलें)", 32, 14.0, 0),
    ("CHENNAI_AIRPORT", "KOYAMBEDU", "metro", "Blue Line -> Green Line (आलंदूर पर बदलें)", 32, 14.0, 0),
    ("CHENNAI_EGMORE", "CHENNAI_AIRPORT", "metro", "Green Line -> Blue Line (सेंट्रल या आलंदूर पर बदलें)", 42, 21.0, 0),

    # Suburban Rail: Beach <-> Central/Park <-> Egmore <-> Guindy <-> Tambaram
    ("CHENNAI_CENTRAL", "TAMBARAM", "suburban_rail", "South Line (चेन्नई बीच - तांबरम)", 45, 28.0, 1),
    ("TAMBARAM", "CHENNAI_CENTRAL", "suburban_rail", "South Line (तांबरम - चेन्नई बीच)", 45, 28.0, 1),
    ("CHENNAI_EGMORE", "TAMBARAM", "suburban_rail", "South Line", 40, 25.0, 1),
    ("TAMBARAM", "CHENNAI_EGMORE", "suburban_rail", "South Line", 40, 25.0, 1),
    ("GUINDY", "TAMBARAM", "suburban_rail", "South Line", 25, 15.0, 1),
    ("TAMBARAM", "GUINDY", "suburban_rail", "South Line", 25, 15.0, 1),
    ("CHENNAI_BEACH", "TAMBARAM", "suburban_rail", "South Line", 50, 30.0, 1),
    ("TAMBARAM", "CHENNAI_BEACH", "suburban_rail", "South Line", 50, 30.0, 1),
    ("CHENNAI_BEACH", "VELACHERY", "suburban_rail", "MRTS Line (चेन्नई बीच - वेलाचेरी)", 40, 19.0, 1),
    ("VELACHERY", "CHENNAI_BEACH", "suburban_rail", "MRTS Line", 40, 19.0, 1),

    # MTC Buses: Major Corridors
    ("CHENNAI_CENTRAL", "KOYAMBEDU", "bus", "MTC Route 15B / 27B", 35, 11.0, 1),
    ("KOYAMBEDU", "CHENNAI_CENTRAL", "bus", "MTC Route 15B / 27B", 35, 11.0, 1),
    ("CHENNAI_CENTRAL", "T_NAGAR", "bus", "MTC Route 11G / 18A", 30, 9.0, 1),
    ("T_NAGAR", "CHENNAI_CENTRAL", "bus", "MTC Route 11G / 18A", 30, 9.0, 1),
    ("KOYAMBEDU", "TAMBARAM", "bus", "MTC Route 70 / 70A", 55, 24.0, 1),
    ("TAMBARAM", "KOYAMBEDU", "bus", "MTC Route 70 / 70A", 55, 24.0, 1)
]

# Station Facilities & Accessibility
FACILITIES = [
    {
        "station_id": "CHENNAI_CENTRAL",
        "wheelchair_available": 1,
        "lift_available": 1,
        "tactile_paths": 1,
        "accessible_toilet": 1,
        "parking_available": 1,
        "notes_hi": "सेंट्रल स्टेशन पर व्हीलचेयर, स्वचालित लिफ्ट, एस्केलेटर और समर्पित दिव्यांग पार्किंग उपलब्ध है।"
    },
    {
        "station_id": "CHENNAI_EGMORE",
        "wheelchair_available": 1,
        "lift_available": 1,
        "tactile_paths": 1,
        "accessible_toilet": 1,
        "parking_available": 1,
        "notes_hi": "एग्मोर स्टेशन पर लिफ्ट, व्हीलचेयर सहायता और विशेष टिकट काउंटर उपलब्ध हैं।"
    },
    {
        "station_id": "CHENNAI_AIRPORT",
        "wheelchair_available": 1,
        "lift_available": 1,
        "tactile_paths": 1,
        "accessible_toilet": 1,
        "parking_available": 1,
        "notes_hi": "एयरपोर्ट स्टेशन हवाई अड्डा टर्मिनल से सीधे एयरोब्रिज और लिफ्ट द्वारा जुड़ा हुआ है।"
    },
    {
        "station_id": "KOYAMBEDU",
        "wheelchair_available": 1,
        "lift_available": 1,
        "tactile_paths": 1,
        "accessible_toilet": 1,
        "parking_available": 1,
        "notes_hi": "सीएमबीटी बस स्टैंड और मेट्रो के बीच व्हीलचेयर रैंप और लिफ्ट उपलब्ध हैं।"
    },
    {
        "station_id": "GUINDY",
        "wheelchair_available": 1,
        "lift_available": 1,
        "tactile_paths": 1,
        "accessible_toilet": 1,
        "parking_available": 1,
        "notes_hi": "गिंडी मेट्रो स्टेशन पर लिफ्ट और स्पर्श पथ की सुविधा है।"
    },
    {
        "station_id": "ALANDUR",
        "wheelchair_available": 1,
        "lift_available": 1,
        "tactile_paths": 1,
        "accessible_toilet": 1,
        "parking_available": 1,
        "notes_hi": "इंटरचेंज स्टेशन होने के कारण दोनों स्तरों पर बहु-लिफ्ट एवं व्हीलचेयर सहायता मौजूद है।"
    },
    {
        "station_id": "TAMBARAM",
        "wheelchair_available": 1,
        "lift_available": 1,
        "tactile_paths": 0,
        "accessible_toilet": 1,
        "parking_available": 1,
        "notes_hi": "तांबरम रेलवे स्टेशन पर व्हीलचेयर और फुट-ओवर-ब्रिज पर लिफ्ट उपलब्ध है।"
    }
]

# Service Timings & Operational Info
SERVICE_INFO = [
    {
        "route_id": "CMRL_BLUE",
        "mode": "metro",
        "line_name": "ब्लू लाइन (विमको नगर - एयरपोर्ट)",
        "first_service": "05:00",
        "last_service": "23:00",
        "peak_frequency_mins": 6,
        "non_peak_frequency_mins": 12,
        "min_fare": 10.0,
        "max_fare": 50.0
    },
    {
        "route_id": "CMRL_GREEN",
        "mode": "metro",
        "line_name": "ग्रीन लाइन (चेन्नई सेंट्रल - सेंट थॉमस माउंट)",
        "first_service": "05:00",
        "last_service": "23:00",
        "peak_frequency_mins": 6,
        "non_peak_frequency_mins": 12,
        "min_fare": 10.0,
        "max_fare": 50.0
    },
    {
        "route_id": "SR_SOUTH_SUBURBAN",
        "mode": "suburban_rail",
        "line_name": "उपनगरीय दक्षिण लाइन (बीच - तांबरम - चेंगलपट्टू)",
        "first_service": "04:15",
        "last_service": "23:50",
        "peak_frequency_mins": 10,
        "non_peak_frequency_mins": 20,
        "min_fare": 5.0,
        "max_fare": 15.0
    },
    {
        "route_id": "MTC_CORE",
        "mode": "bus",
        "line_name": "एमटीसी बस सेवाएं (प्रमुख शहर मार्ग)",
        "first_service": "04:30",
        "last_service": "22:30",
        "peak_frequency_mins": 8,
        "non_peak_frequency_mins": 15,
        "min_fare": 5.0,
        "max_fare": 30.0
    }
]


def init_db():
    """Initializes tables in SQLite database."""
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Stations table
    cursor.execute("""
        CREATE TABLE stations (
            station_id TEXT PRIMARY KEY,
            name_en TEXT NOT NULL,
            name_hi TEXT NOT NULL,
            name_ta TEXT,
            type TEXT NOT NULL,
            latitude REAL,
            longitude REAL
        )
    """)

    # 2. Station Aliases table
    cursor.execute("""
        CREATE TABLE station_aliases (
            alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT NOT NULL,
            alias TEXT NOT NULL,
            language TEXT NOT NULL,
            script TEXT NOT NULL,
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        )
    """)

    # 3. Connections table
    cursor.execute("""
        CREATE TABLE connections (
            connection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_id TEXT NOT NULL,
            destination_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            line_name TEXT NOT NULL,
            travel_time_mins INTEGER,
            distance_km REAL,
            direct INTEGER DEFAULT 1,
            FOREIGN KEY (origin_id) REFERENCES stations(station_id),
            FOREIGN KEY (destination_id) REFERENCES stations(station_id)
        )
    """)

    # 4. Facilities table
    cursor.execute("""
        CREATE TABLE facilities (
            station_id TEXT PRIMARY KEY,
            wheelchair_available INTEGER DEFAULT NULL CHECK (wheelchair_available IN (0, 1)),
            lift_available INTEGER DEFAULT NULL CHECK (lift_available IN (0, 1)),
            tactile_paths INTEGER DEFAULT NULL CHECK (tactile_paths IN (0, 1)),
            accessible_toilet INTEGER DEFAULT NULL CHECK (accessible_toilet IN (0, 1)),
            parking_available INTEGER DEFAULT NULL CHECK (parking_available IN (0, 1)),
            notes_hi TEXT,
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        )
    """)

    # 5. Service Info table
    cursor.execute("""
        CREATE TABLE service_info (
            route_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            line_name TEXT NOT NULL,
            first_service TEXT NOT NULL,
            last_service TEXT NOT NULL,
            peak_frequency_mins INTEGER,
            non_peak_frequency_mins INTEGER,
            min_fare REAL,
            max_fare REAL
        )
    """)

    # Insert Stations
    for s in STATIONS:
        cursor.execute(
            "INSERT INTO stations VALUES (?, ?, ?, ?, ?, ?, ?)",
            (s["station_id"], s["name_en"], s["name_hi"], s["name_ta"], s["type"], s["lat"], s["lon"])
        )

    # Insert Aliases
    for station_id, alias, lang, script in ALIASES:
        cursor.execute(
            "INSERT INTO station_aliases (station_id, alias, language, script) VALUES (?, ?, ?, ?)",
            (station_id, alias, lang, script)
        )

    # Insert Connections
    for conn_data in CONNECTIONS:
        cursor.execute(
            "INSERT INTO connections (origin_id, destination_id, mode, line_name, travel_time_mins, distance_km, direct) VALUES (?, ?, ?, ?, ?, ?, ?)",
            conn_data
        )

    # Insert Facilities
    for f in FACILITIES:
        cursor.execute(
            "INSERT INTO facilities VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f["station_id"], f["wheelchair_available"], f["lift_available"], f["tactile_paths"], f["accessible_toilet"], f["parking_available"], f["notes_hi"])
        )

    # Insert Service Info
    for si in SERVICE_INFO:
        cursor.execute(
            "INSERT INTO service_info VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (si["route_id"], si["mode"], si["line_name"], si["first_service"], si["last_service"], si["peak_frequency_mins"], si["non_peak_frequency_mins"], si["min_fare"], si["max_fare"])
        )

    conn.commit()
    conn.close()
    print(f"✅ Successfully initialized SQLite database at: {DB_PATH}")


def export_aliases_csv():
    """Exports aliases list into data/processed/aliases.csv for gazetteer lookups."""
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    with open(ALIASES_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["station_id", "alias", "language", "script"])
        for row in ALIASES:
            writer.writerow(row)
    print(f"✅ Successfully exported aliases gazetteer to: {ALIASES_CSV_PATH}")


if __name__ == "__main__":
    init_db()
    export_aliases_csv()
