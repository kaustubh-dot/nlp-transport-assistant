"""Read-only canonical name index and ambiguity-preserving entity resolution."""

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from src.normalization import normalize_text
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
        self.route_stops: dict[str, set[str]] = {}
        self._load()
        self.max_alias_tokens = max((len(alias.split()) for alias in self.aliases), default=1)

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
            for hub_id, name in conn.execute("SELECT hub_id, hub_name FROM transport_hubs"):
                self._add(name, hubs[hub_id])
                if normalize_text(name).endswith(" central"):
                    for alias in ("central", "chennai central", "सेंट्रल", "चेन्नई सेंट्रल"):
                        self._add(alias, hubs[hub_id])
            for place_id, name in conn.execute("SELECT place_id, canonical_name FROM places"):
                self._add(name, places[place_id])
                if "," in name:
                    self._add(name.split(",", 1)[0], places[place_id])
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
                for candidate in candidates.values():
                    self._add(alias, candidate)
        for alias, current_name in EXTRA_ROMAN_ALIASES.items():
            for candidate in self.aliases.get(normalize_text(current_name), {}).values():
                self._add(alias, candidate)
        for current_name, aliases in EXACT_NAME_ALIASES.items():
            candidates = tuple(self.aliases.get(normalize_text(current_name), {}).values())
            for alias in aliases:
                for candidate in candidates:
                    self._add(alias, candidate)

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
                if surface in self.aliases:
                    candidates = tuple(sorted(self.aliases[surface].values(), key=lambda c: c.entity_id))
                    match = (end_i, EntitySpan(surface, start, end, candidates))
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
        return Resolution(unique[0].entity_id if len(unique) == 1 else None, unique, len(unique) > 1)
