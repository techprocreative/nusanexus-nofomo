import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { Bot, Trade, Strategy } from './types';
import { BOT_STATUS_COLORS, TRADE_SIDE_COLORS } from './constants';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Formatting utilities
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 8,
  }).format(amount);
}

export function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPercentage(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value / 100);
}

export function formatDate(date: string | Date, format: 'short' | 'long' | 'time' = 'short'): string {
  const d = new Date(date);
  
  switch (format) {
    case 'long':
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(d);
    case 'time':
      return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }).format(d);
    default:
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      }).format(d);
  }
}

export function formatRelativeTime(date: string | Date): string {
  const d = new Date(date);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000);
  
  if (diffInSeconds < 60) {
    return 'just now';
  }
  
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  }
  
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours}h ago`;
  }
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return `${diffInDays}d ago`;
  }
  
  return formatDate(d, 'short');
}

// Bot utilities
export function getBotStatusColor(status: Bot['status']) {
  return BOT_STATUS_COLORS[status];
}

export function getBotStatusText(status: Bot['status']): string {
  const statusTexts = {
    active: 'Active',
    stopped: 'Stopped',
    paused: 'Paused',
    error: 'Error',
  };
  return statusTexts[status];
}

export function calculateProfitLossPercentage(current: number, base: number): number {
  if (base === 0) return 0;
  return ((current - base) / base) * 100;
}

export function getProfitLossColor(value: number): string {
  if (value > 0) return 'text-green-600';
  if (value < 0) return 'text-red-600';
  return 'text-gray-600';
}

// Trade utilities
export function getTradeSideColor(side: Trade['side']) {
  return TRADE_SIDE_COLORS[side];
}

export function getTradeSideText(side: Trade['side']): string {
  return side === 'buy' ? 'Buy' : 'Sell';
}

export function getTradeStatusText(status: Trade['status']): string {
  const statusTexts = {
    pending: 'Pending',
    filled: 'Filled',
    cancelled: 'Cancelled',
    failed: 'Failed',
  };
  return statusTexts[status];
}

export function getTradeStatusColor(status: Trade['status']): string {
  const statusColors = {
    pending: 'text-yellow-600',
    filled: 'text-green-600',
    cancelled: 'text-gray-600',
    failed: 'text-red-600',
  };
  return statusColors[status];
}

// Strategy utilities
export function getStrategyLanguage(code: string): string {
  if (code.includes('def ') || code.includes('class ')) {
    return 'python';
  }
  if (code.includes('function ') || code.includes('const ')) {
    return 'javascript';
  }
  if (code.includes('<') && code.includes('>')) {
    return 'html';
  }
  return 'text';
}

export function validateStrategyCode(code: string): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (!code.trim()) {
    errors.push('Strategy code cannot be empty');
  }
  
  if (code.length > 10000) {
    errors.push('Strategy code is too long (max 10,000 characters)');
  }
  
  // Basic Python validation
  if (code.includes('def ')) {
    if (!code.includes('populate_indicators')) {
      errors.push('Strategy must include populate_indicators function');
    }
    if (!code.includes('populate_entry_trend')) {
      errors.push('Strategy must include populate_entry_trend function');
    }
    if (!code.includes('populate_exit_trend')) {
      errors.push('Strategy must include populate_exit_trend function');
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
}

// Validation utilities
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function isValidPassword(password: string): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }
  
  if (password.length > 100) {
    errors.push('Password is too long');
  }
  
  if (!/(?=.*[a-z])/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (!/(?=.*[A-Z])/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (!/(?=.*\d)/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
  };
}

export function isValidBotName(name: string): boolean {
  return /^[a-zA-Z0-9\s\-_]{3,50}$/.test(name);
}

export function isValidPair(pair: string): boolean {
  const pairRegex = /^[A-Z]{2,10}\/[A-Z]{2,10}$/;
  return pairRegex.test(pair);
}

// API utilities
export function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, v.toString()));
      } else {
        searchParams.append(key, value.toString());
      }
    }
  });
  
  return searchParams.toString();
}

export function parseQueryString(queryString: string): Record<string, string | string[]> {
  const params: Record<string, string | string[]> = {};
  const searchParams = new URLSearchParams(queryString);
  
  for (const [key, value] of searchParams.entries()) {
    if (params[key]) {
      if (Array.isArray(params[key])) {
        (params[key] as string[]).push(value);
      } else {
        params[key] = [params[key] as string, value];
      }
    } else {
      params[key] = value;
    }
  }
  
  return params;
}

// Local storage utilities
export function getLocalStorage<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue;
  
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error(`Error reading from localStorage:`, error);
    return defaultValue;
  }
}

export function setLocalStorage<T>(key: string, value: T): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error writing to localStorage:`, error);
  }
}

export function removeLocalStorage(key: string): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing from localStorage:`, error);
  }
}

// Debounce utility
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// Throttle utility
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// Array utilities
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const group = String(item[key]);
    if (!groups[group]) {
      groups[group] = [];
    }
    groups[group].push(item);
    return groups;
  }, {} as Record<string, T[]>);
}

export function sortBy<T>(array: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] {
  return [...array].sort((a, b) => {
    const aVal = a[key];
    const bVal = b[key];
    
    if (aVal < bVal) return order === 'asc' ? -1 : 1;
    if (aVal > bVal) return order === 'asc' ? 1 : -1;
    return 0;
  });
}

export function filterBy<T>(array: T[], filters: Record<keyof T, any>): T[] {
  return array.filter(item => {
    return Object.entries(filters).every(([key, value]) => {
      if (value === undefined || value === null || value === '') return true;
      return item[key as keyof T] === value;
    });
  });
}

// Date utilities
export function isToday(date: string | Date): boolean {
  const d = new Date(date);
  const today = new Date();
  return d.toDateString() === today.toDateString();
}

export function isThisWeek(date: string | Date): boolean {
  const d = new Date(date);
  const now = new Date();
  const startOfWeek = new Date(now.setDate(now.getDate() - now.getDay()));
  const endOfWeek = new Date(now.setDate(now.getDate() - now.getDay() + 6));
  return d >= startOfWeek && d <= endOfWeek;
}

export function isThisMonth(date: string | Date): boolean {
  const d = new Date(date);
  const now = new Date();
  return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
}

// Color utilities
export function getRandomColor(): string {
  const colors = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#06B6D4', '#F97316', '#EC4899', '#6366F1', '#84CC16'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

export function generateColorFromString(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const colors = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#06B6D4', '#F97316', '#EC4899', '#6366F1', '#84CC16'
  ];
  
  return colors[Math.abs(hash) % colors.length];
}

// Error handling utilities
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  return 'An unknown error occurred';
}

export function isApiError(error: any): error is { response?: { data?: { message?: string } } } {
  return error && typeof error === 'object' && 'response' in error;
}

// Device detection
export function isMobile(): boolean {
  if (typeof window === 'undefined') return false;
  return window.innerWidth < 768;
}

export function isTablet(): boolean {
  if (typeof window === 'undefined') return false;
  return window.innerWidth >= 768 && window.innerWidth < 1024;
}

export function isDesktop(): boolean {
  if (typeof window === 'undefined') return true;
  return window.innerWidth >= 1024;
}