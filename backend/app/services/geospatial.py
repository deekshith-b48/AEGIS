from sqlalchemy import text
from app.database import HighRiskATM, Hotspot
import shapely.wkt
from shapely.geometry import Point
import math

def create_location_point(lat: float, lon: float) -> str:
    """
    Create PostGIS point from latitude/longitude
    """
    return f"POINT({lon} {lat})"

def find_nearby_atms(db, location_point: str, radius_km: float = 5) -> list:
    """
    Find ATMs within specified radius of location
    """
    query = text("""
        SELECT *,
               ST_Distance(location, ST_GeomFromText(:location_point, 4326)) as distance_km
        FROM high_risk_atms
        WHERE ST_DWithin(
            location,
            ST_GeomFromText(:location_point, 4326),
            :radius_meters
        )
        ORDER BY distance_km
        LIMIT 10
    """)

    result = db.execute(
        query,
        {
            "location_point": location_point,
            "radius_meters": radius_km * 1000
        }
    ).fetchall()

    return [dict(row) for row in result]

def calculate_distance(location1: str, location2: str) -> float:
    """
    Calculate distance between two points in kilometers
    """
    query = text("""
        SELECT ST_Distance(
            ST_GeomFromText(:location1, 4326),
            ST_GeomFromText(:location2, 4326)
        ) as distance_km
    """)

    result = db.execute(query, {"location1": location1, "location2": location2}).fetchone()
    return float(result.distance_km) if result else 0

def complaint_to_geojson(complaint) -> dict:
    """
    Convert complaint to GeoJSON feature
    """
    return {
        "type": "Feature",
        "properties": {
            "id": str(complaint.id),
            "scam_type": complaint.scam_type,
            "amount": float(complaint.amount),
            "created_at": complaint.created_at.isoformat()
        },
        "geometry": None  # Will be populated by the caller
    }

def hotspot_to_response(hotspot, db) -> dict:
    """
    Convert hotspot to response format with coordinates
    """
    # Get coordinates
    coords_result = db.execute(
        text("SELECT ST_AsGeoJSON(hotspot_location) as geojson FROM hotspots WHERE id = :id"),
        {"id": hotspot.id}
    ).fetchone()

    return {
        "id": str(hotspot.id),
        "complaint_id": str(hotspot.complaint_id),
        "hotspot_location": coords_result.geojson if coords_result else None,
        "location_name": hotspot.location_name,
        "confidence": hotspot.confidence,
        "time_window_mins": hotspot.time_window_mins,
        "predicted_at": hotspot.predicted_at.isoformat(),
        "status": hotspot.status
    }

def generate_circle_points(center_lon: float, center_lat: float, radius_meters: int) -> list:
    """
    Generate circle points for GeoJSON polygon
    """
    points = []
    num_points = 64  # Number of points in circle

    for i in range(num_points + 1):
        angle = 2 * math.pi * i / num_points

        # Calculate offset in degrees (approximate)
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        lat_offset = (radius_meters / 111000) * math.sin(angle)
        lon_offset = (radius_meters / (111000 * math.cos(math.radians(center_lat)))) * math.cos(angle)

        point_lat = center_lat + lat_offset
        point_lon = center_lon + lon_offset

        points.append([point_lon, point_lat])

    return points