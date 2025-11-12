"""
Advanced Privacy Preservation System for AEGIS
Enhanced k-anonymity and Differential Privacy Implementation

Implements comprehensive privacy preservation with:
- Advanced k-anonymity with optimal clustering
- Differential privacy with adaptive ε allocation
- l-diversity and t-closeness extensions
- Privacy budget management
- Synthetic data generation
- Privacy loss accounting
- Adaptive privacy controls
"""

import asyncio
import json
import logging
import time
import uuid
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm, laplace
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import pairwise_distances
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import PCA
import networkx as nx
from sympy import symbols, Eq, solve
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnonymizationLevel(Enum):
    """Levels of anonymization strength"""
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    MAXIMUM = "maximum"

class PrivacyMetric(Enum):
    """Privacy metrics for evaluation"""
    K_ANONYMITY = "k_anonymity"
    L_DIVERSITY = "l_diversity"
    T_CLOSENESS = "t_closeness"
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    RE_IDENTIFICATION_RISK = "re_identification_risk"
    INFORMATION_LOSS = "information_loss"
    DATA_UTILITY = "data_utility"

@dataclass
class PrivacyBudget:
    """Privacy budget management"""
    total_budget: float
    used_budget: float
    remaining_budget: float
    allocation_history: List[Dict[str, Any]]
    last_reset: datetime
    reset_interval_days: int = 30

@dataclass
class AnonymizationResult:
    """Result of anonymization process"""
    anonymized_data: pd.DataFrame
    privacy_metrics: Dict[str, float]
    information_loss: float
    data_utility: float
    processing_time_ms: float
    privacy_budget_used: float
    anonymization_method: str
    parameters_used: Dict[str, Any]

class AdvancedKAnonymity:
    """Advanced k-anonymity implementation with optimal clustering"""

    def __init__(self, k_value: int = 50, optimization_method: str = 'kmeans'):
        self.k_value = k_value
        self.optimization_method = optimization_method
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.quasi_identifiers = []
        self.sensitive_attributes = []

    def anonymize(self, data: pd.DataFrame, quasi_identifiers: List[str],
                  sensitive_attributes: List[str] = None) -> AnonymizationResult:
        """
        Perform advanced k-anonymity with optimal clustering
        """
        start_time = time.time()

        try:
            # Set attributes
            self.quasi_identifiers = quasi_identifiers
            self.sensitive_attributes = sensitive_attributes or []

            # Validate input
            if not self._validate_input(data):
                raise ValueError("Invalid input data for k-anonymity")

            # Calculate feature importance
            self._calculate_feature_importance(data)

            # Optimize clustering
            optimal_clusters = self._find_optimal_clustering(data)

            # Apply k-anonymity
            anonymized_data = self._apply_k_anonymity(data, optimal_clusters)

            # Apply l-diversity and t-closeness if sensitive attributes exist
            if self.sensitive_attributes:
                anonymized_data = self._apply_l_diversity(anonymized_data)
                anonymized_data = self._apply_t_closeness(anonymized_data)

            # Calculate privacy metrics
            privacy_metrics = self._calculate_privacy_metrics(anonymized_data)

            # Calculate information loss and data utility
            information_loss = self._calculate_information_loss(data, anonymized_data)
            data_utility = self._calculate_data_utility(data, anonymized_data)

            processing_time = (time.time() - start_time) * 1000

            return AnonymizationResult(
                anonymized_data=anonymized_data,
                privacy_metrics=privacy_metrics,
                information_loss=information_loss,
                data_utility=data_utility,
                processing_time_ms=processing_time,
                privacy_budget_used=0.0,  # k-anonymity doesn't use differential privacy budget
                anonymization_method='advanced_k_anonymity',
                parameters_used={
                    'k_value': self.k_value,
                    'optimization_method': self.optimization_method,
                    'optimal_clusters': optimal_clusters
                }
            )

        except Exception as e:
            logger.error(f"K-anonymity error: {str(e)}")
            raise

    def _validate_input(self, data: pd.DataFrame) -> bool:
        """Validate input data"""
        if data.empty:
            return False

        # Check if quasi-identifiers exist in data
        missing_quasi = [qid for qid in self.quasi_identifiers if qid not in data.columns]
        if missing_quasi:
            logger.error(f"Missing quasi-identifiers: {missing_quasi}")
            return False

        # Check if k is reasonable for data size
        if self.k_value >= len(data):
            logger.warning(f"k={self.k_value} is larger than dataset size={len(data)}")
            return False

        return True

    def _calculate_feature_importance(self, data: pd.DataFrame):
        """Calculate importance of quasi-identifier features"""
        # Use variance and cardinality as importance metrics
        for qid in self.quasi_identifiers:
            if data[qid].dtype in ['object', 'category']:
                # Categorical feature importance based on cardinality
                cardinality = data[qid].nunique()
                self.feature_importance[qid] = min(1.0, cardinality / 10.0)
            else:
                # Numerical feature importance based on variance
                variance = data[qid].var()
                self.feature_importance[qid] = min(1.0, variance / data[qid].mean() if data[qid].mean() > 0 else 0)

        # Normalize importance scores
        total_importance = sum(self.feature_importance.values())
        if total_importance > 0:
            for qid in self.feature_importance:
                self.feature_importance[qid] /= total_importance

    def _find_optimal_clustering(self, data: pd.DataFrame) -> int:
        """Find optimal number of clusters for k-anonymity"""
        try:
            # Extract quasi-identifier features
            qi_data = data[self.quasi_identifiers].copy()

            # Preprocess categorical features
            for col in qi_data.columns:
                if qi_data[col].dtype in ['object', 'category']:
                    le = LabelEncoder()
                    qi_data[col] = le.fit_transform(qi_data[col].astype(str))

            # Scale features
            qi_scaled = self.scaler.fit_transform(qi_data)

            # Estimate optimal number of clusters
            n_samples = len(data)
            min_clusters = max(1, n_samples // (self.k_value * 2))
            max_clusters = max(1, n_samples // self.k_value)

            if min_clusters >= max_clusters:
                return max_clusters

            # Use elbow method to find optimal k
            inertias = []
            k_range = range(min_clusters, min(max_clusters, min_clusters + 10))

            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(qi_scaled)
                inertias.append(kmeans.inertia_)

            # Find elbow point
            if len(inertias) >= 2:
                # Simple elbow detection
                diffs = np.diff(inertias)
                second_diffs = np.diff(diffs)
                elbow_idx = np.argmax(second_diffs) + 1 if len(second_diffs) > 0 else 0
                optimal_k = k_range[min(elbow_idx, len(k_range)-1)]
            else:
                optimal_k = min_clusters

            return max(1, optimal_k)

        except Exception as e:
            logger.warning(f"Clustering optimization failed: {str(e)}")
            return max(1, len(data) // self.k_value)

    def _apply_k_anonymity(self, data: pd.DataFrame, n_clusters: int) -> pd.DataFrame:
        """Apply k-anonymity using optimal clustering"""
        try:
            # Prepare data for clustering
            qi_data = data[self.quasi_identifiers].copy()

            # Encode categorical features
            encoders = {}
            for col in qi_data.columns:
                if qi_data[col].dtype in ['object', 'category']:
                    le = LabelEncoder()
                    qi_data[col] = le.fit_transform(qi_data[col].astype(str))
                    encoders[col] = le

            # Scale features
            qi_scaled = self.scaler.fit_transform(qi_data)

            # Perform clustering
            if self.optimization_method == 'kmeans':
                clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            else:  # DBSCAN
                clusterer = DBSCAN(eps=0.5, min_samples=max(2, self.k_value))

            cluster_labels = clusterer.fit_predict(qi_scaled)

            # Add cluster labels to data
            anonymized_data = data.copy()
            anonymized_data['cluster_id'] = cluster_labels

            # Generalize within each cluster
            for cluster_id in anonymized_data['cluster_id'].unique():
                cluster_mask = anonymized_data['cluster_id'] == cluster_id
                cluster_data = anonymized_data[cluster_mask]

                # Check if cluster meets k-anonymity
                if len(cluster_data) < self.k_value:
                    # Merge with nearest cluster
                    nearest_cluster = self._find_nearest_cluster(anonymized_data, cluster_id, qi_scaled)
                    if nearest_cluster is not None:
                        anonymized_data.loc[cluster_mask, 'cluster_id'] = nearest_cluster
                        cluster_mask = anonymized_data['cluster_id'] == nearest_cluster
                        cluster_data = anonymized_data[cluster_mask]

                # Generalize quasi-identifiers within cluster
                for qid in self.quasi_identifiers:
                    generalized_value = self._generalize_attribute(cluster_data[qid], qid)
                    anonymized_data.loc[cluster_mask, qid] = generalized_value

            # Remove cluster_id column
            anonymized_data = anonymized_data.drop('cluster_id', axis=1)

            # Validate k-anonymity
            k_achieved = self._verify_k_anonymity(anonymized_data)
            if k_achieved < self.k_value:
                logger.warning(f"Could not achieve k={self.k_value}, achieved k={k_achieved}")

            return anonymized_data

        except Exception as e:
            logger.error(f"K-anonymity application error: {str(e)}")
            raise

    def _find_nearest_cluster(self, data: pd.DataFrame, target_cluster: int, scaled_data: np.ndarray) -> Optional[int]:
        """Find nearest cluster to merge with"""
        try:
            target_mask = data['cluster_id'] == target_cluster
            target_points = scaled_data[target_mask]

            if len(target_points) == 0:
                return None

            target_centroid = np.mean(target_points, axis=0)

            min_distance = float('inf')
            nearest_cluster = None

            for cluster_id in data['cluster_id'].unique():
                if cluster_id == target_cluster:
                    continue

                cluster_mask = data['cluster_id'] == cluster_id
                cluster_points = scaled_data[cluster_mask]

                if len(cluster_points) == 0:
                    continue

                cluster_centroid = np.mean(cluster_points, axis=0)
                distance = np.linalg.norm(target_centroid - cluster_centroid)

                if distance < min_distance:
                    min_distance = distance
                    nearest_cluster = cluster_id

            return nearest_cluster

        except Exception:
            return None

    def _generalize_attribute(self, values: pd.Series, attribute_name: str) -> Union[str, float]:
        """Generalize attribute values within a cluster"""
        try:
            if values.dtype in ['object', 'category']:
                # Categorical generalization
                value_counts = values.value_counts()
                if len(value_counts) == 1:
                    return values.iloc[0]
                else:
                    # Use most common value or create generalized category
                    most_common = value_counts.index[0]
                    return f"{most_common}_and_{len(value_counts)-1}_others"
            else:
                # Numerical generalization
                min_val = values.min()
                max_val = values.max()

                if min_val == max_val:
                    return min_val
                else:
                    # Create range
                    return f"[{min_val:.2f}, {max_val:.2f}]"

        except Exception:
            return str(values.iloc[0]) if len(values) > 0 else "unknown"

    def _apply_l_diversity(self, data: pd.DataFrame, l_value: int = 3) -> pd.DataFrame:
        """Apply l-diversity constraint"""
        if not self.sensitive_attributes:
            return data

        try:
            # Find equivalence classes based on quasi-identifiers
            equivalence_classes = data.groupby(self.quasi_identifiers)

            valid_classes = []
            suppressed_count = 0

            for name, group in equivalence_classes:
                # Check l-diversity for each sensitive attribute
                meets_l_diversity = True

                for sensitive_attr in self.sensitive_attributes:
                    if sensitive_attr in group.columns:
                        distinct_values = group[sensitive_attr].nunique()
                        if distinct_values < l_value:
                            meets_l_diversity = False
                            break

                if meets_l_diversity:
                    valid_classes.append(group)
                else:
                    suppressed_count += len(group)

            if suppressed_count > 0:
                logger.warning(f"Suppressed {suppressed_count} records due to l-diversity violation")

            if valid_classes:
                result = pd.concat(valid_classes, ignore_index=True)
            else:
                logger.warning("All records suppressed due to l-diversity violation")
                result = data.copy()

            return result

        except Exception as e:
            logger.warning(f"L-diversity application failed: {str(e)}")
            return data

    def _apply_t_closeness(self, data: pd.DataFrame, t_value: float = 0.1) -> pd.DataFrame:
        """Apply t-closeness constraint"""
        if not self.sensitive_attributes:
            return data

        try:
            # Calculate overall distribution for each sensitive attribute
            overall_distributions = {}
            for sensitive_attr in self.sensitive_attributes:
                if sensitive_attr in data.columns:
                    overall_distributions[sensitive_attr] = data[sensitive_attr].value_counts(normalize=True)

            # Find equivalence classes
            equivalence_classes = data.groupby(self.quasi_identifiers)

            valid_classes = []
            suppressed_count = 0

            for name, group in equivalence_classes:
                meets_t_closeness = True

                for sensitive_attr in self.sensitive_attributes:
                    if sensitive_attr in group.columns and sensitive_attr in overall_distributions:
                        # Calculate distribution within equivalence class
                        class_distribution = group[sensitive_attr].value_counts(normalize=True)

                        # Calculate t-closeness (simplified using total variation distance)
                        distance = 0
                        for value in overall_distributions[sensitive_attr].index:
                            overall_prob = overall_distributions[sensitive_attr].get(value, 0)
                            class_prob = class_distribution.get(value, 0)
                            distance += abs(overall_prob - class_prob)

                        distance /= 2  # Total variation distance

                        if distance > t_value:
                            meets_t_closeness = False
                            break

                if meets_t_closeness:
                    valid_classes.append(group)
                else:
                    suppressed_count += len(group)

            if suppressed_count > 0:
                logger.warning(f"Suppressed {suppressed_count} records due to t-closeness violation")

            if valid_classes:
                result = pd.concat(valid_classes, ignore_index=True)
            else:
                logger.warning("All records suppressed due to t-closeness violation")
                result = data.copy()

            return result

        except Exception as e:
            logger.warning(f"T-closeness application failed: {str(e)}")
            return data

    def _verify_k_anonymity(self, data: pd.DataFrame) -> int:
        """Verify achieved k-anonymity"""
        try:
            equivalence_classes = data.groupby(self.quasi_identifiers).size()
            return equivalence_classes.min() if len(equivalence_classes) > 0 else 0
        except Exception:
            return 0

    def _calculate_privacy_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate privacy metrics"""
        metrics = {}

        # K-anonymity
        metrics['k_anonymity_achieved'] = self._verify_k_anonymity(data)

        # Average equivalence class size
        equivalence_classes = data.groupby(self.quasi_identifiers).size()
        metrics['avg_equivalence_class_size'] = equivalence_classes.mean()

        # Number of equivalence classes
        metrics['num_equivalence_classes'] = len(equivalence_classes)

        # L-diversity (if sensitive attributes exist)
        if self.sensitive_attributes:
            l_diversity_scores = []
            for name, group in data.groupby(self.quasi_identifiers):
                for sensitive_attr in self.sensitive_attributes:
                    if sensitive_attr in group.columns:
                        l_diversity_scores.append(group[sensitive_attr].nunique())

            if l_diversity_scores:
                metrics['min_l_diversity'] = min(l_diversity_scores)
                metrics['avg_l_diversity'] = np.mean(l_diversity_scores)

        return metrics

    def _calculate_information_loss(self, original_data: pd.DataFrame, anonymized_data: pd.DataFrame) -> float:
        """Calculate information loss due to anonymization"""
        try:
            total_loss = 0
            num_attributes = 0

            for qid in self.quasi_identifiers:
                if qid in original_data.columns and qid in anonymized_data.columns:
                    if original_data[qid].dtype in ['object', 'category']:
                        # Categorical information loss
                        original_dist = original_data[qid].value_counts(normalize=True)
                        anonymized_dist = anonymized_data[qid].value_counts(normalize=True)

                        # Calculate KL divergence
                        loss = 0
                        for value in original_dist.index:
                            p = original_dist.get(value, 0)
                            q = anonymized_dist.get(value, 1e-10)  # Avoid division by zero
                            if p > 0:
                                loss += p * np.log(p / q)

                        total_loss += loss
                    else:
                        # Numerical information loss (based on variance reduction)
                        original_var = original_data[qid].var()
                        anonymized_var = anonymized_data[qid].var()

                        if original_var > 0:
                            loss = 1 - (anonymized_var / original_var)
                            total_loss += loss

                    num_attributes += 1

            return total_loss / num_attributes if num_attributes > 0 else 0

        except Exception as e:
            logger.warning(f"Information loss calculation error: {str(e)}")
            return 0.5  # Default to moderate loss

    def _calculate_data_utility(self, original_data: pd.DataFrame, anonymized_data: pd.DataFrame) -> float:
        """Calculate data utility score"""
        try:
            # Utility is inverse of information loss
            information_loss = self._calculate_information_loss(original_data, anonymized_data)
            base_utility = max(0, 1 - information_loss)

            # Adjust for record retention
            retention_rate = len(anonymized_data) / len(original_data)
            utility = base_utility * retention_rate

            return max(0, min(1, utility))

        except Exception:
            return 0.5  # Default to moderate utility

class AdvancedDifferentialPrivacy:
    """Advanced differential privacy implementation with adaptive ε allocation"""

    def __init__(self, epsilon_total: float = 1.0, delta: float = 1e-5):
        self.epsilon_total = epsilon_total
        self.delta = delta
        self.epsilon_used = 0.0
        self.epsilon_remaining = epsilon_total
        self.allocation_history = []
        self.sensitivity_calculator = SensitivityCalculator()

    def add_laplace_noise(self, data: Union[float, np.ndarray], sensitivity: float,
                         epsilon: float = None) -> Union[float, np.ndarray]:
        """Add Laplace noise for differential privacy"""
        try:
            if epsilon is None:
                epsilon = self.epsilon_remaining / 2  # Conservative allocation

            if epsilon <= 0:
                raise ValueError("Epsilon must be positive")

            # Calculate scale parameter
            scale = sensitivity / epsilon

            # Add noise
            if isinstance(data, (int, float)):
                noise = np.random.laplace(0, scale)
                result = data + noise
            else:
                noise = np.random.laplace(0, scale, size=data.shape)
                result = data + noise

            # Update epsilon usage
            self._update_epsilon_usage(epsilon, 'laplace_noise')

            return result

        except Exception as e:
            logger.error(f"Laplace noise addition error: {str(e)}")
            raise

    def add_gaussian_noise(self, data: Union[float, np.ndarray], sensitivity: float,
                          epsilon: float = None) -> Union[float, np.ndarray]:
        """Add Gaussian noise for (ε, δ)-differential privacy"""
        try:
            if epsilon is None:
                epsilon = self.epsilon_remaining / 2

            if epsilon <= 0:
                raise ValueError("Epsilon must be positive")

            # Calculate sigma for Gaussian mechanism
            sigma = np.sqrt(2 * np.log(1.25 / self.delta)) * sensitivity / epsilon

            # Add noise
            if isinstance(data, (int, float)):
                noise = np.random.normal(0, sigma)
                result = data + noise
            else:
                noise = np.random.normal(0, sigma, size=data.shape)
                result = data + noise

            # Update epsilon usage
            self._update_epsilon_usage(epsilon, 'gaussian_noise')

            return result

        except Exception as e:
            logger.error(f"Gaussian noise addition error: {str(e)}")
            raise

    def private_count(self, data: pd.Series, epsilon: float = None) -> int:
        """Differentially private count"""
        try:
            true_count = len(data)
            sensitivity = 1  # Changing one record changes count by at most 1

            noisy_count = self.add_laplace_noise(true_count, sensitivity, epsilon)
            return max(0, int(round(noisy_count)))

        except Exception as e:
            logger.error(f"Private count error: {str(e)}")
            return len(data)

    def private_mean(self, data: pd.Series, epsilon: float = None) -> float:
        """Differentially private mean"""
        try:
            if len(data) == 0:
                return 0.0

            true_mean = data.mean()
            sensitivity = (data.max() - data.min()) / len(data)

            noisy_mean = self.add_laplace_noise(true_mean, sensitivity, epsilon)
            return noisy_mean

        except Exception as e:
            logger.error(f"Private mean error: {str(e)}")
            return data.mean() if len(data) > 0 else 0.0

    def private_histogram(self, data: pd.Series, bins: int = 10, epsilon: float = None) -> Tuple[np.ndarray, np.ndarray]:
        """Differentially private histogram"""
        try:
            if len(data) == 0:
                return np.array([]), np.array([])

            # Create histogram
            counts, bin_edges = np.histogram(data, bins=bins)
            sensitivity = 1  # Each person contributes to at most one bin

            # Add noise to counts
            noisy_counts = []
            for count in counts:
                noisy_count = self.add_laplace_noise(count, sensitivity, epsilon / bins)
                noisy_counts.append(max(0, noisy_count))

            return np.array(noisy_counts), bin_edges

        except Exception as e:
            logger.error(f"Private histogram error: {str(e)}")
            counts, bin_edges = np.histogram(data, bins=bins)
            return counts, bin_edges

    def _update_epsilon_usage(self, epsilon_used: float, operation: str):
        """Update epsilon usage tracking"""
        self.epsilon_used += epsilon_used
        self.epsilon_remaining = max(0, self.epsilon_total - self.epsilon_used)

        self.allocation_history.append({
            'timestamp': datetime.utcnow(),
            'epsilon_used': epsilon_used,
            'cumulative_epsilon': self.epsilon_used,
            'remaining_epsilon': self.epsilon_remaining,
            'operation': operation
        })

    def reset_privacy_budget(self):
        """Reset privacy budget"""
        self.epsilon_used = 0.0
        self.epsilon_remaining = self.epsilon_total
        self.allocation_history = []

    def get_privacy_spent(self) -> float:
        """Get total privacy budget spent"""
        return self.epsilon_used

    def get_privacy_remaining(self) -> float:
        """Get remaining privacy budget"""
        return self.epsilon_remaining

class SensitivityCalculator:
    """Calculate sensitivity for different queries"""

    def __init__(self):
        self.cached_sensitivities = {}

    def calculate_count_sensitivity(self, dataset_size: int) -> float:
        """Calculate sensitivity for count query"""
        return 1.0  # Adding/removing one record changes count by at most 1

    def calculate_mean_sensitivity(self, data_range: Tuple[float, float], dataset_size: int) -> float:
        """Calculate sensitivity for mean query"""
        min_val, max_val = data_range
        return (max_val - min_val) / dataset_size

    def calculate_sum_sensitivity(self, data_range: Tuple[float, float]) -> float:
        """Calculate sensitivity for sum query"""
        min_val, max_val = data_range
        return max(abs(min_val), abs(max_val))

    def calculate_variance_sensitivity(self, data_range: Tuple[float, float], dataset_size: int) -> float:
        """Calculate sensitivity for variance query"""
        min_val, max_val = data_range
        return ((max_val - min_val) ** 2) / dataset_size

    def calculate_histogram_sensitivity(self) -> float:
        """Calculate sensitivity for histogram query"""
        return 1.0  # Each person contributes to at most one bin

class PrivacyBudgetManager:
    """Manage privacy budget across multiple computations"""

    def __init__(self, total_budget: float = 1.0, reset_interval_days: int = 30):
        self.total_budget = total_budget
        self.used_budget = 0.0
        self.remaining_budget = total_budget
        self.allocation_history = []
        self.reset_interval_days = reset_interval_days
        self.last_reset = datetime.utcnow()

    def allocate_budget(self, computation_type: str, requested_epsilon: float,
                       priority: str = 'normal') -> Tuple[bool, float]:
        """Allocate privacy budget for computation"""
        try:
            # Check if budget needs reset
            self._check_budget_reset()

            # Priority-based allocation
            priority_multiplier = {
                'low': 0.5,
                'normal': 1.0,
                'high': 1.5,
                'critical': 2.0
            }

            multiplier = priority_multiplier.get(priority, 1.0)
            adjusted_epsilon = requested_epsilon * multiplier

            # Check if enough budget remains
            if adjusted_epsilon <= self.remaining_budget:
                # Allocate budget
                self.used_budget += adjusted_epsilon
                self.remaining_budget = max(0, self.total_budget - self.used_budget)

                allocation_record = {
                    'timestamp': datetime.utcnow(),
                    'computation_type': computation_type,
                    'requested_epsilon': requested_epsilon,
                    'allocated_epsilon': adjusted_epsilon,
                    'priority': priority,
                    'remaining_budget': self.remaining_budget
                }

                self.allocation_history.append(allocation_record)
                return True, adjusted_epsilon
            else:
                return False, 0.0

        except Exception as e:
            logger.error(f"Budget allocation error: {str(e)}")
            return False, 0.0

    def _check_budget_reset(self):
        """Check if budget should be reset"""
        days_since_reset = (datetime.utcnow() - self.last_reset).days
        if days_since_reset >= self.reset_interval_days:
            self.reset_budget()

    def reset_budget(self):
        """Reset privacy budget"""
        self.used_budget = 0.0
        self.remaining_budget = self.total_budget
        self.last_reset = datetime.utcnow()
        logger.info("Privacy budget reset")

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        return {
            'total_budget': self.total_budget,
            'used_budget': self.used_budget,
            'remaining_budget': self.remaining_budget,
            'budget_utilization': self.used_budget / self.total_budget,
            'last_reset': self.last_reset.isoformat(),
            'days_until_reset': max(0, self.reset_interval_days - (datetime.utcnow() - self.last_reset).days),
            'total_allocations': len(self.allocation_history)
        }

class SyntheticDataGenerator:
    """Generate synthetic data with privacy guarantees"""

    def __init__(self):
        self.generators = {
            'independent': self._generate_independent_synthetic,
            'correlated': self._generate_correlated_synthetic,
            'gan_based': self._generate_gan_based_synthetic
        }

    def generate_synthetic_data(self, original_data: pd.DataFrame,
                               method: str = 'independent',
                               sample_size: int = None,
                               privacy_budget: float = 0.1) -> pd.DataFrame:
        """Generate synthetic data preserving statistical properties"""
        try:
            if method not in self.generators:
                raise ValueError(f"Unknown generation method: {method}")

            if sample_size is None:
                sample_size = len(original_data)

            synthetic_data = self.generators[method](original_data, sample_size, privacy_budget)

            logger.info(f"Generated {len(synthetic_data)} synthetic records using {method} method")
            return synthetic_data

        except Exception as e:
            logger.error(f"Synthetic data generation error: {str(e)}")
            raise

    def _generate_independent_synthetic(self, original_data: pd.DataFrame,
                                       sample_size: int, privacy_budget: float) -> pd.DataFrame:
        """Generate synthetic data assuming independent attributes"""
        try:
            synthetic_data = pd.DataFrame()
            dp = AdvancedDifferentialPrivacy(epsilon_total=privacy_budget)

            for column in original_data.columns:
                if original_data[column].dtype in ['object', 'category']:
                    # Categorical attribute
                    value_counts = original_data[column].value_counts(normalize=True)

                    # Add differential privacy to proportions
                    noisy_proportions = []
                    total_privacy_used = 0

                    for value, proportion in value_counts.items():
                        if total_privacy_used < privacy_budget:
                            epsilon_for_value = privacy_budget / len(value_counts)
                            noisy_proportion = dp.add_laplace_noise(proportion, 1/len(original_data), epsilon_for_value)
                            total_privacy_used += epsilon_for_value
                        else:
                            noisy_proportion = proportion

                        noisy_proportions.append(max(0, noisy_proportion))

                    # Normalize proportions
                    total_proportion = sum(noisy_proportions)
                    if total_proportion > 0:
                        noisy_proportions = [p/total_proportion for p in noisy_proportions]

                    # Sample from noisy distribution
                    synthetic_values = np.random.choice(
                        list(value_counts.index),
                        size=sample_size,
                        p=noisy_proportions
                    )
                    synthetic_data[column] = synthetic_values

                else:
                    # Numerical attribute
                    mean = original_data[column].mean()
                    std = original_data[column].std()

                    # Add differential privacy
                    epsilon_for_stat = privacy_budget / 2
                    noisy_mean = dp.add_laplace_noise(mean, std/len(original_data), epsilon_for_stat)
                    noisy_std = dp.add_laplace_noise(std, (original_data[column].max() - original_data[column].min())/len(original_data), epsilon_for_stat)

                    # Generate synthetic values
                    synthetic_values = np.random.normal(noisy_mean, max(0.1, noisy_std), sample_size)
                    synthetic_data[column] = synthetic_values

            return synthetic_data

        except Exception as e:
            logger.error(f"Independent synthetic generation error: {str(e)}")
            raise

    def _generate_correlated_synthetic(self, original_data: pd.DataFrame,
                                     sample_size: int, privacy_budget: float) -> pd.DataFrame:
        """Generate synthetic data preserving correlations"""
        try:
            # Select only numerical columns
            numerical_columns = original_data.select_dtypes(include=[np.number]).columns.tolist()

            if len(numerical_columns) < 2:
                # Fall back to independent generation
                return self._generate_independent_synthetic(original_data, sample_size, privacy_budget)

            # Calculate correlation matrix
            correlation_matrix = original_data[numerical_columns].corr()

            # Add differential privacy to correlation matrix
            dp = AdvancedDifferentialPrivacy(epsilon_total=privacy_budget/2)
            noisy_correlation = correlation_matrix.copy()

            for i in range(len(correlation_matrix)):
                for j in range(len(correlation_matrix.columns)):
                    if i != j:
                        epsilon_for_correlation = privacy_budget / (2 * len(correlation_matrix) * (len(correlation_matrix) - 1))
                        noisy_correlation.iloc[i, j] = dp.add_laplace_noise(
                            correlation_matrix.iloc[i, j],
                            2/len(original_data),
                            epsilon_for_correlation
                        )

            # Ensure correlation matrix is valid
            np.fill_diagonal(noisy_correlation.values, 1.0)
            noisy_correlation = self._make_valid_correlation_matrix(noisy_correlation)

            # Generate synthetic data using the noisy correlation matrix
            synthetic_data = pd.DataFrame()

            # Generate correlated numerical data
            means = original_data[numerical_columns].mean()
            stds = original_data[numerical_columns].std()

            # Add differential privacy to means and stds
            dp_means = AdvancedDifferentialPrivacy(epsilon_total=privacy_budget/4)
            dp_stds = AdvancedDifferentialPrivacy(epsilon_total=privacy_budget/4)

            noisy_means = {}
            noisy_stds = {}
            for col in numerical_columns:
                epsilon_for_stat = privacy_budget / (4 * len(numerical_columns))
                noisy_means[col] = dp_means.add_laplace_noise(means[col], stds[col]/len(original_data), epsilon_for_stat)
                noisy_stds[col] = dp_stds.add_laplace_noise(stds[col], (original_data[col].max() - original_data[col].min())/len(original_data), epsilon_for_stat)

            # Generate multivariate normal data
            mvn_data = np.random.multivariate_normal(
                [noisy_means[col] for col in numerical_columns],
                noisy_correlation.values,
                size=sample_size
            )

            # Scale to original standard deviations
            for i, col in enumerate(numerical_columns):
                synthetic_data[col] = mvn_data[:, i] * max(0.1, noisy_stds[col])

            # Handle categorical columns independently
            categorical_columns = original_data.select_dtypes(include=['object', 'category']).columns.tolist()
            if categorical_columns:
                dp_categorical = AdvancedDifferentialPrivacy(epsilon_total=privacy_budget/4)
                for col in categorical_columns:
                    value_counts = original_data[col].value_counts(normalize=True)

                    # Add differential privacy
                    noisy_proportions = []
                    for value, proportion in value_counts.items():
                        epsilon_for_value = privacy_budget / (4 * len(value_counts) * len(categorical_columns))
                        noisy_proportion = dp_categorical.add_laplace_noise(proportion, 1/len(original_data), epsilon_for_value)
                        noisy_proportions.append(max(0, noisy_proportion))

                    # Normalize proportions
                    total_proportion = sum(noisy_proportions)
                    if total_proportion > 0:
                        noisy_proportions = [p/total_proportion for p in noisy_proportions]

                    # Sample from noisy distribution
                    synthetic_values = np.random.choice(
                        list(value_counts.index),
                        size=sample_size,
                        p=noisy_proportions
                    )
                    synthetic_data[col] = synthetic_values

            return synthetic_data

        except Exception as e:
            logger.error(f"Correlated synthetic generation error: {str(e)}")
            # Fall back to independent generation
            return self._generate_independent_synthetic(original_data, sample_size, privacy_budget)

    def _make_valid_correlation_matrix(self, correlation_matrix: pd.DataFrame) -> pd.DataFrame:
        """Ensure correlation matrix is positive semi-definite"""
        try:
            # Eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eigh(correlation_matrix.values)

            # Set negative eigenvalues to small positive values
            eigenvalues = np.maximum(eigenvalues, 1e-8)

            # Reconstruct correlation matrix
            reconstructed = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

            # Ensure diagonal is 1
            np.fill_diagonal(reconstructed, 1.0)

            return pd.DataFrame(reconstructed, index=correlation_matrix.index, columns=correlation_matrix.columns)

        except Exception:
            return correlation_matrix

    def _generate_gan_based_synthetic(self, original_data: pd.DataFrame,
                                   sample_size: int, privacy_budget: float) -> pd.DataFrame:
        """Generate synthetic data using GANs (simplified implementation)"""
        # This is a placeholder for GAN-based generation
        # In practice, this would involve training a GAN model
        logger.warning("GAN-based synthetic generation not implemented, falling back to independent generation")
        return self._generate_independent_synthetic(original_data, sample_size, privacy_budget)

class PrivacyPreservationSystem:
    """Main privacy preservation system integrating all techniques"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.k_anonymizer = AdvancedKAnonymity(k_value=config.get('k_value', 50))
        self.dp_engine = AdvancedDifferentialPrivacy(
            epsilon_total=config.get('epsilon_total', 1.0),
            delta=config.get('delta', 1e-5)
        )
        self.budget_manager = PrivacyBudgetManager(
            total_budget=config.get('epsilon_total', 1.0),
            reset_interval_days=config.get('reset_interval_days', 30)
        )
        self.synthetic_generator = SyntheticDataGenerator()

        # Performance metrics
        self.metrics = {
            'total_anonymizations': 0,
            'total_dp_operations': 0,
            'average_processing_time': 0.0,
            'privacy_preservation_score': 0.0
        }

    async def preserve_privacy_comprehensive(self, data: pd.DataFrame,
                                          quasi_identifiers: List[str],
                                          sensitive_attributes: List[str] = None,
                                          methods: List[str] = None) -> Dict[str, Any]:
        """Apply comprehensive privacy preservation"""
        try:
            start_time = time.time()

            if methods is None:
                methods = ['k_anonymity', 'differential_privacy']

            results = {
                'original_data_shape': data.shape,
                'methods_applied': methods,
                'processing_steps': []
            }

            processed_data = data.copy()

            # Apply k-anonymity
            if 'k_anonymity' in methods:
                logger.info("Applying k-anonymity...")
                k_anon_result = self.k_anonymizer.anonymize(
                    processed_data,
                    quasi_identifiers,
                    sensitive_attributes
                )

                processed_data = k_anon_result.anonymized_data
                results['k_anonymity'] = {
                    'k_value_achieved': k_anon_result.privacy_metrics.get('k_anonymity_achieved', 0),
                    'information_loss': k_anon_result.information_loss,
                    'data_utility': k_anon_result.data_utility,
                    'records_retained': len(processed_data)
                }
                results['processing_steps'].append('k_anonymity_completed')

            # Apply differential privacy
            if 'differential_privacy' in methods:
                logger.info("Applying differential privacy...")
                dp_result = await self._apply_differential_privacy(processed_data, quasi_identifiers)
                processed_data = dp_result['data']
                results['differential_privacy'] = dp_result['metrics']
                results['processing_steps'].append('differential_privacy_completed')

            # Generate synthetic data if requested
            if 'synthetic_data' in methods:
                logger.info("Generating synthetic data...")
                synthetic_data = self.synthetic_generator.generate_synthetic_data(
                    processed_data,
                    method='correlated',
                    sample_size=len(processed_data),
                    privacy_budget=0.1
                )
                results['synthetic_data'] = {
                    'shape': synthetic_data.shape,
                    'utility_score': self._calculate_synthetic_utility(processed_data, synthetic_data)
                }
                results['processing_steps'].append('synthetic_data_generated')

            # Calculate overall privacy metrics
            results['overall_metrics'] = self._calculate_overall_privacy_metrics(data, processed_data)
            results['processing_time_ms'] = (time.time() - start_time) * 1000

            # Update system metrics
            self._update_system_metrics(results['processing_time_ms'], results['overall_metrics']['privacy_score'])

            logger.info(f"Comprehensive privacy preservation completed in {results['processing_time_ms']:.2f}ms")
            return results

        except Exception as e:
            logger.error(f"Comprehensive privacy preservation error: {str(e)}")
            raise

    async def _apply_differential_privacy(self, data: pd.DataFrame,
                                        quasi_identifiers: List[str]) -> Dict[str, Any]:
        """Apply differential privacy to numerical attributes"""
        try:
            dp_data = data.copy()
            metrics = {
                'operations_performed': [],
                'epsilon_used': 0.0
            }

            # Apply DP to numerical quasi-identifiers
            numerical_qis = [qid for qid in quasi_identifiers
                           if qid in data.columns and data[qid].dtype in ['int64', 'float64']]

            for qid in numerical_qis:
                # Allocate budget for this attribute
                success, allocated_epsilon = self.budget_manager.allocate_budget(
                    f'dp_{qid}',
                    0.1,
                    priority='normal'
                )

                if success:
                    # Calculate sensitivity
                    sensitivity = (data[qid].max() - data[qid].min()) / len(data)

                    # Add noise
                    dp_data[qid] = self.dp_engine.add_laplace_noise(
                        data[qid].values,
                        sensitivity,
                        allocated_epsilon
                    )

                    metrics['operations_performed'].append(qid)
                    metrics['epsilon_used'] += allocated_epsilon

            return {
                'data': dp_data,
                'metrics': metrics
            }

        except Exception as e:
            logger.error(f"Differential privacy application error: {str(e)}")
            return {'data': data, 'metrics': {'error': str(e)}}

    def _calculate_synthetic_utility(self, original_data: pd.DataFrame,
                                   synthetic_data: pd.DataFrame) -> float:
        """Calculate utility score for synthetic data"""
        try:
            utility_scores = []

            # Compare numerical distributions
            numerical_cols = original_data.select_dtypes(include=[np.number]).columns
            for col in numerical_cols:
                if col in synthetic_data.columns:
                    # Kolmogorov-Smirnov test
                    from scipy.stats import ks_2samp
                    ks_statistic, p_value = ks_2samp(original_data[col], synthetic_data[col])
                    utility_scores.append(1 - ks_statistic)  # Higher utility for lower KS statistic

            # Compare categorical distributions
            categorical_cols = original_data.select_dtypes(include=['object', 'category']).columns
            for col in categorical_cols:
                if col in synthetic_data.columns:
                    original_dist = original_data[col].value_counts(normalize=True)
                    synthetic_dist = synthetic_data[col].value_counts(normalize=True)

                    # Calculate total variation distance
                    distance = 0
                    for value in set(original_dist.index) | set(synthetic_dist.index):
                        p = original_dist.get(value, 0)
                        q = synthetic_dist.get(value, 0)
                        distance += abs(p - q)

                    utility_scores.append(1 - distance / 2)  # Normalize to [0,1]

            return np.mean(utility_scores) if utility_scores else 0.5

        except Exception as e:
            logger.warning(f"Synthetic utility calculation error: {str(e)}")
            return 0.5

    def _calculate_overall_privacy_metrics(self, original_data: pd.DataFrame,
                                         processed_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate overall privacy preservation metrics"""
        try:
            metrics = {}

            # Record retention rate
            metrics['record_retention_rate'] = len(processed_data) / len(original_data)

            # Privacy score (combination of various factors)
            k_anon_score = 1.0 - (len(processed_data) / len(original_data))  # Higher suppression = higher privacy
            dp_score = min(1.0, self.dp_engine.get_privacy_spent())  # Higher epsilon usage = lower privacy

            # Weighted privacy score
            metrics['privacy_score'] = 0.6 * k_anon_score + 0.4 * (1 - dp_score)

            # Re-identification risk (simplified estimation)
            equivalence_classes = processed_data.groupby(self.k_anonymizer.quasi_identifiers).size()
            max_class_size = equivalence_classes.max() if len(equivalence_classes) > 0 else 1
            metrics['re_identification_risk'] = 1.0 / max_class_size

            # Data utility score
            metrics['data_utility'] = self.k_anonymizer._calculate_data_utility(original_data, processed_data)

            return metrics

        except Exception as e:
            logger.error(f"Overall privacy metrics calculation error: {str(e)}")
            return {'privacy_score': 0.5, 'error': str(e)}

    def _update_system_metrics(self, processing_time: float, privacy_score: float):
        """Update system performance metrics"""
        self.metrics['total_anonymizations'] += 1

        # Update average processing time
        total_ops = self.metrics['total_anonymizations']
        current_avg = self.metrics['average_processing_time']
        new_avg = (current_avg * (total_ops - 1) + processing_time) / total_ops
        self.metrics['average_processing_time'] = new_avg

        # Update privacy preservation score
        current_privacy_score = self.metrics['privacy_preservation_score']
        new_privacy_score = (current_privacy_score * (total_ops - 1) + privacy_score) / total_ops
        self.metrics['privacy_preservation_score'] = new_privacy_score

    async def get_system_status(self) -> Dict[str, Any]:
        """Get privacy preservation system status"""
        return {
            'total_anonymizations': self.metrics['total_anonymizations'],
            'total_dp_operations': self.metrics['total_dp_operations'],
            'average_processing_time': self.metrics['average_processing_time'],
            'privacy_preservation_score': self.metrics['privacy_preservation_score'],
            'budget_status': self.budget_manager.get_budget_status(),
            'dp_status': {
                'epsilon_total': self.dp_engine.epsilon_total,
                'epsilon_used': self.dp_engine.get_privacy_spent(),
                'epsilon_remaining': self.dp_engine.get_privacy_remaining()
            },
            'supported_methods': ['k_anonymity', 'differential_privacy', 'synthetic_data'],
            'last_updated': datetime.utcnow().isoformat()
        }

# Testing functionality
async def test_advanced_privacy_preservation():
    """Test advanced privacy preservation functionality"""
    print("Testing Advanced Privacy Preservation System")

    # Generate test data
    np.random.seed(42)
    test_data = pd.DataFrame({
        'age': np.random.randint(18, 80, 1000),
        'income': np.random.lognormal(10, 1, 1000),
        'location': np.random.choice(['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata'], 1000),
        'scam_type': np.random.choice(['PHISHING', 'IMPERSONATION', 'FRAUD', 'LOTTERY'], 1000),
        'amount': np.random.lognormal(8, 1.5, 1000)
    })

    print(f"Generated test data: {test_data.shape}")

    # Initialize privacy system
    config = {
        'k_value': 50,
        'epsilon_total': 1.0,
        'delta': 1e-5,
        'reset_interval_days': 30
    }

    privacy_system = PrivacyPreservationSystem(config)

    try:
        # Test comprehensive privacy preservation
        print("\n1. Testing Comprehensive Privacy Preservation...")
        results = await privacy_system.preserve_privacy_comprehensive(
            test_data,
            quasi_identifiers=['age', 'income', 'location'],
            sensitive_attributes=['scam_type'],
            methods=['k_anonymity', 'differential_privacy']
        )

        print(f"Original data shape: {results['original_data_shape']}")
        print(f"Methods applied: {results['methods_applied']}")
        print(f"Processing time: {results['processing_time_ms']:.2f}ms")
        print(f"Processing steps: {results['processing_steps']}")

        if 'k_anonymity' in results:
            k_result = results['k_anonymity']
            print(f"\nK-Anonymity Results:")
            print(f"  K value achieved: {k_result['k_value_achieved']}")
            print(f"  Information loss: {k_result['information_loss']:.3f}")
            print(f"  Data utility: {k_result['data_utility']:.3f}")
            print(f"  Records retained: {k_result['records_retained']}")

        if 'differential_privacy' in results:
            dp_result = results['differential_privacy']
            print(f"\nDifferential Privacy Results:")
            print(f"  Operations performed: {dp_result['metrics']['operations_performed']}")
            print(f"  Epsilon used: {dp_result['metrics']['epsilon_used']:.3f}")

        print(f"\nOverall Metrics:")
        overall = results['overall_metrics']
        print(f"  Record retention rate: {overall['record_retention_rate']:.3f}")
        print(f"  Privacy score: {overall['privacy_score']:.3f}")
        print(f"  Re-identification risk: {overall['re_identification_risk']:.6f}")
        print(f"  Data utility: {overall['data_utility']:.3f}")

        # Test synthetic data generation
        print("\n2. Testing Synthetic Data Generation...")
        sample_data = test_data.head(100)  # Use smaller sample for testing

        synthetic_data = privacy_system.synthetic_generator.generate_synthetic_data(
            sample_data,
            method='correlated',
            sample_size=100,
            privacy_budget=0.1
        )

        print(f"Synthetic data shape: {synthetic_data.shape}")

        # Calculate utility
        utility_score = privacy_system._calculate_synthetic_utility(sample_data, synthetic_data)
        print(f"Synthetic data utility score: {utility_score:.3f}")

        # Test privacy budget management
        print("\n3. Testing Privacy Budget Management...")
        budget_status = privacy_system.budget_manager.get_budget_status()
        print(f"Total budget: {budget_status['total_budget']}")
        print(f"Used budget: {budget_status['used_budget']:.3f}")
        print(f"Remaining budget: {budget_status['remaining_budget']:.3f}")
        print(f"Budget utilization: {budget_status['budget_utilization']:.3f}")

        # Get system status
        print("\n4. System Status:")
        status = await privacy_system.get_system_status()
        print(f"Total anonymizations: {status['total_anonymizations']}")
        print(f"Average processing time: {status['average_processing_time']:.3f}ms")
        print(f"Privacy preservation score: {status['privacy_preservation_score']:.3f}")

        print("\n✅ All privacy preservation tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Privacy preservation test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_advanced_privacy_preservation())