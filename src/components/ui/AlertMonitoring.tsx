"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/Progress';
import {
  AlertTriangle, Bell, Shield, Clock, CheckCircle, XCircle,
  AlertCircle, Info, Zap, Users, MapPin, Filter, RefreshCw
} from 'lucide-react';

interface Alert {
  id: string;
  type: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  message: string;
  source: string;
  timestamp: Date;
  location?: string;
  acknowledged: boolean;
  assignedTo?: string;
  status: 'active' | 'acknowledged' | 'resolved';
  metadata: Record<string, any>;
}

const AlertMonitoring: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    // Simulate real-time alerts
    const mockAlerts: Alert[] = [
      {
        id: 'ALT-001',
        type: 'critical',
        title: 'High-Risk Prediction Confirmed',
        message: 'AI model predicts 95% probability of cash-out at Mumbai Central Station within 30 minutes',
        source: 'CST-Transformer',
        timestamp: new Date(Date.now() - 5 * 60 * 1000),
        location: 'Mumbai Central',
        acknowledged: false,
        status: 'active',
        metadata: { confidence: 95, model: 'CST-Transformer' }
      },
      {
        id: 'ALT-002',
        type: 'high',
        title: 'Multiple Low-Value Transactions Detected',
        message: 'Pattern of 15 transactions under ₹10,000 detected in 5-minute window',
        source: 'Transaction Monitor',
        timestamp: new Date(Date.now() - 12 * 60 * 1000),
        location: 'Delhi Nehru Place',
        acknowledged: true,
        assignedTo: 'Officer Sharma',
        status: 'acknowledged',
        metadata: { transactionCount: 15, totalAmount: 125000 }
      },
      {
        id: 'ALT-003',
        type: 'medium',
        title: 'Behavioral Anomaly Detected',
        message: 'Unusual account activity pattern matches known fraud MO',
        source: 'Behavioral Twin',
        timestamp: new Date(Date.now() - 25 * 60 * 1000),
        acknowledged: false,
        status: 'active',
        metadata: { anomalyScore: 0.78, patternMatch: '87%' }
      },
      {
        id: 'ALT-004',
        type: 'info',
        title: 'Model Retraining Completed',
        message: 'Risk scoring model v2.3 deployed with 4% accuracy improvement',
        source: 'Continuous Learning',
        timestamp: new Date(Date.now() - 45 * 60 * 1000),
        acknowledged: true,
        status: 'resolved',
        metadata: { modelVersion: 'v2.3', improvement: '4%' }
      },
      {
        id: 'ALT-005',
        type: 'low',
        title: 'Digital Cordon Expired',
        message: 'Geofenced area monitoring for Bangalore MG Road has been automatically lifted',
        source: 'NPCI Integration',
        timestamp: new Date(Date.now() - 60 * 60 * 1000),
        location: 'Bangalore MG Road',
        acknowledged: true,
        status: 'resolved',
        metadata: { duration: '90 minutes', transactionsFlagged: 0 }
      }
    ];

    setAlerts(mockAlerts);

    // Simulate real-time updates
    const interval = setInterval(() => {
      setAlerts(prev => {
        const updated = [...prev];
        // Randomly update some alert statuses
        if (Math.random() > 0.7 && updated.length > 0) {
          const randomIndex = Math.floor(Math.random() * updated.length);
          if (updated[randomIndex].status === 'active' && Math.random() > 0.5) {
            updated[randomIndex] = {
              ...updated[randomIndex],
              acknowledged: true,
              status: 'acknowledged',
              assignedTo: 'Auto-assignment'
            };
          }
        }
        return updated;
      });
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const filteredAlerts = alerts.filter(alert => {
    if (selectedFilter === 'all') return true;
    if (selectedFilter === 'active') return alert.status === 'active';
    if (selectedFilter === 'unacknowledged') return !alert.acknowledged;
    return alert.type === selectedFilter;
  });

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'critical': return <XCircle className="h-4 w-4" />;
      case 'high': return <AlertTriangle className="h-4 w-4" />;
      case 'medium': return <AlertCircle className="h-4 w-4" />;
      case 'low': return <Info className="h-4 w-4" />;
      default: return <Bell className="h-4 w-4" />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getAlertBadgeVariant = (type: string) => {
    switch (type) {
      case 'critical': return 'destructive' as const;
      case 'high': return 'warning' as const;
      case 'medium': return 'default' as const;
      case 'low': return 'secondary' as const;
      default: return 'outline' as const;
    }
  };

  const formatTimeAgo = (timestamp: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - timestamp.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // Simulate refresh
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsRefreshing(false);
  };

  const handleAcknowledge = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId
        ? { ...alert, acknowledged: true, status: 'acknowledged' as const, assignedTo: 'Current User' }
        : alert
    ));
  };

  const handleResolve = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId
        ? { ...alert, status: 'resolved' as const }
        : alert
    ));
  };

  const alertStats = {
    total: alerts.length,
    active: alerts.filter(a => a.status === 'active').length,
    critical: alerts.filter(a => a.type === 'critical' && a.status === 'active').length,
    unacknowledged: alerts.filter(a => !a.acknowledged && a.status === 'active').length
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center">
              <Bell className="h-5 w-5 text-red-600 mr-2" />
              Real-Time Alert Monitoring
            </CardTitle>
            <CardDescription>Live security alerts and system notifications</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">{alertStats.total}</div>
            <div className="text-xs text-gray-600">Total Alerts</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">{alertStats.active}</div>
            <div className="text-xs text-gray-600">Active</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{alertStats.critical}</div>
            <div className="text-xs text-gray-600">Critical</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{alertStats.unacknowledged}</div>
            <div className="text-xs text-gray-600">Unacknowledged</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-2 flex-wrap">
          <Filter className="h-4 w-4 text-gray-500" />
          <Button
            variant={selectedFilter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('all')}
          >
            All ({alerts.length})
          </Button>
          <Button
            variant={selectedFilter === 'active' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('active')}
          >
            Active ({alertStats.active})
          </Button>
          <Button
            variant={selectedFilter === 'unacknowledged' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('unacknowledged')}
          >
            Unacknowledged ({alertStats.unacknowledged})
          </Button>
          <Button
            variant={selectedFilter === 'critical' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedFilter('critical')}
          >
            Critical ({alertStats.critical})
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {filteredAlerts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Shield className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No alerts found for the selected filter</p>
            </div>
          ) : (
            filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${getAlertColor(alert.type)} transition-all duration-200 hover:shadow-md`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="mt-1">
                      {getAlertIcon(alert.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="font-semibold text-sm truncate">{alert.title}</h4>
                        <Badge variant={getAlertBadgeVariant(alert.type)} className="text-xs">
                          {alert.type}
                        </Badge>
                        {alert.status === 'active' && (
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        )}
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{alert.message}</p>

                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <div className="flex items-center">
                          <Zap className="h-3 w-3 mr-1" />
                          {alert.source}
                        </div>
                        <div className="flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          {formatTimeAgo(alert.timestamp)}
                        </div>
                        {alert.location && (
                          <div className="flex items-center">
                            <MapPin className="h-3 w-3 mr-1" />
                            {alert.location}
                          </div>
                        )}
                        {alert.assignedTo && (
                          <div className="flex items-center">
                            <Users className="h-3 w-3 mr-1" />
                            {alert.assignedTo}
                          </div>
                        )}
                      </div>

                      {/* Metadata */}
                      {Object.keys(alert.metadata).length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {Object.entries(alert.metadata).map(([key, value]) => (
                            <span key={key} className="text-xs bg-white/50 px-2 py-1 rounded">
                              {key}: {value}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col space-y-2 ml-4">
                    {alert.status === 'active' && !alert.acknowledged && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleAcknowledge(alert.id)}
                      >
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Acknowledge
                      </Button>
                    )}
                    {alert.status !== 'resolved' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResolve(alert.id)}
                      >
                        <Shield className="h-3 w-3 mr-1" />
                        Resolve
                      </Button>
                    )}
                    {alert.status === 'resolved' && (
                      <Badge variant="success" className="text-xs">
                        Resolved
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Alert Processing Progress */}
        {alertStats.unacknowledged > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-yellow-800">
                {alertStats.unacknowledged} alerts require attention
              </span>
              <span className="text-xs text-yellow-600">
                {Math.round((alertStats.active / alertStats.total) * 100)}% active
              </span>
            </div>
            <Progress
              value={(alertStats.active / alertStats.total) * 100}
              variant="warning"
              className="h-2"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AlertMonitoring;