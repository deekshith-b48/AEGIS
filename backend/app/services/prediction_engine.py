from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import Complaint, Hotspot, HighRiskATM
from app.services.geospatial import find_nearby_atms, calculate_distance, create_location_point
from datetime import datetime, timedelta
import uuid
import random

class PredictionEngine:
    def __init__(self, db: Session):
        self.db = db
        self.confidence_threshold = 0.8
        self.prediction_rules = {
            "FAKE_LOAN_APP": self._predict_fake_loan_app,
            "UPI_PHISHING": self._predict_upi_phishing,
            "IMPERSONATION": self._predict_impersonation,
            "LOTTERY_SCAM": self._predict_lottery_scam,
            "INVESTMENT_FRAUD": self._predict_investment_fraud
        }

    def predict_hotspots(self, complaint_id: str) -> list:
        """
        Main prediction algorithm - executes multiple rules and combines results
        """
        complaint = self.db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            return []

        all_predictions = []

        # Execute primary rule based on scam type
        primary_predictor = self.prediction_rules.get(complaint.scam_type, self._predict_default)
        primary_predictions = primary_predictor(complaint)
        all_predictions.extend(primary_predictions)

        # Execute amount-based rule (Rule 2)
        amount_predictions = self._predict_high_amount(complaint)
        all_predictions.extend(amount_predictions)

        # Remove duplicates and rank by confidence
        unique_predictions = self._deduplicate_predictions(all_predictions)
        ranked_predictions = self._rank_by_confidence(unique_predictions, complaint)

        # Create hotspot records for high-confidence predictions
        hotspots_created = []
        for prediction in ranked_predictions[:3]:  # Top 3 predictions only
            if prediction['confidence'] >= self.confidence_threshold:
                hotspot = Hotspot(
                    complaint_id=complaint.id,
                    hotspot_location=text(f"ST_GeomFromText('POINT({prediction['lon']} {prediction['lat']})', 4326)"),
                    location_name=prediction['name'],
                    confidence=prediction['confidence'],
                    time_window_mins=90,
                    predicted_at=datetime.utcnow()
                )

                self.db.add(hotspot)
                hotspots_created.append(hotspot)

        if hotspots_created:
            self.db.commit()
            self._trigger_alerts(hotspots_created)

        return hotspots_created

    def _predict_fake_loan_app(self, complaint: Complaint) -> list:
        """
        Rule 1: Fake loan apps -> nearest ATMs tagged as highway or bus_stand
        """
        target_tags = ["highway", "bus_stand"]

        # Get victim location
        victim_coords = self.db.execute(
            text("SELECT ST_X(victim_location) as lon, ST_Y(victim_location) as lat FROM complaints WHERE id = :id"),
            {"id": complaint.id}
        ).first()

        if not victim_coords:
            return []

        location_point = create_location_point(victim_coords.lat, victim_coords.lon)
        nearby_atms = find_nearby_atms(self.db, location_point, radius_km=5)

        # Filter ATMs with target tags and sort by distance
        filtered_atms = [
            atm for atm in nearby_atms
            if atm['tags'] and any(tag in atm['tags'] for tag in target_tags)
        ]

        return self._rank_atms_by_distance(filtered_atms, location_point, 0.85)

    def _predict_upi_phishing(self, complaint: Complaint) -> list:
        """
        Rule 3: UPI phishing -> ATMs near railway stations
        """
        target_tags = ["railway_station", "metro_station"]

        # Get victim location
        victim_coords = self.db.execute(
            text("SELECT ST_X(victim_location) as lon, ST_Y(victim_location) as lat FROM complaints WHERE id = :id"),
            {"id": complaint.id}
        ).first()

        if not victim_coords:
            return []

        location_point = create_location_point(victim_coords.lat, victim_coords.lon)
        nearby_atms = find_nearby_atms(self.db, location_point, radius_km=3)

        # Filter ATMs near railway stations
        filtered_atms = [
            atm for atm in nearby_atms
            if atm['tags'] and any(tag in atm['tags'] for tag in target_tags)
        ]

        return self._rank_atms_by_distance(filtered_atms, location_point, 0.85)

    def _predict_impersonation(self, complaint: Complaint) -> list:
        """
        Rule 4: Impersonation -> ATMs in commercial areas
        """
        target_tags = ["commercial", "market", "shopping_center"]

        # Get victim location
        victim_coords = self.db.execute(
            text("SELECT ST_X(victim_location) as lon, ST_Y(victim_location) as lat FROM complaints WHERE id = :id"),
            {"id": complaint.id}
        ).first()

        if not victim_coords:
            return []

        location_point = create_location_point(victim_coords.lat, victim_coords.lon)
        nearby_atms = find_nearby_atms(self.db, location_point, radius_km=4)

        filtered_atms = [
            atm for atm in nearby_atms
            if atm['tags'] and any(tag in atm['tags'] for tag in target_tags)
        ]

        return self._rank_atms_by_distance(filtered_atms, location_point, 0.80)

    def _predict_high_amount(self, complaint: Complaint) -> list:
        """
        Rule 2: Amount > 50,000 -> ATMs within 2km of victim
        """
        if float(complaint.amount) > 50000:
            # Get victim location
            victim_coords = self.db.execute(
                text("SELECT ST_X(victim_location) as lon, ST_Y(victim_location) as lat FROM complaints WHERE id = :id"),
                {"id": complaint.id}
            ).first()

            if not victim_coords:
                return []

            location_point = create_location_point(victim_coords.lat, victim_coords.lon)
            nearby_atms = find_nearby_atms(self.db, location_point, radius_km=2)
            return self._rank_atms_by_distance(nearby_atms, location_point, 0.90)
        return []

    def _predict_lottery_scam(self, complaint: Complaint) -> list:
        """
        Rule 5: Lottery scams -> ATMs near post offices and banks
        """
        target_tags = ["post_office", "bank", "government_office"]

        # Get victim location
        victim_coords = self.db.execute(
            text("SELECT ST_X(victim_location) as lon, ST_Y(victim_location) as lat FROM complaints WHERE id = :id"),
            {"id": complaint.id}
        ).first()

        if not victim_coords:
            return []

        location_point = create_location_point(victim_coords.lat, victim_coords.lon)
        nearby_atms = find_nearby_atms(self.db, location_point, radius_km=6)

        filtered_atms = [
            atm for atm in nearby_atms
            if atm['tags'] and any(tag in atm['tags'] for tag in target_tags)
        ]

        return self._rank_atms_by_distance(filtered_atms, location_point, 0.80)

    def _predict_investment_fraud(self, complaint: Complaint) -> list:
        """
        Rule 6: Investment fraud -> ATMs in business districts and commercial areas
        """
        target_tags = ["business_district", "commercial", "it_park", "financial_center"]

        # Get victim location
        victim_coords = self.db.execute(
            text("SELECT ST_X(victim_location) as lon, ST_Y(victim_location) as lat FROM complaints WHERE id = :id"),
            {"id": complaint.id}
        ).first()

        if not victim_coords:
            return []

        location_point = create_location_point(victim_coords.lat, victim_coords.lon)
        nearby_atms = find_nearby_atms(self.db, location_point, radius_km=8)

        filtered_atms = [
            atm for atm in nearby_atms
            if atm['tags'] and any(tag in atm['tags'] for tag in target_tags)
        ]

        return self._rank_atms_by_distance(filtered_atms, location_point, 0.85)

    def _predict_default(self, complaint: Complaint) -> list:
        """
        Default rule: city-center ATMs
        """
        # Get victim location
        victim_coords = self.db.execute(
            text("SELECT ST_X(victim_location) as lon, ST_Y(victim_location) as lat FROM complaints WHERE id = :id"),
            {"id": complaint.id}
        ).first()

        if not victim_coords:
            return []

        # Find city center ATMs (hardcoded Delhi center for MVP)
        city_atms = self.db.query(HighRiskATM).filter(
            HighRiskATM.city == "Delhi"
        ).limit(5).all()

        result = []
        for atm in city_atms:
            # Get ATM coordinates
            atm_coords = self.db.execute(
                text("SELECT ST_X(location) as lon, ST_Y(location) as lat FROM high_risk_atms WHERE id = :id"),
                {"id": atm.id}
            ).first()

            if atm_coords:
                result.append({
                    'id': str(atm.id),
                    'name': atm.name,
                    'lat': atm_coords.lat,
                    'lon': atm_coords.lon,
                    'location': atm.location,
                    'confidence': 0.75
                })

        return result

    def _rank_atms_by_distance(self, atms: list, victim_location_point: str, base_confidence: float) -> list:
        """
        Rank ATMs by distance from victim and assign confidence scores
        """
        if not atms:
            return []

        # Get victim coordinates
        victim_coords = self.db.execute(
            text("SELECT ST_X(ST_GeomFromText(:location_point, 4326)) as lon, ST_Y(ST_GeomFromText(:location_point, 4326)) as lat"),
            {"location_point": victim_location_point}
        ).first()

        if not victim_coords:
            return []

        # Calculate distances and sort
        atms_with_distance = []
        for atm in atms:
            # Get ATM coordinates
            atm_coords = self.db.execute(
                text("SELECT ST_X(location) as lon, ST_Y(location) as lat FROM high_risk_atms WHERE id = :id"),
                {"id": atm['id']}
            ).first()

            if atm_coords:
                # Simple distance calculation (approximate)
                distance = math.sqrt((atm_coords.lon - victim_coords.lon)**2 + (atm_coords.lat - victim_coords.lat)**2) * 111  # Convert to km
                atms_with_distance.append((atm, distance))

        atms_with_distance.sort(key=lambda x: x[1])

        # Create ranked results (top 3)
        ranked_results = []
        for i, (atm, distance) in enumerate(atms_with_distance[:3]):
            # Get ATM coordinates for result
            atm_coords = self.db.execute(
                text("SELECT ST_X(location) as lon, ST_Y(location) as lat FROM high_risk_atms WHERE id = :id"),
                {"id": atm['id']}
            ).first()

            confidence = base_confidence - (i * 0.05)  # Reduce confidence for lower rankings
            ranked_results.append({
                'id': str(atm['id']),
                'name': atm['name'],
                'lat': atm_coords.lat if atm_coords else 0,
                'lon': atm_coords.lon if atm_coords else 0,
                'location': atm['location'],
                'confidence': max(confidence, 0.7)  # Minimum confidence threshold
            })

        return ranked_results

    def _deduplicate_predictions(self, predictions: list) -> list:
        """
        Remove duplicate ATM predictions based on location proximity
        """
        if not predictions:
            return []

        unique_predictions = []
        seen_locations = set()

        for prediction in predictions:
            # Round coordinates to 4 decimal places (~10m precision)
            lat_key = round(prediction['lat'], 4)
            lon_key = round(prediction['lon'], 4)
            location_key = (lat_key, lon_key)

            if location_key not in seen_locations:
                seen_locations.add(location_key)
                unique_predictions.append(prediction)

        return unique_predictions

    def _rank_by_confidence(self, predictions: list, complaint: Complaint) -> list:
        """
        Rank predictions by confidence score and apply additional scoring factors
        """
        if not predictions:
            return []

        # Apply additional scoring factors
        for prediction in predictions:
            base_confidence = prediction['confidence']

            # Boost confidence for high-amount scams
            if float(complaint.amount) > 100000:
                prediction['confidence'] = min(base_confidence + 0.05, 0.95)

            # Boost confidence for ATMs with multiple risk tags
            atm_record = self.db.query(HighRiskATM).filter(
                HighRiskATM.id == prediction['id']
            ).first()

            if atm_record and atm_record.tags and len(atm_record.tags) > 2:
                prediction['confidence'] = min(prediction['confidence'] + 0.03, 0.95)

        # Sort by confidence (descending)
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return predictions

    def _trigger_alerts(self, hotspots: list):
        """
        Trigger alert system for high-confidence predictions
        """
        from app.services.alert_service import AlertService

        alert_service = AlertService()
        for hotspot in hotspots:
            if hotspot.confidence >= 0.8:
                # Send alert
                alert_service.send_high_priority_alert(hotspot)

                # Log prediction for learning system
                self._log_prediction_for_learning(hotspot)

    def _log_prediction_for_learning(self, hotspot):
        """
        Log prediction details for future learning system improvement
        """
        log_entry = {
            'hotspot_id': str(hotspot.id),
            'prediction_confidence': hotspot.confidence,
            'prediction_time': hotspot.predicted_at,
            'location_name': hotspot.location_name
        }

        # In production, this would feed into a machine learning pipeline
        print(f"[LEARNING LOG] Prediction logged: {log_entry}")