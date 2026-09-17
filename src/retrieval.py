"""Transit Knowledge Base retrieval module using SQLite.

Queries transport.db for stations, connections, service timing,
accessibility features, and ticketing rules.
"""

import os
import sqlite3
from typing import Dict, List, Optional, Any


class TransitRetriever:
    """Interacts with the local SQLite transport knowledge base."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to data/processed/transport.db relative to repo root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "data", "processed", "transport.db")
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Returns SQLite connection with dict-like row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_station_info(self, station_id: str) -> Optional[Dict[str, Any]]:
        """Fetches station metadata by canonical ID."""
        if not os.path.exists(self.db_path):
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM stations WHERE station_id = ?",
                (station_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_route(
        self, origin_id: str, destination_id: str, mode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns explicitly stored journeys; does not compute connecting paths."""
        if not os.path.exists(self.db_path):
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT c.*,
                       s1.name_en as origin_name_en, s1.name_hi as origin_name_hi,
                       s2.name_en as dest_name_en, s2.name_hi as dest_name_hi
                FROM connections c
                JOIN stations s1 ON c.origin_id = s1.station_id
                JOIN stations s2 ON c.destination_id = s2.station_id
                WHERE c.origin_id = ? AND c.destination_id = ?
            """
            params: List[Any] = [origin_id, destination_id]
            if mode:
                query_with_mode = query + " AND c.mode = ?"
                cursor.execute(query_with_mode, tuple(params + [mode]))
                rows = cursor.fetchall()
                if rows:
                    return [dict(r) for r in rows]

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def check_availability(
        self, origin_id: str, destination_id: str, mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Checks if connectivity exists between origin and destination."""
        routes = self.get_route(origin_id, destination_id, mode)
        available = len(routes) > 0
        return {
            "available": available,
            "routes": routes,
            "origin_id": origin_id,
            "destination_id": destination_id,
            "mode": mode
        }

    def get_service_timing(
        self, mode: Optional[str] = "metro", line_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves operating timings, first/last trains, and frequencies."""
        if not os.path.exists(self.db_path):
            return []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM service_info WHERE 1=1"
            params: List[Any] = []
            if mode:
                query += " AND mode = ?"
                params.append(mode)
            if line_name:
                query += " AND line_name LIKE ?"
                params.append(f"%{line_name}%")

            cursor.execute(query, tuple(params))
            return [dict(r) for r in cursor.fetchall()]

    def get_accessibility_info(self, station_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves accessibility amenities (wheelchairs, lifts, tactile paths) for station."""
        if not os.path.exists(self.db_path):
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT f.*, s.name_en, s.name_hi
                FROM facilities f
                JOIN stations s ON f.station_id = s.station_id
                WHERE f.station_id = ?
            """
            cursor.execute(query, (station_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_ticketing_info(
        self, origin_id: Optional[str] = None, destination_id: Optional[str] = None, mode: Optional[str] = "metro"
    ) -> Dict[str, Any]:
        """Returns fare and ticketing information for route or general mode."""
        # No fare table exists. Do not infer fares or ticket rules from distance.
        return {}
