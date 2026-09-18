#!/usr/bin/env python3
"""Point-in-polygon geographic classifier for the Chennai Metropolitan Area (CMA).

Uses the official CUMTA / TNGIS administrative boundary MultiPolygon from:
  data/raw/government/2026-09-18/cumta_cma_boundary_official.geojson

Features:
- Exact ray-casting point-in-polygon for MultiPolygon / Polygon rings with hole exclusion.
- Bounding-box pre-filtering for sub-millisecond classification per point.
- Separate regional plausibility check for the broader Chennai commuter catchment area
  (Lat ~12.0 to 14.0, Lon ~79.0 to 81.0).
"""

import os
import sys
import json
from typing import List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CMA_GEOJSON_PATH = os.path.join(
    BASE_DIR, "data", "raw", "government", "2026-09-18", "cumta_cma_boundary_official.geojson"
)

# Regional plausibility box for broader Chennai commuter catchment
REGIONAL_LAT_MIN, REGIONAL_LAT_MAX = 12.00, 14.00
REGIONAL_LON_MIN, REGIONAL_LON_MAX = 79.00, 81.00


class CMABoundaryChecker:
    """Classifies geographic coordinates against the official CUMTA CMA boundary."""

    def __init__(self, geojson_path: Optional[str] = None):
        self.geojson_path = geojson_path or CMA_GEOJSON_PATH
        self.polygons: List[List[List[Tuple[float, float]]]] = []
        self.bbox: Tuple[float, float, float, float] = (999.0, 999.0, -999.0, -999.0)
        self._load_boundary()

    def _load_boundary(self):
        if not os.path.exists(self.geojson_path):
            raise FileNotFoundError(
                f"Official CMA boundary GeoJSON missing at {self.geojson_path}. "
                f"Run acquisition step first."
            )

        with open(self.geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])
        if not features:
            raise ValueError("No features found in CMA boundary GeoJSON.")

        min_lon, min_lat = 999.0, 999.0
        max_lon, max_lat = -999.0, -999.0

        for feat in features:
            geom = feat.get("geometry", {})
            gtype = geom.get("type")
            coords = geom.get("coordinates", [])

            if gtype == "Polygon":
                # List of rings (outer + inner holes)
                poly_rings = []
                for ring in coords:
                    r = [(float(pt[0]), float(pt[1])) for pt in ring]
                    for x, y in r:
                        min_lon = min(min_lon, x)
                        max_lon = max(max_lon, x)
                        min_lat = min(min_lat, y)
                        max_lat = max(max_lat, y)
                    poly_rings.append(r)
                self.polygons.append(poly_rings)

            elif gtype == "MultiPolygon":
                # List of polygons, each having rings
                for poly in coords:
                    poly_rings = []
                    for ring in poly:
                        r = [(float(pt[0]), float(pt[1])) for pt in ring]
                        for x, y in r:
                            min_lon = min(min_lon, x)
                            max_lon = max(max_lon, x)
                            min_lat = min(min_lat, y)
                            max_lat = max(max_lat, y)
                        poly_rings.append(r)
                    self.polygons.append(poly_rings)

        self.bbox = (min_lon, min_lat, max_lon, max_lat)

    @staticmethod
    def _ring_contains_point(x: float, y: float, ring: List[Tuple[float, float]]) -> bool:
        """Ray-casting algorithm to test if point (x=lon, y=lat) is inside a polygon ring."""
        n = len(ring)
        inside = False
        p1x, p1y = ring[0]
        for i in range(1, n + 1):
            p2x, p2y = ring[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def is_inside_cma(self, latitude: float, longitude: float) -> bool:
        """Returns True if (latitude, longitude) is strictly inside the official CMA boundary."""
        if latitude is None or longitude is None:
            return False

        # Fast bounding box rejection
        min_lon, min_lat, max_lon, max_lat = self.bbox
        if not (min_lon <= longitude <= max_lon and min_lat <= latitude <= max_lat):
            return False

        # Point in polygon check
        x, y = longitude, latitude
        for poly in self.polygons:
            if not poly:
                continue
            # Outer ring must contain the point
            outer_ring = poly[0]
            if self._ring_contains_point(x, y, outer_ring):
                # Must not be inside any holes (inner rings)
                in_hole = False
                for hole_ring in poly[1:]:
                    if self._ring_contains_point(x, y, hole_ring):
                        in_hole = True
                        break
                if not in_hole:
                    return True

        return False

    @staticmethod
    def is_regionally_plausible(latitude: float, longitude: float) -> bool:
        """Validates if coordinates belong to the greater Chennai transportation region."""
        if latitude is None or longitude is None:
            return False
        return (
            REGIONAL_LAT_MIN <= latitude <= REGIONAL_LAT_MAX
            and REGIONAL_LON_MIN <= longitude <= REGIONAL_LON_MAX
        )


# Singleton instance for module-level usage
_DEFAULT_CHECKER: Optional[CMABoundaryChecker] = None


def get_cma_checker() -> CMABoundaryChecker:
    global _DEFAULT_CHECKER
    if _DEFAULT_CHECKER is None:
        _DEFAULT_CHECKER = CMABoundaryChecker()
    return _DEFAULT_CHECKER


def is_point_inside_cma(latitude: float, longitude: float) -> bool:
    return get_cma_checker().is_inside_cma(latitude, longitude)


def is_regionally_plausible(latitude: float, longitude: float) -> bool:
    return CMABoundaryChecker.is_regionally_plausible(latitude, longitude)


if __name__ == "__main__":
    checker = get_cma_checker()
    print(f"CMA Boundary loaded with {len(checker.polygons)} polygons.")
    print(f"Bounding Box (Lon Min, Lat Min, Lon Max, Lat Max): {checker.bbox}")

    # Test sample points
    test_points = [
        ("Chennai Central", 13.0827, 80.2707),
        ("Guindy Metro", 13.0098, 80.2132),
        ("Tambaram RS", 12.9249, 80.1197),
        ("Chengalpattu RS", 12.6841, 79.9836),
        ("Arakkonam RS", 13.0786, 79.6683),
        ("Gummidipoondi RS", 13.4072, 80.1306),
        ("Tiruvallur RS", 13.1438, 79.9079),
        ("Delhi Connaught Place", 28.6328, 77.2197),
    ]

    print("\nVerification of test points:")
    for name, lat, lon in test_points:
        inside = checker.is_inside_cma(lat, lon)
        plausible = checker.is_regionally_plausible(lat, lon)
        print(f"  {name:25s} ({lat:.4f}, {lon:.4f}) -> inside_cma: {inside:<5} (plausible: {plausible})")
