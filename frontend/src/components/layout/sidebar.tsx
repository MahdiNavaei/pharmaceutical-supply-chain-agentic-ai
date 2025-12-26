'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  BarChart3,
  TrendingUp,
  Package,
  MapPin,
  AlertTriangle,
  Settings,
  Home
} from 'lucide-react'

const navigation = [
  { name: 'داشبورد', href: '/', icon: Home },
  { name: 'پیش‌بینی تقاضا', href: '/forecasting', icon: TrendingUp },
  { name: 'مدیریت موجودی', href: '/inventory', icon: Package },
  { name: 'بهینه‌سازی مسیرها', href: '/routes', icon: MapPin },
  { name: 'هشدارها', href: '/alerts', icon: AlertTriangle },
  { name: 'گزارش‌ها', href: '/reports', icon: BarChart3 },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex flex-col w-64 bg-white border-l border-gray-200">
      <div className="flex items-center justify-center h-16 px-4 bg-gradient-to-r from-blue-600 to-purple-600">
        <h1 className="text-white text-lg font-bold">دارو زنجیره</h1>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700 border-r-4 border-blue-700'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <Icon className="ml-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-900">Agentic AI</p>
            <p className="text-xs text-gray-600">Supply Chain v1.0</p>
          </div>
        </div>
      </div>
    </div>
  )
}
