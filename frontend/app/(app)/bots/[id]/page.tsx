'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { ArrowLeft, Play, Pause, Square, Settings, Trash2, Bot, TrendingUp, TrendingDown, Activity, AlertCircle, RefreshCw, Edit, Calendar, DollarSign } from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { getBot, startBot, stopBot, deleteBot, getBotStatus } from '@/lib/api/bots'
import { getTradesByBot } from '@/lib/api/trades'
import { Bot as BotType, Trade } from '@/lib/types'

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

export default function BotDetailPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const botId = params.id as string

  const [bot, setBot] = useState<BotType | null>(null)
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadBotData = async () => {
    if (!user || !botId) return

    setLoading(true)
    setError(null)

    try {
      const [botData, tradesData] = await Promise.all([
        getBot(botId),
        getTradesByBot(botId, { limit: 10 })
      ])

      setBot(botData)
      setTrades(tradesData.data || [])
    } catch (err) {
      console.error('Error loading bot data:', err)
      setError(err instanceof Error ? err.message : 'Failed to load bot data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBotData()
  }, [user, botId])

  const handleStartBot = async () => {
    if (!bot) return
    setActionLoading('start')
    try {
      const updatedBot = await startBot(bot.id)
      setBot(updatedBot)
    } catch (error) {
      console.error('Error starting bot:', error)
      alert('Failed to start bot: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setActionLoading(null)
    }
  }

  const handleStopBot = async () => {
    if (!bot) return
    setActionLoading('stop')
    try {
      const updatedBot = await stopBot(bot.id)
      setBot(updatedBot)
    } catch (error) {
      console.error('Error stopping bot:', error)
      alert('Failed to stop bot: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setActionLoading(null)
    }
  }

  const handleDeleteBot = async () => {
    if (!bot) return
    
    if (!confirm('Are you sure you want to delete this bot? This action cannot be undone.')) {
      return
    }
    
    setActionLoading('delete')
    try {
      await deleteBot(bot.id)
      router.push('/bots')
    } catch (error) {
      console.error('Error deleting bot:', error)
      alert('Failed to delete bot: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setActionLoading(null)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-50 border-green-200'
      case 'paused': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'error': return 'text-red-600 bg-red-50 border-red-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getExchangeColor = (exchange: string) => {
    return exchange === 'binance' ? 'text-yellow-600' : 'text-blue-600'
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
        <div className="flex items-center space-x-4 mb-6">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </button>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading bot</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={loadBotData}
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

  if (!bot) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center space-x-4 mb-6">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </button>
        </div>
        <div className="text-center py-12">
          <Bot className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Bot not found</h3>
          <p className="mt-1 text-sm text-gray-500">The bot you're looking for doesn't exist or you don't have access to it.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </button>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">{bot.name}</h2>
            <p className="text-gray-600">{bot.strategy} • {bot.pair}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </button>
          <button className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </button>
        </div>
      </div>

      {/* Status and Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(bot.status)}`}>
              {bot.status.toUpperCase()}
            </span>
            <div className="flex items-center space-x-2">
              <span className={`text-sm font-medium ${getExchangeColor(bot.exchange)}`}>
                {bot.exchange.toUpperCase()}
              </span>
              <span className="text-gray-400">•</span>
              <span className="text-sm text-gray-600">{bot.timeframe}</span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {bot.status === 'active' ? (
              <button
                onClick={handleStopBot}
                disabled={actionLoading === 'stop'}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
              >
                {actionLoading === 'stop' ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <Square className="h-4 w-4 mr-2" />
                )}
                Stop Bot
              </button>
            ) : (
              <button
                onClick={handleStartBot}
                disabled={actionLoading === 'start'}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
              >
                {actionLoading === 'start' ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                Start Bot
              </button>
            )}
            <button
              onClick={handleDeleteBot}
              disabled={actionLoading === 'delete'}
              className="inline-flex items-center px-4 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 bg-white hover:bg-red-50 disabled:opacity-50"
            >
              {actionLoading === 'delete' ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600 mr-2"></div>
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Delete
            </button>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {bot.profit_loss >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-green-500" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-500" />
                )}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total P&L</dt>
                  <dd className={`text-lg font-medium ${bot.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(bot.profit_loss)}
                  </dd>
                  <dt className="text-xs text-gray-500">{formatPercentage(bot.profit_loss_percentage)}</dt>
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
                  <dt className="text-sm font-medium text-gray-500 truncate">Current Balance</dt>
                  <dd className="text-lg font-medium text-gray-900">{formatCurrency(bot.current_balance)}</dd>
                  <dt className="text-xs text-gray-500">of {formatCurrency(bot.base_balance)}</dt>
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
                  <dt className="text-sm font-medium text-gray-500 truncate">Last Trade</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {bot.last_trade_at ? formatRelativeTime(bot.last_trade_at) : 'No trades'}
                  </dd>
                  <dt className="text-xs text-gray-500">{bot.pair}</dt>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Calendar className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Created</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {new Date(bot.created_at).toLocaleDateString()}
                  </dd>
                  <dt className="text-xs text-gray-500">{formatRelativeTime(bot.created_at)}</dt>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Bot Configuration */}
        <div className="col-span-3 bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Configuration</h3>
            <div className="mt-6 space-y-4">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Strategy:</span>
                <span className="text-sm font-medium text-gray-900">{bot.strategy}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Exchange:</span>
                <span className={`text-sm font-medium ${getExchangeColor(bot.exchange)}`}>
                  {bot.exchange.toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Pair:</span>
                <span className="text-sm font-medium text-gray-900">{bot.pair}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Timeframe:</span>
                <span className="text-sm font-medium text-gray-900">{bot.timeframe}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Initial Balance:</span>
                <span className="text-sm font-medium text-gray-900">{formatCurrency(bot.base_balance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Current Balance:</span>
                <span className="text-sm font-medium text-gray-900">{formatCurrency(bot.current_balance)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Trades */}
        <div className="col-span-4 bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Recent Trades</h3>
            <div className="mt-6 space-y-4">
              {trades.length > 0 ? (
                trades.map((trade) => (
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
                      {trade.profit_loss !== null && (
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
                ))
              ) : (
                <div className="text-center py-8">
                  <Activity className="mx-auto h-8 w-8 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-500">No trades yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
