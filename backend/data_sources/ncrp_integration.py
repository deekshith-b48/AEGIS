"""
National Cybercrime Reporting Portal (NCRP) Integration
Simulates the official NCRP API for MVP demonstration
In production, this would integrate with the real NCRP API endpoint
"""

import asyncio
import aiohttp
import json
import logging
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text
import hashlib
import ipaddress

logger = logging.getLogger(__name__)

class NCRPIntegration:
    """
    Simulates NCRP API integration for cybercrime reporting
    In production, this would connect to the official NCRP endpoint
    """

    def __init__(self):
        self.api_base_url = "https://cybercrime.gov.in"
        self.auth_token = os.getenv("NCRP_AUTH_TOKEN", "mock_token_for_mvp")
        self.simulation_mode = True  # True for MVP

    async def submit_complaint(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a complaint to NCRP system

        Args:
            complaint_data: {
                'scam_type': str,
                'amount': float,
                'victim_details': Dict,
                'digital_footprint': Dict
            }
        """
        if self.simulation_mode:
            return await self._simulate_ncrp_submission(complaint_data)
        else:
            return await self._real_ncrp_submission(complaint_data)

    async def _simulate_ncrp_submission(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate NCRP complaint submission for MVP
        """
        try:
            # Generate realistic NCRP complaint ID
            complaint_id = f"CR{datetime.datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"

            # Extract victim details
            victim_details = complaint_data.get('victim_details', {})

            # Generate anonymized location
            victim_location = complaint_data.get('victim_location')
            anonymized_location = self._apply_k_anonymity(victim_location)

            # Store in database
            with SessionLocal() as db:
                query = text("""
                    INSERT INTO ncrp_complaints (
                        complaint_id, scam_type, amount, victim_location,
                        anonymized_location, victim_age_group, victim_gender,
                        digital_footprint, ip_address, status
                    ) VALUES (
                        :complaint_id, :scam_type, :amount,
                        ST_GeomFromText('POINT(:lon :lat)', 4326),
                        ST_GeomFromText('POINT(:anon_lon :anon_lat)', 4326),
                        :age_group, :gender, :digital_footprint, :ip_address, 'received'
                    )
                    RETURNING id;
                """)

                result = db.execute(query, {
                    'complaint_id': complaint_id,
                    'scam_type': complaint_data['scam_type'],
                    'amount': complaint_data['amount'],
                    'lat': victim_location['lat'],
                    'lon': victim_location['lon'],
                    'anon_lat': anonymized_location['lat'],
                    'anon_lon': anonymized_location['lon'],
                    'age_group': victim_details.get('age_group', '18-25'),
                    'gender': victim_details.get('gender', 'prefer_not_to_say'),
                    'digital_footprint': json.dumps(complaint_data.get('digital_footprint', {})),
                    'ip_address': victim_details.get('ip_address', '0.0.0.0')
                })

                db.commit()
                db_complaint_id = result[0][0]

            # Simulate NCRP processing time
            await asyncio.sleep(random.uniform(0.5, 2.0))

            logger.info(f"[NCRP] Complaint {complaint_id} submitted successfully")

            return {
                'success': True,
                'complaint_id': complaint_id,
                'ncrp_id': db_complaint_id,
                'status': 'received',
                'message': 'Complaint submitted to NCRP successfully',
                'submission_time': datetime.utcnow().isoformat(),
                'anonymization_applied': True
            }

        except Exception as e:
            logger.error(f"[NCRP] Error submitting complaint: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to submit complaint to NCRP'
            }

    async def _real_ncrp_submission(self, complaint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Real NCRP API integration (when simulation_mode = False)
        """
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }

        # NCRP API endpoint structure (hypothetical)
        url = f"{self.api_base_url}/api/complaints"

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, json=complaint_data) as response:
                if response.status == 201:
                    result = await response.json()
                    logger.info(f"[NCRP] Real submission successful: {result}")
                    return {
                        'success': True,
                        **result
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"[NCRP] Real submission failed: {response.status} - {error_text}")
                    return {
                        'success': False,
                        'error': error_text,
                        'status_code': response.status
                    }
        """

    def _apply_k_anonymity(self, location: Dict[str, float]) -> Dict[str, float]:
        """
        Apply k-anonymity with k=50 (50 people in the same region)
        """
        # Add noise to maintain privacy while preserving spatial relationships
        # Approximately 100-200m noise (latitude/longitude degrees)
        lat_noise = random.uniform(-0.001, 0.001)  # ~100m
        lon_noise = random.uniform(-0.001, 0.001)  # ~100m

        return {
            'lat': location['lat'] + lat_noise,
            'lon': location['lon'] + lon_noise
        }

    async def get_complaint_status(self, complaint_id: str) -> Dict[str, Any]:
        """
        Get the status of a submitted complaint
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT complaint_id, status, created_at, updated_at
                    FROM ncrp_complaints
                    WHERE complaint_id = :complaint_id
                """)

                result = db.execute(query, {'complaint_id': complaint_id}).fetchone()

                if result:
                    return {
                        'success': True,
                        'complaint_id': result.complaint_id,
                        'status': result.status,
                        'created_at': result.created_at.isoformat(),
                        'updated_at': result.updated_at.isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Complaint not found',
                        'complaint_id': complaint_id
                    }

        except Exception as e:
            logger.error(f"[NCRP] Error getting complaint status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_complaints_batch(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a batch of complaints for processing
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT complaint_id, scam_type, amount,
                           ST_X(anonymized_location) as anon_lat,
                           ST_Y(anonymized_location) as anon_lon,
                           complaint_timestamp, status, created_at
                    FROM ncrp_complaints
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                    ORDER BY complaint_timestamp DESC
                    LIMIT :limit OFFSET :offset
                """)

                results = db.execute(query, {'limit': limit, 'offset': offset}).fetchall()

                complaints = []
                for row in results:
                    complaints.append({
                        'complaint_id': row.complaint_id,
                        'scam_type': row.scam_type,
                        'amount': float(row.amount),
                        'victim_location': {
                            'lat': float(row.anon_lat),
                            'lon': float(row.anon_lon)
                        },
                        'complaint_timestamp': row.complaint_timestamp.isoformat(),
                        'status': row.status,
                        'created_at': row.created_at.isoformat()
                    })

                logger.info(f"[NCRP] Retrieved {len(complaints)} complaints from database")
                return complaints

        except Exception as e:
            logger.error(f"[NCRP] Error getting complaints batch: {str(e)}")
            return []

    async def update_complaint_status(self, complaint_id: str, status: str) -> bool:
        """
        Update the status of a complaint
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    UPDATE ncrp_complaints
                    SET status = :status, updated_at = NOW()
                    WHERE complaint_id = :complaint_id
                """)

                result = db.execute(query, {'complaint_id': complaint_id, 'status': status})
                db.commit()

                success = result.rowcount > 0
                if success:
                    logger.info(f"[NCRP] Updated complaint {complaint_id} status to {status}")
                return success

        except Exception as e:
            logger.error(f"[NCRP] Error updating complaint status: {str(e)}")
            return False

    async def generate_mock_data(self, num_complaints: int = 50) -> List[Dict[str, Any]]:
        """
        Generate mock NCRP data for testing and development
        """
        mock_complaints = []

        scam_types = [
            'UPI_PHISHING', 'FAKE_LOAN_APP', 'IMPERSONATION',
            'LOTTERY_SCAM', 'INVESTMENT_FRAUD', 'ONLINE_SHOPPING_FRAUD'
        ]

        # Major Indian cities with coordinates
        cities = [
            {'name': 'Delhi', 'lat': 28.6139, 'lon': 77.2090},
            {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
            {'name': 'Bangalore', 'lat': 12.9716, 'lon': 77.5946},
            {'name': 'Chennai', 'lat': 13.0827, 'lon': 80.2707},
            {'name': 'Kolkata', 'lat': 22.5726, 'lon': 88.3639},
            {'name': 'Hyderabad', 'lat': 17.3850, 'lon': 78.4867},
            {'name': 'Pune', 'lat': 18.5204, 'lon': 73.8567},
            {'name': 'Ahmedabad', 'lat': 23.0225, 'lon': 72.5714},
            {'name': 'Jaipur', 'lat': 26.9124, 'lon': 75.7878},
            {'name': 'Lucknow', 'lat': 26.8467, 'lon': 80.9462}
        ]

        for i in range(num_complaints):
            city = random.choice(cities)

            # Add some randomness to coordinates within city
            lat_offset = random.uniform(-0.1, 0.1)
            lon_offset = random.uniform(-0.1, 0.1)

            mock_complaint = {
                'complaint_id': f"CR{datetime.datetime.now().strftime('%Y%m%d')}{i+1000:05}",
                'scam_type': random.choice(scam_types),
                'amount': random.choice([500, 1000, 5000, 10000, 25000, 50000, 100000]),
                'victim_location': {
                    'lat': city['lat'] + lat_offset,
                    'lon': city['lon'] + lon_offset
                },
                'victim_details': {
                    'age_group': random.choice(['18-25', '26-35', '36-45', '46-60', '60+']),
                    'gender': random.choice(['male', 'female', 'other']),
                    'ip_address': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
                },
                'digital_footprint': {
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'screen_resolution': '1920x1080',
                    'language': 'en-US,en;q=0.9',
                    'timezone': 'Asia/Kolkata'
                },
                'complaint_timestamp': (datetime.utcnow() - timedelta(hours=random.randint(0, 24))).isoformat(),
                'status': 'received'
            }

            mock_complaints.append(mock_complaint)

        logger.info(f"[NCRP] Generated {len(mock_complaints)} mock complaints")
        return mock_complaints

# Singleton instance
ncrp_integration = NCRPIntegration()