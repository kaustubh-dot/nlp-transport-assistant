"""Reuse the repository's canonical names without expanding the intent model."""
from __future__ import annotations

from functools import lru_cache
import json
import re
import sqlite3

from src.nlp_v2.entities import CanonicalResolver, Resolution
from src.nlp_v2.text import normalize_extraction_text
from src.nlp_v2.domain import _haversine_m


# Surface spellings for existing records, not additional stations or routes.
# A bare Park station remains ambiguous between Park and Park Town.
PROJECT_ALIASES = {
    'RAIL_MAMBALAM': ('माम्बलम', 'मंबलम', 'माम्बलम्', 'मांबलम'),
    'MRTS_VELACHERY': ('वेलाचेरी एमआरटीएस स्टेशन', 'वेलाचरी एमआरटीएस स्टेशन'),
    'RAIL_CHENNAI_PARK': ('park', 'park station', 'पार्क', 'पार्क स्टेशन',
                          'chennai park station', 'चेन्नई पार्क', 'चेन्नई पार्क रेलवे स्टेशन'),
    'RAIL_CHENNAI_PARK_TOWN': ('park', 'park station', 'पार्क', 'पार्क स्टेशन',
                               'park town', 'park town station', 'पार्क टाउन'),
}


class ProjectLocationIndex:
    def __init__(self, catalog: dict):
        self.resolver = CanonicalResolver()
        candidates = {candidate.entity_id: candidate for entries in self.resolver.aliases.values()
                      for candidate in entries.values()}
        self.coordinate_conflicts = {}
        groups = {}
        with sqlite3.connect(self.resolver.db_path.as_uri() + '?mode=ro', uri=True) as conn:
            self.primary_sources = dict(conn.execute('SELECT stop_id,primary_source_id FROM transport_stops'))
            for key, name, latitude, longitude, source in conn.execute(
                    "SELECT stop_id,canonical_name,latitude,longitude,primary_source_id FROM transport_stops WHERE mode='metro' AND latitude IS NOT NULL AND longitude IS NOT NULL"):
                base = re.sub(r'\s+(?:metro station|metro)$', '', normalize_extraction_text(name))
                groups.setdefault(base, []).append((key, latitude, longitude, source))
        for rows in groups.values():
            # Only flag cross-source disagreement for the same station name.
            # Do not merge IDs or choose a source's coordinates silently.
            if not any(row[3] == 'CMRL_API' for row in rows):
                continue
            if any(a[3] != b[3] and _haversine_m(a[1], a[2], b[1], b[2]) > 300
                   for a in rows for b in rows):
                conflict = tuple(candidates[row[0]] for row in rows if row[0] in candidates)
                for key, *_ in rows:
                    self.coordinate_conflicts[key] = conflict
        self.local_aliases = {}
        self.places = {}
        for key, row in self.resolver.entity_details.items():
            self.places[key] = {'id': key, 'name_en': row['canonical_name'],
                                'name_hi': row['canonical_name'], **row}
        for row in catalog['locations']:
            self.places[row['id']] = row
            local_candidates = [candidates[key] for key in (row.get('rail_id'), row.get('metro_id'), row.get('nearby_bus_id'))
                                if key in candidates]
            for alias in row['aliases']:
                self.local_aliases[normalize_extraction_text(alias)] = row['id']
                for candidate in local_candidates:
                    self.resolver._add(alias, candidate)
        for key, aliases in PROJECT_ALIASES.items():
            if key not in candidates:
                continue
            candidate = candidates[key]
            for alias in aliases:
                self.resolver._add(alias, candidate)
                for suffix in ('railway station', 'रेलवे स्टेशन'):
                    if candidate.mode == 'suburban_rail':
                        self.resolver._add(alias + ' ' + suffix, candidate)
        self.resolver.max_alias_tokens = max(len(alias.split()) for alias in self.resolver.aliases)

    def local_id(self, surface: str) -> str | None:
        for alias in sorted(self.local_aliases, key=len, reverse=True):
            if surface == alias or (surface.startswith(alias + ' ') and re.fullmatch(
                    r'(?:(?:metro|railway|suburban railway|मेट्रो|रेलवे)\s*)?(?:station|स्टेशन)|metro|मेट्रो',
                    surface[len(alias):].strip())):
                return self.local_aliases[alias]
        return None

    def mentions(self, query: str) -> list[dict]:
        result = []
        for span in self.resolver.find_spans(query):
            # Generic source names (e.g. a stop literally called Bus Stop) are
            # not an explicit location in a passenger's question.
            if span.surface in {'bus stop', 'bus station', 'bus stand', 'railway station', 'metro station',
                                'बस स्टॉप', 'बस स्टेशन', 'बस अड्डा', 'रेलवे स्टेशन', 'मेट्रो स्टेशन'}:
                continue
            resolution = self.resolver.resolve(span, 'origin', 'point_to_point_route')
            value = self.local_id(span.surface) or resolution.entity_id or span.surface
            result.append({'value': value, 'span': span})
        return result

    def nearby_anchor(self, span, query: str) -> Resolution:
        """Bus is the search target, never the station's required mode."""
        if span.requires_qualification:
            return Resolution(None, span.candidates, True)
        text = normalize_extraction_text(query)
        suffix = re.match(r'\s*(?:(?:metro|railway|mrts|मेट्रो|रेलवे|एमआरटीएस)\s*)?(?:station|स्टेशन)(?!\w)', text[span.end:])
        reference = span.surface + (suffix.group() if suffix else '')
        candidates = list(span.candidates)
        if re.search(r'(?<!\w)(?:metro|मेट्रो)(?!\w)', reference):
            candidates = [row for row in candidates if row.mode == 'metro']
        elif re.search(r'(?<!\w)(?:mrts|एमआरटीएस)(?!\w)', reference):
            candidates = [row for row in candidates if row.mode == 'mrts']
        elif re.search(r'(?<!\w)(?:railway|रेलवे)(?!\w)', reference):
            candidates = [row for row in candidates if row.mode in {'suburban_rail', 'mrts'}]
        elif re.search(r'(?<!\w)(?:station|स्टेशन)(?!\w)', reference):
            # An unqualified station with one rail/Metro record (Velachery)
            # is clear even when multiple nearby bus stops share its name.
            candidates = [row for row in candidates if row.kind == 'stop' and row.mode != 'bus']
        else:
            places = [row for row in candidates if row.kind == 'place']
            candidates = places or candidates
        unique = tuple(sorted(candidates, key=lambda row: row.entity_id))
        if unique and all(row.mode == 'metro' for row in unique) and any(row.entity_id in self.coordinate_conflicts for row in unique):
            conflict = {row.entity_id: row for candidate in unique for row in
                        self.coordinate_conflicts.get(candidate.entity_id, (candidate,))}
            return Resolution(None, tuple(conflict.values()), True)
        if len(unique) > 1 and all(row.mode == 'metro' for row in unique):
            official = [row for row in unique if self.primary_sources.get(row.entity_id) == 'CMRL_API']
            if len(official) == 1:
                return Resolution(official[0].entity_id, unique, False)
        return Resolution(unique[0].entity_id if len(unique) == 1 else None, unique, len(unique) > 1)

    def describe(self, mentions: list[dict], slots: dict, query: str = '') -> tuple[list[dict], dict, list[dict]]:
        mode = slots.get('transport_mode')
        mode = {'rail': 'suburban_rail'}.get(mode, mode) if isinstance(mode, str) else None
        canonical, ambiguous, matches = {}, [], []
        for mention in mentions:
            span, value = mention['span'], mention['value']
            roles = [role for role in ('origin', 'destination', 'station') if slots.get(role) == value]
            candidates = self.resolver.describe_candidates(c.entity_id for c in span.candidates)
            matches.append({'surface': span.surface, 'value': value, 'candidates': candidates})
            for role in roles:
                resolution = (self.nearby_anchor(span, query) if slots.get('station_detail') in {'nearby_bus', 'nearby_transport'}
                              else self.resolver.resolve(span, role, 'point_to_point_route', mode=mode))
                if resolution.entity_id:
                    canonical[role] = resolution.entity_id
                elif resolution.ambiguous:
                    ambiguous.append({'role': role, 'surface': span.surface,
                                      'reason': 'coordinate_conflict' if slots.get('station_detail') in {'nearby_bus', 'nearby_transport'}
                                      and all(row.mode == 'metro' for row in resolution.candidates)
                                      and any(row.entity_id in self.coordinate_conflicts for row in resolution.candidates) else 'name_ambiguity',
                                      'candidates': self.resolver.describe_candidates(c.entity_id for c in resolution.candidates)})
        return matches, canonical, ambiguous


@lru_cache(maxsize=4)
def location_index(catalog_json: str) -> ProjectLocationIndex:
    return ProjectLocationIndex(json.loads(catalog_json))


def index_for(catalog: dict) -> ProjectLocationIndex:
    return location_index(json.dumps(catalog, sort_keys=True, ensure_ascii=False))
