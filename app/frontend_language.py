"""Pure presentation translations; never translate or reinterpret model inputs.

Known explanations are curated. Factual prefixes are localized only when the
original text exactly matches the backend's rendering of the supplied data.
Unknown explanations remain verbatim behind a localized label.
"""

from __future__ import annotations

from math import isfinite
from string import Formatter


LANGUAGE_NAMES = {"en": "English", "hi": "हिंदी", "hinglish": "Hinglish"}

# English templates are stable lookup keys. Dynamic values are never translated
# by tr(), so identifiers, canonical names, amounts, dates and times survive.
CATALOG = {
    "Chennai Transit Assistant": ("चेन्नई परिवहन सहायक", "Chennai Transit Sahayak"),
    "Chennai Transit": ("चेन्नई परिवहन", "Chennai Transit"),
    "Chennai Multimodal Transit Assistant": ("चेन्नई बहु-माध्यम परिवहन सहायक", "Chennai Multimodal Transit Sahayak"),
    "Multilingual transport assistant": ("बहुभाषी परिवहन सहायक", "Kai bhashaon mein transport sahayak"),
    "चेन्नई परिवहन सहायक": ("चेन्नई परिवहन सहायक", "Chennai parivahan sahayak"),
    "Ask about routes, stops, schedules, fares, or nearby transit.": ("रूट, स्टॉप, समय-सारणी, किराए या नजदीकी परिवहन के बारे में पूछें।", "Route, stop, schedule, kiraya ya nazdeeki transport ke baare mein poochhein."),
    "चेन्नई परिवहन सहायक · Ask about routes, stops, schedules, fares, or nearby transit.": ("चेन्नई परिवहन सहायक · रूट, स्टॉप, समय-सारणी, किराए या नजदीकी परिवहन के बारे में पूछें।", "Chennai parivahan sahayak · Route, stop, schedule, kiraya ya nazdeeki transport ke baare mein poochhein."),
    "Ask in your own words": ("अपने शब्दों में पूछें", "Apne shabdon mein poochhein"),
    "English · हिन्दी · Hinglish": ("English · हिंदी · Hinglish", "English · Hindi · Hinglish"),
    "Routes, stops, published schedules, fares and nearby transport.": ("रूट, स्टॉप, प्रकाशित समय-सारणी, किराए और नजदीकी परिवहन।", "Route, stop, published schedule, kiraya aur nazdeeki transport."),
    "Published snapshot": ("प्रकाशित रिकॉर्ड का संकलन", "Published records ka snapshot"),
    "No live updates. Confirm current service and fares with the operator.": ("लाइव अपडेट नहीं हैं। मौजूदा सेवा और किराए की पुष्टि ऑपरेटर से करें।", "Live updates nahi hain. Current service aur kiraya operator se confirm karein."),
    "Transfer, accessibility and facility information is shown only when supported by the source.": ("बदलाव, सुगम्यता और सुविधाओं की जानकारी केवल स्रोत से समर्थित होने पर दिखाई जाती है।", "Transfer, accessibility aur facility ki jaankari sirf source support hone par dikhai jaati hai."),
    "Chennai · Public transport": ("चेन्नई · सार्वजनिक परिवहन", "Chennai · Public transport"),
    "Bus": ("बस", "Bus"), "Metro": ("मेट्रो", "Metro"), "Rail": ("रेल", "Rail"),
    "Published records": ("प्रकाशित रिकॉर्ड", "Published records"),
    "Published snapshot · No live updates · Verify current service with the operator": ("प्रकाशित रिकॉर्ड का संकलन · लाइव अपडेट नहीं · मौजूदा सेवा की पुष्टि ऑपरेटर से करें", "Published snapshot · Live updates nahi · Current service operator se verify karein"),
    "Published information": ("प्रकाशित जानकारी", "Prakashit jaankari"),
    "More information needed": ("अधिक जानकारी चाहिए", "Aur jaankari chahiye"),
    "Information unavailable": ("जानकारी अनुपलब्ध है", "Jaankari unavailable hai"),
    "Outside transport scope": ("परिवहन के दायरे से बाहर", "Transport scope ke bahar"),
    "Request could not be completed": ("अनुरोध पूरा नहीं हो सका", "Request poori nahi ho saki"),
    "Checking the transit snapshot…": ("परिवहन रिकॉर्ड जाँचे जा रहे हैं…", "Transit snapshot check ho raha hai…"),
    "Published route candidates": ("प्रकाशित संभावित रूट", "Published route candidates"),
    "Stop-sequence connectivity only. A current trip or transfer plan is not confirmed.": ("केवल स्टॉप क्रम की कनेक्टिविटी। मौजूदा यात्रा या बदलाव की योजना की पुष्टि नहीं है।", "Sirf stop-sequence connectivity. Current trip ya transfer plan confirm nahi hai."),
    "Route stops": ("रूट के स्टॉप", "Route ke stops"),
    "Route": ("रूट", "Route"),
    "{route} · published sequence {index}": ("{route} · प्रकाशित क्रम {index}", "{route} · published stop kram {index}"),
    "Additional published sequences are not shown here.": ("अतिरिक्त प्रकाशित क्रम यहाँ नहीं दिखाए गए हैं।", "Aur published sequences yahan nahi dikhaye gaye hain."),
    "On published route sequence": ("प्रकाशित रूट क्रम में", "Published route sequence par"),
    "Yes": ("हाँ", "Haan"), "No": ("नहीं", "Nahi"),
    "Published service times": ("प्रकाशित सेवा समय", "Prakashit service samay"),
    "First departure": ("पहला प्रस्थान", "Pehla departure"),
    "Last departure": ("अंतिम प्रस्थान", "Aakhiri departure"),
    "GTFS service-day times may continue past 24:00.": ("GTFS सेवा-दिन का समय 24:00 के बाद भी जारी हो सकता है।", "GTFS service-day ka samay 24:00 ke baad bhi ho sakta hai."),
    "Median scheduled interval": ("समय-सारणी का माध्यिका अंतराल", "Schedule ka median interval"),
    "{minutes:g} min": ("{minutes:g} मिनट", "{minutes:g} min"),
    "Estimated from the {minutes} minutes after {time}.": ("{time} के बाद के {minutes} मिनटों से अनुमानित।", "{time} ke baad ke {minutes} minutes se estimate kiya gaya."),
    "Published departures": ("प्रकाशित प्रस्थान", "Prakashit departures"),
    "Times are schedule records, not live predictions.": ("समय समय-सारणी के रिकॉर्ड हैं, लाइव अनुमान नहीं।", "Samay schedule records hain, live predictions nahi."),
    "Published fare": ("प्रकाशित किराया", "Prakashit kiraya"),
    "Source: {source}": ("स्रोत: {source}", "Source ka record: {source}"),
    "Effective date: {date} · Source: {source}": ("प्रभावी तारीख: {date} · स्रोत: {source}", "Lagu tareekh: {date} · Source: {source}"),
    "Service class: {service}": ("सेवा श्रेणी: {service}", "Service ki class: {service}"),
    "unknown": ("अज्ञात", "unknown"),
    "Nearest by straight line": ("सीधी दूरी से निकटतम", "Seedhi doori se sabse nazdeek"),
    "Walking access and current operation are not verified.": ("पैदल पहुँच और मौजूदा संचालन की पुष्टि नहीं है।", "Walking access aur current operation verify nahi hain."),
    "Interchange details": ("परिवहन बदलाव का विवरण", "Interchange ka vivaran"),
    "Accessibility": ("सुगम्यता", "Accessibility"),
    "Recorded available": ("रिकॉर्ड में उपलब्ध", "Record mein available"),
    "Recorded unavailable": ("रिकॉर्ड में अनुपलब्ध", "Record mein unavailable"),
    "Partial published coverage: some links or route variants cannot be verified.": ("प्रकाशित कवरेज अधूरा है: कुछ कड़ियों या रूट विकल्पों की पुष्टि नहीं हो सकती।", "Published coverage partial hai: kuch links ya route variants verify nahi ho sakte."),
    "Omitted: {links} unusable links and {variants} route variant(s).": ("छोड़े गए: {links} अनुपयोगी कड़ियाँ और {variants} रूट विकल्प।", "Chhode gaye: {links} unusable links aur {variants} route variants."),
    "Hub-to-stop membership is provisional; the exact boarding location needs verification.": ("हब से स्टॉप का संबंध अस्थायी है; सही चढ़ने के स्थान की पुष्टि जरूरी है।", "Hub-to-stop membership provisional hai; exact boarding location verify karna zaroori hai."),
    "Snapshot-derived information. Verify current service and conditions with the operator.": ("यह जानकारी रिकॉर्ड के संकलन से मिली है। मौजूदा सेवा और स्थितियों की पुष्टि ऑपरेटर से करें।", "Snapshot se mili jaankari. Current service aur conditions operator se confirm karein."),
    "The snapshot contains up to {count} route-sequence candidates; current operation is unconfirmed.": ("रिकॉर्ड में अधिकतम {count} संभावित रूट क्रम हैं; मौजूदा संचालन की पुष्टि नहीं है।", "Snapshot mein {count} tak route-sequence candidates hain; current operation confirm nahi hai."),
    "The assistant returned no response.": ("सहायक ने कोई जवाब नहीं दिया।", "Assistant ne koi jawab nahi diya."),
    "Needed: {slots}": ("जरूरी जानकारी: {slots}", "Zaroori jaankari: {slots}"),
    "Question types: {intents}": ("प्रश्न के प्रकार: {intents}", "Sawaal ke types: {intents}"),
    "Question types: {intents}.": ("प्रश्न के प्रकार: {intents}।", "Sawaal ke types: {intents}."),
    "More than one stop or location matches. Include the route number, transport mode or precise stop name in your revised full question.": ("एक से अधिक स्टॉप या स्थान मेल खाते हैं। अपने पूरे संशोधित प्रश्न में रूट नंबर, परिवहन का माध्यम या सही स्टॉप नाम दें।", "Ek se zyada stop ya location match karte hain. Revised poore sawaal mein route number, transport mode ya exact stop name dein."),
    "The local T3 API is offline. Start it with `python -m app.api` to answer questions.": ("स्थानीय T3 API ऑफलाइन है। जवाब पाने के लिए इसे `python -m app.api` से शुरू करें।", "Local T3 API offline hai. Jawaab ke liye ise `python -m app.api` se start karein."),
    "Start with a complete question. Route and fare answers use the published snapshot; live status is unavailable.": ("पूरा प्रश्न पूछें। रूट और किराए के जवाब प्रकाशित रिकॉर्ड पर आधारित हैं; लाइव स्थिति अनुपलब्ध है।", "Poora sawaal poochhein. Route aur kiraya published snapshot se hain; live status unavailable hai."),
    "Nearby metro": ("नजदीकी मेट्रो", "Nazdeeki metro"),
    "Bus route stops": ("बस रूट के स्टॉप", "Bus route ke stops"),
    "Revise your full question": ("अपना पूरा प्रश्न संशोधित करें", "Apna poora sawaal revise karein"),
    "Ask revised question": ("संशोधित प्रश्न पूछें", "Revised sawaal poochhein"),
    "Ask about Chennai public transport…": ("चेन्नई के सार्वजनिक परिवहन के बारे में पूछें…", "Chennai public transport ke baare mein poochhein…"),
    "Language": ("भाषा", "Bhasha"),
    "Choose language": ("भाषा चुनें", "Bhasha chunein"),
    "min": ("मिनट", "min"),
    "Feature": ("सुविधा", "feature"),
    "Original explanation: {message}": ("मूल विवरण: {message}", "Mool vivaran / Original explanation: {message}"),
    "Original explanation: {message}.": ("मूल विवरण: {message}।", "Mool vivaran / Original explanation: {message}."),
    "Please provide {slots}.": ("कृपया {slots} बताएं।", "Kripya {slots} bataein."),
    "Published route candidate: {route} ({mode}). ": ("प्रकाशित संभावित रूट: {route} ({mode})। ", "Published route candidate: {route} ({mode}). "),
    "{route} stops: {stops}. ": ("{route} के स्टॉप: {stops}। ", "{route} ke stops: {stops}. "),
    "The stop appears on the published route sequence. ": ("यह स्टॉप प्रकाशित रूट क्रम में है। ", "Yeh stop published route sequence par hai. "),
    "The stop does not appear on the published route sequence. ": ("यह स्टॉप प्रकाशित रूट क्रम में नहीं है। ", "Yeh stop published route sequence par nahi hai. "),
    "Published first departure: {first}; last: {last} (service-day time). ": ("प्रकाशित पहला प्रस्थान: {first}; अंतिम: {last} (सेवा-दिन का समय)। ", "Prakashit pehla departure: {first}; aakhiri: {last} (service-day samay). "),
    "Published median interval: {minutes} minutes. ": ("प्रकाशित माध्यिका अंतराल: {minutes} मिनट। ", "Published median interval: {minutes} minutes. "),
    "Published departures: {departures} (service-day time). ": ("प्रकाशित प्रस्थान: {departures} (सेवा-दिन का समय)। ", "Prakashit departures: {departures} (service-day samay). "),
    "{route} at {time}": ("{route} — {time}", "{route} — {time}"),
    "Published fare{service}: {currency} {amount} (record effective {date}). ": ("प्रकाशित किराया{service}: {currency} {amount} (रिकॉर्ड की प्रभावी तारीख {date})। ", "Prakashit kiraya{service}: {currency} {amount} (record ki lagu tareekh {date}). "),
    "{feature} is recorded as available. ": ("{feature} रिकॉर्ड में उपलब्ध है। ", "{feature} record mein available hai. "),
    "{feature} is recorded as unavailable. ": ("{feature} रिकॉर्ड में अनुपलब्ध है। ", "{feature} record mein unavailable hai. "),
    "Nearest by straight line: {name} ({distance} m). ": ("सीधी दूरी से निकटतम: {name} ({distance} m)। ", "Seedhi doori se sabse nazdeek: {name} ({distance} m). "),
}

# Backend explanations are exact messages, not substring replacements.
_MESSAGES = {
    "Please enter a transport question.": ("कृपया परिवहन से जुड़ा प्रश्न पूछें।", "Kripya transport ka sawaal poochhein."),
    "Please provide a fare stage number, or the starting and destination stops.": ("कृपया किराए का स्टेज नंबर या शुरुआती और गंतव्य स्टॉप बताएं।", "Kripya fare stage number ya starting aur destination stops bataein."),
    "Please clarify which stop or location you mean.": ("कृपया स्पष्ट करें कि आप किस स्टॉप या स्थान की बात कर रहे हैं।", "Kripya batayein ki kaunsa stop ya location keh rahe hain."),
    "Please clarify the time or day you mean.": ("कृपया समय या दिन स्पष्ट करें।", "Kripya samay ya din saaf bataein."),
    "Please clarify the intended time or day.": ("कृपया इच्छित समय या दिन स्पष्ट करें।", "Kripya intended samay ya din saaf bataein."),
    "Please choose which transport question to answer first.": ("कृपया चुनें कि पहले किस परिवहन प्रश्न का जवाब चाहिए।", "Kripya chunein ki pehle kaunsa transport sawaal answer karein."),
    "Please clarify which transport question you mean.": ("कृपया अपना परिवहन प्रश्न स्पष्ट करें।", "Kripya apna transport sawaal saaf bataein."),
    "Please ask one transport question at a time.": ("कृपया एक बार में एक परिवहन प्रश्न पूछें।", "Kripya ek baar mein ek transport sawaal poochhein."),
    "Please choose one transport mode for this question.": ("कृपया इस प्रश्न के लिए परिवहन का एक माध्यम चुनें।", "Kripya is sawaal ke liye ek transport mode chunein."),
    "Please ask about one route, stop, fare stage or time at a time.": ("कृपया एक बार में एक रूट, स्टॉप, किराए के स्टेज या समय के बारे में पूछें।", "Kripya ek baar mein ek route, stop, fare stage ya samay poochhein."),
    "Please provide the missing journey information.": ("कृपया यात्रा की बाकी जरूरी जानकारी दें।", "Kripya journey ki missing jaankari dein."),
    "Please specify the destination to narrow the departure direction.": ("प्रस्थान की दिशा स्पष्ट करने के लिए कृपया गंतव्य बताएं।", "Departure direction narrow karne ke liye destination bataein."),
    "Waypoint-filtered timetable requests are unsupported. Ask for a boarding stop and destination without a waypoint.": ("बीच के स्थान से छाँटी गई समय-सारणी समर्थित नहीं है। बीच का स्थान दिए बिना चढ़ने का स्टॉप और गंतव्य पूछें।", "Waypoint-filtered timetable supported nahi hai. Waypoint ke bina boarding stop aur destination poochhein."),
    "Before-time and time-range requests are not supported by this operation.": ("यह ऑपरेशन किसी समय से पहले या समय के अंतराल वाले अनुरोधों को समर्थन नहीं देता।", "Yeh operation before-time aur time-range requests support nahi karta."),
    "The assistant could not process this question. Please try again.": ("सहायक यह प्रश्न संसाधित नहीं कर सका। कृपया फिर कोशिश करें।", "Assistant yeh sawaal process nahi kar saka. Phir try karein."),
    "The transport information is unavailable.": ("परिवहन की जानकारी अनुपलब्ध है।", "Transport ki jaankari unavailable hai."),
    "The transport service could not complete the request.": ("परिवहन सेवा अनुरोध पूरा नहीं कर सकी।", "Transport service request poori nahi kar saki."),
    "The transport service could not complete this request.": ("परिवहन सेवा यह अनुरोध पूरा नहीं कर सकी।", "Transport service yeh request poori nahi kar saki."),
    "The transport service returned an invalid state.": ("परिवहन सेवा ने अमान्य स्थिति लौटाई।", "Transport service ne invalid state return ki."),
    "Verified transport data is unavailable for this operation.": ("इस ऑपरेशन के लिए सत्यापित परिवहन डेटा अनुपलब्ध है।", "Is operation ke liye verified transport data unavailable hai."),
    "I can help with Chennai public transport questions.": ("मैं चेन्नई के सार्वजनिक परिवहन से जुड़े प्रश्नों में मदद कर सकता हूँ।", "Main Chennai public transport ke sawaalon mein madad kar sakta hoon."),
    "This assistant covers Chennai public transport questions only.": ("यह सहायक केवल चेन्नई के सार्वजनिक परिवहन से जुड़े प्रश्नों के लिए है।", "Yeh assistant sirf Chennai public transport ke sawaalon ke liye hai."),
    "Live transport status is unavailable; please verify with the operator.": ("लाइव परिवहन स्थिति अनुपलब्ध है; कृपया ऑपरेटर से पुष्टि करें।", "Live transport status unavailable hai; operator se verify karein."),
    "Live transport status is unavailable; verify with the operator.": ("लाइव परिवहन स्थिति अनुपलब्ध है; ऑपरेटर से पुष्टि करें।", "Live transport status unavailable hai; operator se verify karein."),
    "Unknown transport operation.": ("अज्ञात परिवहन ऑपरेशन।", "Unknown transport operation."),
    "The canonical transit database could not complete the request.": ("प्रामाणिक परिवहन डेटाबेस अनुरोध पूरा नहीं कर सका।", "Canonical transit database request poori nahi kar saka."),
    "No mode-consistent published topology is available for the requested transport mode.": ("माँगे गए परिवहन माध्यम से मेल खाता प्रकाशित रूट ढाँचा उपलब्ध नहीं है।", "Requested transport mode se matching published topology available nahi hai."),
    "No mode-consistent published schedule is available for the requested transport mode.": ("माँगे गए परिवहन माध्यम से मेल खाती प्रकाशित समय-सारणी उपलब्ध नहीं है।", "Requested transport mode se matching published schedule available nahi hai."),
    "This snapshot contains no authoritative ticket or pass policy table.": ("इस रिकॉर्ड संकलन में टिकट या पास नीति की कोई आधिकारिक तालिका नहीं है।", "Is snapshot mein authoritative ticket ya pass policy table nahi hai."),
    "Facility availability is not verified in this snapshot.": ("इस रिकॉर्ड संकलन में सुविधा की उपलब्धता सत्यापित नहीं है।", "Is snapshot mein facility availability verify nahi hai."),
    "No confirmed cross-mode transfer graph is available in this snapshot.": ("इस रिकॉर्ड संकलन में अलग परिवहन माध्यमों के बीच बदलाव का कोई पुष्ट नेटवर्क उपलब्ध नहीं है।", "Is snapshot mein confirmed cross-mode transfer graph available nahi hai."),
    "The snapshot has no confirmed interchange records.": ("इस रिकॉर्ड संकलन में परिवहन बदलाव के पुष्ट रिकॉर्ड नहीं हैं।", "Snapshot mein confirmed interchange records nahi hain."),
    "The snapshot contains no verified accessibility feature values.": ("इस रिकॉर्ड संकलन में सुगम्यता सुविधाओं की सत्यापित जानकारी नहीं है।", "Snapshot mein verified accessibility feature values nahi hain."),
    "Published route sequences cannot confirm travel at the requested date or time.": ("प्रकाशित रूट क्रम माँगी गई तारीख या समय पर यात्रा की पुष्टि नहीं कर सकते।", "Published route sequences requested date ya samay par travel confirm nahi kar sakte."),
    "Verified optimization for that route preference is unavailable.": ("उस रूट प्राथमिकता के लिए सत्यापित अनुकूलन अनुपलब्ध है।", "Us route preference ke liye verified optimization unavailable hai."),
    "No directionally valid published route sequence was found for these stops.": ("इन स्टॉपों के लिए सही दिशा वाला कोई प्रकाशित रूट क्रम नहीं मिला।", "In stops ke liye directionally valid published route sequence nahi mila."),
    "Published route-sequence candidates are available; verify service and transfers before travel.": ("प्रकाशित संभावित रूट क्रम उपलब्ध हैं; यात्रा से पहले सेवा और बदलाव की पुष्टि करें।", "Published route-sequence candidates available hain; travel se pehle service aur transfers verify karein."),
    " Partial published topology: unusable intermediate links are not verified.": (" प्रकाशित रूट ढाँचा अधूरा है: अनुपयोगी बीच की कड़ियाँ सत्यापित नहीं हैं।", " Published topology partial hai: unusable intermediate links verify nahi hain."),
    "No mode-consistent published stop sequence is available for that route.": ("उस रूट के लिए परिवहन माध्यम से मेल खाता प्रकाशित स्टॉप क्रम उपलब्ध नहीं है।", "Us route ke liye mode-consistent published stop sequence available nahi hai."),
    "Published stop sequences found. Service operation is not confirmed.": ("प्रकाशित स्टॉप क्रम मिले हैं। सेवा संचालन की पुष्टि नहीं है।", "Published stop sequences mile hain. Service operation confirm nahi hai."),
    "Partial published stop coverage found; unusable links or uncovered route variants are omitted. Service operation is not confirmed.": ("प्रकाशित स्टॉप कवरेज अधूरा है; अनुपयोगी कड़ियाँ या बिना कवरेज वाले रूट विकल्प छोड़े गए हैं। सेवा संचालन की पुष्टि नहीं है।", "Published stop coverage partial hai; unusable links ya uncovered route variants chhode gaye hain. Service operation confirm nahi hai."),
    "Route or stop is absent from the canonical snapshot.": ("रूट या स्टॉप प्रामाणिक रिकॉर्ड संकलन में नहीं है।", "Route ya stop canonical snapshot mein nahi hai."),
    "The route has no published stop sequence in this snapshot.": ("इस रिकॉर्ड संकलन में रूट का प्रकाशित स्टॉप क्रम नहीं है।", "Is snapshot mein route ka published stop sequence nahi hai."),
    "Incomplete mode-consistent route coverage cannot establish that the stop is absent.": ("परिवहन माध्यम से मेल खाता रूट कवरेज अधूरा है; इससे स्टॉप के न होने की पुष्टि नहीं होती।", "Mode-consistent route coverage incomplete hai; isse stop absent hona confirm nahi hota."),
    "Published route-stop sequence checked; current service is not confirmed.": ("प्रकाशित रूट-स्टॉप क्रम जाँचा गया है; मौजूदा सेवा की पुष्टि नहीं है।", "Published route-stop sequence check hua; current service confirm nahi hai."),
    "First/last service cannot interpret this clock constraint as before, after or at a time.": ("पहली/अंतिम सेवा इस घड़ी समय की शर्त को पहले, बाद या ठीक समय के रूप में नहीं समझ सकती।", "First/last service is clock constraint ko before, after ya at a time ke roop mein nahi samajh sakti."),
    "Too many schedule rows to report a reliable first or last time.": ("समय-सारणी के रिकॉर्ड इतने अधिक हैं कि भरोसेमंद पहला या अंतिम समय नहीं बताया जा सकता।", "Schedule rows bahut zyada hain; reliable first ya last samay nahi bataya ja sakta."),
    "No mode-consistent published schedule was found for this stop.": ("इस स्टॉप के लिए परिवहन माध्यम से मेल खाती प्रकाशित समय-सारणी नहीं मिली।", "Is stop ke liye mode-consistent published schedule nahi mila."),
    "Published schedule bounds; verify current operation with the operator.": ("ये प्रकाशित समय-सारणी की सीमाएँ हैं; मौजूदा संचालन की पुष्टि ऑपरेटर से करें।", "Yeh published schedule bounds hain; current operation operator se verify karein."),
    "A specific route or line is needed for a meaningful frequency estimate.": ("उपयोगी आवृत्ति अनुमान के लिए खास रूट या लाइन चाहिए।", "Meaningful frequency estimate ke liye specific route ya line chahiye."),
    "Insufficient published departures for a schedule-based frequency estimate.": ("समय-सारणी पर आधारित आवृत्ति अनुमान के लिए पर्याप्त प्रकाशित प्रस्थान नहीं हैं।", "Schedule-based frequency estimate ke liye published departures kaafi nahi hain."),
    "Specify a destination or unique physical stop to isolate a published departure direction.": ("प्रकाशित प्रस्थान की दिशा अलग करने के लिए गंतव्य या एक स्पष्ट भौतिक स्टॉप बताएं।", "Published departure direction isolate karne ke liye destination ya unique physical stop bataein."),
    "Published departures do not support a reliable frequency estimate.": ("प्रकाशित प्रस्थान भरोसेमंद आवृत्ति अनुमान का समर्थन नहीं करते।", "Published departures reliable frequency estimate support nahi karte."),
    "Median interval estimated from a published timetable, not live service.": ("माध्यिका अंतराल प्रकाशित समय-सारणी से अनुमानित है, लाइव सेवा से नहीं।", "Median interval published timetable se estimate hua hai, live service se nahi."),
    "No mode-consistent published departures were found for this stop.": ("इस स्टॉप के लिए परिवहन माध्यम से मेल खाते प्रकाशित प्रस्थान नहीं मिले।", "Is stop ke liye mode-consistent published departures nahi mile."),
    "No published departures were found after the requested time.": ("माँगे गए समय के बाद कोई प्रकाशित प्रस्थान नहीं मिला।", "Requested samay ke baad published departures nahi mile."),
    "Published departures only; times are not live predictions.": ("केवल प्रकाशित प्रस्थान; ये समय लाइव अनुमान नहीं हैं।", "Sirf published departures; yeh samay live predictions nahi hain."),
    "Static connectivity cannot confirm operating availability on the requested date or time.": ("स्थिर कनेक्टिविटी माँगी गई तारीख या समय पर सेवा संचालन की उपलब्धता की पुष्टि नहीं कर सकती।", "Static connectivity requested date ya samay par operating availability confirm nahi kar sakti."),
    "No mode-consistent directional connection is recorded; this does not establish that service is absent.": ("परिवहन माध्यम से मेल खाता दिशात्मक संबंध रिकॉर्ड में नहीं है; इससे सेवा के न होने की पुष्टि नहीं होती।", "Mode-consistent directional connection record nahi hai; isse service absent hona confirm nahi hota."),
    "A published directional connection is recorded; current operation is not confirmed. Verify before travel.": ("प्रकाशित दिशात्मक संबंध रिकॉर्ड में है; मौजूदा संचालन की पुष्टि नहीं है। यात्रा से पहले पुष्टि करें।", "Published directional connection record hai; current operation confirm nahi hai. Travel se pehle verify karein."),
    "The snapshot does not verify fare rules for that ticket type.": ("रिकॉर्ड संकलन उस टिकट प्रकार के किराया नियमों की पुष्टि नहीं करता।", "Snapshot us ticket type ke fare rules verify nahi karta."),
    "Bus service-class tariffs are unavailable for the requested mode.": ("माँगे गए माध्यम के लिए बस सेवा श्रेणी के किराए अनुपलब्ध हैं।", "Requested mode ke liye bus service-class tariffs unavailable hain."),
    "The canonical origin-destination fare table covers metro journeys only.": ("प्रामाणिक शुरुआती-गंतव्य किराया तालिका केवल मेट्रो यात्राओं के लिए है।", "Canonical origin-destination fare table sirf metro journeys cover karti hai."),
    "The requested fare type is not verified for a metro origin-destination fare.": ("मेट्रो के शुरुआती-गंतव्य किराए के लिए माँगा गया किराया प्रकार सत्यापित नहीं है।", "Metro origin-destination fare ke liye requested fare type verify nahi hai."),
    "The canonical stage fare table covers bus journeys only.": ("प्रामाणिक स्टेज किराया तालिका केवल बस यात्राओं के लिए है।", "Canonical stage fare table sirf bus journeys cover karti hai."),
    "The requested fare or ticket type is not verified for a bus stage fare.": ("बस स्टेज किराए के लिए माँगा गया किराया या टिकट प्रकार सत्यापित नहीं है।", "Bus stage fare ke liye requested fare ya ticket type verify nahi hai."),
    "Published fare record found; confirm the current fare before travel.": ("प्रकाशित किराया रिकॉर्ड मिला है; यात्रा से पहले मौजूदा किराए की पुष्टि करें।", "Published fare record mila hai; travel se pehle current kiraya confirm karein."),
    "Published stage fare found; confirm the current fare before travel.": ("प्रकाशित स्टेज किराया मिला है; यात्रा से पहले मौजूदा किराए की पुष्टि करें।", "Published stage kiraya mila hai; travel se pehle current kiraya confirm karein."),
    "No verified fare record covers the requested journey or stage.": ("माँगी गई यात्रा या स्टेज के लिए कोई सत्यापित किराया रिकॉर्ड नहीं है।", "Requested journey ya stage ke liye verified fare record nahi hai."),
    "No verified accessibility feature was requested.": ("कोई सत्यापित सुगम्यता सुविधा नहीं माँगी गई।", "Koi verified accessibility feature request nahi hua."),
    "That accessibility feature is not recorded in the snapshot.": ("वह सुगम्यता सुविधा रिकॉर्ड संकलन में दर्ज नहीं है।", "Woh accessibility feature snapshot mein record nahi hai."),
    "A single verified physical station is required for accessibility data.": ("सुगम्यता डेटा के लिए एक सत्यापित भौतिक स्टेशन चाहिए।", "Accessibility data ke liye ek verified physical station chahiye."),
    "The accessibility record does not verify this feature.": ("सुगम्यता रिकॉर्ड इस सुविधा की पुष्टि नहीं करता।", "Accessibility record is feature ko verify nahi karta."),
    "Recorded accessibility feature; confirm current working status with the operator.": ("सुगम्यता सुविधा रिकॉर्ड में है; अभी काम करने की स्थिति की पुष्टि ऑपरेटर से करें।", "Accessibility feature record mein hai; current working status operator se confirm karein."),
    "No confirmed interchange is available for this location.": ("इस स्थान के लिए परिवहन बदलाव की कोई पुष्ट जानकारी उपलब्ध नहीं है।", "Is location ke liye confirmed interchange available nahi hai."),
    "The snapshot has no confirmed interchange for this location.": ("रिकॉर्ड संकलन में इस स्थान के लिए परिवहन बदलाव की पुष्ट जानकारी नहीं है।", "Snapshot mein is location ke liye confirmed interchange nahi hai."),
    "Confirmed interchange records found.": ("परिवहन बदलाव के पुष्ट रिकॉर्ड मिले हैं।", "Confirmed interchange records mile hain."),
    "The requested location has no usable canonical coordinates.": ("माँगे गए स्थान के उपयोग योग्य प्रामाणिक निर्देशांक नहीं हैं।", "Requested location ke usable canonical coordinates nahi hain."),
    "No located transport stops match the requested mode.": ("माँगे गए माध्यम से मेल खाते स्थान वाले परिवहन स्टॉप नहीं मिले।", "Requested mode se matching located transport stops nahi mile."),
    "Nearest by straight-line distance only; walking access is not verified.": ("निकटतम केवल सीधी दूरी के आधार पर है; पैदल पहुँच सत्यापित नहीं है।", "Nearest sirf straight-line distance se hai; walking access verify nahi hai."),
    "The local T3 API is unavailable. Start the API and try again.": ("स्थानीय T3 API अनुपलब्ध है। API शुरू करके फिर कोशिश करें।", "Local T3 API unavailable hai. API start karke phir try karein."),
    "The T3 API returned an invalid response.": ("T3 API ने अमान्य जवाब लौटाया।", "T3 API ne invalid response return kiya."),
    "The T3 API could not complete this request.": ("T3 API यह अनुरोध पूरा नहीं कर सका।", "T3 API yeh request poori nahi kar saka."),
}
CATALOG.update(_MESSAGES)

_FIELDS = {
    "origin": ("शुरुआती स्टॉप", "starting stop"), "destination": ("गंतव्य स्टॉप", "destination stop"),
    "via": ("बीच का स्थान", "waypoint"), "station": ("स्टेशन", "station"), "stop": ("स्टॉप", "stop"),
    "landmark": ("पहचान का स्थान", "landmark"), "locality": ("इलाका", "locality"),
    "route_number": ("रूट नंबर", "route number"), "line_name": ("लाइन का नाम", "line name"),
    "transport_mode": ("परिवहन का माध्यम", "transport mode"), "mode_from": ("शुरुआती माध्यम", "starting mode"),
    "mode_to": ("बदलने के बाद का माध्यम", "destination mode"), "preference": ("प्राथमिकता", "preference"),
    "timing_type": ("समय का प्रकार", "samay ka type"), "time": ("समय", "samay"),
    "date": ("तारीख", "tareekh"), "temporal_relative": ("सापेक्ष समय", "relative samay"),
    "ticket_type": ("टिकट का प्रकार", "ticket type"), "fare_type": ("किराए का प्रकार", "kiraya type"),
    "stage_number": ("स्टेज नंबर", "stage number"), "service_type": ("सेवा श्रेणी", "service class"),
    "facility_type": ("सुविधा का प्रकार", "facility type"), "accessibility_feature": ("सुगम्यता सुविधा", "accessibility feature"),
    "station_or_stop": ("चढ़ने का स्टॉप या स्टेशन", "boarding stop ya station"),
    "route_number_or_line_name": ("रूट नंबर या लाइन का नाम", "route number ya line name"),
    "origin_or_stage_number": ("शुरुआती स्टॉप या किराए का स्टेज नंबर", "starting stop ya fare stage number"),
    "destination_or_stage_number": ("गंतव्य स्टॉप या किराए का स्टेज नंबर", "destination stop ya fare stage number"),
    "landmark_or_locality": ("नजदीकी पहचान का स्थान या इलाका", "nazdeeki landmark ya locality"),
    "station_or_mode_pair": ("बदलाव का स्टेशन या दो परिवहन माध्यम", "transfer station ya do transport modes"),
    "point_to_point_route": ("दो स्थानों के बीच रूट", "do jagah ke beech route"),
    "multimodal_route": ("अलग माध्यमों वाली यात्रा", "alag modes wali journey"),
    "route_stop_sequence": ("रूट के स्टॉप का क्रम", "route stops ka sequence"),
    "route_stop_membership": ("रूट में स्टॉप शामिल है या नहीं", "stop route par hai ya nahi"),
    "first_and_last_service": ("पहली और अंतिम सेवा", "pehli aur aakhiri service"),
    "service_frequency": ("सेवा का अंतराल", "service ka interval"),
    "scheduled_departure": ("प्रकाशित प्रस्थान", "published departure"),
    "mode_availability": ("परिवहन माध्यम की उपलब्धता", "transport mode ki availability"),
    "fare_calculation": ("किराए की जानकारी", "kiraya jaankari"),
    "ticketing_and_passes": ("टिकट और पास", "ticket aur pass"),
    "station_facilities": ("स्टेशन की सुविधाएँ", "station facilities"),
    "station_accessibility": ("स्टेशन की सुगम्यता", "station accessibility"),
    "interchange_transfer": ("परिवहन बदलाव", "interchange transfer"),
    "nearest_transport": ("नजदीकी परिवहन", "nazdeeki transport"),
    "realtime_status_query": ("लाइव स्थिति", "live status"), "out_of_scope": ("दायरे से बाहर", "scope ke bahar"),
    "bus": ("बस", "bus"), "metro": ("मेट्रो", "metro"), "suburban_rail": ("उपनगरीय रेल", "suburban rail"),
    "mrts": ("MRTS", "MRTS"), "any": ("कोई भी", "koi bhi"),
    "Ordinary Services": ("साधारण सेवाएँ", "Ordinary services"),
    "Express Services": ("एक्सप्रेस सेवाएँ", "Express services"),
    "Deluxe Services": ("डीलक्स सेवाएँ", "Deluxe services"),
    "Night Services": ("रात्रि सेवाएँ", "Night services"),
    "Air Conditioned Services": ("वातानुकूलित सेवाएँ", "Air conditioned services"),
    "wheelchair": ("व्हीलचेयर", "wheelchair"), "lift": ("लिफ्ट", "lift"), "escalator": ("एस्केलेटर", "escalator"),
    "ramp": ("रैंप", "ramp"), "accessible_toilet": ("सुगम शौचालय", "accessible toilet"),
    "tactile_paths": ("स्पर्शनीय मार्ग", "tactile paths"), "parking": ("पार्किंग", "parking"),
    "interchange": ("परिवहन बदलाव", "interchange"), "restroom": ("शौचालय", "restroom"),
    "waiting_room": ("प्रतीक्षालय", "waiting room"), "cloak_room": ("सामान रखने का कमरा", "cloak room"),
    "atm": ("ATM", "ATM"), "wifi": ("Wi-Fi", "Wi-Fi"), "drinking_water": ("पीने का पानी", "peene ka paani"),
    "route_name": ("रूट का नाम", "route name"), "mode": ("माध्यम", "mode"), "source": ("स्रोत", "Source"),
    "sequence": ("क्रम", "sequence"), "name": ("नाम", "naam"), "distance_m": ("दूरी (m)", "doori (m)"),
    "from_stop_id": ("शुरुआती स्टॉप ID", "starting stop ID"), "to_stop_id": ("अंतिम स्टॉप ID", "destination stop ID"),
    "walking_distance_m": ("पैदल दूरी (m)", "walking doori (m)"),
    "walking_time_min": ("पैदल समय (मिनट)", "walking samay (min)"),
}

_MISSING_DESCRIPTIONS = {
    "origin": "the starting stop", "destination": "the destination stop", "stop": "the stop to check",
    "station": "the station", "station_or_stop": "the boarding stop or station",
    "route_number_or_line_name": "the route number or line name",
    "origin_or_stage_number": "the starting stop or fare stage number",
    "destination_or_stage_number": "the destination stop or fare stage number",
    "landmark_or_locality": "a nearby landmark or locality",
    "station_or_mode_pair": "the transfer station or the two transport modes",
    "transport_mode": "one transport mode",
    "service_type": "the bus service class (Ordinary, Express, Deluxe, Night or Air Conditioned)",
    "route_number": "a supported route number including its complete suffix",
    "via": "a recognized waypoint after “via”",
}
_MISSING_LOCALIZED = {
    "service_type": ("बस सेवा श्रेणी (साधारण, एक्सप्रेस, डीलक्स, रात्रि या वातानुकूलित)", "bus service class (Ordinary, Express, Deluxe, Night ya Air Conditioned)"),
    "route_number": ("पूरे प्रत्यय सहित समर्थित रूट नंबर", "poore suffix ke saath supported route number"),
    "via": ("“via” के बाद पहचाना गया बीच का स्थान", "“via” ke baad recognized waypoint"),
}

# UI panels use tr() for exact header and enum values as well as prose.
# Exact-key lookup cannot alter words contained inside a canonical name.
CATALOG.update(_FIELDS)


def _language(language: str) -> str:
    return language if language in LANGUAGE_NAMES else "en"


def tr(english_template: str, language: str = "en", **values) -> str:
    """Translate an exact template and interpolate untouched caller values."""
    language = _language(language)
    translations = CATALOG.get(english_template)
    template = english_template if language == "en" or not translations else translations[0 if language == "hi" else 1]
    return template.format(**values) if values else template


def field_label(internal_code: str, language: str = "en") -> str:
    """Translate only known field/enum codes; arbitrary names stay untouched."""
    if not isinstance(internal_code, str):
        return internal_code
    language = _language(language)
    translations = _FIELDS.get(internal_code)
    if not translations:
        return internal_code
    if language == "en":
        return internal_code.replace("_", " ")
    return translations[0 if language == "hi" else 1]


def _explanation(message: str, language: str) -> str:
    if not message:
        return ""
    if message in CATALOG:
        return tr(message, language)
    caveat = " Partial published topology: unusable intermediate links are not verified."
    if message.endswith(caveat) and message[:-len(caveat)] in _MESSAGES:
        return tr(message[:-len(caveat)], language) + tr(caveat, language)
    return tr("Original explanation: {message}", language, message=message)


def _number(value) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value):
        return f"{value:g}"
    return None


def _fact_prefix(reply: dict, language: str) -> tuple[str, str] | None:
    """Return exact backend prefix and localized prefix, without inferring facts."""
    data, operation = reply.get("data", {}), reply.get("operation")
    if not isinstance(data, dict):
        return None
    key, values = None, {}
    try:
        if operation == "PLAN_ROUTE" and data.get("routes"):
            row = data["routes"][0]
            key, values = "Published route candidate: {route} ({mode}). ", {"route": row["route_name"], "mode": row["mode"]}
        elif operation == "LIST_ROUTE_STOPS" and data.get("sequences"):
            row = data["sequences"][0]
            names = ", ".join(stop["name"] for stop in row["stops"][:8])
            names += ", …" if len(row["stops"]) > 8 else ""
            key, values = "{route} stops: {stops}. ", {"route": row["route_name"], "stops": names}
        elif operation == "CHECK_STOP_ON_ROUTE" and type(data.get("on_route")) is bool:
            key = "The stop appears on the published route sequence. " if data["on_route"] else "The stop does not appear on the published route sequence. "
        elif operation == "GET_FIRST_LAST_SERVICE":
            key, values = "Published first departure: {first}; last: {last} (service-day time). ", {"first": data["first_departure"], "last": data["last_departure"]}
        elif operation == "GET_SERVICE_FREQUENCY" and _number(data.get("median_headway_minutes")) is not None:
            key, values = "Published median interval: {minutes} minutes. ", {"minutes": _number(data["median_headway_minutes"])}
        elif operation == "GET_SCHEDULED_DEPARTURES":
            rows = data.get("departures", [])
            original = ", ".join(f"{row['route_name']} at {row['time']}" for row in rows)
            localized = ", ".join(tr("{route} at {time}", language, route=row["route_name"], time=row["time"]) for row in rows)
            key = "Published departures: {departures} (service-day time). "
            return tr(key, "en", departures=original), tr(key, language, departures=localized)
        elif operation == "CALCULATE_FARE" and _number(data.get("amount")) is not None:
            service = f" ({data['service_type']})" if data.get("service_type") else ""
            key = "Published fare{service}: {currency} {amount} (record effective {date}). "
            values = {"service": service, "currency": data["currency"], "amount": _number(data["amount"]), "date": data["effective_date"]}
        elif operation == "GET_ACCESSIBILITY_INFO":
            available = "available" if data.get("available") else "unavailable"
            key, values = "{feature} is recorded as " + available + ". ", {"feature": data.get("feature", "Feature")}
        elif operation == "FIND_NEAREST_STATION" and data.get("stops"):
            row = data["stops"][0]
            key, values = "Nearest by straight line: {name} ({distance} m). ", {"name": row["name"], "distance": row["distance_m"]}
    except (KeyError, TypeError, IndexError, AttributeError):
        return None
    if key is None:
        return None
    if any(not isinstance(values[name], str) for name in ("mode", "feature") if name in values):
        return None
    if data.get("service_type") and not isinstance(data["service_type"], str):
        return None
    original = tr(key, "en", **values)
    localized_values = dict(values)
    if "mode" in values:
        localized_values["mode"] = field_label(values["mode"], language)
    if "feature" in values:
        localized_values["feature"] = field_label(values["feature"], language)
    if key.startswith("Published fare") and data.get("service_type"):
        localized_values["service"] = f" ({field_label(data['service_type'], language)})"
    return original, tr(key, language, **localized_values)


def reply_text(reply: dict, language: str = "en") -> str:
    """Localize known response explanations without hiding unknown qualifications."""
    message = reply.get("response_text", "The assistant returned no response.")
    language = _language(language)
    if language == "en":
        return message
    if message in CATALOG:
        return tr(message, language)
    missing = reply.get("missing_slots", [])
    if reply.get("status") == "clarification" and missing and isinstance(missing, (list, tuple)):
        expected = "Please provide " + ", ".join(_MISSING_DESCRIPTIONS.get(name, name.replace("_", " ")) for name in missing) + "."
        if message == expected:
            values = ", ".join(_MISSING_LOCALIZED[name][0 if language == "hi" else 1] if name in _MISSING_LOCALIZED else field_label(name, language) for name in missing)
            return tr("Please provide {slots}.", language, slots=values)
    if reply.get("status") == "ok":
        prefix = _fact_prefix(reply, language)
        if prefix and message.startswith(prefix[0]):
            return prefix[1] + _explanation(message[len(prefix[0]):], language)
    return _explanation(message, language)


def examples(language: str = "en") -> list[tuple[str, str]]:
    """Explicit example questions, sent verbatim when chosen by the user."""
    language = _language(language)
    queries = {
        "en": ("Where is the nearest metro station to Marina Beach?", "List stops on bus route 102", "What is the deluxe bus fare for stage 4?"),
        "hi": ("Marina Beach के सबसे नजदीक मेट्रो स्टेशन कौन सा है?", "बस रूट 102 के स्टॉप बताएं", "स्टेज 4 का डीलक्स बस किराया कितना है?"),
        "hinglish": ("Marina Beach ke sabse nazdeek metro station kaunsa hai?", "Bus route 102 ke stops batao", "Stage 4 ka deluxe bus kiraya kitna hai?"),
    }
    labels = ("Nearby metro", "Bus route stops", "Published fare")
    return [(tr(label, language), query) for label, query in zip(labels, queries[language])]


def _placeholders(template: str) -> list[tuple[str, str, str]]:
    return sorted((field, spec, conversion or "") for _, field, spec, conversion in Formatter().parse(template) if field is not None)


# Fail at catalog authoring time rather than dropping a factual value in the UI.
for _english, _translations in CATALOG.items():
    if any(_placeholders(_english) != _placeholders(_translated) for _translated in _translations):
        raise ValueError(f"Translation changes template placeholders: {_english}")
