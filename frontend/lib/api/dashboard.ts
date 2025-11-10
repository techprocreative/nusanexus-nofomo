import { DashboardStats, Trade } from '@/lib/types'
import { supabase } from '@/lib/supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Get auth token for API requests
async function getAuthToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token || null
}

// Generic API request function
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = await getAuthToken()
  
  if (!token) {
    throw new Error('No authentication token found')
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// Get dashboard statistics for the current user
export async function getDashboardStats(): Promise<DashboardStats> {
  try {
    const response = await apiRequest<DashboardStats>('/v1/dashboard/stats')
    return response
  } catch (error) {
    console.error('Error fetching dashboard stats:', error)
    // Return default stats if API fails
    return {
      total_bots: 0,
      active_bots: 0,
      total_profit_loss: 0,
      total_profit_loss_percentage: 0,
      total_trades: 0,
      win_rate: 0,
      today_profit_loss: 0,
    }
  }
}

// Get recent bots for dashboard
export async function getRecentBots(): Promise<any[]> {
  try {
    const response = await apiRequest<any[]>('/v1/bots/recent')
    return response
  } catch (error) {
    console.error('Error fetching recent bots:', error)
    return []
  }
}

// Get recent trades for dashboard
export async function getRecentTrades(limit: number = 10): Promise<Trade[]> {
  try {
    const response = await apiRequest<Trade[]>(`/v1/trades/recent?limit=${limit}`)
    return response
  } catch (error) {
    console.error('Error fetching recent trades:', error)
    return []
  }
}

// Get user's trading pairs performance
export async function getTradingPairs(): Promise<any[]> {
  try {
    const response = await apiRequest<any[]>('/v1/dashboard/trading-pairs')
    return response
  } catch (error) {
    console.error('Error fetching trading pairs:', error)
    return []
  }
}

// Get bot performance summary
export async function getBotPerformance(): Promise<any[]> {
  try {
    const response = await apiRequest<any[]>('/v1/dashboard/bot-performance')
    return response
  } catch (error) {
    console.error('Error fetching bot performance:', error)
    return []
  }
}
