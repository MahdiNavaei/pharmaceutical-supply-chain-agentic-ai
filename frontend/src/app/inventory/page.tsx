'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Package,
  Search,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

interface InventoryItem {
  drug_id: string
  drug_name: string
  branch_id: string
  current_stock: number
  optimal_stock: number
  safe_stock: number
  demand_forecast: number
  status: 'normal' | 'low' | 'high' | 'critical'
}

export default function InventoryPage() {
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadInventory()
  }, [])

  const loadInventory = async () => {
    setIsLoading(true)
    try {
      // Mock data for demonstration
      const mockInventory: InventoryItem[] = [
        {
          drug_id: 'MET001',
          drug_name: 'Metformin',
          branch_id: 'MAIN_BRANCH',
          current_stock: 450,
          optimal_stock: 500,
          safe_stock: 100,
          demand_forecast: 120,
          status: 'normal'
        },
        {
          drug_id: 'ASP001',
          drug_name: 'Aspirin',
          branch_id: 'MAIN_BRANCH',
          current_stock: 45,
          optimal_stock: 200,
          safe_stock: 40,
          demand_forecast: 80,
          status: 'critical'
        },
        {
          drug_id: 'INS001',
          drug_name: 'Insulin',
          branch_id: 'NORTH_BRANCH',
          current_stock: 320,
          optimal_stock: 300,
          safe_stock: 60,
          demand_forecast: 95,
          status: 'high'
        },
        {
          drug_id: 'AMX001',
          drug_name: 'Amoxicillin',
          branch_id: 'SOUTH_BRANCH',
          current_stock: 180,
          optimal_stock: 250,
          safe_stock: 50,
          demand_forecast: 110,
          status: 'low'
        },
        {
          drug_id: 'OME001',
          drug_name: 'Omeprazole',
          branch_id: 'EAST_BRANCH',
          current_stock: 275,
          optimal_stock: 300,
          safe_stock: 60,
          demand_forecast: 85,
          status: 'normal'
        }
      ]
      setInventory(mockInventory)
    } catch (error) {
      console.error('Failed to load inventory:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredInventory = inventory.filter(item =>
    item.drug_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.branch_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'critical':
        return <Badge variant="destructive">بحرانی</Badge>
      case 'low':
        return <Badge className="bg-orange-100 text-orange-800">کم</Badge>
      case 'high':
        return <Badge className="bg-blue-100 text-blue-800">زیاد</Badge>
      case 'normal':
        return <Badge variant="secondary">نرمال</Badge>
      default:
        return <Badge variant="outline">نامشخص</Badge>
    }
  }

  const getStockPercentage = (current: number, optimal: number) => {
    return Math.round((current / optimal) * 100)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="mr-2 text-gray-600">در حال بارگذاری موجودی...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">مدیریت موجودی</h1>
          <p className="text-gray-600 mt-1">پایش و مدیریت موجودی داروها در شعب مختلف</p>
        </div>
        <Button onClick={loadInventory}>
          <RefreshCw className="h-4 w-4 ml-2" />
          بروزرسانی
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              type="text"
              placeholder="جستجو بر اساس نام دارو یا شعبه..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-4 pr-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Inventory Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredInventory.map((item) => (
          <Card key={`${item.drug_id}-${item.branch_id}`} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{item.drug_name}</CardTitle>
                {getStatusBadge(item.status)}
              </div>
              <CardDescription>{item.branch_id}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Stock Level */}
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>موجودی فعلی</span>
                    <span className="font-medium">{item.current_stock} واحد</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        item.status === 'critical' ? 'bg-red-500' :
                        item.status === 'low' ? 'bg-orange-500' :
                        item.status === 'high' ? 'bg-blue-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(getStockPercentage(item.current_stock, item.optimal_stock), 100)}%` }}
                    ></div>
                  </div>
                </div>

                {/* Details */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">بهینه:</span>
                    <span className="font-medium mr-2">{item.optimal_stock}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">ایمن:</span>
                    <span className="font-medium mr-2">{item.safe_stock}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">پیش‌بینی:</span>
                    <span className="font-medium mr-2">{item.demand_forecast}/ماه</span>
                  </div>
                  <div>
                    <span className="text-gray-600">درصد:</span>
                    <span className="font-medium mr-2">{getStockPercentage(item.current_stock, item.optimal_stock)}%</span>
                  </div>
                </div>

                {/* Status Indicators */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="flex items-center space-x-2 space-x-reverse">
                    {item.current_stock < item.safe_stock ? (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    ) : item.current_stock > item.optimal_stock * 1.2 ? (
                      <TrendingUp className="h-4 w-4 text-blue-500" />
                    ) : (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    )}
                    <span className="text-sm text-gray-600">
                      {item.current_stock < item.safe_stock ? 'نیاز به سفارش' :
                       item.current_stock > item.optimal_stock * 1.2 ? 'موجودی اضافی' : 'وضعیت مناسب'}
                    </span>
                  </div>
                  <Button size="sm" variant="outline">
                    جزئیات
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredInventory.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-gray-500">
              هیچ آیتمی یافت نشد
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Package className="h-8 w-8 text-blue-600 ml-3" />
              <div>
                <p className="text-2xl font-bold text-gray-900">{inventory.length}</p>
                <p className="text-sm text-gray-600">کل آیتم‌ها</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-600 ml-3" />
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {inventory.filter(i => i.status === 'critical').length}
                </p>
                <p className="text-sm text-gray-600">موارد بحرانی</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <TrendingDown className="h-8 w-8 text-orange-600 ml-3" />
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {inventory.filter(i => i.status === 'low').length}
                </p>
                <p className="text-sm text-gray-600">موجودی کم</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600 ml-3" />
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {inventory.filter(i => i.status === 'normal').length}
                </p>
                <p className="text-sm text-gray-600">وضعیت مناسب</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


