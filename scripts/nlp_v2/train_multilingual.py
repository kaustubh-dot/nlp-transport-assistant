"""One raw-query MuRIL candidate warm-started from retained production weights.

Reads original TRAIN/disjoint validation and reviewed multilingual TRAIN/validation
only. No development-test semantic/evaluation use occurs; its bytes receive
manifest integrity hashing. Observed400/stress/human-reference are never read.
Selection uses two legitimate validation Macro-F1 values.
"""
from __future__ import annotations
import argparse
from collections import Counter
from importlib.metadata import version
import json
from pathlib import Path
import random
import time
import numpy as np
import torch
from torch.utils.data import DataLoader
from scripts.nlp_v2.multilingual_corpus import load_corpus
from scripts.nlp_v2.train_production_t3 import Rows, TRAIN_PATH, VALIDATION_PATH, TRAIN_SHA256, VALIDATION_SHA256, load_training_splits
from scripts.nlp_v2.evaluate_multilingual import classification_metrics
from src.nlp_v2.model import DEFAULT_MANIFEST, LABEL_ORDER, MODEL_NAME, MODEL_REVISION, T3IntentClassifier, sha256_file, load_manifest

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE_ROOT=ROOT/'experiments/nlp_v2/production_runs'
CONFIG={'seed':42,'max_epochs':8,'patience':3,'minimum_selection_delta':0.0005,'batch_size':16,'learning_rate':1e-5,'weight_decay':0.01,'max_length':64,'gradient_clip_norm':1.0}


def validate_candidate_output(path):
    path=Path(path).resolve()
    if not path.is_relative_to(CANDIDATE_ROOT) or path==CANDIDATE_ROOT:raise ValueError('Candidate must have its own production_runs directory')
    if path.exists() and any(path.iterdir()):raise ValueError('Candidate output must be empty')
    return path


def training_material():
    if sha256_file(TRAIN_PATH)!=TRAIN_SHA256 or sha256_file(VALIDATION_PATH)!=VALIDATION_SHA256:raise ValueError('Original split hash changed')
    original,oldval=load_training_splits(TRAIN_PATH,VALIDATION_PATH,exclude_overlaps=True)
    original=[dict(r,source='original_train') for r in original]
    new=[dict(r,T3_label=r['intent'],source='multilingual_train') for r in load_corpus('train') if r['classifier_applicable']]
    newval=[dict(r,T3_label=r['intent']) for r in load_corpus('validation') if r['classifier_applicable']]
    if {r['query'].strip().casefold() for r in original+new}&{r['query'].strip().casefold() for r in newval+oldval}:raise ValueError('Combined training exact query overlaps validation')
    assert {r['T3_label'] for r in original+new}==set(LABEL_ORDER)
    return original+new,oldval,newval


def promotion_decision(baseline,candidate):
    failures=[]
    if candidate['new']['macro_f1']<baseline['new']['macro_f1']+.10:failures.append('New validation Macro-F1 gain below0.10')
    if candidate['old']['macro_f1']<baseline['old']['macro_f1']-.01:failures.append('Original validation Macro-F1 drop exceeds0.01')
    english=baseline['old_languages'].get('EN')
    if english and round(candidate['old_languages']['EN']['accuracy']*english['count'])<round(english['accuracy']*english['count'])-1:failures.append('Original English lost more than one correct prediction')
    for group in ['old_languages','new_languages']:
        for language,metric in baseline[group].items():
            if candidate[group][language]['accuracy']<metric['accuracy']-.02:failures.append(group+':'+language+' accuracy drop exceeds0.02')
    for group in ['old_languages','new_languages']:
        for language,metric in baseline[group].items():
            field='macro_f1_supported_classes' if 'macro_f1_supported_classes' in metric else 'macro_f1'
            if candidate[group][language][field]<metric[field]-.02:
                failures.append(group+':'+language+' supported-class Macro-F1 drop exceeds0.02')
    for group,maximum_drop in [('old',.10),('new',.05)]:
        for label,metric in baseline[group]['per_class'].items():
            if metric['support'] and 'f1' in metric and candidate[group]['per_class'][label]['f1']<metric['f1']-maximum_drop:
                failures.append(group+':'+label+' per-class F1 regression')
    for label,metric in baseline['old']['per_class'].items():
        if not metric['support']:continue
        before=round(metric['recall']*metric['support']);after=round(candidate['old']['per_class'][label]['recall']*metric['support'])
        allowance=0 if metric['support']<10 else 1
        if after<before-allowance:failures.append('Original minority/per-class recall regression:'+label)
    return {'eligible':not failures,'failures':failures,'criteria':'Predeclared in L4 clean_diagnosis; selection/promotion uses validation only; reviewer required before production replacement'}


def _metrics(rows,predicted):
    adapted=[{'intent':r['T3_label'],'classifier_applicable':True} for r in rows]
    return classification_metrics(adapted,predicted)


def _predict(model,loader,device):
    predictions=[];model.eval()
    with torch.inference_mode():
        for batch in loader:
            batch.pop('labels')
            predictions.extend(LABEL_ORDER[i] for i in model(**{k:v.to(device) for k,v in batch.items()}).logits.argmax(-1).cpu().tolist())
    return predictions


def _validation_summary(old,new,oldpred,newpred):
    return {'old':_metrics(old,oldpred),'new':_metrics(new,newpred),
            'old_languages':{language:_metrics([r for r in old if r['language_class']==language],[p for r,p in zip(old,oldpred) if r['language_class']==language]) for language in sorted({r['language_class'] for r in old})},
            'new_languages':{language:_metrics([r for r in new if r['language_class']==language],[p for r,p in zip(new,newpred) if r['language_class']==language]) for language in sorted({r['language_class'] for r in new})}}


def train(output):
    output=validate_candidate_output(output)
    if not torch.cuda.is_available():raise RuntimeError('Focused full-model training requires host GPU; CPU fallback disabled')
    torch.empty(1,device='cuda');device=torch.device('cuda')
    random.seed(CONFIG['seed']);np.random.seed(CONFIG['seed']);torch.manual_seed(CONFIG['seed']);torch.cuda.manual_seed_all(CONFIG['seed'])
    torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    material,oldval,newval=training_material()
    classifier=T3IntentClassifier(DEFAULT_MANIFEST);model=classifier.model.to(device);tokenizer=classifier.tokenizer
    trainloader=DataLoader(Rows(material,tokenizer),batch_size=CONFIG['batch_size'],shuffle=True,generator=torch.Generator().manual_seed(CONFIG['seed']))
    oldloader=DataLoader(Rows(oldval,tokenizer),batch_size=CONFIG['batch_size']);newloader=DataLoader(Rows(newval,tokenizer),batch_size=CONFIG['batch_size'])
    baseline=_validation_summary(oldval,newval,_predict(model,oldloader,device),_predict(model,newloader,device))
    optimizer=torch.optim.AdamW(model.parameters(),lr=CONFIG['learning_rate'],weight_decay=CONFIG['weight_decay'])
    output.mkdir(parents=True,exist_ok=True);checkpoint=output/'t3_best.pt';best=-1;wait=0;history=[];started=time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    for epoch in range(1,CONFIG['max_epochs']+1):
        model.train();losses=[]
        for batch in trainloader:
            optimizer.zero_grad(set_to_none=True)
            result=model(**{k:v.to(device) for k,v in batch.items()});result.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),CONFIG['gradient_clip_norm']);optimizer.step();losses.append(float(result.loss.detach().cpu()))
        summary=_validation_summary(oldval,newval,_predict(model,oldloader,device),_predict(model,newloader,device))
        score=(summary['old']['macro_f1']+summary['new']['macro_f1'])/2
        row={'epoch':epoch,'loss':sum(losses)/len(losses),'selection_score':score,'metrics':summary,'elapsed_seconds':time.monotonic()-started};history.append(row)
        print(json.dumps({k:v for k,v in row.items() if k!='metrics'}),flush=True)
        if score>best+CONFIG['minimum_selection_delta']:
            best=score;best_epoch=epoch;best_summary=summary;wait=0;torch.save(model.state_dict(),checkpoint)
        else:
            wait+=1
            if wait>=CONFIG['patience']:break
    metadata={'taxonomy':'T3','model_name':MODEL_NAME,'model_revision':MODEL_REVISION,'label_order':list(LABEL_ORDER),'preprocessing':'raw_query','max_length':64,
              'checkpoint_path':'t3_best.pt','checkpoint_sha256':sha256_file(checkpoint),'warm_start_manifest_sha256':sha256_file(DEFAULT_MANIFEST),'warm_start_checkpoint_sha256':load_manifest(DEFAULT_MANIFEST)['checkpoint_sha256'],
              'configuration':CONFIG,'training_count':len(material),'training_sources':dict(Counter(r['source'] for r in material)),
              'original_train_sha256':TRAIN_SHA256,'original_validation_sha256':VALIDATION_SHA256,
              'reviewed_corpus_hashes':{name:sha256_file(ROOT/'data/nlp_v2/multilingual_v1'/name) for name in ['train.json','validation.json','manifest.json']},
              'original_validation_count':len(oldval),'new_validation_count':len(newval),'selection':'mean of original-disjoint and new-family-disjoint validation 16-label Macro-F1 only','best_epoch':best_epoch,
              'baseline_validation':baseline,'candidate_validation':best_summary,'promotion_decision':promotion_decision(baseline,best_summary),'history':history,
              'environment':{'device':torch.cuda.get_device_name(),'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'packages':{pkg:version(pkg) for pkg in ['torch','transformers','numpy','scikit-learn']}},'elapsed_seconds':time.monotonic()-started,
              'forbidden_inputs_read':False,'production_eligible':'Requires passing promotion criteria and fresh GPT-6.1 Sol xhigh review before replacement'}
    (output/'candidate_manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    return metadata

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=CANDIDATE_ROOT/'multilingual_v1');args=parser.parse_args();m=train(args.output);print(json.dumps({'best_epoch':m['best_epoch'],'promotion':m['promotion_decision']}))
