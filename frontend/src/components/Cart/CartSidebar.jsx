import React, { useState } from 'react'
import { X, ShoppingCart, Trash2, Plus, Minus, ShoppingBag, ArrowRight, Truck, PartyPopper, Check } from 'lucide-react'
import { useCart } from '../../context/CartContext'
import { cartAPI } from '../../services/api'

export default function CartSidebar() {
  const { cart, isOpen, setIsOpen, removeFromCart, updateQuantity, clearCart, fetchCart } = useCart()
  const [checkingOut, setCheckingOut] = useState(false)
  const [orderPlaced, setOrderPlaced] = useState(false)

  const FREE_DELIVERY_THRESHOLD = 399
  const DELIVERY_CHARGE = 49
  const gap = Math.max(0, FREE_DELIVERY_THRESHOLD - cart.total)
  const progressPercent = Math.min(100, (cart.total / FREE_DELIVERY_THRESHOLD) * 100)

  const CATEGORY_EMOJI = { snacks: '🍿', beverages: '🥤', dairy: '🥛', breakfast: '🍳', fruits: '🍎', vegetables: '🥦', healthy: '💪', instant: '🍜', bakery: '🥖' }

  const handleCheckout = async () => {
    setCheckingOut(true)
    try {
      await cartAPI.checkout()
      setOrderPlaced(true)
      await fetchCart()
      setTimeout(() => {
        setOrderPlaced(false)
        setIsOpen(false)
      }, 3000)
    } catch (err) {
      console.error('Checkout failed:', err)
      alert(err.response?.data?.detail || 'Checkout failed. Please try again.')
    } finally {
      setCheckingOut(false)
    }
  }

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm animate-fade-in"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Drawer */}
      <div className={`fixed right-0 top-0 h-full w-full max-w-[400px] bg-white z-50 shadow-2xl flex flex-col transform transition-transform duration-300 ease-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-green-gradient rounded-xl flex items-center justify-center">
              <ShoppingCart size={17} className="text-white" />
            </div>
            <div>
              <h2 className="font-bold text-gray-900">Your Cart</h2>
              <p className="text-xs text-gray-400">{cart.items.length} item{cart.items.length !== 1 ? 's' : ''}</p>
            </div>
          </div>
          <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
            <X size={19} className="text-gray-500" />
          </button>
        </div>

        {/* Delivery Threshold Progress */}
        {cart.items.length > 0 && (
          <div className="px-5 py-3 bg-gradient-to-r from-green-50 to-emerald-50 border-b border-green-100">
            {gap > 0 ? (
              <>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <Truck size={13} className="text-green-600" />
                    <span className="text-[11px] font-bold text-green-700">
                      ₹{gap.toFixed(0)} away from FREE delivery!
                    </span>
                  </div>
                  <span className="text-[10px] text-green-600 font-medium">Save ₹{DELIVERY_CHARGE}</span>
                </div>
                <div className="w-full bg-green-200 rounded-full h-1.5">
                  <div
                    className="bg-green-500 h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </>
            ) : (
              <div className="flex items-center gap-1.5">
                <Check size={13} className="text-green-600" />
                <span className="text-[11px] font-bold text-green-700">
                  🎉 FREE delivery unlocked!
                </span>
              </div>
            )}
          </div>
        )}

        {/* Order Placed Success */}
        {orderPlaced && (
          <div className="absolute inset-0 bg-white z-10 flex flex-col items-center justify-center animate-fade-in">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-4 animate-bounce">
              <PartyPopper size={36} className="text-green-600" />
            </div>
            <h3 className="font-bold text-green-700 text-xl">Order Placed! 🎉</h3>
            <p className="text-gray-500 text-sm mt-2">Your order is being prepared</p>
          </div>
        )}

        {/* Items list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {cart.items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-20 text-center">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <ShoppingBag size={30} className="text-gray-300" />
              </div>
              <h3 className="font-semibold text-gray-500 text-lg">Cart is empty</h3>
              <p className="text-gray-400 text-sm mt-1">Chat with QuickBot to add items!</p>
              <button
                onClick={() => setIsOpen(false)}
                className="mt-5 px-5 py-2.5 bg-green-gradient text-white text-sm font-semibold rounded-xl shadow-green btn-press"
              >
                Start Shopping →
              </button>
            </div>
          ) : (
            cart.items.map((item) => (
              <div key={item.product_id} className="flex gap-3 p-3 bg-gray-50 rounded-2xl animate-fade-in">
                {/* Product image */}
                <div className="w-16 h-16 rounded-xl overflow-hidden bg-white flex-shrink-0 border border-gray-100">
                  <img
                    src={item.product?.image_url || ''}
                    alt={item.product?.name || 'Product'}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.parentElement.innerHTML = `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:28px">${CATEGORY_EMOJI[item.product?.category] || '📦'}</div>`
                    }}
                  />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-gray-900 text-sm leading-tight line-clamp-1">{item.product?.name}</h4>
                  <p className="text-xs text-gray-400 mt-0.5">{item.product?.unit}</p>
                  <p className="text-green-600 font-bold text-sm mt-1">₹{item.product?.price}</p>
                </div>

                {/* Controls */}
                <div className="flex flex-col items-end justify-between">
                  <button onClick={() => removeFromCart(item.product_id)} className="p-1 text-gray-300 hover:text-red-400 transition-colors">
                    <Trash2 size={13} />
                  </button>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                      className="w-6 h-6 rounded-lg bg-gray-200 hover:bg-gray-300 flex items-center justify-center transition-colors"
                    >
                      <Minus size={11} />
                    </button>
                    <span className="text-sm font-bold text-gray-900 w-4 text-center">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                      className="w-6 h-6 rounded-lg bg-green-gradient text-white flex items-center justify-center"
                    >
                      <Plus size={11} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {cart.items.length > 0 && (
          <div className="p-4 border-t border-gray-100 bg-white">
            {/* Delivery charge info */}
            <div className="flex items-center justify-between mb-1 px-1 text-xs">
              <span className="text-gray-400">Subtotal</span>
              <span className="text-gray-600 font-medium">₹{cart.total.toFixed(0)}</span>
            </div>
            <div className="flex items-center justify-between mb-2 px-1 text-xs">
              <span className="text-gray-400">Delivery</span>
              <span className={gap > 0 ? 'text-red-500 font-medium' : 'text-green-600 font-bold'}>
                {gap > 0 ? `₹${DELIVERY_CHARGE}` : 'FREE ✓'}
              </span>
            </div>
            <div className="flex items-center justify-between mb-3 px-1">
              <span className="text-gray-500 font-medium">Order Total</span>
              <span className="text-2xl font-bold gradient-text">
                ₹{(cart.total + (gap > 0 ? DELIVERY_CHARGE : 0)).toFixed(0)}
              </span>
            </div>
            <button
              id="checkout-btn"
              onClick={handleCheckout}
              disabled={checkingOut}
              className="w-full py-4 bg-green-gradient text-white font-bold rounded-2xl flex items-center justify-center gap-2 hover:opacity-90 btn-press shadow-green text-sm disabled:opacity-50"
            >
              {checkingOut ? 'Placing Order...' : 'Place Order'} <ArrowRight size={17} />
            </button>
            <button
              onClick={clearCart}
              className="w-full py-2.5 text-gray-400 hover:text-red-400 text-xs mt-2 transition-colors"
            >
              Clear all items
            </button>
          </div>
        )}
      </div>
    </>
  )
}
