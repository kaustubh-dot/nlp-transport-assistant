"""Academic intent demo with the existing canonical gazetteer and sourced lookup."""
from __future__ import annotations

import json
import re
from pathlib import Path

from src.nlp_v2.text import normalize_extraction_text
from .model import LABELS, ProjectIntentClassifier
from .locations import index_for
from .lookup import curated_journey_guidance, published_route_options
from src.nlp_v2.domain import CanonicalTransitService
from src.nlp_v2.slots import T3SlotExtractor

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / 'data/project/chennai_case_study.json'
MODES = {'metro': ('मेट्रो', 'metro'), 'bus': ('बस', 'bus'),
         'rail': ('रेलवे', 'ट्रेन', 'रेल', 'रेलगाड़ी', 'रेलगाडी', 'train', 'railway', 'railgadi', 'railgaadi', 'rail'),
         'mrts': ('mrts', 'एमआरटीएस'),
         'walking': ('पैदल', 'walking')}

HINGLISH_RESPONSES = {
    'इस छोटे डेमो में एक मूल स्थान और एक गंतव्य लिखें।': 'Is chhote demo mein ek origin aur ek destination likhein.',
    'आपका प्रश्न ट्रेन की देरी या स्थिति के बारे में है। इस प्रोटोटाइप में लाइव ट्रेन डेटा नहीं है; रेलवे की आधिकारिक जानकारी या स्टेशन कर्मचारियों से पुष्टि करें।': 'Aapka sawal train ki deri ya status ke baare mein hai. Is prototype mein live train data nahi hai; official railway information ya station staff se confirm karein.',
    'आपका प्रश्न रेलवे शिकायत के रूप में पहचाना गया है। यह NLP डेमो शिकायत दर्ज नहीं करता; संबंधित रेलवे कर्मचारियों या आधिकारिक शिकायत माध्यम से संपर्क करें।': 'Aapka sawal railway complaint ke roop mein pehchana gaya hai. Yeh NLP demo complaint submit nahi karta; railway staff ya official complaint channel se sampark karein.',
    'यह परियोजना चुने हुए चेन्नई स्टेशनों के परिवहन संबंधी हिंदी प्रश्नों के लिए है।': 'Yeh project chune hue Chennai stations ke Hindi aur Hinglish transport sawaalon ke liye hai.',
    'आपका प्रश्न टिकट या किराये से संबंधित है। इस छोटे डेमो में टिकट बुकिंग और वर्तमान किराये उपलब्ध नहीं हैं। आधिकारिक टिकट सेवा पर जाँचें।': 'Aapka sawal ticket ya kiraye se juda hai. Is chhote demo mein ticket booking aur current fares available nahi hain. Official ticket service par check karein.',
    'माँगी गई सेवा का वर्तमान समय इस छोटे कैटलॉग में नहीं है। पहली/आखिरी ट्रेन या प्रस्थान का समय अनुमान से नहीं बताया जा सकता।': 'Maangi gayi service ka current time is chhote catalog mein nahi hai. First/last train ya departure ka time andaaze se nahi bataya ja sakta.',
    'इस छोटे डेमो में नकारात्मक या बहु-भाग वाले मार्ग प्रश्न स्पष्ट करें। कौन सा परिवहन विकल्प चाहिए?': 'Is chhote demo mein negative ya multiple-part route sawal clear karein. Kaunsa transport option chahiye?',
    'किस स्टेशन और किस सुविधा—लिफ्ट या व्हीलचेयर—के बारे में जानना चाहते हैं?': 'Kis station aur kis facility—lift ya wheelchair—ke baare mein jaanna chahte hain?',
    'कैटलॉग की सुगम्यता जानकारी सेंट्रल मेट्रो के लिए है। रेलवे या मेट्रो स्टेशन स्पष्ट करें।': 'Catalog ki accessibility information Central Metro ke liye hai. Railway ya Metro station clear karein.',
    'इस स्टेशन की माँगी गई सुगम्यता सुविधा की जानकारी छोटे कैटलॉग में नहीं है।': 'Is station ki maangi gayi accessibility facility ki information chhote catalog mein nahi hai.',
    'स्टेशन का पूरा नाम लिखें।': 'Station ka poora naam likhein.',
    'मूल स्थान छोटे कैटलॉग में पहचाना नहीं गया। चुने हुए स्थानों में सेंट्रल, एग्मोर, तांबरम, अवडी, एयरपोर्ट, कोयंबेडु और गिंडी हैं।': 'Origin chhote catalog mein pehchana nahi gaya. Selected locations Central, Egmore, Tambaram, Avadi, Airport, Koyambedu aur Guindy hain.',
    'गंतव्य छोटे कैटलॉग में पहचाना नहीं गया। चुने हुए स्थानों में एयरपोर्ट, कोयंबेडु, गिंडी, सेंट्रल, एग्मोर, तांबरम और अवडी हैं।': 'Destination chhote catalog mein pehchana nahi gaya. Selected locations Airport, Koyambedu, Guindy, Central, Egmore, Tambaram aur Avadi hain.',
    'इस मूल स्थान, गंतव्य और परिवहन माध्यम का कनेक्शन छोटे केस-स्टडी कैटलॉग में नहीं है। इसका अर्थ यह नहीं कि वास्तविक सेवा उपलब्ध नहीं है।': 'Is origin, destination aur transport mode ka connection chhote case-study catalog mein nahi hai. Iska matlab yeh nahi ki real service available nahi hai.',
    'इस स्टेशन की माँगी गई विस्तृत जानकारी छोटे कैटलॉग में नहीं है। स्टेशन कर्मचारियों से पुष्टि करें।': 'Is station ki maangi gayi detailed information chhote catalog mein nahi hai. Station staff se confirm karein.',
}


def hinglish_response(text: str, records: list[dict], places: dict, slots: dict, intent: str) -> str:
    if text in HINGLISH_RESPONSES:
        return HINGLISH_RESPONSES[text]
    if records and records[0].get('type') == 'terminal_service_window':
        row = records[0]
        return (f"16 October 2024 ke CMRL weekday publication mein Central Green Line terminal ka service window "
                f"{row['first_service']}–{row['last_service']} recorded hai. Yeh purana example hai, aaj ka timetable "
                'ya kisi destination ki first/last train nahi. Current official timetable check karein.')
    if records and records[0].get('mode') == 'bus':
        row = records[0]
        response = (f"Community GTFS snapshot mein bus {row['route_name']} ka stop order {row['boarding_stop']} se "
                    f"{row['alighting_stop']} recorded hai. Yeh current service ya railway station se walking access ki confirmation nahi. ")
        if row['destination'] == 'airport':
            response += 'Airport Metro stop ko airport terminal tak poori journey na maanein. '
        return response + 'Stop aur service locally check karein.'
    if records and 'feature' in records[0]:
        if records[0]['feature'] == 'lift':
            return 'Central Metro ke official station page par street, concourse aur platform ke beech lifts listed hain. Current working status station par check karein.'
        return 'Central Metro ke official station page par wheelchair facility listed hai. Availability station staff se confirm karein.'
    if records and 'line_hi' in records[0]:
        row = records[0]
        line = 'Blue Line' if row['line_hi'] == 'ब्लू लाइन' else 'Green Line'
        return (places[row['origin']]['name_en'] + ' Metro se ' + places[row['destination']]['name_en']
                + ' ke liye ' + line + ' ki published connectivity recorded hai. Yeh live service ya railway-to-metro walking/accessibility ki confirmation nahi hai.')
    if records and 'id' in records[0]:
        place = records[0]
        if intent in {'route_query', 'service_availability'} and 'destination' not in slots and slots.get('transport_mode') == 'bus':
            return (place['name_en'] + ' ke paas catalog mein ' + place['nearby_bus_name']
                    + ' bus stop recorded hai. Kisi destination ki bus service confirm karne ke liye destination likhein.')
        response = place['name_en'] + ' is project ke selected locations mein hai.'
        if place.get('nearby_bus_name'):
            response += ' Canonical snapshot mein nearby bus stop ' + place['nearby_bus_name'] + ' recorded hai.'
        return response + ' Yeh current service ya accessible walking route ki confirmation nahi hai.'
    raise ValueError('Missing Hinglish response template')


def extract_entities(query: str, catalog: dict, context_station: str | None = None) -> dict:
    text = normalize_extraction_text(query)
    accepted = [(row['span'].start, row['span'].end, row['value']) for row in index_for(catalog).mentions(query)]
    places = []
    for _, _, place in accepted:
        if place not in places:
            places.append(place)
    slots = {}
    from_suffix = r'\s*(?:(?:(?:रेलवे|मेट्रो|railway|metro)\s*)?(?:स्टेशन|station)\s*|(?:मेट्रो|metro)\s*)?(?:से|se)(?!\w)'
    if len(places) == 1:
        slots['station'] = places[0]
        if any(re.match(from_suffix, text[end:]) for _, end, _ in accepted):
            slots['origin'] = places[0]
    elif len(places) == 2:
        from_places = [place for start, end, place in accepted
                       if re.match(from_suffix, text[end:])
                       or re.search(r'(?<!\w)from\s*$', text[:start])]
        origin = from_places[0] if len(set(from_places)) == 1 else places[0]
        slots.update(origin=origin, destination=next(place for place in places if place != origin))
    elif len(places) > 2:
        slots['ambiguous_locations'] = places
    if not places and context_station and re.search(r'इस\s+स्टेशन|यहाँ|यहां|is\s+station|yahan|yahaan', text):
        slots['station'] = context_station
        if re.search(r'इस\s+स्टेशन\s+से|यहाँ\s+से|यहां\s+से|is\s+station\s+se|yaha[an]*\s+se', text):
            slots['origin'] = context_station
    modes = []
    for mode, words in MODES.items():
        hits = [match for word in words for match in re.finditer(r'(?<!\w)' + re.escape(word) + r'(?!\w)', text)]
        # A railway-station qualifier names the origin; it does not request rail travel.
        hits = [match for match in hits if not (mode == 'rail' and re.match(r'\s+(?:station|स्टेशन)(?!\w)', text[match.end():]))]
        if re.search(r'(?<!\w)(?:पास|नज़दीक|नजदीक|paas|nazdeek|najdeek|near|nearby|nearest|closest)(?!\w)', text):
            # Mode words inside the named anchor (Guindy metro station) are
            # separate from the requested nearby target (a bus stop).
            hits = [match for match in hits if not any(start <= match.start() < end for start, end, _ in accepted)]
        if hits:
            modes.append(mode)
    # "metro ki last train" names a metro service, not two requested modes.
    metro_train = r'(?:मेट्रो|metro)(?:\s+(?:की|ki|आखिरी|पहली|aakhri|aakhiri|pehli|last|first)){0,3}\s+(?:ट्रेन|train)(?!\w)'
    if 'metro' in modes and 'rail' in modes and re.search(metro_train, text):
        modes.remove('rail')
    if 'mrts' in modes and 'rail' in modes and re.search(r'(?:mrts|एमआरटीएस)\s+(?:train|ट्रेन)', text):
        modes.remove('rail')
    if modes:
        slots['transport_mode'] = modes[0] if len(modes) == 1 else modes
    for kind, words in [('last_service', ('आखिरी', 'अंतिम', 'aakhiri', 'aakhri', 'akhri', 'last')),
                        ('first_service', ('पहली', 'पहला', 'सबसे पहले', 'pehli', 'pehla', 'pehle', 'first')),
                        ('frequency', ('अंतराल', 'gap', 'frequency')),
                        ('scheduled_departure', ('अगली', 'अगला', 'next', 'agla')),
                        ('timetable', ('समय-सारणी', 'समय सारणी', 'timetable', 'शुरू', 'बंद', 'shuru', 'band')),
                        ('availability', ('उपलब्ध', 'मिलती', 'है क्या', 'available', 'milti', 'hai kya'))]:
        if any(word in text for word in words):
            slots['information_type'] = kind
            break
    for feature, words in [('wheelchair', ('व्हीलचेयर', 'wheelchair')),
                           ('lift', ('लिफ्ट', 'lift', 'एलिवेटर'))]:
        if any(word in text for word in words):
            slots['accessibility_feature'] = feature
    for detail, words in [('nearby_bus', ('बस स्टॉप', 'बस अड्डे', 'बस अड्डा', 'बस स्टेशन', 'bus stop', 'bus stand', 'bus station', 'bus terminal')),
                          ('address', ('पता', 'address')), ('platforms', ('प्लेटफॉर्म', 'platform')),
                          ('water', ('पीने', 'peene')), ('office', ('कार्यालय', 'office')),
                          ('entry', ('प्रवेश', 'entry'))]:
        if any(word in text for word in words):
            slots['station_detail'] = detail
            break
    for kind, words in [('cleanliness', ('सफाई', 'गंदा', 'गंदगी', 'safai', 'ganda', 'gandagi')),
                        ('water', ('पानी', 'paani', 'pani')), ('food', ('भोजन', 'खाना', 'khana', 'food')),
                        ('staff', ('कर्मचारी', 'व्यवहार', 'staff', 'behaviour')), ('safety', ('सुरक्षा', 'safety')),
                        ('coach_facility', ('कोच', 'खिड़की', 'coach', 'khidki'))]:
        if any(word in text for word in words):
            slots['complaint_type'] = kind
            break
    return slots


class HindiProjectAssistant:
    def __init__(self, classifier=None, catalog_path: Path = CATALOG):
        self.classifier = classifier if classifier is not None else ProjectIntentClassifier()
        self.catalog = json.loads(Path(catalog_path).read_text(encoding='utf-8'))
        self.location_index = index_for(self.catalog)
        self.places = self.location_index.places
        self.service = CanonicalTransitService()
        self.canonical_extractor = T3SlotExtractor(self.location_index.resolver)

    def process_query(self, query: str, context_station: str | None = None) -> dict:
        if not isinstance(query, str) or not query.strip():
            raise ValueError('कृपया हिंदी में प्रश्न लिखें।')
        if context_station is not None and (context_station not in self.places or not self.places[context_station].get('origin')):
            raise ValueError('Unknown case-study station')
        intent, score = self.classifier.predict(query)
        if intent not in LABELS:
            raise ValueError('Classifier returned an unknown project intent')
        slots = extract_entities(query, self.catalog, context_station)
        if intent != 'railway_complaint':
            slots.pop('complaint_type', None)
        if intent != 'station_information':
            slots.pop('station_detail', None)
        elif re.search(r'(?<!\w)(?:पास|नज़दीक|नजदीक|paas|nazdeek|najdeek|near|nearby|nearest|closest)(?!\w)', normalize_extraction_text(query)):
            if isinstance(slots.get('transport_mode'), str) and slots['transport_mode'] in {'metro', 'rail', 'mrts'} and not slots.get('station_detail'):
                slots['station_detail'] = 'nearby_transport'
        mentions = self.location_index.mentions(query)
        matches, canonical_slots, ambiguities = self.location_index.describe(mentions, slots, query)
        result = {'query': query, 'intent': intent, 'model_score': score,
                  'entities': slots, 'status': 'unavailable', 'response_hi': '', 'records': [], 'sources': [],
                  'location_matches': matches, 'canonical_slots': canonical_slots,
                  'location_ambiguities': ambiguities,
                  'entity_labels': {row['value']: self.places.get(row['value'], {}).get('name_en', row['surface'])
                                    for row in matches}}

        def respond(status, text, records=None, sources=None, hinglish=None):
            records = records or []
            result.update(status=status, response_hi=text,
                          response_hinglish=hinglish if hinglish is not None else hinglish_response(text, records, self.places, slots, intent),
                          records=records, sources=sources or [])
            return result

        def canonical_route_reply():
            if slots.get('transport_mode') == 'walking':
                return respond('unavailable', 'सत्यापित पैदल मार्ग इस डेटाबेस में उपलब्ध नहीं है। इसका अर्थ यह नहीं कि वास्तविक पैदल रास्ता नहीं है।',
                               hinglish='Verified walking route is database mein available nahi hai. Iska matlab yeh nahi ki real walking path nahi hai.')
            extracted = self.canonical_extractor.extract(query, 'point_to_point_route')
            blocked = (isinstance(slots.get('transport_mode'), list) or extracted.multiple_execution_scopes
                       or extracted.excluded_modes or extracted.unsupported_temporal_scope or extracted.missing_execution_slots
                       or extracted.clarification_reason not in {None, 'entity_ambiguity'})
            if intent in {'route_query', 'service_availability'} and blocked:
                return respond('clarification', 'एक स्पष्ट यात्रा और समय/परिवहन की शर्तें लिखें।',
                               hinglish='Ek clear journey aur time/transport ki conditions likhein.')
            if intent in {'route_query', 'service_availability'} and not any(key in extracted.slots for key in
                    ('date', 'time', 'temporal_relative', 'route_number', 'line_name', 'via', 'preference')):
                guidance = curated_journey_guidance(self.catalog, matches, slots)
                if guidance:
                    row = guidance[0]
                    return respond('information', row['description_hi'], guidance,
                                   [self.catalog['sources'][row['source']], self.catalog['sources']['canonical']], hinglish=row['description_hinglish'])
            if ambiguities and intent in {'route_query', 'service_availability'} and not extracted.slots.get('via'):
                routes, truncated = published_route_options(self.service, matches, slots, extracted.slots, self.catalog)
                if routes:
                    descriptions = []
                    for row in routes:
                        descriptions.append(f"{row['route_name']} ({row['mode']}): {self.places[row['origin_stop_id']]['name_en']} → {self.places[row['destination_stop_id']]['name_en']}")
                    detail = '; '.join(list(dict.fromkeys(descriptions))[:3])
                    partial_hi = ' कुछ बीच के स्टॉप की कवरेज अधूरी है।' if any(row['partial_topology'] for row in routes) else ''
                    partial_en = ' Kuch intermediate stops ki coverage incomplete hai.' if any(row['partial_topology'] for row in routes) else ''
                    result['route_options_truncated'] = truncated
                    return respond('information', f'प्रकाशित रिकॉर्ड में ये यात्रा विकल्प मिले: {detail}।{partial_hi} दिखाए गए चढ़ने/उतरने के स्टॉप जाँचें। यह स्नैपशॉट है; वर्तमान सेवा या पैदल पहुँच की पुष्टि नहीं है।',
                                   [{'type': 'canonical_route_option', **row} for row in routes], [self.catalog['sources']['canonical']],
                                   hinglish=f'Published records mein yeh travel options mile: {detail}.{partial_en} Dikhaye gaye boarding/alighting stops check karein. Yeh snapshot hai; current service ya walking access ki confirmation nahi hai.')
                requested = slots.get('transport_mode')
                if requested:
                    allowed = {'suburban_rail', 'mrts'} if requested == 'rail' else {requested}
                    unmatched = [match['surface'] for role in ('origin', 'destination') for match in matches
                                 if match['value'] == slots.get(role) and not any(candidate['mode'] in allowed for candidate in match['candidates'])]
                    if unmatched:
                        names = ', '.join(dict.fromkeys(unmatched))
                        return respond('unavailable', f'स्थान पहचाने गए हैं, लेकिन {names} के लिए माँगे गए {requested} स्टेशन/मार्ग का रिकॉर्ड नहीं मिला। आपका परिवहन माध्यम समझ लिया गया है; उसी माध्यम का सत्यापित कनेक्शन उपलब्ध नहीं है।',
                                       sources=[self.catalog['sources']['canonical']],
                                       hinglish=f'Locations pehchane gaye hain, lekin {names} ke liye maange gaye {requested} station/route ka record nahi mila. Aapka transport mode samajh liya gaya hai; usi mode ka verified connection available nahi hai.')
            if ambiguities:
                names = ', '.join(dict.fromkeys(row['surface'] for row in ambiguities))
                return respond('clarification', f'{names} नाम डेटाबेस में पहचाने गए हैं, लेकिन एक से अधिक स्टेशन/स्टॉप मिलते हैं। मेट्रो, रेलवे, MRTS या बस और पूरा स्टेशन/स्टॉप नाम लिखें।',
                               sources=[self.catalog['sources']['canonical']],
                               hinglish=f'{names} database mein pehchane gaye hain, lekin ek se zyada station/stop matches hain. Metro, railway, MRTS ya bus aur poora station/stop naam likhein.')
            if not all(key in canonical_slots for key in ('origin', 'destination')):
                return respond('unavailable', 'स्थान पहचाने गए हैं, लेकिन इस मार्ग का रिकॉर्ड उपलब्ध नहीं है। इसका अर्थ यह नहीं कि वास्तविक सेवा उपलब्ध नहीं है।',
                               hinglish='Locations pehchane gaye hain, lekin is route ka record available nahi hai. Iska matlab yeh nahi ki real service available nahi hai.')
            execution = dict(extracted.slots, **{key: value for key, value in canonical_slots.items() if key in {'origin', 'destination'}})
            if isinstance(slots.get('transport_mode'), str):
                execution['transport_mode'] = {'rail': 'suburban_rail'}.get(slots['transport_mode'], slots['transport_mode'])
            if isinstance(slots.get('transport_mode'), list) or extracted.clarification_reason or extracted.multiple_execution_scopes or extracted.excluded_modes or extracted.unsupported_temporal_scope or extracted.missing_execution_slots:
                return respond('clarification', 'एक परिवहन माध्यम और स्पष्ट मूल स्थान/गंतव्य लिखें।',
                               hinglish='Ek transport mode aur clear origin/destination likhein.')
            answer = self.service.execute('PLAN_ROUTE', execution)
            if answer.status != 'ok':
                return respond('unavailable', 'स्थान डेटाबेस में पहचाने गए हैं। इनके बीच माँगे गए मार्ग का प्रकाशित रिकॉर्ड उपलब्ध नहीं है। इसका अर्थ यह नहीं कि वास्तविक सेवा उपलब्ध नहीं है।',
                               sources=[self.catalog['sources']['canonical']],
                               hinglish='Locations database mein pehchane gaye hain. Inke beech maange gaye route ka published record available nahi hai. Iska matlab yeh nahi ki real service available nahi hai.')
            routes = answer.data['routes']
            descriptions = []
            for row in routes[:3]:
                origin_name = self.places[row['origin_stop_id']]['name_en']
                destination_name = self.places[row['destination_stop_id']]['name_en']
                descriptions.append(f"{row['route_name']} ({row['mode']}): {origin_name} → {destination_name}")
            detail = '; '.join(dict.fromkeys(descriptions))
            return respond('information', f'कैनोनिकल स्नैपशॉट में प्रकाशित स्टॉप-क्रम मिला: {detail}। यह वर्तमान सेवा, यात्रा या सुगम पैदल पहुँच की पुष्टि नहीं है।',
                           [{'type': 'canonical_route_sequence', **row} for row in routes],
                           [self.catalog['sources']['canonical']],
                           hinglish=f'Canonical snapshot mein published stop order mila: {detail}. Yeh current service, trip ya accessible walking access ki confirmation nahi hai.')

        if slots.get('ambiguous_locations'):
            return respond('clarification', 'इस छोटे डेमो में एक मूल स्थान और एक गंतव्य लिखें।')
        if intent == 'train_status':
            return respond('unavailable', 'आपका प्रश्न ट्रेन की देरी या स्थिति के बारे में है। इस प्रोटोटाइप में लाइव ट्रेन डेटा नहीं है; रेलवे की आधिकारिक जानकारी या स्टेशन कर्मचारियों से पुष्टि करें।')
        if intent == 'railway_complaint':
            return respond('information', 'आपका प्रश्न रेलवे शिकायत के रूप में पहचाना गया है। यह NLP डेमो शिकायत दर्ज नहीं करता; संबंधित रेलवे कर्मचारियों या आधिकारिक शिकायत माध्यम से संपर्क करें।')
        if intent == 'out_of_scope':
            return respond('out_of_scope', 'यह परियोजना चुने हुए चेन्नई स्टेशनों के परिवहन संबंधी हिंदी प्रश्नों के लिए है।')
        if intent == 'ticketing':
            return respond('unavailable', 'आपका प्रश्न टिकट या किराये से संबंधित है। इस छोटे डेमो में टिकट बुकिंग और वर्तमान किराये उपलब्ध नहीं हैं। आधिकारिक टिकट सेवा पर जाँचें।')
        if intent == 'service_timing':
            station = slots.get('station') or slots.get('origin')
            # The dated terminal window cannot answer a destination-specific or railway departure.
            rows = [row for row in self.catalog.get('timings', [])
                    if row['location'] == station and row['mode'] == slots.get('transport_mode')
                    and 'destination' not in slots
                    and slots.get('information_type') in {'first_service', 'last_service', 'timetable'}
                    and not re.search(r'आज|कल|रविवार|शनिवार|छुट्टी|\b(?:aaj|today|tomorrow|sunday|saturday|holiday)\b', normalize_extraction_text(query))]
            if rows:
                row = rows[0]
                text = (f"16 अक्टूबर 2024 के CMRL कार्यदिवस प्रकाशन में सेंट्रल ग्रीन लाइन टर्मिनल की सेवा "
                        f"{row['first_service']}–{row['last_service']} दर्ज है। {row['note_hi']}")
                return respond('information', text, rows,
                               [self.catalog['sources'][row['source']], self.catalog['sources'][row['current_timetable_source']]])
            kind = slots.get('information_type')
            extraction_intent, operation = {
                'first_service': ('first_and_last_service', 'GET_FIRST_LAST_SERVICE'),
                'last_service': ('first_and_last_service', 'GET_FIRST_LAST_SERVICE'),
                'frequency': ('service_frequency', 'GET_SERVICE_FREQUENCY'),
            }.get(kind, ('scheduled_departure', 'GET_SCHEDULED_DEPARTURES'))
            requested_mode = slots.get('transport_mode')
            if isinstance(requested_mode, str):
                requested_mode = {'rail': 'suburban_rail'}.get(requested_mode, requested_mode)
            else:
                requested_mode = None
            # Missing entire mode coverage cannot be repaired by guessing a
            # physical stop. The original rail snapshot has names, no schedules.
            if self.service.preflight_mode(operation, requested_mode) is None:
                if ambiguities:
                    return canonical_route_reply()
                extracted = self.canonical_extractor.extract(query, extraction_intent)
                execution = dict(extracted.slots, **canonical_slots)
                if requested_mode:
                    execution['transport_mode'] = requested_mode
                if not (extracted.clarification_reason or extracted.multiple_execution_scopes or extracted.unsupported_temporal_scope
                        or extracted.unsupported_timetable_waypoint or extracted.missing_execution_slots or extracted.excluded_modes
                        or isinstance(slots.get('transport_mode'), list)) and (execution.get('station') or execution.get('origin')):
                    answer = self.service.execute(operation, execution)
                    if answer.status == 'ok':
                        if operation == 'GET_FIRST_LAST_SERVICE':
                            detail = f"first {answer.data['first_departure']}; last {answer.data['last_departure']}"
                        elif operation == 'GET_SERVICE_FREQUENCY':
                            detail = f"median interval {answer.data['median_headway_minutes']} minutes"
                        else:
                            detail = '; '.join(f"{row['route_name']}: {row['time']}" for row in answer.data['departures'])
                        return respond('information', f'संग्रहीत समय-सारणी में: {detail}। ये GTFS सेवा-दिन के समय हैं; वर्तमान सेवा या लाइव प्रस्थान की पुष्टि नहीं है।',
                                       [{'type': 'canonical_timetable', **answer.data}], [self.catalog['sources']['canonical']],
                                       hinglish=f'Stored timetable mein: {detail}. Yeh GTFS service-day times hain; current service ya live departure ki confirmation nahi hai.')
            return respond('unavailable', 'माँगी गई सेवा का वर्तमान समय इस छोटे कैटलॉग में नहीं है। पहली/आखिरी ट्रेन या प्रस्थान का समय अनुमान से नहीं बताया जा सकता।',
                           sources=[self.catalog['sources']['canonical']] if matches else [],
                           hinglish='Station names pehchane gaye hain, lekin maangi gayi service ka departure timetable is database mein available nahi hai. First/last train ka time andaaze se nahi bataya ja sakta.' if matches else None)
        if re.search(r'(?<!\w)(?:नहीं|मत|nahi|nahin|mat)(?!\w)', normalize_extraction_text(query)) and intent in {'route_query', 'service_availability'}:
            return respond('clarification', 'इस छोटे डेमो में नकारात्मक या बहु-भाग वाले मार्ग प्रश्न स्पष्ट करें। कौन सा परिवहन विकल्प चाहिए?')
        station = slots.get('station') or slots.get('origin')
        if intent == 'accessibility':
            if not station:
                return respond('clarification', 'किस स्टेशन और किस सुविधा—लिफ्ट या व्हीलचेयर—के बारे में जानना चाहते हैं?')
            mode, feature = slots.get('transport_mode'), slots.get('accessibility_feature')
            if mode != 'metro':
                return respond('clarification', 'कैटलॉग की सुगम्यता जानकारी सेंट्रल मेट्रो के लिए है। रेलवे या मेट्रो स्टेशन स्पष्ट करें।')
            rows = [row for row in self.catalog['accessibility']
                    if row['location'] == station and row['feature'] == feature and row['mode'] == mode]
            if rows:
                return respond('information', rows[0]['description_hi'], rows,
                               [self.catalog['sources'][row['source']] for row in rows])
            return respond('unavailable', 'इस स्टेशन की माँगी गई सुगम्यता सुविधा की जानकारी छोटे कैटलॉग में नहीं है।')
        if intent == 'station_information':
            if not station:
                return respond('clarification', 'स्टेशन का पूरा नाम लिखें।')
            place = self.places.get(station)
            if isinstance(slots.get('transport_mode'), list) and re.search(r'पास|paas|near|nazdeek|नजदीक', normalize_extraction_text(query)):
                return respond('clarification', 'पास में किस प्रकार का स्टॉप चाहिए—बस, मेट्रो या रेलवे? एक माध्यम चुनें।',
                               hinglish='Paas mein kis type ka stop chahiye—bus, metro ya railway? Ek mode chunein.')
            if slots.get('station_detail') in {'nearby_bus', 'nearby_transport'} and not (slots.get('station_detail') == 'nearby_bus' and (place or {}).get('nearby_bus_name')):
                if isinstance(slots.get('transport_mode'), list):
                    return respond('clarification', 'पास में किस प्रकार का स्टॉप चाहिए—बस, मेट्रो या रेलवे? एक माध्यम चुनें।',
                                   hinglish='Paas mein kis type ka stop chahiye—bus, metro ya railway? Ek mode chunein.')
                target = {'rail': 'suburban_rail'}.get(slots.get('transport_mode'), slots.get('transport_mode')) or 'bus'
                anchor = canonical_slots.get('station') or canonical_slots.get('origin')
                compatible = {anchor} if anchor else set()
                if ambiguities and all(row.get('reason') == 'coordinate_conflict' for row in ambiguities):
                    compatible.update(candidate['entity_id'] for row in ambiguities for candidate in row['candidates'])
                facts = [row for row in self.catalog.get('nearby_transport_facts', [])
                         if row['anchor_stop_id'] in compatible and row['target_mode'] == target]
                if facts:
                    row = facts[0]
                    names = '; '.join(row['stop_names'])
                    return respond('information', f'CMRL के गिंडी मेट्रो स्टेशन पेज की प्रवेश/पहुँच सूची में ये बस स्टॉप दर्ज हैं: {names}। भरोसेमंद पैदल दूरी उपलब्ध नहीं है; सही प्रवेश, स्टॉप की दिशा और वर्तमान सेवा मौके पर जाँचें।',
                                   facts, [self.catalog['sources'][row['source']]],
                                   hinglish=f'CMRL ke Guindy Metro station page ki entrance/access list mein yeh bus stops recorded hain: {names}. Reliable walking distance available nahi hai; sahi entrance, stop ki direction aur current service locally check karein.')
                if ambiguities:
                    if any(row.get('reason') == 'coordinate_conflict' for row in ambiguities):
                        return respond('unavailable', 'स्टेशन और माँगा गया परिवहन माध्यम स्पष्ट हैं, लेकिन स्रोतों में इसी स्टेशन की जगह अलग-अलग दर्ज है। भरोसेमंद पास के स्टॉप/दूरी के लिए पहले इन स्थान रिकॉर्डों का मिलान आवश्यक है।',
                                       sources=[self.catalog['sources']['canonical']],
                                       hinglish='Station aur requested transport mode clear hain, lekin sources mein isi station ki location alag-alag recorded hai. Reliable nearby stop/distance batane se pehle in location records ko reconcile karna zaroori hai.')
                    names = ', '.join(dict.fromkeys(row['surface'] for row in ambiguities))
                    return respond('clarification', f'{names} के पास परिवहन स्टॉप खोजने के लिए मूल रेलवे/MRTS या मेट्रो स्टेशन का पूरा नाम लिखें।',
                                   hinglish=f'{names} ke paas transport stop dhoondhne ke liye starting railway/MRTS ya metro station ka poora naam likhein.')
                answer = self.service.execute('FIND_NEAREST_STATION', {'landmark': anchor, 'transport_mode': target})
                if answer.status == 'ok':
                    stops = answer.data['stops']
                    # Prefer explicitly typed GTFS bus-stop records when OSM
                    # has a coincident station/bus name at the same coordinate.
                    if target == 'bus':
                        stops = [row for row in stops if row['source'] == 'CHENNAI_COMMUNITY_GTFS'] or stops
                    stops = stops[:3]
                    displayed = list({row['name']: row for row in reversed(stops)}.values())
                    displayed.sort(key=lambda row: row['distance_m'])
                    detail = '; '.join(f"{row['name']} (लगभग {row['distance_m']} मीटर सीधी दूरी)" for row in displayed)
                    detail_en = '; '.join(f"{row['name']} (lagbhag {row['distance_m']} metre straight-line distance)" for row in displayed)
                    return respond('information', f"{answer.data['anchor_name']} स्टेशन/स्थान के पास स्नैपशॉट में ये {target} स्टॉप दर्ज हैं: {detail}। सीधी दूरी पैदल मार्ग की दूरी नहीं है; स्टॉप की दिशा और पैदल पहुँच मौके पर जाँचें।",
                                   [{'type': 'canonical_nearby_bus' if target == 'bus' else 'canonical_nearby_transport', 'anchor_id': anchor, **row} for row in stops], [self.catalog['sources']['canonical']],
                                   hinglish=f"{answer.data['anchor_name']} station/place ke paas snapshot mein yeh {target} stops recorded hain: {detail_en}. Straight-line distance walking distance nahi hai; stop ki direction aur walking access locally check karein.")
                return respond('unavailable', 'स्थान और माँगा गया परिवहन माध्यम समझ लिया गया है, लेकिन पास के उस माध्यम के स्टॉप की उपयोगी/सत्यापित जानकारी नहीं मिली।',
                               hinglish='Location aur requested transport mode samajh liya gaya hai, lekin nearby stops ki usable/verified information is mode ke liye nahi mili.')
            if station not in {row['id'] for row in self.catalog['locations']}:
                if ambiguities:
                    return canonical_route_reply()
                if slots.get('station_detail'):
                    return respond('unavailable', 'स्थान पहचाना गया है, लेकिन माँगी गई स्टेशन सुविधा या विस्तृत जानकारी इस डेटाबेस में उपलब्ध नहीं है।',
                                   hinglish='Location pehchana gaya hai, lekin maangi gayi station facility ya detailed information is database mein available nahi hai.')
                return respond('information', f"डेटाबेस में {place['name_en']} का नाम दर्ज है। यह स्टेशन सुविधाओं या वर्तमान सेवा की पुष्टि नहीं है।",
                               [place], [self.catalog['sources']['canonical']],
                               hinglish=f"Database mein {place['name_en']} ka naam recorded hai. Yeh station facilities ya current service ki confirmation nahi hai.")
            if slots.get('station_detail') and (slots['station_detail'] != 'nearby_bus' or not place.get('nearby_bus_name')):
                return respond('unavailable', 'इस स्टेशन की माँगी गई विस्तृत जानकारी छोटे कैटलॉग में नहीं है। स्टेशन कर्मचारियों से पुष्टि करें।')
            if slots.get('origin') and not slots.get('destination') and not slots.get('station_detail'):
                return respond('clarification', 'गंतव्य पहचाना नहीं गया। पूरा स्टेशन, बस स्टॉप या स्थान नाम लिखें।',
                               hinglish='Destination pehchana nahi gaya. Poora station, bus stop ya place name likhein.')
            text = place['name_hi'] + ' इस परियोजना के चुने हुए स्थानों में है।'
            if place.get('nearby_bus_name'):
                text += ' कैनोनिकल स्नैपशॉट में पास का बस स्टॉप ' + place['nearby_bus_name'] + ' दर्ज है।'
            return respond('information', text + ' यह वर्तमान सेवा या सुगम पैदल मार्ग की पुष्टि नहीं है।', [place], [self.catalog['sources']['canonical']])
        constraints = self.canonical_extractor.extract(query, 'point_to_point_route')
        if any(key in constraints.slots for key in ('date', 'time', 'temporal_relative')) or constraints.unsupported_temporal_scope:
            return respond('unavailable', 'संग्रहीत रूट रिकॉर्ड माँगी गई तारीख या समय पर यात्रा/सेवा की पुष्टि नहीं करते। वर्तमान सेवा मौके पर जाँचें।',
                           hinglish='Stored route records maangi gayi date ya time par trip/service confirm nahi karte. Current service locally check karein.')
        if constraints.slots.get('preference') in {'fastest', 'cheapest', 'least_transfers'}:
            return respond('unavailable', 'सबसे तेज़, सबसे सस्ता या सबसे कम बदलाव वाला मार्ग चुनने की सत्यापित जानकारी उपलब्ध नहीं है।',
                           hinglish='Fastest, cheapest ya least-transfer route choose karne ki verified information available nahi hai.')
        if constraints.missing_execution_slots or constraints.multiple_execution_scopes or constraints.clarification_reason not in {None, 'entity_ambiguity'}:
            return respond('clarification', 'यात्रा की शर्तें स्पष्ट करें: मूल स्थान, गंतव्य और कोई माँगा गया बीच का स्टेशन/रूट।',
                           hinglish='Journey ki conditions clear karein: origin, destination aur maanga gaya via station/route.')
        if re.search(r'(?<!\w)(?:via|होते हुए|hote hue)(?!\w)', normalize_extraction_text(query)):
            return respond('unavailable', 'इस छोटे प्रोटोटाइप में बीच के स्टेशन से होकर पूरी यात्रा की पुष्टि उपलब्ध नहीं है। मूल स्थान और गंतव्य का सीधा प्रकाशित कनेक्शन अलग से पूछा जा सकता है।',
                           hinglish='Is chhote prototype mein via station se hokar poori journey ki confirmation available nahi hai. Origin aur destination ka direct published connection alag se poochh sakte hain.')
        origin, destination = slots.get('origin'), slots.get('destination')
        if not origin:
            return respond('clarification', 'मूल स्थान पहचाना नहीं गया। पूरा स्टेशन, बस स्टॉप या स्थान नाम लिखें।',
                           hinglish='Origin pehchana nahi gaya. Poora station, bus stop ya place name likhein.')
        if not destination:
            if slots.get('transport_mode') == 'bus' and self.places.get(origin, {}).get('nearby_bus_name'):
                text = self.places[origin]['name_hi'] + ' के पास कैटलॉग में ' + self.places[origin]['nearby_bus_name'] + ' बस स्टॉप दर्ज है। किसी गंतव्य के लिए बस सेवा की पुष्टि के लिए गंतव्य लिखें।'
                return respond('information', text, [self.places[origin]], [self.catalog['sources']['canonical']])
            return respond('clarification', 'गंतव्य पहचाना नहीं गया। पूरा स्टेशन, बस स्टॉप या स्थान नाम लिखें।',
                           hinglish='Destination pehchana nahi gaya. Poora station, bus stop ya place name likhein.')
        mode = slots.get('transport_mode')
        if isinstance(mode, list):
            return respond('clarification', 'एक यात्रा के लिए एक परिवहन माध्यम चुनें।', hinglish='Ek journey ke liye ek transport mode chunein.')
        if constraints.slots.get('route_number') or constraints.slots.get('line_name'):
            return canonical_route_reply()
        rows = [row for row in self.catalog['connections']
                if row['origin'] == origin and row['destination'] == destination
                and (mode is None or row['mode'] == mode)]
        if rows:
            row = rows[0]
            if row['mode'] == 'bus':
                text = (f"समुदाय GTFS स्नैपशॉट में बस {row['route_name']} का स्टॉप-क्रम {row['boarding_stop']} से "
                        f"{row['alighting_stop']} दर्ज है। {row['note_hi']}")
            else:
                text = (self.places[origin]['name_hi'] + ' मेट्रो से ' + self.places[destination]['name_hi']
                        + ' के लिए ' + row['line_hi'] + ' की प्रकाशित कनेक्टिविटी दर्ज है। ' + row['note_hi'])
            return respond('information', text, rows, [self.catalog['sources'][row['source']]])
        return canonical_route_reply()
