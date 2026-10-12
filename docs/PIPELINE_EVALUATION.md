# Small Hindi/Hinglish pipeline check

Ninety AI-authored, unreviewed questions: 45 paired Hindi/Hinglish scenarios across nine intents. Their exact questions were excluded from training. Diagnostic failures informed a later training-data coverage correction; epoch selection still used only the declared validation partition. This is a reproducible diagnostic, not a blind human benchmark or real-passenger accuracy estimate.

Pipeline success requires correct intent, evaluated slot values, response status and exact catalog record IDs, with source attribution when records are returned. It does not judge fluency, full answer semantics or physical travel feasibility.

| Model | Intent accuracy | Macro F1 | Slot F1 | Slot exact match | Pipeline success |
| --- | --- | --- | --- | --- | --- |
| tfidf | 0.956 | 0.955 | 1.000 | 1.000 | 0.933 |
| muril_finetuned | 0.822 | 0.791 | 1.000 | 1.000 | 0.800 |

Evaluated slots: origin, destination, transport_mode, accessibility_feature, complaint_type. Name recognition reuses the full canonical database and its stored aliases. These checks mainly cover the seven curated example locations; they do not evaluate all database names, unknown-name span detection or a learned NER model. The original expected statuses are retained: broader-name ambiguity can now produce clarification where the earlier seven-name lookup returned unavailable.

## Per-language classification

| Model | Language | Accuracy | Macro F1 |
| --- | --- | --- | --- |
| tfidf | hi | 0.978 | 0.978 |
| tfidf | hinglish | 0.933 | 0.931 |
| muril_finetuned | hi | 0.822 | 0.799 |
| muril_finetuned | hinglish | 0.822 | 0.781 |

## tfidf: retained failures

- Avadi aur Koyambedu ke beech bus available hai? — expected service_availability, predicted service_availability; failed checks: status.
- Tambaram ki first bus kab rawana hogi? — expected service_timing, predicted service_timing; failed checks: status.
- Central ki train scheduled time se kitni der peeche hai? — expected train_status, predicted service_timing; failed checks: intent.
- पौधों को पानी देने का तरीका समझाओ। — expected out_of_scope, predicted route_query; failed checks: intent, status.
- Paudhon ko paani dene ka tareeka samjhao. — expected out_of_scope, predicted route_query; failed checks: intent, status.
- Chennai ka mausam kaisa rahega? — expected out_of_scope, predicted route_query; failed checks: intent, status.

## muril_finetuned: retained failures

- Avadi aur Koyambedu ke beech bus available hai? — expected service_availability, predicted service_availability; failed checks: status.
- Tambaram ki first bus kab rawana hogi? — expected service_timing, predicted service_timing; failed checks: status.
- सेंट्रल की ट्रेन निर्धारित समय से कितनी देर पीछे है? — expected train_status, predicted service_timing; failed checks: intent.
- Central ki train scheduled time se kitni der peeche hai? — expected train_status, predicted service_timing; failed checks: intent.
- एग्मोर आने वाली ट्रेन की आज की स्थिति चाहिए। — expected train_status, predicted service_timing; failed checks: intent.
- Egmore aane wali train ka aaj ka status chahiye. — expected train_status, predicted service_timing; failed checks: intent.
- मेरी ट्रेन आज निरस्त हुई क्या? — expected train_status, predicted service_timing; failed checks: intent.
- रेल के कोच की खिड़की खराब है। — expected railway_complaint, predicted accessibility; failed checks: intent, status.
- Rail ke coach ki khidki kharab hai. — expected railway_complaint, predicted service_timing; failed checks: intent, status.
- आज कौन सा क्रिकेट मैच है? — expected out_of_scope, predicted service_timing; failed checks: intent, status.
- Aaj kaunsa cricket match hai? — expected out_of_scope, predicted service_timing; failed checks: intent, status.
- पौधों को पानी देने का तरीका समझाओ। — expected out_of_scope, predicted railway_complaint; failed checks: intent, status.
- Paudhon ko paani dene ka tareeka samjhao. — expected out_of_scope, predicted route_query; failed checks: intent, status.
- Ek chhoti kahani sunaiye. — expected out_of_scope, predicted station_information; failed checks: intent, status.
- चेन्नई का मौसम कैसा रहेगा? — expected out_of_scope, predicted service_timing; failed checks: intent, status.
- Chennai ka mausam kaisa rahega? — expected out_of_scope, predicted service_timing; failed checks: intent, status.
- सेंट्रल पर मेरे फोन का इंटरनेट नहीं चल रहा। फोन ठीक करने में मदद करो। — expected out_of_scope, predicted ticketing; failed checks: intent, status.
- Central par mere phone ka internet nahi chal raha. Phone theek karne mein help karo. — expected out_of_scope, predicted ticketing; failed checks: intent, status.

## Four user-supplied questions

These four Hinglish inputs were supplied by the user and excluded from training. They were visible during implementation, so they are qualitative demonstrations, not a blind benchmark. Ground-truth intent labels were assigned by the assistant.

First-pass TF-IDF classified one of these four intents correctly; after a general training-data correction it classified all four correctly. MuRIL classified all four in both passes. These inputs informed development and are not evidence of unseen-user accuracy. First-pass predictions are retained in `data/project/development_history.json`.

### tfidf

- **Guindy se Central kaise jayein?**
  - Expected intent: `route_query`; predicted: `route_query`; status: `information`.
  - Guindy Metro se Chennai Central ke liye Blue Line ki published connectivity recorded hai. Yeh live service ya railway-to-metro walking/accessibility ki confirmation nahi hai.
- **Velachery se Park station kaise jayein?**
  - Expected intent: `route_query`; predicted: `route_query`; status: `clarification`.
  - velachery, park station database mein pehchane gaye hain, lekin ek se zyada station/stop matches hain. Metro, railway, MRTS ya bus aur poora station/stop naam likhein.
- **Chennai Central se Mambalam station kaise jau?**
  - Expected intent: `route_query`; predicted: `route_query`; status: `clarification`.
  - chennai central database mein pehchane gaye hain, lekin ek se zyada station/stop matches hain. Metro, railway, MRTS ya bus aur poora station/stop naam likhein.
- **Subah sabse pehle train guindy se chennai central kab hai?**
  - Expected intent: `service_timing`; predicted: `service_timing`; status: `unavailable`.
  - Station names pehchane gaye hain, lekin maangi gayi service ka departure timetable is database mein available nahi hai. First/last train ka time andaaze se nahi bataya ja sakta.
### muril_finetuned

- **Guindy se Central kaise jayein?**
  - Expected intent: `route_query`; predicted: `route_query`; status: `information`.
  - Guindy Metro se Chennai Central ke liye Blue Line ki published connectivity recorded hai. Yeh live service ya railway-to-metro walking/accessibility ki confirmation nahi hai.
- **Velachery se Park station kaise jayein?**
  - Expected intent: `route_query`; predicted: `route_query`; status: `clarification`.
  - velachery, park station database mein pehchane gaye hain, lekin ek se zyada station/stop matches hain. Metro, railway, MRTS ya bus aur poora station/stop naam likhein.
- **Chennai Central se Mambalam station kaise jau?**
  - Expected intent: `route_query`; predicted: `route_query`; status: `clarification`.
  - chennai central database mein pehchane gaye hain, lekin ek se zyada station/stop matches hain. Metro, railway, MRTS ya bus aur poora station/stop naam likhein.
- **Subah sabse pehle train guindy se chennai central kab hai?**
  - Expected intent: `service_timing`; predicted: `service_timing`; status: `unavailable`.
  - Station names pehchane gaye hain, lekin maangi gayi service ka departure timetable is database mein available nahi hai. First/last train ka time andaaze se nahi bataya ja sakta.

## Reproduce

Run `python -m scripts.nlp_v2.evaluate_project` after training. Exact per-question outputs and confusion matrices are saved in `models/hindi_project_checks.json`. Do not train or tune on these checks; retain errors in the report. Human review remains outstanding.
