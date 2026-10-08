"""Read opaque artifact hashes only; never load protected research examples."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[3];P=Path(__file__).parent

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
old=json.loads((ROOT/'reports/nlp_v2/final_review/final_source_context.json').read_text())
manifest_path=ROOT/'models/nlp_v2_t3_manifest.json';manifest=json.loads(manifest_path.read_text())
checkpoint=(manifest_path.parent/manifest['checkpoint_path']).resolve()
checks={
 'checkpoint':{'path':str(checkpoint.relative_to(ROOT)),'actual':sha(checkpoint),'expected':old['checkpoint_sha256']},
 'manifest':{'path':str(manifest_path.relative_to(ROOT)),'actual':sha(manifest_path),'expected':old['manifest_sha256']},
 'canonical_database':{'path':'data/canonical/transit/canonical_transport.db','actual':sha(ROOT/'data/canonical/transit/canonical_transport.db'),'expected':old['canonical_database_sha256']},
 'development_suite':{'path':'data/nlp_v2/development/assistant_coverage_v1.json','actual':sha(ROOT/'data/nlp_v2/development/assistant_coverage_v1.json'),'expected':old['development_suite_sha256']},
}
for measurement in old['preserved_historical_measurements']:
 for name,expected in measurement['report_and_context_hashes'].items():
  path=measurement['directory']+'/'+name
  checks[path]={'path':path,'actual':sha(ROOT/path),'expected':expected}
assert all(c['actual']==c['expected'] for c in checks.values())
for path in ('src/nlp_v2/model.py','src/nlp_v2/entities.py','src/nlp_v2/domain.py','src/nlp_v2/contracts.py','src/nlp_v2/dispatch.py','src/normalization.py'):
 assert sha(ROOT/path)==old['source_hashes'][path],path
checks['untouched_source_paths']={'count':6,'all_equal':True}
verified=json.loads((P/'verified_manifest.json').read_text())
assert all(sha(ROOT/name)==expected for name,expected in verified['source_sha256'].items())
context={'current_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'verified_api_source_commit':verified['git_head'],
 'verified_api_source_py_hashes_match_current':True,
 'frontend_assets':{path:sha(ROOT/path) for path in ('app/transit_theme.html','.streamlit/config.toml')},
 'preserved_artifacts':checks,'training_or_research_evaluator_run':False,
 'custom_queries_are_observed_development_qa_not_heldout_accuracy':True,
 'api_runtime_cpu_threads_environment':{'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2'},
 'independent_case_authors':['hindi_200_qa','hinglish_200_qa'],
 'review_status':'Root final source review; independent final reviewer exhausted usage allowance. No independent whole-project signoff claimed.'}
(P/'source_context.json').write_text(json.dumps(context,indent=2)+'\n')
print('Preserved checkpoint, DB, manifest, development suite and10 historical report/context hashes;6 untouched source modules verified.')
