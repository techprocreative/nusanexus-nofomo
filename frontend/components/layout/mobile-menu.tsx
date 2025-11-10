'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { X, LayoutDashboard, Bot, Brain, TrendingUp, BarChart3, MessageCircle, Settings, User, LogOut } from 'lucide-react'
import { useAuth } from '@/components/providers/auth-provider'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'My Bots', href: '/bots', icon: Bot },
  { name: 'AI Builder', href: '/ai-builder', icon: Brain },
  { name: 'Strategies', href: '/strategies', icon: TrendingUp },
  { name: 'Trades', href: '/trades', icon: BarChart3 },
  { name: 'Chat', href: '/chat', icon: MessageCircle },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Profile', href: '/profile', icon: User },
]

interface MobileMenuProps {
  open: boolean
  setOpen: (open: boolean) => void
}

export function MobileMenu({ open, setOpen }: MobileMenuProps) {
  const pathname = usePathname()
  const { signOut } = useAuth()

  // Lock body scroll when menu is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [open])

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-gray-900/80 z-40 lg:hidden"
        onClick={() => setOpen(false)}
      />

      {/* Slide-out menu */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50 w-full max-w-xs bg-white shadow-xl
          transform transition-transform duration-300 ease-in-out lg:hidden
          ${open ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Close button */}
        <div className="absolute right-0 top-0 -mr-12 pt-2">
          <button
            type="button"
            className="ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
            onClick={() => setOpen(false)}
          >
            <span className="sr-only">Close sidebar</span>
            <X className="h-6 w-6 text-white" aria-hidden="true" />
          </button>
        </div>

        {/* Menu content */}
        <div className="flex h-full flex-col overflow-y-auto py-6 px-6">
          {/* Logo */}
          <div className="flex h-16 shrink-0 items-center mb-6">
            <span className="text-2xl font-bold text-blue-600">NoFOMO</span>
          </div>

          {/* Navigation */}
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-7">
              <li>
                <ul role="list" className="-mx-2 space-y-1">
                  {navigation.map((item) => {
                    const isActive = pathname === item.href
                    return (
                      <li key={item.name}>
                        <Link
                          href={item.href}
                          onClick={() => setOpen(false)}
                          className={`
                            group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold
                            ${isActive
                              ? 'bg-blue-50 text-blue-600'
                              : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                            }
                          `}
                        >
                          <item.icon className="h-6 w-6 shrink-0" aria-hidden="true" />
                          {item.name}
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              </li>

              {/* Sign out button */}
              <li className="mt-auto">
                <button
                  onClick={() => {
                    signOut()
                    setOpen(false)
                  }}
                  className="group -mx-2 flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-700 hover:bg-gray-50 hover:text-blue-600 w-full"
                >
                  <LogOut className="h-6 w-6 shrink-0" aria-hidden="true" />
                  Sign out
                </button>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </>
  )
}
