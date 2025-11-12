"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { MapPin, Activity, Users, AlertTriangle, Shield, Filter, ZoomIn, ZoomOut } from 'lucide-react';

interface PredictionPoint {
  id: string;
  lat: number;
  lng: number;
  risk: 'high' | 'medium' | 'low';
  confidence: number;
  address: string;
  timeWindow: string;
  active: boolean;
}

const GeoAnalyticsMap: React.FC = () => {
  const [predictions, setPredictions] = useState<PredictionPoint[]>([]);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [mapZoom, setMapZoom] = useState(5);

  useEffect(() => {
    // Simulate prediction data
    const mockPredictions: PredictionPoint[] = [
      {
        id: 'P2024-001',
        lat: 19.0760,
        lng: 72.8777,
        risk: 'high',
        confidence: 92,
        address: 'Mumbai Central Station',
        timeWindow: 'Next 60 minutes',
        active: true
      },
      {
        id: 'P2024-002',
        lat: 28.6139,
        lng: 77.2090,
        risk: 'medium',
        confidence: 78,
        address: 'Delhi Nehru Place',
        timeWindow: 'Next 45 minutes',
        active: true
      },
      {
        id: 'P2024-003',
        lat: 12.9716,
        lng: 77.5946,
        risk: 'low',
        confidence: 65,
        address: 'Bangalore MG Road',
        timeWindow: 'Next 90 minutes',
        active: false
      },
      {
        id: 'P2024-004',
        lat: 13.0827,
        lng: 80.2707,
        risk: 'high',
        confidence: 88,
        address: 'Chennai T Nagar',
        timeWindow: 'Next 30 minutes',
        active: true
      },
      {
        id: 'P2024-005',
        lat: 22.5726,
        lng: 88.3639,
        risk: 'medium',
        confidence: 72,
        address: 'Kolkata Park Street',
        timeWindow: 'Next 75 minutes',
        active: true
      }
    ];

    setPredictions(mockPredictions);
  }, []);

  const filteredPredictions = predictions.filter(pred => {
    if (selectedFilter === 'all') return true;
    return pred.risk === selectedFilter;
  });

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getRiskBadgeVariant = (risk: string) => {
    switch (risk) {
      case 'high': return 'destructive' as const;
      case 'medium': return 'warning' as const;
      case 'low': return 'success' as const;
      default: return 'default' as const;
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center">
              <MapPin className="h-5 w-5 text-blue-600 mr-2" />
              Geospatial Predictions
            </CardTitle>
            <CardDescription>Real-time high-risk location predictions</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMapZoom(Math.max(3, mapZoom - 1))}
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setMapZoom(Math.min(10, mapZoom + 1))}
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <Button
            variant={selectedFilter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('all')}
          >
            All ({predictions.length})
          </Button>
          <Button
            variant={selectedFilter === 'high' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('high')}
          >
            High ({predictions.filter(p => p.risk === 'high').length})
          </Button>
          <Button
            variant={selectedFilter === 'medium' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('medium')}
          >
            Medium ({predictions.filter(p => p.risk === 'medium').length})
          </Button>
          <Button
            variant={selectedFilter === 'low' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('low')}
          >
            Low ({predictions.filter(p => p.risk === 'low').length})
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="relative h-96 bg-gradient-to-br from-blue-50 to-green-50">
          {/* Simulated Map */}
          <div className="absolute inset-0 bg-gray-100">
            {/* Map placeholder with grid */}
            <div className="w-full h-full relative" style={{ transform: `scale(${mapZoom / 5})`, transformOrigin: 'center' }}>
              {/* India map outline placeholder */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <div className="w-64 h-80 border-4 border-gray-300 rounded-lg relative bg-gray-50">
                  <div className="absolute top-4 right-8 w-8 h-16 border-4 border-gray-300 rounded" />
                  <div className="absolute top-20 left-6 w-12 h-8 border-4 border-gray-300 rounded" />
                  <div className="absolute bottom-8 left-8 w-16 h-12 border-4 border-gray-300 rounded" />
                </div>
              </div>

              {/* Prediction Points */}
              {filteredPredictions.map((prediction, index) => (
                <div
                  key={prediction.id}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer group"
                  style={{
                    top: `${20 + index * 15}%`,
                    left: `${30 + index * 10}%`,
                  }}
                >
                  {/* Pulse animation for active predictions */}
                  {prediction.active && (
                    <div className={`absolute inset-0 ${getRiskColor(prediction.risk)} rounded-full animate-ping opacity-75`} />
                  )}

                  {/* Prediction marker */}
                  <div className={`relative ${getRiskColor(prediction.risk)} w-4 h-4 rounded-full border-2 border-white shadow-lg group-hover:scale-125 transition-transform`} />

                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                    <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-3 w-48">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-sm">{prediction.id}</span>
                        <Badge variant={getRiskBadgeVariant(prediction.risk)} className="text-xs">
                          {prediction.risk}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-600 mb-1">{prediction.address}</p>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">Confidence: {prediction.confidence}%</span>
                        {prediction.active && (
                          <div className="flex items-center text-green-600">
                            <Activity className="h-3 w-3 mr-1" />
                            Active
                          </div>
                        )}
                      </div>
                      <p className="text-xs text-blue-600 mt-1">{prediction.timeWindow}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Map Legend */}
          <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
            <h4 className="font-semibold text-sm mb-2">Risk Levels</h4>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <span className="text-xs">High Risk</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                <span className="text-xs">Medium Risk</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                <span className="text-xs">Low Risk</span>
              </div>
            </div>
          </div>

          {/* Statistics Overlay */}
          <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
            <h4 className="font-semibold text-sm mb-2">Live Statistics</h4>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Active Predictions</span>
                <span className="font-medium">{filteredPredictions.filter(p => p.active).length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Avg Confidence</span>
                <span className="font-medium">
                  {filteredPredictions.length > 0
                    ? Math.round(filteredPredictions.reduce((acc, p) => acc + p.confidence, 0) / filteredPredictions.length)
                    : 0}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">High Risk Alerts</span>
                <span className="font-medium text-red-600">
                  {filteredPredictions.filter(p => p.risk === 'high').length}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Prediction Details List */}
        <div className="p-4 border-t border-gray-200">
          <h4 className="font-semibold text-sm mb-3">Active Predictions</h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {filteredPredictions.filter(p => p.active).map((prediction) => (
              <div key={prediction.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 ${getRiskColor(prediction.risk)} rounded-full`} />
                  <div>
                    <p className="text-sm font-medium">{prediction.id}</p>
                    <p className="text-xs text-gray-600">{prediction.address}</p>
                  </div>
                </div>
                <div className="text-right">
                  <Badge variant={getRiskBadgeVariant(prediction.risk)} className="text-xs mb-1">
                    {prediction.risk}
                  </Badge>
                  <p className="text-xs text-gray-500">{prediction.confidence}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default GeoAnalyticsMap;