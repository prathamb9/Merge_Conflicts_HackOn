import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Package, Loader2, Clock, CheckCircle2, CreditCard, ChevronDown, ChevronUp,
  MapPin, Wallet, Truck, RotateCcw, Star, ShoppingBag,
} from 'lucide-react'
import Header from '../components/Layout/Header'
import { ordersAPI } from '../services/api'

// ── Delivery timeline ─────────────────────────────────────────────────────────
const STAGES = ['Order Placed', 'Confirmed', 'Packed', 'Out for Delivery', 'Delivered']
function DeliveryTimeline({ status, paymentStatus, createdAt }) {
  // mock progress: completed/paid = all 5 stages, pending = stage 0
  const progress = (status === 'completed' && paymentStatus === 'paid') ? 4 : 0
  const placed = createdAt ? new Date(createdAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''

  return (
    <div className="mt-4">
      <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Delivery Status</p>
      <div className="relative flex items-center justify-between">
        {/* Progress line */}
        <div className="absolute left-0 right-0 h-0.5 bg-gray-100 top-3 z-0" />
        <div
          className="absolute left-0 h-0.5 bg-green-500 top-3 z-0 transition-all duration-700"
          style={{ width: `${(progress / (STAGES.length - 1)) * 100}%` }}
        />
        {STAGES.map((stage, i) => (
          <div key={stage} className="flex flex-col items-center gap-1.5 z-10">
            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
              i <= progress ? 'bg-green-500 border-green-500' : 'bg-white border-gray-200'
            }`}>
              {i <= progress && <CheckCircle2 size={14} className="text-white" />}
            </div>
            <span className={`text-[9px] font-semibold text-center max-w-[52px] leading-tight ${i <= progress ? 'text-green-700' : 'text-gray-400'}`}>
              {stage}
            </span>
          </div>
        ))}
      </div>
      {placed && <p className="text-[10px] text-gray-400 mt-2">Ordered on {placed}</p>}
    </div>
  )
}

// ── Single expandable order card ──────────────────────────────────────────────
function OrderCard({ order, navigate }) {
  const [expanded, setExpanded] = useState(false)
  const grand = order.total_amount + order.delivery_charge
  const isPaid = order.payment_status === 'paid'

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      {/* Header — always visible, click to expand */}
      <button
        className="w-full text-left px-5 py-4 flex items-center justify-between gap-3 hover:bg-gray-50/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-3 min-w-0">
          {/* Icon */}
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${isPaid ? 'bg-green-50' : 'bg-amber-50'}`}>
            {isPaid ? <Package size={18} className="text-green-600" /> : <Clock size={18} className="text-amber-600" />}
          </div>
          <div className="min-w-0">
            <p className="text-xs text-gray-400 font-medium">Order #{order.id.slice(0, 8).toUpperCase()}</p>
            <p className="font-bold text-gray-900 text-base mt-0.5">₹{grand.toFixed(0)}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {order.items.length} item{order.items.length !== 1 ? 's' : ''} · {' '}
              {order.items.slice(0, 2).map((i) => i.product_name).join(', ')}
              {order.items.length > 2 ? ` +${order.items.length - 2} more` : ''}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
          <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-1 rounded-full ${isPaid ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
            {isPaid ? <CheckCircle2 size={10} /> : <Clock size={10} />}
            {isPaid ? 'Delivered' : 'Pending'}
          </span>
          {expanded ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
        </div>
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-gray-100 px-5 pb-5 pt-4 space-y-5 animate-fade-in">
          {/* Item list */}
          <div>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Items Ordered</p>
            <div className="space-y-2">
              {order.items.map((it) => (
                <div key={it.product_id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-center flex-shrink-0">
                      <Package size={14} className="text-gray-300" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{it.product_name}</p>
                      <p className="text-xs text-gray-400">Qty: {it.quantity} · ₹{it.price_at_purchase}/each</p>
                    </div>
                  </div>
                  <span className="text-sm font-bold text-gray-900">₹{(it.price_at_purchase * it.quantity).toFixed(0)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Invoice summary */}
          <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Invoice Summary</p>
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between text-gray-600"><span>Subtotal</span><span>₹{order.total_amount.toFixed(0)}</span></div>
              <div className="flex justify-between text-gray-600">
                <span>Delivery</span>
                <span className={order.delivery_charge > 0 ? 'text-gray-600' : 'text-green-600 font-semibold'}>
                  {order.delivery_charge > 0 ? `₹${order.delivery_charge.toFixed(0)}` : 'FREE ✓'}
                </span>
              </div>
              <div className="border-t border-gray-200 pt-2 flex justify-between font-bold text-gray-900">
                <span>Order Total</span><span className="gradient-text text-base">₹{grand.toFixed(0)}</span>
              </div>
            </div>
          </div>

          {/* Delivery & payment info */}
          <div className="grid grid-cols-2 gap-3">
            {order.delivery_address && (
              <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <MapPin size={13} className="text-green-600" />
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Delivery Address</p>
                </div>
                <p className="text-xs text-gray-700 leading-relaxed">{order.delivery_address}</p>
              </div>
            )}
            {order.payment_method && (
              <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Wallet size={13} className="text-green-600" />
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Payment</p>
                </div>
                <p className="text-xs text-gray-700">{order.payment_method}</p>
                <span className={`text-[10px] font-semibold mt-1 inline-block ${isPaid ? 'text-green-600' : 'text-amber-600'}`}>
                  {isPaid ? '✓ Paid' : '⏳ Pending'}
                </span>
              </div>
            )}
          </div>

          {/* Delivery timeline */}
          <DeliveryTimeline status={order.status} paymentStatus={order.payment_status} createdAt={order.created_at} />

          {/* Actions */}
          <div className="flex gap-2 pt-1">
            {!isPaid && (
              <button
                onClick={() => navigate(`/payment/${order.id}`)}
                className="flex-1 py-2.5 bg-green-gradient text-white text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 btn-press shadow-green"
              >
                <CreditCard size={14} /> Complete Payment
              </button>
            )}
            {isPaid && (
              <button
                onClick={() => navigate('/chat')}
                className="flex-1 py-2.5 bg-gray-100 text-gray-700 text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 btn-press hover:bg-gray-200"
              >
                <RotateCcw size={14} /> Buy Again
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default function OrdersPage() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ordersAPI.list()
      .then((res) => setOrders(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const totalSpent = orders.filter((o) => o.payment_status === 'paid').reduce((s, o) => s + o.total_amount + o.delivery_charge, 0)

  return (
    <div className="min-h-screen">
      <Header />
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Page header */}
        <div className="flex items-end justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Orders</h1>
            <p className="text-sm text-gray-500 mt-0.5">{orders.length} order{orders.length !== 1 ? 's' : ''}</p>
          </div>
          {totalSpent > 0 && (
            <div className="text-right hidden sm:block">
              <p className="text-xs text-gray-400">Total spent</p>
              <p className="text-lg font-bold gradient-text">₹{totalSpent.toFixed(0)}</p>
            </div>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="animate-spin text-green-500" size={32} /></div>
        ) : orders.length === 0 ? (
          <div className="bg-white rounded-2xl border border-gray-100 p-10 text-center">
            <ShoppingBag size={40} className="text-gray-200 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No orders yet</p>
            <p className="text-gray-400 text-sm mt-1">Start a conversation with QuickBot to shop!</p>
            <button onClick={() => navigate('/chat')} className="mt-5 px-5 py-2.5 bg-green-gradient text-white text-sm font-semibold rounded-xl shadow-green btn-press">
              Start Shopping
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map((o) => (
              <OrderCard key={o.id} order={o} navigate={navigate} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
