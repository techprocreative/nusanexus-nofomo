import { Bot, CreateBotForm } from '@/lib/types'
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

// Get all bots for the current user
export async function getBots(): Promise<Bot[]> {
  try {
    const response = await apiRequest<Bot[]>('/v1/bots/')
    return response
  } catch (error) {
    console.error('Error fetching bots:', error)
    throw error
  }
}

// Get a specific bot by ID
export async function getBot(botId: string): Promise<Bot> {
  try {
    const response = await apiRequest<Bot>(`/v1/bots/${botId}`)
    return response
  } catch (error) {
    console.error(`Error fetching bot ${botId}:`, error)
    throw error
  }
}

// Create a new bot
export async function createBot(botData: CreateBotForm): Promise<Bot> {
  try {
    const response = await apiRequest<Bot>('/v1/bots/', {
      method: 'POST',
      body: JSON.stringify(botData),
    })
    return response
  } catch (error) {
    console.error('Error creating bot:', error)
    throw error
  }
}

// Update a bot
export async function updateBot(botId: string, botData: Partial<Bot>): Promise<Bot> {
  try {
    const response = await apiRequest<Bot>(`/v1/bots/${botId}`, {
      method: 'PUT',
      body: JSON.stringify(botData),
    })
    return response
  } catch (error) {
    console.error(`Error updating bot ${botId}:`, error)
    throw error
  }
}

// Delete a bot
export async function deleteBot(botId: string): Promise<void> {
  try {
    await apiRequest<void>(`/v1/bots/${botId}`, {
      method: 'DELETE',
    })
  } catch (error) {
    console.error(`Error deleting bot ${botId}:`, error)
    throw error
  }
}

// Start a bot
export async function startBot(botId: string): Promise<Bot> {
  try {
    const response = await apiRequest<Bot>(`/v1/bots/${botId}/start`, {
      method: 'POST',
    })
    return response
  } catch (error) {
    console.error(`Error starting bot ${botId}:`, error)
    throw error
  }
}

// Stop a bot
export async function stopBot(botId: string): Promise<Bot> {
  try {
    const response = await apiRequest<Bot>(`/v1/bots/${botId}/stop`, {
      method: 'POST',
    })
    return response
  } catch (error) {
    console.error(`Error stopping bot ${botId}:`, error)
    throw error
  }
}

// Get bot status
export async function getBotStatus(botId: string): Promise<any> {
  try {
    const response = await apiRequest<any>(`/v1/bots/${botId}/status`)
    return response
  } catch (error) {
    console.error(`Error fetching bot status ${botId}:`, error)
    throw error
  }
}
