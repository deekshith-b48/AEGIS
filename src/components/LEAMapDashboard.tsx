/**
 * Project AEGIS Greenfield LEA Map Dashboard
 * MapLibre GL + Deck.gl implementation with open tiles
 * Blue dots: complaints (last 2 hours)
 * Pulsing red circles: hotspots (Deck.gl ScatterplotLayer)
 * Yellow circles: digital cordons (GeoJSON polygons)
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Map, { MapRef, NavigationControl, ScaleControl } from 'react-map-gl/maplibre';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { GeoJsonLayer } from '@deck.gl/layers';
import { MapView } from '@deck.gl/core';
import { getRiskHeatmap, submitFeedback, activateCordon } from '@/lib/greenfield_api';
import { GreenfieldRiskHeatmapResponse } from '@/lib/greenfield_api';
import { formatDistanceToNow } from 'date-fns';
import {
  MapPin,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Shield,
  Clock,
  RefreshCw,
  Activity,
  TrendingUp
} from 'lucide-react';

interface HotspotDetail {
  hotspot: any;
  timeLeft: number;
}

export default function LEAMapDashboard() {
  const mapRef = useRef<MapRef>(null);
  const [data, setData] = useState<GreenfieldRiskHeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotDetail | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [mapLoaded, setMapLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial view - centered on India
  const INITIAL_VIEW_STATE = {
    longitude: 77.2090,
    latitude: 28.6139,
    zoom: 5,
    pitch: 0,
    bearing: 0
  };

  // MapLibre GL configuration with open tiles
  const MAP_STYLE = 'https://tiles.stadiamaps.com/styles/osm_bright/style.json';

  // Fetch data from API
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getRiskHeatmap();
      setData(result);
      setLastUpdated(new Date());
      console.log('[LEA DASHBOARD] Data loaded:', {
        complaints: result.complaints.length,
        hotspots: result.hotspots.length,
        cordons: result.cordons.length,
        accuracy: result.system_metrics.system_accuracy
      });
    } catch (err) {
      console.error('[LEA DASHBOARD] Failed to fetch data:', err);
      setError('Failed to load intelligence data');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Set up polling for real-time updates (30 seconds)
  useEffect(() => {
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Calculate time remaining for hotspots
  const getTimeRemaining = (predictedAt: string, timeWindowMins: number) => {
    const predicted = new Date(predictedAt);
    const expiry = new Date(predicted.getTime() + timeWindowMins * 60000);
    const now = new Date();
    const remaining = Math.max(0, Math.floor((expiry.getTime() - now.getTime()) / 60000));
    return remaining;
  };

  // Handle hotspot selection
  const handleHotspotClick = useCallback((info: any) => {
    if (info.object) {
      const hotspot = info.object;
      const timeLeft = getTimeRemaining(hotspot.predicted_at, hotspot.time_window_mins);
      setSelectedHotspot({ hotspot, timeLeft });
    }
  }, []);

  // Handle LEA actions
  const handleMarkAsInterdicted = async (hotspotId: string) => {
    try {
      await submitFeedback({ hotspot_id: hotspotId, outcome: 'confirmed' });
      await fetchData(); // Refresh data
      setSelectedHotspot(null);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleMarkAsFalse = async (hotspotId: string) => {
    try {
      await submitFeedback({ hotspot_id: hotspotId, outcome: 'false' });
      await fetchData(); // Refresh data
      setSelectedHotspot(null);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleActivateCordon = async (hotspotId: string) => {
    try {
      await activateCordon({ hotspot_id: hotspotId });
      await fetchData(); // Refresh data
      setSelectedHotspot(null);
    } catch (error) {
      console.error('Failed to activate cordon:', error);
    }
  };

  // Deck.gl layers
  const layers = [];

  if (data) {
    // Complaints layer - blue dots
    if (data.complaints.length > 0) {
      layers.push(
        new ScatterplotLayer({
          id: 'complaints',
          data: data.complaints.filter(c => c.geometry && c.geometry.coordinates),
          getPosition: (d: any) => d.geometry.coordinates,
          getRadius: 8,
          getFillColor: [59, 130, 246, 200], // Blue with transparency
          stroked: true,
          getLineColor: [59, 130, 246],
          getLineWidth: 2,
          pickable: false,
          autoHighlight: false
        })
      );
    }

    // Hotspots layer - pulsing red circles
    if (data.hotspots.length > 0) {
      layers.push(
        new ScatterplotLayer({
          id: 'hotspots',
          data: data.hotspots.filter(h => h.geometry && h.geometry.coordinates),
          getPosition: (d: any) => d.geometry.coordinates,
          getRadius: 30, // Base radius for hotspots
          getFillColor: [220, 38, 38, 180], // Red with transparency
          stroked: true,
          getLineColor: [220, 38, 38],
          getLineWidth: 3,
          pickable: true,
          autoHighlight: true,
          onClick: handleHotspotClick,
          // Add pulsing effect via animation
          getElevation: (d: any) => {
            const timeLeft = getTimeRemaining(d.predicted_at, d.time_window_mins);
            return timeLeft > 0 ? 100 : 0;
          }
        })
      );
    }

    // Cordons layer - yellow filled circles
    if (data.cordons.length > 0) {
      layers.push(
        new GeoJsonLayer({
          id: 'cordons',
          data: {
            type: 'FeatureCollection',
            features: data.cordons.map((cordon: any) => ({
              type: 'Feature',
              geometry: cordon.geometry,
              properties: cordon
            }))
          },
          getFillColor: [250, 204, 21, 100], // Yellow with transparency
          getLineColor: [250, 204, 21],
          getLineWidth: 2,
          pickable: false,
          autoHighlight: false
        })
      );
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">LEA Dashboard</h1>
            <p className="text-sm text-gray-600">Real-time scam threat intelligence</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-sm text-gray-500">Last Updated</p>
              <p className="text-sm font-medium">{lastUpdated.toLocaleTimeString()}</p>
            </div>
            <button
              onClick={fetchData}
              disabled={loading}
              className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* System Metrics */}
        {data && (
          <div className="grid grid-cols-4 gap-4 mt-4">
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
              <div className="flex items-center">
                <MapPin className="h-5 w-5 text-blue-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Active Complaints</p>
                  <p className="text-lg font-bold text-blue-600">{data.system_metrics.active_complaints}</p>
                </div>
              </div>
            </div>
            <div className="bg-red-50 p-3 rounded-lg border border-red-200">
              <div className="flex items-center">
                <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Active Hotspots</p>
                  <p className="text-lg font-bold text-red-600">{data.system_metrics.active_hotspots}</p>
                </div>
              </div>
            </div>
            <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
              <div className="flex items-center">
                <Shield className="h-5 w-5 text-yellow-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Digital Cordons</p>
                  <p className="text-lg font-bold text-yellow-600">{data.system_metrics.active_cordons}</p>
                </div>
              </div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg border border-green-200">
              <div className="flex items-center">
                <TrendingUp className="h-5 w-5 text-green-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">System Accuracy</p>
                  <p className="text-lg font-bold text-green-600">
                    {(data.system_metrics.system_accuracy * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Map Container */}
      <div className="flex-1 relative">
        {error && (
          <div className="absolute top-4 left-4 z-10 bg-red-50 border border-red-200 rounded-lg p-4 max-w-sm">
            <div className="flex items-center">
              <XCircle className="h-5 w-5 text-red-600 mr-2" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute top-4 right-4 z-10 bg-white rounded-lg shadow-lg p-4 border border-gray-200">
          <h3 className="font-semibold text-sm mb-2">Legend</h3>
          <div className="space-y-2 text-xs">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
              <span>Complaints (Last 90 mins)</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
              <span>Predicted Hotspots</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
              <span>Digital Cordons</span>
            </div>
          </div>
        </div>

        {/* MapLibre GL + Deck.gl */}
        <DeckGL
          viewState={INITIAL_VIEW_STATE}
          controller={true}
          layers={layers}
          onViewStateChange={({ viewState }) => {
            if (mapRef.current) {
              mapRef.current.jumpTo({
                center: [viewState.longitude, viewState.latitude],
                zoom: viewState.zoom,
                bearing: viewState.bearing,
                pitch: viewState.pitch
              });
            }
          }}
        >
          <MapView id="map" width="100%" height="100%" controller={false}>
            <Map
              ref={mapRef}
              mapLibreImport="maplibre-gl"
              mapStyle={MAP_STYLE}
              onLoad={() => setMapLoaded(true)}
              antialias={true}
              reuseMaps
            >
              <NavigationControl position="top-left" />
              <ScaleControl />
            </Map>
          </MapView>
        </DeckGL>

        {/* Loading indicator */}
        {loading && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20">
            <div className="bg-white rounded-lg shadow-lg p-4 border border-gray-200">
              <div className="flex items-center">
                <RefreshCw className="h-6 w-6 animate-spin text-blue-600 mr-3" />
                <p className="text-sm font-medium">Loading intelligence data...</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Hotspot Detail Modal */}
      {selectedHotspot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Hotspot Details</h3>
                <button
                  onClick={() => setSelectedHotspot(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Location</p>
                  <p className="font-medium">{selectedHotspot.hotspot.location_name}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Confidence</p>
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                      <div
                        className="bg-red-600 h-2 rounded-full"
                        style={{ width: `${selectedHotspot.hotspot.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="font-medium">{(selectedHotspot.hotspot.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Time Remaining</p>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2 text-gray-400" />
                    <span className="font-medium">
                      {selectedHotspot.timeLeft > 0 ? `${selectedHotspot.timeLeft} minutes` : 'Expired'}
                    </span>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Hotspot ID</p>
                  <p className="font-mono text-xs">{selectedHotspot.hotspot.id}</p>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {selectedHotspot.timeLeft > 0 && (
                  <>
                    <button
                      onClick={() => handleMarkAsInterdicted(selectedHotspot.hotspot.id)}
                      className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Mark as Interdicted
                    </button>
                    <button
                      onClick={() => handleActivateCordon(selectedHotspot.hotspot.id)}
                      className="w-full bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors flex items-center justify-center"
                    >
                      <Shield className="h-4 w-4 mr-2" />
                      Activate Digital Cordon
                    </button>
                  </>
                )}
                <button
                  onClick={() => handleMarkAsFalse(selectedHotspot.hotspot.id)}
                  className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Mark as False Alarm
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}