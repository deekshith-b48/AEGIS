from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import Cordon, Hotspot
from datetime import datetime, timedelta
import uuid
import math

class CordonService:
    def __init__(self, db: Session):
        self.db = db
        self.default_radius_meters = 2000  # 2km default radius
        self.default_duration_minutes = 45

    def activate_cordon(self, hotspot_id: str, radius_meters: int = None, duration_minutes: int = None) -> dict:
        """
        Activate digital cordon around a hotspot
        """
        try:
            # Get hotspot location
            hotspot = self.db.query(Hotspot).filter(Hotspot.id == hotspot_id).first()
            if not hotspot:
                raise ValueError(f"Hotspot {hotspot_id} not found")

            # Set defaults if not provided
            radius = radius_meters or self.default_radius_meters
            duration = duration_minutes or self.default_duration_minutes

            # Create cordon record
            cordon = Cordon(
                center_location=hotspot.hotspot_location,
                radius_meters=radius,
                expires_at=datetime.utcnow() + timedelta(minutes=duration),
                status='active'
            )

            self.db.add(cordon)
            self.db.commit()
            self.db.refresh(cordon)

            # Simulate NPCI integration
            self._simulate_npci_integration(cordon)

            # Update hotspot status
            hotspot.status = 'interdicted'
            self.db.commit()

            return {
                'cordon_id': str(cordon.id),
                'radius_meters': radius,
                'duration_minutes': duration,
                'expires_at': cordon.expires_at.isoformat(),
                'center_location': str(hotspot.hotspot_location),
                'status': 'active'
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Cordon activation failed: {str(e)}")

    def _simulate_npci_integration(self, cordon: Cordon):
        """
        Simulate NPCI integration for transaction monitoring
        """
        # In production, this would make actual API calls to NPCI
        # For MVP, we simulate the integration

        integration_data = {
            'cordon_id': str(cordon.id),
            'center_coordinates': str(cordon.center_location),
            'radius_meters': cordon.radius_meters,
            'start_time': cordon.created_at.isoformat(),
            'end_time': cordon.expires_at.isoformat(),
            'monitoring_type': 'real_time_transaction_flagging',
            'alert_threshold': 'all_transactions_above_10000'
        }

        print(f"[NPCI SIMULATION] Digital cordon activated for transaction monitoring:")
        print(f"[NPCI SIMULATION] {integration_data}")

        # Simulate webhook call to NPCI
        webhook_response = {
            'status': 'success',
            'cordon_registered': True,
            'transaction_monitoring_active': True,
            'reference_id': f"NPCI-{uuid.uuid4().hex[:8].upper()}"
        }

        print(f"[NPCI SIMULATION] Webhook response: {webhook_response}")

        return webhook_response

    def get_active_cordons(self) -> list:
        """
        Get all currently active cordons
        """
        return self.db.query(Cordon).filter(
            Cordon.status == 'active',
            Cordon.expires_at > datetime.utcnow()
        ).all()

    def deactivate_cordon(self, cordon_id: str) -> bool:
        """
        Manually deactivate a cordon
        """
        try:
            cordon = self.db.query(Cordon).filter(Cordon.id == cordon_id).first()
            if not cordon:
                return False

            cordon.status = 'expired'
            cordon.expires_at = datetime.utcnow()
            self.db.commit()

            # Simulate NPCI deactivation
            self._simulate_npci_deactivation(cordon_id)

            return True

        except Exception as e:
            self.db.rollback()
            print(f"Cordon deactivation error: {str(e)}")
            return False

    def _simulate_npci_deactivation(self, cordon_id: str):
        """
        Simulate NPCI cordon deactivation
        """
        deactivation_data = {
            'cordon_id': cordon_id,
            'deactivation_time': datetime.utcnow().isoformat(),
            'transaction_monitoring_stopped': True
        }

        print(f"[NPCI SIMULATION] Digital cordon deactivated:")
        print(f"[NPCI SIMULATION] {deactivation_data}")

        return True

    def get_cordon_geojson(self, cordon: Cordon) -> dict:
        """
        Convert cordon to GeoJSON polygon for map visualization
        """
        # Extract center point coordinates
        center_coords = self.db.execute(
            text("SELECT ST_X(center_location) as lon, ST_Y(center_location) as lat FROM cordons WHERE id = :id"),
            {"id": cordon.id}
        ).first()

        if not center_coords:
            return None

        # Generate circle points for GeoJSON
        circle_coords = self._generate_circle_points(
            center_coords.lon,
            center_coords.lat,
            cordon.radius_meters
        )

        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [circle_coords]
            },
            "properties": {
                "id": str(cordon.id),
                "radius_meters": cordon.radius_meters,
                "expires_at": cordon.expires_at.isoformat(),
                "status": cordon.status,
                "created_at": cordon.created_at.isoformat()
            }
        }

    def _generate_circle_points(self, center_lon: float, center_lat: float, radius_meters: int) -> list:
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

    def cleanup_expired_cordons(self):
        """
        Automatically mark expired cordons as inactive
        """
        expired_count = self.db.query(Cordon).filter(
            Cordon.status == 'active',
            Cordon.expires_at <= datetime.utcnow()
        ).update({"status": "expired"})

        self.db.commit()

        if expired_count > 0:
            print(f"[CORDON] Cleaned up {expired_count} expired cordons")

        return expired_count