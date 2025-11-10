import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Bot, TrendingUp, Brain, Zap } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Bot className="h-8 w-8 text-blue-600" />
              <h1 className="ml-2 text-2xl font-bold text-gray-900">NusaNexus NoFOMO</h1>
            </div>
            <nav className="hidden md:flex space-x-8">
              <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
                Dashboard
              </Link>
              <Link href="/bots" className="text-gray-600 hover:text-gray-900">
                My Bots
              </Link>
              <Link href="/strategies" className="text-gray-600 hover:text-gray-900">
                Strategies
              </Link>
              <Link href="/ai-builder" className="text-gray-600 hover:text-gray-900">
                AI Builder
              </Link>
            </nav>
            <div className="flex space-x-4">
              <Button variant="outline">Sign In</Button>
              <Button>Get Started</Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            AI-Powered Crypto Trading Bot
            <span className="text-blue-600"> SaaS Platform</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Platform Trading Bot AI berbasis Freqtrade dengan support Binance, Bybit. 
            Generate strategi trading dengan AI, jalankan bot otomatis, dan pantau performa real-time.
          </p>
          <div className="flex justify-center space-x-4">
            <Button size="lg" className="px-8">
              Start Trading Now
            </Button>
            <Button variant="outline" size="lg" className="px-8">
              Watch Demo
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <Card>
            <CardHeader>
              <Bot className="h-10 w-10 text-blue-600 mb-2" />
              <CardTitle>Automated Trading</CardTitle>
              <CardDescription>
                Jalankan bot trading otomatis dengan Freqtrade engine yang powerful
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <Brain className="h-10 w-10 text-green-600 mb-2" />
              <CardTitle>AI Strategy Generator</CardTitle>
              <CardDescription>
                Generate strategi trading personalizado menggunakan LLM AI
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <TrendingUp className="h-10 w-10 text-purple-600 mb-2" />
              <CardTitle>Multi-Exchange Support</CardTitle>
              <CardDescription>
                Support Binance dan Bybit dengan integrasi yang seamless
              </CardDescription>
            </CardHeader>
          </Card>
          
          <Card>
            <CardHeader>
              <Zap className="h-10 w-10 text-yellow-600 mb-2" />
              <CardTitle>Real-time Monitoring</CardTitle>
              <CardDescription>
                Monitor performa bot dan trading dengan dashboard real-time
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Architecture Overview */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-center mb-12">Platform Architecture</h2>
          <div className="bg-white rounded-lg shadow-lg p-8">
            <pre className="text-sm text-gray-600 overflow-x-auto">
{`graph TD
  U[User Dashboard (Next.js)] -->|Auth| A[Supabase Auth]
  U -->|API Calls| B[FastAPI Backend]
  B -->|Read/Write| C[Supabase DB]
  B -->|Queue Job| D[Redis Queue]
  D -->|Exec Task| E[Bot Runner (Freqtrade Engine)]
  E -->|Fetch Data| F[Exchange (Binance/Bybit)]
  E -->|Log Trades| C
  B -->|Invoke| G[AI Engine (LLM)]
  G -->|Generate| H[Strategy Templates]`}
            </pre>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-20 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Start Trading?</h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands of traders using NusaNexus NoFOMO untuk maximize profit mereka
          </p>
          <Button size="lg" className="px-12">
            Get Started Free
          </Button>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center mb-4">
                <Bot className="h-6 w-6" />
                <span className="ml-2 text-lg font-bold">NusaNexus NoFOMO</span>
              </div>
              <p className="text-gray-400">
                AI-Powered Crypto Trading Bot SaaS Platform
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Product</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/features">Features</Link></li>
                <li><Link href="/pricing">Pricing</Link></li>
                <li><Link href="/api">API</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Company</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/about">About</Link></li>
                <li><Link href="/blog">Blog</Link></li>
                <li><Link href="/careers">Careers</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/docs">Documentation</Link></li>
                <li><Link href="/contact">Contact</Link></li>
                <li><Link href="/status">Status</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 NusaNexus NoFOMO. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}