'use client'

import { useEffect, useRef, useCallback, useState } from 'react'
import { useAuth } from '../components/providers/auth-provider'
import { supabase } from '../lib/supabase'
import { toast } from 'react-hot-toast'

export interface RealtimeMessage {
  message_id: string
  type: string
  data: any
  user_id?: string
  bot_id?: string
  trade_id?: string
  strategy_id?: string
  priority: number
  timestamp: string
}

export interface ConnectionStatus {
  connected: boolean
  connectionId?: string
  reconnectAttempts: number
  lastActivity?: string
}

export interface BotUpdate {
  bot_id: string
  status: string
  current_balance?: number
  profit_loss?: number
  profit_loss_percentage?: number
  message?: string
}

export interface TradeUpdate {
  id: string
  bot_id: string
  pair: string
  side: 'buy' | 'sell'
  type: 'entry' | 'exit'
  amount: number
  price: number
  status: string
  profit_loss?: number
}

export interface StrategyUpdate {
  strategy_id: string
  status: 'generating' | 'completed' | 'error'
  progress: number
  message?: string
  result?: any
}

export interface AIChatUpdate {
  session_id: string
  message: string
  response?: string
  confidence?: number
  is_complete?: boolean
}

export interface MetricsUpdate {
  total_bots: number
  active_bots: number
  total_profit: number
  win_rate: number
  total_trades: number
}

export interface AlertData {
  id: string
  level: 'info' | 'warning' | 'error' | 'critical'
  title: string
  message: string
  data?: any
  timestamp: string
}

export function useRealtime() {
  const { user } = useAuth()
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
    reconnectAttempts: 0
  })
  const [botUpdates, setBotUpdates] = useState<Map<string, BotUpdate>>(new Map())
  const [tradeUpdates, setTradeUpdates] = useState<Map<string, TradeUpdate>>(new Map())
  const [strategyUpdates, setStrategyUpdates] = useState<Map<string, StrategyUpdate>>(new Map())
  const [chatUpdates, setChatUpdates] = useState<Map<string, AIChatUpdate[]>>(new Map())
  const [metricsUpdates, setMetricsUpdates] = useState<MetricsUpdate | null>(null)
  const [alerts, setAlerts] = useState<AlertData[]>([])

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const heartbeatIntervalRef = useRef<NodeJS.Timeout>()
  const subscriptionsRef = useRef<Set<string>>(new Set())
  const supabaseChannelsRef = useRef<any[]>([])

  // WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    if (typeof window === 'undefined') return ''
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}/api/v1/ws`
  }, [])

  // Initialize WebSocket connection
  const connect = useCallback(async () => {
    if (!user) return

    try {
      const wsUrl = getWebSocketUrl()
      if (!wsUrl) return

      // Close existing connection
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }

      const accessToken = (await supabase.auth.getSession()).data.session?.access_token
      if (!accessToken) {
        throw new Error('No access token available')
      }

      const connectionId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const ws = new WebSocket(`${wsUrl}?token=${accessToken}&connection_id=${connectionId}`)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnectionStatus({
          connected: true,
          connectionId,
          reconnectAttempts: 0,
          lastActivity: new Date().toISOString()
        })

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30000)

        // Subscribe to user events
        ws.send(JSON.stringify({
          type: 'subscribe',
          subscription: `user:${user.id}`
        }))
      }

      ws.onmessage = (event) => {
        try {
          const message: RealtimeMessage = JSON.parse(event.data)
          handleRealtimeMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setConnectionStatus(prev => ({
          ...prev,
          connected: false,
          lastActivity: new Date().toISOString()
        }))

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current)
        }

        // Auto-reconnect
        if (event.code !== 1000 && event.code !== 1001) {
          const delay = Math.min(1000 * Math.pow(2, connectionStatus.reconnectAttempts), 30000)
          setConnectionStatus(prev => ({ ...prev, reconnectAttempts: prev.reconnectAttempts + 1 }))

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        toast.error('Real-time connection error')
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
      toast.error('Failed to establish real-time connection')
    }
  }, [user, connectionStatus.reconnectAttempts, getWebSocketUrl])

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }
    setConnectionStatus({ connected: false, reconnectAttempts: 0 })
  }, [])

  // Handle real-time messages
  const handleRealtimeMessage = useCallback((message: RealtimeMessage) => {
    setConnectionStatus(prev => ({ ...prev, lastActivity: message.timestamp }))

    switch (message.type) {
      case 'bot_status':
        setBotUpdates(prev => {
          const newMap = new Map(prev)
          newMap.set(message.bot_id!, message.data)
          return newMap
        })

        // Show toast for status changes
        const status = message.data.status
        if (['started', 'stopped', 'paused', 'error'].includes(status)) {
          toast.success(`Bot ${message.data.bot_id} ${status}`)
        }
        break

      case 'trade_executed':
        setTradeUpdates(prev => {
          const newMap = new Map(prev)
          newMap.set(message.trade_id!, message.data)
          return newMap
        })
        toast.success(`Trade executed: ${message.data.pair} ${message.data.side}`)
        break

      case 'strategy_generation':
        setStrategyUpdates(prev => {
          const newMap = new Map(prev)
          newMap.set(message.strategy_id!, message.data)
          return newMap
        })
        break

      case 'ai_chat':
        setChatUpdates(prev => {
          const newMap = new Map(prev)
          const sessionChats = newMap.get(message.data.session_id) || []
          newMap.set(message.data.session_id, [...sessionChats, message.data])
          return newMap
        })
        break

      case 'metrics_update':
        setMetricsUpdates(message.data)
        break

      case 'alert':
        setAlerts(prev => {
          const newAlerts = [message.data, ...prev].slice(0, 50) // Keep last 50 alerts
          return newAlerts
        })

        // Show toast for high priority alerts
        if (message.priority >= 4) {
          if (message.data.level === 'error') {
            toast.error(message.data.title)
          } else {
            toast(message.data.title, { icon: '⚠️' })
          }
        }
        break

      case 'heartbeat':
        // Ignore heartbeat messages
        break

      case 'connection_status':
        if (message.data.status === 'connected') {
          console.log('Connection established:', message.data.connection_id)
        }
        break

      default:
        console.log('Unhandled message type:', message.type, message.data)
    }
  }, [])

  // Subscribe to bot updates
  const subscribeToBot = useCallback((botId: string) => {
    subscriptionsRef.current.add(`bot:${botId}`)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        subscription: `bot:${botId}`
      }))
    }

    // Also subscribe to Supabase Realtime
    const channel = supabase
      .channel(`bot-${botId}`)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'bots',
        filter: `id=eq.${botId}`
      }, (payload) => {
        console.log('Bot change received:', payload)
        setBotUpdates(prev => {
          const newMap = new Map(prev)
          if (payload.new && typeof payload.new === 'object') {
            const bot = payload.new as any
            newMap.set(botId, {
              bot_id: botId,
              status: bot.status,
              current_balance: bot.current_balance,
              profit_loss: bot.profit_loss,
              profit_loss_percentage: bot.profit_loss_percentage
            })
          }
          return newMap
        })
      })
      .subscribe()

    supabaseChannelsRef.current.push(channel)
  }, [])

  // Unsubscribe from bot updates
  const unsubscribeFromBot = useCallback((botId: string) => {
    subscriptionsRef.current.delete(`bot:${botId}`)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        subscription: `bot:${botId}`
      }))
    }
  }, [])

  // Subscribe to strategy updates
  const subscribeToStrategy = useCallback((strategyId: string) => {
    subscriptionsRef.current.add(`strategy:${strategyId}`)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        subscription: `strategy:${strategyId}`
      }))
    }
  }, [])

  // Subscribe to trade updates
  const subscribeToTrade = useCallback((tradeId: string) => {
    subscriptionsRef.current.add(`trade:${tradeId}`)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        subscription: `trade:${tradeId}`
      }))
    }

    // Also subscribe to Supabase Realtime
    const channel = supabase
      .channel(`trade-${tradeId}`)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'trades',
        filter: `id=eq.${tradeId}`
      }, (payload) => {
        console.log('Trade change received:', payload)
        setTradeUpdates(prev => {
          const newMap = new Map(prev)
          if (payload.new && typeof payload.new === 'object') {
            const trade = payload.new as any
            newMap.set(tradeId, trade as TradeUpdate)
          }
          return newMap
        })
      })
      .subscribe()

    supabaseChannelsRef.current.push(channel)
  }, [])

  // Send chat message
  const sendChatMessage = useCallback((sessionId: string, message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'ai_chat',
        session_id: sessionId,
        message
      }))
    }
  }, [])

  // Clear alerts
  const clearAlerts = useCallback(() => {
    setAlerts([])
  }, [])

  // Clear specific alert
  const clearAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId))
  }, [])

  // Connect when user is available
  useEffect(() => {
    if (user) {
      connect()

      // Subscribe to general notifications
      const notificationChannel = supabase
        .channel('notifications')
        .on('postgres_changes', {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${user.id}`
        }, (payload) => {
          console.log('New notification:', payload)
          const notification = payload.new
          const notificationType = notification.type || 'info'
          if (notificationType === 'error') {
            toast.error(notification.title || 'New notification')
          } else if (notificationType === 'success') {
            toast.success(notification.title || 'New notification')
          } else {
            toast(notification.title || 'New notification')
          }
        })
        .subscribe()

      supabaseChannelsRef.current.push(notificationChannel)
    } else {
      disconnect()
    }

    return () => {
      disconnect()
      
      // Clean up Supabase channels
      supabaseChannelsRef.current.forEach(channel => {
        supabase.removeChannel(channel)
      })
      supabaseChannelsRef.current = []
    }
  }, [user, connect, disconnect])

  return {
    // Connection status
    connectionStatus,
    connect,
    disconnect,
    
    // Data
    botUpdates,
    tradeUpdates,
    strategyUpdates,
    chatUpdates,
    metricsUpdates,
    alerts,
    
    // Actions
    subscribeToBot,
    unsubscribeFromBot,
    subscribeToStrategy,
    subscribeToTrade,
    sendChatMessage,
    clearAlerts,
    clearAlert,
    
    // Status
    isConnected: connectionStatus.connected,
    isConnecting: connectionStatus.reconnectAttempts > 0 && !connectionStatus.connected
  }
}