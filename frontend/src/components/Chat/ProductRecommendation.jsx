import React, { useState } from 'react'
import { Star, Plus, Check, Package, RefreshCw, ChefHat, Truck, ShoppingCart } from 'lucide-react'
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
    <div className="flex-shrink-0 w-44 bg-white rounded-2xl shadow-card border border-gray-100 overflow-hidden card-hover shine flex flex-col relative">
      {/* Substitution badge */}
      {product.is_substitute && (
        <div className="absolute top-0 left-0 right-0 bg-amber-500 text-white text-[9px] font-bold px-2 py-1 flex items-center gap-1 z-10">
          <RefreshCw size={9} />
          <span className="truncate">Substituted for {product.original_product}</span>
        </div>
      )}
      
      {/* Real product image with emoji fallback */}
      <div className={`relative h-28 bg-white overflow-hidden flex items-center justify-center ${product.is_substitute ? 'mt-5' : ''}`}>
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
        
        {/* Substitution reason */}
        {product.substitution_reason && (
          <p className="text-xs text-amber-600 mt-1 italic line-clamp-1">🔄 {product.substitution_reason}</p>
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

export default function ProductRecommendation({ recommendations, total, reasoning, recipeMode, skippedIngredients, cartOptimization }) {
  const { addToCart } = useCart()
  const [addingAll, setAddingAll] = useState(false)
  const [allAdded, setAllAdded] = useState(false)

  if (!recommendations?.length && !cartOptimization) return null

  const displayTotal = total ?? recommendations.reduce((s, r) => s + (r.price || 0), 0)

  const handleAddAll = async () => {
    if (addingAll || allAdded) return
    setAddingAll(true)
    try {
      for (const product of recommendations) {
        if (product.in_stock !== false) {
          await addToCart(product.id)
        }
      }
      setAllAdded(true)
      setTimeout(() => setAllAdded(false), 3000)
    } finally {
      setAddingAll(false)
    }
  }

  return (
    <div className="mt-3 animate-slide-up">
      {/* Recipe Mode Header */}
      {recipeMode && (
        <div className="flex items-center gap-2 mb-3 p-3 bg-amber-50 rounded-xl border border-amber-200">
          <span className="text-xl">🍳</span>
          <div className="flex-1">
            <p className="text-amber-800 text-xs font-bold">Recipe Bundle</p>
            <p className="text-amber-600 text-[10px]">All ingredients matched from our catalog</p>
          </div>
          <button
            onClick={handleAddAll}
            disabled={addingAll || allAdded}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all btn-press ${
              allAdded
                ? 'bg-green-100 text-green-700'
                : 'bg-amber-500 text-white hover:bg-amber-600 shadow-sm'
            }`}
          >
            {allAdded ? '✓ All Added!' : addingAll ? 'Adding...' : '🛒 Add All to Cart'}
          </button>
        </div>
      )}

      {/* Skipped Ingredients */}
      {skippedIngredients?.length > 0 && (
        <div className="flex items-start gap-2 mb-3 p-3 bg-blue-50 rounded-xl border border-blue-100">
          <span className="text-blue-500 mt-0.5">📋</span>
          <div>
            <p className="text-blue-700 text-xs font-bold">Skipped (recently purchased)</p>
            <p className="text-blue-600 text-[10px] mt-0.5">
              {skippedIngredients.join(', ')} — you likely have these at home
            </p>
          </div>
        </div>
      )}

      {/* Reasoning */}
      {reasoning && (
        <div className="flex items-start gap-2 mb-3 p-3 bg-green-50 rounded-xl border border-green-100">
          <span className="text-green-500 mt-0.5">💡</span>
          <p className="text-green-700 text-xs font-medium leading-relaxed">{reasoning}</p>
        </div>
      )}

      {/* Cart Optimization Banner */}
      {cartOptimization && cartOptimization.gap > 0 && (
        <div className="mb-3 p-3 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-200">
          <div className="flex items-center gap-2 mb-2">
            <Truck size={14} className="text-purple-600" />
            <p className="text-purple-800 text-xs font-bold">
              ₹{cartOptimization.gap.toFixed(0)} away from {cartOptimization.threshold_name}!
            </p>
            <span className="ml-auto text-purple-600 text-[10px] font-bold bg-purple-100 px-2 py-0.5 rounded-full">
              Save ₹{cartOptimization.savings.toFixed(0)}
            </span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-purple-200 rounded-full h-1.5 mb-2">
            <div
              className="bg-purple-600 h-1.5 rounded-full transition-all"
              style={{ width: `${Math.min(100, (cartOptimization.current_total / cartOptimization.threshold_amount) * 100)}%` }}
            />
          </div>
          {cartOptimization.suggested_products?.length > 0 && (
            <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
              {cartOptimization.suggested_products.slice(0, 3).map((p, i) => (
                <SuggestedMiniCard key={p.id || i} product={p} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Horizontal scrollable cards */}
      {recommendations?.length > 0 && (
        <div
          className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {recommendations.map((product, i) => (
            <ProductCard key={product.id || i} product={product} />
          ))}
        </div>
      )}

      {/* Total summary */}
      {recommendations?.length > 0 && (
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
      )}
    </div>
  )
}


/** Mini card for cart optimization suggestions */
function SuggestedMiniCard({ product }) {
  const { addToCart } = useCart()
  const [added, setAdded] = useState(false)

  const handleAdd = async () => {
    if (added) return
    await addToCart(product.id)
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  return (
    <div className="flex-shrink-0 flex items-center gap-2 bg-white rounded-lg p-2 border border-purple-100 min-w-[180px]">
      <div className="w-8 h-8 rounded-md overflow-hidden bg-gray-50 flex-shrink-0">
        <img src={product.image_url} alt="" className="w-full h-full object-contain" onError={(e) => { e.target.style.display = 'none' }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-bold text-gray-800 truncate">{product.name}</p>
        <p className="text-[10px] text-purple-600 font-bold">₹{product.price}</p>
      </div>
      <button
        onClick={handleAdd}
        className={`p-1 rounded-md transition-all ${added ? 'bg-green-100 text-green-600' : 'bg-purple-100 text-purple-600 hover:bg-purple-200'}`}
      >
        {added ? <Check size={12} /> : <Plus size={12} />}
      </button>
    </div>
  )
}
