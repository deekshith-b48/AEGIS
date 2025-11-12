"""
Enhanced Federated Causal Graph System for Cross-Bank Intelligence
Advanced implementation with real-time updates, predictive analytics, and federated learning
"""

import asyncio
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Tuple, Optional, Set
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import threading
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

Base = declarative_base()

class CausalRelationshipType(Enum):
    """Types of causal relationships"""
    TEMPORAL_PROPAGATION = "temporal_propagation"
    SPATIAL_CORRELATION = "spatial_correlation"
    SCAM_TYPE_PROPAGATION = "scam_type_propagation"
    MERCHANT_NETWORK = "merchant_network"
    ACCOUNT_PATTERN = "account_pattern"
    BEHAVIORAL_MIMICRY = "behavioral_mimicry"
    FINANCIAL_FLOW = "financial_flow"
    COORDINATED_ATTACK = "coordinated_attack"

class RiskLevel(Enum):
    """Risk levels for causal relationships"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CausalNode:
    """Enhanced node in the causal graph"""
    node_id: str
    node_type: str  # 'bank', 'location', 'scam_type', 'merchant', 'account', 'network'
    properties: Dict[str, Any]
    causal_strength: float = 0.0
    influence_score: float = 0.0
    centrality_metrics: Dict[str, float] = None
    temporal_patterns: Dict[str, Any] = None
    risk_level: RiskLevel = RiskLevel.LOW
    last_updated: datetime = None
    activity_score: float = 0.0
    connectivity_score: float = 0.0

@dataclass
class CausalEdge:
    """Enhanced edge in the causal graph"""
    source_id: str
    target_id: str
    strength: float
    causality_type: CausalRelationshipType
    temporal_lag: int
    confidence: float = 0.0
    evidence: List[Dict] = None
    temporal_decay: float = 1.0
    reinforcement_count: int = 0
    risk_contribution: float = 0.0
    predictive_power: float = 0.0
    last_observed: datetime = None

@dataclass
class CausalChain:
    """Causal chain representing multi-step relationships"""
    chain_id: str
    nodes: List[str]
    edges: List[Tuple[str, str]]
    strength: float
    length: int
    temporal_duration: int
    risk_level: RiskLevel
    predictability_score: float
    evolution_history: List[Dict] = None
    validation_accuracy: float = 0.0

class CausalGraphDatabase(Base):
    """Database model for storing causal graph data"""
    __tablename__ = "causal_graph_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    graph_id = Column(String, nullable=False)
    node_data = Column(JSON, nullable=False)
    edge_data = Column(JSON, nullable=False)
    chain_data = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FederatedCausalGraphService:
    """
    Enhanced Federated Causal Graph Service
    Real-time causal relationship discovery and analysis across banking institutions
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Graph structure
        self.graph = nx.DiGraph()
        self.nodes = {}  # node_id -> CausalNode
        self.edges = {}  # (source_id, target_id) -> CausalEdge
        self.causal_chains = {}  # chain_id -> CausalChain
        self.pattern_signatures = {}

        # Real-time processing
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 7),
            decode_responses=True
        )

        # Database setup
        self.engine = create_engine(config.get('database_url', 'sqlite:///aegis_causal_graph.db'))
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Federated learning
        self.federated_models = {}
        self.local_models = {}
        self.global_model = None

        # Analysis parameters
        self.min_causal_strength = config.get('min_causal_strength', 0.3)
        self.max_temporal_lag = config.get('max_temporal_lag', 72)  # hours
        self.correlation_threshold = config.get('correlation_threshold', 0.6)
        self.decay_rate = config.get('decay_rate', 0.05)
        self.update_interval = config.get('update_interval', 300)  # 5 minutes

        # State management
        self.is_running = False
        self.last_update = None
        self.total_analyses = 0
        self.performance_metrics = {}

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def initialize(self):
        """Initialize the enhanced federated causal graph service"""
        logger.info("Initializing Enhanced Federated Causal Graph Service")

        try:
            # Load existing graph data
            await self._load_graph_from_database()

            # Initialize federated learning models
            await self._initialize_federated_models()

            # Start real-time processing
            self.is_running = True
            update_task = asyncio.create_task(self._continuous_update_loop())

            # Start performance monitoring
            monitor_task = asyncio.create_task(self._performance_monitoring())

            logger.info("Enhanced Federated Causal Graph Service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize service: {str(e)}")
            return False

    async def build_enhanced_causal_graph(self, hours_back: int = 48) -> Dict[str, Any]:
        """
        Build enhanced causal graph with advanced analysis
        """
        try:
            logger.info(f"Building enhanced causal graph for last {hours_back} hours")

            start_time = time.time()

            # Step 1: Collect federated data
            federated_data = await self._collect_comprehensive_federated_data(hours_back)
            if not federated_data:
                return {'success': False, 'error': 'No federated data available'}

            # Step 2: Discover causal nodes
            await self._discover_causal_nodes(federated_data)

            # Step 3: Analyze multi-dimensional causal relationships
            await self._analyze_causal_relationships(federated_data)

            # Step 4: Build causal chains
            await self._build_causal_chains()

            # Step 5: Identify pattern signatures
            await self._identify_pattern_signatures()

            # Step 6: Calculate graph metrics
            await self._calculate_advanced_graph_metrics()

            # Step 7: Update predictive models
            await self._update_predictive_models()

            # Step 8: Store in database
            await self._save_graph_to_database()

            processing_time = time.time() - start_time
            self.last_update = datetime.utcnow()
            self.total_analyses += 1

            result = {
                'success': True,
                'nodes_count': len(self.nodes),
                'edges_count': len(self.edges),
                'causal_chains': len(self.causal_chains),
                'pattern_signatures': len(self.pattern_signatures),
                'processing_time_seconds': processing_time,
                'graph_metrics': self.performance_metrics,
                'risk_distribution': self._calculate_risk_distribution()
            }

            # Cache result
            await self._cache_graph_result(result)

            logger.info(f"Enhanced causal graph built successfully: {result}")
            return result

        except Exception as e:
            logger.error(f"Error building enhanced causal graph: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _collect_comprehensive_federated_data(self, hours_back: int) -> Dict[str, List[Dict]]:
        """Collect comprehensive federated data from all sources"""
        try:
            # Import here to avoid circular imports
            from integrations.cfrcrms_integration import CFCFRMSIntegration
            from integrations.i4c_integration import I4CIntegration
            from integrations.ncrp_integration import NCRPIntegration

            # Initialize integrations
            cfrcrms = CFCFRMSIntegration(self.config.get('cfrcrms_config', {}))
            i4c = I4CIntegration(self.config.get('i4c_config', {}))
            ncrp = NCRPIntegration(self.config.get('ncrp_config', {}))

            # Collect data from all sources
            tasks = [
                cfrcrms.fetch_transaction_data(
                    datetime.utcnow() - timedelta(hours=hours_back),
                    datetime.utcnow()
                ),
                i4c.fetch_historical_crime_data(
                    (datetime.utcnow() - timedelta(days=30)).year,
                    datetime.utcnow().year
                ),
                ncrp.fetch_transaction_data(
                    datetime.utcnow() - timedelta(hours=hours_back),
                    datetime.utcnow()
                )
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            federated_data = {}

            # Process CFCFRMS data
            if not isinstance(results[0], Exception) and results[0]:
                federated_data['cfrcrms'] = results[0]

            # Process I4C data
            if not isinstance(results[1], Exception) and results[1]:
                federated_data['i4c'] = results[1]

            # Process NCRP data
            if not isinstance(results[2], Exception) and results[2]:
                federated_data['ncrp'] = results[2]

            logger.info(f"Collected federated data from {len(federated_data)} sources")
            return federated_data

        except Exception as e:
            logger.error(f"Error collecting federated data: {str(e)}")
            return {}

    async def _discover_causal_nodes(self, federated_data: Dict[str, List[Dict]]) -> None:
        """Discover causal nodes from federated data"""
        try:
            node_discoverers = {
                'cfrcrms': self._discover_nodes_from_cfrcrms,
                'i4c': self._discover_nodes_from_i4c,
                'ncrp': self._discover_nodes_from_ncrp
            }

            for source, data in federated_data.items():
                if source in node_discoverers:
                    await node_discoverers[source](data)

            # Add nodes to NetworkX graph
            for node_id, node in self.nodes.items():
                self.graph.add_node(node_id, **asdict(node))

            logger.info(f"Discovered {len(self.nodes)} causal nodes")

        except Exception as e:
            logger.error(f"Error discovering causal nodes: {str(e)}")

    async def _discover_nodes_from_cfrcrms(self, transactions: List[Dict]) -> None:
        """Discover nodes from CFCFRMS transaction data"""
        try:
            for txn in transactions:
                # Bank nodes
                if 'sender_bank' in txn:
                    bank_id = f"bank_{txn['sender_bank']}"
                    if bank_id not in self.nodes:
                        self.nodes[bank_id] = CausalNode(
                            node_id=bank_id,
                            node_type='bank',
                            properties={'bank_code': txn['sender_bank']},
                            last_updated=datetime.utcnow()
                        )

                    self.nodes[bank_id].properties['transaction_count'] = \
                        self.nodes[bank_id].properties.get('transaction_count', 0) + 1

                # Location nodes
                if 'location_lat' in txn and 'location_lon' in txn:
                    location_id = f"location_{round(txn['location_lat'], 2)}_{round(txn['location_lon'], 2)}"
                    if location_id not in self.nodes:
                        self.nodes[location_id] = CausalNode(
                            node_id=location_id,
                            node_type='location',
                            properties={
                                'latitude': txn['location_lat'],
                                'longitude': txn['location_lon']
                            },
                            last_updated=datetime.utcnow()
                        )

                    self.nodes[location_id].properties['incident_count'] = \
                        self.nodes[location_id].properties.get('incident_count', 0) + 1

                # Scam type nodes
                if 'fraud_indicators' in txn and txn['fraud_indicators']:
                    for indicator in txn['fraud_indicators']:
                        scam_id = f"scam_{indicator}"
                        if scam_id not in self.nodes:
                            self.nodes[scam_id] = CausalNode(
                                node_id=scam_id,
                                node_type='scam_type',
                                properties={'scam_type': indicator},
                                last_updated=datetime.utcnow()
                            )

                        self.nodes[scam_id].properties['frequency'] = \
                            self.nodes[scam_id].properties.get('frequency', 0) + 1

        except Exception as e:
            logger.error(f"Error discovering nodes from CFCFRMS data: {str(e)}")

    async def _discover_nodes_from_i4c(self, crimes: List[Dict]) -> None:
        """Discover nodes from I4C crime data"""
        try:
            for crime in crimes:
                # Geographic nodes
                if 'location_lat' in crime and 'location_lon' in crime:
                    geo_id = f"geo_{round(crime['location_lat'], 1)}_{round(crime['location_lon'], 1)}"
                    if geo_id not in self.nodes:
                        self.nodes[geo_id] = CausalNode(
                            node_id=geo_id,
                            node_type='geographic_region',
                            properties={
                                'latitude': crime['location_lat'],
                                'longitude': crime['location_lon'],
                                'region_type': 'hotspot'
                            },
                            last_updated=datetime.utcnow()
                        )

                    self.nodes[geo_id].properties['crime_count'] = \
                        self.nodes[geo_id].properties.get('crime_count', 0) + 1

                # MO nodes
                if 'modus_operandi' in crime:
                    mo_id = f"mo_{crime['modus_operandi'].replace(' ', '_')}"
                    if mo_id not in self.nodes:
                        self.nodes[mo_id] = CausalNode(
                            node_id=mo_id,
                            node_type='modus_operandi',
                            properties={'method': crime['modus_operandi']},
                            last_updated=datetime.utcnow()
                        )

                    self.nodes[mo_id].properties['usage_count'] = \
                        self.nodes[mo_id].properties.get('usage_count', 0) + 1

        except Exception as e:
            logger.error(f"Error discovering nodes from I4C data: {str(e)}")

    async def _discover_nodes_from_ncrp(self, transactions: List[Dict]) -> None:
        """Discover nodes from NCRP transaction data"""
        try:
            for txn in transactions:
                # Account pattern nodes
                if 'account_hash' in txn:
                    pattern_id = f"account_pattern_{txn['account_hash'][:8]}"
                    if pattern_id not in self.nodes:
                        self.nodes[pattern_id] = CausalNode(
                            node_id=pattern_id,
                            node_type='account_pattern',
                            properties={'pattern_hash': txn['account_hash'][:8]},
                            last_updated=datetime.utcnow()
                        )

                    self.nodes[pattern_id].properties['activity_count'] = \
                        self.nodes[pattern_id].properties.get('activity_count', 0) + 1

        except Exception as e:
            logger.error(f"Error discovering nodes from NCRP data: {str(e)}")

    async def _analyze_causal_relationships(self, federated_data: Dict[str, List[Dict]]) -> None:
        """Analyze multi-dimensional causal relationships"""
        try:
            relationship_analyzers = {
                'temporal': self._analyze_temporal_causal_relationships,
                'spatial': self._analyze_spatial_causal_relationships,
                'scam_propagation': self._analyze_scam_type_propagation,
                'merchant_network': self._analyze_merchant_networks,
                'behavioral': self._analyze_behavioral_patterns,
                'financial_flow': self._analyze_financial_flows
            }

            # Run analyzers in parallel
            tasks = [analyzer(federated_data) for analyzer in relationship_analyzers.values()]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Add edges to NetworkX graph
            for edge_key, edge in self.edges.items():
                self.graph.add_edge(
                    edge.source_id, edge.target_id,
                    **asdict(edge)
                )

            logger.info(f"Discovered {len(self.edges)} causal relationships")

        except Exception as e:
            logger.error(f"Error analyzing causal relationships: {str(e)}")

    async def _analyze_temporal_causal_relationships(self, federated_data: Dict[str, List[Dict]]) -> None:
        """Analyze temporal causal relationships"""
        try:
            # Extract time series data for each node type
            time_series_data = {}

            for source, data in federated_data.items():
                if source == 'cfrcrms':
                    for txn in data:
                        if 'sender_bank' in txn:
                            bank_id = f"bank_{txn['sender_bank']}"
                            timestamp = datetime.fromisoformat(txn.get('timestamp', datetime.utcnow().isoformat()))

                            if bank_id not in time_series_data:
                                time_series_data[bank_id] = []
                            time_series_data[bank_id].append(timestamp)

            # Find temporal correlations
            node_ids = list(time_series_data.keys())
            for i, node1 in enumerate(node_ids):
                for node2 in node_ids[i+1:]:
                    correlation = await self._calculate_temporal_correlation(
                        time_series_data[node1], time_series_data[node2]
                    )

                    if correlation >= self.correlation_threshold:
                        temporal_lag = await self._calculate_temporal_lag(
                            time_series_data[node1], time_series_data[node2]
                        )

                        edge_key = (node1, node2)
                        self.edges[edge_key] = CausalEdge(
                            source_id=node1,
                            target_id=node2,
                            strength=correlation,
                            causality_type=CausalRelationshipType.TEMPORAL_PROPAGATION,
                            temporal_lag=temporal_lag,
                            confidence=correlation,
                            last_observed=datetime.utcnow()
                        )

        except Exception as e:
            logger.error(f"Error analyzing temporal causal relationships: {str(e)}")

    async def _calculate_temporal_correlation(self, series1: List[datetime], series2: List[datetime]) -> float:
        """Calculate temporal correlation between two time series"""
        try:
            # Create hourly counts
            def create_hourly_counts(timestamps):
                counts = defaultdict(int)
                for ts in timestamps:
                    hour_key = ts.replace(minute=0, second=0, microsecond=0)
                    counts[hour_key] += 1
                return counts

            counts1 = create_hourly_counts(series1)
            counts2 = create_hourly_counts(series2)

            # Find common hours
            common_hours = set(counts1.keys()) & set(counts2.keys())
            if len(common_hours) < 3:
                return 0.0

            # Create aligned vectors
            values1 = [counts1[hour] for hour in sorted(common_hours)]
            values2 = [counts2[hour] for hour in sorted(common_hours)]

            # Calculate correlation
            if len(set(values1)) == 1 or len(set(values2)) == 1:
                return 0.0

            correlation = np.corrcoef(values1, values2)[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0

        except Exception as e:
            logger.error(f"Error calculating temporal correlation: {str(e)}")
            return 0.0

    async def _calculate_temporal_lag(self, series1: List[datetime], series2: List[datetime]) -> int:
        """Calculate temporal lag between two time series"""
        try:
            def create_hourly_counts(timestamps):
                counts = defaultdict(int)
                for ts in timestamps:
                    hour_key = ts.replace(minute=0, second=0, microsecond=0)
                    counts[hour_key] += 1
                return counts

            counts1 = create_hourly_counts(series1)
            counts2 = create_hourly_counts(series2)

            if not counts1 or not counts2:
                return 0

            # Find peaks
            peak1 = max(counts1.items(), key=lambda x: x[1])[0] if counts1 else None
            peak2 = max(counts2.items(), key=lambda x: x[1])[0] if counts2 else None

            if peak1 and peak2:
                lag_hours = abs((peak2 - peak1).total_seconds()) / 3600
                return min(int(lag_hours), self.max_temporal_lag)

            return 0

        except Exception as e:
            logger.error(f"Error calculating temporal lag: {str(e)}")
            return 0

    async def _analyze_spatial_causal_relationships(self, federated_data: Dict[str, List[Dict]]) -> None:
        """Analyze spatial causal relationships"""
        try:
            # Group data by location
            location_groups = defaultdict(list)

            for source, data in federated_data.items():
                for item in data:
                    lat = item.get('location_lat') or item.get('latitude')
                    lon = item.get('location_lon') or item.get('longitude')

                    if lat and lon:
                        location_key = f"{round(lat, 1)}_{round(lon, 1)}"
                        location_groups[location_key].append(item)

            # Analyze spatial relationships
            locations = list(location_groups.keys())

            for i, loc1 in enumerate(locations):
                for j, loc2 in enumerate(locations):
                    if i != j:
                        # Extract coordinates
                        lat1, lon1 = map(float, loc1.split('_'))
                        lat2, lon2 = map(float, loc2.split('_'))

                        # Calculate distance
                        distance = self._calculate_distance(lat1, lon1, lat2, lon2)

                        # Spatial correlation decreases with distance
                        if distance <= 50:  # Within 50km
                            correlation = 1.0 - (distance / 50)

                            if correlation >= self.correlation_threshold:
                                loc1_id = f"location_{loc1}"
                                loc2_id = f"location_{loc2}"

                                edge_key = (loc1_id, loc2_id)
                                self.edges[edge_key] = CausalEdge(
                                    source_id=loc1_id,
                                    target_id=loc2_id,
                                    strength=correlation,
                                    causality_type=CausalRelationshipType.SPATIAL_CORRELATION,
                                    temporal_lag=0,
                                    confidence=correlation,
                                    last_observed=datetime.utcnow()
                                )

        except Exception as e:
            logger.error(f"Error analyzing spatial causal relationships: {str(e)}")

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers"""
        from math import radians, cos, sin, asin, sqrt

        lat1, lon1 = radians(lat1), radians(lon1)
        lat2, lon2 = radians(lat2), radians(lon2)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth's radius in kilometers

        return c * r

    async def _analyze_scam_type_propagation(self, federated_data: Dict[str, List[Dict]]) -> None:
        """Analyze scam type propagation patterns"""
        try:
            # Track scam propagation across institutions
            scam_sequences = defaultdict(list)

            for source, data in federated_data.items():
                for item in data:
                    if source == 'cfrcrms':
                        scam_type = item.get('fraud_indicators', ['unknown'])[0]
                        timestamp = datetime.fromisoformat(item.get('timestamp', datetime.utcnow().isoformat()))
                        bank = item.get('sender_bank', 'unknown')

                        scam_sequences[scam_type].append((bank, timestamp))

            # Find propagation patterns
            for scam_type, sequences in scam_sequences.items():
                # Group by bank and sort by time
                bank_sequences = defaultdict(list)
                for bank, timestamp in sequences:
                    bank_sequences[bank].append(timestamp)

                # Sort sequences for each bank
                for bank in bank_sequences:
                    bank_sequences[bank].sort()

                # Find propagation chain
                banks = list(bank_sequences.keys())
                if len(banks) > 1:
                    # Calculate first occurrence times
                    first_occurrences = {}
                    for bank, timestamps in bank_sequences.items():
                        if timestamps:
                            first_occurrences[bank] = min(timestamps)

                    # Sort by first occurrence
                    sorted_banks = sorted(first_occurrences.items(), key=lambda x: x[1])

                    # Create propagation edges
                    for i in range(len(sorted_banks) - 1):
                        bank1, time1 = sorted_banks[i]
                        bank2, time2 = sorted_banks[i + 1]

                        time_diff = (time2 - time1).total_seconds() / 3600

                        if time_diff <= self.max_temporal_lag:
                            node1_id = f"bank_{bank1}"
                            node2_id = f"bank_{bank2}"

                            edge_key = f"{node1_id}_{node2_id}_{scam_type}"
                            strength = max(0.1, 1.0 - (time_diff / self.max_temporal_lag))

                            self.edges[edge_key] = CausalEdge(
                                source_id=node1_id,
                                target_id=node2_id,
                                strength=strength,
                                causality_type=CausalRelationshipType.SCAM_TYPE_PROPAGATION,
                                temporal_lag=int(time_diff),
                                confidence=strength,
                                evidence=[{'scam_type': scam_type, 'first_seen': time1.isoformat()}],
                                last_observed=datetime.utcnow()
                            )

        except Exception as e:
            logger.error(f"Error analyzing scam type propagation: {str(e)}")

    async def _analyze_merchant_networks(self, federated_data: Dict[str, List[Dict]]) -> None:
        """Analyze merchant network relationships"""
        try:
            # Group by merchant
            merchant_data = defaultdict(list)

            for source, data in federated_data.items():
                if source == 'cfrcrms':
                    for item in data:
                        merchant_hash = item.get('merchant_hash')
                        if merchant_hash:
                            merchant_data[merchant_hash].append(item)

            # Find merchants appearing across multiple banks
            for merchant_hash, transactions in merchant_data.items():
                banks_involved = set()
                for txn in transactions:
                    bank = txn.get('sender_bank')
                    if bank:
                        banks_involved.add(bank)

                if len(banks_involved) > 1:
                    # Create network edges between banks
                    banks = list(banks_involved)
                    for i, bank1 in enumerate(banks):
                        for j, bank2 in enumerate(banks):
                            if i != j:
                                node1_id = f"bank_{bank1}"
                                node2_id = f"bank_{bank2}"

                                edge_key = f"merchant_{merchant_hash[:8]}_{node1_id}_{node2_id}"

                                # Calculate risk based on transaction amounts
                                avg_amount = np.mean([t.get('amount', 0) for t in transactions])
                                risk_score = min(avg_amount / 100000, 1.0)  # Normalize by 100k

                                self.edges[edge_key] = CausalEdge(
                                    source_id=node1_id,
                                    target_id=node2_id,
                                    strength=risk_score,
                                    causality_type=CausalRelationshipType.MERCHANT_NETWORK,
                                    temporal_lag=0,
                                    confidence=risk_score,
                                    evidence=[{'merchant_hash': merchant_hash, 'avg_amount': avg_amount}],
                                    last_observed=datetime.utcnow()
                                )

        except Exception as e:
            logger.error(f"Error analyzing merchant networks: {str(e)}")

    async def _analyze_behavioral_patterns(self, federated_data: Dict[str, List[Dict]]) -> None:
        """Analyze behavioral pattern relationships"""
        try:
            # This would analyze similar behaviors across different entities
            # Simplified implementation for demonstration

            behavioral_patterns = defaultdict(list)

            for source, data in federated_data.items():
                for item in data:
                    # Extract behavioral features
                    features = {
                        'amount_range': item.get('amount', 0),
                        'time_of_day': datetime.fromisoformat(item.get('timestamp', datetime.utcnow().isoformat())).hour,
                        'risk_score': item.get('risk_score', 0),
                        'is_off_hours': datetime.fromisoformat(item.get('timestamp', datetime.utcnow().isoformat())).hour < 6 or \
                                      datetime.fromisoformat(item.get('timestamp', datetime.utcnow().isoformat())).hour > 22
                    }

                    pattern_key = f"behavior_{features['time_of_day']//4}_{'high' if features['amount_range'] > 50000 else 'low'}"
                    behavioral_patterns[pattern_key].append((item.get('sender_bank', 'unknown'), features))

            # Find similar behavioral patterns across banks
            for pattern, instances in behavioral_patterns.items():
                banks = set(inst[0] for inst in instances)
                if len(banks) > 1:
                    # Create behavioral similarity edges
                    banks_list = list(banks)
                    for i, bank1 in enumerate(banks_list):
                        for j, bank2 in enumerate(banks_list):
                            if i != j:
                                node1_id = f"bank_{bank1}"
                                node2_id = f"bank_{bank2}"

                                edge_key = f"behavioral_{pattern}_{node1_id}_{node2_id}"

                                self.edges[edge_key] = CausalEdge(
                                    source_id=node1_id,
                                    target_id=node2_id,
                                    strength=0.5,  # Moderate strength for behavioral similarity
                                    causality_type=CausalRelationshipType.BEHAVIORAL_MIMICRY,
                                    temporal_lag=0,
                                    confidence=0.5,
                                    evidence=[{'pattern': pattern, 'instances': len(instances)}],
                                    last_observed=datetime.utcnow()
                                )

        except Exception as e:
            logger.error(f"Error analyzing behavioral patterns: {str(e)}")

    async def _analyze_financial_flows(self, federated_data: Dict[str, List[Dict]]) -> None:
        """Analyze financial flow relationships"""
        try:
            # Track financial flows between entities
            flow_data = defaultdict(list)

            for source, data in federated_data.items():
                if source == 'cfrcrms':
                    for item in data:
                        sender = item.get('sender_bank', 'unknown')
                        receiver = item.get('receiver_bank', 'unknown')
                        amount = item.get('amount', 0)

                        if sender and receiver and sender != receiver:
                            flow_key = f"{sender}_{receiver}"
                            flow_data[flow_key].append(amount)

            # Create financial flow edges
            for flow_key, amounts in flow_data.items():
                sender, receiver = flow_key.split('_')

                if len(amounts) >= 3:  # Minimum transactions for meaningful analysis
                    avg_amount = np.mean(amounts)
                    total_amount = sum(amounts)
                    frequency = len(amounts)

                    # Calculate flow strength based on amount and frequency
                    flow_strength = min((total_amount / 1000000) * (frequency / 10), 1.0)

                    if flow_strength >= self.min_causal_strength:
                        sender_id = f"bank_{sender}"
                        receiver_id = f"bank_{receiver}"

                        edge_key = f"flow_{flow_key}"

                        self.edges[edge_key] = CausalEdge(
                            source_id=sender_id,
                            target_id=receiver_id,
                            strength=flow_strength,
                            causality_type=CausalRelationshipType.FINANCIAL_FLOW,
                            temporal_lag=0,
                            confidence=flow_strength,
                            evidence=[{
                                'avg_amount': avg_amount,
                                'total_amount': total_amount,
                                'frequency': frequency
                            }],
                            last_observed=datetime.utcnow()
                        )

        except Exception as e:
            logger.error(f"Error analyzing financial flows: {str(e)}")

    async def _build_causal_chains(self) -> None:
        """Build multi-step causal chains"""
        try:
            chain_id = 1

            # Find all simple paths of length 3-6
            for source_node in self.graph.nodes():
                for target_node in self.graph.nodes():
                    if source_node != target_node:
                        try:
                            # Find paths of different lengths
                            for path_length in range(3, 7):
                                paths = list(nx.all_simple_paths(
                                    self.graph, source_node, target_node, cutoff=path_length
                                ))

                                for path in paths:
                                    if len(path) == path_length:
                                        chain_strength = self._calculate_chain_strength(path)

                                        if chain_strength >= self.min_causal_strength:
                                            # Calculate temporal duration
                                            temporal_duration = self._calculate_chain_duration(path)

                                            # Determine risk level
                                            risk_level = self._calculate_chain_risk_level(path)

                                            # Calculate predictability
                                            predictability = self._calculate_chain_predictability(path)

                                            chain = CausalChain(
                                                chain_id=f"chain_{chain_id:04d}",
                                                nodes=path,
                                                edges=[(path[i], path[i+1]) for i in range(len(path)-1)],
                                                strength=chain_strength,
                                                length=path_length,
                                                temporal_duration=temporal_duration,
                                                risk_level=risk_level,
                                                predictability_score=predictability,
                                                evolution_history=[],
                                                validation_accuracy=0.0
                                            )

                                            self.causal_chains[chain.chain_id] = chain
                                            chain_id += 1

                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            continue

            # Sort chains by strength
            self.causal_chains = dict(sorted(
                self.causal_chains.items(),
                key=lambda x: x[1].strength,
                reverse=True
            ))

            logger.info(f"Built {len(self.causal_chains)} causal chains")

        except Exception as e:
            logger.error(f"Error building causal chains: {str(e)}")

    def _calculate_chain_strength(self, path: List[str]) -> float:
        """Calculate overall strength of a causal chain"""
        try:
            if len(path) < 2:
                return 0.0

            # Multiply edge strengths along the path
            chain_strength = 1.0
            for i in range(len(path) - 1):
                edge_data = self.graph[path[i]][path[i + 1]]
                edge_strength = edge_data.get('strength', 0)
                chain_strength *= edge_strength

                # Early termination if strength drops too low
                if chain_strength < 0.1:
                    return chain_strength

            return chain_strength

        except Exception as e:
            logger.error(f"Error calculating chain strength: {str(e)}")
            return 0.0

    def _calculate_chain_duration(self, path: List[str]) -> int:
        """Calculate temporal duration of a causal chain"""
        try:
            total_lag = 0
            for i in range(len(path) - 1):
                edge_data = self.graph[path[i]][path[i + 1]]
                temporal_lag = edge_data.get('temporal_lag', 0)
                total_lag += temporal_lag

            return total_lag

        except Exception as e:
            logger.error(f"Error calculating chain duration: {str(e)}")
            return 0

    def _calculate_chain_risk_level(self, path: List[str]) -> RiskLevel:
        """Calculate risk level of a causal chain"""
        try:
            risk_scores = []

            # Collect risk from nodes and edges
            for node_id in path:
                if node_id in self.nodes:
                    node = self.nodes[node_id]
                    if hasattr(node, 'risk_level'):
                        risk_scores.append({
                            RiskLevel.LOW: 0.25,
                            RiskLevel.MEDIUM: 0.5,
                            RiskLevel.HIGH: 0.75,
                            RiskLevel.CRITICAL: 1.0
                        }.get(node.risk_level, 0.5))

            for i in range(len(path) - 1):
                edge_data = self.graph[path[i]][path[i + 1]]
                edge_strength = edge_data.get('strength', 0)
                risk_scores.append(edge_strength)

            if not risk_scores:
                return RiskLevel.LOW

            avg_risk = np.mean(risk_scores)

            if avg_risk >= 0.8:
                return RiskLevel.CRITICAL
            elif avg_risk >= 0.6:
                return RiskLevel.HIGH
            elif avg_risk >= 0.4:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        except Exception as e:
            logger.error(f"Error calculating chain risk level: {str(e)}")
            return RiskLevel.LOW

    def _calculate_chain_predictability(self, path: List[str]) -> float:
        """Calculate predictability score of a causal chain"""
        try:
            # Base predictability on edge confidence values
            confidence_scores = []

            for i in range(len(path) - 1):
                edge_data = self.graph[path[i]][path[i + 1]]
                confidence = edge_data.get('confidence', 0)
                confidence_scores.append(confidence)

            if not confidence_scores:
                return 0.5

            # Predictability is the average confidence
            predictability = np.mean(confidence_scores)

            # Adjust for chain length (longer chains are less predictable)
            length_penalty = min(0.1 * (len(path) - 3), 0.3)
            predictability = max(0.1, predictability - length_penalty)

            return predictability

        except Exception as e:
            logger.error(f"Error calculating chain predictability: {str(e)}")
            return 0.5

    async def _identify_pattern_signatures(self) -> None:
        """Identify repeating causal patterns (signatures)"""
        try:
            # Group chains by structural patterns
            pattern_groups = defaultdict(list)

            for chain_id, chain in self.causal_chains.items():
                # Create signature from node types and edge types
                signature_parts = []

                for i in range(len(chain.nodes) - 1):
                    source_node = self.nodes.get(chain.nodes[i])
                    target_node = self.nodes.get(chain.nodes[i + 1])
                    edge_data = self.graph[chain.nodes[i]][chain.nodes[i + 1]]

                    if source_node and target_node:
                        signature_parts.append(
                            f"{source_node.node_type}->{edge_data.get('causality_type', 'unknown')->value}->{target_node.node_type}"
                        )

                signature = " -> ".join(signature_parts)
                pattern_groups[signature].append(chain)

            # Identify significant patterns
            for signature, chains in pattern_groups.items():
                if len(chains) >= 2:  # Pattern appears at least twice
                    avg_strength = np.mean([c.strength for c in chains])
                    avg_predictability = np.mean([c.predictability_score for c in chains])

                    self.pattern_signatures[signature] = {
                        'frequency': len(chains),
                        'avg_strength': avg_strength,
                        'avg_predictability': avg_predictability,
                        'avg_length': np.mean([c.length for c in chains]),
                        'risk_distribution': Counter([c.risk_level.value for c in chains]),
                        'example_chains': [c.chain_id for c in chains[:3]]  # Top 3 examples
                    }

            logger.info(f"Identified {len(self.pattern_signatures)} pattern signatures")

        except Exception as e:
            logger.error(f"Error identifying pattern signatures: {str(e)}")

    async def _calculate_advanced_graph_metrics(self) -> None:
        """Calculate advanced graph metrics"""
        try:
            metrics = {}

            if self.graph.number_of_nodes() > 0:
                # Basic metrics
                metrics['node_count'] = self.graph.number_of_nodes()
                metrics['edge_count'] = self.graph.number_of_edges()
                metrics['density'] = nx.density(self.graph)

                # Centrality measures
                degree_centrality = nx.degree_centrality(self.graph)
                betweenness_centrality = nx.betweenness_centrality(self.graph)
                closeness_centrality = nx.closeness_centrality(self.graph)

                # Update node centrality metrics
                for node_id in self.nodes:
                    if node_id in degree_centrality:
                        if not self.nodes[node_id].centrality_metrics:
                            self.nodes[node_id].centrality_metrics = {}

                        self.nodes[node_id].centrality_metrics.update({
                            'degree': degree_centrality[node_id],
                            'betweenness': betweenness_centrality[node_id],
                            'closeness': closeness_centrality[node_id]
                        })

                # Most influential nodes
                metrics['most_central_nodes'] = sorted(
                    degree_centrality.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]

                # Connected components
                metrics['connected_components'] = nx.number_connected_components(self.graph.to_undirected())

                # Clustering coefficient
                metrics['avg_clustering'] = nx.average_clustering(self.graph.to_undirected())

                # Path analysis
                if nx.is_weakly_connected(self.graph):
                    metrics['avg_shortest_path'] = nx.average_shortest_path_length(self.graph)
                    metrics['diameter'] = nx.diameter(self.graph)

                # Node risk distribution
                risk_counts = Counter([node.risk_level.value for node in self.nodes.values()])
                metrics['risk_distribution'] = dict(risk_counts)

                # Edge type distribution
                edge_types = Counter([edge.causality_type.value for edge in self.edges.values()])
                metrics['edge_type_distribution'] = dict(edge_types)

            self.performance_metrics = metrics
            logger.info(f"Calculated advanced graph metrics: {len(metrics)} metrics")

        except Exception as e:
            logger.error(f"Error calculating advanced graph metrics: {str(e)}")

    def _calculate_risk_distribution(self) -> Dict[str, Any]:
        """Calculate risk distribution across the graph"""
        try:
            if not self.nodes:
                return {}

            risk_counts = Counter([node.risk_level.value for node in self.nodes.values()])
            total_nodes = len(self.nodes)

            distribution = {
                'counts': dict(risk_counts),
                'percentages': {
                    risk_level: (count / total_nodes) * 100
                    for risk_level, count in risk_counts.items()
                },
                'high_risk_percentage': (
                    (risk_counts.get('high', 0) + risk_counts.get('critical', 0)) / total_nodes
                ) * 100
            }

            return distribution

        except Exception as e:
            logger.error(f"Error calculating risk distribution: {str(e)}")
            return {}

    async def predict_cross_bank_threats(self, target_bank: str, hours_ahead: int = 24) -> Dict[str, Any]:
        """Predict cross-bank threats using causal graph analysis"""
        try:
            target_node_id = f"bank_{target_bank}"

            if target_node_id not in self.nodes:
                return {
                    'threat_score': 0.0,
                    'risk_level': RiskLevel.LOW.value,
                    'threat_factors': [],
                    'recommendations': []
                }

            # Find incoming causal relationships
            incoming_edges = []
            for edge_key, edge in self.edges.items():
                if edge.target_id == target_node_id:
                    incoming_edges.append(edge)

            # Calculate threat score
            threat_score = 0.0
            threat_factors = []

            for edge in incoming_edges:
                edge_contribution = edge.strength * edge.confidence

                # Adjust for temporal decay
                if edge.last_observed:
                    hours_since_observed = (datetime.utcnow() - edge.last_observed).total_seconds() / 3600
                    temporal_decay = max(0.1, 1.0 - (hours_since_observed / 168))  # Decay over 1 week
                    edge_contribution *= temporal_decay

                threat_score += edge_contribution

                # Add threat factor details
                factor = {
                    'source_entity': edge.source_id,
                    'relationship_type': edge.causality_type.value,
                    'strength': edge.strength,
                    'confidence': edge.confidence,
                    'temporal_lag': edge.temporal_lag,
                    'evidence_count': len(edge.evidence) if edge.evidence else 0
                }
                threat_factors.append(factor)

            # Normalize threat score
            threat_score = min(threat_score, 1.0)

            # Determine risk level
            if threat_score >= 0.8:
                risk_level = RiskLevel.CRITICAL
            elif threat_score >= 0.6:
                risk_level = RiskLevel.HIGH
            elif threat_score >= 0.4:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW

            # Generate recommendations
            recommendations = self._generate_threat_recommendations(threat_factors, risk_level)

            # Check for relevant causal chains
            relevant_chains = []
            for chain_id, chain in self.causal_chains.items():
                if target_node_id in chain.nodes and chain.strength >= 0.5:
                    relevant_chains.append({
                        'chain_id': chain_id,
                        'strength': chain.strength,
                        'length': chain.length,
                        'risk_level': chain.risk_level.value,
                        'predictability': chain.predictability_score
                    })

            # Sort threat factors by contribution
            threat_factors.sort(key=lambda x: x['strength'] * x['confidence'], reverse=True)

            return {
                'target_bank': target_bank,
                'threat_score': threat_score,
                'risk_level': risk_level.value,
                'prediction_horizon_hours': hours_ahead,
                'threat_factors': threat_factors[:10],  # Top 10 factors
                'relevant_causal_chains': relevant_chains[:5],  # Top 5 chains
                'recommendations': recommendations,
                'prediction_confidence': min(0.9, len(incoming_edges) / 10),
                'last_analysis': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error predicting cross-bank threats: {str(e)}")
            return {
                'threat_score': 0.0,
                'risk_level': RiskLevel.LOW.value,
                'error': str(e)
            }

    def _generate_threat_recommendations(self, threat_factors: List[Dict], risk_level: RiskLevel) -> List[str]:
        """Generate threat mitigation recommendations"""
        recommendations = []

        # Based on relationship types
        relationship_types = [factor['relationship_type'] for factor in threat_factors]

        if 'temporal_propagation' in relationship_types:
            recommendations.append("Monitor for time-based attack patterns")
            recommendations.append("Implement time-series anomaly detection")

        if 'scam_type_propagation' in relationship_types:
            recommendations.append("Enhance scam type detection and blocking")
            recommendations.append("Share scam intelligence with partner banks")

        if 'merchant_network' in relationship_types:
            recommendations.append("Screen high-risk merchants more thoroughly")
            recommendations.append("Implement merchant behavior monitoring")

        if 'financial_flow' in relationship_types:
            recommendations.append("Monitor unusual financial flow patterns")
            recommendations.append("Implement transaction limit controls")

        # Based on risk level
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("IMMEDIATE: Implement enhanced monitoring and alerting")
            recommendations.append("Consider temporary account restrictions")
        elif risk_level == RiskLevel.HIGH:
            recommendations.append("Increase monitoring frequency and sensitivity")
            recommendations.append("Prepare incident response protocols")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Maintain standard monitoring protocols")
            recommendations.append("Review and update detection rules")

        return recommendations

    async def _continuous_update_loop(self):
        """Continuous loop for updating the causal graph"""
        while self.is_running:
            try:
                logger.info("Starting scheduled causal graph update")

                # Update with latest data
                result = await self.build_enhanced_causal_graph(hours_back=24)

                if result.get('success'):
                    logger.info(f"Scheduled update completed: {result['nodes_count']} nodes, {result['edges_count']} edges")
                else:
                    logger.error(f"Scheduled update failed: {result.get('error', 'Unknown error')}")

                # Wait for next update
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"Error in continuous update loop: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _performance_monitoring(self):
        """Monitor system performance and health"""
        while self.is_running:
            try:
                # Calculate performance metrics
                current_time = datetime.utcnow()
                uptime = (current_time - (self.last_update or current_time)).total_seconds()

                performance_data = {
                    'uptime_hours': uptime / 3600,
                    'total_analyses': self.total_analyses,
                    'nodes_count': len(self.nodes),
                    'edges_count': len(self.edges),
                    'chains_count': len(self.causal_chains),
                    'patterns_count': len(self.pattern_signatures),
                    'memory_usage': self._estimate_memory_usage(),
                    'graph_density': nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0,
                    'last_update': self.last_update.isoformat() if self.last_update else None,
                    'is_healthy': self._check_system_health()
                }

                # Cache performance data
                self.redis_client.setex(
                    "causal_graph_performance",
                    300,  # 5 minutes
                    json.dumps(performance_data, default=str)
                )

                # Log performance metrics
                logger.info(f"Performance metrics: {performance_data}")

                # Wait for next monitoring cycle
                await asyncio.sleep(300)  # 5 minutes

            except Exception as e:
                logger.error(f"Error in performance monitoring: {str(e)}")
                await asyncio.sleep(60)

    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage of the graph"""
        try:
            # Rough estimation
            node_memory = len(self.nodes) * 1024  # 1KB per node
            edge_memory = len(self.edges) * 512     # 512B per edge
            chain_memory = len(self.causal_chains) * 2048  # 2KB per chain

            total_bytes = node_memory + edge_memory + chain_memory

            if total_bytes < 1024:
                return f"{total_bytes} B"
            elif total_bytes < 1024 * 1024:
                return f"{total_bytes / 1024:.1f} KB"
            else:
                return f"{total_bytes / (1024 * 1024):.1f} MB"

        except Exception:
            return "Unknown"

    def _check_system_health(self) -> bool:
        """Check overall system health"""
        try:
            # Check if components are responding
            health_checks = [
                len(self.nodes) > 0,
                len(self.edges) > 0,
                self.last_update is not None,
                (datetime.utcnow() - self.last_update).total_seconds() < 3600  # Updated within last hour
            ]

            return all(health_checks)

        except Exception:
            return False

    async def _initialize_federated_models(self):
        """Initialize federated learning models"""
        try:
            # Initialize basic federated learning structure
            self.federated_models = {
                'causal_strength_predictor': {
                    'model_type': 'linear_regression',
                    'features': ['temporal_lag', 'edge_type', 'source_risk', 'target_risk'],
                    'model': None,
                    'accuracy': 0.0
                }
            }

            logger.info("Federated learning models initialized")

        except Exception as e:
            logger.error(f"Error initializing federated models: {str(e)}")

    async def _update_predictive_models(self):
        """Update predictive models with new data"""
        try:
            # Prepare training data from edges
            training_data = []
            for edge in self.edges.values():
                features = [
                    edge.temporal_lag,
                    hash(edge.causality_type.value) % 100,  # Encode edge type
                    self.nodes.get(edge.source_id, CausalNode("", "", {})).risk_level.value == 'high',
                    self.nodes.get(edge.target_id, CausalNode("", "", {})).risk_level.value == 'high'
                ]
                target = edge.strength

                training_data.append((features, target))

            # Update models (simplified for demonstration)
            if len(training_data) > 10:
                # In practice, this would use actual ML libraries
                for model_name, model_info in self.federated_models.items():
                    # Simple accuracy calculation
                    predictions = [0.5] * len(training_data)  # Dummy predictions
                    actuals = [target for _, target in training_data]

                    mse = np.mean([(p - a) ** 2 for p, a in zip(predictions, actuals)])
                    accuracy = max(0, 1 - mse)

                    model_info['accuracy'] = accuracy

            logger.info("Predictive models updated")

        except Exception as e:
            logger.error(f"Error updating predictive models: {str(e)}")

    async def _save_graph_to_database(self):
        """Save graph data to database"""
        try:
            db = self.SessionLocal()
            try:
                # Serialize graph data
                node_data = {node_id: asdict(node) for node_id, node in self.nodes.items()}
                edge_data = {f"{k[0]}_{k[1]}": asdict(edge) for k, edge in self.edges.items()}
                chain_data = {chain_id: asdict(chain) for chain_id, chain in self.causal_chains.items()}

                # Create database record
                graph_record = CausalGraphDatabase(
                    graph_id=f"graph_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    node_data=node_data,
                    edge_data=edge_data,
                    chain_data=chain_data,
                    metadata={
                        'nodes_count': len(self.nodes),
                        'edges_count': len(self.edges),
                        'chains_count': len(self.causal_chains),
                        'patterns_count': len(self.pattern_signatures),
                        'performance_metrics': self.performance_metrics
                    }
                )

                db.add(graph_record)
                db.commit()

                logger.info("Graph data saved to database")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error saving graph to database: {str(e)}")

    async def _load_graph_from_database(self):
        """Load graph data from database"""
        try:
            db = self.SessionLocal()
            try:
                # Get latest graph record
                latest_record = db.query(CausalGraphDatabase).order_by(
                    CausalGraphDatabase.created_at.desc()
                ).first()

                if latest_record:
                    # Load nodes
                    for node_id, node_data in latest_record.node_data.items():
                        node_data['last_updated'] = datetime.fromisoformat(node_data['last_updated']) if node_data.get('last_updated') else datetime.utcnow()
                        self.nodes[node_id] = CausalNode(**node_data)

                    # Load edges
                    for edge_key, edge_data in latest_record.edge_data.items():
                        source_id, target_id = edge_key.split('_', 1)
                        edge_data['causality_type'] = CausalRelationshipType(edge_data['causality_type'])
                        edge_data['last_observed'] = datetime.fromisoformat(edge_data['last_observed']) if edge_data.get('last_observed') else datetime.utcnow()

                        edge = CausalEdge(
                            source_id=source_id,
                            target_id=target_id,
                            **{k: v for k, v in edge_data.items() if k not in ['source_id', 'target_id']}
                        )
                        self.edges[(source_id, target_id)] = edge

                    # Load chains
                    if latest_record.chain_data:
                        for chain_id, chain_data in latest_record.chain_data.items():
                            chain_data['risk_level'] = RiskLevel(chain_data['risk_level'])
                            self.causal_chains[chain_id] = CausalChain(**chain_data)

                    # Rebuild NetworkX graph
                    for node_id, node in self.nodes.items():
                        self.graph.add_node(node_id, **asdict(node))

                    for edge_key, edge in self.edges.items():
                        self.graph.add_edge(edge.source_id, edge.target_id, **asdict(edge))

                    logger.info(f"Loaded graph from database: {len(self.nodes)} nodes, {len(self.edges)} edges")

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error loading graph from database: {str(e)}")

    async def _cache_graph_result(self, result: Dict[str, Any]):
        """Cache graph analysis result"""
        try:
            self.redis_client.setex(
                "latest_causal_graph_analysis",
                3600,  # 1 hour
                json.dumps(result, default=str)
            )

        except Exception as e:
            logger.error(f"Error caching graph result: {str(e)}")

    async def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get comprehensive causal graph analysis"""
        try:
            # Get latest cached result
            cached_result = self.redis_client.get("latest_causal_graph_analysis")
            if cached_result:
                return json.loads(cached_result)

            # Generate new analysis if not cached
            return await self.build_enhanced_causal_graph(hours_back=24)

        except Exception as e:
            logger.error(f"Error getting comprehensive analysis: {str(e)}")
            return {'error': str(e)}

    async def export_graph_visualization_data(self) -> Dict[str, Any]:
        """Export graph data for visualization"""
        try:
            nodes_data = []
            edges_data = []

            # Prepare nodes data
            for node_id, node in self.nodes.items():
                nodes_data.append({
                    'id': node_id,
                    'type': node.node_type,
                    'properties': node.properties,
                    'risk_level': node.risk_level.value,
                    'centrality': node.centrality_metrics or {},
                    'activity_score': node.activity_score,
                    'connectivity_score': node.connectivity_score
                })

            # Prepare edges data
            for edge_key, edge in self.edges.items():
                edges_data.append({
                    'source': edge.source_id,
                    'target': edge.target_id,
                    'strength': edge.strength,
                    'type': edge.causality_type.value,
                    'temporal_lag': edge.temporal_lag,
                    'confidence': edge.confidence,
                    'risk_contribution': edge.risk_contribution
                })

            return {
                'nodes': nodes_data,
                'edges': edges_data,
                'metrics': self.performance_metrics,
                'chains': [
                    {
                        'id': chain_id,
                        'nodes': chain.nodes,
                        'strength': chain.strength,
                        'risk_level': chain.risk_level.value,
                        'predictability': chain.predictability_score
                    }
                    for chain_id, chain in list(self.causal_chains.items())[:10]  # Top 10 chains
                ],
                'patterns': self.pattern_signatures
            }

        except Exception as e:
            logger.error(f"Error exporting visualization data: {str(e)}")
            return {'nodes': [], 'edges': [], 'error': str(e)}

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up Enhanced Federated Causal Graph Service")

            self.is_running = False

            if self.executor:
                self.executor.shutdown(wait=True)

            if self.redis_client:
                self.redis_client.close()

            logger.info("Enhanced Federated Causal Graph Service cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Factory function
async def create_enhanced_federated_causal_graph(config: Dict[str, Any]) -> FederatedCausalGraphService:
    """Create and initialize enhanced federated causal graph service"""
    service = FederatedCausalGraphService(config)
    success = await service.initialize()

    if not success:
        raise Exception("Failed to initialize Enhanced Federated Causal Graph Service")

    return service

# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'redis_host': 'localhost',
        'redis_port': 6379,
        'database_url': 'sqlite:///aegis_causal_graph.db',
        'min_causal_strength': 0.3,
        'max_temporal_lag': 72,
        'correlation_threshold': 0.6,
        'update_interval': 300
    }

    async def main():
        # Create service
        service = await create_enhanced_federated_causal_graph(config)

        try:
            # Build causal graph
            result = await service.build_enhanced_causal_graph(hours_back=48)
            print(f"Causal graph result: {result}")

            # Get comprehensive analysis
            analysis = await service.get_comprehensive_analysis()
            print(f"Analysis: {analysis}")

            # Export visualization data
            viz_data = await service.export_graph_visualization_data()
            print(f"Visualization data: {len(viz_data['nodes'])} nodes, {len(viz_data['edges'])} edges")

            # Predict threats for a sample bank
            threats = await service.predict_cross_bank_threats("HDFC")
            print(f"Threat prediction: {threats}")

            # Keep service running
            while True:
                await asyncio.sleep(60)

        except KeyboardInterrupt:
            logger.info("Shutting down Enhanced Federated Causal Graph Service")
        finally:
            await service.cleanup()

    # Run the service
    asyncio.run(main())