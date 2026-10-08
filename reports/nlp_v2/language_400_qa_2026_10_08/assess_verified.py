"""Manual judgments for every changed final reply; reuse byte-identical reviews.

Original independent assessments remain unchanged. Domain rejections are
normalized to safe_limitation because they do not fulfill a transport goal.
These observed custom cases are development QA, never independent accuracy.
"""
import csv
import json
from collections import Counter
from pathlib import Path
P = Path(__file__).parent
# Explicit semantic review, read alongside authored expectations and full JSON.
REVIEWS = {
'hindi': {
6: ('safe_limitation','mode_consistent_source_limit','Explicit suburban mode now survives. Correct journey family refuses absent topology; endpoints remain unverified under terminal source preflight.'),
12: ('recognition_failure','negated_prediction_guarded','Excluded fare no longer produces INR20. Positive route goal is explicit, but the unchanged classifier chooses fare and the guard asks intent again. Safer, still a recognition failure.'),
51: ('safe_limitation','mode_consistent_source_limit','Local rail phrase now retains suburban mode and first-service timing; false कल is gone. Published suburban schedules are absent; station recognition is bypassed/unverified.'),
59: ('safe_limitation','mode_consistent_source_limit','Suburban mode and last timing survive. No timetable is invented. Sunday/station extraction is not established by the source preflight.'),
63: ('recognition_failure','wrong_family_with_corrected_substring','False कल and missing suburban mode are fixed, but frequency still becomes availability. Wrong-family source refusal remains failure.'),
75: ('safe_limitation','mode_consistent_source_limit','Suburban mode retained, false कल removed; correct scheduled-departure family discloses absent published schedules.'),
76: ('safe_limitation','source_limit_with_corrected_period','दोपहर२:३० now yields14:30. Correct metro schedule source refusal remains source-limited, not a timetable answer.'),
87: ('safe_limitation','mode_consistent_source_limit','Correct suburban availability family and mode now disclose missing topology; does not assert a connection exists.'),
91: ('safe_limitation','source_limit_with_secondary_endpoint_issue','Negative availability question is retained as availability, with suburban mode and no false कल. Source absence blocks connection facts. Returned origin=Central still misuses the supplied destination; no completed OD extraction is claimed.'),
97: ('goal_correct','dated_published_stage_tariff','Ordinary class and spelled stage4 retained; INR8 is a dated official2018 tariff with source and current-fare caveat.'),
98: ('goal_correct','dated_published_stage_tariff','Express class and Devanagari stage6 retained; dated official2018 INR15 tariff, source and current-fare caveat supplied.'),
99: ('goal_correct','dated_published_stage_tariff','Deluxe class and आठ चरण=8 retained; dated official INR25 tariff supplied with source/effective date and current-fare caveat.'),
100: ('goal_correct','dated_published_stage_tariff','रात्रि सेवा now maps explicitly to Night, and पाँच=5. Dated Night INR19 tariff is supplied; Ordinary fallback seen in the intermediate postfix run is corrected.'),
101: ('safe_limitation','requested_class_source_absent','AC and stage10 retained. No verified AC tariff exists for this scope, so source limitation replaces the unnecessary stage prompt.'),
104: ('goal_correct','dated_published_stage_tariff','Ordinary and तीन=3 retained; dated official INR7 tariff is returned with source/effective date and current-fare caveat.'),
105: ('legitimate_clarification','genuine_unknown_service_class','Stage4 preserved; explicitly unknown service class now prompts for class rather than silently defaulting Ordinary.'),
107: ('legitimate_clarification','invalid_stage_clarified','Invalid zero stage now requests a valid stage, without fare execution.'),
108: ('legitimate_clarification','invalid_stage_clarified','31 is outside supported1–30 stages; valid-stage clarification does not truncate to a supported number.'),
143: ('recognition_failure','negated_prediction_guarded','Excluded parking/facility prediction is guarded. Explicit lift/accessibility goal still not recognized by unchanged classifier; asking intent again remains failure.'),
156: ('recognition_failure','negated_prediction_guarded','Excluded parking prediction is guarded; explicit line-transfer goal remains unrecognized, so intent clarification does not fulfill it.'),
165: ('needs_review','published_rail_mode_labels_need_source_audit','Requested suburban mode now filters the actual source records and no bus is returned. Published RAIL_THIRUVALLIKENI/RAIL_LIGHT_HOUSE are labelled suburban_rail in the unchanged snapshot. Their separation from MRTS needs an independent source audit; no factual mode-correct success is claimed.'),
194: ('legitimate_clarification','genuine_multiple_goals','Stop list plus live bus position are both retained as candidate families. Neither is partially executed; asks which to answer first.'),
199: ('recognition_failure','negated_stage_count_competes','Positive stage10 and excluded stage4 are conservatively treated as competing scopes. No wrong fare executes, but the explicit positive count is not recognized.'),
},
'hinglish': {
33: ('goal_correct','published_structured_stop_sequence','Hindi-digit25R possessive code preserved; actual JSON supplies the complete ordered published33-stop variant, with no coverage gaps and source/operation caveat.'),
50: ('recognition_failure','wrong_first_last_family_safely_route_filtered','25R now retained, preventing unrelated departures. Last-service question still becomes scheduled_departure; no matching departures is safe but remains wrong family.'),
55: ('legitimate_clarification','genuine_missing_boarding_stop','21G and last timing retained. Boarding stop is explicitly absent, so the single stop prompt is necessary.'),
58: ('recognition_failure','supplied_boarding_stop_unrecognized','570S suffix now retained, but explicit Kelambakkam boarding stop is still lost and requested again.'),
59: ('recognition_failure','negated_prediction_guarded','Excluded live prediction is guarded, but explicit first published-metro service is still not recognized.'),
60: ('recognition_failure','wrong_first_last_family_with_route_fix','21G is retained but first-service question remains scheduled_departure. Safe waypoint limitation does not rescue wrong family.'),
65: ('recognition_failure','plural_mode_fixed_route_still_missing','Plural buses now retains bus and narrows physical Saidapet candidates, but supplied21 G route is still absent. Partial fix is not full legitimate clarification.'),
71: ('recognition_failure','wrong_frequency_family','Plural bus mode now survives; frequency request still becomes scheduled_departure, and102 route is omitted. Waypoint refusal remains wrong family.'),
72: ('recognition_failure','wrong_frequency_family_with_route_fix','25R now survives and kal correctly clarifies day; frequency remains scheduled_departure, so wrong family is unresolved.'),
76: ('safe_limitation','source_limit_with_corrected_period','shaam6:20 now18:20, station/mode retained. Metro schedule absence remains a source limitation.'),
98: ('goal_correct','dated_published_stage_tariff','Express and11 stages retained; dated official INR22 stage tariff includes source/effective date and current-fare caveat.'),
99: ('goal_correct','dated_published_stage_tariff','Deluxe and8 stage retained; dated official INR25 tariff includes source/effective date and current-fare caveat.'),
102: ('goal_correct','dated_published_stage_tariff','Ordinary and native६ stage retained; dated official INR10 tariff includes source/effective date and current-fare caveat.'),
106: ('legitimate_clarification','genuinely_missing_fare_basis','Both endpoints and stage are explicitly absent. Valid-stage prompt requests a genuinely missing fare basis; no arbitrary tariff.'),
143: ('recognition_failure','negated_prediction_guarded','Excluded parking prediction guarded. Explicit lift goal remains unrecognized by classifier and asks intent again.'),
155: ('recognition_failure','negated_prediction_guarded','Excluded fare no longer asks fare endpoints. Explicit interchange goal still unrecognized; intent prompt remains failure.'),
158: ('needs_review','unqualified_landmark_alias_selects_specific_campus','Generic bus-stop target no longer becomes an anchor. Actual resolver selects IIT Madras, Thaiyur Campus for unqualified IIT Madras and returns a distance around that campus. User did not specify campus; this source/alias selection needs audit and is not credited as goal success.'),
161: ('legitimate_clarification','genuine_reference_location_specificity','Single nearest-bus goal now retains mode and asks which physical Besant Nagar reference is intended, with four distinct source stop candidates. Does not silently choose a locality coordinate.'),
164: ('legitimate_clarification','genuinely_missing_reference_location','Explicitly absent location now requests landmark/locality; generic Bus Stop alias does not invent candidates.'),
165: ('recognition_failure','anchor_mode_target_relation_unrecognized','Single metro-station anchor plus bus target still becomes a competing-mode prompt. Anchor name/qualifier relation not retained.'),
166: ('recognition_failure','negated_target_mode_competes','Positive metro target and excluded bus still become competing modes; no wrong nearest fact executes, but requested scope is not retained.'),
178: ('recognition_failure','negated_prediction_guarded','Excluded route stops no longer execute a stop list. Explicit live-location goal remains unrecognized by classifier and asks intent again.'),
}}

def dump(path, value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
summary={};comparison=[]
for language,prefix in [('hindi','HI'),('hinglish','HG')]:
 base=json.loads((P/language/'baseline.json').read_text()); final=json.loads((P/language/'verified.json').read_text())
 original=json.loads((P/language/'assessment.json').read_text()); norm=[]
 for a in original:
  a=dict(a)
  if language=='hinglish' and a['id'] in {'HG200_182','HG200_183'}:
   a.update(category='safe_limitation',normalization_note='Correct out-of-scope rejection is not completed transport-goal fulfillment.')
  norm.append(a)
 dump(P/language/'normalized_baseline_assessment.json',norm)
 manual={f'{prefix}200_{n:03d}':review for n,review in REVIEWS[language].items()}
 changed={n['id'] for o,n in zip(base,final) if o['actual']!=n['actual']}
 assert changed==set(manual),(language,changed-set(manual),set(manual)-changed)
 reviewed=[]
 for old,new,a in zip(base,final,norm):
  assert old['id']==new['id']==a['id']
  if new['id'] in manual:
   cat,issue,note=manual[new['id']]
   record={'id':new['id'],'category':cat,'issue_type':issue,'notes':note,'review_method':'manual rereview of changed actual query/expectation/full response'}
  else: record={**a,'review_method':'independent baseline manual review reused because public response is byte-identical'}
  reviewed.append(record)
  comparison.append({'language':language,'id':new['id'],'query':new['query'],'response_changed':new['id'] in changed,'baseline_category':a['category'],'verified_category':record['category'],'issue_type':record['issue_type'],'notes':record['notes']})
 dump(P/language/'verified_assessment.json',reviewed)
 summary[language]={'total':200,'changed_responses':len(changed),'baseline_categories':dict(Counter(a['category'] for a in norm)),'verified_categories':dict(Counter(a['category'] for a in reviewed))}
dump(P/'semantic_counts.json',summary)
with (P/'semantic_comparison.csv').open('w',newline='',encoding='utf-8') as f:
 writer=csv.DictWriter(f,fieldnames=list(comparison[0]));writer.writeheader();writer.writerows(comparison)
print(json.dumps(summary,indent=2))
