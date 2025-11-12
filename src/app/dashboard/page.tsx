"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  Shield, AlertTriangle, TrendingUp, Users, MapPin, Clock,
  Brain, Network, BarChart3, Zap, Activity, Eye, ArrowUpRight,
  ArrowDownRight, Target, ShieldCheck, Lock, Database, Cpu
} from 'lucide-react';
import GeoAnalyticsMap from '@/components/ui/GeoAnalyticsMap';
import AlertMonitoring from '@/components/ui/AlertMonitoring';

const AnalyticsDashboard: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [realTimeData, setRealTimeData] = useState({
    activeAlerts: 0,
    processingQueue: 0,
    systemLoad: 0,
    predictionsAccuracy: 0
  });
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [riskDistribution, setRiskDistribution] = useState([]);
  const [modelPerformance, setModelPerformance] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState([]);

  // Simulate real-time data updates
  useEffect(() => {
    // Initialize data
    const initializeData = () => {
      setTimeSeriesData([
        { time: '00:00', complaints: 45, predictions: 12, accuracy: 56 },
        { time: '04:00', complaints: 38, predictions: 10, accuracy: 58 },
        { time: '08:00', complaints: 89, predictions: 25, accuracy: 62 },
        { time: '12:00', complaints: 156, predictions: 48, accuracy: 65 },
        { time: '16:00', complaints: 134, predictions: 42, accuracy: 68 },
        { time: '20:00', complaints: 98, predictions: 31, accuracy: 71 },
        { time: '23:59', complaints: 67, predictions: 21, accuracy: 74 }
      ]);

      setRiskDistribution([
        { name: 'High Risk', value: 23, color: '#ef4444' },
        { name: 'Medium Risk', value: 45, color: '#f59e0b' },
        { name: 'Low Risk', value: 89, color: '#10b981' },
        { name: 'Minimal Risk', value: 156, color: '#3b82f6' }
      ]);

      setModelPerformance([
        { model: 'CST-Transformer', accuracy: 78, speed: 1.2, status: 'active' },
        { model: 'Federated Graph', accuracy: 82, speed: 0.8, status: 'active' },
        { model: 'Behavioral Twin', accuracy: 75, speed: 1.5, status: 'training' },
        { model: 'Risk Engine', accuracy: 85, speed: 0.5, status: 'active' }
      ]);

      setSystemMetrics([
        { metric: 'CPU Usage', value: 67, threshold: 80 },
        { metric: 'Memory', value: 54, threshold: 85 },
        { metric: 'API Response', value: 1.2, threshold: 2.0 },
        { metric: 'Queue Depth', value: 12, threshold: 50 }
      ]);

      setRealTimeData({
        activeAlerts: 8,
        processingQueue: 23,
        systemLoad: 67,
        predictionsAccuracy: 74
      });

      setIsLoading(false);
    };

    initializeData();

    // Simulate real-time updates
    const interval = setInterval(() => {
      setRealTimeData(prev => ({
        activeAlerts: Math.max(0, prev.activeAlerts + Math.floor(Math.random() * 5) - 2),
        processingQueue: Math.max(0, prev.processingQueue + Math.floor(Math.random() * 10) - 4),
        systemLoad: Math.min(100, Math.max(0, prev.systemLoad + Math.floor(Math.random() * 20) - 10)),
        predictionsAccuracy: Math.min(100, Math.max(0, prev.predictionsAccuracy + Math.floor(Math.random() * 6) - 3))
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading analytics dashboard..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <BarChart3 className="h-8 w-8 text-orange-600 mr-3" />
                Real-Time Analytics Dashboard
              </h1>
              <p className="text-gray-600 mt-2">Live monitoring and insights for Project AEGIS</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-gray-600">Live</span>
              <Badge variant="success" className="ml-2">System Online</Badge>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Active Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{realTimeData.activeAlerts}</div>
              <div className="flex items-center text-xs text-gray-500 mt-1">
                <ArrowUpRight className="h-3 w-3 text-red-500 mr-1" />
                <span className="text-red-500">12%</span> from last hour
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Processing Queue</CardTitle>
              <Clock className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{realTimeData.processingQueue}</div>
              <div className="flex items-center text-xs text-gray-500 mt-1">
                <ArrowDownRight className="h-3 w-3 text-green-500 mr-1" />
                <span className="text-green-500">8%</span> from last hour
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">System Load</CardTitle>
              <Activity className="h-4 w-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{realTimeData.systemLoad}%</div>
              <Progress value={realTimeData.systemLoad} className="mt-2" />
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Prediction Accuracy</CardTitle>
              <Target className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">{realTimeData.predictionsAccuracy}%</div>
              <div className="flex items-center text-xs text-gray-500 mt-1">
                <ArrowUpRight className="h-3 w-3 text-green-500 mr-1" />
                <span className="text-green-500">3%</span> improvement
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <TrendingUp className="h-5 w-5 text-blue-600 mr-2" />
                24-Hour Activity Trends
              </CardTitle>
              <CardDescription>Complaints, predictions, and accuracy over time</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="complaints" stroke="#3b82f6" strokeWidth={2} name="Complaints" />
                  <Line type="monotone" dataKey="predictions" stroke="#10b981" strokeWidth={2} name="Predictions" />
                  <Line type="monotone" dataKey="accuracy" stroke="#f59e0b" strokeWidth={2} name="Accuracy %" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="h-5 w-5 text-purple-600 mr-2" />
                Risk Distribution
              </CardTitle>
              <CardDescription>Cases by risk level</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {riskDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* AI Models Performance */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Brain className="h-5 w-5 text-orange-600 mr-2" />
              AI Model Performance
            </CardTitle>
            <CardDescription>Real-time performance metrics for all AI models</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {modelPerformance.map((model, index) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold text-gray-900">{model.model}</h4>
                    <Badge
                      variant={model.status === 'active' ? 'success' : 'warning'}
                      className="text-xs"
                    >
                      {model.status}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Accuracy</span>
                        <span className="font-medium">{model.accuracy}%</span>
                      </div>
                      <Progress value={model.accuracy} variant="success" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Speed</span>
                        <span className="font-medium">{model.speed}s</span>
                      </div>
                      <Progress value={Math.min(100, (2 - model.speed) * 50)} variant="default" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* System Metrics */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Cpu className="h-5 w-5 text-green-600 mr-2" />
              System Health Metrics
            </CardTitle>
            <CardDescription>Real-time system performance indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {systemMetrics.map((metric, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">{metric.metric}</span>
                    <span className={`text-sm font-bold ${
                      metric.value > metric.threshold * 0.8 ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {metric.value}{metric.metric.includes('%') ? '%' : metric.metric.includes('s') ? 's' : ''}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        metric.value > metric.threshold * 0.8 ? 'bg-red-600' : 'bg-green-600'
                      }`}
                      style={{ width: `${(metric.value / (metric.threshold * 1.2)) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Geospatial and Alert Monitoring */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <GeoAnalyticsMap />
          <AlertMonitoring />
        </div>

        {/* Recent Predictions */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Eye className="h-5 w-5 text-blue-600 mr-2" />
              Recent Predictions & System Status
            </CardTitle>
            <CardDescription>Latest AI predictions and external system connectivity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Predictions */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-4">Latest AI Predictions</h4>
                <div className="space-y-3">
                  {[
                    { id: 'P2024-001', location: 'Mumbai Central', risk: 'High', confidence: 92, status: 'active' },
                    { id: 'P2024-002', location: 'Delhi Nehru Place', risk: 'Medium', confidence: 78, status: 'monitoring' },
                    { id: 'P2024-003', location: 'Bangalore MG Road', risk: 'Low', confidence: 65, status: 'resolved' },
                    { id: 'P2024-004', location: 'Chennai T Nagar', risk: 'High', confidence: 88, status: 'active' },
                  ].map((prediction, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <MapPin className="h-4 w-4 text-gray-500" />
                        <div>
                          <p className="font-medium text-gray-900">{prediction.id}</p>
                          <p className="text-sm text-gray-600">{prediction.location}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge
                          variant={prediction.risk === 'High' ? 'destructive' : prediction.risk === 'Medium' ? 'warning' : 'success'}
                          className="text-xs"
                        >
                          {prediction.risk}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">{prediction.confidence}% confidence</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* System Integration Status */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-4">External System Connectivity</h4>
                <div className="space-y-3">
                  {[
                    { name: 'NCRP Integration', status: 'connected', latency: '45ms' },
                    { name: 'CFCFRMS Banking', status: 'connected', latency: '120ms' },
                    { name: 'I4C Database', status: 'connected', latency: '78ms' },
                    { name: 'NPCI API', status: 'connected', latency: '32ms' },
                    { name: 'Kafka Pipeline', status: 'connected', latency: '5ms' },
                  ].map((system, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`w-2 h-2 rounded-full ${
                          system.status === 'connected' ? 'bg-green-500' : 'bg-red-500'
                        } animate-pulse`} />
                        <span className="font-medium text-gray-900">{system.name}</span>
                      </div>
                      <div className="text-right">
                        <Badge variant="success" className="text-xs">
                          {system.status}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">{system.latency}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;