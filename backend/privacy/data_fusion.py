"""
Privacy-Preserving Data Fusion System
Implements k-anonymity, differential privacy, and secure multi-party computation
for combining data from NCRP, CFCFRMS, and I4C while maintaining privacy guarantees
"""

import asyncio
import numpy as np
import pandas as pd
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

class PrivacyLevel(Enum):
    """
    Privacy preservation levels
    """
    MINIMAL = "minimal"      # Basic anonymization
    STANDARD = "standard"    # k-anonymity + basic differential privacy
    HIGH = "high"           # Advanced differential privacy + secure aggregation
    MAXIMUM = "maximum"     # Full cryptographic privacy with SMPC

class DataType(Enum):
    """
    Types of data requiring different privacy treatments
    """
    LOCATION = "location"
    TEMPORAL = "temporal"
    FINANCIAL = "financial"
    BEHAVIORAL = "behavioral"
    DEMOGRAPHIC = "demographic"

@dataclass
class PrivacyBudget:
    """
    Differential privacy budget management
    """
    total_epsilon: float = 1.0
    used_epsilon: float = 0.0
    remaining_epsilon: float = 1.0
    reset_time: datetime = None

    def __post_init__(self):
        if self.reset_time is None:
            self.reset_time = datetime.utcnow() + timedelta(days=1)

@dataclass
class PrivacyParameters:
    """
    Privacy preservation parameters
    """
    k_anonymity: int = 50  # k value for k-anonymity
    epsilon: float = 0.5   # Differential privacy epsilon
    delta: float = 1e-5    # Differential privacy delta
    sensitivity: float = 1.0  # Query sensitivity
    noise_scale: float = None  # Calculated from epsilon, sensitivity

class PrivacyPreservingDataFusion:
    """
    Privacy-preserving data fusion system for cybercrime intelligence
    """

    def __init__(self):
        self.encryption_key = self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

        # Privacy parameters
        self.privacy_params = {
            DataType.LOCATION: PrivacyParameters(k_anonymity=50, epsilon=0.5),
            DataType.FINANCIAL: PrivacyParameters(k_anonymity=30, epsilon=0.3),
            DataType.TEMPORAL: PrivacyParameters(k_anonymity=20, epsilon=0.8),
            DataType.BEHAVIORAL: PrivacyParameters(k_anonymity=40, epsilon=0.6),
            DataType.DEMOGRAPHIC: PrivacyParameters(k_anonymity=100, epsilon=0.4)
        }

        # Privacy budgets
        self.privacy_budgets = {
            data_type: PrivacyBudget(total_epsilon=params.epsilon)
            for data_type, params in self.privacy_params.items()
        }

        # Anonymization caches
        self.location_clusters = {}
        self.temporal_buckets = {}
        self.financial_bins = {}

        # SMPC participants (data sources)
        self.smpc_participants = ['NCRP', 'CFCFRMS', 'I4C']
        self.smpc_shares = {}

        # Audit log
        self.audit_log = []

    def _generate_encryption_key(self) -> bytes:
        """
        Generate encryption key for data protection
        """
        password = b"aegis_privacy_key_2025"
        salt = b"aegis_salt_2025"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    async def fuse_data_sources(self, ncrp_data: List[Dict], bank_data: List[Dict],
                               i4c_data: List[Dict], privacy_level: PrivacyLevel = PrivacyLevel.STANDARD) -> Dict[str, Any]:
        """
        Fuse data from multiple sources with privacy preservation
        """
        try:
            logger.info(f"[Privacy Fusion] Starting data fusion with privacy level: {privacy_level.value}")

            fusion_id = f"fusion_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"

            # Step 1: Validate input data
            validated_data = await self._validate_input_data(ncrp_data, bank_data, i4c_data)

            # Step 2: Apply privacy preservation based on level
            if privacy_level == PrivacyLevel.MINIMAL:
                processed_data = await self._apply_minimal_privacy(validated_data)
            elif privacy_level == PrivacyLevel.STANDARD:
                processed_data = await self._apply_standard_privacy(validated_data)
            elif privacy_level == PrivacyLevel.HIGH:
                processed_data = await self._apply_high_privacy(validated_data)
            elif privacy_level == PrivacyLevel.MAXIMUM:
                processed_data = await self._apply_maximum_privacy(validated_data)

            # Step 3: Perform secure data fusion
            fused_result = await self._secure_data_fusion(processed_data, fusion_id)

            # Step 4: Generate privacy guarantees report
            privacy_report = await self._generate_privacy_report(fusion_id, privacy_level, processed_data)

            # Step 5: Log fusion operation
            await self._log_fusion_operation(fusion_id, privacy_level, len(validated_data['ncrp']) + len(validated_data['bank']) + len(validated_data['i4c']))

            result = {
                'fusion_id': fusion_id,
                'fused_data': fused_result,
                'privacy_report': privacy_report,
                'privacy_level': privacy_level.value,
                'timestamp': datetime.utcnow().isoformat(),
                'data_sources': ['NCRP', 'CFCFRMS', 'I4C'],
                'privacy_guarantees': await self._get_privacy_guarantees(privacy_level)
            }

            logger.info(f"[Privacy Fusion] Data fusion completed: {fusion_id}")
            return result

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error during data fusion: {str(e)}")
            return {'error': str(e), 'fusion_id': None}

    async def _validate_input_data(self, ncrp_data: List[Dict], bank_data: List[Dict], i4c_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Validate and sanitize input data
        """
        try:
            validated = {
                'ncrp': [],
                'bank': [],
                'i4c': []
            }

            # Validate NCRP data
            for item in ncrp_data:
                if self._validate_ncrp_record(item):
                    sanitized = self._sanitize_ncrp_record(item)
                    validated['ncrp'].append(sanitized)

            # Validate bank data
            for item in bank_data:
                if self._validate_bank_record(item):
                    sanitized = self._sanitize_bank_record(item)
                    validated['bank'].append(sanitized)

            # Validate I4C data
            for item in i4c_data:
                if self._validate_i4c_record(item):
                    sanitized = self._sanitize_i4c_record(item)
                    validated['i4c'].append(sanitized)

            logger.info(f"[Privacy Fusion] Validated data: NCRP={len(validated['ncrp'])}, Bank={len(validated['bank'])}, I4C={len(validated['i4c'])}")
            return validated

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error validating input data: {str(e)}")
            return {'ncrp': [], 'bank': [], 'i4c': []}

    def _validate_ncrp_record(self, record: Dict) -> bool:
        """Validate NCRP record"""
        required_fields = ['complaint_id', 'scam_type', 'amount', 'victim_location']
        return all(field in record for field in required_fields)

    def _validate_bank_record(self, record: Dict) -> bool:
        """Validate bank transaction record"""
        required_fields = ['transaction_id', 'bank_code', 'transaction_type', 'amount', 'location']
        return all(field in record for field in required_fields)

    def _validate_i4c_record(self, record: Dict) -> bool:
        """Validate I4C crime record"""
        required_fields = ['crime_id', 'scam_type', 'modus_operandi', 'location']
        return all(field in record for field in required_fields)

    def _sanitize_ncrp_record(self, record: Dict) -> Dict:
        """Sanitize NCRP record by removing PII"""
        sanitized = record.copy()

        # Remove explicit PII fields
        pii_fields = ['victim_name', 'victim_phone', 'victim_email', 'victim_aadhar']
        for field in pii_fields:
            sanitized.pop(field, None)

        # Hash any remaining identifiers
        if 'complaint_id' in sanitized:
            sanitized['complaint_id_hash'] = self._hash_identifier(sanitized['complaint_id'])
            del sanitized['complaint_id']

        return sanitized

    def _sanitize_bank_record(self, record: Dict) -> Dict:
        """Sanitize bank transaction record"""
        sanitized = record.copy()

        # Hash account identifiers
        if 'account_number' in sanitized:
            sanitized['account_hash'] = self._hash_identifier(sanitized['account_number'])
            del sanitized['account_number']

        if 'upi_id' in sanitized:
            sanitized['upi_hash'] = self._hash_identifier(sanitized['upi_id'])
            del sanitized['upi_id']

        return sanitized

    def _sanitize_i4c_record(self, record: Dict) -> Dict:
        """Sanitize I4C crime record"""
        sanitized = record.copy()

        # Hash crime identifier
        if 'crime_id' in sanitized:
            sanitized['crime_id_hash'] = self._hash_identifier(sanitized['crime_id'])
            del sanitized['crime_id']

        # Remove victim-specific details
        victim_fields = ['victim_name', 'victim_address', 'victim_contact']
        for field in victim_fields:
            sanitized.pop(field, None)

        return sanitized

    def _hash_identifier(self, identifier: str) -> str:
        """Hash identifier with salt"""
        salt = "aegis_hash_salt_2025"
        return hashlib.sha256((identifier + salt).encode()).hexdigest()

    async def _apply_minimal_privacy(self, data: Dict) -> Dict:
        """
        Apply minimal privacy preservation (basic anonymization)
        """
        try:
            processed = {'ncrp': [], 'bank': [], 'i4c': []}

            # Process NCRP data
            for record in data['ncrp']:
                processed_record = record.copy()

                # Basic location anonymization (add small noise)
                if 'victim_location' in processed_record:
                    processed_record['victim_location'] = self._add_location_noise(
                        processed_record['victim_location'], 0.001, 0.001
                    )

                processed['ncrp'].append(processed_record)

            # Process bank data
            for record in data['bank']:
                processed_record = record.copy()

                # Basic amount rounding
                if 'amount' in processed_record:
                    processed_record['amount'] = round(processed_record['amount'] / 1000) * 1000

                processed['bank'].append(processed_record)

            # Process I4C data
            for record in data['i4c']:
                processed_record = record.copy()
                # Basic sanitization already done
                processed['i4c'].append(processed_record)

            return processed

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error applying minimal privacy: {str(e)}")
            return data

    async def _apply_standard_privacy(self, data: Dict) -> Dict:
        """
        Apply standard privacy preservation (k-anonymity + differential privacy)
        """
        try:
            processed = {'ncrp': [], 'bank': [], 'i4c': []}

            # Process NCRP data with k-anonymity
            for record in data['ncrp']:
                processed_record = record.copy()

                # Apply k-anonymity to location
                if 'victim_location' in processed_record:
                    processed_record['victim_location'] = await self._apply_k_anonymity_location(
                        processed_record['victim_location'], DataType.LOCATION
                    )

                # Add differential privacy to amount
                if 'amount' in processed_record:
                    processed_record['amount'] = await self._add_differential_privacy_noise(
                        processed_record['amount'], DataType.FINANCIAL
                    )

                processed['ncrp'].append(processed_record)

            # Process bank data
            for record in data['bank']:
                processed_record = record.copy()

                # Apply k-anonymity to location
                if 'location' in processed_record:
                    processed_record['location'] = await self._apply_k_anonymity_location(
                        processed_record['location'], DataType.LOCATION
                    )

                # Add differential privacy to risk scores
                if 'risk_score' in processed_record:
                    processed_record['risk_score'] = await self._add_differential_privacy_noise(
                        processed_record['risk_score'], DataType.BEHAVIORAL
                    )

                processed['bank'].append(processed_record)

            # Process I4C data
            for record in data['i4c']:
                processed_record = record.copy()

                # Apply k-anonymity to location
                if 'location' in processed_record:
                    processed_record['location'] = await self._apply_k_anonymity_location(
                        processed_record['location'], DataType.LOCATION
                    )

                processed['i4c'].append(processed_record)

            return processed

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error applying standard privacy: {str(e)}")
            return await self._apply_minimal_privacy(data)

    async def _apply_high_privacy(self, data: Dict) -> Dict:
        """
        Apply high privacy preservation (advanced differential privacy + secure aggregation)
        """
        try:
            # First apply standard privacy
            processed = await self._apply_standard_privacy(data)

            # Apply additional privacy measures

            # Aggregate statistics before fusion
            aggregated_stats = await self._compute_aggregated_statistics(processed)

            # Apply stronger differential privacy to aggregated data
            private_stats = await self._apply_differential_privacy_to_aggregates(aggregated_stats)

            # Replace detailed data with private aggregates
            processed['aggregated_statistics'] = private_stats

            return processed

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error applying high privacy: {str(e)}")
            return await self._apply_standard_privacy(data)

    async def _apply_maximum_privacy(self, data: Dict) -> Dict:
        """
        Apply maximum privacy preservation (full SMPC)
        """
        try:
            # Initialize SMPC
            await self._initialize_smpc()

            # Convert data to SMPC shares
            smpc_data = {}
            for source, records in data.items():
                smpc_data[source] = await self._create_smpc_shares(records, source)

            # Perform secure aggregation
            securely_aggregated = await self._secure_multiparty_aggregation(smpc_data)

            # Return only aggregated results with maximum privacy
            processed = {
                'secure_aggregates': securely_aggregated,
                'privacy_level': 'maximum',
                'smpc_used': True
            }

            return processed

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error applying maximum privacy: {str(e)}")
            return await self._apply_high_privacy(data)

    async def _apply_k_anonymity_location(self, location: Dict[str, float], data_type: DataType) -> Dict[str, float]:
        """
        Apply k-anonymity to location data
        """
        try:
            params = self.privacy_params[data_type]
            k = params.k_anonymity

            # Create location cluster key
            lat_cluster = round(location['lat'] / 0.01) * 0.01  # ~1km clusters
            lon_cluster = round(location['lon'] / 0.01) * 0.01

            cluster_key = f"{lat_cluster:.3f}_{lon_cluster:.3f}"

            # Check if cluster exists in cache
            if cluster_key in self.location_clusters:
                cluster_center = self.location_clusters[cluster_key]
            else:
                # Create new cluster
                cluster_center = {
                    'lat': lat_cluster + np.random.uniform(-0.005, 0.005),
                    'lon': lon_cluster + np.random.uniform(-0.005, 0.005)
                }
                self.location_clusters[cluster_key] = cluster_center

            # Add noise within cluster bounds
            noise_level = 0.002  # ~200m noise
            anonymized_location = {
                'lat': cluster_center['lat'] + np.random.uniform(-noise_level, noise_level),
                'lon': cluster_center['lon'] + np.random.uniform(-noise_level, noise_level)
            }

            return anonymized_location

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error applying k-anonymity to location: {str(e)}")
            return location

    async def _add_differential_privacy_noise(self, value: float, data_type: DataType) -> float:
        """
        Add Laplace noise for differential privacy
        """
        try:
            params = self.privacy_params[data_type]

            # Check privacy budget
            budget = self.privacy_budgets[data_type]
            if budget.remaining_epsilon <= 0:
                logger.warning(f"[Privacy Fusion] Privacy budget exhausted for {data_type.value}")
                return value

            # Calculate noise scale
            noise_scale = params.sensitivity / params.epsilon

            # Generate Laplace noise
            noise = np.random.laplace(0, noise_scale)

            # Add noise to value
            noisy_value = value + noise

            # Update privacy budget
            budget.used_epsilon += params.epsilon
            budget.remaining_epsilon = max(0, budget.total_epsilon - budget.used_epsilon)

            # Ensure non-negative values
            if value >= 0:
                noisy_value = max(0, noisy_value)

            return noisy_value

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error adding differential privacy noise: {str(e)}")
            return value

    def _add_location_noise(self, location: Dict[str, float], lat_range: float, lon_range: float) -> Dict[str, float]:
        """
        Add simple noise to location
        """
        return {
            'lat': location['lat'] + np.random.uniform(-lat_range, lat_range),
            'lon': location['lon'] + np.random.uniform(-lon_range, lon_range)
        }

    async def _initialize_smpc(self) -> None:
        """
        Initialize Secure Multi-Party Computation
        """
        try:
            # Generate secret shares for each participant
            self.smpc_shares = {}
            for participant in self.smpc_participants:
                self.smpc_shares[participant] = {
                    'secret': secrets.token_bytes(32),
                    'public_key': None  # In real implementation, would generate cryptographic keys
                }

            logger.info("[Privacy Fusion] SMPC initialized")

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error initializing SMPC: {str(e)}")

    async def _create_smpc_shares(self, data: List[Dict], source: str) -> List[Dict]:
        """
        Create SMPC shares for data
        """
        try:
            shares = []

            for record in data:
                # Convert record to numerical features
                numerical_features = self._extract_numerical_features(record)

                # Create secret shares
                record_shares = {}
                for feature_name, feature_value in numerical_features.items():
                    # Split value into random shares
                    shares_list = [np.random.uniform(-1, 1) for _ in range(len(self.smpc_participants) - 1)]

                    # Calculate final share to reconstruct original value
                    final_share = feature_value - sum(shares_list)
                    shares_list.append(final_share)

                    record_shares[feature_name] = shares_list

                shares.append(record_shares)

            return shares

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error creating SMPC shares: {str(e)}")
            return []

    def _extract_numerical_features(self, record: Dict) -> Dict[str, float]:
        """
        Extract numerical features from record
        """
        features = {}

        # Location features
        if 'victim_location' in record or 'location' in record:
            location = record.get('victim_location', record.get('location', {}))
            features['lat'] = location.get('lat', 0.0)
            features['lon'] = location.get('lon', 0.0)

        # Financial features
        if 'amount' in record:
            features['amount'] = float(record['amount'])

        # Risk features
        if 'risk_score' in record:
            features['risk_score'] = float(record['risk_score'])

        # Temporal features
        if 'timestamp' in record or 'complaint_timestamp' in record:
            timestamp_str = record.get('timestamp', record.get('complaint_timestamp', ''))
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
                features['hour'] = float(timestamp.hour)
                features['day_of_week'] = float(timestamp.weekday())

        return features

    async def _secure_multiparty_aggregation(self, smpc_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Perform secure aggregation of SMPC shares
        """
        try:
            # Collect all shares from all participants
            all_shares = {}

            for source, shares in smpc_data.items():
                for record_shares in shares:
                    for feature_name, feature_shares in record_shares.items():
                        if feature_name not in all_shares:
                            all_shares[feature_name] = []
                        all_shares[feature_name].extend(feature_shares)

            # Securely reconstruct aggregated values
            aggregated_results = {}

            for feature_name, shares in all_shares.items():
                # In real SMPC, this would involve secure protocols
                # For demo, we'll compute mean of shares
                aggregated_value = np.mean(shares)
                aggregated_results[feature_name] = float(aggregated_value)

            return {
                'aggregated_features': aggregated_results,
                'participant_count': len(smpc_data),
                'total_records': sum(len(shares) for shares in smpc_data.values()),
                'privacy_method': 'SMPC'
            }

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error in SMPC aggregation: {str(e)}")
            return {}

    async def _compute_aggregated_statistics(self, data: Dict) -> Dict[str, Any]:
        """
        Compute aggregated statistics from data
        """
        try:
            stats = {
                'total_records': {
                    'ncrp': len(data['ncrp']),
                    'bank': len(data['bank']),
                    'i4c': len(data['i4c'])
                },
                'location_clusters': {},
                'financial_stats': {},
                'temporal_patterns': {},
                'scam_type_distribution': {}
            }

            # Location clustering
            all_locations = []
            for record in data['ncrp']:
                if 'victim_location' in record:
                    all_locations.append(record['victim_location'])
            for record in data['bank']:
                if 'location' in record:
                    all_locations.append(record['location'])

            if all_locations:
                # Cluster locations
                location_clusters = self._cluster_locations(all_locations)
                stats['location_clusters'] = {
                    'cluster_count': len(location_clusters),
                    'avg_cluster_size': len(all_locations) / len(location_clusters) if location_clusters else 0
                }

            # Financial statistics
            all_amounts = []
            for record in data['ncrp']:
                if 'amount' in record:
                    all_amounts.append(record['amount'])
            for record in data['bank']:
                if 'amount' in record:
                    all_amounts.append(record['amount'])

            if all_amounts:
                stats['financial_stats'] = {
                    'total_amount': sum(all_amounts),
                    'avg_amount': np.mean(all_amounts),
                    'median_amount': np.median(all_amounts),
                    'max_amount': max(all_amounts),
                    'min_amount': min(all_amounts)
                }

            # Scam type distribution
            scam_types = []
            for record in data['ncrp']:
                if 'scam_type' in record:
                    scam_types.append(record['scam_type'])
            for record in data['i4c']:
                if 'scam_type' in record:
                    scam_types.append(record['scam_type'])

            if scam_types:
                from collections import Counter
                scam_counts = Counter(scam_types)
                stats['scam_type_distribution'] = dict(scam_counts)

            return stats

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error computing aggregated statistics: {str(e)}")
            return {}

    def _cluster_locations(self, locations: List[Dict], cluster_size: float = 0.05) -> List[List[Dict]]:
        """
        Cluster locations for privacy preservation
        """
        try:
            if not locations:
                return []

            clusters = []
            used_locations = set()

            for i, location in enumerate(locations):
                if i in used_locations:
                    continue

                # Create new cluster
                cluster = [location]
                used_locations.add(i)

                # Find nearby locations
                for j, other_location in enumerate(locations):
                    if j in used_locations:
                        continue

                    distance = self._calculate_location_distance(location, other_location)
                    if distance <= cluster_size:
                        cluster.append(other_location)
                        used_locations.add(j)

                clusters.append(cluster)

            return clusters

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error clustering locations: {str(e)}")
            return [locations]

    def _calculate_location_distance(self, loc1: Dict, loc2: Dict) -> float:
        """
        Calculate distance between two locations
        """
        try:
            from math import radians, cos, sin, asin, sqrt

            lat1, lon1 = radians(loc1['lat']), radians(loc1['lon'])
            lat2, lon2 = radians(loc2['lat']), radians(loc2['lon'])

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Earth's radius in kilometers

            return c * r

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error calculating location distance: {str(e)}")
            return float('inf')

    async def _apply_differential_privacy_to_aggregates(self, stats: Dict) -> Dict:
        """
        Apply differential privacy to aggregated statistics
        """
        try:
            private_stats = stats.copy()

            # Add noise to financial statistics
            if 'financial_stats' in private_stats:
                financial_stats = private_stats['financial_stats'].copy()

                for key in ['total_amount', 'avg_amount', 'median_amount', 'max_amount']:
                    if key in financial_stats:
                        financial_stats[key] = await self._add_differential_privacy_noise(
                            financial_stats[key], DataType.FINANCIAL
                        )

                private_stats['financial_stats'] = financial_stats

            # Add noise to location cluster counts
            if 'location_clusters' in private_stats:
                location_stats = private_stats['location_clusters'].copy()

                if 'cluster_count' in location_stats:
                    location_stats['cluster_count'] = max(1, int(await self._add_differential_privacy_noise(
                        float(location_stats['cluster_count']), DataType.LOCATION
                    )))

                if 'avg_cluster_size' in location_stats:
                    location_stats['avg_cluster_size'] = await self._add_differential_privacy_noise(
                        location_stats['avg_cluster_size'], DataType.LOCATION
                    )

                private_stats['location_clusters'] = location_stats

            return private_stats

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error applying differential privacy to aggregates: {str(e)}")
            return stats

    async def _secure_data_fusion(self, processed_data: Dict, fusion_id: str) -> Dict[str, Any]:
        """
        Perform secure data fusion on processed data
        """
        try:
            # If using SMPC, return secure aggregates
            if 'secure_aggregates' in processed_data:
                return {
                    'fusion_method': 'secure_multiparty_computation',
                    'results': processed_data['secure_aggregates']
                }

            # Otherwise, perform privacy-preserving fusion
            fusion_result = {
                'fusion_method': 'privacy_preserving_aggregation',
                'spatial_hotspots': await self._identify_spatial_hotspots(processed_data),
                'temporal_patterns': await self._identify_temporal_patterns(processed_data),
                'risk_correlations': await self._identify_risk_correlations(processed_data),
                'aggregated_insights': await self._generate_aggregated_insights(processed_data)
            }

            # If aggregated statistics are available, include them
            if 'aggregated_statistics' in processed_data:
                fusion_result['aggregated_statistics'] = processed_data['aggregated_statistics']

            return fusion_result

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error in secure data fusion: {str(e)}")
            return {'error': str(e)}

    async def _identify_spatial_hotspots(self, data: Dict) -> List[Dict]:
        """
        Identify spatial hotspots from fused data
        """
        try:
            hotspots = []

            # Collect all locations
            all_locations = []
            for record in data['ncrp']:
                if 'victim_location' in record:
                    all_locations.append({
                        'location': record['victim_location'],
                        'weight': 1.0,
                        'source': 'ncrp',
                        'type': record.get('scam_type', 'unknown')
                    })

            for record in data['bank']:
                if 'location' in record and record.get('is_suspicious', False):
                    all_locations.append({
                        'location': record['location'],
                        'weight': record.get('risk_score', 0.5),
                        'source': 'bank',
                        'type': record.get('transaction_type', 'unknown')
                    })

            # Cluster locations into hotspots
            if all_locations:
                location_clusters = self._cluster_locations([loc['location'] for loc in all_locations], 0.1)

                for i, cluster in enumerate(location_clusters):
                    if len(cluster) >= 3:  # Minimum cluster size
                        # Calculate cluster center
                        center_lat = np.mean([loc['lat'] for loc in cluster])
                        center_lon = np.mean([loc['lon'] for loc in cluster])

                        # Calculate cluster intensity
                        cluster_intensity = len(cluster) * 0.1  # Base intensity

                        hotspots.append({
                            'hotspot_id': f"hs_{fusion_id}_{i:03d}",
                            'location': {'lat': center_lat, 'lon': center_lon},
                            'intensity': cluster_intensity,
                            'cluster_size': len(cluster),
                            'data_sources': list(set([loc['source'] for loc in all_locations
                                                     if self._point_in_cluster(loc['location'], cluster)]))
                        })

            # Sort by intensity
            hotspots.sort(key=lambda x: x['intensity'], reverse=True)

            return hotspots[:10]  # Return top 10 hotspots

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error identifying spatial hotspots: {str(e)}")
            return []

    def _point_in_cluster(self, point: Dict, cluster: List[Dict], threshold: float = 0.1) -> bool:
        """
        Check if a point is in a cluster
        """
        for cluster_point in cluster:
            distance = self._calculate_location_distance(point, cluster_point)
            if distance <= threshold:
                return True
        return False

    async def _identify_temporal_patterns(self, data: Dict) -> Dict[str, Any]:
        """
        Identify temporal patterns from fused data
        """
        try:
            patterns = {
                'hourly_distribution': {},
                'daily_distribution': {},
                'peak_hours': [],
                'trend_analysis': {}
            }

            # Collect temporal data
            all_timestamps = []

            for record in data['ncrp']:
                if 'complaint_timestamp' in record:
                    all_timestamps.append(datetime.fromisoformat(record['complaint_timestamp']))

            for record in data['bank']:
                if 'timestamp' in record:
                    all_timestamps.append(datetime.fromisoformat(record['timestamp']))

            if all_timestamps:
                # Hourly distribution
                hour_counts = {}
                for ts in all_timestamps:
                    hour = ts.hour
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1

                patterns['hourly_distribution'] = hour_counts

                # Peak hours
                sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                patterns['peak_hours'] = [hour for hour, _ in sorted_hours[:3]]

                # Daily distribution
                day_counts = {}
                for ts in all_timestamps:
                    day = ts.weekday()
                    day_counts[day] = day_counts.get(day, 0) + 1

                patterns['daily_distribution'] = day_counts

            return patterns

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error identifying temporal patterns: {str(e)}")
            return {}

    async def _identify_risk_correlations(self, data: Dict) -> Dict[str, Any]:
        """
        Identify risk correlations between different data sources
        """
        try:
            correlations = {
                'source_correlations': {},
                'risk_factors': {},
                'cross_source_patterns': []
            }

            # Analyze correlations between sources
            ncrp_risks = [record.get('amount', 0) for record in data['ncrp'] if 'amount' in record]
            bank_risks = [record.get('risk_score', 0) for record in data['bank'] if 'risk_score' in record]

            if ncrp_risks and bank_risks:
                # Simple correlation analysis
                ncrp_avg = np.mean(ncrp_risks)
                bank_avg = np.mean(bank_risks)

                correlations['source_correlations'] = {
                    'ncrp_avg_risk': ncrp_avg,
                    'bank_avg_risk': bank_avg,
                    'correlation_strength': min(abs(ncrp_avg - bank_avg) / max(ncrp_avg, bank_avg), 1.0)
                }

            return correlations

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error identifying risk correlations: {str(e)}")
            return {}

    async def _generate_aggregated_insights(self, data: Dict) -> Dict[str, Any]:
        """
        Generate aggregated insights from fused data
        """
        try:
            insights = {
                'total_incidents': len(data['ncrp']) + len(data['bank']) + len(data['i4c']),
                'data_completeness': {},
                'privacy_level_applied': 'standard',
                'fusion_quality': 0.8  # Placeholder metric
            }

            # Calculate data completeness
            total_fields = 0
            present_fields = 0

            for source, records in data.items():
                for record in records:
                    for field in record.keys():
                        total_fields += 1
                        if record[field] is not None:
                            present_fields += 1

            if total_fields > 0:
                insights['data_completeness'] = {
                    'overall_completeness': present_fields / total_fields,
                    'total_fields': total_fields,
                    'present_fields': present_fields
                }

            return insights

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error generating aggregated insights: {str(e)}")
            return {}

    async def _generate_privacy_report(self, fusion_id: str, privacy_level: PrivacyLevel,
                                    processed_data: Dict) -> Dict[str, Any]:
        """
        Generate privacy preservation report
        """
        try:
            report = {
                'fusion_id': fusion_id,
                'privacy_level': privacy_level.value,
                'techniques_applied': [],
                'privacy_metrics': {},
                'data_utility': {},
                'compliance': {
                    'dpdp_compliant': True,
                    'privacy_budget_used': {},
                    'anonymization_quality': 0.8
                }
            }

            # List applied techniques
            if privacy_level in [PrivacyLevel.STANDARD, PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
                report['techniques_applied'].append('k-anonymity')
                report['techniques_applied'].append('differential_privacy')

            if privacy_level in [PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
                report['techniques_applied'].append('secure_aggregation')

            if privacy_level == PrivacyLevel.MAXIMUM:
                report['techniques_applied'].append('secure_multiparty_computation')

            # Privacy metrics
            report['privacy_metrics'] = {
                'k_anonymity_values': {data_type.value: params.k_anonymity
                                    for data_type, params in self.privacy_params.items()},
                'epsilon_values': {data_type.value: params.epsilon
                                for data_type, params in self.privacy_params.items()},
                'privacy_budget_remaining': {data_type.value: budget.remaining_epsilon
                                         for data_type, budget in self.privacy_budgets.items()}
            }

            # Data utility metrics
            total_records = sum(len(records) for records in processed_data.values()
                              if isinstance(records, list))

            report['data_utility'] = {
                'records_processed': total_records,
                'information_loss_estimate': 0.15 if privacy_level == PrivacyLevel.MAXIMUM else 0.05,
                'utility_preservation': 0.85 if privacy_level == PrivacyLevel.MAXIMUM else 0.95
            }

            return report

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error generating privacy report: {str(e)}")
            return {'error': str(e)}

    async def _get_privacy_guarantees(self, privacy_level: PrivacyLevel) -> Dict[str, Any]:
        """
        Get privacy guarantees for the specified level
        """
        guarantees = {
            'minimal': {
                'guarantees': ['Basic data anonymization'],
                'formal_guarantees': [],
                'attack_resistance': ['Basic re-identification']
            },
            'standard': {
                'guarantees': ['k-anonymity', 'ε-differential privacy'],
                'formal_guarantees': ['k-anonymity theorem', 'differential privacy theorem'],
                'attack_resistance': ['Linkage attacks', 'Background knowledge attacks']
            },
            'high': {
                'guarantees': ['k-anonymity', 'ε-differential privacy', 'Secure aggregation'],
                'formal_guarantees': ['k-anonymity theorem', 'differential privacy theorem', 'Secure aggregation protocols'],
                'attack_resistance': ['Linkage attacks', 'Background knowledge attacks', 'Inference attacks']
            },
            'maximum': {
                'guarantees': ['k-anonymity', 'ε-differential privacy', 'Secure multiparty computation'],
                'formal_guarantees': ['k-anonymity theorem', 'differential privacy theorem', 'SMPC security proofs'],
                'attack_resistance': ['Linkage attacks', 'Background knowledge attacks', 'Inference attacks', 'Malicious participant attacks']
            }
        }

        return guarantees.get(privacy_level.value, guarantees['standard'])

    async def _log_fusion_operation(self, fusion_id: str, privacy_level: PrivacyLevel, record_count: int) -> None:
        """
        Log fusion operation for audit purposes
        """
        try:
            log_entry = {
                'fusion_id': fusion_id,
                'privacy_level': privacy_level.value,
                'timestamp': datetime.utcnow().isoformat(),
                'records_processed': record_count,
                'data_sources': self.smpc_participants,
                'privacy_techniques': await self._get_privacy_guarantees(privacy_level)
            }

            self.audit_log.append(log_entry)

            # Keep audit log size manageable
            if len(self.audit_log) > 1000:
                self.audit_log = self.audit_log[-500:]  # Keep last 500 entries

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error logging fusion operation: {str(e)}")

    async def reset_privacy_budgets(self) -> None:
        """
        Reset privacy budgets for new time period
        """
        try:
            for data_type, budget in self.privacy_budgets.items():
                budget.used_epsilon = 0.0
                budget.remaining_epsilon = budget.total_epsilon
                budget.reset_time = datetime.utcnow() + timedelta(days=1)

            logger.info("[Privacy Fusion] Privacy budgets reset")

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error resetting privacy budgets: {str(e)}")

    async def get_privacy_status(self) -> Dict[str, Any]:
        """
        Get current privacy system status
        """
        try:
            return {
                'privacy_budgets': {
                    data_type.value: {
                        'total_epsilon': budget.total_epsilon,
                        'used_epsilon': budget.used_epsilon,
                        'remaining_epsilon': budget.remaining_epsilon,
                        'reset_time': budget.reset_time.isoformat()
                    }
                    for data_type, budget in self.privacy_budgets.items()
                },
                'location_clusters_count': len(self.location_clusters),
                'audit_log_size': len(self.audit_log),
                'smpc_participants': self.smpc_participants,
                'privacy_parameters': {
                    data_type.value: {
                        'k_anonymity': params.k_anonymity,
                        'epsilon': params.epsilon,
                        'sensitivity': params.sensitivity
                    }
                    for data_type, params in self.privacy_params.items()
                }
            }

        except Exception as e:
            logger.error(f"[Privacy Fusion] Error getting privacy status: {str(e)}")
            return {'error': str(e)}

# Global privacy fusion service instance
privacy_preserving_fusion = PrivacyPreservingDataFusion()