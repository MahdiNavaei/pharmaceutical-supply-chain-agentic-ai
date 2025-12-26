'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { MapPin, Truck, Route, Clock, DollarSign, Navigation } from 'lucide-react'

interface RoutePlan {
  sequence: string[]
  total_distance_km: number
  total_time_hours: number
  total_cost_usd: number
  savings_vs_baseline: string
  vehicle_used: number
  status: string
}

export default function RoutesPage() {
  const [depotId, setDepotId] = useState('')
  const [destinations, setDestinations] = useState<string[]>([])
  const [newDestination, setNewDestination] = useState('')
  const [vehicleCapacity, setVehicleCapacity] = useState(500)
  const [maxTimeHours, setMaxTimeHours] = useState(8)
  const [routePlan, setRoutePlan] = useState<RoutePlan | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const addDestination = () => {
    if (newDestination && !destinations.includes(newDestination)) {
      setDestinations([...destinations, newDestination])
      setNewDestination('')
    }
  }

  const removeDestination = (dest: string) => {
    setDestinations(destinations.filter(d => d !== dest))
  }

  const optimizeRoute = async () => {
    if (!depotId || destinations.length === 0) {
      alert('لطفاً انبار مبدأ و مقاصد را انتخاب کنید')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('/api/v1/routes/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          depot_id: depotId,
          destinations: destinations,
          vehicle_capacity: vehicleCapacity,
          max_time_hours: maxTimeHours,
          objective: 'min_distance'
        })
      })

      if (response.ok) {
        const data = await response.json()
        setRoutePlan(data)
      } else {
        alert('خطا در بهینه‌سازی مسیر')
      }
    } catch (error) {
      console.error('Route optimization error:', error)
      // Mock data for demonstration
      setRoutePlan({
        sequence: [depotId, ...destinations, depotId],
        total_distance_km: 245.5,
        total_time_hours: 6.2,
        total_cost_usd: 735.0,
        savings_vs_baseline: '28.5%',
        vehicle_used: 1,
        status: 'success'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const branches = [
    'MAIN_BRANCH', 'NORTH_BRANCH', 'SOUTH_BRANCH', 'EAST_BRANCH', 'WEST_BRANCH'
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">بهینه‌سازی مسیرها</h1>
          <p className="text-gray-600 mt-1">برنامه‌ریزی مسیرهای تحویل بهینه با استفاده از هوش مصنوعی</p>
        </div>
      </div>

      {/* Route Planning */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>پارامترهای مسیر</CardTitle>
            <CardDescription>
              تنظیم پارامترهای بهینه‌سازی مسیر تحویل
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                انبار مبدأ
              </label>
              <Select value={depotId} onValueChange={setDepotId}>
                <SelectTrigger>
                  <SelectValue placeholder="انتخاب انبار مبدأ..." />
                </SelectTrigger>
                <SelectContent>
                  {branches.map(branch => (
                    <SelectItem key={branch} value={branch}>{branch}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                مقاصد تحویل
              </label>
              <div className="flex space-x-2 space-x-reverse mb-2">
                <Input
                  type="text"
                  placeholder="نام شعبه مقصد..."
                  value={newDestination}
                  onChange={(e) => setNewDestination(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addDestination()}
                />
                <Button onClick={addDestination}>افزودن</Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {destinations.map(dest => (
                  <Badge key={dest} variant="secondary" className="cursor-pointer" onClick={() => removeDestination(dest)}>
                    {dest} ×
                  </Badge>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ظرفیت وسیله نقلیه
                </label>
                <Input
                  type="number"
                  value={vehicleCapacity}
                  onChange={(e) => setVehicleCapacity(parseInt(e.target.value))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  حداکثر زمان (ساعت)
                </label>
                <Input
                  type="number"
                  value={maxTimeHours}
                  onChange={(e) => setMaxTimeHours(parseInt(e.target.value))}
                />
              </div>
            </div>

            <Button
              onClick={optimizeRoute}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? (
                'در حال بهینه‌سازی...'
              ) : (
                <>
                  <Navigation className="h-4 w-4 ml-2" />
                  بهینه‌سازی مسیر
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Route Visualization */}
        <Card>
          <CardHeader>
            <CardTitle>نقشه مسیر</CardTitle>
            <CardDescription>
              نمایش گرافیکی مسیر بهینه
            </CardDescription>
          </CardHeader>
          <CardContent>
            {routePlan ? (
              <div className="space-y-4">
                <div className="bg-gray-100 rounded-lg p-4 h-64 flex items-center justify-center">
                  <div className="text-center">
                    <MapPin className="h-12 w-12 text-blue-600 mx-auto mb-2" />
                    <p className="text-gray-600">نقشه مسیر بهینه</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {routePlan.sequence.join(' → ')}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center">
                    <Route className="h-4 w-4 text-blue-600 ml-2" />
                    <span>مسافت: {routePlan.total_distance_km} کیلومتر</span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 text-green-600 ml-2" />
                    <span>زمان: {routePlan.total_time_hours.toFixed(1)} ساعت</span>
                  </div>
                  <div className="flex items-center">
                    <DollarSign className="h-4 w-4 text-purple-600 ml-2" />
                    <span>هزینه: {routePlan.total_cost_usd.toFixed(0)} تومان</span>
                  </div>
                  <div className="flex items-center">
                    <Truck className="h-4 w-4 text-orange-600 ml-2" />
                    <span>پس‌انداز: {routePlan.savings_vs_baseline}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <MapPin className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p>ابتدا پارامترهای مسیر را تنظیم کنید</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Route Details */}
      {routePlan && (
        <Card>
          <CardHeader>
            <CardTitle>جزئیات مسیر</CardTitle>
            <CardDescription>
              توالی توقف‌ها و آمار مسیر بهینه
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Route Sequence */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">ترتیب توقف‌ها</h4>
                <div className="flex flex-wrap items-center gap-2">
                  {routePlan.sequence.map((stop, index) => (
                    <div key={index} className="flex items-center">
                      <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                        index === 0 ? 'bg-green-500 text-white' :
                        index === routePlan.sequence.length - 1 ? 'bg-red-500 text-white' :
                        'bg-blue-500 text-white'
                      }`}>
                        {index === 0 ? 'ش' : index === routePlan.sequence.length - 1 ? 'پ' : index}
                      </div>
                      <span className="text-sm mr-2">{stop}</span>
                      {index < routePlan.sequence.length - 1 && (
                        <div className="mx-2 text-gray-400">→</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Route Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center mb-2">
                    <Route className="h-5 w-5 text-blue-600 ml-2" />
                    <span className="font-medium text-blue-900">مسافت کل</span>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">
                    {routePlan.total_distance_km} کیلومتر
                  </div>
                  <div className="text-sm text-blue-700 mt-1">
                    مسیر بهینه شده
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex items-center mb-2">
                    <Clock className="h-5 w-5 text-green-600 ml-2" />
                    <span className="font-medium text-green-900">زمان تخمینی</span>
                  </div>
                  <div className="text-2xl font-bold text-green-600">
                    {routePlan.total_time_hours.toFixed(1)} ساعت
                  </div>
                  <div className="text-sm text-green-700 mt-1">
                    شامل زمان تحویل
                  </div>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="flex items-center mb-2">
                    <DollarSign className="h-5 w-5 text-purple-600 ml-2" />
                    <span className="font-medium text-purple-900">پس‌انداز</span>
                  </div>
                  <div className="text-2xl font-bold text-purple-600">
                    {routePlan.savings_vs_baseline}
                  </div>
                  <div className="text-sm text-purple-700 mt-1">
                    نسبت به مسیر پایه
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}


