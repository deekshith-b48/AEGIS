"""
Indian Cyber Crime Coordination Centre (I4C) Historical Data Integration
Simulates I4C historical crime data for pattern analysis and training
In production, this would integrate with the real I4C data warehouse
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
import os

logger = logging.getLogger(__name__)

class I4CIntegration:
    """
    Simulates I4C API integration for historical crime data analysis
    In production, this would connect to the official I4C data warehouse
    """

    def __init__(self):
        self.api_base_url = "https://i4c.gov.in"
        self.auth_token = os.getenv("I4C_AUTH_TOKEN", "mock_token_for_mvp")
        self.simulation_mode = True  # True for MVP

        # Modus Operandi patterns for different scam types
        self.modus_operandi = {
            'UPI_PHISHING': [
                'Fake UPI payment requests with urgent language',
                'QR code scams claiming payment required',
                'Impersonation of government officials demanding UPI payments',
                'Job offer scams requiring UPI registration fees',
                'Lottery prize scams requiring UPI verification payments'
            ],
            'FAKE_LOAN_APP': [
                'Illegal loan apps with processing fee demands',
                'High-interest digital lending without proper documentation',
                'Threats and harassment for loan repayment',
                'Access to contacts for pressure tactics',
                'Fake loan approval with advance payment requirements'
            ],
            'IMPERSONATION': [
                'Government official impersonation for fines/taxes',
                'Police/CBI impersonation for investigation payments',
                'Bank official impersonation for account verification',
                'Family member impersonation for emergency funds',
                'Business impersonation for advance payment scams'
            ],
            'LOTTERY_SCAM': [
                'Fake lottery winnings requiring processing fees',
                'International prize claims with tax payments',
                'Online gaming prizes with verification payments',
                'WhatsApp lottery messages with payment requirements',
                'Fake inheritance claims with legal fees'
            ],
            'INVESTMENT_FRAUD': [
                'High-return investment schemes with guaranteed profits',
                'Cryptocurrency investment scams with fake platforms',
                'Stock market manipulation schemes',
                'Real estate investment fraud with fake documents',
                'Ponzi schemes with referral bonuses'
            ]
        }

        # Criminal networks (simulated)
        self.criminal_networks = [
            'UPID_Syndicate_1', 'LoanApp_Ring_2', 'Phishing_Network_3',
            'Impersonation_Gang_4', 'Investment_Scam_5', 'International_Ring_6'
        ]

        # Geographic distribution of crimes
        self.crime_hotspots = [
            {'state': 'Maharashtra', 'cities': ['Mumbai', 'Pune', 'Nagpur'], 'weight': 0.25},
            {'state': 'Karnataka', 'cities': ['Bangalore', 'Mysore', 'Hubli'], 'weight': 0.20},
            {'state': 'Delhi', 'cities': ['New Delhi', 'Noida', 'Gurgaon'], 'weight': 0.18},
            {'state': 'Tamil Nadu', 'cities': ['Chennai', 'Coimbatore', 'Madurai'], 'weight': 0.15},
            {'state': 'Uttar Pradesh', 'cities': ['Lucknow', 'Kanpur', 'Ghaziabad'], 'weight': 0.12},
            {'state': 'West Bengal', 'cities': ['Kolkata', 'Howrah', 'Siliguri'], 'weight': 0.10}
        ]

    async def fetch_historical_data(self, months_back: int = 12) -> List[Dict[str, Any]]:
        """
        Fetch historical crime data from I4C for analysis

        Args:
            months_back: Number of months to look back

        Returns:
            List of historical crime records
        """
        if self.simulation_mode:
            return await self._simulate_historical_data(months_back)
        else:
            return await self._real_historical_data(months_back)

    async def _simulate_historical_data(self, months_back: int) -> List[Dict[str, Any]]:
        """
        Simulate I4C historical crime data for MVP
        """
        try:
            base_date = datetime.utcnow() - timedelta(days=months_back * 30)
            crime_records = []

            # Generate crime data for each month
            for month_offset in range(months_back):
                month_start = base_date + timedelta(days=month_offset * 30)
                month_end = month_start + timedelta(days=30)

                # Base crime volume varies by recent trends
                base_crime_volume = random.randint(800, 1200) + (month_offset * 50)  # Increasing trend

                # Distribute crimes across scam types
                for scam_type, mo_list in self.modus_operandi.items():
                    scam_count = int(base_crime_volume * random.uniform(0.15, 0.25))

                    for i in range(scam_count):
                        crime = await self._create_historical_crime_record(
                            scam_type, mo_list, month_start, month_end, i
                        )
                        crime_records.append(crime)

            # Store in database
            await self._store_crime_records(crime_records)

            logger.info(f"[I4C] Generated {len(crime_records)} historical crime records over {months_back} months")
            return crime_records

        except Exception as e:
            logger.error(f"[I4C] Error simulating historical data: {str(e)}")
            return []

    async def _create_historical_crime_record(self, scam_type: str, mo_list: List[str], month_start: datetime, month_end: datetime, index: int) -> Dict:
        """
        Create a single historical crime record
        """
        # Random date within the month
        days_offset = random.randint(0, 29)
        crime_date = month_start + timedelta(days=days_offset)

        # Select geographic location based on hotspot distribution
        location_data = self._select_crime_location()
        location = self._generate_location_for_hotspot(location_data)

        # Select modus operandi
        modus_operandi = random.choice(mo_list)

        # Determine if it's a repeat offender
        is_repeat_offender = random.random() < 0.25  # 25% repeat offenders

        # Assign to criminal network
        criminal_network = random.choice(self.criminal_networks)

        # Generate victim profile
        victim_profile = self._generate_victim_profile()

        # Determine outcome
        outcomes = ['arrest_made', 'case_pending', 'suspects_identified', 'under_investigation', 'case_closed']
        outcome_weights = [0.15, 0.35, 0.20, 0.20, 0.10]
        outcome = random.choices(outcomes, weights=outcome_weights)[0]

        # Calculate conviction rate based on outcome
        conviction_rates = {
            'arrest_made': random.uniform(0.6, 0.9),
            'case_pending': random.uniform(0.2, 0.5),
            'suspects_identified': random.uniform(0.3, 0.6),
            'under_investigation': random.uniform(0.1, 0.4),
            'case_closed': random.uniform(0.0, 0.3)
        }
        conviction_rate = conviction_rates[outcome]

        # Calculate severity score (1-10)
        severity_factors = {
            'financial_loss': random.uniform(10000, 1000000),  # ₹10K to ₹10L
            'victim_count': random.randint(1, 50),
            'sophistication': random.uniform(0.3, 1.0),
            'geographic_spread': random.uniform(0.1, 1.0),
            'repeat_offense': 1.0 if is_repeat_offender else 0.0
        }

        severity_score = min(10, (
            severity_factors['financial_loss'] / 100000 * 3 +  # Financial impact
            severity_factors['victim_count'] / 10 * 2 +  # Victim count
            severity_factors['sophistication'] * 2 +  # Sophistication
            severity_factors['geographic_spread'] * 2 +  # Geographic spread
            severity_factors['repeat_offense'] * 1  # Repeat offense
        ))

        return {
            'crime_id': f"I4C{crime_date.strftime('%Y%m')}{index:06}",
            'modus_operandi': modus_operandi,
            'repeat_offender': is_repeat_offender,
            'criminal_network': criminal_network,
            'location': location,
            'date_range_start': crime_date.date(),
            'date_range_end': (crime_date + timedelta(days=random.randint(1, 30))).date(),
            'scam_type': scam_type,
            'victim_profile': victim_profile,
            'outcome': outcome,
            'conviction_rate': conviction_rate,
            'severity_score': int(severity_score),
            'data_source': 'I4C_Historical',
            'imported_at': datetime.utcnow().isoformat()
        }

    def _select_crime_location(self) -> Dict:
        """
        Select crime location based on hotspot distribution
        """
        weights = [spot['weight'] for spot in self.crime_hotspots]
        selected = random.choices(self.crime_hotspots, weights=weights)[0]
        return selected

    def _generate_location_for_hotspot(self, hotspot_data: Dict) -> Dict[str, float]:
        """
        Generate location coordinates for the selected hotspot
        """
        city_coordinates = {
            'Mumbai': {'lat': 19.0760, 'lon': 72.8777},
            'Pune': {'lat': 18.5204, 'lon': 73.8567},
            'Nagpur': {'lat': 21.1458, 'lon': 79.0882},
            'Bangalore': {'lat': 12.9716, 'lon': 77.5946},
            'Mysore': {'lat': 12.2958, 'lon': 76.6394},
            'Hubli': {'lat': 15.3647, 'lon': 75.1240},
            'New Delhi': {'lat': 28.6139, 'lon': 77.2090},
            'Noida': {'lat': 28.5355, 'lon': 77.3910},
            'Gurgaon': {'lat': 28.4595, 'lon': 77.0266},
            'Chennai': {'lat': 13.0827, 'lon': 80.2707},
            'Coimbatore': {'lat': 11.0168, 'lon': 76.9558},
            'Madurai': {'lat': 9.9252, 'lon': 78.1198},
            'Lucknow': {'lat': 26.8467, 'lon': 80.9462},
            'Kanpur': {'lat': 26.4499, 'lon': 80.3319},
            'Ghaziabad': {'lat': 28.6692, 'lon': 77.4538},
            'Kolkata': {'lat': 22.5726, 'lon': 88.3639},
            'Howrah': {'lat': 22.5958, 'lon': 88.2636},
            'Siliguri': {'lat': 26.7100, 'lon': 88.4280}
        }

        city = random.choice(hotspot_data['cities'])
        base_coords = city_coordinates[city]

        # Add random offset within ~50km radius
        lat_offset = random.uniform(-0.45, 0.45)
        lon_offset = random.uniform(-0.45, 0.45)

        return {
            'lat': base_coords['lat'] + lat_offset,
            'lon': base_coords['lon'] + lon_offset,
            'city': city,
            'state': hotspot_data['state']
        }

    def _generate_victim_profile(self) -> Dict:
        """
        Generate anonymized victim profile
        """
        age_groups = ['18-25', '26-35', '36-45', '46-60', '60+']
        occupations = ['student', 'professional', 'business', 'retired', 'homemaker', 'unemployed']
        digital_literacy = ['low', 'medium', 'high']
        platforms = ['UPI', 'Bank Transfer', 'Cryptocurrency', 'Digital Wallets', 'Credit Card']

        return {
            'age_group': random.choice(age_groups),
            'occupation': random.choice(occupations),
            'digital_literacy': random.choice(digital_literacy),
            'platform_used': random.choice(platforms),
            'tech_savvy': random.choice([True, False]),
            'urban_rural': random.choice(['urban', 'rural', 'semi-urban'])
        }

    async def _store_crime_records(self, crime_records: List[Dict]) -> None:
        """
        Store crime records in database
        """
        try:
            with SessionLocal() as db:
                for record in crime_records:
                    query = text("""
                        INSERT INTO i4c_crime_data (
                            crime_id, modus_operandi, repeat_offender, criminal_network,
                            location, date_range_start, date_range_end, scam_type,
                            victim_profile, outcome, conviction_rate, severity_score,
                            data_source, imported_at
                        ) VALUES (
                            :crime_id, :modus_operandi, :repeat_offender, :criminal_network,
                            ST_GeomFromText('POINT(:lon :lat)', 4326),
                            :date_range_start, :date_range_end, :scam_type,
                            :victim_profile, :outcome, :conviction_rate, :severity_score,
                            :data_source, :imported_at
                        )
                        ON CONFLICT (crime_id) DO NOTHING
                    """)

                    location = record['location']
                    db.execute(query, {
                        'crime_id': record['crime_id'],
                        'modus_operandi': record['modus_operandi'],
                        'repeat_offender': record['repeat_offender'],
                        'criminal_network': record['criminal_network'],
                        'lat': location['lat'],
                        'lon': location['lon'],
                        'date_range_start': record['date_range_start'],
                        'date_range_end': record['date_range_end'],
                        'scam_type': record['scam_type'],
                        'victim_profile': json.dumps(record['victim_profile']),
                        'outcome': record['outcome'],
                        'conviction_rate': record['conviction_rate'],
                        'severity_score': record['severity_score'],
                        'data_source': record['data_source'],
                        'imported_at': record['imported_at']
                    })

                db.commit()
                logger.info(f"[I4C] Stored {len(crime_records)} crime records in database")

        except Exception as e:
            logger.error(f"[I4C] Error storing crime records: {str(e)}")

    async def _real_historical_data(self, months_back: int) -> List[Dict[str, Any]]:
        """
        Real I4C API integration (when simulation_mode = False)
        """
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }

        # I4C API endpoint structure (hypothetical)
        url = f"{self.api_base_url}/api/historical-crimes"
        params = {
            'months_back': months_back,
            'include_outcomes': True,
            'include_profiles': True
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"[I4C] Real fetch successful: {len(result.get('crimes', []))} records")
                    return result.get('crimes', [])
                else:
                    error_text = await response.text()
                    logger.error(f"[I4C] Real fetch failed: {response.status} - {error_text}")
                    return []

    async def analyze_crime_patterns(self, months_back: int = 6) -> Dict[str, Any]:
        """
        Analyze historical crime patterns for intelligence
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT scam_type, COUNT(*) as count,
                           AVG(severity_score) as avg_severity,
                           AVG(conviction_rate) as avg_conviction_rate,
                           COUNT(CASE WHEN repeat_offender = TRUE THEN 1 END) as repeat_count,
                           COUNT(CASE WHEN outcome = 'arrest_made' THEN 1 END) as arrest_count
                    FROM i4c_crime_data
                    WHERE date_range_start >= CURRENT_DATE - INTERVAL ':months_back months'
                    GROUP BY scam_type
                    ORDER BY count DESC
                """)

                results = db.execute(query, {'months_back': months_back}).fetchall()

                analysis = {
                    'total_crimes': 0,
                    'by_scam_type': {},
                    'by_severity': {'high': 0, 'medium': 0, 'low': 0},
                    'repeat_offender_rate': 0.0,
                    'arrest_rate': 0.0,
                    'avg_conviction_rate': 0.0,
                    'trending_modus_operandi': {},
                    'criminal_networks': {},
                    'geographic_hotspots': []
                }

                total_crimes = 0
                total_repeat = 0
                total_arrests = 0
                total_conviction_sum = 0

                for row in results:
                    scam_type = row.scam_type
                    count = row.count
                    avg_severity = float(row.avg_severity) if row.avg_severity else 0
                    avg_conviction = float(row.avg_conviction_rate) if row.avg_conviction_rate else 0
                    repeat_count = row.repeat_count
                    arrest_count = row.arrest_count

                    total_crimes += count
                    total_repeat += repeat_count
                    total_arrests += arrest_count
                    total_conviction_sum += avg_conviction * count

                    # Categorize by severity
                    if avg_severity >= 7:
                        analysis['by_severity']['high'] += count
                    elif avg_severity >= 4:
                        analysis['by_severity']['medium'] += count
                    else:
                        analysis['by_severity']['low'] += count

                    analysis['by_scam_type'][scam_type] = {
                        'count': count,
                        'avg_severity': avg_severity,
                        'avg_conviction_rate': avg_conviction,
                        'repeat_offender_count': repeat_count,
                        'arrest_count': arrest_count,
                        'repeat_rate': repeat_count / count if count > 0 else 0,
                        'arrest_rate': arrest_count / count if count > 0 else 0
                    }

                analysis['total_crimes'] = total_crimes
                analysis['repeat_offender_rate'] = total_repeat / total_crimes if total_crimes > 0 else 0
                analysis['arrest_rate'] = total_arrests / total_crimes if total_crimes > 0 else 0
                analysis['avg_conviction_rate'] = total_conviction_sum / total_crimes if total_crimes > 0 else 0

                # Get trending modus operandi
                analysis['trending_modus_operandi'] = await self._get_trending_modus_operandi(months_back)

                # Get criminal network analysis
                analysis['criminal_networks'] = await self._analyze_criminal_networks(months_back)

                # Get geographic hotspots
                analysis['geographic_hotspots'] = await self._identify_geographic_hotspots(months_back)

                logger.info(f"[I4C] Crime pattern analysis completed for {months_back} months")
                return analysis

        except Exception as e:
            logger.error(f"[I4C] Error analyzing crime patterns: {str(e)}")
            return {}

    async def _get_trending_modus_operandi(self, months_back: int) -> Dict[str, Any]:
        """
        Identify trending modus operandi patterns
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT modus_operandi, scam_type, COUNT(*) as count,
                           AVG(severity_score) as avg_severity
                    FROM i4c_crime_data
                    WHERE date_range_start >= CURRENT_DATE - INTERVAL ':months_back months'
                    GROUP BY modus_operandi, scam_type
                    ORDER BY count DESC
                    LIMIT 10
                """)

                results = db.execute(query, {'months_back': months_back}).fetchall()

                trending = {}
                for row in results:
                    trending[row.modus_operandi] = {
                        'scam_type': row.scam_type,
                        'count': row.count,
                        'avg_severity': float(row.avg_severity) if row.avg_severity else 0
                    }

                return trending

        except Exception as e:
            logger.error(f"[I4C] Error getting trending MO: {str(e)}")
            return {}

    async def _analyze_criminal_networks(self, months_back: int) -> Dict[str, Any]:
        """
        Analyze criminal network activities
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT criminal_network, scam_type, COUNT(*) as count,
                           COUNT(CASE WHEN repeat_offender = TRUE THEN 1 END) as repeat_count,
                           AVG(severity_score) as avg_severity,
                           AVG(conviction_rate) as avg_conviction_rate
                    FROM i4c_crime_data
                    WHERE date_range_start >= CURRENT_DATE - INTERVAL ':months_back months'
                    AND criminal_network IS NOT NULL
                    GROUP BY criminal_network, scam_type
                    ORDER BY count DESC
                """)

                results = db.execute(query, {'months_back': months_back}).fetchall()

                networks = {}
                for row in results:
                    network = row.criminal_network
                    if network not in networks:
                        networks[network] = {
                            'total_crimes': 0,
                            'by_scam_type': {},
                            'repeat_offenses': 0,
                            'avg_severity': 0,
                            'avg_conviction_rate': 0
                        }

                    networks[network]['total_crimes'] += row.count
                    networks[network]['repeat_offenses'] += row.repeat_count
                    networks[network]['by_scam_type'][row.scam_type] = row.count

                return networks

        except Exception as e:
            logger.error(f"[I4C] Error analyzing criminal networks: {str(e)}")
            return {}

    async def _identify_geographic_hotspots(self, months_back: int) -> List[Dict[str, Any]]:
        """
        Identify geographic hotspots of criminal activity
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT
                        ST_X(location) as lat,
                        ST_Y(location) as lon,
                        scam_type,
                        COUNT(*) as crime_count,
                        AVG(severity_score) as avg_severity,
                        COUNT(CASE WHEN repeat_offender = TRUE THEN 1 END) as repeat_count
                    FROM i4c_crime_data
                    WHERE date_range_start >= CURRENT_DATE - INTERVAL ':months_back months'
                    GROUP BY scam_type, ST_SnapToGrid(location, 0.1, 0.1)  -- Group by ~10km grid
                    HAVING COUNT(*) >= 3
                    ORDER BY crime_count DESC
                    LIMIT 20
                """)

                results = db.execute(query, {'months_back': months_back}).fetchall()

                hotspots = []
                for row in results:
                    hotspots.append({
                        'location': {
                            'lat': float(row.lat),
                            'lon': float(row.lon)
                        },
                        'scam_type': row.scam_type,
                        'crime_count': row.crime_count,
                        'avg_severity': float(row.avg_severity) if row.avg_severity else 0,
                        'repeat_offenses': row.repeat_count,
                        'risk_level': 'high' if row.crime_count >= 10 else 'medium' if row.crime_count >= 5 else 'low'
                    })

                return hotspots

        except Exception as e:
            logger.error(f"[I4C] Error identifying hotspots: {str(e)}")
            return []

    async def get_training_data_for_ml(self, months_back: int = 12) -> List[Dict[str, Any]]:
        """
        Get historical data formatted for ML model training
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT
                        scam_type,
                        modus_operandi,
                        ST_X(location) as lat,
                        ST_Y(location) as lon,
                        date_range_start,
                        date_range_end,
                        severity_score,
                        repeat_offender,
                        criminal_network,
                        victim_profile,
                        outcome,
                        conviction_rate
                    FROM i4c_crime_data
                    WHERE date_range_start >= CURRENT_DATE - INTERVAL ':months_back months'
                    ORDER BY date_range_start DESC
                """)

                results = db.execute(query, {'months_back': months_back}).fetchall()

                training_data = []
                for row in results:
                    training_data.append({
                        'scam_type': row.scam_type,
                        'modus_operandi': row.modus_operandi,
                        'location': {'lat': float(row.lat), 'lon': float(row.lon)},
                        'date_range_start': row.date_range_start.isoformat(),
                        'date_range_end': row.date_range_end.isoformat(),
                        'severity_score': row.severity_score,
                        'repeat_offender': row.repeat_offender,
                        'criminal_network': row.criminal_network,
                        'victim_profile': json.loads(row.victim_profile),
                        'outcome': row.outcome,
                        'conviction_rate': float(row.conviction_rate),
                        'duration_days': (row.date_range_end - row.date_range_start).days
                    })

                logger.info(f"[I4C] Retrieved {len(training_data)} records for ML training")
                return training_data

        except Exception as e:
            logger.error(f"[I4C] Error getting training data: {str(e)}")
            return []

# Singleton instance
i4c_integration = I4CIntegration()