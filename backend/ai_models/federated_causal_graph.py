"""
Federated Causal Graph for Cross-Bank Intelligence
Analyzes causal relationships between cybercrime patterns across different banks
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
from sqlalchemy.orm import Session
from app.database import SessionLocal
from sqlalchemy import text
from data_sources.bank_integration import bank_integration
from data_sources.ncrp_integration import ncrp_integration
import statistics

logger = logging.getLogger(__name__)

class CausalNode:
    """
    Represents a node in the causal graph (bank, location, scam type, etc.)
    """

    def __init__(self, node_id: str, node_type: str, properties: Dict):
        self.node_id = node_id
        self.node_type = node_type  # 'bank', 'location', 'scam_type', 'merchant', 'account'
        self.properties = properties
        self.causal_strength = 0.0
        self.influence_score = 0.0
        self temporality = {}  # Time-based influence patterns

class CausalEdge:
    """
    Represents a causal relationship between nodes
    """

    def __init__(self, source_id: str, target_id: str, strength: float,
                 causality_type: str, temporal_lag: int):
        self.source_id = source_id
        self.target_id = target_id
        self.strength = strength  # Causal strength (0-1)
        self.causality_type = causality_type  # 'direct', 'indirect', 'correlational'
        self.temporal_lag = temporal_lag  # Time lag in hours
        self.confidence = 0.0
        self.evidence = []  # Supporting evidence

class FederatedCausalGraph:
    """
    Federated Causal Graph for analyzing cross-bank cybercrime patterns
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = {}  # node_id -> CausalNode
        self.edges = {}  # (source_id, target_id) -> CausalEdge
        self.causal_chains = []  # Discovered causal chains
        self.pattern_signatures = {}  # Repeating causal patterns

        # Causal analysis parameters
        self.min_causal_strength = 0.3
        self.max_temporal_lag = 72  # hours
        self.correlation_threshold = 0.6

    async def build_federated_graph(self, hours_back: int = 48) -> Dict[str, Any]:
        """
        Build causal graph from federated bank data
        """
        try:
            logger.info("[Federated Causal Graph] Building federated causal graph...")

            # Step 1: Collect data from all banks
            bank_data = await self._collect_federated_data(hours_back)
            if not bank_data:
                raise ValueError("No federated data available")

            # Step 2: Identify causal nodes
            await self._identify_causal_nodes(bank_data)

            # Step 3: Discover causal relationships
            await self._discover_causal_relationships(bank_data)

            # Step 4: Analyze causal chains
            await self._analyze_causal_chains()

            # Step 5: Identify pattern signatures
            await self._identify_pattern_signatures()

            logger.info(f"[Federated Causal Graph] Built graph with {len(self.nodes)} nodes and {len(self.edges)} edges")

            return {
                'success': True,
                'nodes_count': len(self.nodes),
                'edges_count': len(self.edges),
                'causal_chains': len(self.causal_chains),
                'pattern_signatures': len(self.pattern_signatures),
                'graph_metrics': self._calculate_graph_metrics()
            }

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error building graph: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _collect_federated_data(self, hours_back: int) -> Dict[str, List[Dict]]:
        """
        Collect transaction data from all banks
        """
        try:
            # Get suspicious transactions from all banks
            suspicious_txns = await bank_integration.get_suspicious_transactions(hours_back, 0.5)
            ncrp_complaints = await ncrp_integration.get_complaints_batch(limit=200, offset=0)

            # Group by bank
            federated_data = defaultdict(list)

            for txn in suspicious_txns:
                bank_code = txn['bank_code']
                federated_data[bank_code].append(txn)

            # Add NCRP data as separate source
            federated_data['NCRP'] = ncrp_complaints

            return dict(federated_data)

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error collecting federated data: {str(e)}")
            return {}

    async def _identify_causal_nodes(self, federated_data: Dict[str, List[Dict]]) -> None:
        """
        Identify causal nodes from federated data
        """
        try:
            for source, transactions in federated_data.items():
                for txn in transactions:
                    # Bank nodes
                    if source != 'NCRP':
                        bank_node_id = f"bank_{source}"
                        if bank_node_id not in self.nodes:
                            self.nodes[bank_node_id] = CausalNode(
                                bank_node_id, 'bank',
                                {'bank_code': source, 'transaction_count': 0}
                            )
                        self.nodes[bank_node_id].properties['transaction_count'] += 1

                    # Location nodes (spatial clustering)
                    if 'location' in txn:
                        location_key = self._get_location_key(txn['location'])
                        location_node_id = f"location_{location_key}"

                        if location_node_id not in self.nodes:
                            self.nodes[location_node_id] = CausalNode(
                                location_node_id, 'location',
                                {'coordinates': txn['location'], 'incident_count': 0}
                            )
                        self.nodes[location_node_id].properties['incident_count'] += 1

                    # Scam type nodes
                    if 'scam_type' in txn:
                        scam_node_id = f"scam_{txn['scam_type']}"
                        if scam_node_id not in self.nodes:
                            self.nodes[scam_node_id] = CausalNode(
                                scam_node_id, 'scam_type',
                                {'scam_type': txn['scam_type'], 'frequency': 0}
                            )
                        self.nodes[scam_node_id].properties['frequency'] += 1

                    # Merchant nodes (for digital transactions)
                    if 'merchant_hash' in txn and txn['merchant_hash']:
                        merchant_node_id = f"merchant_{txn['merchant_hash'][:8]}"
                        if merchant_node_id not in self.nodes:
                            self.nodes[merchant_node_id] = CausalNode(
                                merchant_node_id, 'merchant',
                                {'merchant_hash': txn['merchant_hash'], 'transaction_count': 0}
                            )
                        self.nodes[merchant_node_id].properties['transaction_count'] += 1

                    # Account pattern nodes (behavioral)
                    if 'account_hash' in txn:
                        account_pattern = self._get_account_pattern(txn)
                        pattern_node_id = f"pattern_{account_pattern}"

                        if pattern_node_id not in self.nodes:
                            self.nodes[pattern_node_id] = CausalNode(
                                pattern_node_id, 'account_pattern',
                                {'pattern': account_pattern, 'occurrences': 0}
                            )
                        self.nodes[pattern_node_id].properties['occurrences'] += 1

            # Add nodes to networkx graph
            for node_id, node in self.nodes.items():
                self.graph.add_node(node_id, **node.properties, node_type=node.node_type)

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error identifying nodes: {str(e)}")

    def _get_location_key(self, location: Dict[str, float], precision: float = 0.1) -> str:
        """
        Get location key for spatial clustering
        """
        lat_rounded = round(location['lat'] / precision) * precision
        lon_rounded = round(location['lon'] / precision) * precision
        return f"{lat_rounded:.1f}_{lon_rounded:.1f}"

    def _get_account_pattern(self, txn: Dict) -> str:
        """
        Extract behavioral pattern from account transaction
        """
        pattern_parts = []

        # Transaction amount range
        amount = txn.get('amount', 0)
        if amount < 1000:
            pattern_parts.append('low_amount')
        elif amount < 10000:
            pattern_parts.append('medium_amount')
        else:
            pattern_parts.append('high_amount')

        # Time pattern
        if 'timestamp' in txn:
            timestamp = datetime.fromisoformat(txn['timestamp'])
            if 22 <= timestamp.hour or timestamp.hour <= 5:
                pattern_parts.append('off_hours')
            else:
                pattern_parts.append('business_hours')

        # Risk level
        risk_score = txn.get('risk_score', 0)
        if risk_score >= 0.8:
            pattern_parts.append('high_risk')
        elif risk_score >= 0.5:
            pattern_parts.append('medium_risk')
        else:
            pattern_parts.append('low_risk')

        return '_'.join(pattern_parts)

    async def _discover_causal_relationships(self, federated_data: Dict[str, List[Dict]]) -> None:
        """
        Discover causal relationships between nodes using temporal analysis
        """
        try:
            # Analyze temporal correlations across banks
            await self._analyze_cross_bank_temporal_patterns(federated_data)

            # Analyze spatial causal relationships
            await self._analyze_spatial_causal_patterns(federated_data)

            # Analyze scam type propagation
            await self._analyze_scam_type_propagation(federated_data)

            # Analyze merchant-to-merchant relationships
            await self._analyze_merchant_networks(federated_data)

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error discovering relationships: {str(e)}")

    async def _analyze_cross_bank_temporal_patterns(self, federated_data: Dict[str, List[Dict]]) -> None:
        """
        Analyze temporal patterns across different banks
        """
        try:
            banks = [k for k in federated_data.keys() if k != 'NCRP']

            for i, bank1 in enumerate(banks):
                for bank2 in banks[i+1:]:
                    correlation = await self._calculate_temporal_correlation(
                        federated_data[bank1], federated_data[bank2]
                    )

                    if correlation >= self.correlation_threshold:
                        # Create causal edge
                        edge_key = (f"bank_{bank1}", f"bank_{bank2}")
                        temporal_lag = await self._calculate_temporal_lag(
                            federated_data[bank1], federated_data[bank2]
                        )

                        self.edges[edge_key] = CausalEdge(
                            f"bank_{bank1}", f"bank_{bank2}",
                            correlation, 'correlational', temporal_lag
                        )

                        self.graph.add_edge(
                            f"bank_{bank1}", f"bank_{bank2}",
                            strength=correlation, type='correlational',
                            temporal_lag=temporal_lag
                        )

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error analyzing temporal patterns: {str(e)}")

    async def _calculate_temporal_correlation(self, data1: List[Dict], data2: List[Dict]) -> float:
        """
        Calculate temporal correlation between two datasets
        """
        try:
            # Create time series for both datasets
            time_series1 = await self._create_time_series(data1)
            time_series2 = await self._create_time_series(data2)

            if len(time_series1) == 0 or len(time_series2) == 0:
                return 0.0

            # Align time series
            common_hours = set(time_series1.keys()) & set(time_series2.keys())
            if len(common_hours) < 3:  # Need at least 3 data points
                return 0.0

            values1 = [time_series1[hour] for hour in sorted(common_hours)]
            values2 = [time_series2[hour] for hour in sorted(common_hours)]

            # Calculate correlation
            if len(set(values1)) == 1 or len(set(values2)) == 1:
                return 0.0  # No variance

            correlation = np.corrcoef(values1, values2)[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error calculating correlation: {str(e)}")
            return 0.0

    async def _create_time_series(self, data: List[Dict]) -> Dict[int, int]:
        """
        Create hourly time series from transaction data
        """
        time_series = defaultdict(int)

        for item in data:
            if 'timestamp' in item:
                timestamp = datetime.fromisoformat(item['timestamp'])
                hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                time_series[hour_key] += 1

        return dict(time_series)

    async def _calculate_temporal_lag(self, data1: List[Dict], data2: List[Dict]) -> int:
        """
        Calculate temporal lag between two datasets
        """
        try:
            # Simple implementation: find peak difference
            time_series1 = await self._create_time_series(data1)
            time_series2 = await self._create_time_series(data2)

            if len(time_series1) == 0 or len(time_series2) == 0:
                return 0

            # Find peaks
            peak1_time = max(time_series1.items(), key=lambda x: x[1])[0] if time_series1 else None
            peak2_time = max(time_series2.items(), key=lambda x: x[1])[0] if time_series2 else None

            if peak1_time and peak2_time:
                lag_hours = abs((peak2_time - peak1_time).total_seconds()) / 3600
                return min(int(lag_hours), self.max_temporal_lag)

            return 0

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error calculating temporal lag: {str(e)}")
            return 0

    async def _analyze_spatial_causal_patterns(self, federated_data: Dict[str, List[Dict]]) -> None:
        """
        Analyze spatial causal relationships
        """
        try:
            # Group transactions by location
            location_data = defaultdict(list)

            for source, transactions in federated_data.items():
                for txn in transactions:
                    if 'location' in txn:
                        location_key = self._get_location_key(txn['location'])
                        location_data[location_key].append(txn)

            # Find spatial relationships
            locations = list(location_data.keys())

            for i, loc1 in enumerate(locations):
                for j, loc2 in enumerate(locations):
                    if i != j:
                        spatial_correlation = await self._calculate_spatial_correlation(
                            location_data[loc1], location_data[loc2]
                        )

                        if spatial_correlation >= self.correlation_threshold:
                            edge_key = (f"location_{loc1}", f"location_{loc2}")
                            self.edges[edge_key] = CausalEdge(
                                f"location_{loc1}", f"location_{loc2}",
                                spatial_correlation, 'spatial', 0
                            )

                            self.graph.add_edge(
                                f"location_{loc1}", f"location_{loc2}",
                                strength=spatial_correlation, type='spatial'
                            )

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error analyzing spatial patterns: {str(e)}")

    async def _calculate_spatial_correlation(self, data1: List[Dict], data2: List[Dict]) -> float:
        """
        Calculate spatial correlation between two location datasets
        """
        try:
            # Calculate distance between locations
            if not data1 or not data2:
                return 0.0

            loc1 = data1[0]['location']
            loc2 = data2[0]['location']

            distance = self._calculate_distance(loc1, loc2)

            # Spatial correlation decreases with distance
            # Using inverse distance relationship
            max_distance = 50.0  # km
            if distance <= max_distance:
                correlation = 1.0 - (distance / max_distance)
                return correlation
            else:
                return 0.0

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error calculating spatial correlation: {str(e)}")
            return 0.0

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

    async def _analyze_scam_type_propagation(self, federated_data: Dict[str, List[Dict]]) -> None:
        """
        Analyze how scam types propagate across banks
        """
        try:
            # Track scam type sequences
            scam_sequences = defaultdict(list)

            for source, transactions in federated_data.items():
                scam_times = defaultdict(list)

                for txn in transactions:
                    if 'scam_type' in txn and 'timestamp' in txn:
                        scam_type = txn['scam_type']
                        timestamp = datetime.fromisoformat(txn['timestamp'])
                        scam_times[scam_type].append(timestamp)

                # Sort by time for each scam type
                for scam_type, times in scam_times.items():
                    scam_times[scam_type].sort()
                    scam_sequences[source].extend([(scam_type, t) for t in times])

            # Find propagation patterns
            banks = [k for k in federated_data.keys() if k != 'NCRP']

            for scam_type in set([seq[0] for bank_seqs in scam_sequences.values() for seq in bank_seqs]):
                bank_first_occurrence = {}

                for bank in banks:
                    if bank in scam_sequences:
                        for st, timestamp in scam_sequences[bank]:
                            if st == scam_type and bank not in bank_first_occurrence:
                                bank_first_occurrence[bank] = timestamp
                                break

                # Create temporal propagation edges
                bank_list = sorted(bank_first_occurrence.items(), key=lambda x: x[1])

                for i in range(len(bank_list) - 1):
                    bank1, time1 = bank_list[i]
                    bank2, time2 = bank_list[i + 1]

                    time_diff = (time2 - time1).total_seconds() / 3600  # hours

                    if time_diff <= self.max_temporal_lag:
                        edge_key = (f"bank_{bank1}", f"bank_{bank2}")
                        edge_id = f"{edge_key}_{scam_type}"

                        if edge_id not in self.edges:
                            strength = max(0.1, 1.0 - (time_diff / self.max_temporal_lag))
                            self.edges[edge_id] = CausalEdge(
                                f"bank_{bank1}", f"bank_{bank2}",
                                strength, 'scam_propagation', int(time_diff)
                            )

                            self.graph.add_edge(
                                f"bank_{bank1}", f"bank_{bank2}",
                                strength=strength, type='scam_propagation',
                                scam_type=scam_type, temporal_lag=int(time_diff)
                            )

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error analyzing scam propagation: {str(e)}")

    async def _analyze_merchant_networks(self, federated_data: Dict[str, List[Dict]]) -> None:
        """
        Analyze merchant-to-merchant transaction networks
        """
        try:
            merchant_connections = defaultdict(set)
            merchant_patterns = defaultdict(list)

            for source, transactions in federated_data.items():
                for txn in transactions:
                    if 'merchant_hash' in txn and txn['merchant_hash']:
                        merchant_id = txn['merchant_hash'][:8]

                        # Track merchant activity patterns
                        merchant_patterns[merchant_id].append({
                            'bank': source,
                            'timestamp': txn.get('timestamp'),
                            'amount': txn.get('amount'),
                            'risk_score': txn.get('risk_score', 0)
                        })

            # Find merchants that appear across multiple banks
            cross_bank_merchants = {
                m_id: patterns for m_id, patterns in merchant_patterns.items()
                if len(set(p['bank'] for p in patterns)) > 1
            }

            # Create merchant network edges
            for merchant_id, patterns in cross_bank_merchants.items():
                banks_involved = list(set(p['bank'] for p in patterns))

                for i, bank1 in enumerate(banks_involved):
                    for bank2 in banks_involved[i+1:]:
                        edge_key = f"merchant_{merchant_id}_{bank1}_{bank2}"

                        # Calculate merchant risk score
                        avg_risk = np.mean([p['risk_score'] for p in patterns])

                        self.edges[edge_key] = CausalEdge(
                            f"bank_{bank1}", f"bank_{bank2}",
                            avg_risk, 'merchant_network', 0
                        )

                        self.graph.add_edge(
                            f"bank_{bank1}", f"bank_{bank2}",
                            strength=avg_risk, type='merchant_network',
                            merchant_id=merchant_id
                        )

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error analyzing merchant networks: {str(e)}")

    async def _analyze_causal_chains(self) -> None:
        """
        Analyze causal chains in the graph
        """
        try:
            # Find paths of length 3-5 that could indicate causal chains
            for source_node in self.graph.nodes():
                for target_node in self.graph.nodes():
                    if source_node != target_node:
                        try:
                            # Find all paths between nodes
                            paths = list(nx.all_simple_paths(
                                self.graph, source_node, target_node, cutoff=5
                            ))

                            for path in paths:
                                if len(path) >= 3:  # Minimum chain length
                                    chain_strength = self._calculate_chain_strength(path)

                                    if chain_strength >= self.min_causal_strength:
                                        self.causal_chains.append({
                                            'path': path,
                                            'strength': chain_strength,
                                            'length': len(path),
                                            'causal_types': [
                                                self.graph[path[i]][path[i+1]].get('type', 'unknown')
                                                for i in range(len(path)-1)
                                            ]
                                        })

                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            continue

            # Sort by strength
            self.causal_chains.sort(key=lambda x: x['strength'], reverse=True)

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error analyzing causal chains: {str(e)}")

    def _calculate_chain_strength(self, path: List[str]) -> float:
        """
        Calculate overall strength of a causal chain
        """
        try:
            if len(path) < 2:
                return 0.0

            # Multiply edge strengths along the path
            chain_strength = 1.0
            for i in range(len(path) - 1):
                edge_data = self.graph[path[i]][path[i + 1]]
                edge_strength = edge_data.get('strength', 0)
                chain_strength *= edge_strength

                # If any edge is very weak, the chain is weak
                if chain_strength < 0.1:
                    return chain_strength

            return chain_strength

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error calculating chain strength: {str(e)}")
            return 0.0

    async def _identify_pattern_signatures(self) -> None:
        """
        Identify repeating causal patterns (signatures)
        """
        try:
            # Group causal chains by their structural patterns
            pattern_signatures = defaultdict(list)

            for chain in self.causal_chains:
                # Create signature from causal types and node types
                signature_parts = []

                for i in range(len(chain['path']) - 1):
                    source_type = self.nodes[chain['path'][i]].node_type
                    target_type = self.nodes[chain['path'][i + 1]].node_type
                    edge_type = chain['causal_types'][i]

                    signature_parts.append(f"{source_type}->{edge_type}->{target_type}")

                signature = " -> ".join(signature_parts)
                pattern_signatures[signature].append(chain)

            # Store significant patterns (appearing multiple times)
            for signature, chains in pattern_signatures.items():
                if len(chains) >= 2:  # Pattern appears at least twice
                    self.pattern_signatures[signature] = {
                        'frequency': len(chains),
                        'avg_strength': np.mean([c['strength'] for c in chains]),
                        'avg_length': np.mean([c['length'] for c in chains]),
                        'example_chains': chains[:3]  # Store top 3 examples
                    }

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error identifying pattern signatures: {str(e)}")

    def _calculate_graph_metrics(self) -> Dict[str, Any]:
        """
        Calculate various graph metrics
        """
        try:
            metrics = {}

            if self.graph.number_of_nodes() > 0:
                metrics['node_count'] = self.graph.number_of_nodes()
                metrics['edge_count'] = self.graph.number_of_edges()
                metrics['density'] = nx.density(self.graph)
                metrics['avg_clustering'] = nx.average_clustering(self.graph.to_undirected())

                # Node centrality measures
                degree_centrality = nx.degree_centrality(self.graph)
                metrics['most_central_nodes'] = sorted(
                    degree_centrality.items(), key=lambda x: x[1], reverse=True
                )[:5]

                # Connected components
                metrics['connected_components'] = nx.number_connected_components(self.graph.to_undirected())

            return metrics

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error calculating metrics: {str(e)}")
            return {}

    async def predict_cross_bank_risk(self, bank_code: str, hours_ahead: int = 6) -> Dict[str, Any]:
        """
        Predict cross-bank risk based on causal relationships
        """
        try:
            bank_node_id = f"bank_{bank_code}"

            if bank_node_id not in self.nodes:
                return {'risk_score': 0.0, 'risk_factors': [], 'connected_banks': []}

            # Find connected banks through causal relationships
            connected_banks = []
            risk_factors = []
            total_risk = 0.0

            for neighbor in self.graph.neighbors(bank_node_id):
                edge_data = self.graph[bank_node_id][neighbor]
                edge_strength = edge_data.get('strength', 0)
                edge_type = edge_data.get('type', 'unknown')

                if edge_strength > 0.3:  # Significant connection
                    connected_banks.append({
                        'bank_id': neighbor,
                        'connection_strength': edge_strength,
                        'relationship_type': edge_type,
                        'temporal_lag': edge_data.get('temporal_lag', 0)
                    })

                    # Add to risk score
                    total_risk += edge_strength * 0.5

                    # Add specific risk factors
                    if edge_type == 'scam_propagation':
                        scam_type = edge_data.get('scam_type', 'unknown')
                        risk_factors.append({
                            'factor': 'scam_propagation',
                            'description': f"Scam type {scam_type} propagating from connected bank",
                            'severity': edge_strength
                        })
                    elif edge_type == 'merchant_network':
                        merchant_id = edge_data.get('merchant_id', 'unknown')
                        risk_factors.append({
                            'factor': 'shared_merchant',
                            'description': f"Shared high-risk merchant {merchant_id}",
                            'severity': edge_strength
                        })

            # Check for pattern signatures
            for signature, pattern_data in self.pattern_signatures.items():
                if bank_node_id in signature:
                    pattern_risk = pattern_data['avg_strength'] * 0.3
                    total_risk += pattern_risk
                    risk_factors.append({
                        'factor': 'recurring_pattern',
                        'description': f"Recurring causal pattern: {signature}",
                        'severity': pattern_data['avg_strength']
                    })

            # Normalize risk score
            risk_score = min(total_risk, 1.0)

            return {
                'bank_code': bank_code,
                'risk_score': risk_score,
                'risk_level': 'high' if risk_score >= 0.7 else 'medium' if risk_score >= 0.4 else 'low',
                'risk_factors': risk_factors,
                'connected_banks': connected_banks,
                'prediction_horizon_hours': hours_ahead,
                'confidence': 0.8 if len(connected_banks) > 0 else 0.5
            }

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error predicting cross-bank risk: {str(e)}")
            return {'risk_score': 0.0, 'risk_factors': [], 'connected_banks': []}

    async def export_graph_analysis(self) -> Dict[str, Any]:
        """
        Export comprehensive graph analysis
        """
        try:
            return {
                'graph_summary': {
                    'nodes': len(self.nodes),
                    'edges': len(self.edges),
                    'causal_chains': len(self.causal_chains),
                    'pattern_signatures': len(self.pattern_signatures)
                },
                'graph_metrics': self._calculate_graph_metrics(),
                'top_causal_chains': self.causal_chains[:10],
                'pattern_signatures': dict(list(self.pattern_signatures.items())[:10]),
                'node_analysis': {
                    node_id: {
                        'type': node.node_type,
                        'properties': node.properties,
                        'influence_score': node.influence_score
                    }
                    for node_id, node in list(self.nodes.items())[:20]
                }
            }

        except Exception as e:
            logger.error(f"[Federated Causal Graph] Error exporting analysis: {str(e)}")
            return {}

# Global service instance
federated_causal_graph = FederatedCausalGraph()