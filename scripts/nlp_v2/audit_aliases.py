"""Read-only inventory of every canonical name and production alias."""
import json
import sqlite3
from collections import Counter
from pathlib import Path
from src.nlp_v2.entities import CanonicalResolver
from src.nlp_v2.model import sha256_file
from src.nlp_v2.text import normalize_extraction_text

def audit():
    resolver=CanonicalResolver()
    with sqlite3.connect(resolver.db_path.resolve().as_uri()+'?mode=ro',uri=True) as c:
        inventory={table:c.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ['transport_stops','transport_hubs','places','stop_names','place_names']}
        names=list(c.execute('SELECT stop_id,canonical_name FROM transport_stops'))+list(c.execute('SELECT hub_id,hub_name FROM transport_hubs'))+list(c.execute('SELECT place_id,canonical_name FROM places'))
        names+=list(c.execute('SELECT stop_id,name FROM stop_names'))+list(c.execute('SELECT place_id,name FROM place_names'))
    missing=[entity for entity,name in names if entity not in resolver.aliases.get(normalize_extraction_text(name),{})]
    counts=Counter('Devanagari' if any('\u0900'<=x<='\u097f' for x in key) else 'other' for key in resolver.aliases)
    invalid={key:ids for key,ids in resolver.aliases.items() if any(entity not in resolver.entity_details for entity in ids)}
    assert not missing and not invalid
    return {'canonical_database_sha256':sha256_file(resolver.db_path),'inventory':inventory,'canonical_and_existing_names_audited':len(names),'missing_or_unknown_ids':0,'alias_keys':len(resolver.aliases),'ambiguous_keys':sum(len(ids)>1 for ids in resolver.aliases.values()),'script_keys':dict(counts),'alias_catalog_sha256':sha256_file(Path('data/nlp_v2/reviewed_name_aliases_v1.json')),'policy':'Exact canonical/existing surfaces, reviewed transliteration, punctuation/NFC/spacing, mode qualification. Collisions accumulate IDs. No fuzzy match or cross-ID physical merge.'}
if __name__=='__main__':print(json.dumps(audit(),indent=2))
