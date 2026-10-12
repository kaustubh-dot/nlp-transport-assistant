"""Create a small, explicitly synthetic Hindi teaching dataset; no challenge input."""
from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

from src.hindi_project.model import LABELS, ROOT

# Entire template families are held out. Slot substitutions cannot cross splits.
TEMPLATES = {
    'route_query': [
        '{origin} से {destination} कैसे जाऊँ?', '{destination} जाने के लिए {origin} से रास्ता बताइए।',
        '{origin} से {destination} तक पहुँचने का मार्ग क्या है?', '{origin} से {destination} का परिवहन विकल्प बताओ।',
        'मुझे {origin} से {destination} जाना है, कैसे पहुँचूँ?', '{origin} से {destination} जाने के लिए कौन सा रास्ता लूँ?',
        '{destination} पहुँचने का तरीका {origin} से समझाइए।', '{origin} से {destination} की यात्रा का मार्ग समझाओ।',
        'मैं {origin} पर हूँ, {destination} तक सफर कैसे करूँ?', '{destination} तक आने-जाने के रास्ते की जानकारी {origin} से चाहिए।'],
    'service_availability': [
        '{origin} से {destination} के लिए {mode} उपलब्ध है क्या?', '{origin} से {destination} तक {mode} मिलती है?',
        '{origin} और {destination} के बीच {mode} कनेक्टिविटी है?', '{destination} के लिए {origin} से {mode} की सुविधा है क्या?',
        '{origin} से {destination} जाने वाली {mode} है क्या?', '{origin} से {destination} तक {mode} सेवा मिल सकती है?',
        '{destination} के लिए {mode} का कनेक्शन {origin} से मिलता है?', '{origin} से {destination} के बीच {mode} चलती है क्या?',
        'क्या {origin} से {destination} के लिए {mode} का संपर्क मौजूद है?', '{origin} से {destination} की {mode} सेवा उपलब्ध होने की जानकारी चाहिए।'],
    'service_timing': [
        '{origin} से आखिरी {mode} कितने बजे है?', '{origin} से पहली {mode} कब चलती है?',
        '{origin} पर {mode} सेवा का समय बताइए।', '{origin} से {mode} की अंतिम सेवा कब है?',
        '{origin} पर {mode} कितनी देर के अंतराल पर मिलती है?', '{origin} से सुबह पहली {mode} का समय क्या है?',
        '{origin} से रात में आखिरी {mode} कब निकलती है?', '{origin} की {mode} समय-सारणी जाननी है।',
        '{origin} से {mode} का अगला निर्धारित प्रस्थान कब होता है?', 'सेवा शुरू और समाप्त होने का वक्त {origin} की {mode} के लिए बताओ।'],
    'station_information': [
        '{origin} स्टेशन की जानकारी दीजिए।', '{origin} पर कौन से प्लेटफॉर्म हैं?',
        '{origin} स्टेशन का पता क्या है?', '{origin} पर स्टेशन कार्यालय कहाँ है?',
        '{origin} पर पीने का पानी कहाँ मिलेगा?', '{origin} स्टेशन में यात्रियों की सुविधाएँ बताइए।',
        '{origin} स्टेशन के प्रवेश द्वार की जानकारी चाहिए।', '{origin} रेलवे स्टेशन के बारे में बताओ।',
        '{origin} के पास मौजूद बस स्टॉप का नाम क्या है?', '{origin} स्टेशन की बुनियादी जानकारी समझाइए।'],
    'accessibility': [
        '{origin} मेट्रो में व्हीलचेयर उपलब्ध है क्या?', '{origin} मेट्रो स्टेशन पर लिफ्ट है?',
        '{origin} पर दिव्यांग यात्रियों की सुविधाएँ बताओ।', '{origin} मेट्रो में व्हीलचेयर की सहायता कैसे मिलेगी?',
        '{origin} स्टेशन पर रैंप की सुविधा है क्या?', '{origin} मेट्रो में लिफ्ट से प्लेटफॉर्म पहुँच सकते हैं?',
        '{origin} मेट्रो की सुगम्यता की जानकारी चाहिए।', '{origin} पर एस्केलेटर उपलब्ध है?',
        '{origin} मेट्रो पर चलने में कठिनाई वाले यात्री को क्या सहायता मिलेगी?', '{origin} स्टेशन की बाधारहित पहुँच और व्हीलचेयर सुविधा समझाइए।'],
    'ticketing': [
        '{origin} से {destination} का टिकट कैसे खरीदूँ?', '{origin} से {destination} का किराया कितना है?',
        'मेरा {mode} टिकट बुक नहीं हो रहा है।', '{origin} पर {mode} का टिकट काउंटर कहाँ है?',
        '{origin} से {destination} के लिए टिकट बुकिंग की जानकारी चाहिए।', '{mode} का पास कहाँ बनता है?',
        '{origin} से {destination} यात्रा के टिकट का दाम बताओ।', 'मेरे {mode} टिकट का भुगतान असफल हो गया।',
        '{mode} का टिकट आरक्षित करने का तरीका समझाइए।', '{origin} से {destination} का टिकट खरीदने में मदद चाहिए।'],
    'train_status': [
        '{origin} की ट्रेन बहुत लेट है।', '{origin} आने वाली ट्रेन की लाइव स्थिति क्या है?',
        '{origin} की ट्रेन में कितनी देरी है?', '{origin} की ट्रेन अभी कहाँ पहुँची है?',
        '{origin} की रेलगाड़ी देर से क्यों आ रही है?', '{origin} की ट्रेन समय पर नहीं पहुँची।',
        '{origin} की ट्रेन का वर्तमान स्टेटस बताओ।', '{origin} की ट्रेन आज रद्द हुई है क्या?',
        '{origin} की रेलगाड़ी की अभी की स्थिति जाननी है।', '{origin} की ट्रेन विलंब से चल रही है, स्थिति बताइए।'],
    'railway_complaint': [
        '{origin} की ट्रेन में {issue} की शिकायत है।', '{origin} स्टेशन पर {issue} की समस्या बताना चाहता हूँ।',
        '{origin} की रेलगाड़ी में {issue} ठीक नहीं है।', '{origin} रेलवे में {issue} के बारे में शिकायत कैसे करूँ?',
        '{origin} की ट्रेन में {issue} को लेकर परेशानी है।', '{origin} के रेलवे कर्मचारियों को {issue} की समस्या बतानी है।',
        '{origin} की ट्रेन की {issue} खराब है, शिकायत करनी है।', '{origin} स्टेशन की {issue} से मैं असंतुष्ट हूँ।',
        'मुझे {origin} की रेलवे सेवा में {issue} के बारे में शिकायत दर्ज करने की जानकारी चाहिए।', '{origin} के रेल सफर में {issue} से जुड़ी परेशानी हुई है।'],
    'out_of_scope': [
        'आज {topic} के बारे में बताओ।', '{topic} की जानकारी चाहिए।',
        '{topic} का नया समाचार बताइए।', '{topic} पर एक कहानी सुनाओ।',
        'मुझे {topic} के बारे में सीखना है।', '{topic} पर सलाह दीजिए।',
        '{topic} से जुड़े सवाल का जवाब चाहिए।', '{topic} का विवरण समझाओ।',
        'क्या आप {topic} पर चर्चा कर सकते हैं?', 'मैं {topic} के बारे में जानना चाहता हूँ।'],
}

# These share the Hindi semantic-family numbers and therefore the same split.
HINGLISH = {
    'route_query': ['{origin} se {destination} kaise jaun?', '{origin} se {destination} tak pahunchne ka rasta kya hai?', 'Mujhe {origin} se {destination} jana hai, kaise pahunchun?', '{origin} se {destination} ki yatra ka route samjhao.', 'Main {origin} par hoon, {destination} tak travel kaise karun?'],
    'service_availability': ['{origin} se {destination} ke liye {mode} available hai kya?', '{origin} aur {destination} ke beech {mode} connectivity hai?', '{origin} se {destination} jaane wali {mode} hai kya?', '{origin} se {destination} ke beech {mode} chalti hai kya?', 'Kya {origin} se {destination} ke liye {mode} connection maujood hai?'],
    'service_timing': ['{origin} se aakhiri {mode} kitne baje hai?', '{origin} ki {mode} ka time batao.', '{origin} par {mode} kitni der ke gap mein milti hai?', '{origin} ki {mode} timetable chahiye.', '{origin} se {mode} ka agla scheduled departure kab hai?'],
    'station_information': ['{origin} station ki jaankari dijiye.', '{origin} station ka address kya hai?', '{origin} par peene ka paani kahan milega?', '{origin} railway station ke baare mein batao.', '{origin} ke paas bus stop ka naam kya hai?'],
    'accessibility': ['{origin} metro mein wheelchair available hai kya?', '{origin} par divyang passengers ki facilities batao.', '{origin} station par ramp hai kya?', '{origin} par escalator available hai?', '{origin} metro mein chalne mein dikkat wale passenger ko kya help milegi?'],
    'ticketing': ['{origin} se {destination} ka ticket kaise kharidun?', 'Mera {mode} ticket book nahi ho raha.', '{origin} se {destination} ticket booking ki jaankari chahiye.', 'Mere {mode} ticket ka payment fail ho gaya.', '{mode} ka ticket reserve karne ka tarika samjhao.'],
    'train_status': ['{origin} ki train bahut late hai.', '{origin} ki train mein kitni deri hai?', '{origin} ki railgadi late kyun aa rahi hai?', '{origin} ki train aaj cancel hui hai kya?', '{origin} ki train ki abhi ki position janni hai.'],
    'railway_complaint': ['{origin} ki train mein {issue} ki complaint hai.', '{origin} ki train mein {issue} theek nahi hai.', '{origin} ki train mein {issue} ko lekar pareshani hai.', '{origin} station ki {issue} se main khush nahi hoon.', '{origin} ki railway service mein {issue} ki complaint karne ki jaankari chahiye.'],
    'out_of_scope': ['Aaj {topic} ke baare mein batao.', '{topic} ki latest news bataiye.', 'Mujhe {topic} ke baare mein seekhna hai.', '{topic} ki details samjhao.', 'Kya aap {topic} par discussion kar sakte hain?'],
}


def build_rows() -> list[dict]:
    pairs = list(itertools.product(['चेन्नई सेंट्रल', 'एग्मोर', 'तांबरम', 'अवडी'],
                                   ['एयरपोर्ट', 'कोयंबेडु', 'गिंडी']))
    issues = ['सफाई', 'पानी की आपूर्ति', 'भोजन की गुणवत्ता', 'कर्मचारियों का व्यवहार', 'शौचालय की सफाई', 'कोच की सफाई']
    topics = ['क्रिकेट', 'मौसम', 'फिल्म', 'राजनीति', 'गणित', 'खाना पकाने',
              'बागवानी', 'संगीत', 'परीक्षा', 'कंप्यूटर गेम', 'कविता', 'शेयर बाजार']
    rows = []
    for label in LABELS:
        for family, template in enumerate(TEMPLATES[label]):
            split = 'train' if family < 7 else 'validation' if family == 7 else 'test'
            # Families without destination/mode variation must still yield 12 distinct texts.
            candidates = []
            for index, (origin, destination) in enumerate(pairs):
                query = template.format(origin=origin, destination=destination,
                                        mode='मेट्रो' if index % 2 else 'बस',
                                        issue=issues[index % len(issues)], topic=topics[index])
                candidates.append(query)
            unique = list(dict.fromkeys(candidates))
            # Polite context prefixes stay within the same family/split.
            if len(unique) < 12:
                prefixes = ('', 'कृपया ', 'मुझे जानकारी चाहिए: ', 'मेरा प्रश्न है: ',
                            'यात्रा के लिए पूछ रहा हूँ: ', 'हिंदी में बताइए: ')
                unique = [prefix + query for prefix in prefixes for query in unique][:12]
            for index, query in enumerate(unique):
                rows.append({'id': f'{label}_{family:02d}_{index:02d}', 'text': query,
                             'intent': label, 'family_id': f'{label}:{family}', 'split': split,
                             'source': 'synthetic_template', 'human_reviewed': 'false', 'language': 'hi'})
    # Short, location-free development examples for the original railway tasks.
    seeds = {
        'train_status': ['मेरी रेलगाड़ी लेट चल रही है।', 'ट्रेन देर से आने वाली है।',
                         'मेरी ट्रेन अभी कहाँ है?', 'रेल देर से पहुँचेगी क्या?', 'गाड़ी अपने समय पर नहीं आई।'],
        'railway_complaint': ['ट्रेन में शौचालय गंदा है।', 'रेलगाड़ी में पानी नहीं आ रहा।',
                              'कोच में सफाई नहीं हुई।', 'रेलवे कर्मचारी खराब व्यवहार कर रहे हैं।', 'रेल में खाना खराब मिला।'],
    }
    for label, questions in seeds.items():
        for index, query in enumerate(questions):
            rows.append({'id': f'{label}_seed_{index}', 'text': query, 'intent': label,
                         'family_id': label + ':short_seed', 'split': 'train',
                         'source': 'synthetic_development_seed', 'human_reviewed': 'false', 'language': 'hi'})
    roman_pairs = list(itertools.product(['Chennai Central', 'Egmore', 'Tambaram', 'Avadi'],
                                         ['Airport', 'Koyambedu', 'Guindy']))
    roman_issues = ['safai', 'paani ki supply', 'khane ki quality', 'staff ka behaviour', 'toilet ki safai', 'coach ki safai']
    roman_topics = ['cricket', 'mausam', 'film', 'politics', 'maths', 'cooking',
                    'gardening', 'music', 'exam', 'computer games', 'poetry', 'share market']
    for label in LABELS:
        roman_templates = list(zip((0, 2, 4, 7, 8), HINGLISH[label]))
        if label == 'accessibility':
            roman_templates.append((1, '{origin} metro station par lift hai?'))
        for family, template in roman_templates:
            split = 'train' if family < 7 else 'validation' if family == 7 else 'test'
            questions = [template.format(origin=origin, destination=destination,
                         mode='metro' if index % 2 else 'bus', issue=roman_issues[index % 6], topic=roman_topics[index])
                         for index, (origin, destination) in enumerate(roman_pairs)]
            unique = list(dict.fromkeys(questions))
            if len(unique) < 12:
                prefixes = ('', 'Please ', 'Mujhe jaankari chahiye: ', 'Mera sawal hai: ',
                            'Travel ke liye pooch raha hoon: ', 'Please samjhaiye: ')
                unique = [prefix + query for prefix in prefixes for query in unique][:12]
            for index, query in enumerate(unique):
                rows.append({'id': f'{label}_hl_{family:02d}_{index:02d}', 'text': query, 'intent': label,
                             'family_id': f'{label}:{family}', 'split': split, 'source': 'synthetic_template',
                             'human_reviewed': 'false', 'language': 'hinglish'})
    roman_seeds = {
        'train_status': ['Meri railgadi late chal rahi hai.', 'Train der se aane wali hai.', 'Meri train abhi kahan hai?',
                         'Rail late pahunchne wali hai kya?', 'Gaadi apne time par nahi aayi.'],
        'railway_complaint': ['Train mein toilet ganda hai.', 'Railgadi mein paani nahi aa raha.', 'Coach mein safai nahi hui.',
                              'Railway staff ka behaviour kharab hai.', 'Train mein khana kharab mila.'],
    }
    for label, questions in roman_seeds.items():
        for index, query in enumerate(questions):
            rows.append({'id': f'{label}_hl_seed_{index}', 'text': query, 'intent': label,
                         'family_id': label + ':short_seed', 'split': 'train',
                         'source': 'synthetic_development_seed', 'human_reviewed': 'false', 'language': 'hinglish'})
    # Replace variants rather than growing the assignment into a data program.
    authored = json.loads((ROOT / 'data/project/development_examples.json').read_text())
    for label in LABELS:
        pairs = authored['examples'][label]
        for language in ('hi', 'hinglish'):
            redundant = [row for row in rows if row['intent'] == label and row['language'] == language
                         and row['split'] == 'train' and row['source'] == 'synthetic_template'][:len(pairs)]
            for row in redundant:
                rows.remove(row)
        for index, pair in enumerate(pairs):
            for language, query in zip(('hi', 'hinglish'), pair):
                rows.append({'id': f'{label}_authored_{language}_{index}', 'text': query, 'intent': label,
                             'family_id': f'{label}:authored_{index}', 'split': 'train',
                             'source': authored['source'], 'human_reviewed': 'false', 'language': language})
    if len({r['text'] for r in rows}) != len(rows):
        raise ValueError('Generated duplicate questions')
    return rows


def main():
    path = ROOT / 'data/project/hindi_intents.csv'
    rows = build_rows()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'{len(rows)} synthetic Hindi/Hinglish rows written to {path}')
    catalog = json.loads((ROOT / 'data/project/chennai_case_study.json').read_text())
    aliases = {alias: place['id'] for place in catalog['locations'] for alias in place['aliases']}
    pairs = list(itertools.product(['चेन्नई सेंट्रल', 'एग्मोर', 'तांबरम', 'अवडी'],
                                   ['एयरपोर्ट', 'कोयंबेडु', 'गिंडी']))
    roman_pairs = list(itertools.product(['Chennai Central', 'Egmore', 'Tambaram', 'Avadi'],
                                         ['Airport', 'Koyambedu', 'Guindy']))
    entities = []
    for row in rows:
        if row['intent'] not in {'route_query', 'service_availability'} or row['source'] != 'synthetic_template':
            continue
        index = int(row['id'].rsplit('_', 1)[1])
        origin, destination = (pairs if row['language'] == 'hi' else roman_pairs)[index]
        if row['language'] == 'hinglish':
            origin, destination = origin.lower(), destination.lower()
        entities.append({'id': row['id'], 'text': row['text'], 'origin': aliases[origin],
                         'destination': aliases[destination],
                         'transport_mode': ('metro' if index % 2 else 'bus') if row['intent'] == 'service_availability' else '',
                         'family_id': row['family_id'], 'split': row['split'], 'source': 'synthetic_template',
                         'language': row['language']})
    with (path.parent / 'entity_slots.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(entities[0]))
        writer.writeheader()
        writer.writerows(entities)
    print(f'{len(entities)} linked synthetic slot examples written')


if __name__ == '__main__':
    main()
