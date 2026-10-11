"""Read-only canonical name index and ambiguity-preserving entity resolution."""

from dataclasses import dataclass
from pathlib import Path
import re
import json
import sqlite3

from .text import normalize_extraction_text as normalize_text
from src.entity_extractor import DEFAULT_GAZETTEER


DEFAULT_DB = Path(__file__).resolve().parents[2] / "data/canonical/transit/canonical_transport.db"
EXTRA_ROMAN_ALIASES = {"gindi": "Guindy", "guindi": "Guindy", "gindy": "Guindy"}
# Independently authored development/synthetic name translations, resolved
# through current canonical names; duplicate physical IDs remain separate.
EXACT_NAME_ALIASES = {
    'Alwar Thirunagar': ('अलवर तिरुनगर',),
    'Poonamallee Bus Terminus': ('पूनमल्ली बस टर्मिनस', 'पूनमल्ली bus terminus'),
    'Marina Beach': ('मरीना बीच', 'मरीना beach', 'marina बीच'),
}


def _route_key(value: str) -> str:
    return value.upper().replace(" ", "").replace("-", "")


@dataclass(frozen=True)
class EntityCandidate:
    entity_id: str
    kind: str
    mode: str | None = None


@dataclass(frozen=True)
class EntitySpan:
    surface: str
    start: int
    end: int
    candidates: tuple[EntityCandidate, ...]
    requires_qualification: bool = False


@dataclass(frozen=True)
class Resolution:
    entity_id: str | None
    candidates: tuple[EntityCandidate, ...]
    ambiguous: bool


class CanonicalResolver:
    """Resolve explicit names to current canonical KB IDs without fuzzy guesses."""

    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.aliases: dict[str, dict[str, EntityCandidate]] = {}
        self.incomplete_names: dict[str, dict[str, EntityCandidate]] = {}
        self.route_stops: dict[str, set[str]] = {}
        self.entity_details: dict[str, dict] = {}
        self._load()
        self.max_alias_tokens = max((len(alias.split()) for alias in self.aliases.keys() | self.incomplete_names.keys()), default=1)

    def _add(self, name: str, candidate: EntityCandidate) -> None:
        key = normalize_text(name)
        if key:
            self.aliases.setdefault(key, {})[candidate.entity_id] = candidate

    def _load(self) -> None:
        if not self.db_path.is_file():
            raise FileNotFoundError(f"Canonical transport database not found: {self.db_path}")
        with sqlite3.connect(self.db_path.resolve().as_uri() + "?mode=ro", uri=True) as conn:
            stops = {row[0]: EntityCandidate(row[0], "stop", row[2])
                     for row in conn.execute("SELECT stop_id, canonical_name, mode FROM transport_stops")}
            hubs = {row[0]: EntityCandidate(row[0], "hub")
                    for row in conn.execute("SELECT hub_id, hub_name FROM transport_hubs")}
            places = {row[0]: EntityCandidate(row[0], "place")
                      for row in conn.execute("SELECT place_id, canonical_name FROM places")}
            for stop_id, name, _ in conn.execute("SELECT stop_id, canonical_name, mode FROM transport_stops"):
                self._add(name, stops[stop_id])
                self.entity_details[stop_id] = dict(entity_id=stop_id, canonical_name=name, kind="stop", mode=stops[stop_id].mode)
            for hub_id, name in conn.execute("SELECT hub_id, hub_name FROM transport_hubs"):
                self._add(name, hubs[hub_id])
                self.entity_details[hub_id] = dict(entity_id=hub_id, canonical_name=name, kind="hub", mode=None)
                if normalize_text(name).endswith(" central"):
                    for alias in ("central", "chennai central", "सेंट्रल", "चेन्नई सेंट्रल"):
                        self._add(alias, hubs[hub_id])
            for place_id, name in conn.execute("SELECT place_id, canonical_name FROM places"):
                self._add(name, places[place_id])
                self.entity_details[place_id] = dict(entity_id=place_id, canonical_name=name, kind="place", mode=None)
                if "," in name:
                    base,qualifier=name.split(",",1)
                    if normalize_text(qualifier) in {'chennai','chennai city'}:
                        self._add(base, places[place_id])
                    elif normalize_text(qualifier):
                        self.incomplete_names.setdefault(normalize_text(base),{})[place_id]=places[place_id]
            for stop_id, name in conn.execute("SELECT stop_id, name FROM stop_names"):
                if stop_id in stops:
                    self._add(name, stops[stop_id])
            for place_id, name in conn.execute("SELECT place_id, name FROM place_names"):
                if place_id in places:
                    self._add(name, places[place_id])

            route_ids: dict[str, set[str]] = {}
            for route_id, short_name in conn.execute("SELECT route_id, route_short_name FROM transport_routes WHERE status = 'operational'"):
                if short_name:
                    route_ids.setdefault(_route_key(short_name), set()).add(route_id)
            stops_by_route: dict[str, set[str]] = {}
            for route_id, stop_id in conn.execute("""
                SELECT rs.route_id, rs.canonical_stop_id FROM route_stops rs
                JOIN transport_routes r ON r.route_id = rs.route_id AND r.status = 'operational'
                JOIN transport_stops s ON s.stop_id = rs.canonical_stop_id AND s.mode = r.mode
            """):
                stops_by_route.setdefault(route_id, set()).add(stop_id)
            self.route_stops = {code: set().union(*(stops_by_route.get(route_id, set()) for route_id in ids))
                                for code, ids in route_ids.items()}

        # Reuse only the legacy gazetteer's surface aliases; resolve against
        # today's canonical names, never its legacy IDs.
        for entry in DEFAULT_GAZETTEER.values():
            target = normalize_text(entry["canonical_name_en"])
            candidates = self.aliases.get(target, {})
            for alias in entry["aliases"]:
                for candidate in tuple(candidates.values()):
                    if re.search(r"(?:metro|मेट्रो)$", normalize_text(alias)) and candidate.mode != "metro":
                        continue
                    self._add(alias, candidate)
        for alias, current_name in EXTRA_ROMAN_ALIASES.items():
            for candidate in self.aliases.get(normalize_text(current_name), {}).values():
                self._add(alias, candidate)
        for current_name, aliases in EXACT_NAME_ALIASES.items():
            candidates = tuple(self.aliases.get(normalize_text(current_name), {}).values())
            for alias in aliases:
                for candidate in candidates:
                    self._add(alias, candidate)

        catalog = json.loads((Path(__file__).resolve().parents[2] / "data/nlp_v2/reviewed_name_aliases_v1.json").read_text())
        for entry in catalog['entries']:
            candidates = tuple(self.aliases.get(normalize_text(entry['canonical_name']), {}).values())
            for alias in entry['aliases']:
                for candidate in candidates:
                    self._add(alias, candidate)
        # Deterministic spacing variants preserve the complete collision set.
        for name, candidates in tuple(self.aliases.items()):
            if len(name.split()) > 1:
                for candidate in tuple(candidates.values()):
                    self._add(name.replace(' ', ''), candidate)
        qualifiers = {
            'metro': ('metro station', 'मेट्रो स्टेशन'),
            'bus': ('bus stop', 'बस स्टॉप'),
            'suburban_rail': ('suburban railway station', 'railway station', 'उपनगरीय रेल स्टेशन', 'रेलवे स्टेशन'),
            'mrts': ('mrts station', 'एमआरटीएस स्टेशन'),
        }
        for name, candidates in tuple(self.aliases.items()):
            for candidate in tuple(candidates.values()):
                if candidate.kind == 'stop':
                    for qualifier in qualifiers.get(candidate.mode, ()):
                        self._add(name + ' ' + qualifier, candidate)
        # Qualifiers can collide with an existing canonical name. Reconcile
        # the complete final set across every whitespace-equivalent surface.
        spacing_groups: dict[str, dict[str, EntityCandidate]] = {}
        for name, candidates in self.aliases.items():
            spacing_groups.setdefault(name.replace(' ', ''), {}).update(candidates)
        for name in tuple(self.aliases):
            self.aliases[name] = spacing_groups[name.replace(' ', '')]
        for compact, candidates in spacing_groups.items():
            self.aliases[compact] = candidates
        incomplete_groups: dict[str, dict[str, EntityCandidate]] = {}
        for name, candidates in self.incomplete_names.items():
            incomplete_groups.setdefault(name.replace(' ', ''), {}).update(candidates)
        for name in self.aliases.keys() | self.incomplete_names.keys():
            compact = name.replace(' ', '')
            if compact in incomplete_groups:
                self.incomplete_names[name] = incomplete_groups[compact]
        self.incomplete_names.update(incomplete_groups)

    def describe_candidates(self, entity_ids) -> list[dict]:
        """Expose only actual loaded canonical names, with IDs for disambiguation."""
        return [dict(self.entity_details[key]) for key in sorted(set(entity_ids)) if key in self.entity_details]

    def find_spans(self, text: str) -> tuple[EntitySpan, ...]:
        """Find longest non-overlapping exact names in normalized input."""
        normalized = normalize_text(text)
        tokens = list(re.finditer(r"\S+", normalized))
        spans: list[EntitySpan] = []
        i = 0
        while i < len(tokens):
            match = None
            for end_i in range(min(len(tokens), i + self.max_alias_tokens), i, -1):
                start, end = tokens[i].start(), tokens[end_i - 1].end()
                surface = normalized[start:end]
                if surface in self.aliases or surface in self.incomplete_names:
                    partial=surface in self.incomplete_names
                    entries=dict(self.aliases.get(surface, {}))
                    entries.update(self.incomplete_names.get(surface, {}))
                    candidates = tuple(sorted(entries.values(), key=lambda c: c.entity_id))
                    match = (end_i, EntitySpan(surface, start, end, candidates, partial))
                    break
            if match:
                i, span = match
                spans.append(span)
            else:
                i += 1
        return tuple(spans)

    def resolve(self, span: EntitySpan, role: str, intent: str, mode: str | None = None,
                route_number: str | None = None) -> Resolution:
        """Apply role, explicit mode, and route context to exact candidates."""
        candidates = list(span.candidates)
        if span.requires_qualification:
            return Resolution(None, tuple(candidates), True)
        if role in {"landmark", "locality"}:
            places = [candidate for candidate in candidates if candidate.kind == "place"]
            candidates = places or [candidate for candidate in candidates if candidate.kind in {'stop', 'hub'}]
        elif role in {"station", "stop"}:
            candidates = [candidate for candidate in candidates if candidate.kind == "stop"]
        elif role in {"origin", "destination", "via"}:
            candidates = [candidate for candidate in candidates if candidate.kind in {"hub", "stop", "place"}]

        if mode and mode != "any" and role not in {"landmark", "locality"}:
            mode_stops = [candidate for candidate in candidates if candidate.kind == "stop" and candidate.mode == mode]
            # Preserve explicit known entities when their mode is incompatible;
            # downstream services must reject them rather than lose the constraint.
            candidates = mode_stops or [candidate for candidate in candidates if candidate.kind == "place"] or candidates
        elif role in {"origin", "destination", "via"} and intent in {"point_to_point_route", "multimodal_route", "mode_availability"}:
            hubs = [candidate for candidate in candidates if candidate.kind == "hub"]
            if hubs:
                candidates = hubs

        if role in {"stop", "station"} and route_number:
            on_route = self.route_stops.get(_route_key(route_number), set())
            on_route_candidates = [candidate for candidate in candidates if candidate.entity_id in on_route]
            if on_route_candidates:
                candidates = on_route_candidates

        unique = tuple(sorted(candidates, key=lambda candidate: candidate.entity_id))
        if intent == 'nearest_transport' and role in {'landmark','locality'} and len(unique)==1 and unique[0].kind=='stop':
            physical_reference = bool(re.search(r'(?<!\w)(?:station|stop|terminus|terminal|depot|metro|railway|mrts|स्टेशन|स्टॉप|मेट्रो|एमआरटीएस)(?!\w)',span.surface))
            if not physical_reference:
                return Resolution(None, unique, True)
        return Resolution(unique[0].entity_id if len(unique) == 1 else None, unique, len(unique) > 1)
