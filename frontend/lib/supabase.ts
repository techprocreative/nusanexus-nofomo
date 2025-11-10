import { createClient } from '@supabase/supabase-js'
import { SUPABASE_CONFIG } from './constants'

export const supabase = createClient(
  SUPABASE_CONFIG.URL,
  SUPABASE_CONFIG.ANON_KEY,
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  }
)

// Database types
export type Database = {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          full_name: string | null
          avatar_url: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          full_name?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          full_name?: string | null
          avatar_url?: string | null
          updated_at?: string
        }
      }
      bots: {
        Row: {
          id: string
          user_id: string
          name: string
          strategy: string
          status: 'active' | 'stopped' | 'paused' | 'error'
          exchange: 'binance' | 'bybit'
          pair: string
          timeframe: string
          base_balance: number
          current_balance: number
          profit_loss: number
          profit_loss_percentage: number
          created_at: string
          updated_at: string
          last_trade_at: string | null
          config: any
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          strategy: string
          status?: 'active' | 'stopped' | 'paused' | 'error'
          exchange: 'binance' | 'bybit'
          pair: string
          timeframe: string
          base_balance: number
          current_balance?: number
          profit_loss?: number
          profit_loss_percentage?: number
          created_at?: string
          updated_at?: string
          last_trade_at?: string | null
          config?: any
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          strategy?: string
          status?: 'active' | 'stopped' | 'paused' | 'error'
          exchange?: 'binance' | 'bybit'
          pair?: string
          timeframe?: string
          base_balance?: number
          current_balance?: number
          profit_loss?: number
          profit_loss_percentage?: number
          updated_at?: string
          last_trade_at?: string | null
          config?: any
        }
      }
      trades: {
        Row: {
          id: string
          bot_id: string
          user_id: string
          pair: string
          side: 'buy' | 'sell'
          type: 'entry' | 'exit'
          amount: number
          price: number
          fee: number
          profit_loss: number | null
          status: 'pending' | 'filled' | 'cancelled' | 'failed'
          exchange_order_id: string | null
          created_at: string
          filled_at: string | null
        }
        Insert: {
          id?: string
          bot_id: string
          user_id: string
          pair: string
          side: 'buy' | 'sell'
          type: 'entry' | 'exit'
          amount: number
          price: number
          fee: number
          profit_loss?: number | null
          status?: 'pending' | 'filled' | 'cancelled' | 'failed'
          exchange_order_id?: string | null
          created_at?: string
          filled_at?: string | null
        }
        Update: {
          id?: string
          bot_id?: string
          user_id?: string
          pair?: string
          side?: 'buy' | 'sell'
          type?: 'entry' | 'exit'
          amount?: number
          price?: number
          fee?: number
          profit_loss?: number | null
          status?: 'pending' | 'filled' | 'cancelled' | 'failed'
          exchange_order_id?: string | null
          filled_at?: string | null
        }
      }
      strategies: {
        Row: {
          id: string
          user_id: string
          name: string
          description: string | null
          strategy_code: string
          timeframe: string
          exchange: string
          pair: string
          is_public: boolean
          is_ai_generated: boolean
          performance: any | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          description?: string | null
          strategy_code: string
          timeframe: string
          exchange: string
          pair: string
          is_public?: boolean
          is_ai_generated?: boolean
          performance?: any | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          description?: string | null
          strategy_code?: string
          timeframe?: string
          exchange?: string
          pair?: string
          is_public?: boolean
          is_ai_generated?: boolean
          performance?: any | null
          updated_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}