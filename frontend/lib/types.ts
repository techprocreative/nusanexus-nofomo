// Core types for NusaNexus NoFOMO

export interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Bot {
  id: string;
  user_id: string;
  name: string;
  strategy: string;
  status: 'active' | 'stopped' | 'paused' | 'error';
  exchange: 'binance' | 'bybit';
  pair: string;
  timeframe: string;
  base_balance: number;
  current_balance: number;
  profit_loss: number;
  profit_loss_percentage: number;
  created_at: string;
  updated_at: string;
  last_trade_at?: string;
  config: BotConfig;
}

export interface BotConfig {
  stake_amount: number;
  stop_loss?: number;
  take_profit?: number;
  max_trades?: number;
  roi?: number;
  strategy_params: Record<string, any>;
}

export interface Trade {
  id: string;
  bot_id: string;
  bot_name?: string; // Populated from bot relation
  user_id: string;
  pair: string;
  side: 'buy' | 'sell';
  type: 'entry' | 'exit';
  amount: number;
  price: number;
  fee: number;
  profit_loss?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'failed';
  exchange_order_id?: string;
  created_at: string;
  filled_at?: string;
}

export interface Strategy {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  strategy_code: string;
  timeframe: string;
  exchange: string;
  pair: string;
  is_public: boolean;
  is_ai_generated: boolean;
  performance?: StrategyPerformance;
  created_at: string;
  updated_at: string;
}

export interface StrategyPerformance {
  total_trades: number;
  win_rate: number;
  profit_loss: number;
  profit_loss_percentage: number;
  sharpe_ratio?: number;
  max_drawdown: number;
  avg_trade_duration: number;
}

export interface MarketData {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    strategy_id?: string;
    bot_id?: string;
    suggestion_type?: string;
  };
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_bots: number;
  active_bots: number;
  total_profit_loss: number;
  total_profit_loss_percentage: number;
  total_trades: number;
  win_rate: number;
  today_profit_loss: number;
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface FilterOptions {
  search?: string;
  status?: string;
  exchange?: string;
  pair?: string;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface ThemeConfig {
  mode: 'light' | 'dark';
  primary_color: string;
  secondary_color: string;
}

export interface UserPreferences {
  theme: ThemeConfig;
  notifications: {
    email: boolean;
    push: boolean;
    trade_alerts: boolean;
    bot_status: boolean;
  };
  default_exchange: string;
  default_timeframe: string;
  auto_refresh_interval: number;
}

export interface BacktestResult {
  id: string;
  strategy_id: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  initial_balance: number;
  final_balance: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  profit_loss: number;
  profit_loss_percentage: number;
  max_drawdown: number;
  sharpe_ratio: number;
  win_rate: number;
  avg_trade_duration: number;
  trades: Trade[];
  equity_curve: EquityPoint[];
}

export interface EquityPoint {
  timestamp: string;
  balance: number;
  drawdown: number;
}

export interface ExchangeConfig {
  name: string;
  display_name: string;
  is_active: boolean;
  supported_pairs: string[];
  required_credentials: string[];
}

export interface OrderBook {
  symbol: string;
  bids: [number, number][];
  asks: [number, number][];
  timestamp: string;
}

export interface KlineData {
  open_time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  close_time: number;
  quote_volume: number;
  trades: number;
  buy_base_volume: number;
  buy_quote_volume: number;
  ignore: string;
}

// WebSocket message types
export interface WSMessage {
  type: 'bot_status' | 'trade_update' | 'market_data' | 'notification' | 'chat';
  data: any;
  timestamp: string;
}

export interface BotStatusUpdate {
  bot_id: string;
  status: Bot['status'];
  current_balance: number;
  profit_loss: number;
  profit_loss_percentage: number;
  last_trade_at?: string;
}

export interface TradeUpdate {
  trade_id: string;
  bot_id: string;
  status: Trade['status'];
  filled_at?: string;
  price?: number;
  amount?: number;
}

// Form types
export interface CreateBotForm {
  name: string;
  strategy: string;
  exchange: Bot['exchange'];
  pair: string;
  timeframe: string;
  config: BotConfig;
}

export interface CreateStrategyForm {
  name: string;
  description?: string;
  strategy_code: string;
  timeframe: string;
  exchange: string;
  pair: string;
  is_public: boolean;
}

export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm {
  email: string;
  password: string;
  confirm_password: string;
  full_name: string;
}

export interface SettingsForm {
  full_name?: string;
  email?: string;
  default_exchange: string;
  default_timeframe: string;
  notifications: UserPreferences['notifications'];
  theme: ThemeConfig;
}