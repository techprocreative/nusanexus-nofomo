'use client'

import { useState, useEffect } from 'react'
import { Bot, Brain, Send, Sparkles, Code, Play, Save, Download } from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata?: {
    strategy_id?: string
    suggestion_type?: string
  }
}

interface StrategyTemplate {
  id: string
  name: string
  description: string
  category: string
  code: string
  performance?: {
    win_rate: number
    profit_factor: number
    total_return: number
  }
}

export default function AIBuilderPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [strategyCode, setStrategyCode] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState<StrategyTemplate | null>(null)
  const [templates, setTemplates] = useState<StrategyTemplate[]>([])
  const { user } = useAuth()

  useEffect(() => {
    // Load strategy templates
    const mockTemplates: StrategyTemplate[] = [
      {
        id: '1',
        name: 'RSI Mean Reversion',
        description: 'Uses RSI oversold/overbought levels for entries',
        category: 'Mean Reversion',
        code: `def populate_indicators(dataframe, metadata):
    dataframe["rsi"] = ta.RSI(dataframe["close"], timeperiod=14)
    return dataframe

def populate_entry_trend(dataframe, metadata):
    conditions = []
    conditions.append(dataframe["rsi"] < 30)
    return conditions

def populate_exit_trend(dataframe, metadata):
    conditions = []
    conditions.append(dataframe["rsi"] > 70)
    return conditions`,
        performance: {
          win_rate: 68.5,
          profit_factor: 1.45,
          total_return: 12.3
        }
      },
      {
        id: '2',
        name: 'MACD Crossover',
        description: 'MACD signal line crossover strategy',
        category: 'Trend Following',
        code: `def populate_indicators(dataframe, metadata):
    macd = ta.MACD(dataframe["close"])
    dataframe["macd"] = macd["macd"]
    dataframe["macdsignal"] = macd["macdsignal"]
    dataframe["macdhist"] = macd["macdhist"]
    return dataframe

def populate_entry_trend(dataframe, metadata):
    conditions = []
    conditions.append(dataframe["macd"] > dataframe["macdsignal"])
    return conditions

def populate_exit_trend(dataframe, metadata):
    conditions = []
    conditions.append(dataframe["macd"] < dataframe["macdsignal"])
    return conditions`,
        performance: {
          win_rate: 62.1,
          profit_factor: 1.28,
          total_return: 8.7
        }
      },
      {
        id: '3',
        name: 'Bollinger Bands',
        description: 'Price bounce between Bollinger Bands',
        category: 'Momentum',
        code: `def populate_indicators(dataframe, metadata):
    bollinger = ta.BBANDS(dataframe["close"], timeperiod=20)
    dataframe["bb_lowerband"] = bollinger["lowerband"]
    dataframe["bb_upperband"] = bollinger["upperband"]
    dataframe["bb_middleband"] = bollinger["middleband"]
    return dataframe

def populate_entry_trend(dataframe, metadata):
    conditions = []
    conditions.append(dataframe["close"] < dataframe["bb_lowerband"])
    return conditions

def populate_exit_trend(dataframe, metadata):
    conditions = []
    conditions.append(dataframe["close"] > dataframe["bb_upperband"])
    return conditions`,
        performance: {
          win_rate: 71.2,
          profit_factor: 1.52,
          total_return: 15.8
        }
      }
    ]
    
    setTemplates(mockTemplates)
    
    // Add initial message
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content: 'Hello! I\'m your AI trading strategy assistant. I can help you create custom trading strategies using technical indicators. You can ask me to generate strategies for specific pairs, timeframes, or trading styles. What would you like to build today?',
        timestamp: new Date().toISOString()
      }
    ])
  }, [])

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        {
          content: `I understand you want to ${inputMessage.toLowerCase()}. Based on current market conditions, I recommend using RSI combined with MACD for optimal entry and exit signals. Here's a strategy I've generated for you:`,
          suggestion_type: 'strategy_generation'
        },
        {
          content: `Great question! For that approach, I suggest using Bollinger Bands with volume confirmation. This combination has shown good results in volatile markets. Let me create the code for you.`,
          suggestion_type: 'optimization'
        },
        {
          content: `That's an interesting strategy concept. I've analyzed similar approaches and found that adding a stop-loss at 2% and take-profit at 4% can improve risk management. Would you like me to implement these parameters?`,
          suggestion_type: 'risk_management'
        }
      ]
      
      const randomResponse = responses[Math.floor(Math.random() * responses.length)]
      
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: randomResponse.content,
        timestamp: new Date().toISOString(),
        metadata: {
          suggestion_type: randomResponse.suggestion_type
        }
      }
      
      setMessages(prev => [...prev, assistantMessage])
      setLoading(false)
    }, 2000)
  }

  const handleTemplateSelect = (template: StrategyTemplate) => {
    setSelectedTemplate(template)
    setStrategyCode(template.code)
  }

  const handleSaveStrategy = () => {
    if (!strategyCode.trim()) return
    // Implementation for saving strategy
    console.log('Saving strategy...', strategyCode)
  }

  const handleTestStrategy = () => {
    if (!strategyCode.trim()) return
    // Implementation for testing strategy
    console.log('Testing strategy...', strategyCode)
  }

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">AI Strategy Builder</h2>
          <p className="text-gray-600">Generate and customize trading strategies with AI assistance</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleTestStrategy}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <Play className="h-4 w-4 mr-2" />
            Test
          </button>
          <button
            onClick={handleSaveStrategy}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Save className="h-4 w-4 mr-2" />
            Save
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Interface */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg h-96">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <Brain className="h-5 w-5 text-blue-600" />
                <h3 className="text-lg font-medium">AI Assistant</h3>
              </div>
            </div>
            
            <div className="flex flex-col h-80">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      {message.metadata?.suggestion_type && (
                        <div className="mt-2 flex items-center text-xs opacity-75">
                          <Sparkles className="h-3 w-3 mr-1" />
                          {message.metadata.suggestion_type}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg">
                      <div className="flex space-x-2">
                        <div className="animate-pulse w-2 h-2 bg-gray-400 rounded-full"></div>
                        <div className="animate-pulse w-2 h-2 bg-gray-400 rounded-full animation-delay-200"></div>
                        <div className="animate-pulse w-2 h-2 bg-gray-400 rounded-full animation-delay-400"></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="p-4 border-t border-gray-200">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Ask me to create a strategy, optimize parameters, or explain indicators..."
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={loading}
                    className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Strategy Templates */}
        <div>
          <div className="bg-white shadow rounded-lg">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <Code className="h-5 w-5 text-green-600" />
                <h3 className="text-lg font-medium">Templates</h3>
              </div>
            </div>
            <div className="p-4 space-y-3">
              {templates.map((template) => (
                <div
                  key={template.id}
                  onClick={() => handleTemplateSelect(template)}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedTemplate?.id === template.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-900">{template.name}</h4>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {template.category}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mb-2">{template.description}</p>
                  {template.performance && (
                    <div className="text-xs space-y-1">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Win Rate:</span>
                        <span className="text-green-600 font-medium">{template.performance.win_rate}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Profit:</span>
                        <span className="text-blue-600 font-medium">{template.performance.total_return}%</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Code Editor */}
      <div className="bg-white shadow rounded-lg">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bot className="h-5 w-5 text-purple-600" />
              <h3 className="text-lg font-medium">Strategy Code</h3>
            </div>
            <div className="flex space-x-2">
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <Download className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
        <div className="p-4">
          <textarea
            value={strategyCode}
            onChange={(e) => setStrategyCode(e.target.value)}
            className="w-full h-64 font-mono text-sm border border-gray-300 rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Your strategy code will appear here..."
          />
        </div>
      </div>
    </div>
  )
}