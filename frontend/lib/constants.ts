// Constants for NusaNexus NoFOMO

export const APP_NAME = 'NusaNexus NoFOMO';
export const APP_DESCRIPTION = 'AI-Powered Crypto Trading Bot SaaS Platform';

// API Endpoints
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    PROFILE: '/api/v1/auth/profile',
  },
  BOTS: {
    LIST: '/api/v1/bots',
    CREATE: '/api/v1/bots',
    GET: (id: string) => `/api/v1/bots/${id}`,
    UPDATE: (id: string) => `/api/v1/bots/${id}`,
    DELETE: (id: string) => `/api/v1/bots/${id}`,
    START: (id: string) => `/api/v1/bots/${id}/start`,
    STOP: (id: string) => `/api/v1/bots/${id}/stop`,
    PAUSE: (id: string) => `/api/v1/bots/${id}/pause`,
    STATS: (id: string) => `/api/v1/bots/${id}/stats`,
    TRADES: (id: string) => `/api/v1/bots/${id}/trades`,
  },
  STRATEGIES: {
    LIST: '/api/v1/strategies',
    CREATE: '/api/v1/strategies',
    GET: (id: string) => `/api/v1/strategies/${id}`,
    UPDATE: (id: string) => `/api/v1/strategies/${id}`,
    DELETE: (id: string) => `/api/v1/strategies/${id}`,
    DUPLICATE: (id: string) => `/api/v1/strategies/${id}/duplicate`,
    BACKTEST: (id: string) => `/api/v1/strategies/${id}/backtest`,
    PUBLIC: '/api/v1/strategies/public',
  },
  TRADES: {
    LIST: '/api/v1/trades',
    GET: (id: string) => `/api/v1/trades/${id}`,
    EXPORT: '/api/v1/trades/export',
  },
  AI: {
    GENERATE: '/api/v1/ai/generate',
    CHAT: '/api/v1/ai/chat',
    STRATEGIES: '/api/v1/ai/strategies',
    OPTIMIZE: '/api/v1/ai/optimize',
  },
  DASHBOARD: {
    STATS: '/api/v1/dashboard/stats',
    ACTIVITY: '/api/v1/dashboard/activity',
    CHARTS: '/api/v1/dashboard/charts',
  },
  SETTINGS: {
    USER: '/api/v1/settings/user',
    EXCHANGE: '/api/v1/settings/exchange',
    NOTIFICATIONS: '/api/v1/settings/notifications',
  },
};

// Supabase Configuration
export const SUPABASE_CONFIG = {
  URL: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
  TABLES: {
    USERS: 'users',
    BOTS: 'bots',
    TRADES: 'trades',
    STRATEGIES: 'strategies',
    USER_PREFERENCES: 'user_preferences',
    NOTIFICATIONS: 'notifications',
    CHAT_MESSAGES: 'chat_messages',
  },
  REALTIME_CHANNELS: {
    BOTS: 'bots',
    TRADES: 'trades',
    NOTIFICATIONS: 'notifications',
    CHAT: 'chat',
  },
};

// Exchange Configuration
export const EXCHANGES = {
  BINANCE: {
    name: 'binance',
    display_name: 'Binance',
    icon: '/icons/binance.svg',
    color: '#F3BA2F',
    pairs: ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT', 'UNI/USDT'],
    timeframes: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'],
  },
  BYBIT: {
    name: 'bybit',
    display_name: 'Bybit',
    icon: '/icons/bybit.svg',
    color: '#00A9E0',
    pairs: ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT', 'UNI/USDT'],
    timeframes: ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '1w', '1M'],
  },
} as const;

// Bot Status Colors
export const BOT_STATUS_COLORS = {
  active: {
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
    dot: 'bg-green-500',
  },
  stopped: {
    color: 'text-gray-600',
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    dot: 'bg-gray-400',
  },
  paused: {
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    dot: 'bg-yellow-500',
  },
  error: {
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
    dot: 'bg-red-500',
  },
} as const;

// Trade Side Colors
export const TRADE_SIDE_COLORS = {
  buy: {
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
  },
  sell: {
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
  },
} as const;

// Notification Types
export const NOTIFICATION_TYPES = {
  info: {
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    icon: 'Info',
  },
  success: {
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: 'CheckCircle',
  },
  warning: {
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    icon: 'AlertTriangle',
  },
  error: {
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: 'XCircle',
  },
} as const;

// Chart Colors
export const CHART_COLORS = {
  primary: '#3B82F6',
  secondary: '#10B981',
  accent: '#F59E0B',
  danger: '#EF4444',
  warning: '#F97316',
  info: '#06B6D4',
  purple: '#8B5CF6',
  pink: '#EC4899',
  indigo: '#6366F1',
} as const;

// Time intervals for auto-refresh
export const REFRESH_INTERVALS = {
  OFF: 0,
  SLOW: 30000, // 30 seconds
  NORMAL: 15000, // 15 seconds
  FAST: 5000, // 5 seconds
  ULTRA: 2000, // 2 seconds
} as const;

// Default values
export const DEFAULTS = {
  STAKE_AMOUNT: 100,
  MAX_TRADES: 10,
  STOP_LOSS: 2, // 2%
  TAKE_PROFIT: 4, // 4%
  ROI: 1, // 1%
  REFRESH_INTERVAL: REFRESH_INTERVALS.NORMAL,
  DEFAULT_THEME: 'light' as const,
  DEFAULT_EXCHANGE: 'binance' as const,
  DEFAULT_TIMEFRAME: '1h' as const,
} as const;

// Validation Rules
export const VALIDATION = {
  BOT_NAME: {
    min: 3,
    max: 50,
    pattern: /^[a-zA-Z0-9\s\-_]+$/,
  },
  STRATEGY_NAME: {
    min: 3,
    max: 100,
    pattern: /^[a-zA-Z0-9\s\-_]+$/,
  },
  EMAIL: {
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  },
  PASSWORD: {
    min: 8,
    max: 100,
  },
  STAKE_AMOUNT: {
    min: 10,
    max: 10000,
  },
  STOP_LOSS: {
    min: 0.1,
    max: 20,
  },
  TAKE_PROFIT: {
    min: 0.1,
    max: 50,
  },
} as const;

// Routes
export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  BOTS: '/bots',
  BOT_DETAIL: (id: string) => `/bots/${id}`,
  STRATEGIES: '/strategies',
  STRATEGY_DETAIL: (id: string) => `/strategies/${id}`,
  AI_BUILDER: '/ai-builder',
  TRADES: '/trades',
  SETTINGS: '/settings',
  PROFILE: '/profile',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  CHAT: '/chat',
  MARKET: '/market',
  ANALYTICS: '/analytics',
} as const;

// Navigation items
export const NAVIGATION_ITEMS = [
  {
    name: 'Dashboard',
    href: ROUTES.DASHBOARD,
    icon: 'LayoutDashboard',
    description: 'Overview of all bots and performance',
  },
  {
    name: 'My Bots',
    href: ROUTES.BOTS,
    icon: 'Bot',
    description: 'Manage your trading bots',
  },
  {
    name: 'AI Builder',
    href: ROUTES.AI_BUILDER,
    icon: 'Brain',
    description: 'Generate strategies with AI',
  },
  {
    name: 'Strategies',
    href: ROUTES.STRATEGIES,
    icon: 'TrendingUp',
    description: 'Strategy marketplace and management',
  },
  {
    name: 'Trades',
    href: ROUTES.TRADES,
    icon: 'BarChart3',
    description: 'Trade history and analytics',
  },
  {
    name: 'Chat',
    href: ROUTES.CHAT,
    icon: 'MessageCircle',
    description: 'AI Assistant Chat',
  },
  {
    name: 'Settings',
    href: ROUTES.SETTINGS,
    icon: 'Settings',
    description: 'App settings and preferences',
  },
  {
    name: 'Profile',
    href: ROUTES.PROFILE,
    icon: 'User',
    description: 'Account management',
  },
] as const;