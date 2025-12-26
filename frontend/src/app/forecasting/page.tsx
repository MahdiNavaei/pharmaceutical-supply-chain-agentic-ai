'use client'

import { useState } from 'react'
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
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp, Calendar, Target, AlertCircle, RefreshCw } from 'lucide-react'

interface ForecastPoint {
  date: string
  predicted: number
  actual?: number
  lower_bound: number
  upper_bound: number
}

interface ForecastApiPoint {
  date: string
  yhat?: number
  yhat_lower?: number
  yhat_upper?: number
  actual?: number
  predicted?: number
  lower_bound?: number
  upper_bound?: number
}

interface ForecastApiResponse {
  forecast: ForecastApiPoint[]
  metrics: {
    mape: number | null
    rmse: number | null
    mae: number | null
  }
  confidence_interval?: {
    lower?: number
    upper?: number
  }
  model: string
  status: string
  message?: string
}

interface ForecastData {
  forecast: ForecastPoint[]
  metrics: {
    mape: number | null
    rmse: number | null
    mae: number | null
  }
  model: string
  status: string
  message?: string
}

export default function ForecastingPage() {
  const [selectedDrug, setSelectedDrug] = useState('')
  const [horizonDays, setHorizonDays] = useState(30)
  const [model, setModel] = useState('prophet')
  const [forecastData, setForecastData] = useState<ForecastData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const drugs = [
    'Metformin', 'Aspirin', 'Insulin', 'Amoxicillin', 'Omeprazole',
    'Losartan', 'Simvastatin', 'Albuterol', 'Warfarin', 'Furosemide'
  ]

  const normalizeForecast = (data: ForecastApiResponse): ForecastData => ({
    forecast: (data.forecast || []).map((point) => ({
      date: point.date,
      predicted: point.yhat ?? point.predicted ?? 0,
      actual: point.actual,
      lower_bound: point.yhat_lower ?? point.lower_bound ?? 0,
      upper_bound: point.yhat_upper ?? point.upper_bound ?? 0
    })),
    metrics: {
      mape: data.metrics?.mape ?? null,
      rmse: data.metrics?.rmse ?? null,
      mae: data.metrics?.mae ?? null
    },
    model: data.model,
    status: data.status,
    message: data.message
  })

  const formatMetric = (value: number | null, suffix = '') => {
    if (value === null || value === undefined) return `-${suffix}`
    return `${value}${suffix}`
  }

  const runForecast = async () => {
    if (!selectedDrug) {
      setError('لطفاً یک دارو انتخاب کنید')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch('/api/v1/forecast/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_type: 'branch',
          entity_id: 'MAIN_BRANCH',
          item_id: selectedDrug,
          horizon_days: horizonDays,
          model: model
        })
      })

      if (!response.ok) {
        setError('خطا در دریافت پیش‌بینی')
        setForecastData(null)
        return
      }

      const apiData: ForecastApiResponse = await response.json()
      const normalized = normalizeForecast(apiData)

      if (normalized.status !== 'success' || !normalized.forecast.length) {
        setError(apiData.message || 'پیش‌بینی معتبری برنگشت')
        setForecastData(null)
        return
      }

      setForecastData(normalized)
    } catch (err) {
      console.error('Forecast error:', err)
      setError('خطا در اتصال به سرور')
      setForecastData(null)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">پیش‌بینی تقاضای دارویی</h1>
          <p className="text-gray-600 mt-1">استفاده از مدل‌های هوش مصنوعی برای پیش‌بینی نیاز بازار</p>
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>پارامترهای پیش‌بینی</CardTitle>
          <CardDescription>
            انتخاب دارو و تنظیمات مدل پیش‌بینی
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                انتخاب دارو
              </label>
              <Select value={selectedDrug} onValueChange={setSelectedDrug}>
                <SelectTrigger>
                  <SelectValue placeholder="انتخاب دارو..." />
                </SelectTrigger>
                <SelectContent>
                  {drugs.map(drug => (
                    <SelectItem key={drug} value={drug}>{drug}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                افق زمانی (روز)
              </label>
              <Select value={horizonDays.toString()} onValueChange={(value) => setHorizonDays(parseInt(value))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">7 روز</SelectItem>
                  <SelectItem value="14">14 روز</SelectItem>
                  <SelectItem value="30">30 روز</SelectItem>
                  <SelectItem value="60">60 روز</SelectItem>
                  <SelectItem value="90">90 روز</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                مدل پیش‌بینی
              </label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="prophet">Prophet</SelectItem>
                  <SelectItem value="lstm">LSTM</SelectItem>
                  <SelectItem value="moving_average">میانگین متحرک</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button
                onClick={runForecast}
                disabled={isLoading}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 ml-2 animate-spin" />
                    در حال پیش‌بینی...
                  </>
                ) : (
                  <>
                    <TrendingUp className="h-4 w-4 ml-2" />
                    اجرای پیش‌بینی
                  </>
                )}
              </Button>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-center">
                <AlertCircle className="h-5 w-5 text-red-600 ml-2" />
                <span className="text-red-800 text-sm">{error}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {forecastData && (
        <>
          {/* Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">دقت مدل (MAPE)</CardTitle>
                <Target className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {formatMetric(forecastData.metrics.mape, '%')}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  خطای میانگین درصد
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">RMSE</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {formatMetric(forecastData.metrics.rmse)}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  ریشه خطای مربع میانگین
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">MAE</CardTitle>
                <Calendar className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">
                  {formatMetric(forecastData.metrics.mae)}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  خطای مطلق میانگین
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Forecast Chart */}
          <Card>
            <CardHeader>
              <CardTitle>نمودار پیش‌بینی تقاضا</CardTitle>
              <CardDescription>
                پیش‌بینی تقاضا برای {selectedDrug} به مدت {horizonDays} روز آینده
                <Badge variant="outline" className="mr-2">
                  مدل: {forecastData.model}
                </Badge>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastData.forecast}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => new Date(value).toLocaleDateString('fa-IR')}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                      labelFormatter={(value) => new Date(value).toLocaleDateString('fa-IR')}
                      formatter={(value) => [value?.toLocaleString() || '0', 'مقدار پیش‌بینی']}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted"
                      stroke="#3b82f6"
                      strokeWidth={3}
                      dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="upper_bound"
                      stroke="#10b981"
                      strokeWidth={1}
                      strokeDasharray="5 5"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="lower_bound"
                      stroke="#ef4444"
                      strokeWidth={1}
                      strokeDasharray="5 5"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Forecast Table */}
          <Card>
            <CardHeader>
              <CardTitle>جدول پیش‌بینی</CardTitle>
              <CardDescription>
                جزئیات پیش‌بینی روزانه
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        تاریخ
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        پیش‌بینی
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        حداقل
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        حداکثر
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {forecastData.forecast.slice(0, 10).map((item, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(item.date).toLocaleDateString('fa-IR')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-medium">
                          {item.predicted.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {item.lower_bound.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {item.upper_bound.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
