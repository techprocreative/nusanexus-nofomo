'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Bot, TrendingUp, TrendingDown, DollarSign, Activity, BarChart3 } from 'lucide-react'
import { formatCurrency, formatPercentage, formatRelativeTime } from '@/lib/utils'
import { useAuth } from '@/components/providers/auth-provider'

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
  const { user } = useAuth()

  useEffect(() => {
    // Simulate loading dashboard data
    const loadDashboardData = async () => {
      setLoading(true)
      try {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // Mock data
        setStats({
          totalBots: 5,
          activeBots: 3,
          totalProfitLoss: 1250.75,
          totalProfitLossPercentage: 8.5,
          totalTrades: 147,
          winRate: 68.5,
          todayProfitLoss: 45.30,
        })

        setRecentBots([
          {
            id: '1',
            name: 'BTC Scalper',
            status: 'active',
            profit_loss: 250.50,
            profit_loss_percentage: 12.5,
            pair: 'BTC/USDT',
            last_trade_at: new Date(Date.now() - 300000).toISOString(),
          },
          {
            id: '2',
            name: 'ETH Trend',
            status: 'active',
            profit_loss: 180.25,
            profit_loss_percentage: 9.0,
            pair: 'ETH/USDT',
            last_trade_at: new Date(Date.now() - 600000).toISOString(),
          },
          {
            id: '3',
            name: 'BNB Swing',
            status: 'paused',
            profit_loss: -45.20,
            profit_loss_percentage: -2.3,
            pair: 'BNB/USDT',
            last_trade_at: new Date(Date.now() - 1800000).toISOString(),
          },
        ])

        setRecentTrades([
          {
            id: '1',
            pair: 'BTC/USDT',
            side: 'buy',
            amount: 0.1,
            price: 45000,
            profit_loss: 50.25,
            created_at: new Date(Date.now() - 300000).toISOString(),
            status: 'filled',
          },
          {
            id: '2',
            pair: 'ETH/USDT',
            side: 'sell',
            amount: 1.5,
            price: 2800,
            profit_loss: 25.40,
            created_at: new Date(Date.now() - 600000).toISOString(),
            status: 'filled',
          },
          {
            id: '3',
            pair: 'BNB/USDT',
            side: 'buy',
            amount: 2.0,
            price: 320,
            profit_loss: -12.30,
            created_at: new Date(Date.now() - 900000).toISOString(),
            status: 'filled',
          },
        ])
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      loadDashboardData()
    }
  }, [user])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-50'
      case 'paused': return 'text-yellow-600 bg-yellow-50'
      case 'error': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getTradeSideColor = (side: string) => {
    return side === 'buy' ? 'text-green-600' : 'text-red-600'
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

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </Button>
          <Button size="sm">
            <Bot className="h-4 w-4 mr-2" />
            Create Bot
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Bots</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalBots}</div>
            <p className="text-xs text-muted-foreground">
              {stats.activeBots} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            {stats.totalProfitLoss >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats.totalProfitLoss)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(stats.totalProfitLossPercentage)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Trades</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalTrades}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(stats.winRate)} win rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's P&L</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats.todayProfitLoss)}</div>
            <p className="text-xs text-muted-foreground">
              +12.5% from yesterday
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Bots */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Bots</CardTitle>
            <CardDescription>Your latest trading bots and their performance</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentBots.map((bot) => (
              <div key={bot.id} className="flex items-center space-x-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{bot.name}</p>
                  <p className="text-xs text-muted-foreground">{bot.pair}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bot.status)}`}>
                    {bot.status}
                  </span>
                  <div className="text-right">
                    <p className={`text-sm font-medium ${bot.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(bot.profit_loss)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatPercentage(bot.profit_loss_percentage)}
                    </p>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  {bot.last_trade_at ? formatRelativeTime(bot.last_trade_at) : 'No trades'}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Trades */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Trades</CardTitle>
            <CardDescription>Latest trading activity across all bots</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentTrades.map((trade) => (
              <div key={trade.id} className="flex items-center space-x-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{trade.pair}</p>
                  <p className="text-xs text-muted-foreground">
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
                <div className="text-xs text-muted-foreground">
                  {formatRelativeTime(trade.created_at)}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}