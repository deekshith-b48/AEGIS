/**
 * Project AEGIS Greenfield LEA Dashboard
 * MapLibre GL + Deck.gl implementation with exact specifications
 */

'use client';

import { useState, useEffect } from 'react';
import LEAMapDashboard from '@/components/LEAMapDashboard';
import { getRiskHeatmap, reweightRules } from '@/lib/greenfield_api';
import { Shield, Activity, TrendingUp, Settings, RefreshCw } from 'lucide-react';

export default function LEADashboard() {
  const [systemMetrics, setSystemMetrics] = useState<any>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [reweighting, setReweighting] = useState(false);

  // Fetch initial system metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await getRiskHeatmap();
        setSystemMetrics(data.system_metrics);
      } catch (error) {
        console.error('Failed to fetch system metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Handle rule re-weighting
  const handleReweightRules = async (feedbackType: 'confirmed' | 'false') => {
    try {
      setReweighting(true);
      const result = await reweightRules(feedbackType);
      setSystemMetrics(result);
      setShowSettings(false);
    } catch (error) {
      console.error('Failed to reweight rules:', error);
    } finally {
      setReweighting(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <Shield className="h-8 w-8 text-orange-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">LEA Dashboard</h1>
              <p className="text-sm text-gray-600">Project AEGIS - Real-time Scam Threat Intelligence</p>
            </div>
          </div>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center"
          >
            <Settings className="h-4 w-4 mr-2" />
            Learning Controls
          </button>
        </div>

        {/* System Metrics Bar */}
        {systemMetrics && (
          <div className="grid grid-cols-5 gap-4 mt-4">
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
              <div className="flex items-center">
                <Activity className="h-5 w-5 text-blue-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Active Complaints</p>
                  <p className="text-lg font-bold text-blue-600">{systemMetrics.active_complaints}</p>
                </div>
              </div>
            </div>
            <div className="bg-red-50 p-3 rounded-lg border border-red-200">
              <div className="flex items-center">
                <Shield className="h-5 w-5 text-red-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Active Hotspots</p>
                  <p className="text-lg font-bold text-red-600">{systemMetrics.active_hotspots}</p>
                </div>
              </div>
            </div>
            <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
              <div className="flex items-center">
                <div className="h-5 w-5 bg-yellow-500 rounded-full mr-2"></div>
                <div>
                  <p className="text-xs text-gray-500">Digital Cordons</p>
                  <p className="text-lg font-bold text-yellow-600">{systemMetrics.active_cordons}</p>
                </div>
              </div>
            </div>
            <div className="bg-green-50 p-3 rounded-lg border border-green-200">
              <div className="flex items-center">
                <TrendingUp className="h-5 w-5 text-green-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">System Accuracy</p>
                  <p className="text-lg font-bold text-green-600">
                    {(systemMetrics.system_accuracy * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
              <div className="flex items-center">
                <RefreshCw className="h-5 w-5 text-purple-600 mr-2" />
                <div>
                  <p className="text-xs text-gray-500">Learning Engine</p>
                  <p className="text-lg font-bold text-purple-600">Active</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Learning Controls Panel */}
      {showSettings && (
        <div className="bg-gray-50 border-b border-gray-200 p-4">
          <div className="max-w-4xl mx-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Learning Loop Controls</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Rule Weights */}
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <h4 className="font-medium text-gray-900 mb-3">Current Rule Weights</h4>
                {systemMetrics?.rule_weights && (
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Fake Loan App</span>
                      <span className="text-sm font-medium">{systemMetrics.rule_weights.fake_loan_app.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">High Value Loss</span>
                      <span className="text-sm font-medium">{systemMetrics.rule_weights.high_value.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">UPI Phishing</span>
                      <span className="text-sm font-medium">{systemMetrics.rule_weights.upi_phishing.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Fallback Rule</span>
                      <span className="text-sm font-medium">{systemMetrics.rule_weights.fallback.toFixed(2)}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Re-weighting Controls */}
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <h4 className="font-medium text-gray-900 mb-3">Manual Rule Re-weighting</h4>
                <p className="text-sm text-gray-600 mb-4">
                  Simulate nightly learning adjustments based on LEA feedback
                </p>
                <div className="space-y-3">
                  <button
                    onClick={() => handleReweightRules('confirmed')}
                    disabled={reweighting}
                    className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center justify-center"
                  >
                    <TrendingUp className="h-4 w-4 mr-2" />
                    {reweighting ? 'Updating...' : 'Increase Weights (Confirmed)'}
                  </button>
                  <button
                    onClick={() => handleReweightRules('false')}
                    disabled={reweighting}
                    className="w-full bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center justify-center"
                  >
                    <Activity className="h-4 w-4 mr-2" />
                    {reweighting ? 'Updating...' : 'Decrease Weights (False)'}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-3">
                  Adjustments: ±5% per rule with ±1% system accuracy change
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Map Dashboard */}
      <div className="flex-1">
        <LEAMapDashboard />
      </div>

      {/* Footer Info */}
      <div className="bg-gray-100 border-t border-gray-200 p-3">
        <div className="flex justify-between items-center text-xs text-gray-600">
          <div>
            <span className="font-medium">Project AEGIS</span> - Greenfield Implementation
          </div>
          <div>
            MapLibre GL + Deck.gl | OpenStreetMap Tiles | Real-time Intelligence
          </div>
          <div>
            PostGIS Spatial Queries | Rule-Based AI | Zero PII Design
          </div>
        </div>
      </div>
    </div>
  );
}