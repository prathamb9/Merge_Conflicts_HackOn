import React, { useState } from 'react'
import { Star, Plus, Check, Package } from 'lucide-react'
import { useCart } from '../../context/CartContext'

const CATEGORY_EMOJI = {
  beauty: '💄', fragrances: '🌸', furniture: '🛋️', groceries: '🛒',
  'home-decoration': '🖼️', 'kitchen-accessories': '🍴', laptops: '💻',
  'mens-shirts': '👔', 'mens-shoes': '👞', 'mens-watches': '⌚',
  'mobile-accessories': '🔌', motorcycle: '🏍️', 'skin-care': '🧴',
  smartphones: '📱', 'sports-accessories': '🏀', sunglasses: '🕶️',
  tablets: '📲', tops: '👕', vehicle: '🚗', 'womens-bags': '👜',
  'womens-dresses': '👗', 'womens-jewellery': '💍', 'womens-shoes': '👠',
  'womens-watches': '⌚', snacks: '🍿', beverages: '🥤', dairy: '🥛',
  breakfast: '🍳', fruits: '🍎', vegetables: '🥦', healthy: '💪',
  instant: '🍜', bakery: '🥖',
}

function ProductCard({ product }) {
  const { addToCart } = useCart()
  const [added, setAdded] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleAdd = async () => {
    if (loading || added) return
    setLoading(true)
    try {
      await addToCart(product.id)
      setAdded(true)
      setTimeout(() => setAdded(false), 2200)
    } finally {
      setLoading(false)
    }
  }

  const discount = product.mrp > product.price
    ? Math.round(((product.mrp - product.price) / product.mrp) * 100)
    : 0

  const emoji = CATEGORY_EMOJI[product.category?.toLowerCase()] || '📦'

  return (
    <div className="flex-shrink-0 w-44 bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden card-hover shine flex flex-col">
      {/* Real product image with emoji fallback */}
      <div className="relative h-28 bg-white overflow-hidden flex items-center justify-center">
        <img
          src={product.image_url}
          alt={product.name}
          loading="lazy"
          className="w-full h-full object-contain p-2"
          onError={(e) => {
            e.target.style.display = 'none'
            if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex'
          }}
        />
        <div className="hidden w-full h-full items-center justify-center text-5xl absolute inset-0 bg-gradient-to-br from-gray-50 to-gray-100">
          {emoji}
        </div>

        {/* Rating */}
        <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm rounded-lg px-1.5 py-0.5 flex items-center gap-1 shadow-sm">
          <Star size={9} className="text-yellow-400" fill="#FBBF24" />
          <span className="text-xs font-bold text-gray-700">{product.rating}</span>
        </div>

        {/* Discount badge */}
        {discount > 0 && (
          <div className="absolute top-2 left-2 bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-lg shadow-sm">
            {discount}% OFF
          </div>
        )}

        {/* Out of stock overlay */}
        {!product.in_stock && (
          <div className="absolute inset-0 bg-black/55 flex items-center justify-center">
            <span className="text-white text-xs font-bold bg-red-500/90 px-2 py-1 rounded-full">Out of Stock</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3 flex flex-col flex-1">
        <p className="text-xs text-gray-400 font-medium truncate">{product.brand}</p>
        <h4 className="text-sm font-bold text-gray-900 leading-tight mt-0.5 line-clamp-2 flex-1">{product.name}</h4>
        <p className="text-xs text-gray-400 mt-1">{product.unit}</p>

        {/* Reason (chat context) */}
        {product.reason && (
          <p className="text-xs text-green-600 mt-1 italic line-clamp-1">✓ {product.reason}</p>
        )}

        {/* Price row */}
        <div className="flex items-center gap-2 mt-2">
          <span className="text-base font-bold text-gray-900">₹{product.price}</span>
          {discount > 0 && <span className="text-xs text-gray-400 line-through">₹{product.mrp}</span>}
        </div>

        {/* Add button */}
        <button
          onClick={handleAdd}
          disabled={!product.in_stock || loading}
          className={`w-full mt-2 py-1.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all btn-press ${
            added
              ? 'bg-green-100 text-green-700 border border-green-200'
              : product.in_stock
              ? 'bg-green-gradient text-white hover:opacity-90 shadow-green'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          {added ? <><Check size={12} /> Added!</> : loading ? '...' : <><Plus size={12} /> Add to Cart</>}
        </button>
      </div>
    </div>
  )
}

export default function ProductRecommendation({ recommendations, total, reasoning }) {
  if (!recommendations?.length) return null

  const displayTotal = total ?? recommendations.reduce((s, r) => s + (r.price || 0), 0)

  return (
    <div className="mt-3 animate-slide-up">
      {/* Reasoning */}
      {reasoning && (
        <div className="flex items-start gap-2 mb-3 p-3 bg-green-50 rounded-xl border border-green-100">
          <span className="text-green-500 mt-0.5">💡</span>
          <p className="text-green-700 text-xs font-medium leading-relaxed">{reasoning}</p>
        </div>
      )}

      {/* Horizontal scrollable cards */}
      <div
        className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        {recommendations.map((product, i) => (
          <ProductCard key={product.id || i} product={product} />
        ))}
      </div>

      {/* Total summary */}
      <div className="flex items-center justify-between mt-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
        <div className="flex items-center gap-2 text-gray-400">
          <Package size={15} />
          <span className="text-sm">{recommendations.length} item{recommendations.length !== 1 ? 's' : ''}</span>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400 mb-0.5">Estimated Total</p>
          <p className="text-lg font-bold gradient-text">₹{displayTotal.toFixed(0)}</p>
        </div>
      </div>
    </div>
  )
}
