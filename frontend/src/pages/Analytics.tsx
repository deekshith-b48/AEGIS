import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  MapPin,
  Users,
  Calendar,
  Download,
  Activity,
  Eye,
  AlertTriangle,
  Shield,
  Clock
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { formatNumber, formatCurrency, getRelativeTime } from '@/lib/utils'

// Mock analytics data
const mockAnalytics = {
  overview: {
    totalComplaints: 1247,
    resolvedComplaints: 892,
    successRate: 71.5,
    avgResponseTime: 2.4,
    totalAmountRecovered: 2400000,
    activePredictions: 45,
    accuracyRate: 87.3
  },
  trends: {
    complaintsByMonth: [
      { month: 'Jan', complaints: 98, resolved: 82 },
      { month: 'Feb', complaints: 112, resolved: 95 },
      { month: 'Mar', complaints: 134, resolved: 108 },
      { month: 'Apr', complaints: 156, resolved: 142 },
      { month: 'May', complaints: 178, resolved: 165 },
      { month: 'Jun', complaints: 145, resolved: 138 }
    ],
    scamTypes: [
      { type: 'Online Fraud', count: 423, percentage: 33.9 },
      { type: 'Phishing', count: 312, percentage: 25.0 },
      { type: 'Shopping Scam', count: 267, percentage: 21.4 },
      { type: 'Job Fraud', count: 156, percentage: 12.5 },
      { type: 'Investment Fraud', count: 89, percentage: 7.2 }
    ],
    topLocations: [
      { location: 'Mumbai, Maharashtra', count: 234, amount: 850000 },
      { location: 'Delhi, NCR', count: 198, amount: 620000 },
      { location: 'Bangalore, Karnataka', count: 167, amount: 480000 },
      { location: 'Hyderabad, Telangana', count: 145, amount: 390000 },
      { location: 'Chennai, Tamil Nadu', count: 123, amount: 310000 }
    ],
    performance: {
      responseTime: [
        { metric: 'Average Response Time', value: 2.4, unit: 'hours', target: 2.0 },
        { metric: 'Resolution Time', value: 48, unit: 'hours', target: 72.0 },
        { metric: 'Prediction Accuracy', value: 87.3, unit: '%', target: 85.0 },
        { metric: 'Cordon Success Rate', value: 92.1, unit: '%', target: 90.0 }
      ]
    }
}

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('6m')
  const [selectedMetric, setSelectedMetric] = useState('overview')

  const timeRanges = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '3m', label: 'Last 3 Months' },
    { value: '6m', label: 'Last 6 Months' },
    { value: '1y', label: 'Last Year' }
  ]

  const metricCards = [
    {
      title: 'Total Complaints',
      value: mockAnalytics.overview.totalComplaints,
      change: 12.5,
      icon: Shield,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Resolved Complaints',
      value: mockAnalytics.overview.resolvedComplaints,
      change: 8.3,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Success Rate',
      value: `${mockAnalytics.overview.successRate}%`,
      change: 5.2,
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      title: 'Amount Recovered',
      value: formatCurrency(mockAnalytics.overview.totalAmountRecovered),
      change: 15.7,
      icon: Activity,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive insights and performance metrics</p>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeRanges.map((range) => (
                <SelectItem key={range.value} value={range.value}>
                  {range.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export Report
          </Button>
          <Button>
            <BarChart3 className="w-4 h-4 mr-2" />
            Generate Insights
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricCards.map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
          >
            <Card className="hover:shadow-lg transition-shadow duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{metric.title}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{metric.value}</p>
                  </div>
                  <div className={`p-3 rounded-lg ${metric.bgColor}`}>
                    <metric.icon className={`w-6 h-6 ${metric.color}`} />
                  </div>
                </div>
                <div className="flex items-center mt-4">
                  <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
                  <span className="text-sm font-medium text-green-600">{metric.change}%</span>
                  <span className="text-sm text-gray-500 ml-1">vs last period</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Complaint Trends */}
        <Card>
          <CardHeader>
            <CardTitle>Complaint Trends</CardTitle>
            <CardDescription>Monthly complaint volume and resolution rates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center">
              <div className="text-center">
                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Interactive line chart</p>
                <p className="text-sm text-gray-400 mt-2">Shows complaint trends over time</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Scam Types Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Scam Types Distribution</CardTitle>
            <CardDescription>Breakdown of cybercrime complaint types</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockAnalytics.trends.scamTypes.map((scam, index) => (
                <motion.div
                  key={scam.type}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-aegis-600 rounded-full"></div>
                    <span className="text-sm font-medium text-gray-900">{scam.type}</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-sm text-gray-600">{scam.count} cases</div>
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-aegis-600 h-2 rounded-full"
                        style={{ width: `${scam.percentage}%` }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-500">{scam.percentage}%</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Top Locations */}
        <Card>
          <CardHeader>
            <CardTitle>Top Affected Locations</CardTitle>
            <CardDescription>Locations with highest complaint volumes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockAnalytics.trends.topLocations.map((location, index) => (
                <motion.div
                  key={location.location}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <MapPin className="w-4 h-4 text-gray-600" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">{location.location}</div>
                      <div className="text-xs text-gray-500">{location.count} complaints</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">{formatCurrency(location.amount)}</div>
                    <div className="text-xs text-gray-500">Total amount</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Performance Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
            <CardDescription>Key performance indicators and targets</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockAnalytics.trends.performance.map((metric, index) => (
                <motion.div
                  key={metric.metric}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="p-4 border border-gray-200 rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{metric.metric}</div>
                      <div className="text-xs text-gray-500">Target: {metric.target}{metric.unit}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-gray-900">
                        {metric.value}{metric.unit}
                      </div>
                      <div className="text-xs text-gray-500">
                        {metric.value >= metric.target ? (
                          <span className="text-green-600">On target</span>
                        ) : (
                          <span className="text-yellow-600">Below target</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          metric.value >= metric.target ? 'bg-green-600' : 'bg-yellow-600'
                        }`}
                        style={{ width: `${Math.min((metric.value / metric.target) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Additional Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Model Performance */}
        <Card>
          <CardHeader>
            <CardTitle>AI Model Performance</CardTitle>
            <CardDescription>Accuracy and effectiveness metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-aegis-600">{mockAnalytics.overview.accuracyRate}%</div>
                <div className="text-sm text-gray-600">Overall Accuracy</div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>CST-Transformer</span>
                  <span className="font-medium">89.2%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Federated Graph</span>
                  <span className="font-medium">85.7%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Behavioral Twin</span>
                  <span className="font-medium">87.0%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Response Time Analysis */}
        <Card>
          <CardHeader>
            <CardTitle>Response Time Analysis</CardTitle>
            <CardDescription>Average response times by priority</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-red-600" />
                  <span className="text-sm font-medium">Critical</span>
                </div>
                <span className="text-sm font-medium text-gray-900">1.2 hours</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-orange-600" />
                  <span className="text-sm font-medium">High</span>
                </div>
                <span className="text-sm font-medium text-gray-900">2.1 hours</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Eye className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium">Medium</span>
                </div>
                <span className="text-sm font-medium text-gray-900">3.5 hours</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium">Low</span>
                </div>
                <span className="text-sm font-medium text-gray-900">6.8 hours</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Digital Cordon Effectiveness */}
        <Card>
          <CardHeader>
            <CardTitle>Digital Cordon Effectiveness</CardTitle>
            <CardDescription>Success rates and impact metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">92.1%</div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Cordons Activated</span>
                  <span className="font-medium">156</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Funds Protected</span>
                  <span className="font-medium">₹4.2M</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Avg. Response Time</span>
                  <span className="font-medium">8.5 min</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}