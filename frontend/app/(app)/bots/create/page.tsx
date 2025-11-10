'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Save, Bot, Settings } from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'
import { createBot } from '@/lib/api/bots'
import { CreateBotForm, Bot } from '@/lib/types'

const POPULAR_PAIRS = [
  'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
  'DOT/USDT', 'MATIC/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT'
]

const POPULAR_TIMEFRAMES = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' }
]

const EXCHANGES = [
  { value: 'binance', label: 'Binance' },
  { value: 'bybit', label: 'Bybit' }
]

const STRATEGIES = [
  { value: 'custom_scalping', label: 'Custom Scalping v2.1' },
  { value: 'trend_following', label: 'Trend Following AI' },
  { value: 'swing_trading', label: 'Swing Trading Bot' },
  { value: 'grid_trading', label: 'Grid Trading v3' },
  { value: 'momentum', label: 'Momentum Strategy' },
  { value: 'mean_reversion', label: 'Mean Reversion' },
  { value: 'dca', label: 'Dollar Cost Averaging' }
]

export default function CreateBotPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState<CreateBotForm>({
    name: '',
    strategy: '',
    exchange: 'binance',
    pair: 'BTC/USDT',
    timeframe: '15m',
    config: {
      stake_amount: 100,
      stop_loss: 2.0,
      take_profit: 4.0,
      max_trades: 10,
      roi: 1.0,
      strategy_params: {
        rsi_period: 14,
        rsi_oversold: 30,
        rsi_overbought: 70,
        macd_fast: 12,
        macd_slow: 26,
        macd_signal: 9
      }
    }
  })

  const handleInputChange = (field: string, value: any) => {
    if (field.startsWith('config.')) {
      const configField = field.replace('config.', '')
      setFormData(prev => ({
        ...prev,
        config: {
          ...prev.config,
          [configField]: value
        }
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }))
    }
  }

  const handleConfigParamChange = (param: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      config: {
        ...prev.config,
        strategy_params: {
          ...prev.config.strategy_params,
          [param]: value
        }
      }
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user) {
      setError('You must be logged in to create a bot')
      return
    }

    if (!formData.name.trim()) {
      setError('Bot name is required')
      return
    }

    if (!formData.strategy) {
      setError('Please select a strategy')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const newBot = await createBot(formData)
      router.push(`/bots/${newBot.id}`)
    } catch (err) {
      console.error('Error creating bot:', err)
      setError(err instanceof Error ? err.message : 'Failed to create bot')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <button
          onClick={() => router.back()}
          className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Create New Bot</h2>
          <p className="text-gray-600">Set up your trading bot configuration</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Bot className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>
          </div>
          
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                Bot Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="My BTC Trading Bot"
                required
              />
            </div>

            <div>
              <label htmlFor="exchange" className="block text-sm font-medium text-gray-700">
                Exchange *
              </label>
              <select
                id="exchange"
                value={formData.exchange}
                onChange={(e) => handleInputChange('exchange', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                required
              >
                {EXCHANGES.map(exchange => (
                  <option key={exchange.value} value={exchange.value}>
                    {exchange.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="pair" className="block text-sm font-medium text-gray-700">
                Trading Pair *
              </label>
              <select
                id="pair"
                value={formData.pair}
                onChange={(e) => handleInputChange('pair', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                required
              >
                {POPULAR_PAIRS.map(pair => (
                  <option key={pair} value={pair}>
                    {pair}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="timeframe" className="block text-sm font-medium text-gray-700">
                Timeframe *
              </label>
              <select
                id="timeframe"
                value={formData.timeframe}
                onChange={(e) => handleInputChange('timeframe', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                required
              >
                {POPULAR_TIMEFRAMES.map(timeframe => (
                  <option key={timeframe.value} value={timeframe.value}>
                    {timeframe.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="sm:col-span-2">
              <label htmlFor="strategy" className="block text-sm font-medium text-gray-700">
                Strategy *
              </label>
              <select
                id="strategy"
                value={formData.strategy}
                onChange={(e) => handleInputChange('strategy', e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select a strategy</option>
                {STRATEGIES.map(strategy => (
                  <option key={strategy.value} value={strategy.value}>
                    {strategy.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Trading Configuration */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Settings className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Trading Configuration</h3>
          </div>
          
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="stake_amount" className="block text-sm font-medium text-gray-700">
                Initial Balance (USD) *
              </label>
              <input
                type="number"
                id="stake_amount"
                value={formData.config.stake_amount}
                onChange={(e) => handleInputChange('config.stake_amount', parseFloat(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="10"
                step="0.01"
                required
              />
            </div>

            <div>
              <label htmlFor="stop_loss" className="block text-sm font-medium text-gray-700">
                Stop Loss (%)
              </label>
              <input
                type="number"
                id="stop_loss"
                value={formData.config.stop_loss}
                onChange={(e) => handleInputChange('config.stop_loss', parseFloat(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="0.1"
                max="10"
                step="0.1"
              />
            </div>

            <div>
              <label htmlFor="take_profit" className="block text-sm font-medium text-gray-700">
                Take Profit (%)
              </label>
              <input
                type="number"
                id="take_profit"
                value={formData.config.take_profit}
                onChange={(e) => handleInputChange('config.take_profit', parseFloat(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="0.1"
                max="20"
                step="0.1"
              />
            </div>

            <div>
              <label htmlFor="max_trades" className="block text-sm font-medium text-gray-700">
                Max Concurrent Trades
              </label>
              <input
                type="number"
                id="max_trades"
                value={formData.config.max_trades}
                onChange={(e) => handleInputChange('config.max_trades', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="1"
                max="50"
              />
            </div>

            <div>
              <label htmlFor="roi" className="block text-sm font-medium text-gray-700">
                Target ROI (%)
              </label>
              <input
                type="number"
                id="roi"
                value={formData.config.roi}
                onChange={(e) => handleInputChange('config.roi', parseFloat(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="0.1"
                max="10"
                step="0.1"
              />
            </div>
          </div>
        </div>

        {/* Strategy Parameters */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Strategy Parameters</h3>
          
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="rsi_period" className="block text-sm font-medium text-gray-700">
                RSI Period
              </label>
              <input
                type="number"
                id="rsi_period"
                value={formData.config.strategy_params.rsi_period}
                onChange={(e) => handleConfigParamChange('rsi_period', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="5"
                max="50"
              />
            </div>

            <div>
              <label htmlFor="rsi_oversold" className="block text-sm font-medium text-gray-700">
                RSI Oversold Level
              </label>
              <input
                type="number"
                id="rsi_oversold"
                value={formData.config.strategy_params.rsi_oversold}
                onChange={(e) => handleConfigParamChange('rsi_oversold', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="10"
                max="40"
              />
            </div>

            <div>
              <label htmlFor="rsi_overbought" className="block text-sm font-medium text-gray-700">
                RSI Overbought Level
              </label>
              <input
                type="number"
                id="rsi_overbought"
                value={formData.config.strategy_params.rsi_overbought}
                onChange={(e) => handleConfigParamChange('rsi_overbought', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="60"
                max="90"
              />
            </div>

            <div>
              <label htmlFor="macd_fast" className="block text-sm font-medium text-gray-700">
                MACD Fast Period
              </label>
              <input
                type="number"
                id="macd_fast"
                value={formData.config.strategy_params.macd_fast}
                onChange={(e) => handleConfigParamChange('macd_fast', parseInt(e.target.value))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                min="5"
                max="20"
              />
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Create Bot
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
