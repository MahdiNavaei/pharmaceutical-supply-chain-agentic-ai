'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  TrendingUp,
  Package,
  Truck,
  AlertTriangle,
  DollarSign,
  Clock,
  CheckCircle,
  RefreshCw
} from 'lucide-react'
import { useEffect, useState } from 'react'

interface KPIMetrics {
  total_forecast_accuracy: number
  inventory_turnover: number
  delivery_on_time: number
  stockout_reduction: number
  cost_savings: number
  alerts_critical: number
  alerts_warning: number
  system_health: string
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<KPIMetrics>({
    total_forecast_accuracy: 0,
    inventory_turnover: 0,
    delivery_on_time: 0,
    stockout_reduction: 0,
    cost_savings: 0,
    alerts_critical: 0,
    alerts_warning: 0,
    system_health: 'healthy'
  })

  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading metrics from API
    const loadMetrics = async () => {
      try {
        // In real implementation, this would call the backend API
        const response = await fetch('/api/v1/dashboard/kpis')
        if (response.ok) {
          const data = await response.json()
          setMetrics(data)
        } else {
          // Mock data for demonstration
          setMetrics({
            total_forecast_accuracy: 94.2,
            inventory_turnover: 12.8,
            delivery_on_time: 97.5,
            stockout_reduction: 78.3,
            cost_savings: 245000,
            alerts_critical: 3,
            alerts_warning: 12,
            system_health: 'healthy'
          })
        }
      } catch (error) {
        console.error('Failed to load metrics:', error)
        // Keep mock data
      } finally {
        setIsLoading(false)
      }
    }

    loadMetrics()
  }, [])

  const kpiCards = [
    {
      title: 'دقت پیش‌بینی',
      value: `${metrics.total_forecast_accuracy}%`,
      description: 'دقت مدل‌های پیش‌بینی تقاضا',
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'چرخش موجودی',
      value: `${metrics.inventory_turnover}`,
      description: 'دفعات چرخش موجودی در سال',
      icon: Package,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'تحویل به موقع',
      value: `${metrics.delivery_on_time}%`,
      description: 'درصد تحویل‌های به موقع',
      icon: Truck,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    },
    {
      title: 'کاهش کمبود',
      value: `${metrics.stockout_reduction}%`,
      description: 'کاهش موارد کمبود موجودی',
      icon: CheckCircle,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50'
    }
  ]

  const alerts = [
    {
      type: 'critical',
      title: 'کمبود موجودی اورژانسی',
      message: 'داروی متفورمین در شعبه مرکزی کمتر از ۲ روز موجودی دارد',
      time: '۱۰ دقیقه پیش',
      branch: 'شعبه مرکزی'
    },
    {
      type: 'warning',
      title: 'تأخیر در تحویل',
      message: 'مسیر تحویل به شعبه شمالی ۲ ساعت تأخیر دارد',
      time: '۳۰ دقیقه پیش',
      branch: 'شعبه شمالی'
    },
    {
      type: 'info',
      title: 'پیش‌بینی تقاضا تکمیل شد',
      message: 'پیش‌بینی تقاضای ماه آینده برای ۵۰ دارو محاسبه شد',
      time: '۱ ساعت پیش',
      branch: 'سیستم'
    }
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="mr-2 text-gray-600">در حال بارگذاری...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">داشبورد مدیریت زنجیره تأمین</h1>
          <p className="text-gray-700 mt-1">نمای کلی عملکرد سیستم هوش مصنوعی</p>
        </div>
        <div className="flex items-center space-x-3 space-x-reverse">
          <Badge variant={metrics.system_health === 'healthy' ? 'default' : 'destructive'}>
            سیستم {metrics.system_health === 'healthy' ? 'سالم' : 'نیاز به بررسی'}
          </Badge>
          <Button>
            <RefreshCw className="h-4 w-4 ml-2" />
            بروزرسانی
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((kpi, index) => {
          const Icon = kpi.icon
          return (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-700">
                  {kpi.title}
                </CardTitle>
                <div className={`p-2 rounded-lg ${kpi.bgColor}`}>
                  <Icon className={`h-4 w-4 ${kpi.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{kpi.value}</div>
                <p className="text-xs text-gray-600 mt-1">{kpi.description}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Cost Savings & Alerts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Savings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <DollarSign className="h-5 w-5 ml-2 text-green-600" />
              پس‌انداز هزینه‌ای
            </CardTitle>
            <CardDescription>
              صرفه‌جویی حاصل از بهینه‌سازی‌های هوش مصنوعی
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600 mb-2">
              {metrics.cost_savings.toLocaleString()} تومان
            </div>
            <div className="text-sm text-gray-600">
              در مقایسه با روش‌های سنتی
            </div>
          </CardContent>
        </Card>

        {/* Alert Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 ml-2 text-orange-600" />
              خلاصه هشدارها
            </CardTitle>
            <CardDescription>
              وضعیت فعلی هشدارهای سیستم
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{metrics.alerts_critical}</div>
                <div className="text-sm text-gray-600">بحرانی</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{metrics.alerts_warning}</div>
                <div className="text-sm text-gray-600">هشدار</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">0</div>
                <div className="text-sm text-gray-600">اطلاعات</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>هشدارهای اخیر</CardTitle>
          <CardDescription>
            آخرین فعالیت‌ها و هشدارهای سیستم
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {alerts.map((alert, index) => (
              <div key={index} className="flex items-start space-x-3 space-x-reverse p-3 rounded-lg border border-gray-200 hover:bg-gray-50">
                <div className={`p-1 rounded-full ${
                  alert.type === 'critical' ? 'bg-red-100' :
                  alert.type === 'warning' ? 'bg-orange-100' : 'bg-blue-100'
                }`}>
                  <AlertTriangle className={`h-4 w-4 ${
                    alert.type === 'critical' ? 'text-red-600' :
                    alert.type === 'warning' ? 'text-orange-600' : 'text-blue-600'
                  }`} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900">{alert.title}</h4>
                    <div className="flex items-center text-xs text-gray-500">
                      <Clock className="h-3 w-3 ml-1" />
                      {alert.time}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                  <Badge variant="outline" className="mt-2 text-xs">
                    {alert.branch}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}