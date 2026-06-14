import React, { useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ShoppingCart, MessageSquare, Package, LogOut, Zap, User as UserIcon, ClipboardList, CalendarDays, Users } from 'lucide-react'
import gsap from 'gsap'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'

const NAV = [
  { path: '/chat', label: 'AI Chat', icon: MessageSquare },
  { path: '/products', label: 'Products', icon: Package },
  { path: '/meal-plan', label: 'Meal Plan', icon: CalendarDays },
  { path: '/group', label: 'Group', icon: Users },
  { path: '/orders', label: 'Orders', icon: ClipboardList },
  { path: '/account', label: 'Account', icon: UserIcon },
]

export default function Header() {
  const { user, logout } = useAuth()
  const { itemCount, setIsOpen } = useCart()
  const location = useLocation()
  const headerRef = useRef(null)

  useEffect(() => {
    if (!headerRef.current) return
    gsap.fromTo(
      headerRef.current,
      { y: -70, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }
    )
  }, [])

  return (
    <header ref={headerRef} className="sticky top-0 z-40 px-3 pt-3">
      <div className="max-w-7xl mx-auto glass rounded-2xl px-4 h-16 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/chat" className="flex items-center gap-2.5 flex-shrink-0 group">
          <div className="relative w-10 h-10 bg-green-gradient rounded-xl flex items-center justify-center shadow-green group-hover:scale-105 transition-transform overflow-hidden btn-premium">
            <Zap size={19} className="text-white relative z-10" fill="white" />
            <div className="absolute inset-0 animate-glow-pulse rounded-xl" />
          </div>
          <div className="hidden sm:block leading-tight">
            <span className="text-xl font-bold gradient-text font-display tracking-tight">QuickBot</span>
            <p className="text-[10px] text-gray-500 -mt-1 tracking-[0.18em] uppercase font-semibold">Premium AI Shopping</p>
          </div>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-0.5 glass-panel rounded-xl p-1">
          {NAV.map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path || location.pathname.startsWith(path + '/')
            return (
              <Link
                key={path}
                to={path}
                className={`relative flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                  active
                    ? 'bg-green-gradient text-white shadow-green'
                    : 'text-gray-600 hover:bg-white/70 hover:text-gray-900'
                }`}
              >
                <Icon size={16} />
                <span className="hidden lg:block">{label}</span>
              </Link>
            )
          })}
        </nav>

        {/* Right actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            id="cart-toggle"
            onClick={() => setIsOpen(true)}
            className="relative flex items-center gap-2 px-3.5 py-2.5 bg-white/70 hover:bg-white text-green-700 rounded-xl font-bold text-sm transition-all btn-press lift border border-white/70"
          >
            <ShoppingCart size={17} />
            <span className="hidden sm:block">Cart</span>
            {itemCount > 0 && (
              <span className="absolute -top-2 -right-2 min-w-[20px] h-5 px-1 bg-gold-gradient rounded-full text-white text-xs flex items-center justify-center font-bold shadow-glow-gold animate-bounce-subtle">
                {itemCount > 9 ? '9+' : itemCount}
              </span>
            )}
          </button>

          <div className="flex items-center gap-2 pl-2 border-l border-white/50">
            <div className="w-9 h-9 bg-green-gradient rounded-full flex items-center justify-center text-white text-sm font-bold select-none shadow-green ring-2 ring-white/60">
              {user?.username?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span className="hidden md:block text-sm font-semibold text-gray-700 max-w-[100px] truncate">
              {user?.username}
            </span>
            <button
              id="logout-btn"
              onClick={logout}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="Sign out"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
