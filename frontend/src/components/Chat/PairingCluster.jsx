import React, { useEffect, useState } from 'react'
import { Sparkles, Plus, Check, Loader2 } from 'lucide-react'
import { pairingAPI } from '../../services/api'
import { useCart } from '../../context/CartContext'

function PairingCard({ product }) {
  const { addToCart } = useCart()
  const [added, setAdded] = useState(false)

  const handleAdd = async () => {
    await addToCart(product.id)
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  return (
    <div className="flex-shrink-0 w-36 bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex flex-col card-hover">
      {/* Image */}
      <div className="h-24 bg-gray-50 flex items-center justify-center overflow-hidden">
        <img
          src={product.image_url}
          alt={product.name}
          className="w-full h-full object-contain p-1.5"
          loading="lazy"
          onError={(e) => { e.target.style.display = 'none' }}
        />
      </div>
      {/* Info */}
      <div className="p-2.5 flex-1 flex flex-col">
        <p className="text-[10px] text-gray-400 truncate">{product.brand}</p>
        <p className="text-xs font-bold text-gray-800 line-clamp-2 flex-1 mt-0.5">{product.name}</p>
        {product.pairing_reason && (
          <p className="text-[9px] text-violet-600 mt-1 line-clamp-1">✦ {product.pairing_reason}</p>
        )}
        <div className="flex items-center justify-between mt-1.5">
          <span className="text-sm font-bold text-gray-900">₹{product.price}</span>
          <button
            onClick={handleAdd}
            className={`p-1.5 rounded-lg text-xs transition-all btn-press ${
              added ? 'bg-green-100 text-green-600' : 'bg-violet-100 text-violet-700 hover:bg-violet-200'
            }`}
          >
            {added ? <Check size={12} /> : <Plus size={12} />}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function PairingCluster({ productIds, filters }) {
  const [cluster, setCluster] = useState(null)
  const [loading, setLoading] = useState(false)
  const { addToCart } = useCart()
  const [addedAll, setAddedAll] = useState(false)

  useEffect(() => {
    if (!productIds?.length) return
    setLoading(true)
    pairingAPI.get(productIds, filters)
      .then((res) => setCluster(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [productIds?.join(',')])

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-1 py-2 text-violet-600">
        <Loader2 size={14} className="animate-spin" />
        <span className="text-xs font-medium">Finding perfect pairings…</span>
      </div>
    )
  }

  if (!cluster?.products?.length) return null

  const handleAddAll = async () => {
    for (const p of cluster.products) {
      if (p?.id) await addToCart(p.id)
    }
    setAddedAll(true)
    setTimeout(() => setAddedAll(false), 2200)
  }

  return (
    <div className="mt-4 animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5">
          <div className="w-6 h-6 rounded-lg bg-violet-100 flex items-center justify-center">
            <Sparkles size={13} className="text-violet-600" />
          </div>
          <h4 className="text-sm font-bold text-gray-800">{cluster.cluster_label}</h4>
        </div>
        <button
          onClick={handleAddAll}
          disabled={addedAll}
          className={`text-[10px] font-bold px-2.5 py-1 rounded-full transition-all btn-press ${
            addedAll
              ? 'bg-green-100 text-green-700'
              : 'bg-violet-100 text-violet-700 hover:bg-violet-200'
          }`}
        >
          {addedAll ? '✓ All Added!' : 'Add All'}
        </button>
      </div>

      {/* Cards */}
      <div
        className="flex gap-3 overflow-x-auto pb-2"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {cluster.products.map((p) => (
          <PairingCard key={p.id} product={p} />
        ))}
      </div>

      {/* Footer */}
      <div className="mt-2 flex items-center justify-between px-1">
        <p className="text-[10px] text-gray-400 flex items-center gap-1">
          <Sparkles size={10} className="text-violet-400" />
          Graph-traversal engine — {cluster.products.length} complementary picks
        </p>
        <p className="text-[10px] text-gray-500 font-semibold">
          +₹{cluster.total_add_on_price?.toFixed(0)} if added
        </p>
      </div>
    </div>
  )
}
