"""
Real-Time GIS with WebSocket Updates
Advanced geospatial processing with real-time data streaming
"""

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import aiohttp
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
import numpy as np

logger = logging.getLogger(__name__)

class GISDataType(Enum):
    """GIS data types"""
    COMPLAINTS = "complaints"
    TRANSACTIONS = "transactions"
    HOTSPOTS = "hotspots"
    RISK_ZONES = "risk_zones"
    PREDICTIONS = "predictions"
    CORDONS = "cordons"

class HeatmapIntensity(Enum):
    """Heatmap intensity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4
    CRITICAL = 5

@dataclass
class GeoPoint:
    """Geographic point with attributes"""
    lat: float
    lon: float
    data_type: GISDataType
    value: float
    intensity: HeatmapIntensity
    timestamp: datetime
    metadata: Dict[str, Any] = None
    id: str = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.id is None:
            self.id = f"geo_{self.timestamp.strftime('%Y%m%d_%H%M%S')}_{hash(str(self.lat) + str(self.lon)) % 10000:04d}"

@dataclass
class GeoCluster:
    """Geographic cluster of points"""
    cluster_id: str
    center_lat: float
    center_lon: float
    radius_km: float
    point_count: int
    intensity: HeatmapIntensity
    data_points: List[GeoPoint]
    created_at: datetime

@dataclass
class RealTimeGISUpdate:
    """Real-time GIS update payload"""
    update_id: str
    timestamp: datetime
    data_type: GISDataType
    points: List[GeoPoint]
    clusters: List[GeoCluster]
    heatmap_data: Dict[str, Any]
    bounding_box: Dict[str, float]

class RealTimeGIS:
    """
    Real-time GIS system with WebSocket support
    """

    def __init__(self):
        self.websocket_connections = set()
        self.active_hotspots = {}
        self.heatmaps = {}
        self.geo_clusters = {}
        self.spatial_index = {}  # Simple spatial index
        self.update_interval = 30  # seconds
        self.is_running = False

        # GIS configuration
        self.map_config = {
            'default_center': {'lat': 28.6139, 'lon': 77.2090},  # Delhi
            'default_zoom': 10,
            'max_zoom': 18,
            'min_zoom': 3,
            'update_radius': 50,  # km
            'cluster_radius': 2.0,  # km
            'intensity_decay': 0.95  # Decay factor per update
        }

        # WebSocket server
        self.websocket_port = 8765
        self.websocket_host = '0.0.0.0'

    async def initialize(self) -> bool:
        """Initialize real-time GIS system"""
        try:
            logger.info("[Real-Time GIS] Initializing real-time GIS system...")

            # Initialize spatial index
            await self._initialize_spatial_index()

            # Load existing data
            await self._load_existing_data()

            # Start WebSocket server
            await self._start_websocket_server()

            # Start update loop
            await self._start_update_loop()

            self.is_running = True
            logger.info("[Real-Time GIS] Real-time GIS system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error initializing GIS system: {str(e)}")
            return False

    async def _initialize_spatial_index(self) -> None:
        """Initialize spatial indexing for efficient queries"""
        try:
            # Create grid-based spatial index
            grid_size = 0.01  # ~1km grid
            lat_range = (6.0, 38.0)  # India lat range
            lon_range = (68.0, 98.0)  # India lon range

            lat_steps = int((lat_range[1] - lat_range[0]) / grid_size)
            lon_steps = int((lon_range[1] - lon_range[0]) / grid_size)

            self.spatial_index = {
                'grid_size': grid_size,
                'lat_range': lat_range,
                'lon_range': lon_range,
                'lat_steps': lat_steps,
                'lon_steps': lon_steps,
                'grid': {}  # Will be populated as needed
            }

            logger.info(f"[Real-Time GIS] Spatial index initialized: {lat_steps}x{lon_steps} grid")

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error initializing spatial index: {str(e)}")

    async def _load_existing_data(self) -> None:
        """Load existing data from database"""
        try:
            with SessionLocal() as db:
                # Load recent complaints
                complaints_result = db.execute(text("""
                    SELECT complaint_id, amount, ST_Y(victim_location) as lat,
                           ST_X(victim_location) as lon, scam_type,
                           created_at as timestamp
                    FROM ncrp_complaints
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    AND victim_location IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 1000
                """)).fetchall()

                for row in complaints_result:
                    if row.lat and row.lon:
                        point = GeoPoint(
                            lat=float(row.lat),
                            lon=float(row.lon),
                            data_type=GISDataType.COMPLAINTS,
                            value=float(row.amount),
                            intensity=self._calculate_intensity(float(row.amount), 'amount'),
                            timestamp=row.timestamp,
                            metadata={
                                'complaint_id': row.complaint_id,
                                'scam_type': row.scam_type
                            }
                        )
                        await self._add_point_to_index(point)

                # Load suspicious transactions
                transactions_result = db.execute(text("""
                    SELECT transaction_id, amount, risk_score,
                           ST_Y(location) as lat, ST_X(location) as lon,
                           transaction_type, timestamp
                    FROM bank_transactions
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    AND is_suspicious = true
                    AND location IS NOT NULL
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """)).fetchall()

                for row in transactions_result:
                    if row.lat and row.lon:
                        point = GeoPoint(
                            lat=float(row.lat),
                            lon=float(row.lon),
                            data_type=GISDataType.TRANSACTIONS,
                            value=float(row.risk_score),
                            intensity=self._calculate_intensity(float(row.risk_score), 'risk_score'),
                            timestamp=row.timestamp,
                            metadata={
                                'transaction_id': row.transaction_id,
                                'transaction_type': row.transaction_type,
                                'amount': float(row.amount)
                            }
                        )
                        await self._add_point_to_index(point)

                logger.info(f"[Real-Time GIS] Loaded {len(complaints_result) + len(transactions_result)} existing data points")

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error loading existing data: {str(e)}")

    def _calculate_intensity(self, value: float, value_type: str) -> HeatmapIntensity:
        """Calculate intensity based on value and type"""
        try:
            if value_type == 'amount':
                if value < 1000:
                    return HeatmapIntensity.LOW
                elif value < 10000:
                    return HeatmapIntensity.MEDIUM
                elif value < 50000:
                    return HeatmapIntensity.HIGH
                elif value < 100000:
                    return HeatmapIntensity.VERY_HIGH
                else:
                    return HeatmapIntensity.CRITICAL

            elif value_type == 'risk_score':
                if value < 0.3:
                    return HeatmapIntensity.LOW
                elif value < 0.5:
                    return HeatmapIntensity.MEDIUM
                elif value < 0.7:
                    return HeatmapIntensity.HIGH
                elif value < 0.9:
                    return HeatmapIntensity.VERY_HIGH
                else:
                    return HeatmapIntensity.CRITICAL

            else:
                # Default calculation
                if value < 0.2:
                    return HeatmapIntensity.LOW
                elif value < 0.4:
                    return HeatmapIntensity.MEDIUM
                elif value < 0.6:
                    return HeatmapIntensity.HIGH
                elif value < 0.8:
                    return HeatmapIntensity.VERY_HIGH
                else:
                    return HeatmapIntensity.CRITICAL

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error calculating intensity: {str(e)}")
            return HeatmapIntensity.MEDIUM

    async def _add_point_to_index(self, point: GeoPoint) -> None:
        """Add point to spatial index"""
        try:
            grid_key = self._get_grid_key(point.lat, point.lon)

            if grid_key not in self.spatial_index['grid']:
                self.spatial_index['grid'][grid_key] = []

            self.spatial_index['grid'][grid_key].append(point)

            # Limit grid size to prevent memory issues
            if len(self.spatial_index['grid'][grid_key]) > 100:
                self.spatial_index['grid'][grid_key] = self.spatial_index['grid'][grid_key][-50:]

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error adding point to index: {str(e)}")

    def _get_grid_key(self, lat: float, lon: float) -> str:
        """Get grid key for coordinates"""
        try:
            lat_step = int((lat - self.spatial_index['lat_range'][0]) / self.spatial_index['grid_size'])
            lon_step = int((lon - self.spatial_index['lon_range'][0]) / self.spatial_index['grid_size'])
            return f"{lat_step}_{lon_step}"
        except Exception as e:
            logger.error(f"[Real-Time GIS] Error getting grid key: {str(e)}")
            return "0_0"

    async def _start_websocket_server(self) -> None:
        """Start WebSocket server for real-time updates"""
        try:
            logger.info(f"[Real-Time GIS] Starting WebSocket server on {self.websocket_host}:{self.websocket_port}")

            async def handle_websocket(websocket, path):
                """Handle WebSocket connection"""
                logger.info(f"[Real-Time GIS] WebSocket client connected from {websocket.remote_address}")

                try:
                    # Add to connections
                    self.websocket_connections.add(websocket)

                    # Send initial data
                    initial_data = await self.get_current_gis_data()
                    await websocket.send(json.dumps(initial_data))

                    # Keep connection alive and send updates
                    try:
                        async for message in websocket:
                            # Handle client messages (ping, subscribe, etc.)
                            await self._handle_client_message(websocket, message)
                    except websockets.exceptions.ConnectionClosed:
                        pass

                except Exception as e:
                    logger.error(f"[Real-Time GIS] WebSocket error: {str(e)}")
                finally:
                    self.websocket_connections.discard(websocket)
                    logger.info("[Real-Time GIS] WebSocket client disconnected")

            # Start WebSocket server
            server = await websockets.serve(
                handle_websocket,
                self.websocket_host,
                self.websocket_port
            )

            logger.info(f"[Real-Time GIS] WebSocket server started successfully")

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error starting WebSocket server: {str(e)}")

    async def _handle_client_message(self, websocket, message: str) -> None:
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)

            if data.get('type') == 'ping':
                await websocket.send(json.dumps({'type': 'pong', 'timestamp': datetime.utcnow().isoformat()}))

            elif data.get('type') == 'subscribe':
                # Subscribe to specific data types
                await websocket.send(json.dumps({
                    'type': 'subscription_confirmed',
                    'subscribed_to': data.get('data_types', 'all'),
                    'timestamp': datetime.utcnow().isoformat()
                }))

            elif data.get('type') == 'get_heatmap':
                heatmap_data = await self.get_heatmap_data(
                    center=data.get('center', self.map_config['default_center']),
                    radius_km=data.get('radius', 10),
                    grid_size=data.get('grid_size', 50)
                )
                await websocket.send(json.dumps({
                    'type': 'heatmap_data',
                    'data': heatmap_data,
                    'timestamp': datetime.utcnow().isoformat()
                }))

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error handling client message: {str(e)}")

    async def _start_update_loop(self) -> None:
        """Start the main update loop"""
        try:
            logger.info("[Real-Time GIS] Starting update loop")

            while self.is_running:
                try:
                    # Update hotspots
                    await self._update_hotspots()

                    # Update heatmaps
                    await self._update_heatmaps()

                    # Update clusters
                    await self._update_clusters()

                    # Broadcast updates to WebSocket clients
                    await self._broadcast_updates()

                    # Wait for next update
                    await asyncio.sleep(self.update_interval)

                except Exception as e:
                    logger.error(f"[Real-Time GIS] Error in update loop: {str(e)}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"[Real-Time GIS] Fatal error in update loop: {str(e)}")

    async def _update_hotspots(self) -> None:
        """Update active hotspots"""
        try:
            current_time = datetime.utcnow()
            decay_factor = self.map_config['intensity_decay']

            # Get all points from spatial index
            all_points = []
            for grid_points in self.spatial_index['grid'].values():
                for point in grid_points:
                    # Apply time-based decay
                    time_diff = (current_time - point.timestamp).total_seconds() / 3600  # hours
                    if time_diff < 24:  # Only consider points from last 24 hours
                        decayed_intensity = point.intensity.value * (decay_factor ** time_diff)

                        if decayed_intensity > 0.1:  # Only keep significant points
                            point.metadata['decayed_intensity'] = decayed_intensity
                            all_points.append(point)

            # Cluster points into hotspots
            clusters = await self._cluster_points(all_points)

            # Update active hotspots
            self.active_hotspots = {}
            for cluster in clusters:
                if cluster.point_count >= 3:  # Minimum 3 points for hotspot
                    hotspot_id = f"hotspot_{cluster.cluster_id}"
                    self.active_hotspots[hotspot_id] = cluster

            logger.debug(f"[Real-Time GIS] Updated {len(self.active_hotspots)} active hotspots")

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error updating hotspots: {str(e)}")

    async def _cluster_points(self, points: List[GeoPoint], max_radius_km: float = 2.0) -> List[GeoCluster]:
        """Cluster points using simple grid-based clustering"""
        try:
            if not points:
                return []

            clusters = []
            used_points = set()

            for point in points:
                if point.id in used_points:
                    continue

                # Find nearby points
                nearby_points = [point]
                used_points.add(point.id)

                for other_point in points:
                    if other_point.id not in used_points:
                        distance = self._calculate_distance(point, other_point)
                        if distance <= max_radius_km:
                            nearby_points.append(other_point)
                            used_points.add(other_point.id)

                # Calculate cluster properties
                avg_lat = sum(p.lat for p in nearby_points) / len(nearby_points)
                avg_lon = sum(p.lon for p in nearby_points) / len(nearby_points)

                # Calculate radius as maximum distance from center
                max_distance = 0
                total_intensity = 0
                for p in nearby_points:
                    distance = self._calculate_distance(
                        {'lat': avg_lat, 'lon': avg_lon},
                        {'lat': p.lat, 'lon': p.lon}
                    )
                    max_distance = max(max_distance, distance)
                    total_intensity += p.intensity.value

                avg_intensity = total_intensity / len(nearby_points)
                intensity = HeatmapIntensity(min(5, max(1, int(avg_intensity))))

                cluster = GeoCluster(
                    cluster_id=secrets.token_hex(4),
                    center_lat=avg_lat,
                    center_lon=avg_lon,
                    radius_km=max_distance,
                    point_count=len(nearby_points),
                    intensity=intensity,
                    data_points=nearby_points,
                    created_at=datetime.utcnow()
                )

                clusters.append(cluster)

            return clusters

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error clustering points: {str(e)}")
            return []

    def _calculate_distance(self, point1: Dict[str, float], point2: Dict[str, float]) -> float:
        """Calculate distance between two points in kilometers"""
        try:
            from math import radians, cos, sin, asin, sqrt

            lat1, lon1 = radians(point1['lat']), radians(point1['lon'])
            lat2, lon2 = radians(point2['lat']), radians(point2['lon'])

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Earth's radius in kilometers

            return c * r

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error calculating distance: {str(e)}")
            return 0

    async def _update_heatmaps(self) -> None:
        """Update heatmap data"""
        try:
            center = self.map_config['default_center']
            radius = 50  # 50km radius

            heatmap_data = await self.get_heatmap_data(center, radius, 30)
            self.heatmaps['main'] = heatmap_data

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error updating heatmaps: {str(e)}")

    async def _update_clusters(self) -> None:
        """Update cluster data"""
        try:
            self.geo_clusters = {hotspot_id: cluster for hotspot_id, cluster in self.active_hotspots.items()}
        except Exception as e:
            logger.error(f"[Real-Time GIS] Error updating clusters: {str(e)}")

    async def _broadcast_updates(self) -> None:
        """Broadcast updates to all WebSocket clients"""
        try:
            if not self.websocket_connections:
                return

            update_data = await self._create_update_payload()

            # Send to all connected clients
            disconnected_clients = set()

            for websocket in self.websocket_connections:
                try:
                    await websocket.send(json.dumps(update_data))
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(websocket)
                except Exception as e:
                    logger.error(f"[Real-Time GIS] Error broadcasting to client: {str(e)}")
                    disconnected_clients.add(websocket)

            # Remove disconnected clients
            for client in disconnected_clients:
                self.websocket_connections.discard(client)

            if disconnected_clients:
                logger.info(f"[Real-Time GIS] Removed {len(disconnected_clients)} disconnected clients")

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error broadcasting updates: {str(e)}")

    async def _create_update_payload(self) -> Dict[str, Any]:
        """Create update payload for WebSocket clients"""
        try:
            update_data = {
                'type': 'gis_update',
                'timestamp': datetime.utcnow().isoformat(),
                'hotspots': [],
                'heatmaps': {},
                'clusters': [],
                'statistics': {
                    'active_connections': len(self.websocket_connections),
                    'active_hotspots': len(self.active_hotspots),
                    'total_points': sum(len(points) for points in self.spatial_index['grid'].values()),
                    'last_update': datetime.utcnow().isoformat()
                }
            }

            # Add hotspots
            for hotspot_id, cluster in self.active_hotspots.items():
                update_data['hotspots'].append({
                    'id': hotspot_id,
                    'lat': cluster.center_lat,
                    'lon': cluster.center_lon,
                    'radius': cluster.radius_km,
                    'intensity': cluster.intensity.value,
                    'point_count': cluster.point_count,
                    'created_at': cluster.created_at.isoformat()
                })

            # Add heatmaps
            update_data['heatmaps'] = self.heatmaps

            # Add clusters
            for cluster_id, cluster in self.geo_clusters.items():
                update_data['clusters'].append({
                    'id': cluster.cluster_id,
                    'lat': cluster.center_lat,
                    'lon': cluster.center_lon,
                    'radius': cluster.radius_km,
                    'intensity': cluster.intensity.value,
                    'point_count': cluster.point_count
                })

            return update_data

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error creating update payload: {str(e)}")
            return {'type': 'error', 'error': str(e)}

    async def add_geo_point(self, point_data: Dict[str, Any]) -> str:
        """Add a new geo point and trigger updates"""
        try:
            point = GeoPoint(
                lat=point_data['lat'],
                lon=point_data['lon'],
                data_type=GISDataType(point_data.get('data_type', 'complaints')),
                value=float(point_data.get('value', 1.0)),
                intensity=self._calculate_intensity(float(point_data.get('value', 1.0)), point_data.get('value_type', 'amount')),
                timestamp=datetime.utcnow(),
                metadata=point_data.get('metadata', {})
            )

            # Add to spatial index
            await self._add_point_to_index(point)

            # Trigger immediate update for critical points
            if point.intensity in [HeatmapIntensity.CRITICAL, HeatmapIntensity.VERY_HIGH]:
                await self._broadcast_updates()

            logger.debug(f"[Real-Time GIS] Added geo point {point.id} with intensity {point.intensity.value}")
            return point.id

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error adding geo point: {str(e)}")
            return ""

    async def get_heatmap_data(self, center: Dict[str, float], radius_km: float, grid_size: int) -> Dict[str, Any]:
        """Generate heatmap data for the specified area"""
        try:
            heatmap = {
                'center': center,
                'radius_km': radius_km,
                'grid_size': grid_size,
                'grid': np.zeros((grid_size, grid_size)),
                'metadata': {
                    'cell_size_km': (radius_km * 2) / grid_size,
                    'max_intensity': 0,
                    'total_points': 0
                }
            }

            # Calculate grid bounds
            lat_range = radius_km / 111.0  # Approximate km per degree latitude
            lon_range = radius_km / (111.0 * math.cos(math.radians(center['lat'])))  # Adjust for longitude

            min_lat = center['lat'] - lat_range
            max_lat = center['lat'] + lat_range
            min_lon = center['lon'] - lon_range
            max_lon = center['lon'] + lon_range

            lat_step = (max_lat - min_lat) / grid_size
            lon_step = (max_lon - min_lon) / grid_size

            # Process all points in the area
            for grid_points in self.spatial_index['grid'].values():
                for point in grid_points:
                    if (min_lat <= point.lat <= max_lat and
                        min_lon <= point.lon <= max_lon):
                        # Find grid cell
                        lat_index = int((point.lat - min_lat) / lat_step)
                        lon_index = int((point.lon - min_lon) / lon_step)

                        if 0 <= lat_index < grid_size and 0 <= lon_index < grid_size:
                            intensity_value = point.intensity.value

                            # Apply decay if needed
                            if 'decayed_intensity' in point.metadata:
                                intensity_value = point.metadata['decayed_intensity']

                            heatmap['grid'][lat_index][lon_index] += intensity_value
                            heatmap['metadata']['max_intensity'] = max(
                                heatmap['metadata']['max_intensity'], intensity_value
                            )
                            heatmap['metadata']['total_points'] += 1

            # Normalize grid
            if heatmap['metadata']['max_intensity'] > 0:
                heatmap['grid'] = heatmap['grid'] / heatmap['metadata']['max_intensity']

            # Convert grid to list for JSON serialization
            heatmap['grid_data'] = heatmap['grid'].tolist()
            heatmap['bounds'] = {
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lon': min_lon,
                'max_lon': max_lon
            }

            return heatmap

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error generating heatmap data: {str(e)}")
            return {}

    async def get_current_gis_data(self) -> Dict[str, Any]:
        """Get current GIS data"""
        try:
            return {
                'type': 'current_data',
                'timestamp': datetime.utcnow().isoformat(),
                'hotspots': [
                    {
                        'id': hotspot_id,
                        'lat': cluster.center_lat,
                        'lon': cluster.center_lon,
                        'radius': cluster.radius_km,
                        'intensity': cluster.intensity.value,
                        'point_count': cluster.point_count
                    }
                    for hotspot_id, cluster in self.active_hotspots.items()
                ],
                'clusters': [
                    {
                        'id': cluster.cluster_id,
                        'lat': cluster.center_lat,
                        'lon': cluster.center_lon,
                        'radius': cluster.radius_km,
                        'intensity': cluster.intensity.value,
                        'point_count': cluster.point_count
                    }
                    for cluster in self.geo_clusters.values()
                ],
                'total_points': sum(len(points) for points in self.spatial_index['grid'].values()),
                'active_connections': len(self.websocket_connections)
            }

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error getting current GIS data: {str(e)}")
            return {'error': str(e)}

    async def search_nearby_points(self, lat: float, lon: float, radius_km: float,
                                  data_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for points near a location"""
        try:
            nearby_points = []
            search_radius = radius_km

            # Search in surrounding grid cells
            grid_key = self._get_grid_key(lat, lon)
            base_lat_step = int((lat - self.spatial_index['lat_range'][0]) / self.spatial_index['grid_size'])
            base_lon_step = int((lon - self.spatial_index['lon_range'][0]) / self.spatial_index['grid_size'])

            # Check surrounding grids (3x3)
            for lat_offset in [-1, 0, 1]:
                for lon_offset in [-1, 0, 1]:
                    search_grid_key = f"{base_lat_step + lat_offset}_{base_lon_step + lon_offset}"

                    if search_grid_key in self.spatial_index['grid']:
                        for point in self.spatial_index['grid'][search_grid_key]:
                            if data_type is None or point.data_type.value == data_type:
                                distance = self._calculate_distance(
                                    {'lat': lat, 'lon': lon},
                                    {'lat': point.lat, 'lon': point.lon}
                                )

                                if distance <= search_radius:
                                    nearby_points.append({
                                        'id': point.id,
                                        'lat': point.lat,
                                        'lon': point.lon,
                                        'data_type': point.data_type.value,
                                        'value': point.value,
                                        'intensity': point.intensity.value,
                                        'timestamp': point.timestamp.isoformat(),
                                        'distance_km': distance,
                                        'metadata': point.metadata
                                    })

            # Sort by distance and limit results
            nearby_points.sort(key=lambda x: x['distance_km'])
            return nearby_points[:limit]

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error searching nearby points: {str(e)}")
            return []

    async def get_gis_statistics(self) -> Dict[str, Any]:
        """Get GIS statistics"""
        try:
            total_points = sum(len(points) for points in self.spatial_index['grid'].values())

            intensity_distribution = {
                'low': 0,
                'medium': 0,
                'high': 0,
                'very_high': 0,
                'critical': 0
            }

            for grid_points in self.spatial_index['grid'].values():
                for point in grid_points:
                    intensity_distribution[point.intensity.name.lower()] += 1

            return {
                'total_points': total_points,
                'active_hotspots': len(self.active_hotspots),
                'active_clusters': len(self.geo_clusters),
                'websocket_connections': len(self.websocket_connections),
                'intensity_distribution': intensity_distribution,
                'grid_cells': len(self.spatial_index['grid']),
                'last_update': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error getting GIS statistics: {str(e)}")
            return {'error': str(e)}

    async def cleanup_old_data(self, hours_back: int = 24) -> int:
        """Clean up old data points"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            removed_count = 0

            # Clean up spatial index
            for grid_key, grid_points in self.spatial_index['grid'].items():
                original_count = len(grid_points)
                # Keep only recent points
                grid_points[:] = [p for p in grid_points if p.timestamp >= cutoff_time]
                removed_count += original_count - len(grid_points)

            # Clean up expired hotspots
            expired_hotspots = [
                hotspot_id for hotspot_id, hotspot in self.active_hotspots.items()
                if hotspot.created_at < cutoff_time
            ]

            for hotspot_id in expired_hotspots:
                del self.active_hotspots[hotspot_id]

            logger.info(f"[Real-Time GIS] Cleaned up {removed_count} old points and {len(expired_hotspots)} expired hotspots")
            return removed_count

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error cleaning up old data: {str(e)}")
            return 0

    async def stop(self) -> None:
        """Stop the real-time GIS system"""
        try:
            logger.info("[Real-Time GIS] Stopping real-time GIS system...")
            self.is_running = False

            # Close WebSocket connections
            for websocket in self.websocket_connections:
                try:
                    await websocket.close()
                except:
                    pass

            self.websocket_connections.clear()
            logger.info("[Real-Time GIS] Real-time GIS system stopped")

        except Exception as e:
            logger.error(f"[Real-Time GIS] Error stopping system: {str(e)}")

# Global real-time GIS instance
real_time_gis = RealTimeGIS()