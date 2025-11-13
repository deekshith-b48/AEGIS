import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  Shield,
  AlertTriangle,
  MapPin,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  Activity,
  Eye,
  BarChart3,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { formatNumber, formatCurrency, getRelativeTime, getStatusColor } from '@/lib/utils'

// Mock data - replace with actual API calls
const mockStats = {
  totalComplaints: 1247,
  activeAlerts: 23,
  predictionsMade: 856,
  successRate: 87.3,
  responseTime: 2.4,
  cordonsActive: 12
}

const mockRecentActivity = [
  {
    id: 1,
    type: 'complaint',
    message: 'New online fraud complaint registered',
    time: new Date(Date.now() - 1000 * 60 * 5),
    status: 'pending',
    priority: 'high'
  },
  {
    id: 2,
    type: 'prediction',
    message: 'High-risk prediction generated for Mumbai Central',
    time: new Date(Date.now() - 1000 * 60 * 15),
    status: 'active',
    priority: 'critical'
  },
  {
    id: 3,
    type: 'alert',
    message: 'Digital cordon activated successfully',
    time: new Date(Date.now() - 1000 * 60 * 30),
    status: 'completed',
    priority: 'medium'
  },
  {
    id: 4,
    type: 'system',
    message: 'AI model training completed',
    time: new Date(Date.now() - 1000 * 60 * 45),
    status: 'completed',
    priority: 'low'
  }
]

const mockMetrics = [
  { name: 'Mon', complaints: 45, resolved: 38 },
  { name: 'Tue', complaints: 52, resolved: 45 },
  { name: 'Wed', complaints: 38, resolved: 42 },
  { name: 'Thu', complaints: 65, resolved: 58 },
  { name: 'Fri', complaints: 71, resolved: 69 },
  { name: 'Sat', complaints: 48, resolved: 44 },
  { name: 'Sun', complaints: 35, resolved: 33 }
]

export default function Dashboard() {
  const [timeRange, setTimeRange] = useState('7d')
  const [selectedMetric, setSelectedMetric] = useState('complaints')

  const statCards = [
    {
      title: 'Total Complaints',
      value: mockStats.totalComplaints,
      change: 12.5,
      changeType: 'increase',
      icon: Shield,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Active Alerts',
      value: mockStats.activeAlerts,
      change: -5.2,
      changeType: 'decrease',
      icon: AlertTriangle,
      color: 'text-red-600',
      bgColor: 'bg-red-50'
    },
    {
      title: 'Predictions Made',
      value: mockStats.predictionsMade,
      change: 8.7,
      changeType: 'increase',
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Success Rate',
      value: `${mockStats.successRate}%`,
      change: 3.2,
      changeType: 'increase',
      icon: CheckCircle,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Real-time overview of cybercrime response activities</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <BarChart3 className="w-4 h-4 mr-2" />
            Export Report
          </Button>
          <Button size="sm">
            <Zap className="w-4 h-4 mr-2" />
            Quick Actions
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
          >
            <Card className="hover:shadow-lg transition-shadow duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                </div>
                <div className="flex items-center mt-4">
                  {stat.changeType === 'increase' ? (
                    <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-600 mr-1" />
                  )}
                  <span className={`text-sm font-medium ${
                    stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {Math.abs(stat.change)}%
                  </span>
                  <span className="text-sm text-gray-500 ml-1">from last week</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Weekly Performance</CardTitle>
                  <CardDescription>Complaints received vs resolved</CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant={selectedMetric === 'complaints' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedMetric('complaints')}
                  >
                    Complaints
                  </Button>
                  <Button
                    variant={selectedMetric === 'resolved' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedMetric('resolved')}
                  >
                    Resolved
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center">
                {/* Placeholder for actual chart */}
                <div className="text-center">
                  <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Interactive chart will be displayed here</p>
                  <p className="text-sm text-gray-400 mt-2">Line/bar chart showing weekly trends</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest system updates and events</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockRecentActivity.map((activity) => (
                <motion.div
                  key={activity.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex items-start space-x-3"
                >
                  <div className={`p-2 rounded-lg ${
                    activity.type === 'complaint' ? 'bg-blue-50' :
                    activity.type === 'prediction' ? 'bg-purple-50' :
                    activity.type === 'alert' ? 'bg-red-50' :
                    'bg-gray-50'
                  }`}>
                    {
                      activity.type === 'complaint' ? <Shield className="w-4 h-4 text-blue-600" /> :
                      activity.type === 'prediction' ? <TrendingUp className="w-4 h-4 text-purple-600" /> :
                      activity.type === 'alert' ? <AlertTriangle className="w-4 h-4 text-red-600" /> :
                      <Activity className="w-4 h-4 text-gray-600" />
                    }
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900">{activity.message}</p>
                    <div className="flex items-center mt-1 space-x-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(activity.priority)}`}>
                        {activity.priority}
                      </span>
                      <span className="text-xs text-gray-500">
                        {getRelativeTime(activity.time)}
                      </span>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    {activity.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : activity.status === 'active' ? (
                      <Eye className="w-4 h-4 text-blue-500" />
                    ) : (
                      <Clock className="w-4 h-4 text-yellow-500" />
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4">
              View All Activity
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions & Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks and shortcuts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <Button variant="outline" className="justify-start">
                <Shield className="w-4 h-4 mr-2" />
                New Complaint
              </Button>
              <Button variant="outline" className="justify-start">
                <MapPin className="w-4 h-4 mr-2" />
                View Maps
              </Button>
              <Button variant="outline" className="justify-start">
                <AlertTriangle className="w-4 h-4 mr-2" />
                Create Alert
              </Button>
              <Button variant="outline" className="justify-start">
                <Users className="w-4 h-4 mr-2" />
                Manage Users
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>Overall system health and performance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium">API Status</span>
                </div>
                <span className="text-sm text-green-600">Operational</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium">Database</span>
                </div>
                <span className="text-sm text-green-600">Connected</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                  <span className="text-sm font-medium">AI Models</span>
                </div>
                <span className="text-sm text-yellow-600">Training</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium">Response Time</span>
                </div>
                <span className="text-sm text-gray-600">{mockStats.responseTime}s</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm font-medium">Active Cordons</span>
                </div>
                <span className="text-sm text-blue-600">{mockStats.cordonsActive}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Live Map Preview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Live Activity Map</CardTitle>
              <CardDescription>Real-time locations of active alerts and predictions</CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <MapPin className="w-4 h-4 mr-2" />
              View Full Map
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Interactive map will be displayed here</p>
              <p className="text-sm text-gray-400 mt-2">Showcasing real-time locations with heatmaps</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}