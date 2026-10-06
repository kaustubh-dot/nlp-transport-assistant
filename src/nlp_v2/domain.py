"""Read-only, provenance-aware operations over the canonical transit snapshot."""

from __future__ import annotations

from datetime import date
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
import sqlite3
from statistics import median
from typing import Any, Mapping

from .dispatch import OPERATIONS, ServiceResult


DEFAULT_DB = Path(__file__).resolve().parents[2] / "data/canonical/transit/canonical_transport.db"


def _unavailable(message: str, data: dict | None = None) -> ServiceResult:
    return ServiceResult("unavailable", data or {}, message)


def _ok(message: str, data: dict) -> ServiceResult:
    return ServiceResult("ok", data, message)


def _haversine_m(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    radius_m = 6_371_000
    dlat, dlon = radians(b_lat - a_lat), radians(b_lon - a_lon)
    value = sin(dlat / 2) ** 2 + cos(radians(a_lat)) * cos(radians(b_lat)) * sin(dlon / 2) ** 2
    return 2 * radius_m * asin(sqrt(value))


class CanonicalTransitService:
    """Execute every T3 operation without mutating or embellishing source data."""

    handlers = {
        "PLAN_ROUTE": "_plan_route",
        "PLAN_MULTIMODAL_ROUTE": "_multimodal_route",
        "LIST_ROUTE_STOPS": "_list_route_stops",
        "CHECK_STOP_ON_ROUTE": "_check_stop_on_route",
        "GET_FIRST_LAST_SERVICE": "_first_last",
        "GET_SERVICE_FREQUENCY": "_frequency",
        "GET_SCHEDULED_DEPARTURES": "_departures",
        "CHECK_SERVICE_AVAILABILITY": "_availability",
        "CALCULATE_FARE": "_fare",
        "GET_TICKETING_POLICY": "_ticketing",
        "GET_STATION_FACILITY": "_facility",
        "GET_ACCESSIBILITY_INFO": "_accessibility",
        "GET_INTERCHANGE_DETAILS": "_interchange",
        "FIND_NEAREST_STATION": "_nearest",
        "REJECT_UNSUPPORTED_REALTIME": "_realtime",
        "REJECT_OUT_OF_SCOPE": "_out_of_scope",
    }

    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path).resolve()
        if not self.db_path.is_file():
            raise FileNotFoundError(f"Canonical transit database missing: {self.db_path}")
        if set(self.handlers) != set(OPERATIONS.values()):
            raise RuntimeError("T3 operation coverage is incomplete")

    def execute(self, operation: str, slots: Mapping[str, Any]) -> ServiceResult:
        if operation not in self.handlers:
            return ServiceResult("error", {}, "Unknown transport operation.")
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=5) as conn:
                conn.row_factory = sqlite3.Row
                return getattr(self, self.handlers[operation])(conn, slots)
        except sqlite3.Error:
            return ServiceResult("error", {}, "The canonical transit database could not complete the request.")

    @staticmethod
    def _physical_stops(conn: sqlite3.Connection, entity_id: str | None) -> tuple[list[str], bool]:
        if not entity_id:
            return [], False
        if entity_id.startswith("HUB_"):
            rows = conn.execute(
                "SELECT DISTINCT stop_id, verified FROM hub_members WHERE hub_id = ?", (entity_id,)
            ).fetchall()
            return [row["stop_id"] for row in rows], any(not row["verified"] for row in rows)
        row = conn.execute("SELECT stop_id FROM transport_stops WHERE stop_id = ?", (entity_id,)).fetchone()
        return ([row["stop_id"]] if row else []), False

    @staticmethod
    def _mode(slots: Mapping[str, Any]) -> str | None:
        mode = slots.get("transport_mode")
        return None if mode in (None, "any") else ("suburban_rail" if mode == "mrts" else mode)

    @staticmethod
    def _route_ids(conn: sqlite3.Connection, slots: Mapping[str, Any]) -> list[sqlite3.Row]:
        name = slots.get("route_number") or slots.get("line_name")
        if not name:
            return []
        mode = CanonicalTransitService._mode(slots)
        sql = "SELECT route_id, route_short_name, mode, source_id FROM transport_routes WHERE REPLACE(REPLACE(UPPER(route_short_name), ' ', ''), '-', '') = REPLACE(REPLACE(UPPER(?), ' ', ''), '-', '') AND status = 'operational'"
        params: list[Any] = [name]
        if mode:
            sql += " AND mode = ?"
            params.append(mode)
        return conn.execute(sql, params).fetchall()

    def _route_candidates(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> tuple[list[dict], bool]:
        origins, origin_provisional = self._physical_stops(conn, slots.get("origin"))
        destinations, destination_provisional = self._physical_stops(conn, slots.get("destination"))
        if not origins or not destinations:
            return [], False
        via = slots.get("via")
        vias, via_provisional = self._physical_stops(conn, via) if via else ([], False)
        if via and not vias:
            return [], False
        mode = self._mode(slots)
        sql = f"""
            SELECT DISTINCT r.route_id, r.route_short_name, r.mode, r.source_id,
                   a.direction_id, a.stop_sequence AS origin_sequence,
                   b.stop_sequence AS destination_sequence,
                   a.canonical_stop_id AS origin_stop_id,
                   b.canonical_stop_id AS destination_stop_id
            FROM route_stops a
            JOIN route_stops b ON b.route_id = a.route_id
                 AND b.direction_id = a.direction_id AND b.stop_sequence > a.stop_sequence
            JOIN transport_routes r ON r.route_id = a.route_id AND r.status = 'operational'
            JOIN transport_stops os ON os.stop_id = a.canonical_stop_id AND os.mode = r.mode
            JOIN transport_stops ds ON ds.stop_id = b.canonical_stop_id AND ds.mode = r.mode
            WHERE a.canonical_stop_id IN ({','.join('?' for _ in origins)})
              AND b.canonical_stop_id IN ({','.join('?' for _ in destinations)})
        """
        params: list[Any] = origins + destinations
        if mode:
            sql += " AND r.mode = ?"
            params.append(mode)
        route_name = slots.get("route_number") or slots.get("line_name")
        if route_name:
            sql += " AND REPLACE(REPLACE(UPPER(r.route_short_name), ' ', ''), '-', '') = REPLACE(REPLACE(UPPER(?), ' ', ''), '-', '')"
            params.append(route_name)
        if via:
            sql += f""" AND EXISTS (
                SELECT 1 FROM route_stops v
                WHERE v.route_id = a.route_id AND v.direction_id = a.direction_id
                  AND v.stop_sequence > a.stop_sequence AND v.stop_sequence < b.stop_sequence
                  AND v.canonical_stop_id IN ({','.join('?' for _ in vias)})
            )"""
            params.extend(vias)
        sql += " ORDER BY b.stop_sequence - a.stop_sequence, r.route_id LIMIT 10"
        rows = conn.execute(sql, params).fetchall()
        result = [{
            "route_id": row["route_id"], "route_name": row["route_short_name"],
            "mode": row["mode"], "direction_id": row["direction_id"],
            "origin_stop_id": row["origin_stop_id"], "destination_stop_id": row["destination_stop_id"],
            "origin_sequence": row["origin_sequence"], "destination_sequence": row["destination_sequence"],
            "source": row["source_id"],
        } for row in rows]
        return result, origin_provisional or destination_provisional or via_provisional

    def _plan_route(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        if slots.get("preference") in {"fastest", "cheapest", "least_transfers"}:
            return _unavailable("Verified optimization for that route preference is unavailable.")
        routes, hub_provisional = self._route_candidates(conn, slots)
        if not routes:
            return _unavailable("No directionally valid published route sequence was found for these stops.")
        return _ok("Published route-sequence candidates are available; verify service and transfers before travel.", {
            "routes": routes, "provisional": True, "hub_membership_unverified": hub_provisional,
            "scope": "published_stop_sequence_not_trip_confirmation",
        })

    def _multimodal_route(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        return _unavailable("No confirmed cross-mode transfer graph is available in this snapshot.", {
            "reason": "interchanges_and_hub_memberships_unverified",
        })

    def _list_route_stops(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        routes = self._route_ids(conn, slots)
        sequences = []
        for route in routes:
            rows = conn.execute("""
                SELECT rs.direction_id, rs.stop_sequence, rs.canonical_stop_id,
                       s.canonical_name, s.mode
                FROM route_stops rs
                JOIN transport_stops s ON s.stop_id = rs.canonical_stop_id
                WHERE rs.route_id = ? AND s.mode = ?
                ORDER BY rs.direction_id, rs.stop_sequence
            """, (route["route_id"], route["mode"])).fetchall()
            by_direction: dict[int, list[dict]] = {}
            for row in rows:
                by_direction.setdefault(row["direction_id"], []).append({
                    "sequence": row["stop_sequence"], "stop_id": row["canonical_stop_id"],
                    "name": row["canonical_name"],
                })
            for direction, stops in by_direction.items():
                if len(stops) > 1:
                    sequences.append({
                        "route_id": route["route_id"], "route_name": route["route_short_name"],
                        "mode": route["mode"], "direction_id": direction,
                        "stops": stops, "source": route["source_id"],
                    })
        if not sequences:
            return _unavailable("No mode-consistent published stop sequence is available for that route.")
        return _ok("Published stop sequences found; service operation is not confirmed.", {
            "sequences": sequences[:10], "truncated": len(sequences) > 10, "provisional": True,
        })

    def _check_stop_on_route(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        routes = self._route_ids(conn, slots)
        stop_ids, hub_provisional = self._physical_stops(conn, slots.get("stop"))
        if not routes or not stop_ids:
            return _unavailable("Route or stop is absent from the canonical snapshot.")
        route_ids = [row["route_id"] for row in routes]
        sql = f"""
            SELECT COUNT(*) FROM route_stops rs
            JOIN transport_routes r ON r.route_id = rs.route_id
            JOIN transport_stops s ON s.stop_id = rs.canonical_stop_id AND s.mode = r.mode
            WHERE rs.route_id IN ({','.join('?' for _ in route_ids)})
              AND rs.canonical_stop_id IN ({','.join('?' for _ in stop_ids)})
        """
        count = conn.execute(sql, route_ids + stop_ids).fetchone()[0]
        coverage = conn.execute(f"""
            SELECT COUNT(*) FROM route_stops rs
            JOIN transport_routes r ON r.route_id = rs.route_id
            JOIN transport_stops s ON s.stop_id = rs.canonical_stop_id AND s.mode = r.mode
            WHERE rs.route_id IN ({','.join('?' for _ in route_ids)})
        """, route_ids).fetchone()[0]
        if coverage == 0:
            return _unavailable("The route has no published stop sequence in this snapshot.")
        return _ok("Published route-stop sequence checked; current service is not confirmed.", {
            "on_route": bool(count), "route_ids": route_ids,
            "provisional": True, "hub_membership_unverified": hub_provisional,
        })

    def _scheduled_rows(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> list[sqlite3.Row] | None:
        entity_id = slots.get("station") or slots.get("stop") or slots.get("origin")
        stop_ids, _ = self._physical_stops(conn, entity_id)
        if not stop_ids:
            return []
        sql = f"""
            SELECT st.departure_time, tr.route_id, r.route_short_name, r.mode, r.source_id
            FROM stop_times st
            JOIN trips tr ON tr.trip_id = st.trip_id
            JOIN transport_routes r ON r.route_id = tr.route_id AND r.status = 'operational'
            JOIN transport_stops s ON s.stop_id = st.canonical_stop_id AND s.mode = r.mode
            WHERE st.canonical_stop_id IN ({','.join('?' for _ in stop_ids)})
              AND st.departure_time IS NOT NULL
        """
        params: list[Any] = list(stop_ids)
        mode = self._mode(slots)
        if mode:
            sql += " AND r.mode = ?"
            params.append(mode)
        route_name = slots.get("route_number") or slots.get("line_name")
        if route_name:
            sql += " AND REPLACE(REPLACE(UPPER(r.route_short_name), ' ', ''), '-', '') = REPLACE(REPLACE(UPPER(?), ' ', ''), '-', '')"
            params.append(route_name)
        if slots.get("date"):
            chosen = date.fromisoformat(slots["date"])
            weekday = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")[chosen.weekday()]
            sql += f""" AND EXISTS (
                SELECT 1 FROM service_calendars cal WHERE cal.service_id = tr.service_id
                  AND cal.start_date <= ? AND cal.end_date >= ? AND cal.{weekday} = 1
            )"""
            params.extend([chosen.strftime("%Y%m%d")] * 2)
        destination = slots.get("destination")
        if destination:
            destination_stops, _ = self._physical_stops(conn, destination)
            if not destination_stops:
                return []
            sql += f""" AND EXISTS (
                SELECT 1 FROM stop_times dst
                JOIN transport_stops ds ON ds.stop_id = dst.canonical_stop_id AND ds.mode = r.mode
                WHERE dst.trip_id = st.trip_id AND dst.stop_sequence > st.stop_sequence
                  AND dst.canonical_stop_id IN ({','.join('?' for _ in destination_stops)})
            )"""
            params.extend(destination_stops)
        rows = conn.execute(sql + " ORDER BY st.departure_time LIMIT 10001", params).fetchall()
        return None if len(rows) > 10000 else rows

    def _first_last(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        rows = self._scheduled_rows(conn, slots)
        if rows is None:
            return _unavailable("Too many schedule rows to report a reliable first or last time.")
        if not rows:
            return _unavailable("No mode-consistent published schedule was found for this stop.")
        return _ok("Published schedule bounds; verify current operation with the operator.", {
            "first_departure": rows[0]["departure_time"],
            "last_departure": rows[-1]["departure_time"],
            "timing_type": slots.get("timing_type"), "source": sorted({row["source_id"] for row in rows}),
            "time_format": "gtfs_service_day", "provisional": True,
        })

    def _frequency(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        if not (slots.get("route_number") or slots.get("line_name")):
            return _unavailable("A specific route or line is needed for a meaningful frequency estimate.")
        rows = self._scheduled_rows(conn, slots)
        if rows is None or len(rows) < 2:
            return _unavailable("Insufficient published departures for a schedule-based frequency estimate.")
        def minutes(value: str) -> int:
            hour, minute, second = map(int, value.split(":"))
            return hour * 60 + minute + (1 if second >= 30 else 0)
        times = sorted({minutes(row["departure_time"]) for row in rows})
        requested = slots.get("time")
        if requested:
            if isinstance(requested, (list, tuple)):
                requested = requested[0] if len(requested) == 1 else None
            if requested:
                start = minutes(requested)
                times = [value for value in times if start <= value < start + 120]
        gaps = [b - a for a, b in zip(times, times[1:]) if 0 < b - a <= 180]
        if not gaps:
            return _unavailable("Published departures do not support a reliable frequency estimate.")
        return _ok("Median interval estimated from a published timetable, not live service.", {
            "median_headway_minutes": median(gaps), "sample_intervals": len(gaps),
            "source": sorted({row["source_id"] for row in rows}),
            "window_start": requested, "window_minutes": 120 if requested else None,
            "provisional": True,
        })

    def _departures(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        rows = self._scheduled_rows(conn, slots)
        if rows is None or not rows:
            return _unavailable("No mode-consistent published departures were found for this stop.")
        threshold = slots.get("time")
        if isinstance(threshold, (list, tuple)):
            threshold = threshold[0] if len(threshold) == 1 else None
        selected = [row for row in rows if not threshold or row["departure_time"] >= threshold][:5]
        if not selected:
            return _unavailable("No published departures were found after the requested time.")
        return _ok("Published departures only; times are not live predictions.", {
            "departures": [{"time": row["departure_time"], "route_id": row["route_id"],
                            "route_name": row["route_short_name"], "source": row["source_id"]}
                           for row in selected],
            "time_format": "gtfs_service_day", "provisional": True,
        })

    def _availability(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        routes, _ = self._route_candidates(conn, slots)
        return _unavailable("Current operating availability cannot be confirmed from this snapshot.", {
            "published_directional_route_candidates": len(routes), "provisional": True,
        })

    def _fare(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        if slots.get("ticket_type") not in (None, "token"):
            return _unavailable("The snapshot does not verify fare rules for that ticket type.")
        mode = self._mode(slots)
        origin, destination = slots.get("origin"), slots.get("destination")
        if origin and destination:
            if mode not in (None, "metro"):
                return _unavailable("The canonical origin-destination fare table covers metro journeys only.")
            if slots.get("fare_type") not in (None, "distance_fare") or slots.get("service_type"):
                return _unavailable("The requested fare type is not verified for a metro origin-destination fare.")
            row = conn.execute("""
                SELECT token_fare, discounted_fare, currency, effective_date, source_id
                FROM cmrl_station_fares WHERE origin_stop_id = ? AND destination_stop_id = ?
                ORDER BY effective_date DESC LIMIT 1
            """, (origin, destination)).fetchone()
            if row:
                return _ok("Published fare record found; confirm the current fare before travel.", {
                    "amount": row["token_fare"], "discounted_amount": row["discounted_fare"],
                    "currency": row["currency"], "effective_date": row["effective_date"],
                    "source": row["source_id"], "provisional": True,
                })
        stage = slots.get("stage_number")
        if stage:
            if mode not in (None, "bus"):
                return _unavailable("The canonical stage fare table covers bus journeys only.")
            if slots.get("fare_type") not in (None, "stage_fare") or slots.get("ticket_type"):
                return _unavailable("The requested fare or ticket type is not verified for a bus stage fare.")
            service = slots.get("service_type") or "Ordinary Services"
            row = conn.execute("""
                SELECT fare_amount, currency, effective_date, government_order, source_id
                FROM fares WHERE stage_number = ? AND service_type = ?
                ORDER BY effective_date DESC LIMIT 1
            """, (stage, service)).fetchone()
            if row:
                return _ok("Published stage fare found; confirm the current fare before travel.", {
                    "amount": row["fare_amount"], "currency": row["currency"],
                    "stage_number": stage, "service_type": service,
                    "effective_date": row["effective_date"], "source": row["source_id"],
                    "government_order": row["government_order"], "provisional": True,
                })
        return _unavailable("No verified fare record covers the requested journey or stage.")

    def _ticketing(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        return _unavailable("This snapshot contains no authoritative ticket or pass policy table.")

    def _facility(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        return _unavailable("Facility availability is not verified in this snapshot.")

    def _accessibility(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        feature = slots.get("accessibility_feature")
        if feature == "any" or not feature:
            return _unavailable("No verified accessibility feature was requested.")
        columns = {
            "wheelchair": "wheelchair_available", "lift": "lift_available",
            "escalator": "escalator_available", "ramp": "ramp_available",
            "accessible_toilet": "accessible_toilet", "tactile_paths": "tactile_paths",
        }
        if feature not in columns:
            return _unavailable("That accessibility feature is not recorded in the snapshot.")
        stops, hub_provisional = self._physical_stops(conn, slots.get("station"))
        if len(stops) != 1 or hub_provisional:
            return _unavailable("A single verified physical station is required for accessibility data.")
        row = conn.execute(f"SELECT {columns[feature]} FROM accessibility WHERE stop_id = ?", stops).fetchone()
        if not row or row[0] is None:
            return _unavailable("The accessibility record does not verify this feature.")
        return _ok("Recorded accessibility feature; confirm current working status with the operator.", {
            "station": stops[0], "feature": feature, "available": bool(row[0]), "provisional": True,
        })

    def _interchange(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        stops, _ = self._physical_stops(conn, slots.get("station"))
        if not stops:
            return _unavailable("No confirmed interchange is available for this location.")
        sql = f"""SELECT from_stop_id, to_stop_id, walking_distance_m, walking_time_min
                   FROM interchanges WHERE confirmed = 1 AND
                   (from_stop_id IN ({','.join('?' for _ in stops)}) OR
                    to_stop_id IN ({','.join('?' for _ in stops)})) LIMIT 10"""
        rows = conn.execute(sql, stops + stops).fetchall()
        if not rows:
            return _unavailable("The snapshot has no confirmed interchange for this location.")
        return _ok("Confirmed interchange records found.", {
            "transfers": [dict(row) for row in rows], "provisional": False,
        })

    def _nearest(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        anchor = slots.get("landmark") or slots.get("locality")
        row = conn.execute("SELECT latitude, longitude, canonical_name FROM places WHERE place_id = ?", (anchor,)).fetchone()
        if not row:
            row = conn.execute("SELECT latitude, longitude, hub_name AS canonical_name FROM transport_hubs WHERE hub_id = ?", (anchor,)).fetchone()
        if not row or row["latitude"] is None or row["longitude"] is None:
            return _unavailable("The requested location has no usable canonical coordinates.")
        mode = self._mode(slots)
        sql = "SELECT stop_id, canonical_name, mode, latitude, longitude, primary_source_id FROM transport_stops WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND inside_cma = 1"
        params: list[Any] = []
        if mode:
            sql += " AND mode = ?"
            params.append(mode)
        stops = []
        for stop in conn.execute(sql, params):
            stops.append({
                "stop_id": stop["stop_id"], "name": stop["canonical_name"], "mode": stop["mode"],
                "distance_m": round(_haversine_m(row["latitude"], row["longitude"], stop["latitude"], stop["longitude"])),
                "source": stop["primary_source_id"],
            })
        if not stops:
            return _unavailable("No located transport stops match the requested mode.")
        stops.sort(key=lambda item: (item["distance_m"], item["stop_id"]))
        return _ok("Nearest by straight-line distance only; walking access is not verified.", {
            "anchor": anchor, "anchor_name": row["canonical_name"],
            "stops": stops[:5], "distance_type": "straight_line", "provisional": True,
        })

    def _realtime(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        return _unavailable("Live transport status is unavailable; verify with the operator.")

    def _out_of_scope(self, conn: sqlite3.Connection, slots: Mapping[str, Any]) -> ServiceResult:
        return ServiceResult("unavailable", {}, "This assistant covers Chennai public transport questions only.")
