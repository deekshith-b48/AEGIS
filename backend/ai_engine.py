"""
Project AEGIS - AI Prediction Engine (MVP)
Pure Python rule-based system with no ML dependencies

Input: { fraud_type: str, amount: float, victim_lat: float, victim_lon: float }
Output: { hotspot_location: [lon, lat], location_name: str, confidence: float, time_window_mins: int }
"""

from sqlalchemy import text
from app.database import SessionLocal
import logging
from typing import Dict, List, Optional, Tuple
import math

logger = logging.getLogger(__name__)

class AEGISPredictionEngine:
    """
    Rule-based AI prediction engine for Project AEGIS MVP.
    Implements exact specifications from greenfield requirements.
    """

    def __init__(self):
        self.confidence_threshold = 0.8
        self.default_time_window = 45  # minutes as per specification

        # Rule weights for learning simulation (start at 1.0)
        self.rule_weights = {
            'fake_loan_app': 1.0,
            'high_value': 1.0,
            'upi_phishing': 1.0,
            'fallback': 1.0
        }

        self.system_accuracy = 0.58  # Starting accuracy for MVP

    def predict_hotspot(self, complaint: Dict) -> Optional[Dict]:
        """
        Main prediction function implementing exact greenfield specification.

        Args:
            complaint: {
                'fraud_type': str,
                'amount': float,
                'victim_lat': float,
                'victim_lon': float
            }

        Returns:
            Dict with hotspot prediction or None if confidence < 0.8
        """
        try:
            # Extract complaint data
            fraud_type = complaint.get('fraud_type', '').upper()
            amount = float(complaint.get('amount', 0))
            victim_lat = float(complaint.get('victim_lat', 0))
            victim_lon = float(complaint.get('victim_lon', 0))

            logger.info(f"Processing complaint: {fraud_type}, amount: {amount}, location: {victim_lat}, {victim_lon}")

            # Apply rules in priority order
            prediction = None

            # Rule 1: Fake Loan App -> Highway/Bus Stand ATMs (confidence = 0.85)
            if fraud_type == 'FAKE_LOAN_APP':
                prediction = self._predict_fake_loan_app(victim_lat, victim_lon)
                if prediction:
                    prediction['confidence'] = 0.85 * self.rule_weights['fake_loan_app']
                    prediction['rule_applied'] = 'fake_loan_app'

            # Rule 2: High-Value Loss (amount > 50,000) -> ATMs within 2000 meters (confidence = 0.85)
            if amount > 50000 and not prediction:
                prediction = self._predict_high_value(victim_lat, victim_lon)
                if prediction:
                    prediction['confidence'] = 0.85 * self.rule_weights['high_value']
                    prediction['rule_applied'] = 'high_value'

            # Rule 3: UPI Phishing -> Railway ATMs (confidence = 0.85)
            if fraud_type == 'UPI_PHISHING' and not prediction:
                prediction = self._predict_upi_phishing(victim_lat, victim_lon)
                if prediction:
                    prediction['confidence'] = 0.85 * self.rule_weights['upi_phishing']
                    prediction['rule_applied'] = 'upi_phishing'

            # Rule 4: Fallback -> Nearest ATM in same city (confidence = 0.75)
            if not prediction:
                prediction = self._predict_fallback(victim_lat, victim_lon)
                if prediction:
                    prediction['confidence'] = 0.75 * self.rule_weights['fallback']
                    prediction['rule_applied'] = 'fallback'

            # Apply confidence threshold
            if prediction and prediction['confidence'] >= self.confidence_threshold:
                prediction['time_window_mins'] = self.default_time_window
                logger.info(f"Hotspot predicted: {prediction['location_name']}, confidence: {prediction['confidence']:.2f}")
                return prediction
            else:
                logger.info(f"No high-confidence prediction (threshold: {self.confidence_threshold})")
                return None

        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return None

    def _predict_fake_loan_app(self, victim_lat: float, victim_lon: float) -> Optional[Dict]:
        """
        Rule: Find nearest ATM with 'highway' or 'bus_stand' tags.
        """
        with SessionLocal() as db:
            try:
                # Query ATMs with highway or bus_stand tags
                query = text("""
                    SELECT id, name, location, city, tags,
                           ST_Distance(location, ST_GeomFromText(:point, 4326)) as distance_meters
                    FROM high_risk_atms
                    WHERE tags && ARRAY['highway', 'bus_stand']
                    ORDER BY distance_meters
                    LIMIT 1
                """)

                point = f'POINT({victim_lon} {victim_lat})'
                result = db.execute(query, {"point": point}).fetchone()

                if result:
                    return self._format_prediction(result, victim_lat, victim_lon)
                else:
                    logger.warning("No highway/bus_stand ATMs found for fake loan app rule")
                    return None

            except Exception as e:
                logger.error(f"Fake loan app prediction error: {str(e)}")
                return None

    def _predict_high_value(self, victim_lat: float, victim_lon: float) -> Optional[Dict]:
        """
        Rule: Find nearest ATM within 2000 meters for high-value complaints.
        """
        with SessionLocal() as db:
            try:
                # Query ATMs within 2000 meters
                query = text("""
                    SELECT id, name, location, city, tags,
                           ST_Distance(location, ST_GeomFromText(:point, 4326)) as distance_meters
                    FROM high_risk_atms
                    WHERE ST_DWithin(location, ST_GeomFromText(:point, 4326), 2000)
                    ORDER BY distance_meters
                    LIMIT 1
                """)

                point = f'POINT({victim_lon} {victim_lat})'
                result = db.execute(query, {"point": point}).fetchone()

                if result:
                    return self._format_prediction(result, victim_lat, victim_lon)
                else:
                    logger.warning("No ATMs found within 2000m for high-value rule")
                    return None

            except Exception as e:
                logger.error(f"High-value prediction error: {str(e)}")
                return None

    def _predict_upi_phishing(self, victim_lat: float, victim_lon: float) -> Optional[Dict]:
        """
        Rule: Find nearest ATM with 'railway' tags.
        """
        with SessionLocal() as db:
            try:
                # Query ATMs with railway tags
                query = text("""
                    SELECT id, name, location, city, tags,
                           ST_Distance(location, ST_GeomFromText(:point, 4326)) as distance_meters
                    FROM high_risk_atms
                    WHERE tags && ARRAY['railway']
                    ORDER BY distance_meters
                    LIMIT 1
                """)

                point = f'POINT({victim_lon} {victim_lat})'
                result = db.execute(query, {"point": point}).fetchone()

                if result:
                    return self._format_prediction(result, victim_lat, victim_lon)
                else:
                    logger.warning("No railway ATMs found for UPI phishing rule")
                    return None

            except Exception as e:
                logger.error(f"UPI phishing prediction error: {str(e)}")
                return None

    def _predict_fallback(self, victim_lat: float, victim_lon: float) -> Optional[Dict]:
        """
        Fallback: Return nearest ATM in same city.
        """
        with SessionLocal() as db:
            try:
                # First, find the nearest city
                city_query = text("""
                    SELECT city, ST_Distance(location, ST_GeomFromText(:point, 4326)) as distance_meters
                    FROM high_risk_atms
                    GROUP BY city
                    ORDER BY distance_meters
                    LIMIT 1
                """)

                point = f'POINT({victim_lon} {victim_lat})'
                city_result = db.execute(city_query, {"point": point}).fetchone()

                if not city_result:
                    logger.warning("No cities found for fallback rule")
                    return None

                nearest_city = city_result.city

                # Find nearest ATM in that city
                atm_query = text("""
                    SELECT id, name, location, city, tags,
                           ST_Distance(location, ST_GeomFromText(:point, 4326)) as distance_meters
                    FROM high_risk_atms
                    WHERE city = :city
                    ORDER BY distance_meters
                    LIMIT 1
                """)

                result = db.execute(atm_query, {"point": point, "city": nearest_city}).fetchone()

                if result:
                    return self._format_prediction(result, victim_lat, victim_lon)
                else:
                    logger.warning(f"No ATMs found in city {nearest_city} for fallback rule")
                    return None

            except Exception as e:
                logger.error(f"Fallback prediction error: {str(e)}")
                return None

    def _format_prediction(self, atm_result, victim_lat: float, victim_lon: float) -> Dict:
        """
        Format ATM database result into prediction format.
        """
        # Extract coordinates from PostGIS geography
        coords_query = text("""
            SELECT ST_X(location) as lon, ST_Y(location) as lat
            FROM high_risk_atms
            WHERE id = :id
        """)

        with SessionLocal() as db:
            coords = db.execute(coords_query, {"id": atm_result.id}).fetchone()

            if not coords:
                logger.error(f"Could not extract coordinates for ATM {atm_result.id}")
                return None

            return {
                'hotspot_location': [float(coords.lon), float(coords.lat)],
                'location_name': str(atm_result.name),
                'distance_meters': float(atm_result.distance_meters),
                'city': str(atm_result.city),
                'tags': atm_result.tags if atm_result.tags else []
            }

    def update_rule_weights(self, feedback_type: str):
        """
        Update rule weights based on LEA feedback for learning simulation.

        Args:
            feedback_type: 'confirmed' or 'false'
        """
        weight_change = 0.05  # 5% adjustment

        if feedback_type == 'confirmed':
            # Increase weights
            for rule in self.rule_weights:
                self.rule_weights[rule] = min(2.0, self.rule_weights[rule] + weight_change)
        elif feedback_type == 'false':
            # Decrease weights
            for rule in self.rule_weights:
                self.rule_weights[rule] = max(0.1, self.rule_weights[rule] - weight_change)

        # Update system accuracy (mock calculation for MVP)
        if feedback_type == 'confirmed':
            self.system_accuracy = min(0.95, self.system_accuracy + 0.01)
        elif feedback_type == 'false':
            self.system_accuracy = max(0.10, self.system_accuracy - 0.01)

        logger.info(f"Updated rule weights: {self.rule_weights}")
        logger.info(f"System accuracy: {self.system_accuracy:.2f}")

    def get_system_accuracy(self) -> float:
        """Get current system accuracy percentage."""
        return self.system_accuracy

# Singleton instance for the application
prediction_engine = AEGISPredictionEngine()