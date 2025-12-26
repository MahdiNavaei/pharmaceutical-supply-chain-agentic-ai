'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, BarChart2, RefreshCw, TrendingUp, Bell, ShieldAlert } from 'lucide-react'

interface KPIResponse {
  total_forecast_accuracy: number
  inventory_turnover: number
  delivery_on_time: number
  stockout_reduction: number
  cost_savings: number
  alerts_critical: number
  alerts_warning: number
  system_health: string
}

interface AlertItem {
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

interface AlertsResponse {
  alerts: AlertItem[]
  total_alerts: number
  critical_count: number
  warning_count: number
  info_count: number
  ai_insights?: string
}

export default function ReportsPage() {
  const [kpis, setKpis] = useState<KPIResponse | null>(null)
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [aiInsights, setAiInsights] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      setError('')
      try {
        const [kpiRes, alertsRes] = await Promise.all([
          fetch('/api/v1/dashboard/kpis'),
          fetch('/api/v1/alerts')
        ])

        if (kpiRes.ok) {
          const data = await kpiRes.json()
          setKpis(data)
        } else {
          setError('خطا در دریافت KPI ها')
        }

        if (alertsRes.ok) {
          const data: AlertsResponse = await alertsRes.json()
          setAlerts(data.alerts || [])
          setAiInsights(data.ai_insights || '')
        }
      } catch (err) {
        console.error('Reports fetch error:', err)
        setError('خطا در دریافت گزارش‌ها')
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [])

  const kpiCards = kpis ? [
    { title: 'دقت پیش‌بینی', value: `${kpis.total_forecast_accuracy}%`, desc: 'میانگین دقت مدل‌ها', icon: TrendingUp, color: 'text-emerald-600' },
    { title: 'گردش موجودی', value: kpis.inventory_turnover.toString(), desc: 'دوران گردش موجودی', icon: BarChart2, color: 'text-blue-600' },
    { title: 'تحویل به موقع', value: `${kpis.delivery_on_time}%`, desc: 'درصد سفارش‌های به موقع', icon: RefreshCw, color: 'text-purple-600' },
    { title: 'کاهش کمبود', value: `${kpis.stockout_reduction}%`, desc: 'کاهش ریسک stockout', icon: ShieldAlert, color: 'text-orange-600' },
    { title: 'صرفه‌جویی هزینه', value: kpis.cost_savings.toLocaleString(), desc: 'صرفه‌جویی کل (ریال)', icon: TrendingUp, color: 'text-indigo-600' },
    { title: 'هشدارهای بحرانی', value: kpis.alerts_critical.toString(), desc: 'تعداد هشدارهای فوری', icon: Bell, color: 'text-red-600' },
  ] : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">گزارش‌ها</h1>
          <p className="text-gray-600 mt-1">نمای کلی عملکرد، هشدارها و تحلیل هوشمند</p>
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center space-x-2 space-x-reverse bg-white border border-gray-200 rounded-md p-4">
          <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
          <span className="text-gray-700 text-sm">در حال بارگذاری گزارش‌ها...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3 flex items-center space-x-2 space-x-reverse">
          <AlertCircle className="h-5 w-5 text-red-600" />
          <span className="text-red-700 text-sm">{error}</span>
        </div>
      )}

      {/* KPI Grid */}
      {!isLoading && kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {kpiCards.map((kpi, idx) => {
            const Icon = kpi.icon
            return (
              <Card key={idx}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-700">{kpi.title}</CardTitle>
                  <Icon className={`h-4 w-4 ${kpi.color}`} />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-gray-900">{kpi.value}</div>
                  <p className="text-xs text-gray-500 mt-1">{kpi.desc}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Alerts Snapshot */}
      {!isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>هشدارهای اخیر</CardTitle>
            <CardDescription>آخرین هشدارهای فعال سیستم</CardDescription>
          </CardHeader>
          <CardContent>
            {alerts.length === 0 ? (
              <div className="text-sm text-gray-600">هشداری ثبت نشده است.</div>
            ) : (
              <div className="space-y-3">
                {alerts.slice(0, 5).map((alert, idx) => (
                  <div key={idx} className="p-3 border border-gray-200 rounded-lg bg-white flex items-start justify-between">
                    <div className="flex items-start space-x-2 space-x-reverse">
                      <Badge variant={alert.severity === 'CRITICAL' ? 'destructive' : alert.severity === 'WARNING' ? 'secondary' : 'outline'}>
                        {alert.severity === 'CRITICAL' ? 'بحرانی' : alert.severity === 'WARNING' ? 'هشدار' : 'اطلاع'}
                      </Badge>
                      <div className="text-sm text-gray-800">
                        <div className="font-medium text-gray-900">{alert.message}</div>
                        <div className="text-gray-600 mt-1 flex flex-wrap gap-2">
                          <span>شعبه: {alert.branch_id}</span>
                          <span>کالا: {alert.item_id}</span>
                          {alert.days_until_stockout !== undefined && (
                            <span>روز تا اتمام: {alert.days_until_stockout}</span>
                          )}
                        </div>
                        {alert.recommended_action && (
                          <div className="text-xs text-blue-600 mt-1">اقدام پیشنهادی: {alert.recommended_action}</div>
                        )}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(alert.timestamp).toLocaleString('fa-IR')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* AI Insights */}
      {!isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>تحلیل هوشمند</CardTitle>
            <CardDescription>خلاصه توصیه‌های مدل زبانی روی هشدارهای اخیر</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm leading-6 text-gray-800 whitespace-pre-wrap">
              {aiInsights || 'تحلیل هوشمند در دسترس نیست.'}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
