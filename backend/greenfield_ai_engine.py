"""
Project AEGIS Greenfield AI Engine
Pure Python rule-based prediction system with no ML dependencies

Input: { fraud_type: str, amount: float, victim_lat: float, victim_lon: float }
Output: { hotspot_location: [lon, lat], location_name: str, confidence: float, time_window_mins: int }

Rules:
1. Fake Loan App -> Highway/Bus Stand ATMs (confidence = 0.85)
2. High-Value Loss (amount > 50,000) -> ATMs within 2000 meters (confidence = 0.85)
3. UPI Phishing -> Railway ATMs (confidence = 0.85)
4. Fallback -> Nearest ATM in same city (confidence = 0.75)

Only ONE hotspot generated per complaint (top prediction).
"""

from sqlalchemy import text
from app.database import SessionLocal
import logging
from typing import Dict, Optional, Tuple
import math

logger = logging.getLogger(__name__)

class GreenfieldAEGISEngine:
    """
    Rule-based AI prediction engine for Project AEGIS greenfield implementation.
    Follows exact specifications with no ML dependencies.
    """

    def __init__(self):
        self.confidence_threshold = 0.8
        self.default_time_window = 45  # minutes as per specification

        # Initial rule weights for learning simulation
        self.rule_weights = {
            'fake_loan_app': 1.0,
            'high_value': 1.0,
            'upi_phishing': 1.0,
            'fallback': 1.0
        }

        # System accuracy starting point
        self.system_accuracy = 0.58

    def predict_hotspot(self, complaint: Dict) -> Optional[Dict]:
        """
        Main prediction function following exact greenfield specification.

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

            logger.info(f"[AI ENGINE] Processing complaint: {fraud_type}, amount: {amount}, location: {victim_lat}, {victim_lon}")

            prediction = None

            # Rule 1: Fake Loan App -> Highway/Bus Stand ATMs (confidence = 0.85)
            if fraud_type == 'FAKE_LOAN_APP':
                prediction = self._predict_fake_loan_app(victim_lat, victim_lon)
                if prediction:
                    prediction['confidence'] = 0.85 * self.rule_weights['fake_loan_app']
                    prediction['rule_applied'] = 'fake_loan_app'
                    logger.info(f"[AI ENGINE] Rule 1 applied: Fake Loan App -> {prediction['location_name']}")

            # Rule 2: High-Value Loss (amount > 50,000) -> ATMs within 2000 meters (confidence = 0.85)
            if amount > 50000 and not prediction:
                prediction = self._predict_high_value(victim_lat, victim_lon)
                if prediction:
                    prediction['confidence'] = 0.85 * self.rule_weights['high_value']
                    prediction['rule_applied'] = 'high_value'
                    logger.info(f"[AI ENGINE] Rule 2 applied: High Value -> {prediction['location_name']}")

            # Rule 3: UPI Phishing -> Railway ATMs (confidence = 0.85)
            if fraud_type == 'UPI_PHISHING' and not prediction:
                prediction = self._predict_upi_phishing(victim_lat, victim_lon)
                if prediction:
                    prediction['confidence'] = 0.85 * self.rule_weights['upi_phishing']
                    prediction['rule_applied'] = 'upi_phishing'
                    logger.info(f"[AI ENGINE] Rule 3 applied: UPI Phishing -> {prediction['location_name']}")

            # Rule 4: Fallback -> Nearest ATM in same city (confidence = 0.75)
            if not prediction:
                prediction = self._predict_fallback(victim_lat, victim_lon)
                if prediction:
                    prediction['confidence'] = 0.75 * self.rule_weights['fallback']
                    prediction['rule_applied'] = 'fallback'
                    logger.info(f"[AI ENGINE] Rule 4 applied: Fallback -> {prediction['location_name']}")

            # Apply confidence threshold (only generate hotspot if confidence >= 0.8)
            if prediction and prediction['confidence'] >= self.confidence_threshold:
                prediction['time_window_mins'] = self.default_time_window
                logger.info(f"[AI ENGINE] HOTSPOST GENERATED: {prediction['location_name']} (confidence: {prediction['confidence']:.2f})")
                return prediction
            else:
                logger.info(f"[AI ENGINE] NO HOTSPOT: confidence {prediction['confidence'] if prediction else 0:.2f} < threshold {self.confidence_threshold}")
                return None

        except Exception as e:
            logger.error(f"[AI ENGINE] Prediction error: {str(e)}")
            return None

    def _predict_fake_loan_app(self, victim_lat: float, victim_lon: float) -> Optional[Dict]:
        """
        Rule 1: Find nearest ATM where 'highway' = ANY(tags) OR 'bus_stand' = ANY(tags)
        """
        with SessionLocal() as db:
            try:
                # Query ATMs with highway or bus_stand tags using exact specification
                query = text("""
                    SELECT id, name, location, city, tags,
                           ST_Distance(location, ST_GeomFromText(:point, 4326)) as distance_meters
                    FROM high_risk_atms
                    WHERE 'highway' = ANY(tags) OR 'bus_stand' = ANY(tags)
                    ORDER BY distance_meters
                    LIMIT 1
                """)

                point = f'POINT({victim_lon} {victim_lat})'
                result = db.execute(query, {"point": point}).fetchone()

                if result:
                    logger.info(f"[AI ENGINE] Fake Loan App: Found {result.name} at {result.distance_meters:.0f}m")
                    return self._format_prediction(result, victim_lat, victim_lon)
                else:
                    logger.warning("[AI ENGINE] Fake Loan App: No highway/bus_stand ATMs found")
                    return None

            except Exception as e:
                logger.error(f"[AI ENGINE] Fake Loan App prediction error: {str(e)}")
                return None

    def _predict_high_value(self, victim_lat: float, victim_lon: float) -> Optional[Dict]:
        """
        Rule 2: Find all ATMs within 2000 meters of victim, return closest
        """
        with SessionLocal() as db:
            try:
                # Query ATMs within 2000 meters using ST_DWithin
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
                    logger.info(f"[AI ENGINE] High Value: Found {result.name} at {result.distance_meters:.0f}m (within 2000m)")
                    return self._format_prediction(result, victim_lat, victim_lon)
                else:
                    logger.warning("[AI ENGINE] High Value: No ATMs found within 2000m")
                    return None

            except Exception as e:
                logger.error(f"[AI ENGINE] High Value prediction error: {str(e)}")
                return None

    def _predict_upi_phishing(self, victim_lat: float, victim_lon: float) -> Optional[Dict]:
        """
        Rule 3: Find nearest ATM where 'railway' = ANY(tags)
        """
        with SessionLocal() as db:
            try:
                # Query ATMs with railway tags using exact specification
                query = text("""
                    SELECT id, name, location, city, tags,
                           ST_Distance(location, ST_GeomFromText(:point, 4326)) as distance_meters
                    FROM high_risk_atms
                    WHERE 'railway' = ANY(tags)
                    ORDER BY distance_meters
                    LIMIT 1
                """)

                point = f'POINT({victim_lon} {victim_lat})'
                result = db.execute(query, {"point": point}).fetchone()

                if result:
                    logger.info(f"[AI ENGINE] UPI Phishing: Found {result.name} at {result.distance_meters:.0f}m")
                    return self._format_prediction(result, victim_lat, victim_lon)
                else:
                    logger.warning("[AI ENGINE] UPI Phishing: No railway ATMs found")
                    return None

            except Exception as e:
                logger.error(f"[AI ENGINE] UPI Phishing prediction error: {str(e)}")
                return None

    def _predict_fallback(self, victim_lat: float, victim_lon: float) -> Optional[Dict]:
        """
        Rule 4: Return nearest ATM in same city
        """
        with SessionLocal() as db:
            try:
                # Use the custom function to find nearest ATM in same city
                query = text("""
                    SELECT * FROM find_nearest_city_atm(:victim_lat, :victim_lon)
                    LIMIT 1
                """)

                result = db.execute(query, {
                    "victim_lat": victim_lat,
                    "victim_lon": victim_lon
                }).fetchone()

                if result:
                    logger.info(f"[AI ENGINE] Fallback: Found {result.name} in {result.city} at {result.distance_meters:.0f}m")
                    return self._format_prediction(result, victim_lat, victim_lon)
                else:
                    logger.warning("[AI ENGINE] Fallback: No ATMs found in any city")
                    return None

            except Exception as e:
                logger.error(f"[AI ENGINE] Fallback prediction error: {str(e)}")
                return None

    def _format_prediction(self, atm_result, victim_lat: float, victim_lon: float) -> Dict:
        """
        Format ATM database result into exact specification output format.

        Returns:
            {
                "hotspot_location": [lon, lat],
                "location_name": "HDFC ATM - CSMT",
                "confidence": float,
                "time_window_mins": int
            }
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
                logger.error(f"[AI ENGINE] Could not extract coordinates for ATM {atm_result.id}")
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
        weight_change = 0.05  # 5% adjustment per specification

        if feedback_type == 'confirmed':
            # Increase all rule weights by 5%
            for rule in self.rule_weights:
                self.rule_weights[rule] = min(2.0, self.rule_weights[rule] + weight_change)
            # Update system accuracy (mock calculation)
            self.system_accuracy = min(0.95, self.system_accuracy + 0.01)
            logger.info(f"[AI ENGINE] Rule weights increased by 5% after confirmed feedback")

        elif feedback_type == 'false':
            # Decrease all rule weights by 5%
            for rule in self.rule_weights:
                self.rule_weights[rule] = max(0.1, self.rule_weights[rule] - weight_change)
            # Update system accuracy (mock calculation)
            self.system_accuracy = max(0.10, self.system_accuracy - 0.01)
            logger.info(f"[AI ENGINE] Rule weights decreased by 5% after false feedback")

        logger.info(f"[AI ENGINE] Updated rule weights: {self.rule_weights}")
        logger.info(f"[AI ENGINE] System accuracy: {self.system_accuracy:.2f}")

    def get_system_accuracy(self) -> float:
        """Get current system accuracy percentage."""
        return self.system_accuracy

    def get_rule_weights(self) -> Dict:
        """Get current rule weights for dashboard display."""
        return self.rule_weights.copy()

# Singleton instance for the application
greenfield_prediction_engine = GreenfieldAEGISEngine()