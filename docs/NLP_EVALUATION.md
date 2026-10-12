# Hindi / Hinglish intent-classification experiment

Synthetic teaching data; template families are disjoint across train/validation/test. These results are not real-passenger accuracy. The frozen 400-query challenge is not used.

Rows: {'train': 1112, 'validation': 216, 'test': 324}. Seed: 42. Pooling: mean. Selected epoch: 1 (validation only).

The existing transport-fine-tuned MuRIL checkpoint is reused. Its final two encoder layers and a new nine-class head are trained for 5 epochs; the remaining encoder and embeddings are frozen. This is partial fine-tuning, not a fresh pretrained-model comparison. No hyperparameter search was run.

| Model | Split | Accuracy | Macro precision | Macro recall | Macro F1 |
| --- | --- | --- | --- | --- | --- |
| tfidf | validation | 0.981 | 0.983 | 0.981 | 0.981 |
| tfidf | test | 0.975 | 0.980 | 0.975 | 0.975 |
| muril_finetuned | validation | 0.884 | 0.887 | 0.884 | 0.882 |
| muril_finetuned | test | 0.787 | 0.823 | 0.787 | 0.780 |

## Hindi and Hinglish separately

| Model | Language | Test rows | Accuracy | Macro F1 |
| --- | --- | --- | --- | --- |
| tfidf | hi | 216 | 0.963 | 0.962 |
| tfidf | hinglish | 108 | 1.000 | 1.000 |
| muril_finetuned | hi | 216 | 0.833 | 0.832 |
| muril_finetuned | hinglish | 108 | 0.694 | 0.660 |

## tfidf: test confusion matrix

Rows are true labels; columns are predicted labels.

| True / predicted | route_query | service_availability | service_timing | station_information | accessibility | ticketing | train_status | railway_complaint | out_of_scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| route_query | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| service_availability | 0 | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| service_timing | 0 | 8 | 28 | 0 | 0 | 0 | 0 | 0 | 0 |
| station_information | 0 | 0 | 0 | 36 | 0 | 0 | 0 | 0 | 0 |
| accessibility | 0 | 0 | 0 | 0 | 36 | 0 | 0 | 0 | 0 |
| ticketing | 0 | 0 | 0 | 0 | 0 | 36 | 0 | 0 | 0 |
| train_status | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 0 | 0 |
| railway_complaint | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 | 0 |
| out_of_scope | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 |

Example classification errors:

- सेवा शुरू और समाप्त होने का वक्त चेन्नई सेंट्रल की बस के लिए बताओ। → service_availability (label: service_timing)
- सेवा शुरू और समाप्त होने का वक्त चेन्नई सेंट्रल की मेट्रो के लिए बताओ। → service_availability (label: service_timing)
- सेवा शुरू और समाप्त होने का वक्त एग्मोर की मेट्रो के लिए बताओ। → service_availability (label: service_timing)
- सेवा शुरू और समाप्त होने का वक्त एग्मोर की बस के लिए बताओ। → service_availability (label: service_timing)
- सेवा शुरू और समाप्त होने का वक्त तांबरम की बस के लिए बताओ। → service_availability (label: service_timing)

## muril_finetuned: test confusion matrix

Rows are true labels; columns are predicted labels.

| True / predicted | route_query | service_availability | service_timing | station_information | accessibility | ticketing | train_status | railway_complaint | out_of_scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| route_query | 20 | 0 | 0 | 11 | 0 | 0 | 0 | 0 | 5 |
| service_availability | 0 | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| service_timing | 0 | 0 | 36 | 0 | 0 | 0 | 0 | 0 | 0 |
| station_information | 0 | 0 | 0 | 29 | 0 | 0 | 0 | 0 | 7 |
| accessibility | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 24 | 0 |
| ticketing | 0 | 0 | 0 | 0 | 0 | 36 | 0 | 0 | 0 |
| train_status | 0 | 0 | 0 | 5 | 0 | 0 | 30 | 0 | 1 |
| railway_complaint | 0 | 0 | 0 | 0 | 2 | 9 | 0 | 25 | 0 |
| out_of_scope | 1 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 31 |

Example classification errors:

- मैं एग्मोर पर हूँ, एयरपोर्ट तक सफर कैसे करूँ? → station_information (label: route_query)
- मैं एग्मोर पर हूँ, गिंडी तक सफर कैसे करूँ? → station_information (label: route_query)
- मैं अवडी पर हूँ, गिंडी तक सफर कैसे करूँ? → station_information (label: route_query)
- एयरपोर्ट तक आने-जाने के रास्ते की जानकारी एग्मोर से चाहिए। → out_of_scope (label: route_query)
- गिंडी तक आने-जाने के रास्ते की जानकारी एग्मोर से चाहिए। → out_of_scope (label: route_query)

## Entity / slot extraction

Rule-based gazetteer, 72 linked synthetic test queries: precision 1.000, recall 1.000, F1 1.000, exact match 1.000.

Fields evaluated: origin, destination and transport mode. Intent prediction is held out of this component measurement; these are related synthetic questions, not independent passenger data or end-to-end accuracy.

Per-class precision, recall, F1 and support are saved in `models/hindi_project_metrics.json`. Human-authored Hindi examples and broader entity evaluation remain academic follow-up work.
