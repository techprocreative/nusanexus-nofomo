import { Trade } from '@/lib/types'
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

// Get all trades for the current user
export async function getTrades(params: {
  page?: number
  limit?: number
  bot_id?: string
  pair?: string
  status?: string
} = {}): Promise<{ data: Trade[]; total: number; page: number; limit: number; has_next: boolean; has_prev: boolean }> {
  try {
    const searchParams = new URLSearchParams()
    if (params.page) searchParams.append('page', params.page.toString())
    if (params.limit) searchParams.append('limit', params.limit.toString())
    if (params.bot_id) searchParams.append('bot_id', params.bot_id)
    if (params.pair) searchParams.append('pair', params.pair)
    if (params.status) searchParams.append('status', params.status)
    
    const queryString = searchParams.toString()
    const endpoint = `/v1/trades/${queryString ? `?${queryString}` : ''}`
    
    const response = await apiRequest<{ data: Trade[]; total: number; page: number; limit: number; has_next: boolean; has_prev: boolean }>(endpoint)
    return response
  } catch (error) {
    console.error('Error fetching trades:', error)
    throw error
  }
}

// Get a specific trade by ID
export async function getTrade(tradeId: string): Promise<Trade> {
  try {
    const response = await apiRequest<Trade>(`/v1/trades/${tradeId}`)
    return response
  } catch (error) {
    console.error(`Error fetching trade ${tradeId}:`, error)
    throw error
  }
}

// Get recent trades
export async function getRecentTrades(limit: number = 10): Promise<Trade[]> {
  try {
    const response = await apiRequest<Trade[]>(`/v1/trades/recent?limit=${limit}`)
    return response
  } catch (error) {
    console.error('Error fetching recent trades:', error)
    return []
  }
}

// Get trades for a specific bot
export async function getTradesByBot(botId: string, params: {
  page?: number
  limit?: number
  status?: string
} = {}): Promise<{ data: Trade[]; total: number; page: number; limit: number; has_next: boolean; has_prev: boolean }> {
  try {
    const searchParams = new URLSearchParams()
    if (params.page) searchParams.append('page', params.page.toString())
    if (params.limit) searchParams.append('limit', params.limit.toString())
    if (params.status) searchParams.append('status', params.status)
    
    const queryString = searchParams.toString()
    const endpoint = `/v1/trades/bot/${botId}${queryString ? `?${queryString}` : ''}`
    
    const response = await apiRequest<{ data: Trade[]; total: number; page: number; limit: number; has_next: boolean; has_prev: boolean }>(endpoint)
    return response
  } catch (error) {
    console.error(`Error fetching trades for bot ${botId}:`, error)
    throw error
  }
}
