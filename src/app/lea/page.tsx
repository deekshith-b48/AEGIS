'use client';

import { useState, useEffect } from 'react';
import { MapPin, AlertTriangle, CheckCircle, XCircle, Shield, Clock, RefreshCw, AlertCircle } from 'lucide-react';
import { getRiskHeatmap, submitFeedback, activateCordon } from '@/lib/api';
import { Hotspot, Cordon } from '@/types';

interface SystemMetrics {
  active_complaints: number;
  active_hotspots: number;
  active_cordons: number;
  system_accuracy: number;
}

export default function LEADashboard() {
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [cordons, setCordons] = useState<Cordon[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics>({
    active_complaints: 0,
    active_hotspots: 0,
    active_cordons: 0,
    system_accuracy: 0.58,
  });
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [alertInbox, setAlertInbox] = useState<Hotspot[]>([]);

  // Fetch data from API
  const fetchData = async () => {
    try {
      setIsLoading(true);
      const data = await getRiskHeatmap();
      setHotspots(data.hotspots);
      setCordons(data.cordons);
      setMetrics(data.system_metrics);
      setAlertInbox(data.hotspots.filter(h => h.confidence >= 0.8));
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, []);

  // Set up polling for real-time updates
  useEffect(() => {
    const interval = setInterval(fetchData, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleMarkAsInterdicted = async (hotspotId: string) => {
    try {
      await submitFeedback({
        hotspot_id: hotspotId,
        lea_action: 'interdicted',
        notes: 'Marked as interdicted via dashboard'
      });
      await fetchData(); // Refresh data
      setSelectedHotspot(null);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleMarkAsFalse = async (hotspotId: string) => {
    try {
      await submitFeedback({
        hotspot_id: hotspotId,
        lea_action: 'false',
        notes: 'False alarm - no suspicious activity'
      });
      await fetchData(); // Refresh data
      setSelectedHotspot(null);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleActivateCordon = async (hotspotId: string) => {
    try {
      await activateCordon({
        hotspot_id: hotspotId,
        radius_meters: 2000,
        duration_minutes: 45
      });
      await fetchData(); // Refresh data
    } catch (error) {
      console.error('Failed to activate cordon:', error);
    }
  };

  const getTimeRemaining = (predictedAt: string, timeWindowMins: number) => {
    const predicted = new Date(predictedAt);
    const expiry = new Date(predicted.getTime() + timeWindowMins * 60000);
    const now = new Date();
    const remaining = Math.max(0, Math.floor((expiry.getTime() - now.getTime()) / 60000));
    return remaining;
  };

  return (
    <div className="h-full">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">LEA Dashboard</h1>
          <p className="text-gray-600">Real-time scam threat intelligence and prediction system</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Last Updated</p>
            <p className="text-sm font-medium">{lastUpdated.toLocaleTimeString()}</p>
          </div>
          <button
            onClick={fetchData}
            disabled={isLoading}
            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="bg-blue-100 p-2 rounded-lg mr-3">
              <AlertTriangle className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Active Complaints</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.active_complaints}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="bg-red-100 p-2 rounded-lg mr-3">
              <MapPin className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Active Hotspots</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.active_hotspots}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="bg-yellow-100 p-2 rounded-lg mr-3">
              <Shield className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Digital Cordons</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.active_cordons}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
          <div className="flex items-center">
            <div className="bg-green-100 p-2 rounded-lg mr-3">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">System Accuracy</p>
              <p className="text-2xl font-bold text-gray-900">{(metrics.system_accuracy * 100).toFixed(0)}%</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map Area */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow border border-gray-200 h-full">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Risk Intelligence Map</h2>
              <p className="text-sm text-gray-500">Real-time threat predictions and active alerts</p>
            </div>
            <div className="p-4 h-96 bg-gray-100 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <MapPin className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Interactive Map View</h3>
                <p className="text-gray-500 mb-4">
                  MapLibre GL integration would display real-time intelligence here
                </p>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-white p-3 rounded border">
                    <div className="flex items-center mb-1">
                      <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                      <span className="font-medium">Complaints</span>
                    </div>
                    <p className="text-gray-600">Last 2 hours</p>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <div className="flex items-center mb-1">
                      <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                      <span className="font-medium">Hotspots</span>
                    </div>
                    <p className="text-gray-600">Pulsing alerts</p>
                  </div>
                </div>
                {/* Mock Hotspot Visualization */}
                <div className="mt-4 space-y-2">
                  {hotspots.slice(0, 3).map((hotspot, index) => (
                    <div
                      key={hotspot.id}
                      className="bg-white p-3 rounded border flex items-center justify-between cursor-pointer hover:bg-gray-50"
                      onClick={() => setSelectedHotspot(hotspot)}
                    >
                      <div className="flex items-center">
                        <div className={`w-3 h-3 rounded-full mr-3 ${
                          hotspot.status === 'active' ? 'bg-red-500' :
                          hotspot.status === 'interdicted' ? 'bg-green-500' : 'bg-gray-500'
                        }`}></div>
                        <div className="text-left">
                          <p className="font-medium text-sm">{hotspot.location_name}</p>
                          <p className="text-xs text-gray-500">
                            Confidence: {(hotspot.confidence * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">
                          {getTimeRemaining(hotspot.predicted_at, hotspot.time_window_mins)}m left
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Alert Inbox */}
          <div className="bg-white rounded-lg shadow border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Alert Inbox</h2>
              <p className="text-sm text-gray-500">High-confidence predictions</p>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {alertInbox.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p>No high-confidence alerts</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {alertInbox.map((alert) => (
                    <div
                      key={alert.id}
                      className="p-4 hover:bg-gray-50 cursor-pointer"
                      onClick={() => setSelectedHotspot(alert)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium text-sm text-gray-900">{alert.location_name}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {(alert.confidence * 100).toFixed(0)}% confidence
                          </p>
                          <div className="flex items-center mt-2">
                            <Clock className="h-3 w-3 text-gray-400 mr-1" />
                            <span className="text-xs text-gray-500">
                              {getTimeRemaining(alert.predicted_at, alert.time_window_mins)}m remaining
                            </span>
                          </div>
                        </div>
                        <div className={`px-2 py-1 text-xs rounded-full ${
                          alert.status === 'active' ? 'bg-red-100 text-red-700' :
                          alert.status === 'interdicted' ? 'bg-green-100 text-green-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {alert.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-lg shadow border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
            </div>
            <div className="p-4 space-y-2">
              <button
                onClick={fetchData}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Data
              </button>
              <button className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors">
                Export Report
              </button>
              <button className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors">
                Settings
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Hotspot Detail Modal */}
      {selectedHotspot && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
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
                  <p className="font-medium">{selectedHotspot.location_name}</p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Confidence</p>
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                      <div
                        className="bg-red-600 h-2 rounded-full"
                        style={{ width: `${selectedHotspot.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="font-medium">{(selectedHotspot.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Time Remaining</p>
                  <p className="font-medium">
                    {getTimeRemaining(selectedHotspot.predicted_at, selectedHotspot.time_window_mins)} minutes
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <div className={`px-2 py-1 text-sm rounded-full inline-block ${
                    selectedHotspot.status === 'active' ? 'bg-red-100 text-red-700' :
                    selectedHotspot.status === 'interdicted' ? 'bg-green-100 text-green-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {selectedHotspot.status}
                  </div>
                </div>
              </div>

              <div className="mt-6 flex space-x-3">
                {selectedHotspot.status === 'active' && (
                  <>
                    <button
                      onClick={() => handleMarkAsInterdicted(selectedHotspot.id)}
                      className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Mark as Interdicted
                    </button>
                    <button
                      onClick={() => handleActivateCordon(selectedHotspot.id)}
                      className="flex-1 bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors flex items-center justify-center"
                    >
                      <Shield className="h-4 w-4 mr-2" />
                      Activate Digital Cordon
                    </button>
                  </>
                )}
                {selectedHotspot.status === 'active' && (
                  <button
                    onClick={() => handleMarkAsFalse(selectedHotspot.id)}
                    className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    Mark as False Alarm
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}