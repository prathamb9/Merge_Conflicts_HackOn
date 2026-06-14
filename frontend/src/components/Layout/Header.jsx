import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ShoppingCart, MessageSquare, Package, LogOut, Zap, User as UserIcon, ClipboardList, CalendarDays, Users } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useCart } from '../../context/CartContext'

export default function Header() {
  const { user, logout } = useAuth()
  const { itemCount, setIsOpen } = useCart()
  const location = useLocation()

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/chat" className="flex items-center gap-2.5 flex-shrink-0 group">
          <div className="w-9 h-9 bg-green-gradient rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform shadow-green">
            <Zap size={18} className="text-white" fill="white" />
          </div>
          <div className="hidden sm:block">
            <span className="text-xl font-bold gradient-text">QuickBot</span>
            <p className="text-xs text-gray-400 -mt-0.5">AI Shopping</p>
          </div>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1">
          {[
            { path: '/chat', label: 'AI Chat', icon: MessageSquare },
            { path: '/products', label: 'Products', icon: Package },
            { path: '/meal-plan', label: 'Meal Plan', icon: CalendarDays },
            { path: '/group', label: 'Group', icon: Users },
            { path: '/orders', label: 'Orders', icon: ClipboardList },
            { path: '/account', label: 'Account', icon: UserIcon },
          ].map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                location.pathname === path
                  ? 'bg-green-50 text-green-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Icon size={16} />
              <span className="hidden lg:block">{label}</span>
            </Link>
          ))}
        </nav>

        {/* Right actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Cart */}
          <button
            id="cart-toggle"
            onClick={() => setIsOpen(true)}
            className="relative flex items-center gap-2 px-3 py-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-xl font-semibold text-sm transition-all btn-press"
          >
            <ShoppingCart size={17} />
            <span className="hidden sm:block">Cart</span>
            {itemCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 min-w-[20px] h-5 px-1 bg-green-gradient rounded-full text-white text-xs flex items-center justify-center font-bold animate-bounce-subtle">
                {itemCount > 9 ? '9+' : itemCount}
              </span>
            )}
          </button>

          {/* User avatar + logout */}
          <div className="flex items-center gap-2 pl-2 border-l border-gray-100">
            <div className="w-8 h-8 bg-green-gradient rounded-full flex items-center justify-center text-white text-sm font-bold select-none">
              {user?.username?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span className="hidden md:block text-sm font-medium text-gray-700 max-w-[100px] truncate">
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
