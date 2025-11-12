"""
Bank Transaction Logs Integration via CFCFRMS
Simulates bank transaction data from Cyber Crime Reporting Portal of Banks
In production, this would integrate with the real CFCFRMS API endpoint
"""

import asyncio
import aiohttp
import json
import logging
import uuid
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text
import os

logger = logging.getLogger(__name__)

class BankIntegration:
    """
    Simulates CFCFRMS API integration for bank transaction monitoring
    In production, this would connect to the official CFCFRMS endpoint
    """

    def __init__(self):
        self.api_base_url = "https://cfcfrms.gov.in"
        self.auth_token = os.getenv("CFCFRMS_AUTH_TOKEN", "mock_token_for_mvp")
        self.simulation_mode = True  # True for MVP

        # Major Indian banks for simulation
        self.banks = [
            {"code": "SBIN", "name": "State Bank of India"},
            {"code": "HDFC", "name": "HDFC Bank"},
            {"code": "ICIC", "name": "ICICI Bank"},
            {"code": "AXIS", "name": "Axis Bank"},
            {"code": "PUNB", "name": "Punjab National Bank"},
            {"code": "UBIN", "name": "Union Bank of India"},
            {"code": "BKID", "name": "Bank of India"},
            {"code": "CORP", "name": "Corporation Bank"},
            {"code": "MAHA", "name": "Bank of Maharashtra"},
            {"code": "CANR", "name": "Canara Bank"}
        ]

        # Transaction types
        self.transaction_types = [
            {"type": "CASH_WITHDRAWAL", "weight": 0.3},
            {"type": "BALANCE_ENQUIRY", "weight": 0.2},
            {"type": "MINI_STATEMENT", "weight": 0.15},
            {"type": "PIN_CHANGE", "weight": 0.1},
            {"type": "FUND_TRANSFER", "weight": 0.15},
            {"type": "MOBILE_RECHARGE", "weight": 0.1}
        ]

    async def fetch_transaction_logs(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Fetch transaction logs from CFCFRMS for the last N hours

        Args:
            hours_back: Number of hours to look back

        Returns:
            List of transaction records
        """
        if self.simulation_mode:
            return await self._simulate_transaction_logs(hours_back)
        else:
            return await self._real_transaction_logs(hours_back)

    async def _simulate_transaction_logs(self, hours_back: int) -> List[Dict[str, Any]]:
        """
        Simulate CFCFRMS transaction logs for MVP
        """
        try:
            base_time = datetime.utcnow() - timedelta(hours=hours_back)
            transactions = []

            # Generate transactions for each bank
            for bank in self.banks:
                # Base transaction volume varies by bank size
                base_volume = random.randint(500, 2000) if bank["code"] in ["SBIN", "HDFC", "ICIC"] else random.randint(100, 500)

                # Simulate suspicious transactions (5-15% of total)
                suspicious_count = int(base_volume * random.uniform(0.05, 0.15))
                normal_count = base_volume - suspicious_count

                # Generate suspicious transactions
                suspicious_txns = await self._generate_suspicious_transactions(
                    bank, base_time, suspicious_count, hours_back
                )
                transactions.extend(suspicious_txns)

                # Generate normal transactions
                normal_txns = await self._generate_normal_transactions(
                    bank, base_time, normal_count, hours_back
                )
                transactions.extend(normal_txns)

            # Sort by timestamp
            transactions.sort(key=lambda x: x['timestamp'])

            # Store in database
            await self._store_transactions(transactions)

            logger.info(f"[CFCFRMS] Generated {len(transactions)} transaction logs from {len(self.banks)} banks")
            return transactions

        except Exception as e:
            logger.error(f"[CFCFRMS] Error simulating transaction logs: {str(e)}")
            return []

    async def _generate_suspicious_transactions(self, bank: Dict, base_time: datetime, count: int, hours_back: int) -> List[Dict]:
        """
        Generate suspicious transaction patterns
        """
        transactions = []

        for i in range(count):
            # Distribute transactions across the time window
            hour_offset = random.randint(0, hours_back - 1)
            minute_offset = random.randint(0, 59)
            timestamp = base_time + timedelta(hours=hour_offset, minutes=minute_offset)

            # Select transaction type (ATM transactions are more suspicious)
            trans_type = random.choices(
                self.transaction_types,
                weights=[0.4, 0.15, 0.1, 0.05, 0.2, 0.1]  # Higher weight for ATM types
            )[0]

            txn = await self._create_suspicious_transaction(bank, base_time, trans_type, hour_offset, i)
            transactions.append(txn)

        return transactions

    async def _create_suspicious_transaction(self, bank: Dict, base_time: datetime, trans_type: Dict, hour_offset: int, index: int) -> Dict:
        """
        Create a single suspicious transaction with fraud signals
        """
        # Suspicious amounts (round figures, typical of fraud)
        suspicious_amounts = [1000, 2000, 5000, 10000, 20000, 50000, 100000]
        amount = random.choice(suspicious_amounts)

        # Generate location near high-risk areas
        location = self._generate_suspicious_location()

        # Create hashed account identifier
        account_hash = hashlib.sha256(f"{bank['code']}_suspicious_{index}_{hour_offset}".encode()).hexdigest()[:32]

        # Create merchant hash for digital transactions
        merchant_hash = hashlib.sha256(f"suspicious_merchant_{index}".encode()).hexdigest()[:32] if trans_type["type"] != "CASH_WITHDRAWAL" else None

        # Generate fraud signals
        fraud_signals = {
            'unusual_amount': amount in suspicious_amounts,
            'new_account': random.random() < 0.1,  # 10% chance
            'multiple_attempts': random.random() < 0.15,  # 15% chance
            'off_hours': hour_offset in [0, 1, 2, 3, 4, 5, 22, 23],  # Late night/early morning
            'high_velocity': random.random() < 0.05,  # 5% chance
            'geolocation_mismatch': random.random() < 0.08,  # 8% chance
            'suspicious_pattern': random.random() < 0.12,  # 12% chance
            'atm_location_anomaly': trans_type["type"] == "CASH_WITHDRAWAL" and random.random() < 0.2
        }

        # Calculate risk score
        risk_score = self._calculate_risk_score(fraud_signals, amount, trans_type["type"])

        return {
            'transaction_id': f"TXN{bank['code']}{datetime.utcnow().strftime('%Y%m%d')}{index:06}",
            'bank_code': bank['code'],
            'transaction_type': trans_type["type"],
            'amount': amount,
            'account_hash': account_hash,
            'upi_id': f"fake{random.randint(100000, 999999)}@ybl" if trans_type["type"] != "CASH_WITHDRAWAL" else None,
            'merchant_hash': merchant_hash,
            'location': location,
            'risk_score': risk_score,
            'fraud_signals': fraud_signals,
            'is_suspicious': True,
            'timestamp': (base_time + timedelta(hours=hour_offset, minutes=random.randint(0, 59))).isoformat(),
            'batch_id': str(uuid.uuid4())
        }

    async def _generate_normal_transactions(self, bank: Dict, base_time: datetime, count: int, hours_back: int) -> List[Dict]:
        """
        Generate normal transaction patterns
        """
        transactions = []

        for i in range(count):
            # Distribute transactions across normal business hours
            hour_offset = random.choices(
                list(range(hours_back)),
                weights=[0.02 if h in [0, 1, 2, 3, 4, 5, 22, 23] else 0.12 for h in range(hours_back)]
            )[0]

            timestamp = base_time + timedelta(hours=hour_offset, minutes=random.randint(0, 59))
            trans_type = random.choices(self.transaction_types, weights=[t["weight"] for t in self.transaction_types])[0]

            txn = await self._create_normal_transaction(bank, base_time, trans_type, hour_offset, i)
            transactions.append(txn)

        return transactions

    async def _create_normal_transaction(self, bank: Dict, base_time: datetime, trans_type: Dict, hour_offset: int, index: int) -> Dict:
        """
        Create a single normal transaction
        """
        # Normal amounts (varied, not round figures)
        amount = round(random.uniform(100, 10000), -1) if trans_type["type"] == "CASH_WITHDRAWAL" else round(random.uniform(50, 5000), -1)

        # Generate location across normal areas
        location = self._generate_normal_location()

        # Create hashed account identifier
        account_hash = hashlib.sha256(f"{bank['code']}_normal_{index}_{hour_offset}".encode()).hexdigest()[:32]

        # Create merchant hash for digital transactions
        merchant_hash = hashlib.sha256(f"normal_merchant_{index}".encode()).hexdigest()[:32] if trans_type["type"] != "CASH_WITHDRAWAL" else None

        # Normal transaction signals (mostly false)
        fraud_signals = {
            'unusual_amount': False,
            'new_account': random.random() < 0.01,  # 1% chance
            'multiple_attempts': random.random() < 0.02,  # 2% chance
            'off_hours': False,
            'high_velocity': random.random() < 0.01,  # 1% chance
            'geolocation_mismatch': random.random() < 0.01,  # 1% chance
            'suspicious_pattern': False,
            'atm_location_anomaly': False
        }

        # Calculate low risk score
        risk_score = self._calculate_risk_score(fraud_signals, amount, trans_type["type"])

        return {
            'transaction_id': f"TXN{bank['code']}{datetime.utcnow().strftime('%Y%m%d')}{index:06}",
            'bank_code': bank['code'],
            'transaction_type': trans_type["type"],
            'amount': amount,
            'account_hash': account_hash,
            'upi_id': f"user{random.randint(100000, 999999)}@ybl" if trans_type["type"] != "CASH_WITHDRAWAL" else None,
            'merchant_hash': merchant_hash,
            'location': location,
            'risk_score': risk_score,
            'fraud_signals': fraud_signals,
            'is_suspicious': False,
            'timestamp': (base_time + timedelta(hours=hour_offset, minutes=random.randint(0, 59))).isoformat(),
            'batch_id': str(uuid.uuid4())
        }

    def _generate_suspicious_location(self) -> Dict[str, float]:
        """
        Generate location near suspicious areas (high-risk zones)
        """
        # High-risk locations (near transport hubs, highways)
        suspicious_locations = [
            {"lat": 28.6139, "lon": 77.2090},  # Delhi
            {"lat": 19.0760, "lon": 72.8777},  # Mumbai
            {"lat": 12.9716, "lon": 77.5946},  # Bangalore
            {"lat": 13.0827, "lon": 80.2707},  # Chennai
            {"lat": 22.5726, "lon": 88.3639},  # Kolkata
        ]

        base = random.choice(suspicious_locations)
        # Add small offset
        return {
            'lat': base['lat'] + random.uniform(-0.05, 0.05),
            'lon': base['lon'] + random.uniform(-0.05, 0.05)
        }

    def _generate_normal_location(self) -> Dict[str, float]:
        """
        Generate location across normal areas
        """
        # Normal locations across India
        normal_locations = [
            {"lat": 26.9124, "lon": 75.7878},  # Jaipur
            {"lat": 23.0225, "lon": 72.5714},  # Ahmedabad
            {"lat": 17.3850, "lon": 78.4867},  # Hyderabad
            {"lat": 18.5204, "lon": 73.8567},  # Pune
            {"lat": 26.8467, "lon": 80.9462},  # Lucknow
            {"lat": 21.1458, "lon": 79.0882},  # Nagpur
            {"lat": 28.5355, "lon": 77.3910},  # Noida
            {"lat": 12.8399, "lon": 80.1550},  # Chennai suburbs
        ]

        base = random.choice(normal_locations)
        # Add offset
        return {
            'lat': base['lat'] + random.uniform(-0.1, 0.1),
            'lon': base['lon'] + random.uniform(-0.1, 0.1)
        }

    def _calculate_risk_score(self, fraud_signals: Dict, amount: float, trans_type: str) -> float:
        """
        Calculate risk score based on fraud signals and transaction characteristics
        """
        score = 0.0

        # Base score by transaction type
        type_scores = {
            'CASH_WITHDRAWAL': 0.3,
            'BALANCE_ENQUIRY': 0.1,
            'MINI_STATEMENT': 0.1,
            'PIN_CHANGE': 0.2,
            'FUND_TRANSFER': 0.4,
            'MOBILE_RECHARGE': 0.2
        }
        score += type_scores.get(trans_type, 0.2)

        # Add fraud signal scores
        if fraud_signals['unusual_amount']:
            score += 0.2
        if fraud_signals['new_account']:
            score += 0.15
        if fraud_signals['multiple_attempts']:
            score += 0.25
        if fraud_signals['off_hours']:
            score += 0.2
        if fraud_signals['high_velocity']:
            score += 0.3
        if fraud_signals['geolocation_mismatch']:
            score += 0.2
        if fraud_signals['suspicious_pattern']:
            score += 0.15
        if fraud_signals['atm_location_anomaly']:
            score += 0.25

        # Amount-based scoring
        if amount > 50000:
            score += 0.3
        elif amount > 20000:
            score += 0.2
        elif amount > 10000:
            score += 0.1

        # Cap at 1.0
        return min(score, 1.0)

    async def _store_transactions(self, transactions: List[Dict]) -> None:
        """
        Store transactions in database
        """
        try:
            with SessionLocal() as db:
                for txn in transactions:
                    query = text("""
                        INSERT INTO bank_transactions (
                            transaction_id, bank_code, transaction_type, amount,
                            account_hash, upi_id, merchant_hash, location,
                            risk_score, fraud_signals, is_suspicious, timestamp, batch_id
                        ) VALUES (
                            :transaction_id, :bank_code, :transaction_type, :amount,
                            :account_hash, :upi_id, :merchant_hash,
                            ST_GeomFromText('POINT(:lon :lat)', 4326),
                            :risk_score, :fraud_signals, :is_suspicious, :timestamp, :batch_id
                        )
                        ON CONFLICT (transaction_id) DO NOTHING
                    """)

                    db.execute(query, {
                        'transaction_id': txn['transaction_id'],
                        'bank_code': txn['bank_code'],
                        'transaction_type': txn['transaction_type'],
                        'amount': txn['amount'],
                        'account_hash': txn['account_hash'],
                        'upi_id': txn.get('upi_id'),
                        'merchant_hash': txn.get('merchant_hash'),
                        'lat': txn['location']['lat'],
                        'lon': txn['location']['lon'],
                        'risk_score': txn['risk_score'],
                        'fraud_signals': json.dumps(txn['fraud_signals']),
                        'is_suspicious': txn['is_suspicious'],
                        'timestamp': txn['timestamp'],
                        'batch_id': txn['batch_id']
                    })

                db.commit()
                logger.info(f"[CFCFRMS] Stored {len(transactions)} transactions in database")

        except Exception as e:
            logger.error(f"[CFCFRMS] Error storing transactions: {str(e)}")

    async def _real_transaction_logs(self, hours_back: int) -> List[Dict[str, Any]]:
        """
        Real CFCFRMS API integration (when simulation_mode = False)
        """
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }

        # CFCFRMS API endpoint structure (hypothetical)
        url = f"{self.api_base_url}/api/transactions"
        params = {
            'hours_back': hours_back,
            'include_fraud_signals': True
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"[CFCFRMS] Real fetch successful: {len(result.get('transactions', []))} transactions")
                    return result.get('transactions', [])
                else:
                    error_text = await response.text()
                    logger.error(f"[CFCFRMS] Real fetch failed: {response.status} - {error_text}")
                    return []

    async def get_suspicious_transactions(self, hours_back: int = 24, min_risk_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Get suspicious transactions above risk threshold
        """
        try:
            with SessionLocal() as db:
                query = text("""
                    SELECT transaction_id, bank_code, transaction_type, amount,
                           ST_X(location) as lat, ST_Y(location) as lon,
                           risk_score, fraud_signals, timestamp
                    FROM bank_transactions
                    WHERE is_suspicious = TRUE
                    AND risk_score >= :min_risk_score
                    AND timestamp >= NOW() - INTERVAL ':hours_back hours'
                    ORDER BY risk_score DESC, timestamp DESC
                """)

                results = db.execute(query, {
                    'min_risk_score': min_risk_score,
                    'hours_back': hours_back
                }).fetchall()

                transactions = []
                for row in results:
                    transactions.append({
                        'transaction_id': row.transaction_id,
                        'bank_code': row.bank_code,
                        'transaction_type': row.transaction_type,
                        'amount': float(row.amount),
                        'location': {
                            'lat': float(row.lat),
                            'lon': float(row.lon)
                        },
                        'risk_score': float(row.risk_score),
                        'fraud_signals': json.loads(row.fraud_signals),
                        'timestamp': row.timestamp.isoformat()
                    })

                logger.info(f"[CFCFRMS] Retrieved {len(transactions)} suspicious transactions")
                return transactions

        except Exception as e:
            logger.error(f"[CFCFRMS] Error getting suspicious transactions: {str(e)}")
            return []

    async def analyze_transaction_patterns(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Analyze transaction patterns for anomaly detection
        """
        try:
            suspicious = await self.get_suspicious_transactions(hours_back, 0.5)

            analysis = {
                'total_suspicious': len(suspicious),
                'high_risk_count': len([t for t in suspicious if t['risk_score'] >= 0.8]),
                'medium_risk_count': len([t for t in suspicious if 0.6 <= t['risk_score'] < 0.8]),
                'low_risk_count': len([t for t in suspicious if 0.4 <= t['risk_score'] < 0.6]),

                'by_transaction_type': {},
                'by_bank': {},
                'by_hour': {},
                'average_risk_score': 0.0,
                'hotspot_locations': []
            }

            if suspicious:
                # Average risk score
                analysis['average_risk_score'] = sum(t['risk_score'] for t in suspicious) / len(suspicious)

                # Group by transaction type
                for txn in suspicious:
                    txn_type = txn['transaction_type']
                    analysis['by_transaction_type'][txn_type] = analysis['by_transaction_type'].get(txn_type, 0) + 1

                # Group by bank
                for txn in suspicious:
                    bank = txn['bank_code']
                    analysis['by_bank'][bank] = analysis['by_bank'].get(bank, 0) + 1

                # Group by hour
                for txn in suspicious:
                    hour = datetime.fromisoformat(txn['timestamp']).hour
                    analysis['by_hour'][hour] = analysis['by_hour'].get(hour, 0) + 1

                # Find hotspot locations (clusters of suspicious transactions)
                analysis['hotspot_locations'] = self._find_hotspot_locations(suspicious)

            logger.info(f"[CFCFRMS] Transaction pattern analysis completed")
            return analysis

        except Exception as e:
            logger.error(f"[CFCFRMS] Error analyzing patterns: {str(e)}")
            return {}

    def _find_hotspot_locations(self, transactions: List[Dict], threshold_km: float = 2.0) -> List[Dict]:
        """
        Find geographic hotspots where suspicious transactions cluster
        """
        hotspots = []

        # Simple clustering: group transactions within threshold distance
        for i, txn1 in enumerate(transactions):
            nearby_count = 0
            nearby_txns = []

            for j, txn2 in enumerate(transactions):
                if i != j:
                    distance = self._calculate_distance(txn1['location'], txn2['location'])
                    if distance <= threshold_km:
                        nearby_count += 1
                        nearby_txns.append(txn2)

            # If this transaction has 3+ nearby suspicious transactions, it's a hotspot
            if nearby_count >= 3:
                hotspots.append({
                    'center_location': txn1['location'],
                    'transaction_count': nearby_count + 1,
                    'average_risk_score': sum(t['risk_score'] for t in nearby_txns + [txn1]) / (nearby_count + 1),
                    'transaction_types': list(set(t['transaction_type'] for t in nearby_txns + [txn1])),
                    'banks': list(set(t['bank_code'] for t in nearby_txns + [txn1]))
                })

        # Remove duplicates (same hotspot identified from different center points)
        unique_hotspots = []
        for hotspot in hotspots:
            is_duplicate = False
            for existing in unique_hotspots:
                distance = self._calculate_distance(hotspot['center_location'], existing['center_location'])
                if distance <= threshold_km:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_hotspots.append(hotspot)

        return unique_hotspots[:5]  # Return top 5 hotspots

    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """
        Calculate distance between two locations in kilometers
        """
        from math import radians, cos, sin, asin, sqrt

        lat1, lon1 = radians(loc1['lat']), radians(loc1['lon'])
        lat2, lon2 = radians(loc2['lat']), radians(loc2['lon'])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth's radius in kilometers

        return c * r

# Singleton instance
bank_integration = BankIntegration()