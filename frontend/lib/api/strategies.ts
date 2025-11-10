import { Strategy, CreateStrategyForm } from '@/lib/types'
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

// Get all strategies for the current user
export async function getStrategies(): Promise<Strategy[]> {
  try {
    const response = await apiRequest<Strategy[]>('/v1/strategies/')
    return response
  } catch (error) {
    console.error('Error fetching strategies:', error)
    throw error
  }
}

// Get a specific strategy by ID
export async function getStrategy(strategyId: string): Promise<Strategy> {
  try {
    const response = await apiRequest<Strategy>(`/v1/strategies/${strategyId}`)
    return response
  } catch (error) {
    console.error(`Error fetching strategy ${strategyId}:`, error)
    throw error
  }
}

// Create a new strategy
export async function createStrategy(strategyData: CreateStrategyForm): Promise<Strategy> {
  try {
    const response = await apiRequest<Strategy>('/v1/strategies/', {
      method: 'POST',
      body: JSON.stringify(strategyData),
    })
    return response
  } catch (error) {
    console.error('Error creating strategy:', error)
    throw error
  }
}

// Update a strategy
export async function updateStrategy(strategyId: string, strategyData: Partial<Strategy>): Promise<Strategy> {
  try {
    const response = await apiRequest<Strategy>(`/v1/strategies/${strategyId}`, {
      method: 'PUT',
      body: JSON.stringify(strategyData),
    })
    return response
  } catch (error) {
    console.error(`Error updating strategy ${strategyId}:`, error)
    throw error
  }
}

// Delete a strategy
export async function deleteStrategy(strategyId: string): Promise<void> {
  try {
    await apiRequest<void>(`/v1/strategies/${strategyId}`, {
      method: 'DELETE',
    })
  } catch (error) {
    console.error(`Error deleting strategy ${strategyId}:`, error)
    throw error
  }
}

// Get public strategies
export async function getPublicStrategies(): Promise<Strategy[]> {
  try {
    const response = await apiRequest<Strategy[]>('/v1/strategies/public')
    return response
  } catch (error) {
    console.error('Error fetching public strategies:', error)
    throw error
  }
}
