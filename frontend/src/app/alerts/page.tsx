'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  Search,
  Filter,
  Bell,
  AlertCircle
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

interface Alert {
  severity: 'CRITICAL' | 'WARNING' | 'INFO'
  branch_id: string
  item_id: string
  alert_type: string
  current_stock?: number
  days_until_stockout?: number
  message: string
  recommended_action: string
  timestamp: string
  is_resolved: boolean
}

interface AlertSummary {
  total_alerts: number
  critical_count: number
  warning_count: number
  info_count: number
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [summary, setSummary] = useState<AlertSummary>({
    total_alerts: 0,
    critical_count: 0,
    warning_count: 0,
    info_count: 0
  })
  const [aiInsights, setAiInsights] = useState<string>('')
  const [filteredAlerts, setFilteredAlerts] = useState<Alert[]>([])
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadAlerts()
  }, [])

  useEffect(() => {
    filterAlerts()
  }, [alerts, severityFilter, searchQuery])

  const loadAlerts = async () => {
    setIsLoading(true)
    try {
      // In real implementation, this would call the backend API
      const response = await fetch('/api/v1/alerts')
      if (response.ok) {
        const data = await response.json()
        setAlerts(data.alerts || [])
        setSummary({
          total_alerts: data.total_alerts || 0,
          critical_count: data.critical_count || 0,
          warning_count: data.warning_count || 0,
          info_count: data.info_count || 0
        })
        setAiInsights(data.ai_insights || 'تحلیل هوشمند در دسترس نیست')
      } else {
        // Mock data for demonstration
        const mockAlerts: Alert[] = [
          {
            severity: 'CRITICAL',
            branch_id: 'MAIN_BRANCH',
            item_id: 'Metformin',
            alert_type: 'STOCKOUT_RISK',
            current_stock: 45,
            days_until_stockout: 1.5,
            message: 'کمبود موجودی اورژانسی: ۱.۵ روز موجودی باقی مانده',
            recommended_action: 'URGENT_ORDER',
            timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
            is_resolved: false
          },
          {
            severity: 'WARNING',
            branch_id: 'NORTH_BRANCH',
            item_id: 'Insulin',
            alert_type: 'LOW_STOCK',
            current_stock: 120,
            days_until_stockout: 5.2,
            message: 'موجودی کم: ۵.۲ روز موجودی باقی مانده',
            recommended_action: 'ORDER_SOON',
            timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
            is_resolved: false
          },
          {
            severity: 'INFO',
            branch_id: 'SYSTEM',
            item_id: 'AI_MODEL',
            alert_type: 'FORECAST_COMPLETED',
            message: 'پیش‌بینی تقاضای ماه آینده برای ۵۰ دارو تکمیل شد',
            recommended_action: 'REVIEW_RESULTS',
            timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
            is_resolved: false
          },
          {
            severity: 'CRITICAL',
            branch_id: 'SOUTH_BRANCH',
            item_id: 'Aspirin',
            alert_type: 'STOCKOUT_RISK',
            current_stock: 25,
            days_until_stockout: 0.8,
            message: 'کمبود موجودی اورژانسی: کمتر از ۱ روز موجودی باقی مانده',
            recommended_action: 'URGENT_ORDER',
            timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
            is_resolved: false
          },
          {
            severity: 'WARNING',
            branch_id: 'EAST_BRANCH',
            item_id: 'Amoxicillin',
            alert_type: 'OVERSTOCK',
            current_stock: 850,
            message: 'موجودی اضافی: ۳۵۰ واحد بیش از حد بهینه',
            recommended_action: 'REDISTRIBUTE',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            is_resolved: false
          }
        ]
        setAlerts(mockAlerts)
        setSummary({
          total_alerts: mockAlerts.length,
          critical_count: mockAlerts.filter(a => a.severity === 'CRITICAL').length,
          warning_count: mockAlerts.filter(a => a.severity === 'WARNING').length,
          info_count: mockAlerts.filter(a => a.severity === 'INFO').length
        })
        setAiInsights('تحلیل هوشمند در دسترس نیست')
      }
    } catch (error) {
      console.error('Failed to load alerts:', error)
      setAiInsights('تحلیل هوشمند در دسترس نیست')
      // Keep mock data
    } finally {
      setIsLoading(false)
    }
  }

  const filterAlerts = () => {
    let filtered = alerts

    // Filter by severity
    if (severityFilter !== 'all') {
      filtered = filtered.filter(alert => alert.severity === severityFilter)
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(alert =>
        alert.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        alert.item_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        alert.branch_id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    setFilteredAlerts(filtered)
  }

  const resolveAlert = async (alertIndex: number) => {
    // In real implementation, this would call the backend API
    const updatedAlerts = [...alerts]
    updatedAlerts[alertIndex].is_resolved = true
    setAlerts(updatedAlerts)

    // Update summary
    setSummary(prev => ({
      ...prev,
      total_alerts: prev.total_alerts - 1,
      critical_count: updatedAlerts[alertIndex].severity === 'CRITICAL' ? prev.critical_count - 1 : prev.critical_count,
      warning_count: updatedAlerts[alertIndex].severity === 'WARNING' ? prev.warning_count - 1 : prev.warning_count,
      info_count: updatedAlerts[alertIndex].severity === 'INFO' ? prev.info_count - 1 : prev.info_count
    }))
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-200'
      case 'WARNING': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'INFO': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return <AlertTriangle className="h-4 w-4" />
      case 'WARNING': return <AlertCircle className="h-4 w-4" />
      case 'INFO': return <Bell className="h-4 w-4" />
      default: return <AlertCircle className="h-4 w-4" />
    }
  }

  const chartData = [
    { name: 'بحرانی', value: summary.critical_count, color: '#ef4444' },
    { name: 'هشدار', value: summary.warning_count, color: '#f97316' },
    { name: 'اطلاعات', value: summary.info_count, color: '#3b82f6' }
  ]

  const branchData = [
    { branch: 'شعبه مرکزی', alerts: 2 },
    { branch: 'شعبه شمالی', alerts: 1 },
    { branch: 'شعبه جنوبی', alerts: 1 },
    { branch: 'شعبه شرقی', alerts: 1 }
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="mr-2 text-gray-600">در حال بارگذاری هشدارها...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">پایش هشدارها</h1>
          <p className="text-gray-600 mt-1">مدیریت و پیگیری هشدارهای سیستم زنجیره تأمین</p>
        </div>
        <Button onClick={loadAlerts}>
          <RefreshCw className="h-4 w-4 ml-2" />
          بروزرسانی
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">کل هشدارها</CardTitle>
            <AlertTriangle className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{summary.total_alerts}</div>
            <p className="text-xs text-gray-500 mt-1">هشدار فعال</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">بحرانی</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{summary.critical_count}</div>
            <p className="text-xs text-gray-500 mt-1">نیاز به اقدام فوری</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">هشدار</CardTitle>
            <AlertCircle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{summary.warning_count}</div>
            <p className="text-xs text-gray-500 mt-1">نیاز به توجه</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">اطلاعات</CardTitle>
            <Bell className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{summary.info_count}</div>
            <p className="text-xs text-gray-500 mt-1">اطلاعات سیستمی</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>توزیع هشدارها بر اساس شدت</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>هشدارها بر اساس شعبه</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={branchData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="branch" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="alerts" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Insights */}
      <Card>
        <CardHeader>
          <CardTitle>تحلیل هوشمند هشدارها</CardTitle>
          <CardDescription>خلاصه توصیه‌های مدل زبانی بر اساس هشدارهای فعلی</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm leading-6 text-gray-800 whitespace-pre-wrap">
            {aiInsights || 'تحلیل هوشمند در دسترس نیست'}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>فیلتر هشدارها</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  type="text"
                  placeholder="جستجو در هشدارها..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-4 pr-10"
                />
              </div>
            </div>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="فیلتر شدت" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">همه هشدارها</SelectItem>
                <SelectItem value="CRITICAL">بحرانی</SelectItem>
                <SelectItem value="WARNING">هشدار</SelectItem>
                <SelectItem value="INFO">اطلاعات</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Alerts List */}
      <Card>
        <CardHeader>
          <CardTitle>لیست هشدارها</CardTitle>
          <CardDescription>
            {filteredAlerts.length} هشدار از {alerts.length} هشدار کل
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.map((alert, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${
                  alert.is_resolved ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-200 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 space-x-reverse">
                    <div className={`p-2 rounded-full ${getSeverityColor(alert.severity)}`}>
                      {getSeverityIcon(alert.severity)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 space-x-reverse mb-2">
                        <Badge variant="outline" className={getSeverityColor(alert.severity)}>
                          {alert.severity === 'CRITICAL' ? 'بحرانی' :
                           alert.severity === 'WARNING' ? 'هشدار' : 'اطلاعات'}
                        </Badge>
                        <Badge variant="secondary">{alert.branch_id}</Badge>
                        <Badge variant="secondary">{alert.item_id}</Badge>
                        <Badge variant="outline">{alert.alert_type}</Badge>
                      </div>

                      <h4 className="text-sm font-medium text-gray-900 mb-1">
                        {alert.message}
                      </h4>

                      {alert.recommended_action && (
                        <p className="text-sm text-blue-600 mb-2">
                          اقدام پیشنهادی: {alert.recommended_action}
                        </p>
                      )}

                      {alert.current_stock && (
                        <div className="flex items-center space-x-4 space-x-reverse text-sm text-gray-600">
                          <span>موجودی فعلی: {alert.current_stock}</span>
                          {alert.days_until_stockout && (
                            <span>روز تا کمبود: {alert.days_until_stockout}</span>
                          )}
                        </div>
                      )}

                      <div className="flex items-center text-xs text-gray-500 mt-2">
                        <Clock className="h-3 w-3 ml-1" />
                        {new Date(alert.timestamp).toLocaleString('fa-IR')}
                      </div>
                    </div>
                  </div>

                  {!alert.is_resolved && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => resolveAlert(index)}
                      className="flex items-center"
                    >
                      <CheckCircle className="h-4 w-4 ml-1" />
                      حل شد
                    </Button>
                  )}

                  {alert.is_resolved && (
                    <Badge variant="secondary" className="bg-green-100 text-green-800">
                      <CheckCircle className="h-3 w-3 ml-1" />
                      حل شده
                    </Badge>
                  )}
                </div>
              </div>
            ))}

            {filteredAlerts.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                هیچ هشداری یافت نشد
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


