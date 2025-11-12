"""
I4C (Indian Cybercrime Coordination Centre) Historical Crime Data Integration
Advanced Historical Pattern Analysis for AEGIS

Implements comprehensive historical crime data analysis with:
- Temporal pattern analysis
- Geographic clustering
- Modus operandi classification
- Criminal network mapping
- Predictive trend analysis
- Cross-jurisdictional intelligence sharing
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, Text, Boolean, ARRAY, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID, JSON
import redis
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point, Polygon
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class CrimeCategory(Enum):
    """Crime categories for classification"""
    FINANCIAL_FRAUD = "financial_fraud"
    CYBER_FRAUD = "cyber_fraud"
    IMPERSONATION = "impersonation"
    IDENTITY_THEFT = "identity_theft"
    PHISHING = "phishing"
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    DATA_BREACH = "data_breach"
    ONLINE_SCAMS = "online_scams"
    DIGITAL_PAYMENTS_FRAUD = "digital_payments_fraud"
    SOCIAL_MEDIA_FRAUD = "social_media_fraud"
    BUSINESS_EMAIL_COMPROMISE = "business_email_compromise"

class InvestigationStatus(Enum):
    """Investigation status categories"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    UNDER_INVESTIGATION = "under_investigation"
    SOLVED = "solved"
    UNSOLVED = "unsolved"
    CLOSED = "closed"
    TRANSFERRED = "transferred"

class CriminalSophistication(Enum):
    """Criminal sophistication levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ADVANCED = "advanced"
    ORGANIZED = "organized"

@dataclass
class HistoricalCrimeRecord:
    """Historical crime record data structure"""
    case_id: str
    report_date: datetime
    crime_date: datetime
    crime_category: CrimeCategory
    subcategory: str
    modus_operandi: List[str]
    victim_profile: Dict[str, Any]
    perpetrator_profile: Dict[str, Any]
    location_data: Dict[str, Any]
    financial_loss: float
    currency: str
    digital_evidence: List[str]
    forensics_data: Dict[str, Any]
    investigation_details: Dict[str, Any]
    outcome: str
    status: InvestigationStatus
    law_enforcement_agency: str
    jurisdiction: str
    related_cases: List[str]
    criminal_network_id: Optional[str]
    sophistication_level: CriminalSophistication
    cross_border_impact: bool
    digital_platforms_used: List[str]
    victim_count: int
    perpetrator_count: int

@dataclass
class CrimePattern:
    """Identified crime pattern"""
    pattern_id: str
    pattern_type: str
    description: str
    confidence_score: float
    temporal_pattern: Dict[str, Any]
    geographic_pattern: Dict[str, Any]
    behavioral_pattern: Dict[str, Any]
    affected_cases: List[str]
    predicted_next_occurrence: Optional[datetime]
    risk_assessment: Dict[str, Any]

@dataclass
class CriminalNetwork:
    """Criminal network analysis"""
    network_id: str
    network_name: str
    member_count: int
    sophistication_level: CriminalSophistication
    primary_crime_types: List[CrimeCategory]
    geographic_scope: List[str]
    known_associates: List[str]
    modus_operandi: List[str]
    estimated_infrastructure: Dict[str, Any]
    financial_impact_estimate: float
    active_period: Tuple[datetime, datetime]
    current_status: str
    threat_level: str

class HistoricalCrimeData(Base):
    """SQLAlchemy model for historical crime data"""
    __tablename__ = "historical_crime_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id_hash = Column(String, nullable=False, unique=True, index=True)
    report_date = Column(DateTime, nullable=False, index=True)
    crime_date = Column(DateTime, nullable=False, index=True)
    crime_category = Column(String, nullable=False, index=True)
    subcategory = Column(String, nullable=True)
    modus_operandi_codes = Column(ARRAY(String), nullable=True)
    victim_demographics_hash = Column(String, nullable=True)  # Hashed for privacy
    perpetrator_demographics_hash = Column(String, nullable=True)  # Hashed for privacy
    location_cluster = Column(String, nullable=False, index=True)
    coordinates_lat = Column(Float, nullable=False)
    coordinates_lon = Column(Float, nullable=False)
    financial_loss = Column(Numeric(15, 2), nullable=True)
    currency = Column(String(3), nullable=False, default='INR')
    digital_evidence_count = Column(Integer, default=0)
    forensics_indicators = Column(ARRAY(String), nullable=True)
    investigation_duration_days = Column(Integer, nullable=True)
    outcome_code = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    law_enforcement_agency_code = Column(String, nullable=False)
    jurisdiction_code = Column(String, nullable=False, index=True)
    criminal_network_id_hash = Column(String, nullable=True, index=True)
    sophistication_level = Column(String, nullable=False)
    cross_border_impact = Column(Boolean, nullable=False, default=False)
    digital_platforms = Column(ARRAY(String), nullable=True)
    victim_count = Column(Integer, nullable=False, default=1)
    perpetrator_count = Column(Integer, nullable=False, default=1)
    data_quality_score = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CrimePatternRecord(Base):
    """SQLAlchemy model for identified crime patterns"""
    __tablename__ = "crime_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id = Column(String, nullable=False, unique=True, index=True)
    pattern_type = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    temporal_signature = Column(JSON, nullable=True)
    geographic_signature = Column(JSON, nullable=True)
    behavioral_signature = Column(JSON, nullable=True)
    affected_cases_count = Column(Integer, nullable=False, default=0)
    first_seen_date = Column(DateTime, nullable=False)
    last_seen_date = Column(DateTime, nullable=False)
    predicted_next_occurrence = Column(DateTime, nullable=True)
    risk_assessment = Column(JSON, nullable=True)
    pattern_strength = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CriminalNetworkRecord(Base):
    """SQLAlchemy model for criminal networks"""
    __tablename__ = "criminal_networks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id_hash = Column(String, nullable=False, unique=True, index=True)
    network_name = Column(String, nullable=False)
    member_count_estimate = Column(Integer, nullable=False)
    sophistication_level = Column(String, nullable=False)
    primary_crime_types = Column(ARRAY(String), nullable=True)
    geographic_scope = Column(ARRAY(String), nullable=True)
    known_associates_hash = Column(ARRAY(String), nullable=True)
    modus_operandi_codes = Column(ARRAY(String), nullable=True)
    infrastructure_indicators = Column(JSON, nullable=True)
    financial_impact_estimate = Column(Numeric(15, 2), nullable=True)
    active_start_date = Column(DateTime, nullable=False)
    active_end_date = Column(DateTime, nullable=True)
    current_status = Column(String, nullable=False)
    threat_level = Column(String, nullable=False, index=True)
    network_strength = Column(Float, nullable=False, default=0.0)
    cross_jurisdictional = Column(Boolean, nullable=False, default=False)
    last_activity_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CrimePatternAnalyzer:
    """
    Advanced crime pattern analysis engine
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.dbscan = DBSCAN(eps=0.3, min_samples=5)
        self.kmeans = KMeans(n_clusters=10, random_state=42)
        self.pca = PCA(n_components=5)
        self.pattern_cache = {}

    def analyze_temporal_patterns(self, crime_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal patterns in crime data"""
        logger.info("Analyzing temporal patterns in historical crime data")

        temporal_analysis = {
            'hourly_patterns': self._analyze_hourly_patterns(crime_data),
            'daily_patterns': self._analyze_daily_patterns(crime_data),
            'weekly_patterns': self._analyze_weekly_patterns(crime_data),
            'monthly_patterns': self._analyze_monthly_patterns(crime_data),
            'seasonal_patterns': self._analyze_seasonal_patterns(crime_data),
            'trend_analysis': self._analyze_temporal_trends(crime_data),
            'cyclical_patterns': self._detect_cyclical_patterns(crime_data)
        }

        return temporal_analysis

    def _analyze_hourly_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze hourly crime patterns"""
        if 'crime_date' not in df.columns:
            return {}

        df['hour'] = pd.to_datetime(df['crime_date']).dt.hour
        hourly_counts = df['hour'].value_counts().sort_index()

        # Find peak hours
        peak_hours = hourly_counts.nlargest(3).index.tolist()
        low_hours = hourly_counts.nsmallest(3).index.tolist()

        return {
            'distribution': hourly_counts.to_dict(),
            'peak_hours': peak_hours,
            'low_activity_hours': low_hours,
            'hourly_variance': float(hourly_counts.var()),
            'peak_to_off_peak_ratio': float(hourly_counts.max() / (hourly_counts.min() + 1))
        }

    def _analyze_daily_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze daily crime patterns"""
        df['day_of_month'] = pd.to_datetime(df['crime_date']).dt.day
        daily_counts = df['day_of_month'].value_counts().sort_index()

        return {
            'distribution': daily_counts.to_dict(),
            'peak_days': daily_counts.nlargest(5).index.tolist(),
            'monthly_variance': float(daily_counts.var()),
            'beginning_month_vs_end_month_ratio': float(
                daily_counts[daily_counts.index <= 10].sum() /
                (daily_counts[daily_counts.index >= 20].sum() + 1)
            )
        }

    def _analyze_weekly_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze weekly crime patterns"""
        df['day_of_week'] = pd.to_datetime(df['crime_date']).dt.day_name()
        weekly_counts = df['day_of_week'].value_counts()

        # Weekend vs Weekday analysis
        weekend_days = ['Saturday', 'Sunday']
        weekend_count = df[df['day_of_week'].isin(weekend_days)].shape[0]
        weekday_count = df[~df['day_of_week'].isin(weekend_days)].shape[0]

        return {
            'distribution': weekly_counts.to_dict(),
            'peak_day': weekly_counts.idxmax(),
            'lowest_day': weekly_counts.idxmin(),
            'weekend_vs_weekday_ratio': float(weekend_count / (weekday_count + 1)),
            'weekday_variance': float(df[~df['day_of_week'].isin(weekend_days)]['day_of_week'].value_counts().var())
        }

    def _analyze_monthly_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze monthly crime patterns"""
        df['month'] = pd.to_datetime(df['crime_date']).dt.month_name()
        monthly_counts = df['month'].value_counts()

        # Season analysis
        def get_season(month):
            if month in ['December', 'January', 'February']:
                return 'Winter'
            elif month in ['March', 'April', 'May']:
                return 'Spring'
            elif month in ['June', 'July', 'August']:
                return 'Summer'
            else:
                return 'Monsoon'

        df['season'] = df['month'].apply(get_season)
        seasonal_counts = df['season'].value_counts()

        return {
            'monthly_distribution': monthly_counts.to_dict(),
            'peak_month': monthly_counts.idxmax(),
            'lowest_month': monthly_counts.idxmin(),
            'seasonal_distribution': seasonal_counts.to_dict(),
            'peak_season': seasonal_counts.idxmax(),
            'monthly_variance': float(monthly_counts.var())
        }

    def _analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze seasonal patterns in detail"""
        df['month'] = pd.to_datetime(df['crime_date']).dt.month
        df['year'] = pd.to_datetime(df['crime_date']).dt.year

        # Calculate year-over-year changes for each month
        monthly_trends = {}
        for month in range(1, 13):
            month_data = df[df['month'] == month].groupby('year').size()
            if len(month_data) > 1:
                trend = np.polyfit(range(len(month_data)), month_data.values, 1)[0]
                monthly_trends[month] = float(trend)

        return {
            'monthly_trends': monthly_trends,
            'increasing_trend_months': [month for month, trend in monthly_trends.items() if trend > 0],
            'decreasing_trend_months': [month for month, trend in monthly_trends.items() if trend < 0],
            'strongest_trend_month': max(monthly_trends, key=monthly_trends.get) if monthly_trends else None
        }

    def _analyze_temporal_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall temporal trends"""
        df['year_month'] = pd.to_datetime(df['crime_date']).dt.to_period('M')
        monthly_counts = df['year_month'].value_counts().sort_index()

        if len(monthly_counts) < 3:
            return {'insufficient_data': True}

        # Calculate trend using linear regression
        x = np.arange(len(monthly_counts))
        y = monthly_counts.values
        trend_coefficient = np.polyfit(x, y, 1)[0]

        # Calculate seasonal decomposition components
        trend_component = np.convolve(y, np.ones(3)/3, mode='same')  # Simple moving average

        return {
            'overall_trend': 'increasing' if trend_coefficient > 0 else 'decreasing',
            'trend_strength': float(abs(trend_coefficient)),
            'trend_component': trend_component.tolist(),
            'peak_period': monthly_counts.idxmax().strftime('%Y-%m') if hasattr(monthly_counts.idxmax(), 'strftime') else str(monthly_counts.idxmax()),
            'lowest_period': monthly_counts.idxmin().strftime('%Y-%m') if hasattr(monthly_counts.idxmin(), 'strftime') else str(monthly_counts.idxmax()),
            'volatility': float(np.std(y))
        }

    def _detect_cyclical_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect cyclical patterns using autocorrelation"""
        df['date'] = pd.to_datetime(df['crime_date']).dt.date
        daily_counts = df.groupby('date').size().sort_index()

        if len(daily_counts) < 14:
            return {'insufficient_data': True}

        # Simple autocorrelation for different lags
        autocorrelations = {}
        series = daily_counts.values

        for lag in [7, 14, 30, 90]:  # Weekly, bi-weekly, monthly, quarterly
            if len(series) > lag:
                correlation = np.corrcoef(series[:-lag], series[lag:])[0, 1]
                autocorrelations[f'{lag}_day'] = float(correlation) if not np.isnan(correlation) else 0.0

        # Find strongest cyclical pattern
        strongest_cycle = max(autocorrelations, key=autocorrelations.get) if autocorrelations else None

        return {
            'autocorrelations': autocorrelations,
            'strongest_cyclical_pattern': strongest_cycle,
            'has_weekly_pattern': autocorrelations.get('7_day', 0) > 0.3,
            'has_monthly_pattern': autocorrelations.get('30_day', 0) > 0.3
        }

    def analyze_geographic_patterns(self, crime_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze geographic patterns in crime data"""
        logger.info("Analyzing geographic patterns in historical crime data")

        if 'coordinates_lat' not in crime_data.columns or 'coordinates_lon' not in crime_data.columns:
            return {'error': 'Missing coordinate data'}

        # Create point geometries
        geometry = [Point(xy) for xy in zip(crime_data['coordinates_lon'], crime_data['coordinates_lat'])]
        gdf = gpd.GeoDataFrame(crime_data, geometry=geometry)

        geographic_analysis = {
            'hotspot_analysis': self._identify_geographic_hotspots(gdf),
            'spatial_clustering': self._perform_spatial_clustering(gdf),
            'regional_analysis': self._analyze_regional_patterns(gdf),
            'geographic_distribution': self._analyze_geographic_distribution(gdf),
            'spatial_temporal_patterns': self._analyze_spatial_temporal_patterns(gdf)
        }

        return geographic_analysis

    def _identify_geographic_hotspots(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Identify geographic hotspots using density analysis"""
        if len(gdf) < 10:
            return {'insufficient_data': True}

        # Create a grid for density analysis
        bounds = gdf.total_bounds
        grid_size = 0.01  # Approximately 1km grid

        # Create grid cells
        x_coords = np.arange(bounds[0], bounds[2] + grid_size, grid_size)
        y_coords = np.arange(bounds[1], bounds[3] + grid_size, grid_size)

        hotspot_cells = []
        for i, x in enumerate(x_coords[:-1]):
            for j, y in enumerate(y_coords[:-1]):
                cell_polygon = Polygon([
                    (x, y), (x + grid_size, y),
                    (x + grid_size, y + grid_size), (x, y + grid_size)
                ])

                # Count points in cell
                points_in_cell = gdf[gdf.geometry.within(cell_polygon)]
                count = len(points_in_cell)

                if count >= 3:  # Minimum threshold for hotspot
                    hotspot_cells.append({
                        'cell_id': f"grid_{i}_{j}",
                        'centroid_lat': y + grid_size/2,
                        'centroid_lon': x + grid_size/2,
                        'crime_count': count,
                        'density': count / (grid_size * grid_size),
                        'crime_types': points_in_cell['crime_category'].value_counts().to_dict()
                    })

        # Sort by density
        hotspot_cells.sort(key=lambda x: x['density'], reverse=True)

        return {
            'total_hotspots': len(hotspot_cells),
            'top_hotspots': hotspot_cells[:10],
            'hotspot_density_distribution': [cell['density'] for cell in hotspot_cells],
            'average_hotspot_density': np.mean([cell['density'] for cell in hotspot_cells]) if hotspot_cells else 0
        }

    def _perform_spatial_clustering(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Perform spatial clustering analysis"""
        if len(gdf) < 20:
            return {'insufficient_data': True}

        # Extract coordinates
        coords = np.array([[point.x, point.y] for point in gdf.geometry])

        # Perform DBSCAN clustering
        clustering = DBSCAN(eps=0.01, min_samples=3).fit(coords)
        labels = clustering.labels_

        # Analyze clusters
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in labels else 0)

        clusters = []
        for label in unique_labels:
            if label == -1:  # Noise points
                continue

            cluster_mask = labels == label
            cluster_points = gdf[cluster_mask]

            # Calculate cluster centroid
            centroid_x = cluster_points.geometry.x.mean()
            centroid_y = cluster_points.geometry.y.mean()

            clusters.append({
                'cluster_id': int(label),
                'centroid_lat': centroid_y,
                'centroid_lon': centroid_x,
                'size': len(cluster_points),
                'crime_types': cluster_points['crime_category'].value_counts().to_dict(),
                'time_span': {
                    'start': cluster_points['crime_date'].min(),
                    'end': cluster_points['crime_date'].max()
                }
            })

        return {
            'n_clusters': n_clusters,
            'n_noise_points': list(labels).count(-1),
            'clusters': clusters,
            'cluster_sizes': [cluster['size'] for cluster in clusters],
            'average_cluster_size': np.mean([cluster['size'] for cluster in clusters]) if clusters else 0
        }

    def _analyze_regional_patterns(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Analyze crime patterns by region"""
        if 'jurisdiction_code' not in gdf.columns:
            return {'error': 'Missing jurisdiction data'}

        regional_analysis = {}
        for jurisdiction in gdf['jurisdiction_code'].unique():
            region_data = gdf[gdf['jurisdiction_code'] == jurisdiction]

            regional_analysis[jurisdiction] = {
                'total_crimes': len(region_data),
                'crime_types': region_data['crime_category'].value_counts().to_dict(),
                'average_financial_loss': float(region_data['financial_loss'].mean()) if 'financial_loss' in region_data.columns else 0,
                'geographic_center': {
                    'lat': region_data.geometry.y.mean(),
                    'lon': region_data.geometry.x.mean()
                },
                'time_span': {
                    'start': region_data['crime_date'].min(),
                    'end': region_data['crime_date'].max()
                },
                'sophistication_levels': region_data['sophistication_level'].value_counts().to_dict() if 'sophistication_level' in region_data.columns else {}
            }

        return {
            'regional_breakdown': regional_analysis,
            'total_regions': len(regional_analysis),
            'highest_crime_region': max(regional_analysis, key=lambda x: regional_analysis[x]['total_crimes']) if regional_analysis else None
        }

    def _analyze_geographic_distribution(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Analyze overall geographic distribution"""
        coords = np.array([[point.x, point.y] for point in gdf.geometry])

        # Calculate bounding box
        bounds = gdf.total_bounds

        # Calculate geographic center (centroid)
        centroid = gdf.geometry.unary_union.centroid

        # Calculate standard distance (measure of dispersion)
        distances_from_centroid = [point.distance(centroid) for point in gdf.geometry]
        standard_distance = np.std(distances_from_centroid)

        return {
            'bounding_box': {
                'min_lat': float(bounds[1]),
                'max_lat': float(bounds[3]),
                'min_lon': float(bounds[0]),
                'max_lon': float(bounds[2])
            },
            'geographic_center': {
                'lat': float(centroid.y),
                'lon': float(centroid.x)
            },
            'standard_distance': float(standard_distance),
            'spatial_dispersion': float(np.var(distances_from_centroid)),
            'coverage_area_km2': float(len(gdf) * (standard_distance ** 2) * np.pi / 1000000)  # Rough estimate
        }

    def _analyze_spatial_temporal_patterns(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Analyze how crime patterns spread geographically over time"""
        if len(gdf) < 20:
            return {'insufficient_data': True}

        # Sort by time
        gdf_sorted = gdf.sort_values('crime_date')

        # Divide time into periods
        n_periods = min(5, len(gdf_sorted) // 10)  # Maximum 5 periods, minimum 10 crimes per period
        if n_periods < 2:
            return {'insufficient_data': True}

        period_size = len(gdf_sorted) // n_periods
        spatial_temporal_analysis = []

        for i in range(n_periods):
            start_idx = i * period_size
            end_idx = (i + 1) * period_size if i < n_periods - 1 else len(gdf_sorted)

            period_data = gdf_sorted.iloc[start_idx:end_idx]

            if len(period_data) > 0:
                centroid = period_data.geometry.unary_union.centroid
                spatial_temporal_analysis.append({
                    'period': i + 1,
                    'time_range': {
                        'start': period_data['crime_date'].min(),
                        'end': period_data['crime_date'].max()
                    },
                    'crime_count': len(period_data),
                    'geographic_center': {
                        'lat': float(centroid.y),
                        'lon': float(centroid.x)
                    },
                    'spatial_dispersion': float(np.std([point.distance(centroid) for point in period_data.geometry]))
                })

        return {
            'periods': spatial_temporal_analysis,
            'spatial_drift': self._calculate_spatial_drift(spatial_temporal_analysis),
            'temporal_expansion': self._calculate_temporal_expansion(spatial_temporal_analysis)
        }

    def _calculate_spatial_drift(self, periods: List[Dict]) -> Dict[str, Any]:
        """Calculate geographic center drift over time"""
        if len(periods) < 2:
            return {'insufficient_data': True}

        centers = [(p['geographic_center']['lon'], p['geographic_center']['lat']) for p in periods]

        # Calculate total drift
        total_drift = 0
        for i in range(1, len(centers)):
            dx = centers[i][0] - centers[i-1][0]
            dy = centers[i][1] - centers[i-1][1]
            total_drift += np.sqrt(dx**2 + dy**2)

        return {
            'total_drift_km': total_drift * 111,  # Rough conversion to kilometers
            'average_drift_per_period_km': (total_drift * 111) / (len(centers) - 1),
            'drift_direction': 'expanding' if total_drift > 0.01 else 'stable'
        }

    def _calculate_temporal_expansion(self, periods: List[Dict]) -> Dict[str, Any]:
        """Calculate spatial expansion over time"""
        if len(periods) < 2:
            return {'insufficient_data': True}

        dispersions = [p['spatial_dispersion'] for p in periods]

        return {
            'initial_dispersion': dispersions[0],
            'final_dispersion': dispersions[-1],
            'expansion_factor': dispersions[-1] / (dispersions[0] + 0.001),
            'expansion_trend': 'expanding' if dispersions[-1] > dispersions[0] else 'contracting'
        }

    def analyze_modus_operandi_patterns(self, crime_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze modus operandi patterns"""
        logger.info("Analyzing modus operandi patterns in historical crime data")

        if 'modus_operandi_codes' not in crime_data.columns:
            return {'error': 'Missing modus operandi data'}

        mo_analysis = {
            'common_mo_sequences': self._analyze_mo_sequences(crime_data),
            'mo_by_crime_type': self._analyze_mo_by_crime_type(crime_data),
            'mo_evolution': self._analyze_mo_evolution(crime_data),
            'sophistication_progression': self._analyze_sophistication_progression(crime_data),
            'cross_crime_mo_patterns': self._analyze_cross_crime_mo_patterns(crime_data)
        }

        return mo_analysis

    def _analyze_mo_sequences(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze common sequences of modus operandi"""
        mo_sequences = []

        for _, row in df.iterrows():
            if pd.notna(row['modus_operandi_codes']) and row['modus_operandi_codes']:
                # Sort MO codes to create consistent sequences
                sorted_mo = sorted(row['modus_operandi_codes'])
                mo_sequence = '_'.join(sorted_mo)
                mo_sequences.append(mo_sequence)

        if not mo_sequences:
            return {'no_data': True}

        sequence_counts = pd.Series(mo_sequences).value_counts()

        return {
            'total_unique_sequences': len(sequence_counts),
            'most_common_sequences': sequence_counts.head(10).to_dict(),
            'sequence_diversity': float(len(sequence_counts) / len(mo_sequences)),
            'average_sequence_length': float(np.mean([len(seq.split('_')) for seq in mo_sequences]))
        }

    def _analyze_mo_by_crime_type(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze MO patterns by crime type"""
        mo_by_crime = {}

        for crime_type in df['crime_category'].unique():
            crime_data = df[df['crime_category'] == crime_type]

            # Flatten all MO codes for this crime type
            all_mo = []
            for mo_list in crime_data['modus_operandi_codes'].dropna():
                if mo_list:
                    all_mo.extend(mo_list)

            if all_mo:
                mo_counts = pd.Series(all_mo).value_counts()
                mo_by_crime[crime_type] = {
                    'most_common_mo': mo_counts.head(5).to_dict(),
                    'unique_mo_count': len(mo_counts),
                    'total_mo_instances': len(all_mo)
                }

        return {
            'crime_type_mo_analysis': mo_by_crime,
            'shared_mo_patterns': self._find_shared_mo_patterns(mo_by_crime)
        }

    def _find_shared_mo_patterns(self, mo_by_crime: Dict) -> List[str]:
        """Find MO patterns shared across multiple crime types"""
        all_mo_sets = []
        for crime_type, data in mo_by_crime.items():
            mo_set = set(data['most_common_mo'].keys())
            all_mo_sets.append(mo_set)

        if len(all_mo_sets) < 2:
            return []

        # Find intersection of MO sets
        shared_mo = set.intersection(*all_mo_sets) if all_mo_sets else set()
        return list(shared_mo)

    def _analyze_mo_evolution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze how modus operandi has evolved over time"""
        df['year'] = pd.to_datetime(df['crime_date']).dt.year

        mo_evolution = {}
        for year in sorted(df['year'].unique()):
            year_data = df[df['year'] == year]

            # Collect MO codes for this year
            year_mo = []
            for mo_list in year_data['modus_operandi_codes'].dropna():
                if mo_list:
                    year_mo.extend(mo_list)

            if year_mo:
                mo_counts = pd.Series(year_mo).value_counts()
                mo_evolution[year] = {
                    'top_mo': mo_counts.head(5).to_dict(),
                    'unique_mo_count': len(mo_counts),
                    'total_instances': len(year_mo)
                }

        return {
            'yearly_evolution': mo_evolution,
            'emerging_mo_trends': self._identify_emerging_mo_trends(mo_evolution),
            'declining_mo_trends': self._identify_declining_mo_trends(mo_evolution)
        }

    def _identify_emerging_mo_trends(self, mo_evolution: Dict) -> List[str]:
        """Identify emerging MO trends"""
        if len(mo_evolution) < 2:
            return []

        years = sorted(mo_evolution.keys())
        recent_years = years[-2:]
        earlier_years = years[:-2] if len(years) > 2 else years[:1]

        # Get MO counts for recent and earlier periods
        recent_mo = {}
        for year in recent_years:
            for mo, count in mo_evolution[year]['top_mo'].items():
                recent_mo[mo] = recent_mo.get(mo, 0) + count

        earlier_mo = {}
        for year in earlier_years:
            for mo, count in mo_evolution[year]['top_mo'].items():
                earlier_mo[mo] = earlier_mo.get(mo, 0) + count

        # Find MOs with significant increase
        emerging_mo = []
        for mo in recent_mo:
            if mo not in earlier_mo:
                emerging_mo.append(mo)
            else:
                increase_ratio = recent_mo[mo] / (earlier_mo[mo] + 1)
                if increase_ratio > 2.0:  # More than 2x increase
                    emerging_mo.append(mo)

        return emerging_mo

    def _identify_declining_mo_trends(self, mo_evolution: Dict) -> List[str]:
        """Identify declining MO trends"""
        if len(mo_evolution) < 2:
            return []

        years = sorted(mo_evolution.keys())
        recent_years = years[-2:]
        earlier_years = years[:-2] if len(years) > 2 else years[:1]

        # Get MO counts for recent and earlier periods
        recent_mo = {}
        for year in recent_years:
            for mo, count in mo_evolution[year]['top_mo'].items():
                recent_mo[mo] = recent_mo.get(mo, 0) + count

        earlier_mo = {}
        for year in earlier_years:
            for mo, count in mo_evolution[year]['top_mo'].items():
                earlier_mo[mo] = earlier_mo.get(mo, 0) + count

        # Find MOs with significant decrease
        declining_mo = []
        for mo in earlier_mo:
            if mo not in recent_mo:
                declining_mo.append(mo)
            else:
                decrease_ratio = earlier_mo[mo] / (recent_mo[mo] + 1)
                if decrease_ratio > 2.0:  # More than 2x decrease
                    declining_mo.append(mo)

        return declining_mo

    def _analyze_sophistication_progression(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sophistication level progression"""
        if 'sophistication_level' not in df.columns:
            return {'no_sophistication_data': True}

        df['year'] = pd.to_datetime(df['crime_date']).dt.year
        sophistication_by_year = {}

        for year in sorted(df['year'].unique()):
            year_data = df[df['year'] == year]
            soph_counts = year_data['sophistication_level'].value_counts()
            sophistication_by_year[year] = soph_counts.to_dict()

        return {
            'yearly_sophistication': sophistication_by_year,
            'sophistication_trend': self._calculate_sophistication_trend(sophistication_by_year),
            'advanced_crime_increase': self._analyze_advanced_crime_increase(sophistication_by_year)
        }

    def _calculate_sophistication_trend(self, sophistication_by_year: Dict) -> str:
        """Calculate overall sophistication trend"""
        if len(sophistication_by_year) < 2:
            return 'insufficient_data'

        # Calculate average sophistication score per year
        sophistication_scores = {'low': 1, 'medium': 2, 'high': 3, 'advanced': 4, 'organized': 5}
        yearly_scores = []

        for year in sorted(sophistication_by_year.keys()):
            year_data = sophistication_by_year[year]
            total_crimes = sum(year_data.values())
            weighted_score = sum(sophistication_scores.get(level, 0) * count
                                for level, count in year_data.items())
            avg_score = weighted_score / total_crimes if total_crimes > 0 else 0
            yearly_scores.append(avg_score)

        # Calculate trend
        if len(yearly_scores) >= 2:
            trend = np.polyfit(range(len(yearly_scores)), yearly_scores, 1)[0]
            return 'increasing' if trend > 0.1 else 'stable' if abs(trend) <= 0.1 else 'decreasing'

        return 'insufficient_data'

    def _analyze_advanced_crime_increase(self, sophistication_by_year: Dict) -> Dict[str, Any]:
        """Analyze increase in advanced/organized crimes"""
        advanced_levels = ['advanced', 'organized']
        advanced_counts = {}

        for year in sorted(sophistication_by_year.keys()):
            year_data = sophistication_by_year[year]
            advanced_count = sum(year_data.get(level, 0) for level in advanced_levels)
            total_count = sum(year_data.values())
            advanced_percentage = (advanced_count / total_count * 100) if total_count > 0 else 0
            advanced_counts[year] = {
                'count': advanced_count,
                'percentage': advanced_percentage
            }

        return {
            'yearly_advanced_crimes': advanced_counts,
            'advanced_crime_trend': 'increasing' if len(advanced_counts) > 1 and
                                 list(advanced_counts.values())[-1]['percentage'] >
                                 list(advanced_counts.values())[0]['percentage'] else 'stable'
        }

    def _analyze_cross_crime_mo_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze MO patterns that cross crime categories"""
        # Create MO to crime type mapping
        mo_to_crime_types = {}

        for _, row in df.iterrows():
            if pd.notna(row['modus_operandi_codes']) and row['modus_operandi_codes']:
                crime_type = row['crime_category']
                for mo in row['modus_operandi_codes']:
                    if mo not in mo_to_crime_types:
                        mo_to_crime_types[mo] = set()
                    mo_to_crime_types[mo].add(crime_type)

        # Find MOs used across multiple crime types
        cross_crime_mo = {}
        for mo, crime_types in mo_to_crime_types.items():
            if len(crime_types) > 1:
                cross_crime_mo[mo] = {
                    'crime_types': list(crime_types),
                    'crime_type_count': len(crime_types),
                    'versatility_score': len(crime_types) / len(df['crime_category'].unique())
                }

        # Sort by versatility
        sorted_cross_mo = sorted(cross_crime_mo.items(),
                               key=lambda x: x[1]['crime_type_count'], reverse=True)

        return {
            'total_cross_crime_mo': len(cross_crime_mo),
            'most_versatile_mo': dict(sorted_cross_mo[:10]),
            'cross_crime_patterns': [
                {
                    'mo': mo,
                    'crime_types': data['crime_types'],
                    'versatility_score': data['versatility_score']
                }
                for mo, data in sorted_cross_mo[:20]
            ]
        }

class I4CIntegrationService:
    """
    Main I4C integration service for historical crime data analysis
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('i4c_base_url', 'https://api.i4c.gov.in')
        self.api_key = config.get('i4c_api_key')
        self.pattern_analyzer = CrimePatternAnalyzer()

        # Database setup
        self.engine = create_engine(config.get('database_url', 'sqlite:///aegis_i4c.db'))
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Redis for caching
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 2),
            decode_responses=True
        )

        # Analysis configuration
        self.batch_size = config.get('batch_size', 1000)
        self.analysis_interval = config.get('analysis_interval', 3600)  # 1 hour
        self.pattern_confidence_threshold = config.get('pattern_confidence_threshold', 0.7)

        self.session = None
        self.last_analysis_time = None
        self.total_records_analyzed = 0
        self.total_patterns_identified = 0

    async def initialize(self):
        """Initialize the I4C integration service"""
        logger.info("Initializing I4C Integration Service")

        # Create HTTP session
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'AEGIS-I4C-Integration/1.0'
            },
            timeout=aiohttp.ClientTimeout(total=60)
        )

        # Test connectivity
        await self._test_i4c_connectivity()

        logger.info("I4C Integration Service initialized successfully")

    async def _test_i4c_connectivity(self):
        """Test connectivity to I4C API"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    logger.info("I4C API connectivity test successful")
                else:
                    logger.warning(f"I4C API health check failed: {response.status}")
        except Exception as e:
            logger.error(f"I4C API connectivity test failed: {str(e)}")
            # Don't raise - we can work with cached/simulated data

    async def fetch_historical_crime_data(self, start_date: datetime, end_date: datetime) -> List[HistoricalCrimeRecord]:
        """
        Fetch historical crime data from I4C API within specified date range
        """
        logger.info(f"Fetching I4C historical crime data from {start_date} to {end_date}")

        # For demo purposes, generate synthetic historical data
        # In production, this would fetch from actual I4C API
        crime_records = []

        # Generate synthetic historical crime records
        num_records = np.random.randint(100, 1000)
        for i in range(num_records):
            crime_date = start_date + timedelta(
                days=np.random.randint(0, (end_date - start_date).days)
            )

            # Generate realistic crime data
            crime_category = np.random.choice(list(CrimeCategory), p=[
                0.3, 0.25, 0.15, 0.1, 0.08, 0.05, 0.03, 0.02, 0.01, 0.005, 0.003, 0.002
            ])

            sophistication = np.random.choice(list(CriminalSophistication), p=[
                0.4, 0.3, 0.2, 0.08, 0.02
            ])

            # Generate location around major Indian cities
            cities = [
                (28.6139, 77.2090),  # Delhi
                (19.0760, 72.8777),  # Mumbai
                (12.9716, 77.5946),  # Bengaluru
                (17.3850, 78.4867),  # Hyderabad
                (13.0827, 80.2707),  # Chennai
                (22.5726, 88.3639),  # Kolkata
                (26.9124, 75.7873),  # Jaipur
                (23.2599, 77.4126),  # Bhopal
                (21.1458, 79.0882)   # Nagpur
            ]

            city_lat, city_lon = cities[np.random.randint(0, len(cities))]
            location_lat = city_lat + np.random.uniform(-0.5, 0.5)
            location_lon = city_lon + np.random.uniform(-0.5, 0.5)

            # Generate modus operandi
            mo_options = [
                ['phishing_email', 'fake_website', 'social_engineering'],
                ['impersonation', 'document_forgery', 'identity_theft'],
                ['malware', 'data_breach', 'system_compromise'],
                ['upi_fraud', 'fake_payment_gateway', 'transaction_interception'],
                ['social_media_scam', 'fake_profile', 'financial_fraud']
            ]

            modus_operandi = np.random.choice(mo_options)
            if np.random.random() < 0.3:  # 30% chance of additional MO
                additional_mo = np.random.choice(['phone_call', 'sms_scam', 'whatsapp_fraud'])
                modus_operandi.append(additional_mo)

            record = HistoricalCrimeRecord(
                case_id=f"I4C_{uuid.uuid4().hex[:12].upper()}",
                report_date=crime_date + timedelta(hours=np.random.randint(1, 72)),
                crime_date=crime_date,
                crime_category=crime_category,
                subcategory=f"{crime_category.value}_{np.random.randint(1, 10):02d}",
                modus_operandi=modus_operandi,
                victim_profile={
                    'age_group': np.random.choice(['18-25', '26-35', '36-45', '46-55', '55+']),
                    'gender': np.random.choice(['M', 'F', 'Other']),
                    'occupation': np.random.choice(['student', 'employed', 'business', 'retired', 'unemployed']),
                    'location_type': np.random.choice(['urban', 'suburban', 'rural'])
                },
                perpetrator_profile={
                    'estimated_age': np.random.randint(18, 65),
                    'organization_type': np.random.choice(['individual', 'small_group', 'organized_gang']),
                    'technical_skill': sophistication.value,
                    'location_type': np.random.choice(['domestic', 'international', 'mixed'])
                },
                location_data={
                    'latitude': location_lat,
                    'longitude': location_lon,
                    'city': 'Unknown',
                    'state': 'Unknown',
                    'pincode': f"{np.random.randint(100000, 999999)}"
                },
                financial_loss=np.random.lognormal(8, 2),  # Log-normal distribution
                currency='INR',
                digital_evidence=[f'evidence_{j}' for j in range(np.random.randint(0, 5))],
                forensics_data={
                    'ip_addresses': [f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"],
                    'device_fingerprints': [f"device_{uuid.uuid4().hex[:8]}"],
                    'malware_signatures': np.random.choice([], p=[0.7, 0.3]).tolist()
                },
                investigation_details={
                    'duration_days': np.random.randint(1, 365),
                    'agencies_involved': np.random.randint(1, 4),
                    'cross_jurisdictional': np.random.random() < 0.2
                },
                outcome=np.random.choice(['solved', 'unsolved', 'pending', 'closed'], p=[0.3, 0.4, 0.2, 0.1]),
                status=np.random.choice(list(InvestigationStatus)),
                law_enforcement_agency=f"LEA_{np.random.randint(1, 20):02d}",
                jurisdiction=f"JUR_{np.random.randint(1, 15):02d}",
                related_cases=[f"CASE_{uuid.uuid4().hex[:8].upper()}" for _ in range(np.random.randint(0, 3))],
                criminal_network_id=f"NET_{uuid.uuid4().hex[:8].upper()}" if np.random.random() < 0.2 else None,
                sophistication_level=sophistication,
                cross_border_impact=np.random.random() < 0.15,
                digital_platforms_used=np.random.choice([
                    ['email', 'website'],
                    ['social_media', 'messaging_app'],
                    ['banking_portal', 'payment_app'],
                    ['ecommerce', 'job_portal'],
                    ['matrimony_site', 'dating_app']
                ], p=[0.3, 0.25, 0.2, 0.15, 0.1]),
                victim_count=np.random.randint(1, 50),
                perpetrator_count=np.random.randint(1, 10)
            )
            crime_records.append(record)

        logger.info(f"Fetched {len(crime_records)} historical crime records from I4C (simulated)")
        return crime_records

    async def analyze_historical_patterns(self, crime_records: List[HistoricalCrimeRecord]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of historical crime patterns
        """
        logger.info(f"Analyzing patterns in {len(crime_records)} historical crime records")

        if not crime_records:
            return {'error': 'No crime records to analyze'}

        # Convert to DataFrame for analysis
        df = pd.DataFrame([self._crime_record_to_dict(record) for record in crime_records])

        # Store records in database
        await self._store_crime_records(df)

        # Perform pattern analysis
        analysis_results = {
            'temporal_patterns': self.pattern_analyzer.analyze_temporal_patterns(df),
            'geographic_patterns': self.pattern_analyzer.analyze_geographic_patterns(df),
            'modus_operandi_patterns': self.pattern_analyzer.analyze_modus_operandi_patterns(df),
            'criminal_network_analysis': await self._analyze_criminal_networks(df),
            'sophistication_analysis': await self._analyze_sophistication_trends(df),
            'cross_jurisdictional_patterns': await self._analyze_cross_jurisdictional_patterns(df),
            'predictive_insights': await self._generate_predictive_insights(df)
        }

        # Identify significant patterns
        significant_patterns = await self._identify_significant_patterns(analysis_results)

        # Store analysis results
        await self._store_analysis_results(analysis_results, significant_patterns)

        # Cache results
        await self._cache_analysis_results(analysis_results)

        # Update metrics
        self.total_records_analyzed += len(crime_records)
        self.total_patterns_identified += len(significant_patterns)

        logger.info(f"Pattern analysis completed: {len(significant_patterns)} significant patterns identified")

        return {
            'analysis_summary': {
                'records_analyzed': len(crime_records),
                'patterns_identified': len(significant_patterns),
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'analysis_categories': list(analysis_results.keys())
            },
            'detailed_results': analysis_results,
            'significant_patterns': significant_patterns
        }

    def _crime_record_to_dict(self, record: HistoricalCrimeRecord) -> Dict:
        """Convert HistoricalCrimeRecord to dictionary"""
        return {
            'case_id_hash': hashlib.sha256(record.case_id.encode()).hexdigest()[:16],
            'report_date': record.report_date,
            'crime_date': record.crime_date,
            'crime_category': record.crime_category.value,
            'subcategory': record.subcategory,
            'modus_operandi_codes': record.modus_operandi,
            'victim_demographics_hash': hashlib.sha256(
                json.dumps(record.victim_profile, sort_keys=True).encode()
            ).hexdigest()[:16],
            'perpetrator_demographics_hash': hashlib.sha256(
                json.dumps(record.perpetrator_profile, sort_keys=True).encode()
            ).hexdigest()[:16],
            'location_cluster': self._get_location_cluster(
                record.location_data['latitude'],
                record.location_data['longitude']
            ),
            'coordinates_lat': record.location_data['latitude'],
            'coordinates_lon': record.location_data['longitude'],
            'financial_loss': record.financial_loss,
            'currency': record.currency,
            'digital_evidence_count': len(record.digital_evidence),
            'forensics_indicators': list(record.forensics_data.get('malware_signatures', [])),
            'investigation_duration_days': record.investigation_details.get('duration_days'),
            'outcome_code': record.outcome,
            'status': record.status.value,
            'law_enforcement_agency_code': record.law_enforcement_agency,
            'jurisdiction_code': record.jurisdiction,
            'criminal_network_id_hash': hashlib.sha256(
                record.criminal_network_id.encode()
            ).hexdigest()[:16] if record.criminal_network_id else None,
            'sophistication_level': record.sophistication_level.value,
            'cross_border_impact': record.cross_border_impact,
            'digital_platforms': record.digital_platforms_used,
            'victim_count': record.victim_count,
            'perpetrator_count': record.perpetrator_count
        }

    def _get_location_cluster(self, lat: float, lon: float) -> str:
        """Get location cluster from coordinates"""
        # Simple grid-based clustering (approximate 5km x 5km grid)
        lat_grid = int(lat * 20)  # 0.05 degree grid
        lon_grid = int(lon * 20)
        return f"LOC_{lat_grid:04d}_{lon_grid:04d}"

    async def _store_crime_records(self, df: pd.DataFrame):
        """Store crime records in database"""
        db = self.SessionLocal()
        try:
            for _, row in df.iterrows():
                db_record = HistoricalCrimeData(**row.to_dict())
                db.add(db_record)

            db.commit()
            logger.info(f"Stored {len(df)} historical crime records in database")

        except Exception as e:
            db.rollback()
            logger.error(f"Error storing crime records: {str(e)}")
            raise
        finally:
            db.close()

    async def _analyze_criminal_networks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze criminal network patterns"""
        # Group by criminal network
        network_analysis = {}

        # Analyze known networks
        known_networks = df[df['criminal_network_id_hash'].notna()]
        if len(known_networks) > 0:
            for network_hash in known_networks['criminal_network_id_hash'].unique():
                network_data = known_networks[known_networks['criminal_network_id_hash'] == network_hash]

                network_analysis[network_hash] = {
                    'case_count': len(network_data),
                    'crime_types': network_data['crime_category'].value_counts().to_dict(),
                    'geographic_scope': network_data['location_cluster'].nunique(),
                    'time_span': {
                        'start': network_data['crime_date'].min(),
                        'end': network_data['crime_date'].max()
                    },
                    'total_financial_loss': float(network_data['financial_loss'].sum()),
                    'sophistication_levels': network_data['sophistication_level'].value_counts().to_dict(),
                    'cross_border_cases': network_data['cross_border_impact'].sum()
                }

        return {
            'known_networks': network_analysis,
            'total_known_networks': len(network_analysis),
            'potential_network_indicators': self._identify_potential_networks(df)
        }

    def _identify_potential_networks(self, df: pd.DataFrame) -> List[Dict]:
        """Identify potential criminal networks based on patterns"""
        potential_networks = []

        # Look for patterns suggesting network activity
        # 1. Same MO across multiple locations
        mo_location_analysis = df.groupby('modus_operandi_codes').agg({
            'location_cluster': 'nunique',
            'case_id_hash': 'count',
            'crime_date': ['min', 'max']
        }).reset_index()

        # Filter for MOs used in multiple locations
        potential_network_mo = mo_location_analysis[
            (mo_location_analysis[('location_cluster', 'nunique')] >= 3) &
            (mo_location_analysis[('case_id_hash', 'count')] >= 5)
        ]

        for _, row in potential_network_mo.iterrows():
            potential_networks.append({
                'indicator_type': 'multi_location_mo',
                'modus_operandi': row['modus_operandi_codes'],
                'location_count': row[('location_cluster', 'nunique')],
                'case_count': row[('case_id_hash', 'count')],
                'time_span_days': (row[('crime_date', 'max')] - row[('crime_date', 'min')]).days,
                'confidence': min(0.8, row[('case_id_hash', 'count')] / 20)
            })

        # 2. Temporal clustering of similar crimes
        for crime_type in df['crime_category'].unique():
            crime_type_data = df[df['crime_category'] == crime_type].sort_values('crime_date')

            # Look for temporal clusters
            for i in range(len(crime_type_data) - 3):
                window = crime_type_data.iloc[i:i+4]
                time_span = (window['crime_date'].max() - window['crime_date'].min()).days

                if time_span <= 30 and len(window['location_cluster'].unique()) >= 2:
                    potential_networks.append({
                        'indicator_type': 'temporal_spatial_cluster',
                        'crime_type': crime_type,
                        'case_count': len(window),
                        'location_count': len(window['location_cluster'].unique()),
                        'time_span_days': time_span,
                        'confidence': min(0.7, len(window) / 10)
                    })

        return potential_networks

    async def _analyze_sophistication_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze sophistication level trends"""
        sophistication_analysis = {}

        # Overall sophistication distribution
        sophistication_dist = df['sophistication_level'].value_counts().to_dict()

        # Sophistication by crime type
        sophistication_by_crime = {}
        for crime_type in df['crime_category'].unique():
            crime_data = df[df['crime_category'] == crime_type]
            sophistication_by_crime[crime_type] = crime_data['sophistication_level'].value_counts().to_dict()

        # Sophistication vs financial impact correlation
        sophistication_impact = df.groupby('sophistication_level')['financial_loss'].agg(['mean', 'median', 'std']).to_dict()

        # Sophistication vs investigation success
        sophistication_success = df.groupby('sophistication_level')['outcome_code'].value_counts(normalize=True).to_dict()

        return {
            'overall_distribution': sophistication_dist,
            'by_crime_type': sophistication_by_crime,
            'financial_impact_correlation': sophistication_impact,
            'investigation_success_rates': sophistication_success,
            'trend_analysis': self._calculate_sophistication_trends(df)
        }

    def _calculate_sophistication_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate sophistication trends over time"""
        df['year'] = pd.to_datetime(df['crime_date']).dt.year

        sophistication_scores = {'low': 1, 'medium': 2, 'high': 3, 'advanced': 4, 'organized': 5}
        yearly_scores = []

        for year in sorted(df['year'].unique()):
            year_data = df[df['year'] == year]
            year_scores = [sophistication_scores[level] for level in year_data['sophistication_level']]
            yearly_scores.append({
                'year': year,
                'average_score': np.mean(year_scores),
                'median_score': np.median(year_scores),
                'case_count': len(year_scores)
            })

        # Calculate trend
        if len(yearly_scores) >= 2:
            scores = [ys['average_score'] for ys in yearly_scores]
            trend_coefficient = np.polyfit(range(len(scores)), scores, 1)[0]
            trend_direction = 'increasing' if trend_coefficient > 0.05 else 'decreasing' if trend_coefficient < -0.05 else 'stable'
        else:
            trend_direction = 'insufficient_data'

        return {
            'yearly_breakdown': yearly_scores,
            'overall_trend': trend_direction,
            'sophistication_growth_rate': float(trend_coefficient) if len(yearly_scores) >= 2 else 0
        }

    async def _analyze_cross_jurisdictional_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze cross-jurisdictional crime patterns"""
        cross_jurisdictional = df[df['jurisdiction_code'] != df['law_enforcement_agency_code']]

        if len(cross_jurisdictional) == 0:
            return {'no_cross_jurisdictional_cases': True}

        # Analyze jurisdiction pairs
        jurisdiction_pairs = cross_jurisdictional.groupby(['jurisdiction_code', 'law_enforcement_agency_code']).size().reset_index(name='case_count')
        top_pairs = jurisdiction_pairs.nlargest(10, 'case_count')

        # Analyze characteristics of cross-jurisdictional crimes
        cross_jurisdictional_analysis = {
            'total_cases': len(cross_jurisdictional),
            'percentage_of_total': len(cross_jurisdictional) / len(df) * 100,
            'crime_types': cross_jurisdictional['crime_category'].value_counts().to_dict(),
            'sophistication_levels': cross_jurisdictional['sophistication_level'].value_counts().to_dict(),
            'average_financial_loss': float(cross_jurisdictional['financial_loss'].mean()),
            'top_jurisdiction_pairs': top_pairs.to_dict('records'),
            'success_rate': cross_jurisdictional['outcome_code'].value_counts(normalize=True).to_dict()
        }

        return cross_jurisdictional_analysis

    async def _generate_predictive_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate predictive insights based on historical patterns"""
        predictive_insights = {}

        # Predict likely next crime types based on trends
        crime_type_trends = df.groupby([df['crime_date'].dt.year, 'crime_category']).size().unstack(fill_value=0)
        if len(crime_type_trends) >= 2:
            recent_trend = crime_type_trends.iloc[-1] - crime_type_trends.iloc[-2]
            increasing_crime_types = recent_trend[recent_trend > 0].sort_values(ascending=False)

            predictive_insights['increasing_crime_types'] = increasing_crime_types.head(5).to_dict()

        # Predict high-risk locations based on historical frequency
        location_risk = df.groupby('location_cluster').agg({
            'case_id_hash': 'count',
            'financial_loss': 'sum',
            'sophistication_level': lambda x: (x == 'advanced').sum() + (x == 'organized').sum()
        }).reset_index()

        location_risk['risk_score'] = (
            location_risk['case_id_hash'] * 0.4 +
            location_risk['financial_loss'] / location_risk['financial_loss'].max() * 0.3 +
            location_risk['sophistication_level'] / location_risk['sophistication_level'].max() * 0.3
        )

        predictive_insights['high_risk_locations'] = location_risk.nlargest(10, 'risk_score')[['location_cluster', 'risk_score']].to_dict('records')

        # Predict seasonal patterns
        df['month'] = pd.to_datetime(df['crime_date']).dt.month
        seasonal_patterns = df.groupby('month').size().to_dict()
        peak_months = sorted(seasonal_patterns, key=seasonal_patterns.get, reverse=True)[:3]

        predictive_insights['seasonal_predictions'] = {
            'peak_months': peak_months,
            'low_activity_months': sorted(seasonal_patterns, key=seasonal_patterns.get)[:3],
            'monthly_distribution': seasonal_patterns
        }

        return predictive_insights

    async def _identify_significant_patterns(self, analysis_results: Dict[str, Any]) -> List[Dict]:
        """Identify significant patterns from analysis results"""
        significant_patterns = []

        # Analyze temporal patterns for significance
        temporal = analysis_results.get('temporal_patterns', {})
        if 'peak_hours' in temporal.get('hourly_patterns', {}):
            significant_patterns.append({
                'pattern_type': 'temporal',
                'pattern_name': 'Peak_Activity_Hours',
                'description': f"Peak criminal activity observed during hours: {temporal['hourly_patterns']['peak_hours']}",
                'confidence': 0.8,
                'data': temporal['hourly_patterns']
            })

        # Analyze geographic hotspots
        geographic = analysis_results.get('geographic_patterns', {})
        hotspots = geographic.get('hotspot_analysis', {})
        if 'top_hotspots' in hotspots and hotspots['top_hotspots']:
            for hotspot in hotspots['top_hotspots'][:3]:
                significant_patterns.append({
                    'pattern_type': 'geographic',
                    'pattern_name': 'Crime_Hotspot',
                    'description': f"High crime density area with {hotspot['crime_count']} incidents",
                    'confidence': min(0.9, 0.5 + hotspot['density'] / 10),
                    'data': hotspot
                })

        # Analyze MO patterns
        mo_patterns = analysis_results.get('modus_operandi_patterns', {})
        common_sequences = mo_patterns.get('common_mo_sequences', {})
        if 'most_common_sequences' in common_sequences:
            for sequence, count in list(common_sequences['most_common_sequences'].items())[:3]:
                significant_patterns.append({
                    'pattern_type': 'modus_operandi',
                    'pattern_name': 'Common_MO_Sequence',
                    'description': f"Frequently used MO combination: {sequence}",
                    'confidence': min(0.85, 0.4 + count / 50),
                    'data': {'sequence': sequence, 'frequency': count}
                })

        # Sort by confidence
        significant_patterns.sort(key=lambda x: x['confidence'], reverse=True)

        return significant_patterns

    async def _store_analysis_results(self, analysis_results: Dict[str, Any], significant_patterns: List[Dict]):
        """Store analysis results in database"""
        db = self.SessionLocal()
        try:
            # Store significant patterns
            for i, pattern in enumerate(significant_patterns):
                pattern_record = CrimePatternRecord(
                    pattern_id=f"PAT_{uuid.uuid4().hex[:12].upper()}",
                    pattern_type=pattern['pattern_type'],
                    pattern_name=pattern['pattern_name'],
                    description=pattern['description'],
                    confidence_score=pattern['confidence'],
                    pattern_signature=pattern['data'],
                    affected_cases_count=pattern['data'].get('crime_count', 0),
                    first_seen_date=datetime.utcnow() - timedelta(days=30),
                    last_seen_date=datetime.utcnow(),
                    risk_assessment={'level': 'high' if pattern['confidence'] > 0.8 else 'medium'},
                    pattern_strength=pattern['confidence']
                )
                db.add(pattern_record)

            db.commit()
            logger.info(f"Stored {len(significant_patterns)} significant patterns in database")

        except Exception as e:
            db.rollback()
            logger.error(f"Error storing analysis results: {str(e)}")
            raise
        finally:
            db.close()

    async def _cache_analysis_results(self, analysis_results: Dict[str, Any]):
        """Cache analysis results in Redis"""
        try:
            cache_key = "i4c:latest_analysis"
            cache_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_summary': {
                    'temporal_patterns': len(analysis_results.get('temporal_patterns', {})),
                    'geographic_hotspots': len(analysis_results.get('geographic_patterns', {}).get('hotspot_analysis', {}).get('top_hotspots', [])),
                    'mo_patterns': len(analysis_results.get('modus_operandi_patterns', {})),
                    'criminal_networks': analysis_results.get('criminal_network_analysis', {}).get('total_known_networks', 0),
                    'predictive_insights': len(analysis_results.get('predictive_insights', {}))
                }
            }

            self.redis_client.setex(cache_key, 3600, json.dumps(cache_data, default=str))
            logger.info("Cached latest I4C analysis results in Redis")

        except Exception as e:
            logger.warning(f"Error caching to Redis: {str(e)}")

    async def get_analysis_dashboard_data(self) -> Dict[str, Any]:
        """Get data for analysis dashboard"""
        db = self.SessionLocal()
        try:
            # Get recent statistics
            now = datetime.utcnow()
            week_ago = now - timedelta(weeks=1)
            month_ago = now - timedelta(weeks=4)

            # Record counts
            recent_records = db.query(HistoricalCrimeData).filter(
                HistoricalCrimeData.crime_date >= week_ago
            ).count()

            monthly_records = db.query(HistoricalCrimeData).filter(
                HistoricalCrimeData.crime_date >= month_ago
            ).count()

            # Pattern counts
            recent_patterns = db.query(CrimePatternRecord).filter(
                CrimePatternRecord.last_seen_date >= week_ago
            ).count()

            active_patterns = db.query(CrimePatternRecord).filter(
                CrimePatternRecord.is_active == True
            ).count()

            # Get top crime categories
            top_crimes = db.query(
                HistoricalCrimeData.crime_category,
                db.func.count(HistoricalCrimeData.id)
            ).filter(
                HistoricalCrimeData.crime_date >= month_ago
            ).group_by(HistoricalCrimeData.crime_category).order_by(
                db.func.count(HistoricalCrimeData.id).desc()
            ).limit(5).all()

            # Get sophistication trends
            sophistication_trends = db.query(
                HistoricalCrimeData.sophistication_level,
                db.func.count(HistoricalCrimeData.id)
            ).filter(
                HistoricalCrimeData.crime_date >= month_ago
            ).group_by(HistoricalCrimeData.sophistication_level).all()

            return {
                'analysis_status': 'active',
                'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                'total_records_analyzed': self.total_records_analyzed,
                'total_patterns_identified': self.total_patterns_identified,
                'recent_activity': {
                    'records_last_week': recent_records,
                    'records_last_month': monthly_records,
                    'patterns_last_week': recent_patterns,
                    'active_patterns_total': active_patterns
                },
                'top_crime_categories': [
                    {'category': category, 'count': count} for category, count in top_crimes
                ],
                'sophistication_distribution': [
                    {'level': level, 'count': count} for level, count in sophistication_trends
                ],
                'system_health': {
                    'pattern_analyzer_ready': True,
                    'database_connected': True,
                    'redis_connected': self.redis_client.ping(),
                    'analysis_uptime_hours': (datetime.utcnow() - (self.last_analysis_time or datetime.utcnow())).total_seconds() / 3600
                }
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {'error': str(e)}
        finally:
            db.close()

    async def start_continuous_analysis(self):
        """Start continuous historical data analysis"""
        logger.info("Starting continuous I4C historical data analysis")

        while True:
            try:
                # Calculate time range for analysis
                end_time = datetime.utcnow()
                start_time = self.last_analysis_time or (end_time - timedelta(days=30))

                # Fetch and analyze historical data
                crime_records = await self.fetch_historical_crime_data(start_time, end_time)

                if crime_records:
                    analysis_results = await self.analyze_historical_patterns(crime_records)

                    # Log analysis results
                    logger.info(f"Continuous analysis completed: {analysis_results['analysis_summary']}")

                # Update last analysis time
                self.last_analysis_time = end_time

                # Wait for next analysis cycle
                await asyncio.sleep(self.analysis_interval)

            except Exception as e:
                logger.error(f"Error in continuous analysis: {str(e)}")
                await asyncio.sleep(300)  # 5 minute retry interval

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up I4C Integration Service")

        if self.session:
            await self.session.close()

        if self.redis_client:
            self.redis_client.close()

        logger.info("I4C Integration Service cleanup completed")

# Configuration and initialization
async def create_i4c_service(config: Dict[str, Any]) -> I4CIntegrationService:
    """Create and initialize I4C integration service"""
    service = I4CIntegrationService(config)
    await service.initialize()
    return service

# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'i4c_base_url': 'https://api.i4c.gov.in/v1',
        'i4c_api_key': 'your-api-key-here',
        'database_url': 'sqlite:///aegis_i4c.db',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'batch_size': 1000,
        'analysis_interval': 3600,
        'pattern_confidence_threshold': 0.7
    }

    async def main():
        # Create and start service
        service = await create_i4c_service(config)

        try:
            # Start continuous analysis
            await service.start_continuous_analysis()
        except KeyboardInterrupt:
            logger.info("Shutting down I4C Integration Service")
        finally:
            await service.cleanup()

    # Run the service
    asyncio.run(main())