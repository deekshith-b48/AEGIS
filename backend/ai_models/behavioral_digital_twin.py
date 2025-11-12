"""
Behavioral Digital Twin AI for Criminal MO Simulation
Creates sophisticated behavioral models of criminal modus operandi for predictive analysis
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict, Counter
from dataclasses import dataclass
from enum import Enum
import random
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text
from data_sources.ncrp_integration import ncrp_integration
from data_sources.bank_integration import bank_integration
from data_sources.i4c_integration import i4c_integration

logger = logging.getLogger(__name__)

class CriminalProfileType(Enum):
    """
    Types of criminal profiles based on behavioral patterns
    """
    OPPORTUNISTIC = "opportunistic"  # Low planning, high adaptability
    PROFESSIONAL = "professional"    # High planning, repeat patterns
    ORGANIZED = "organized"          # Network-based, division of labor
    TECH_SAVVY = "tech_savvy"        # Digital-first, sophisticated tools
    TRADITIONAL = "traditional"      # Physical presence, low-tech methods

class MOCategory(Enum):
    """
    Modus Operandi categories
    """
    FINANCIAL_FRAUD = "financial_fraud"
    IMPERSONATION = "impersonation"
    DIGITAL_SCAM = "digital_scam"
    PHYSICAL_INTIMIDATION = "physical_intimidation"
    IDENTITY_THEFT = "identity_theft"

@dataclass
class BehaviorPattern:
    """
    Represents a specific behavior pattern
    """
    pattern_id: str
    behavior_type: str
    frequency: float
    intensity: float
    temporal_pattern: Dict  # Time-based patterns
    spatial_pattern: Dict   # Location-based patterns
    success_rate: float
    adaptability_score: float

@dataclass
class CriminalTwin:
    """
    Digital twin of a criminal entity
    """
    twin_id: str
    profile_type: CriminalProfileType
    mo_categories: List[MOCategory]
    behavior_patterns: List[BehaviorPattern]
    risk_level: float
    adaptability_quotient: float
    network_influence: float
    learning_capability: float
    historical_performance: Dict
    current_state: Dict

class BehavioralDigitalTwin:
    """
    Behavioral Digital Twin AI for simulating and predicting criminal behavior
    """

    def __init__(self):
        self.criminal_twins = {}  # twin_id -> CriminalTwin
        self.behavior_templates = {}  # Template behaviors for different profiles
        self.mo_database = {}  # Historical MO database
        self.prediction_models = {}  # Behavioral prediction models
        self.simulation_results = []  # Recent simulation results

        # Behavioral parameters
        self.learning_rate = 0.1
        self.adaptation_threshold = 0.7
        self.simulation_horizon_hours = 48
        self.behavior_decay_rate = 0.05

    async def initialize_twins(self) -> Dict[str, Any]:
        """
        Initialize behavioral digital twins from historical data
        """
        try:
            logger.info("[Behavioral Digital Twin] Initializing criminal twins...")

            # Step 1: Load historical data
            historical_data = await self._load_historical_data()

            # Step 2: Extract behavior patterns
            behavior_patterns = await self._extract_behavior_patterns(historical_data)

            # Step 3: Create behavior templates
            await self._create_behavior_templates(behavior_patterns)

            # Step 4: Generate criminal twins
            await self._generate_criminal_twins(behavior_patterns)

            # Step 5: Calibrate prediction models
            await self._calibrate_prediction_models()

            logger.info(f"[Behavioral Digital Twin] Initialized {len(self.criminal_twins)} criminal twins")

            return {
                'success': True,
                'twins_created': len(self.criminal_twins),
                'behavior_patterns': len(behavior_patterns),
                'templates_created': len(self.behavior_templates)
            }

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error initializing twins: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _load_historical_data(self) -> Dict[str, List[Dict]]:
        """
        Load historical data from all sources
        """
        try:
            ncrp_data = await ncrp_integration.get_complaints_batch(limit=500, offset=0)
            bank_suspicious = await bank_integration.get_suspicious_transactions(hours_back=168)  # 1 week
            i4c_data = await i4c_integration.get_training_data_for_ml(months_back=3)

            return {
                'ncrp_complaints': ncrp_data,
                'bank_transactions': bank_suspicious,
                'i4c_crimes': i4c_data
            }

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error loading historical data: {str(e)}")
            return {}

    async def _extract_behavior_patterns(self, historical_data: Dict) -> List[Dict]:
        """
        Extract behavior patterns from historical data
        """
        try:
            patterns = []

            # Analyze NCRP complaints
            for complaint in historical_data.get('ncrp_complaints', []):
                pattern = await self._analyze_complaint_behavior(complaint)
                if pattern:
                    patterns.append(pattern)

            # Analyze bank transactions
            for txn in historical_data.get('bank_transactions', []):
                pattern = await self._analyze_transaction_behavior(txn)
                if pattern:
                    patterns.append(pattern)

            # Analyze I4C crimes
            for crime in historical_data.get('i4c_crimes', []):
                pattern = await self._analyze_crime_behavior(crime)
                if pattern:
                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error extracting patterns: {str(e)}")
            return []

    async def _analyze_complaint_behavior(self, complaint: Dict) -> Optional[Dict]:
        """
        Analyze behavior pattern from a complaint
        """
        try:
            timestamp = datetime.fromisoformat(complaint['complaint_timestamp'])
            scam_type = complaint['scam_type']
            amount = complaint['amount']

            # Temporal pattern
            temporal_pattern = {
                'hour_of_day': timestamp.hour,
                'day_of_week': timestamp.weekday(),
                'month': timestamp.month,
                'is_weekend': timestamp.weekday() >= 5,
                'is_business_hours': 9 <= timestamp.hour <= 17
            }

            # Spatial pattern
            location = complaint['victim_location']
            spatial_pattern = {
                'lat': location['lat'],
                'lon': location['lon'],
                'urban_density': self._estimate_urban_density(location),
                'proximity_to_transport': self._estimate_transport_proximity(location)
            }

            # Behavioral indicators
            behavioral_indicators = {
                'scam_type': scam_type,
                'amount_category': self._categorize_amount(amount),
                'planning_level': self._estimate_planning_level(scam_type, amount),
                'sophistication': self._estimate_sophistication(scam_type, complaint),
                'risk_appetite': self._estimate_risk_appetite(amount)
            }

            return {
                'source': 'ncrp',
                'temporal_pattern': temporal_pattern,
                'spatial_pattern': spatial_pattern,
                'behavioral_indicators': behavioral_indicators,
                'success_indicators': {'complaint_filed': True, 'amount_lost': amount}
            }

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error analyzing complaint: {str(e)}")
            return None

    async def _analyze_transaction_behavior(self, txn: Dict) -> Optional[Dict]:
        """
        Analyze behavior pattern from a suspicious transaction
        """
        try:
            timestamp = datetime.fromisoformat(txn['timestamp'])
            transaction_type = txn['transaction_type']
            amount = txn['amount']
            risk_score = txn['risk_score']
            fraud_signals = txn['fraud_signals']

            # Temporal pattern
            temporal_pattern = {
                'hour_of_day': timestamp.hour,
                'day_of_week': timestamp.weekday(),
                'is_off_hours': timestamp.hour < 6 or timestamp.hour > 22,
                'transaction_frequency': 'high' if fraud_signals.get('high_velocity') else 'normal'
            }

            # Spatial pattern
            location = txn['location']
            spatial_pattern = {
                'lat': location['lat'],
                'lon': location['lon'],
                'location_risk': 'high' if txn['is_suspicious'] else 'normal',
                'atm_anomaly': fraud_signals.get('atm_location_anomaly', False)
            }

            # Behavioral indicators
            behavioral_indicators = {
                'transaction_type': transaction_type,
                'amount_category': self._categorize_amount(amount),
                'planning_level': 'high' if fraud_signals.get('new_account') else 'medium',
                'sophistication': 'high' if fraud_signals.get('geolocation_mismatch') else 'medium',
                'risk_appetite': 'high' if amount > 50000 else 'medium',
                'digital_preference': transaction_type != 'CASH_WITHDRAWAL'
            }

            return {
                'source': 'bank',
                'temporal_pattern': temporal_pattern,
                'spatial_pattern': spatial_pattern,
                'behavioral_indicators': behavioral_indicators,
                'success_indicators': {'transaction_completed': True, 'risk_score': risk_score}
            }

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error analyzing transaction: {str(e)}")
            return None

    async def _analyze_crime_behavior(self, crime: Dict) -> Optional[Dict]:
        """
        Analyze behavior pattern from I4C crime data
        """
        try:
            modus_operandi = crime['modus_operandi']
            scam_type = crime['scam_type']
            severity_score = crime['severity_score']
            repeat_offender = crime['repeat_offender']
            victim_profile = crime['victim_profile']

            # Temporal pattern (estimated from date range)
            date_start = crime['date_range_start']
            date_end = crime['date_range_end']
            duration_days = (date_end - date_start).days if date_end and date_start else 1

            temporal_pattern = {
                'operation_duration': duration_days,
                'is_repeat_offender': repeat_offender,
                'victim_count': severity_score * 2,  # Estimate from severity
                'planning_horizon': 'long' if duration_days > 7 else 'short'
            }

            # Spatial pattern (general)
            spatial_pattern = {
                'geographic_scope': 'multi_city' if severity_score > 7 else 'single_city',
                'target_preference': victim_profile.get('urban_rural', 'urban'),
                'mobility_level': 'high' if duration_days > 30 else 'medium'
            }

            # Behavioral indicators
            behavioral_indicators = {
                'modus_operandi': modus_operandi,
                'scam_type': scam_type,
                'planning_level': 'high' if repeat_offender else 'medium',
                'sophistication': 'high' if severity_score > 7 else 'medium',
                'risk_appetite': 'high' if severity_score > 8 else 'medium',
                'organization_level': 'high' if repeat_offender else 'low'
            }

            return {
                'source': 'i4c',
                'temporal_pattern': temporal_pattern,
                'spatial_pattern': spatial_pattern,
                'behavioral_indicators': behavioral_indicators,
                'success_indicators': {
                    'conviction_rate': crime.get('conviction_rate', 0),
                    'case_outcome': crime.get('outcome', 'unknown')
                }
            }

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error analyzing crime: {str(e)}")
            return None

    def _estimate_urban_density(self, location: Dict[str, float]) -> str:
        """
        Estimate urban density based on location
        """
        # Simplified urban density estimation
        major_cities = [
            (28.6139, 77.2090),  # Delhi
            (19.0760, 72.8777),  # Mumbai
            (12.9716, 77.5946),  # Bangalore
            (13.0827, 80.2707),  # Chennai
            (22.5726, 88.3639),  # Kolkata
        ]

        for city_lat, city_lon in major_cities:
            distance = self._calculate_distance(location, {'lat': city_lat, 'lon': city_lon})
            if distance < 20:  # Within 20km
                return 'high'

        return 'medium'

    def _estimate_transport_proximity(self, location: Dict[str, float]) -> str:
        """
        Estimate proximity to transport hubs
        """
        # Simplified transport proximity estimation
        transport_hubs = [
            (28.6139, 77.2090),  # Delhi (major hub)
            (19.0760, 72.8777),  # Mumbai
            (12.9716, 77.5946),  # Bangalore
            (13.0827, 80.2707),  # Chennai
        ]

        min_distance = float('inf')
        for hub_lat, hub_lon in transport_hubs:
            distance = self._calculate_distance(location, {'lat': hub_lat, 'lon': hub_lon})
            min_distance = min(min_distance, distance)

        if min_distance < 5:
            return 'very_high'
        elif min_distance < 15:
            return 'high'
        elif min_distance < 50:
            return 'medium'
        else:
            return 'low'

    def _calculate_distance(self, loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
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

    def _categorize_amount(self, amount: float) -> str:
        """
        Categorize transaction amount
        """
        if amount < 1000:
            return 'very_low'
        elif amount < 10000:
            return 'low'
        elif amount < 50000:
            return 'medium'
        elif amount < 200000:
            return 'high'
        else:
            return 'very_high'

    def _estimate_planning_level(self, scam_type: str, amount: float) -> str:
        """
        Estimate planning level based on scam type and amount
        """
        high_planning_scams = ['INVESTMENT_FRAUD', 'LOTTERY_SCAM', 'FAKE_LOAN_APP']
        if scam_type in high_planning_scams or amount > 100000:
            return 'high'
        elif amount > 20000:
            return 'medium'
        else:
            return 'low'

    def _estimate_sophistication(self, scam_type: str, context: Dict) -> str:
        """
        Estimate sophistication level
        """
        tech_savvy_scams = ['UPI_PHISHING', 'INVESTMENT_FRAUD']
        if scam_type in tech_savvy_scams:
            return 'high'
        elif 'digital_footprint' in context and context['digital_footprint']:
            return 'medium'
        else:
            return 'low'

    def _estimate_risk_appetite(self, amount: float) -> str:
        """
        Estimate risk appetite based on amount
        """
        if amount > 200000:
            return 'very_high'
        elif amount > 50000:
            return 'high'
        elif amount > 10000:
            return 'medium'
        else:
            return 'low'

    async def _create_behavior_templates(self, patterns: List[Dict]) -> None:
        """
        Create behavior templates for different criminal profiles
        """
        try:
            # Group patterns by profile characteristics
            profile_groups = defaultdict(list)

            for pattern in patterns:
                profile_type = self._classify_profile(pattern)
                profile_groups[profile_type].append(pattern)

            # Create templates for each profile type
            for profile_type, profile_patterns in profile_groups.items():
                template = await self._create_profile_template(profile_type, profile_patterns)
                self.behavior_templates[profile_type.value] = template

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error creating templates: {str(e)}")

    def _classify_profile(self, pattern: Dict) -> CriminalProfileType:
        """
        Classify criminal profile based on behavior pattern
        """
        indicators = pattern['behavioral_indicators']
        temporal = pattern['temporal_pattern']
        spatial = pattern['spatial_pattern']

        # Scoring for different profile types
        scores = {
            CriminalProfileType.OPPORTUNISTIC: 0,
            CriminalProfileType.PROFESSIONAL: 0,
            CriminalProfileType.ORGANIZED: 0,
            CriminalProfileType.TECH_SAVVY: 0,
            CriminalProfileType.TRADITIONAL: 0
        }

        # Opportunistic traits
        if temporal.get('is_business_hours', False):
            scores[CriminalProfileType.OPPORTUNISTIC] += 2
        if indicators.get('planning_level') == 'low':
            scores[CriminalProfileType.OPPORTUNISTIC] += 2

        # Professional traits
        if indicators.get('planning_level') == 'high':
            scores[CriminalProfileType.PROFESSIONAL] += 2
        if temporal.get('planning_horizon') == 'long':
            scores[CriminalProfileType.PROFESSIONAL] += 2

        # Organized traits
        if spatial.get('geographic_scope') == 'multi_city':
            scores[CriminalProfileType.ORGANIZED] += 3
        if indicators.get('organization_level') == 'high':
            scores[CriminalProfileType.ORGANIZED] += 2

        # Tech-savvy traits
        if indicators.get('digital_preference', False):
            scores[CriminalProfileType.TECH_SAVVY] += 3
        if indicators.get('scam_type') in ['UPI_PHISHING', 'INVESTMENT_FRAUD']:
            scores[CriminalProfileType.TECH_SAVVY] += 2

        # Traditional traits
        if not indicators.get('digital_preference', True):
            scores[CriminalProfileType.TRADITIONAL] += 2
        if indicators.get('transaction_type') == 'CASH_WITHDRAWAL':
            scores[CriminalProfileType.TRADITIONAL] += 2

        # Return profile with highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    async def _create_profile_template(self, profile_type: CriminalProfileType, patterns: List[Dict]) -> Dict:
        """
        Create a behavior template for a specific profile type
        """
        try:
            # Aggregate patterns
            temporal_patterns = [p['temporal_pattern'] for p in patterns]
            spatial_patterns = [p['spatial_pattern'] for p in patterns]
            behavioral_indicators = [p['behavioral_indicators'] for p in patterns]

            template = {
                'profile_type': profile_type.value,
                'temporal_preferences': self._aggregate_temporal_patterns(temporal_patterns),
                'spatial_preferences': self._aggregate_spatial_patterns(spatial_patterns),
                'behavioral_traits': self._aggregate_behavioral_traits(behavioral_indicators),
                'success_patterns': self._extract_success_patterns(patterns),
                'adaptability_markers': self._identify_adaptability_markers(patterns)
            }

            return template

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error creating template: {str(e)}")
            return {}

    def _aggregate_temporal_patterns(self, temporal_patterns: List[Dict]) -> Dict:
        """
        Aggregate temporal patterns
        """
        aggregated = {
            'preferred_hours': [],
            'preferred_days': [],
            'off_hours_frequency': 0,
            'weekend_preference': 0
        }

        hours = [p.get('hour_of_day', 12) for p in temporal_patterns]
        days = [p.get('day_of_week', 0) for p in temporal_patterns]

        # Find most common hours and days
        hour_counts = Counter(hours)
        day_counts = Counter(days)

        aggregated['preferred_hours'] = [h for h, _ in hour_counts.most_common(3)]
        aggregated['preferred_days'] = [d for d, _ in day_counts.most_common(3)]
        aggregated['off_hours_frequency'] = sum(1 for p in temporal_patterns if p.get('is_off_hours', False)) / len(temporal_patterns)
        aggregated['weekend_preference'] = sum(1 for p in temporal_patterns if p.get('is_weekend', False)) / len(temporal_patterns)

        return aggregated

    def _aggregate_spatial_patterns(self, spatial_patterns: List[Dict]) -> Dict:
        """
        Aggregate spatial patterns
        """
        aggregated = {
            'preferred_density': 'medium',
            'transport_proximity': 'medium',
            'geographic_scope': 'single_city',
            'mobility_level': 'medium'
        }

        densities = [p.get('urban_density', 'medium') for p in spatial_patterns]
        proximities = [p.get('transport_proximity', 'medium') for p in spatial_patterns]

        aggregated['preferred_density'] = Counter(densities).most_common(1)[0][0]
        aggregated['transport_proximity'] = Counter(proximities).most_common(1)[0][0]

        return aggregated

    def _aggregate_behavioral_traits(self, behavioral_indicators: List[Dict]) -> Dict:
        """
        Aggregate behavioral traits
        """
        aggregated = {
            'preferred_scam_types': [],
            'amount_preferences': [],
            'planning_tendencies': [],
            'sophistication_level': 'medium',
            'risk_appetite_level': 'medium'
        }

        scam_types = [b.get('scam_type', 'UNKNOWN') for b in behavioral_indicators]
        amounts = [b.get('amount_category', 'medium') for b in behavioral_indicators]
        planning = [b.get('planning_level', 'medium') for b in behavioral_indicators]
        sophistication = [b.get('sophistication', 'medium') for b in behavioral_indicators]
        risk_appetite = [b.get('risk_appetite', 'medium') for b in behavioral_indicators]

        aggregated['preferred_scam_types'] = [st for st, _ in Counter(scam_types).most_common(3)]
        aggregated['amount_preferences'] = [a for a, _ in Counter(amounts).most_common(2)]
        aggregated['planning_tendencies'] = [p for p, _ in Counter(planning).most_common(2)]
        aggregated['sophistication_level'] = Counter(sophistication).most_common(1)[0][0]
        aggregated['risk_appetite_level'] = Counter(risk_appetite).most_common(1)[0][0]

        return aggregated

    def _extract_success_patterns(self, patterns: List[Dict]) -> Dict:
        """
        Extract success patterns from behavior patterns
        """
        success_metrics = []

        for pattern in patterns:
            success_indicators = pattern.get('success_indicators', {})
            if 'risk_score' in success_indicators:
                success_metrics.append(success_indicators['risk_score'])
            elif 'amount_lost' in success_indicators:
                success_metrics.append(min(success_indicators['amount_lost'] / 100000, 1.0))

        if success_metrics:
            avg_success = np.mean(success_metrics)
            return {
                'average_success_rate': avg_success,
                'success_variability': np.std(success_metrics),
                'high_success_conditions': 'high_amount' if avg_success > 0.7 else 'medium_amount'
            }

        return {'average_success_rate': 0.5, 'success_variability': 0.2}

    def _identify_adaptability_markers(self, patterns: List[Dict]) -> Dict:
        """
        Identify adaptability markers
        """
        markers = {
            'temporal_flexibility': 0.0,
            'spatial_adaptability': 0.0,
            'method_diversity': 0.0,
            'learning_rate': 0.1
        }

        # Calculate temporal flexibility (variance in timing)
        hours = [p['temporal_pattern'].get('hour_of_day', 12) for p in patterns if 'hour_of_day' in p['temporal_pattern']]
        if hours:
            markers['temporal_flexibility'] = min(np.std(hours) / 12, 1.0)  # Normalize by max possible std

        # Calculate spatial adaptability
        locations = [(p['spatial_pattern'].get('lat', 0), p['spatial_pattern'].get('lon', 0))
                    for p in patterns if 'lat' in p['spatial_pattern']]
        if len(locations) > 1:
            distances = [self._calculate_distance({'lat': l1[0], 'lon': l1[1]}, {'lat': l2[0], 'lon': l2[1]})
                        for i, l1 in enumerate(locations) for l2 in locations[i+1:]]
            markers['spatial_adaptability'] = min(np.mean(distances) / 1000, 1.0)  # Normalize by 1000km

        # Calculate method diversity
        scam_types = [p['behavioral_indicators'].get('scam_type', 'UNKNOWN') for p in patterns]
        unique_scams = len(set(scam_types))
        markers['method_diversity'] = min(unique_scams / 5, 1.0)  # Normalize by 5 scam types

        return markers

    async def _generate_criminal_twins(self, patterns: List[Dict]) -> None:
        """
        Generate criminal twins based on behavior patterns
        """
        try:
            # Group patterns by profile and create twins
            profile_groups = defaultdict(list)

            for pattern in patterns:
                profile_type = self._classify_profile(pattern)
                profile_groups[profile_type].append(pattern)

            twin_id = 1

            for profile_type, profile_patterns in profile_groups.items():
                # Create multiple twins for each profile type
                num_twins = max(1, len(profile_patterns) // 10)  # One twin per 10 patterns

                for i in range(num_twins):
                    twin = await self._create_criminal_twin(
                        f"twin_{twin_id:04d}",
                        profile_type,
                        profile_patterns[i::num_twins]  # Distribute patterns among twins
                    )
                    self.criminal_twins[twin.twin_id] = twin
                    twin_id += 1

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error generating twins: {str(e)}")

    async def _create_criminal_twin(self, twin_id: str, profile_type: CriminalProfileType, patterns: List[Dict]) -> CriminalTwin:
        """
        Create a criminal twin with specific behaviors
        """
        try:
            # Extract MO categories from patterns
            mo_categories = list(set([self._map_to_mo_category(p['behavioral_indicators'].get('scam_type', 'UNKNOWN'))
                                    for p in patterns]))

            # Create behavior patterns
            behavior_patterns = []
            for i, pattern in enumerate(patterns):
                behavior_pattern = BehaviorPattern(
                    pattern_id=f"{twin_id}_pattern_{i:03d}",
                    behavior_type=pattern['behavioral_indicators'].get('scam_type', 'UNKNOWN'),
                    frequency=1.0 / len(patterns),  # Equal frequency initially
                    intensity=self._calculate_pattern_intensity(pattern),
                    temporal_pattern=pattern['temporal_pattern'],
                    spatial_pattern=pattern['spatial_pattern'],
                    success_rate=self._estimate_pattern_success(pattern),
                    adaptability_score=0.5  # Will be updated through learning
                )
                behavior_patterns.append(behavior_pattern)

            # Calculate twin characteristics
            risk_level = self._calculate_twin_risk_level(patterns)
            adaptability_quotient = self._calculate_adaptability_quotient(patterns)
            network_influence = self._estimate_network_influence(patterns)
            learning_capability = adaptability_quotient * 0.8

            twin = CriminalTwin(
                twin_id=twin_id,
                profile_type=profile_type,
                mo_categories=mo_categories,
                behavior_patterns=behavior_patterns,
                risk_level=risk_level,
                adaptability_quotient=adaptability_quotient,
                network_influence=network_influence,
                learning_capability=learning_capability,
                historical_performance={'attempts': 0, 'successes': 0, 'evolutions': 0},
                current_state={
                    'active': True,
                    'last_activity': datetime.utcnow().isoformat(),
                    'current_phase': 'observation',
                    'stress_level': 0.3
                }
            )

            return twin

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error creating twin: {str(e)}")
            # Return default twin
            return CriminalTwin(
                twin_id=twin_id,
                profile_type=profile_type,
                mo_categories=[MOCategory.FINANCIAL_FRAUD],
                behavior_patterns=[],
                risk_level=0.5,
                adaptability_quotient=0.5,
                network_influence=0.3,
                learning_capability=0.4,
                historical_performance={'attempts': 0, 'successes': 0, 'evolutions': 0},
                current_state={'active': True, 'last_activity': datetime.utcnow().isoformat()}
            )

    def _map_to_mo_category(self, scam_type: str) -> MOCategory:
        """
        Map scam type to MO category
        """
        mapping = {
            'UPI_PHISHING': MOCategory.DIGITAL_SCAM,
            'FAKE_LOAN_APP': MOCategory.FINANCIAL_FRAUD,
            'IMPERSONATION': MOCategory.IMPERSONATION,
            'LOTTERY_SCAM': MOCategory.FINANCIAL_FRAUD,
            'INVESTMENT_FRAUD': MOCategory.FINANCIAL_FRAUD
        }
        return mapping.get(scam_type, MOCategory.DIGITAL_SCAM)

    def _calculate_pattern_intensity(self, pattern: Dict) -> float:
        """
        Calculate intensity of a behavior pattern
        """
        intensity_factors = []

        # Amount-based intensity
        if 'amount_lost' in pattern.get('success_indicators', {}):
            amount = pattern['success_indicators']['amount_lost']
            intensity_factors.append(min(amount / 100000, 1.0))

        # Risk score intensity
        if 'risk_score' in pattern.get('success_indicators', {}):
            risk_score = pattern['success_indicators']['risk_score']
            intensity_factors.append(risk_score)

        # Sophistication intensity
        sophistication = pattern['behavioral_indicators'].get('sophistication', 'medium')
        sophistication_score = {'low': 0.3, 'medium': 0.6, 'high': 0.9}.get(sophistication, 0.6)
        intensity_factors.append(sophistication_score)

        return np.mean(intensity_factors) if intensity_factors else 0.5

    def _estimate_pattern_success(self, pattern: Dict) -> float:
        """
        Estimate success rate of a pattern
        """
        success_indicators = pattern.get('success_indicators', {})

        if 'risk_score' in success_indicators:
            return min(success_indicators['risk_score'], 1.0)
        elif 'conviction_rate' in success_indicators:
            # Low conviction rate suggests high success
            return max(1.0 - success_indicators['conviction_rate'], 0.1)
        else:
            return 0.6  # Default moderate success

    def _calculate_twin_risk_level(self, patterns: List[Dict]) -> float:
        """
        Calculate overall risk level for a twin
        """
        if not patterns:
            return 0.5

        risk_factors = []

        for pattern in patterns:
            indicators = pattern['behavioral_indicators']

            # Risk from planning level
            planning_level = indicators.get('planning_level', 'medium')
            planning_risk = {'low': 0.3, 'medium': 0.6, 'high': 0.9}.get(planning_level, 0.6)
            risk_factors.append(planning_risk)

            # Risk from sophistication
            sophistication = indicators.get('sophistication', 'medium')
            sophistication_risk = {'low': 0.3, 'medium': 0.6, 'high': 0.9}.get(sophistication, 0.6)
            risk_factors.append(sophistication_risk)

            # Risk from amount
            amount_category = indicators.get('amount_category', 'medium')
            amount_risk = {'very_low': 0.1, 'low': 0.3, 'medium': 0.6, 'high': 0.8, 'very_high': 0.95}.get(amount_category, 0.6)
            risk_factors.append(amount_risk)

        return np.mean(risk_factors)

    def _calculate_adaptability_quotient(self, patterns: List[Dict]) -> float:
        """
        Calculate adaptability quotient for a twin
        """
        if not patterns:
            return 0.5

        adaptability_factors = []

        # Method diversity
        scam_types = list(set([p['behavioral_indicators'].get('scam_type', 'UNKNOWN') for p in patterns]))
        method_diversity = min(len(scam_types) / 5, 1.0)
        adaptability_factors.append(method_diversity)

        # Temporal flexibility
        hours = [p['temporal_pattern'].get('hour_of_day', 12) for p in patterns if 'hour_of_day' in p['temporal_pattern']]
        if hours:
            temporal_flexibility = min(np.std(hours) / 12, 1.0)
            adaptability_factors.append(temporal_flexibility)

        # Learning indicators
        repeat_offender_count = sum(1 for p in patterns if p.get('repeat_offender', False))
        learning_factor = min(repeat_offender_count / len(patterns), 1.0)
        adaptability_factors.append(learning_factor)

        return np.mean(adaptability_factors) if adaptability_factors else 0.5

    def _estimate_network_influence(self, patterns: List[Dict]) -> float:
        """
        Estimate network influence for a twin
        """
        if not patterns:
            return 0.3

        network_indicators = []

        # Geographic scope
        multi_city_patterns = sum(1 for p in patterns if p['spatial_pattern'].get('geographic_scope') == 'multi_city')
        geographic_influence = min(multi_city_patterns / len(patterns), 1.0)
        network_indicators.append(geographic_influence)

        # Organization level
        organized_patterns = sum(1 for p in patterns if p['behavioral_indicators'].get('organization_level') == 'high')
        organization_influence = min(organized_patterns / len(patterns), 1.0)
        network_indicators.append(organization_influence)

        return np.mean(network_indicators) if network_indicators else 0.3

    async def _calibrate_prediction_models(self) -> None:
        """
        Calibrate prediction models based on initialized twins
        """
        try:
            # Initialize prediction models for each behavior type
            behavior_types = set()
            for twin in self.criminal_twins.values():
                for pattern in twin.behavior_patterns:
                    behavior_types.add(pattern.behavior_type)

            for behavior_type in behavior_types:
                self.prediction_models[behavior_type] = {
                    'base_probability': 0.5,
                    'temporal_weights': {h: 1.0 for h in range(24)},
                    'spatial_weights': {'urban': 1.0, 'suburban': 1.0, 'rural': 1.0},
                    'adaptation_factor': 1.0,
                    'learning_rate': self.learning_rate
                }

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error calibrating models: {str(e)}")

    async def simulate_criminal_behavior(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Simulate criminal behavior using digital twins
        """
        try:
            logger.info(f"[Behavioral Digital Twin] Simulating criminal behavior for {hours_ahead} hours...")

            simulations = []

            for twin in self.criminal_twins.values():
                if not twin.current_state.get('active', True):
                    continue

                # Simulate behavior for each active twin
                twin_simulations = await self._simulate_twin_behavior(twin, hours_ahead)
                simulations.extend(twin_simulations)

            # Sort by risk level and timestamp
            simulations.sort(key=lambda x: (x['risk_score'], x['predicted_time']), reverse=True)

            # Store simulation results
            self.simulation_results = simulations[:50]  # Keep top 50 predictions

            logger.info(f"[Behavioral Digital Twin] Generated {len(simulations)} behavior predictions")

            return simulations

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error simulating behavior: {str(e)}")
            return []

    async def _simulate_twin_behavior(self, twin: CriminalTwin, hours_ahead: int) -> List[Dict]:
        """
        Simulate behavior for a specific twin
        """
        try:
            twin_simulations = []

            for hour_offset in range(hours_ahead):
                predicted_time = datetime.utcnow() + timedelta(hours=hour_offset)

                # Check if twin is likely to be active at this time
                activity_probability = await self._calculate_activity_probability(twin, predicted_time)

                if random.random() < activity_probability:
                    # Generate behavior prediction
                    behavior_pattern = await self._select_behavior_pattern(twin, predicted_time)

                    if behavior_pattern:
                        prediction = await self._generate_behavior_prediction(
                            twin, behavior_pattern, predicted_time, hour_offset
                        )
                        twin_simulations.append(prediction)

            return twin_simulations

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error simulating twin behavior: {str(e)}")
            return []

    async def _calculate_activity_probability(self, twin: CriminalTwin, timestamp: datetime) -> float:
        """
        Calculate probability of twin being active at given time
        """
        try:
            base_activity = 0.3  # Base activity probability

            # Temporal preferences
            template = self.behavior_templates.get(twin.profile_type.value, {})
            temporal_prefs = template.get('temporal_preferences', {})

            hour = timestamp.hour
            day_of_week = timestamp.weekday()

            # Check if preferred hour
            if hour in temporal_prefs.get('preferred_hours', []):
                base_activity += 0.3

            # Check if preferred day
            if day_of_week in temporal_prefs.get('preferred_days', []):
                base_activity += 0.2

            # Weekend preference
            if day_of_week >= 5 and temporal_prefs.get('weekend_preference', 0) > 0.5:
                base_activity += 0.2

            # Off-hours activity
            if hour < 6 or hour > 22:
                base_activity += temporal_prefs.get('off_hours_frequency', 0) * 0.3

            # Stress and adaptation effects
            stress_level = twin.current_state.get('stress_level', 0.3)
            if stress_level > 0.7:
                base_activity *= 1.2  # Higher stress increases activity
            elif stress_level < 0.2:
                base_activity *= 0.8  # Low stress decreases activity

            return min(base_activity, 1.0)

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error calculating activity probability: {str(e)}")
            return 0.3

    async def _select_behavior_pattern(self, twin: CriminalTwin, timestamp: datetime) -> Optional[BehaviorPattern]:
        """
        Select behavior pattern for twin at given time
        """
        try:
            if not twin.behavior_patterns:
                return None

            # Weight patterns by frequency and temporal compatibility
            pattern_weights = []

            for pattern in twin.behavior_patterns:
                weight = pattern.frequency

                # Temporal compatibility
                pattern_hour = pattern.temporal_pattern.get('hour_of_day', 12)
                hour_diff = abs(timestamp.hour - pattern_hour)
                temporal_compatibility = 1.0 - (hour_diff / 12.0)  # Max 12 hour difference
                weight *= temporal_compatibility

                # Recent success increases weight
                weight *= (1.0 + pattern.success_rate)

                # Adaptability effect
                weight *= (1.0 + pattern.adaptability_score)

                pattern_weights.append(weight)

            # Select pattern probabilistically
            total_weight = sum(pattern_weights)
            if total_weight > 0:
                probabilities = [w / total_weight for w in pattern_weights]
                selected_index = np.random.choice(len(twin.behavior_patterns), p=probabilities)
                return twin.behavior_patterns[selected_index]

            return None

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error selecting pattern: {str(e)}")
            return None

    async def _generate_behavior_prediction(self, twin: CriminalTwin, pattern: BehaviorPattern,
                                          timestamp: datetime, hour_offset: int) -> Dict[str, Any]:
        """
        Generate detailed behavior prediction
        """
        try:
            # Base prediction
            prediction = {
                'prediction_id': f"pred_{twin.twin_id}_{timestamp.strftime('%Y%m%d%H%M')}",
                'twin_id': twin.twin_id,
                'profile_type': twin.profile_type.value,
                'behavior_type': pattern.behavior_type,
                'predicted_time': timestamp.isoformat(),
                'confidence': pattern.success_rate * pattern.intensity,
                'risk_score': twin.risk_level * pattern.intensity,
                'time_horizon_hours': hour_offset,
                'adaptation_indicators': {}
            }

            # Location prediction
            location = await self._predict_location(twin, pattern, timestamp)
            prediction['predicted_location'] = location

            # Methodology prediction
            methodology = await self._predict_methodology(twin, pattern)
            prediction['predicted_methodology'] = methodology

            # Target prediction
            target_profile = await self._predict_target(twin, pattern)
            prediction['predicted_target_profile'] = target_profile

            # Adaptation indicators
            adaptation = await self._predict_adaptations(twin, pattern)
            prediction['adaptation_indicators'] = adaptation

            # Counter-detection measures
            counter_detection = await self._predict_counter_detection(twin, pattern)
            prediction['counter_detection_measures'] = counter_detection

            return prediction

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error generating prediction: {str(e)}")
            return {}

    async def _predict_location(self, twin: CriminalTwin, pattern: BehaviorPattern, timestamp: datetime) -> Dict[str, Any]:
        """
        Predict location for criminal activity
        """
        try:
            base_location = pattern.spatial_pattern

            # Add spatial adaptation based on twin's adaptability
            if twin.adaptability_quotient > 0.7:
                # High adaptability: vary location more
                lat_noise = random.uniform(-0.1, 0.1)
                lon_noise = random.uniform(-0.1, 0.1)
            else:
                # Low adaptability: stick to known patterns
                lat_noise = random.uniform(-0.02, 0.02)
                lon_noise = random.uniform(-0.02, 0.02)

            predicted_location = {
                'lat': base_location.get('lat', 28.6139) + lat_noise,
                'lon': base_location.get('lon', 77.2090) + lon_noise,
                'urban_density': base_location.get('urban_density', 'medium'),
                'transport_proximity': base_location.get('transport_proximity', 'medium'),
                'location_confidence': 0.7 + (twin.adaptability_quotient * 0.2)
            }

            return predicted_location

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error predicting location: {str(e)}")
            return {'lat': 28.6139, 'lon': 77.2090, 'urban_density': 'medium'}

    async def _predict_methodology(self, twin: CriminalTwin, pattern: BehaviorPattern) -> Dict[str, Any]:
        """
        Predict criminal methodology
        """
        try:
            methodology = {
                'primary_method': pattern.behavior_type,
                'complexity_level': 'high' if twin.profile_type == CriminalProfileType.PROFESSIONAL else 'medium',
                'technology_usage': 'high' if twin.profile_type == CriminalProfileType.TECH_SAVVY else 'medium',
                'planning_horizon': 'long' if pattern.temporal_pattern.get('planning_horizon') == 'long' else 'short',
                'coordination_level': 'high' if twin.network_influence > 0.7 else 'medium'
            }

            # Adapt methodology based on twin's learning
            if twin.learning_capability > 0.7:
                methodology['adaptation_likelihood'] = 'high'
                methodology['new_techniques'] = True

            return methodology

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error predicting methodology: {str(e)}")
            return {'primary_method': pattern.behavior_type, 'complexity_level': 'medium'}

    async def _predict_target(self, twin: CriminalTwin, pattern: BehaviorPattern) -> Dict[str, Any]:
        """
        Predict target profile
        """
        try:
            template = self.behavior_templates.get(twin.profile_type.value, {})
            behavioral_traits = template.get('behavioral_traits', {})

            target_profile = {
                'demographic': behavioral_traits.get('preferred_demographic', 'general'),
                'tech_sophistication': 'medium' if twin.profile_type == CriminalProfileType.TECH_SAVVY else 'low',
                'financial_capacity': behavioral_traits.get('amount_preferences', ['medium'])[0],
                'vulnerability_factors': ['limited_awareness', 'urgency', 'trust_authority']
            }

            return target_profile

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error predicting target: {str(e)}")
            return {'demographic': 'general', 'tech_sophistication': 'medium'}

    async def _predict_adaptations(self, twin: CriminalTwin, pattern: BehaviorPattern) -> Dict[str, Any]:
        """
        Predict likely adaptations
        """
        try:
            adaptations = {
                'temporal_adaptation': twin.adaptability_quotient > 0.6,
                'spatial_adaptation': twin.adaptability_quotient > 0.7,
                'methodology_adaptation': twin.learning_capability > 0.6,
                'target_adaptation': twin.network_influence > 0.5,
                'adaptation_probability': min(twin.adaptability_quotient * twin.learning_capability, 1.0)
            }

            return adaptations

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error predicting adaptations: {str(e)}")
            return {'adaptation_probability': 0.3}

    async def _predict_counter_detection(self, twin: CriminalTwin, pattern: BehaviorPattern) -> Dict[str, Any]:
        """
        Predict counter-detection measures
        """
        try:
            counter_detection = {
                'digital_anonymity': twin.profile_type == CriminalProfileType.TECH_SAVVY,
                'location_obfuscation': twin.risk_level > 0.7,
                'identity_concealment': twin.profile_type in [CriminalProfileType.PROFESSIONAL, CriminalProfileType.ORGANIZED],
                'communication_encryption': twin.profile_type == CriminalProfileType.TECH_SAVVY,
                'operational_security_level': 'high' if twin.risk_level > 0.8 else 'medium'
            }

            return counter_detection

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error predicting counter-detection: {str(e)}")
            return {'operational_security_level': 'medium'}

    async def learn_from_outcomes(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """
        Learn from actual outcomes to improve twin models
        """
        try:
            logger.info(f"[Behavioral Digital Twin] Learning from {len(feedback_data)} outcomes...")

            learning_results = {
                'twins_updated': 0,
                'patterns_adapted': 0,
                'models_improved': 0,
                'overall_accuracy_change': 0.0
            }

            for feedback in feedback_data:
                # Find relevant twin
                twin_id = feedback.get('twin_id')
                if twin_id in self.criminal_twins:
                    twin = self.criminal_twins[twin_id]
                    await self._update_twin_from_feedback(twin, feedback)
                    learning_results['twins_updated'] += 1

                # Update prediction models
                behavior_type = feedback.get('behavior_type')
                if behavior_type in self.prediction_models:
                    await self._update_prediction_model(behavior_type, feedback)
                    learning_results['models_improved'] += 1

            # Recalculate twin performance metrics
            await self._recalculate_twin_performance()

            logger.info(f"[Behavioral Digital Twin] Learning completed. Updated {learning_results['twins_updated']} twins")

            return learning_results

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error learning from outcomes: {str(e)}")
            return {'error': str(e)}

    async def _update_twin_from_feedback(self, twin: CriminalTwin, feedback: Dict) -> None:
        """
        Update twin model based on feedback
        """
        try:
            outcome = feedback.get('outcome', 'unknown')
            prediction_accuracy = feedback.get('prediction_accuracy', 0.5)

            # Update historical performance
            twin.historical_performance['attempts'] += 1
            if outcome == 'success':
                twin.historical_performance['successes'] += 1

            # Update behavior patterns
            behavior_type = feedback.get('behavior_type')
            for pattern in twin.behavior_patterns:
                if pattern.behavior_type == behavior_type:
                    # Adjust frequency based on success
                    if outcome == 'success':
                        pattern.frequency *= 1.1
                        pattern.success_rate = (pattern.success_rate * 0.8) + (prediction_accuracy * 0.2)
                    else:
                        pattern.frequency *= 0.9
                        pattern.success_rate = (pattern.success_rate * 0.8) + ((1 - prediction_accuracy) * 0.2)

                    # Update adaptability
                    if prediction_accuracy < 0.5:  # Poor prediction
                        pattern.adaptability_score = min(pattern.adaptability_score + 0.1, 1.0)
                        twin.historical_performance['evolutions'] += 1

            # Update twin characteristics
            if prediction_accuracy < 0.4:  # Significant prediction error
                twin.adaptability_quotient = min(twin.adaptability_quotient + 0.05, 1.0)
                twin.learning_capability = min(twin.learning_capability + 0.02, 1.0)

            # Update stress level
            if outcome == 'failure':
                twin.current_state['stress_level'] = min(twin.current_state.get('stress_level', 0.3) + 0.1, 1.0)
            else:
                twin.current_state['stress_level'] = max(twin.current_state.get('stress_level', 0.3) - 0.05, 0.1)

            twin.current_state['last_activity'] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error updating twin: {str(e)}")

    async def _update_prediction_model(self, behavior_type: str, feedback: Dict) -> None:
        """
        Update prediction model based on feedback
        """
        try:
            if behavior_type not in self.prediction_models:
                return

            model = self.prediction_models[behavior_type]
            prediction_accuracy = feedback.get('prediction_accuracy', 0.5)
            timestamp = datetime.fromisoformat(feedback.get('timestamp', datetime.utcnow().isoformat()))
            hour = timestamp.hour

            # Update temporal weights
            current_weight = model['temporal_weights'].get(hour, 1.0)
            adjustment = self.learning_rate * (prediction_accuracy - 0.5)
            model['temporal_weights'][hour] = max(0.1, current_weight + adjustment)

            # Update base probability
            model['base_probability'] = max(0.1, min(0.9,
                model['base_probability'] + self.learning_rate * (prediction_accuracy - 0.5) * 0.1))

            # Update adaptation factor
            if prediction_accuracy < 0.4:
                model['adaptation_factor'] = min(model['adaptation_factor'] + 0.05, 2.0)

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error updating prediction model: {str(e)}")

    async def _recalculate_twin_performance(self) -> None:
        """
        Recalculate performance metrics for all twins
        """
        try:
            for twin in self.criminal_twins.values():
                if twin.historical_performance['attempts'] > 0:
                    success_rate = twin.historical_performance['successes'] / twin.historical_performance['attempts']

                    # Update risk level based on performance
                    if success_rate > 0.8:
                        twin.risk_level = min(twin.risk_level * 1.1, 1.0)
                    elif success_rate < 0.3:
                        twin.risk_level = max(twin.risk_level * 0.9, 0.1)

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error recalculating performance: {str(e)}")

    async def export_twin_analysis(self) -> Dict[str, Any]:
        """
        Export comprehensive twin analysis
        """
        try:
            analysis = {
                'summary': {
                    'total_twins': len(self.criminal_twins),
                    'active_twins': sum(1 for t in self.criminal_twins.values() if t.current_state.get('active', True)),
                    'profile_distribution': {},
                    'avg_risk_level': 0.0,
                    'avg_adaptability': 0.0
                },
                'top_predictions': self.simulation_results[:10],
                'behavior_patterns': {},
                'learning_metrics': {}
            }

            # Profile distribution
            for twin in self.criminal_twins.values():
                profile = twin.profile_type.value
                analysis['summary']['profile_distribution'][profile] = \
                    analysis['summary']['profile_distribution'].get(profile, 0) + 1
                analysis['summary']['avg_risk_level'] += twin.risk_level
                analysis['summary']['avg_adaptability'] += twin.adaptability_quotient

            if len(self.criminal_twins) > 0:
                analysis['summary']['avg_risk_level'] /= len(self.criminal_twins)
                analysis['summary']['avg_adaptability'] /= len(self.criminal_twins)

            # Behavior pattern analysis
            for twin in self.criminal_twins.values():
                for pattern in twin.behavior_patterns:
                    behavior = pattern.behavior_type
                    if behavior not in analysis['behavior_patterns']:
                        analysis['behavior_patterns'][behavior] = {
                            'frequency': 0, 'avg_success': 0, 'count': 0
                        }
                    analysis['behavior_patterns'][behavior]['frequency'] += pattern.frequency
                    analysis['behavior_patterns'][behavior]['avg_success'] += pattern.success_rate
                    analysis['behavior_patterns'][behavior]['count'] += 1

            # Calculate averages for behavior patterns
            for behavior, data in analysis['behavior_patterns'].items():
                if data['count'] > 0:
                    data['avg_success'] /= data['count']

            return analysis

        except Exception as e:
            logger.error(f"[Behavioral Digital Twin] Error exporting analysis: {str(e)}")
            return {}

# Global service instance
behavioral_digital_twin = BehavioralDigitalTwin()