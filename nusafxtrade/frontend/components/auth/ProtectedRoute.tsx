'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '../providers/auth-provider'
import { LoadingSpinner } from '../ui/loading-spinner'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: string
  requireSubscription?: string
  fallback?: React.ReactNode
}

export function ProtectedRoute({ 
  children, 
  requiredRole, 
  requireSubscription,
  fallback 
}: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [isAuthorized, setIsAuthorized] = useState(false)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const checkAuthorization = async () => {
      if (loading) return

      if (!user) {
        // Redirect to login with return URL
        const returnUrl = encodeURIComponent(pathname)
        router.push(`/login?returnUrl=${returnUrl}`)
        return
      }

      try {
        // Check role-based access
        if (requiredRole && user.user_metadata?.role !== requiredRole) {
          router.push('/unauthorized')
          return
        }

        // Check subscription-based access
        if (requireSubscription) {
          const subscriptionLevel = user.user_metadata?.subscription_plan || 'free'
          const planHierarchy: Record<string, number> = { free: 0, pro: 1, enterprise: 2 }
          const userLevel = planHierarchy[subscriptionLevel] ?? 0
          const requiredLevel = planHierarchy[requireSubscription] ?? 0

          if (userLevel < requiredLevel) {
            router.push('/subscription-required')
            return
          }
        }

        setIsAuthorized(true)
      } catch (error) {
        console.error('Authorization check failed:', error)
        router.push('/error')
      } finally {
        setChecking(false)
      }
    }

    checkAuthorization()
  }, [user, loading, requiredRole, requireSubscription, router, pathname])

  if (loading || checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthorized) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h2>
          <p className="text-gray-600 mb-6">
            You don't have permission to access this page.
          </p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

export function useRequireAuth() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      const currentPath = window.location.pathname
      const returnUrl = encodeURIComponent(currentPath)
      router.push(`/login?returnUrl=${returnUrl}`)
    }
  }, [user, loading, router])

  return { user, loading }
}

export function useRequireRole(requiredRole: string) {
  const { user, loading } = useAuth()
  const [isAuthorized, setIsAuthorized] = useState(false)

  useEffect(() => {
    if (!loading) {
      const userRole = user?.user_metadata?.role
      setIsAuthorized(userRole === requiredRole)
    }
  }, [user, loading, requiredRole])

  return { isAuthorized, loading, user }
}

export function useRequireSubscription(requiredPlan: string) {
  const { user, loading } = useAuth()
  const [isAuthorized, setIsAuthorized] = useState(false)

  useEffect(() => {
    if (!loading) {
      const userPlan = user?.user_metadata?.subscription_plan || 'free'
      const planHierarchy = { free: 0, pro: 1, enterprise: 2 }
      const userLevel = planHierarchy[userPlan] || 0
      const requiredLevel = planHierarchy[requiredPlan] || 0
      setIsAuthorized(userLevel >= requiredLevel)
    }
  }, [user, loading, requiredPlan])

  return { isAuthorized, loading, user, userPlan: user?.user_metadata?.subscription_plan }
}

export function RoleGuard({ 
  children, 
  allowedRoles, 
  fallback = null 
}: { 
  children: React.ReactNode
  allowedRoles: string[]
  fallback?: React.ReactNode 
}) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner />
      </div>
    )
  }

  if (!user) {
    return null
  }

  const userRole = user.user_metadata?.role
  if (!userRole || !allowedRoles.includes(userRole)) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

export function SubscriptionGuard({ 
  children, 
  requiredPlan,
  fallback = null 
}: { 
  children: React.ReactNode
  requiredPlan: string
  fallback?: React.ReactNode 
}) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <LoadingSpinner />
      </div>
    )
  }

  if (!user) {
    return null
  }

  const userPlan = user.user_metadata?.subscription_plan || 'free'
  const planHierarchy = { free: 0, pro: 1, enterprise: 2 }
  const userLevel = planHierarchy[userPlan] || 0
  const requiredLevel = planHierarchy[requiredPlan] || 0

  if (userLevel < requiredLevel) {
    return <>{fallback}</>
  }

  return <>{children}</>
}