import React, { useState } from 'react'
import { Scale, X, Check, ArrowRight, Loader2, TrendingDown, ShoppingCart } from 'lucide-react'
import { bargainAPI } from '../../services/api'
import { useCart } from '../../context/CartContext'

const OUTCOME_STYLE = {
  accept:  { bg: 'bg-green-50',  border: 'border-green-200', text: 'text-green-800', icon: <Check size={16} className="text-green-600" /> },
  counter: { bg: 'bg-amber-50',  border: 'border-amber-200', text: 'text-amber-800', icon: <TrendingDown size={16} className="text-amber-600" /> },
  decline: { bg: 'bg-red-50',    border: 'border-red-200',   text: 'text-red-800',   icon: <X size={16} className="text-red-600" /> },
}

export default function BargainModal({ productIds, productNames, listTotal, onClose }) {
  const { addToCart } = useCart()
  const [offer, setOffer] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [addedAll, setAddedAll] = useState(false)

  const handleHaggle = async () => {
    const amount = parseFloat(offer)
    if (!amount || amount <= 0) { setError('Please enter a valid offer amount'); return }
    setLoading(true)
    setError('')
    try {
      const res = await bargainAPI.haggle(productIds, amount)
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Negotiation failed. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAddAll = async () => {
    const items = result?.counter_items || []
    for (const item of items) {
      if (item?.id) await addToCart(item.id)
    }
    setAddedAll(true)
    setTimeout(() => { setAddedAll(false); onClose() }, 1500)
  }

  const style = result ? (OUTCOME_STYLE[result.outcome] || OUTCOME_STYLE.counter) : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-amber-50 to-orange-50">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500 flex items-center justify-center">
              <Scale size={18} className="text-white" />
            </div>
            <div>
              <h2 className="font-bold text-gray-900 text-sm">Bargain Bot</h2>
              <p className="text-[10px] text-amber-700 font-medium">Make me an offer I can't refuse 😄</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-xl text-gray-400"><X size={18} /></button>
        </div>

        <div className="p-6 space-y-4">
          {/* Products being negotiated */}
          <div className="bg-gray-50 rounded-2xl p-3 border border-gray-100">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1.5">Negotiating for</p>
            <p className="text-sm text-gray-800 font-medium">{productNames}</p>
            <p className="text-xs text-gray-500 mt-1">List price: <span className="font-bold text-gray-700">₹{listTotal?.toFixed(0)}</span></p>
          </div>

          {/* Offer input */}
          {!result && (
            <div>
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-2">Your Offer (₹)</label>
              <div className="flex gap-2">
                <div className="flex-1 flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 focus-within:border-amber-400">
                  <span className="text-gray-400 font-bold text-sm">₹</span>
                  <input
                    type="number"
                    value={offer}
                    onChange={(e) => setOffer(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleHaggle()}
                    placeholder={listTotal ? Math.round(listTotal * 0.9) : ''}
                    className="flex-1 bg-transparent text-sm font-bold text-gray-800 focus:outline-none"
                    autoFocus
                  />
                </div>
                <button
                  onClick={handleHaggle}
                  disabled={loading || !offer}
                  className="px-4 py-2.5 bg-amber-500 text-white text-sm font-bold rounded-xl flex items-center gap-1.5 hover:bg-amber-600 disabled:opacity-50 btn-press"
                >
                  {loading ? <Loader2 size={16} className="animate-spin" /> : <><ArrowRight size={16} /> Offer</>}
                </button>
              </div>
              {error && <p className="text-red-500 text-xs mt-1.5">{error}</p>}
            </div>
          )}

          {/* Result */}
          {result && style && (
            <div className={`rounded-2xl p-4 border ${style.bg} ${style.border} space-y-3`}>
              <div className="flex items-start gap-2">
                {style.icon}
                <p className={`text-sm font-medium leading-relaxed ${style.text}`}>{result.message}</p>
              </div>

              {result.discount_pct > 0 && (
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${style.bg} ${style.text} border ${style.border}`}>
                    {result.discount_pct.toFixed(1)}% OFF
                  </span>
                  <span className={`text-sm font-bold ${style.text}`}>₹{result.final_price.toFixed(0)}</span>
                </div>
              )}

              {/* Counter items */}
              {result.counter_items?.length > 0 && (
                <div className="space-y-1.5">
                  {result.counter_items.slice(0, 4).map((item, i) => item?.name && (
                    <div key={i} className="flex items-center justify-between bg-white/60 rounded-xl px-3 py-1.5 border border-white">
                      <span className="text-xs text-gray-700 font-medium truncate max-w-[60%]">{item.name}</span>
                      <span className="text-xs font-bold text-gray-900">₹{item.price}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-2 pt-1">
                {result.outcome !== 'decline' && (
                  <button
                    onClick={handleAddAll}
                    disabled={addedAll}
                    className="flex-1 py-2.5 bg-green-gradient text-white text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 btn-press shadow-green"
                  >
                    {addedAll ? <><Check size={13} /> Added!</> : <><ShoppingCart size={13} /> Add to Cart</>}
                  </button>
                )}
                <button
                  onClick={() => setResult(null)}
                  className="px-3 py-2.5 bg-white border border-gray-200 text-xs font-bold text-gray-600 rounded-xl btn-press hover:bg-gray-50"
                >
                  Counter again
                </button>
              </div>
            </div>
          )}

          {/* Tips */}
          {!result && (
            <p className="text-[10px] text-gray-400 text-center">
              💡 Our AI evaluates your offer against margins, your order history, and available swaps.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
