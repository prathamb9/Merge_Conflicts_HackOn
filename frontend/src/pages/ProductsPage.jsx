import React, { useState, useEffect, useCallback } from 'react'
import { Search, Plus, Check, Star, Filter, ArrowRight, ChevronDown, ChevronRight } from 'lucide-react'
import Header from '../components/Layout/Header'
import CartSidebar from '../components/Cart/CartSidebar'
import { productsAPI } from '../services/api'
import { useCart } from '../context/CartContext'

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
  const [adding, setAdding] = useState(false)

  const handleAdd = async () => {
    if (adding || added) return
    setAdding(true)
    try {
      await addToCart(product.id)
      setAdded(true)
      setTimeout(() => setAdded(false), 2000)
    } finally {
      setAdding(false)
    }
  }

  const discount = product.mrp > product.price
    ? Math.round(((product.mrp - product.price) / product.mrp) * 100)
    : 0

  const emoji = CATEGORY_EMOJI[product.category?.toLowerCase()] || '📦'

  return (
    <div className="bg-white rounded-3xl border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden flex flex-col group relative card-hover shine">
      {/* Product Image */}
      <div className="relative h-44 bg-white overflow-hidden flex items-center justify-center">
        <img
          src={product.image_url}
          alt={product.name}
          loading="lazy"
          className="w-full h-full object-contain p-3 group-hover:scale-105 transition-transform duration-300"
          onError={(e) => {
            e.target.style.display = 'none'
            if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex'
          }}
        />
        <div className="hidden w-full h-full items-center justify-center text-7xl absolute inset-0 bg-gradient-to-br from-gray-50 to-gray-100">
          {emoji}
        </div>

        {/* Badges */}
        <div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm rounded-xl px-2 py-0.5 flex items-center gap-1 shadow-sm border border-gray-100">
          <Star size={11} className="text-yellow-400" fill="#FBBF24" />
          <span className="text-xs font-bold text-gray-700">{product.rating || '4.0'}</span>
        </div>

        {discount > 0 && (
          <div className="absolute top-3 left-3 bg-red-500 text-white text-xs font-black px-2 py-1 rounded-xl shadow-sm">
            {discount}% OFF
          </div>
        )}

        {!product.in_stock && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center backdrop-blur-[1px]">
            <span className="text-white text-xs font-bold bg-red-500/90 px-3 py-1.5 rounded-full shadow-lg">Out of Stock</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4 flex flex-col flex-1">
        <span className="text-xs text-gray-400 font-bold tracking-wider uppercase">{product.brand}</span>
        <h4 className="text-sm font-bold text-gray-900 leading-tight mt-1 line-clamp-2 flex-1">{product.name}</h4>
        <p className="text-xs text-gray-400 mt-1.5 font-medium bg-gray-50 self-start px-2 py-0.5 rounded-md">{product.unit}</p>

        {/* Nutritional tags */}
        <div className="flex flex-wrap gap-1 mt-2.5">
          {product.is_vegetarian && (
            <span className="text-[9px] font-bold text-green-700 bg-green-50 border border-green-200/50 px-1.5 py-0.5 rounded">VEG</span>
          )}
          {product.is_vegan && (
            <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200/50 px-1.5 py-0.5 rounded">VEGAN</span>
          )}
          {product.is_high_protein && (
            <span className="text-[9px] font-bold text-blue-700 bg-blue-50 border border-blue-200/50 px-1.5 py-0.5 rounded">HIGH PROTEIN</span>
          )}
        </div>

        {/* Price & Add */}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-50">
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-base font-black text-gray-900">₹{product.price}</span>
              {discount > 0 && <span className="text-xs text-gray-400 line-through">₹{product.mrp}</span>}
            </div>
            <p className="text-[10px] text-gray-400 font-medium">Incl. all taxes</p>
          </div>

          <button
            onClick={handleAdd}
            disabled={!product.in_stock || adding}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all btn-press ${
              added
                ? 'bg-green-100 text-green-700 border border-green-200'
                : product.in_stock
                ? 'bg-green-gradient text-white hover:opacity-90 shadow-green'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            {added ? <><Check size={12} className="inline mr-1" /> Added</> : adding ? '...' : <><Plus size={12} className="inline mr-1" /> Add</>}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function ProductsPage() {
  const [products, setProducts] = useState([])
  const [departments, setDepartments] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('All')
  const [expandedDept, setExpandedDept] = useState(null)
  const [searchText, setSearchText] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch departments (grouped categories)
  useEffect(() => {
    async function loadDepartments() {
      try {
        const res = await productsAPI.departments()
        setDepartments(res.data.departments || [])
      } catch (err) {
        console.error('Error fetching departments:', err)
        // Fallback to flat categories
        try {
          const catRes = await productsAPI.categories()
          setDepartments([{
            department: '📦 All Categories',
            categories: (catRes.data.categories || []).map(c => ({ slug: c, label: c.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) }))
          }])
        } catch (e2) {
          setError(`Failed to load categories: ${e2.message}`)
        }
      }
    }
    loadDepartments()
  }, [])

  // Debounce search text
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchText)
      setPage(1)
    }, 300)
    return () => clearTimeout(handler)
  }, [searchText])

  // Fetch products
  const loadProducts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await productsAPI.list({
        category: selectedCategory === 'All' ? null : selectedCategory,
        search: debouncedSearch || null,
        page,
        limit: 12
      })
      if (page === 1) {
        setProducts(res.data.products)
      } else {
        setProducts((prev) => [...prev, ...res.data.products])
      }
      setTotal(res.data.total)
    } catch (err) {
      console.error('Error loading products:', err)
      setError(`Failed to load products: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }, [selectedCategory, debouncedSearch, page])

  useEffect(() => {
    loadProducts()
  }, [loadProducts])

  const handleCategorySelect = (catSlug) => {
    setSelectedCategory(catSlug)
    setPage(1)
  }

  const toggleDept = (deptName) => {
    setExpandedDept(expandedDept === deptName ? null : deptName)
  }

  const loadMore = () => {
    setPage((prev) => prev + 1)
  }

  // Count how many categories are inside the selected department
  const getActiveDeptLabel = () => {
    if (selectedCategory === 'All') return null
    for (const dept of departments) {
      for (const cat of dept.categories) {
        if (cat.slug === selectedCategory) return dept.department
      }
    }
    return null
  }
  const activeDept = getActiveDeptLabel()

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <CartSidebar />

      {/* Main Content Area */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 flex flex-col gap-6">
        
        {/* Top bar with heading and search */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black text-gray-900">Explore Catalog</h1>
            <p className="text-gray-400 text-sm font-medium mt-1">Browse 8 departments &middot; 24 categories &middot; 190+ products</p>
          </div>
          
          <div className="relative w-full md:max-w-md bg-white border border-gray-100 rounded-2xl flex items-center px-4 py-3 input-glow shadow-sm">
            <Search size={18} className="text-gray-400 mr-2 flex-shrink-0" />
            <input
              id="search-input"
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Search by product, brand, or tag..."
              className="w-full bg-transparent text-sm text-gray-800 placeholder-gray-400 focus:outline-none"
            />
          </div>
        </div>

        {/* Department-Grouped Category Navigation */}
        <div className="space-y-2">
          {/* "All" pill */}
          <div className="flex gap-2 flex-wrap items-center">
            <button
              onClick={() => { handleCategorySelect('All'); setExpandedDept(null) }}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl text-sm font-bold transition-all whitespace-nowrap btn-press border ${
                selectedCategory === 'All'
                  ? 'bg-green-gradient text-white border-transparent shadow-green'
                  : 'bg-white text-gray-600 border-gray-100 hover:border-gray-200 shadow-sm'
              }`}
            >
              <span>🏪</span>
              <span>All Products</span>
            </button>
          </div>

          {/* Department Accordion */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
            {departments.map((dept) => {
              const isExpanded = expandedDept === dept.department
              const isDeptActive = activeDept === dept.department

              return (
                <div key={dept.department} className={`rounded-2xl border overflow-hidden transition-all ${
                  isDeptActive ? 'border-green-300 bg-green-50/30' : 'border-gray-100 bg-white'
                }`}>
                  {/* Department Header */}
                  <button
                    onClick={() => toggleDept(dept.department)}
                    className={`w-full flex items-center justify-between px-4 py-3 text-left transition-all ${
                      isExpanded
                        ? 'bg-gradient-to-r from-green-50 to-emerald-50'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <span className={`text-xs font-bold truncate ${
                      isDeptActive ? 'text-green-700' : 'text-gray-700'
                    }`}>
                      {dept.department}
                    </span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span className="text-[10px] text-gray-400 font-medium">{dept.categories.length}</span>
                      {isExpanded
                        ? <ChevronDown size={14} className="text-gray-400" />
                        : <ChevronRight size={14} className="text-gray-400" />
                      }
                    </div>
                  </button>

                  {/* Sub-categories */}
                  {isExpanded && (
                    <div className="px-3 pb-3 space-y-1 animate-fade-in">
                      {dept.categories.map((cat) => {
                        const isActive = selectedCategory === cat.slug
                        const emoji = CATEGORY_EMOJI[cat.slug] || '📦'
                        return (
                          <button
                            key={cat.slug}
                            onClick={() => handleCategorySelect(cat.slug)}
                            className={`w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left text-xs font-semibold transition-all btn-press ${
                              isActive
                                ? 'bg-green-gradient text-white shadow-green'
                                : 'text-gray-600 hover:bg-gray-50'
                            }`}
                          >
                            <span className="text-sm">{emoji}</span>
                            <span className="truncate">{cat.label}</span>
                          </button>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Active Filter Breadcrumb */}
        {selectedCategory !== 'All' && (
          <div className="flex items-center gap-2 text-xs text-gray-500 font-medium">
            <span className="text-gray-400">Browsing:</span>
            {activeDept && (
              <>
                <span className="text-green-700 font-bold">{activeDept}</span>
                <span className="text-gray-300">›</span>
              </>
            )}
            <span className="text-gray-800 font-bold bg-green-50 px-2 py-0.5 rounded-lg border border-green-200">
              {CATEGORY_EMOJI[selectedCategory] || '📦'} {selectedCategory.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
            <button
              onClick={() => { handleCategorySelect('All'); setExpandedDept(null) }}
              className="text-red-400 hover:text-red-600 ml-1 font-bold"
            >
              ✕ Clear
            </button>
          </div>
        )}

        {/* Products Grid */}
        {error ? (
          <div className="bg-red-50 rounded-3xl border border-red-200 p-12 text-center">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">⚠️</span>
            </div>
            <h3 className="text-lg font-bold text-red-700">Error Loading Products</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
            <button
              onClick={() => {
                setError(null)
                loadProducts()
              }}
              className="mt-4 px-6 py-2 bg-red-500 text-white rounded-xl font-bold hover:bg-red-600 transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : products.length === 0 && !loading ? (
          <div className="bg-white rounded-3xl border border-gray-100 p-12 text-center shadow-sm">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search size={30} className="text-gray-300" />
            </div>
            <h3 className="text-lg font-bold text-gray-700">No products found</h3>
            <p className="text-gray-400 text-sm mt-1">We couldn't find matches for "{searchText}". Try other keywords!</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}

        {/* Loading placeholder cards */}
        {loading && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-white rounded-3xl border border-gray-100 p-4 animate-pulse flex flex-col h-[320px]">
                <div className="w-full h-40 bg-gray-100 rounded-2xl mb-4" />
                <div className="h-4 bg-gray-100 rounded-lg w-1/3 mb-2" />
                <div className="h-6 bg-gray-100 rounded-lg w-3/4 mb-4" />
                <div className="flex justify-between items-center mt-auto">
                  <div className="h-6 bg-gray-100 rounded-lg w-1/4" />
                  <div className="h-8 bg-gray-100 rounded-xl w-1/3" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Load More Button */}
        {products.length < total && !loading && (
          <div className="flex justify-center mt-6">
            <button
              onClick={loadMore}
              className="flex items-center gap-2 px-8 py-3.5 bg-white border border-gray-200 hover:border-gray-300 text-gray-700 text-sm font-bold rounded-2xl transition-all shadow-sm btn-press"
            >
              Load More Products <ArrowRight size={15} />
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
