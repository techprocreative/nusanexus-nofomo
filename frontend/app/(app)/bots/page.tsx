'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, Play, Pause, Square, Settings, Trash2, Bot, AlertCircle, RefreshCw } from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { getBots, startBot, stopBot, deleteBot, updateBot } from '@/lib/api/bots'
import { Bot as BotType } from '@/lib/types'

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

export default function BotsPage() {
  const router = useRouter()
  const [bots, setBots] = useState<BotType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [actionLoading, setActionLoading] = useState<{ [key: string]: boolean }>({})
  const { user } = useAuth()

  const loadBots = async (showRefreshing = false) => {
    if (!user) return
    
    if (showRefreshing) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }
    
    setError(null)
    
    try {
      const botsData = await getBots()
      setBots(botsData || [])
    } catch (err) {
      console.error('Error loading bots:', err)
      setError(err instanceof Error ? err.message : 'Failed to load bots')
      setBots([])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadBots()
  }, [user])

  const handleRefresh = () => {
    loadBots(true)
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

  const handleStartBot = async (botId: string) => {
    setActionLoading(prev => ({ ...prev, [botId]: true }))
    try {
      const updatedBot = await startBot(botId)
      setBots(bots.map(bot => bot.id === botId ? updatedBot : bot))
    } catch (error) {
      console.error('Error starting bot:', error)
      alert('Failed to start bot: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setActionLoading(prev => ({ ...prev, [botId]: false }))
    }
  }

  const handleStopBot = async (botId: string) => {
    setActionLoading(prev => ({ ...prev, [botId]: true }))
    try {
      const updatedBot = await stopBot(botId)
      setBots(bots.map(bot => bot.id === botId ? updatedBot : bot))
    } catch (error) {
      console.error('Error stopping bot:', error)
      alert('Failed to stop bot: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setActionLoading(prev => ({ ...prev, [botId]: false }))
    }
  }

  const handlePauseBot = async (botId: string) => {
    setActionLoading(prev => ({ ...prev, [botId]: true }))
    try {
      // Since there's no pauseBot API function, we'll use updateBot to set status to 'paused'
      const updatedBot = await updateBot(botId, { status: 'paused' })
      setBots(bots.map(bot => bot.id === botId ? updatedBot : bot))
    } catch (error) {
      console.error('Error pausing bot:', error)
      alert('Failed to pause bot: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setActionLoading(prev => ({ ...prev, [botId]: false }))
    }
  }

  const handleDeleteBot = async (botId: string) => {
    if (!confirm('Are you sure you want to delete this bot? This action cannot be undone.')) {
      return
    }
    
    setActionLoading(prev => ({ ...prev, [botId]: true }))
    try {
      await deleteBot(botId)
      setBots(bots.filter(bot => bot.id !== botId))
    } catch (error) {
      console.error('Error deleting bot:', error)
      alert('Failed to delete bot: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setActionLoading(prev => ({ ...prev, [botId]: false }))
    }
  }

  const handleBotCardClick = (botId: string) => {
    router.push(`/bots/${botId}`)
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
              <h3 className="text-sm font-medium text-red-800">Error loading bots</h3>
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">My Bots</h2>
          <p className="text-gray-600">Manage and monitor your trading bots</p>
        </div>
        <div className="flex items-center space-x-2">
          <button 
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button 
            onClick={() => router.push('/bots/create')}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Bot
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {bots.map((bot) => (
              <div 
                key={bot.id} 
                className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleBotCardClick(bot.id)}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <Bot className="h-6 w-6 text-blue-600" />
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{bot.name}</h3>
                      <p className="text-sm text-gray-500">{bot.strategy}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(bot.status)}`}>
                    {bot.status}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Pair:</span>
                    <span className={`text-sm font-medium ${getExchangeColor(bot.exchange)}`}>
                      {bot.pair}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Exchange:</span>
                    <span className="text-sm font-medium text-gray-900 capitalize">
                      {bot.exchange}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Timeframe:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {bot.timeframe}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Balance:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatCurrency(bot.current_balance)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">P&L:</span>
                    <span className={`text-sm font-medium ${bot.profit_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(bot.profit_loss)} ({formatPercentage(bot.profit_loss_percentage)})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Last Trade:</span>
                    <span className="text-sm text-gray-900">
                      {bot.last_trade_at ? formatRelativeTime(bot.last_trade_at) : 'No trades'}
                    </span>
                  </div>
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <div className="flex space-x-2">
                    {bot.status === 'active' ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handlePauseBot(bot.id)
                        }}
                        className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-md"
                        title="Pause Bot"
                      >
                        <Pause className="h-4 w-4" />
                      </button>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleStartBot(bot.id)
                        }}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-md"
                        title="Start Bot"
                      >
                        <Play className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleStopBot(bot.id)
                      }}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                      title="Stop Bot"
                    >
                      <Square className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => e.stopPropagation()}
                      className="p-2 text-gray-600 hover:bg-gray-50 rounded-md"
                      title="Bot Settings"
                    >
                      <Settings className="h-4 w-4" />
                    </button>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteBot(bot.id)
                    }}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                    title="Delete Bot"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {bots.length === 0 && (
            <div className="text-center py-12">
              <Bot className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No bots</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating your first trading bot.</p>
              <div className="mt-6">
                <button 
                  onClick={() => router.push('/bots/create')}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Bot
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}