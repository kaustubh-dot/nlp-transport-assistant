"""Clean multilingual layer metrics. Never reads observed400 or stress/reference."""
from __future__ import annotations
from collections import Counter
from dataclasses import asdict
import argparse
import json
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from scripts.nlp_v2.multilingual_corpus import load_corpus
from scripts.nlp_v2.train_production_t3 import TRAIN_PATH, VALIDATION_PATH, TRAIN_SHA256, VALIDATION_SHA256, load_training_splits
from src.nlp_v2.assistant import T3Assistant
from src.nlp_v2.contracts import IntentPrediction
from src.nlp_v2.entities import CanonicalResolver
from src.nlp_v2.model import DEFAULT_MANIFEST, LABEL_ORDER, T3IntentClassifier, load_manifest, sha256_file
from src.nlp_v2.slots import T3SlotExtractor


def classification_metrics(rows, predicted):
    if len(rows)!=len(predicted):raise ValueError('Misaligned classifier records')
    pairs=[(r['intent'],p) for r,p in zip(rows,predicted) if r['classifier_applicable']]
    if not pairs:return {'count':0,'accuracy':None,'macro_f1':None,'per_class':{}}
    gold,pred=map(list,zip(*pairs))
    if any(x not in LABEL_ORDER for x in gold+pred):raise ValueError('Invalid classifier label')
    precision,recall,f1,support=precision_recall_fscore_support(gold,pred,labels=list(LABEL_ORDER),zero_division=0)
    return {'count':len(gold),'accuracy':float(accuracy_score(gold,pred)),'macro_f1':float(sum(f1)/len(LABEL_ORDER)),
            'macro_f1_supported_classes':float(sum(f1[i] for i,count in enumerate(support) if count)/sum(count>0 for count in support)),
            'per_class':{label:{'support':int(support[i]),'precision':float(precision[i]),'recall':float(recall[i]),'f1':float(f1[i])} for i,label in enumerate(LABEL_ORDER)},
            'confusion_matrix':confusion_matrix(gold,pred,labels=list(LABEL_ORDER)).tolist()}


def _equal(a,b,*,unordered=False):
    return sorted(a)==sorted(b) if unordered and isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)) else a==b


def score_extraction(row,extraction):
    """Gold comes from independently authored data, never production output."""
    gold=row['slots'];actual=extraction.slots
    slots=sum(_equal(actual.get(key),value,unordered=key=='time') for key,value in gold.items())
    entity_gold=row['entity_expectations']
    entity_correct=0
    for role,expectation in entity_gold.items():
        ids=set(expectation['canonical_ids'])
        if len(ids)==1:
            entity_correct+=actual.get(role) in ids
        else:
            entity_correct+=role not in actual and any(set(c.entity_id for c in unresolved.candidates)==ids for unresolved in extraction.unresolved)
    constraints={k:v for k,v in row.get('request_constraints',{}).items() if k not in {'tags'}}
    preserved=dict(getattr(extraction,'request_constraints',{}))
    preserved.update({k:actual.get(k) for k in ('date','time','temporal_relative') if k in actual})
    preserved['clock']=actual.get('time');preserved['relative_day']=actual.get('temporal_relative')
    preserved['required_modes']=list(extraction.requested_modes)
    preserved['excluded_modes']=list(getattr(extraction,'excluded_modes',()))
    correct=sum(_equal(preserved.get(k),v,unordered=k in {'required_modes','excluded_modes','route_numbers','clock'}) for k,v in constraints.items())
    return {'slot_correct':slots,'slot_total':len(gold),'slot_exact':int(slots==len(gold) and set(actual)<=set(gold)),
            'unexpected_slot_values':sum(k not in gold for k in actual),
            'entity_correct':entity_correct,'entity_total':len(entity_gold),'entity_exact':int(entity_correct==len(entity_gold)),
            'constraint_correct':correct,'constraint_total':len(constraints),'constraint_exact':int(correct==len(constraints))}


def predict_labels(classifier,queries,batch_size=16):
    import torch
    result=[]
    for start in range(0,len(queries),batch_size):
        raw=queries[start:start+batch_size]
        encoded=classifier.tokenizer(raw,truncation=True,max_length=64,padding='max_length',return_tensors='pt')
        with torch.inference_mode():indices=classifier.model(**encoded).logits.argmax(-1).tolist()
        result.extend(LABEL_ORDER[i] for i in indices)
    return result


class FixedClassifier:
    def __init__(self,label):self.label=label
    def predict(self,query):return IntentPrediction(self.label,(self.label,),1.0)


def clarification_metrics(records):
    assessed=correct=masked=0
    preflight_reasons={'ticket_policy_absent','facility_verification_absent','confirmed_multimodal_graph_absent',
                       'confirmed_interchanges_absent','accessibility_values_absent',
                       'published_mode_topology_absent','published_mode_schedule_absent'}
    for record in records:
        reply=record['injected'] or record['actual']
        expected=record['expected_clarification']
        if not expected and reply['status']!='clarification':continue
        is_mask=(record['injected'] is not None and expected in {'missing_slot','entity_ambiguity','temporal_ambiguity'}
                 and reply['status']=='unavailable' and reply.get('data',{}).get('reason') in preflight_reasons)
        if is_mask:
            masked+=1
        else:
            assessed+=1
            correct+=reply['status']=='clarification' and reply['clarification_reason']==expected
    return {'assessed':assessed,'matches_authored_state':correct,'source_preflight_masked':masked,
            'definition':'Includes null-intent cases using actual reply; intent-injected reply otherwise. Only documented source preflight reasons mask unresolved execution/temporal/entity inputs; ok/error/unrelated refusal is a failure.'}


def evaluate_partition(rows,predicted,resolver):
    extractor=T3SlotExtractor(resolver)
    records=[]
    for row,label in zip(rows,predicted):
        actual=T3Assistant(classifier=FixedClassifier(label),resolver=resolver,extractor=extractor).process_query(row['query'])
        extraction=extractor.extract(row['query'],row['intent']) if row['intent'] else None
        score=score_extraction(row,extraction) if extraction else None
        injected=(T3Assistant(classifier=FixedClassifier(row['intent']),resolver=resolver,extractor=extractor).process_query(row['query']) if row['intent'] else None)
        records.append({'id':row['id'],'language_class':row['language_class'],'gold_intent':row['intent'],'predicted':label,'classifier_applicable':row['classifier_applicable'],'score':score,'actual':asdict(actual),'injected':asdict(injected) if injected else None,'extraction':asdict(extraction) if extraction else None,'expected_clarification':row['expected_clarification']})
    def aggregate(indices):
        subset=[records[i] for i in indices];typed=[r for r in subset if r['score']]
        totals=Counter()
        for r in typed:totals.update(r['score'])
        rates={}
        for field in ('slot','entity','constraint'):
            correct,count=totals[field+'_correct'],totals[field+'_total']
            rates[field]={'correct':correct,'count':count,'rate':correct/count if count else None,'exact_rows':totals[field+'_exact'],'rows':len(typed)}
        eligible=[r for r in typed if r['actual']['status']=='ok']
        bounded=sum(r['predicted']==r['gold_intent'] and all(r['score'][k]==1 for k in ('slot_exact','entity_exact','constraint_exact')) for r in eligible)
        return {'count':len(subset),'classifier':classification_metrics([rows[i] for i in indices],[predicted[i] for i in indices]),'intent_injected_extraction':rates,
                'clarification':clarification_metrics(subset),
                'response_status':dict(Counter(r['actual']['status'] for r in subset)),
                'operation_success':{'completed_bounded_goal_conservative':bounded,'ok_replies':len(eligible),'definition':'ok plus correct intended operation and all authored slots/entities/constraints; does not independently validate transit facts'},
                'classifier_vs_injected_extraction_partition':dict(Counter(('classifier_and_downstream' if r['predicted']!=r['gold_intent'] else 'downstream_only') if not all(r['score'][k] for k in ('slot_exact','entity_exact','constraint_exact')) else ('classifier_only' if r['predicted']!=r['gold_intent'] else 'both_correct') for r in typed if r['classifier_applicable']))}
    return {'overall':aggregate(list(range(len(rows)))),'by_language':{language:aggregate([i for i,r in enumerate(rows) if r['language_class']==language]) for language in sorted({r['language_class'] for r in rows})}},records


def evaluate(manifest_path=DEFAULT_MANIFEST):
    classifier=T3IntentClassifier(manifest_path);resolver=CanonicalResolver()
    report={'model_manifest_sha256':sha256_file(Path(manifest_path)),'checkpoint_sha256':load_manifest(manifest_path)['checkpoint_sha256'],
            'evaluation_type':'clean_multilingual_validation_and_development_test_diagnosis','selection_policy':'development_test diagnostic only; candidate selection may read validation only','new_corpus_manifest_sha256':sha256_file(Path('data/nlp_v2/multilingual_v1/manifest.json'))}
    all_records={}
    for partition in ('validation','development_test'):
        rows=load_corpus(partition)
        labels=predict_labels(classifier,[r['query'] for r in rows])
        report[partition],all_records[partition]=evaluate_partition(rows,labels,resolver)
    if sha256_file(TRAIN_PATH)!=TRAIN_SHA256 or sha256_file(VALIDATION_PATH)!=VALIDATION_SHA256:raise ValueError('Historical TRAIN/validation hash mismatch')
    train,validation=load_training_splits(TRAIN_PATH,VALIDATION_PATH,exclude_overlaps=True)
    rows=[{'intent':r['T3_label'],'classifier_applicable':True,'language_class':r['language_class']} for r in validation]
    labels=predict_labels(classifier,[r['query'] for r in validation])
    report['legitimate_disjoint_validation']={'count':len(rows),'original_train_count':len(train),'classifier':classification_metrics(rows,labels),'by_language':{language:classification_metrics([r for r in rows if r['language_class']==language],[p for r,p in zip(rows,labels) if r['language_class']==language]) for language in sorted({r['language_class'] for r in rows})}}
    report['limitations']=['New corpus is internally family-disjoint and reviewed; underlying T3 meanings may exist in original legitimate TRAIN.','Extraction measured directly with injected intended intent to avoid unavailable preflight masking.','No observed400 or historical stress/reference content was read.','Slot metrics are authored gold recall; unexpected extra slots reported separately, not claimed harmless.','Small held-out per-language/class supports create large uncertainty; neither dataset is an untouched external acceptance test.']
    return report,all_records

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--details',type=Path,required=True);args=parser.parse_args()
    report,records=evaluate(args.manifest);args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');args.details.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print(json.dumps({key:report[key]['overall']['classifier'] for key in ('validation','development_test')},indent=2))
