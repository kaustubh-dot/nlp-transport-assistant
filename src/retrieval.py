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
        """Finds direct or connected routes between origin and destination."""
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
                query += " AND c.mode = ?"
                params.append(mode)

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
        if origin_id and destination_id:
            routes = self.get_route(origin_id, destination_id, mode)
            if routes:
                route = routes[0]
                # Standard fare approximation based on distance/mode if not in DB
                dist = route.get("distance_km", 10.0)
                fare = min(60, max(10, int(dist * 2.5)))
                return {
                    "mode": mode or route.get("mode"),
                    "estimated_fare": fare,
                    "origin_id": origin_id,
                    "destination_id": destination_id,
                    "ticketing_methods": ["QR Code (WhatsApp/App)", "Smart Card", "Token Counter", "NCMC Card"]
                }

        # Fallback to general mode fare range
        timings = self.get_service_timing(mode)
        min_fare = timings[0].get("min_fare", 10) if timings else 10
        max_fare = timings[0].get("max_fare", 60) if timings else 60

        return {
            "mode": mode,
            "min_fare": min_fare,
            "max_fare": max_fare,
            "ticketing_methods": ["QR Code Ticket", "Metro Smart Card (20% Discount)", "Token at Station Kiosks"]
        }
