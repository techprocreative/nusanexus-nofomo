'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Bot, TrendingUp, TrendingDown, DollarSign, Activity, BarChart3, AlertCircle, RefreshCw } from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { getDashboardStats, getRecentBots, getRecentTrades } from '@/lib/api/dashboard'

// Simple formatting functions
function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount)
}

function formatPercentage(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function formatRelativeTime(date: string): string {
  const d = new Date(date)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000)
  
  if (diffInSeconds < 60) return 'just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  return `${Math.floor(diffInSeconds / 86400)}d ago`
}

interface DashboardStats {
  totalBots: number
  activeBots: number
  totalProfitLoss: number
  totalProfitLossPercentage: number
  totalTrades: number
  winRate: number
  todayProfitLoss: number
}

interface Bot {
  id: string
  name: string
  status: 'active' | 'stopped' | 'paused' | 'error'
  profit_loss: number
  profit_loss_percentage: number
  pair: string
  last_trade_at?: string
}

interface Trade {
  id: string
  pair: string
  side: 'buy' | 'sell'
  amount: number
  price: number
  profit_loss?: number
  created_at: string
  status: 'pending' | 'filled' | 'cancelled' | 'failed'
}

export default function DashboardPage() {
  const router = useRouter()
  const [stats, setStats] = useState<DashboardStats>({
    totalBots: 0,
    activeBots: 0,
    totalProfitLoss: 0,
    totalProfitLossPercentage: 0,
    totalTrades: 0,
    winRate: 0,
    todayProfitLoss: 0,
  })
  const [recentBots, setRecentBots] = useState<Bot[]>([])
  const [recentTrades, setRecentTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const { user } = useAuth()

  const loadDashboardData = async (showRefreshing = false) => {
    if (!user) return
    
    if (showRefreshing) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }
    
    setError(null)
    
    try {
      // Load dashboard statistics
      const [statsData, botsData, tradesData] = await Promise.all([
        getDashboardStats(),
        getRecentBots(),
        getRecentTrades(10)
      ])

      setStats({
        totalBots: statsData.total_bots,
        activeBots: statsData.active_bots,
        totalProfitLoss: statsData.total_profit_loss,
        totalProfitLossPercentage: statsData.total_profit_loss_percentage,
        totalTrades: statsData.total_trades,
        winRate: statsData.win_rate,
        todayProfitLoss: statsData.today_profit_loss,
      })

      setRecentBots(botsData || [])
      setRecentTrades(tradesData || [])
    } catch (err) {
      console.error('Error loading dashboard data:', err)
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
      
      // Set default values on error
      setStats({
        totalBots: 0,
        activeBots: 0,
        totalProfitLoss: 0,
        totalProfitLossPercentage: 0,
        totalTrades: 0,
        winRate: 0,
        todayProfitLoss: 0,
      })
      setRecentBots([])
      setRecentTrades([])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [user])

  const handleRefresh = () => {
    loadDashboardData(true)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-50'
      case 'paused': return 'text-yellow-600 bg-yellow-50'
      case 'error': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  if (loading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={handleRefresh}
                  className="inline-flex items-center px-3 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <div className="flex items-center space-x-2">
          <button 
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </button>
          <button 
            onClick={() => router.push('/bots/create')}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Bot className="h-4 w-4 mr-2" />
            Create Bot
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Bot className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Bots</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.totalBots}</dd>
                  <dt className="text-xs text-gray-500">{stats.activeBots} active</dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {stats.totalProfitLoss >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-green-500" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-500" />
                )}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total P&L</dt>
                  <dd className="text-lg font-medium text-gray-900">{formatCurrency(stats.totalProfitLoss)}</dd>
                  <dt className="text-xs text-gray-500">{formatPercentage(stats.totalProfitLossPercentage)}</dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Activity className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Trades</dt>
                  <dd className="text-lg font-medium text-gray-900">{stats.totalTrades}</dd>
                  <dt className="text-xs text-gray-500">{formatPercentage(stats.winRate)} win rate</dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Today's P&L</dt>
                  <dd className="text-lg font-medium text-gray-900">{formatCurrency(stats.todayProfitLoss)}</dd>
                  <dt className="text-xs text-gray-500">+12.5% from yesterday</dt>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Bots */}
        <div className="col-span-4 bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Bots</h3>
            <p className="mt-1 text-sm text-gray-500">Your latest trading bots and their performance</p>
            <div className="mt-6 space-y-4">
              {recentBots.map((bot) => (
                <div key={bot.id} className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{bot.name}</p>
                    <p className="text-xs text-gray-500">{bot.pair}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bot.status)}`}>
                      {bot.status}
                    </span>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${bot.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(bot.profit_loss)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatPercentage(bot.profit_loss_percentage)}
                      </p>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 ml-4">
                    {bot.last_trade_at ? formatRelativeTime(bot.last_trade_at) : 'No trades'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Trades */}
        <div className="col-span-3 bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Trades</h3>
            <p className="mt-1 text-sm text-gray-500">Latest trading activity across all bots</p>
            <div className="mt-6 space-y-4">
              {recentTrades.map((trade) => (
                <div key={trade.id} className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{trade.pair}</p>
                    <p className="text-xs text-gray-500">
                      {trade.amount} @ {formatCurrency(trade.price)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      trade.side === 'buy' ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'
                    }`}>
                      {trade.side.toUpperCase()}
                    </span>
                    {trade.profit_loss !== undefined && (
                      <div className="text-right">
                        <p className={`text-sm font-medium ${trade.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(trade.profit_loss)}
                        </p>
                      </div>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 ml-4">
                    {formatRelativeTime(trade.created_at)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}