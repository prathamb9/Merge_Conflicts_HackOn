import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CalendarDays, Loader2, Sparkles, Check, ShoppingCart, Trash2, RefreshCw,
  Utensils, Plus, Minus,
} from 'lucide-react'
import Header from '../components/Layout/Header'
import { mealPlanAPI } from '../services/api'
import { useCart } from '../context/CartContext'

const GOAL_PRESETS = [
  'high-protein breakfasts and light dinners',
  'budget-friendly vegetarian meals',
  'quick 20-minute weeknight dinners',
  'weight-loss low-calorie meals',
  'balanced family meals',
]

export default function MealPlannerPage() {
  const navigate = useNavigate()
  const { addToCart, setIsOpen } = useCart()

  const [goal, setGoal] = useState(GOAL_PRESETS[0])
  const [days, setDays] = useState(7)
  const [servings, setServings] = useState(2)
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState(null)

  // which meal ids are enabled (user can remove meals)
  const [enabled, setEnabled] = useState({})
  const [shoppingList, setShoppingList] = useState([])
  const [total, setTotal] = useState(0)
  const [rebuilding, setRebuilding] = useState(false)
  const [addedAll, setAddedAll] = useState(false)

  const generate = async () => {
    setLoading(true)
    setPlan(null)
    try {
      const res = await mealPlanAPI.generate(goal, days, servings)
      setPlan(res.data)
      const en = {}
      ;(res.data.plan || []).forEach((d) => d.meals.forEach((m) => { en[m.id] = true }))
      setEnabled(en)
      setShoppingList(res.data.shopping_list || [])
      setTotal(res.data.total || 0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const toggleMeal = (id) => setEnabled((p) => ({ ...p, [id]: !p[id] }))

  const rebuildList = async () => {
    if (!plan) return
    setRebuilding(true)
    try {
      const ingredients = []
      plan.plan.forEach((d) => d.meals.forEach((m) => {
        if (enabled[m.id]) ingredients.push(...(m.ingredients || []))
      }))
      const res = await mealPlanAPI.consolidate(ingredients, servings)
      setShoppingList(res.data.shopping_list || [])
      setTotal(res.data.total || 0)
    } finally {
      setRebuilding(false)
    }
  }

  const adjustQty = (idx, delta) => {
    setShoppingList((prev) => {
      const next = [...prev]
      const item = { ...next[idx] }
      item.quantity = Math.max(1, (item.quantity || 1) + delta)
      next[idx] = item
      return next
    })
  }

  const removeItem = (idx) => setShoppingList((prev) => prev.filter((_, i) => i !== idx))

  const addAllToCart = async () => {
    for (const item of shoppingList) {
      for (let q = 0; q < (item.quantity || 1); q++) {
        await addToCart(item.id)
      }
    }
    setAddedAll(true)
    setTimeout(() => { setAddedAll(false); setIsOpen(true) }, 1200)
  }

  const listTotal = shoppingList.reduce((s, it) => s + it.price * (it.quantity || 1), 0)

  return (
    <div className="min-h-screen">
      <Header />
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-2.5 mb-1">
          <div className="w-9 h-9 rounded-xl bg-green-gradient flex items-center justify-center shadow-green">
            <CalendarDays size={18} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Weekly Meal Planner</h1>
        </div>
        <p className="text-sm text-gray-500 mb-6">
          Tell me your goal — I'll plan your week and turn it into one smart shopping list. Edit anything you like.
        </p>

        {/* Controls */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-4 mb-6">
          <div>
            <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-2">Your Goal</label>
            <input
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-green-400"
              placeholder="e.g. high-protein breakfasts and light dinners"
            />
            <div className="flex flex-wrap gap-2 mt-2">
              {GOAL_PRESETS.map((g) => (
                <button key={g} onClick={() => setGoal(g)} className="text-[11px] px-2.5 py-1 rounded-full bg-gray-50 border border-gray-200 text-gray-600 hover:border-green-300 hover:text-green-700">
                  {g}
                </button>
              ))}
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-2">Days: {days}</label>
              <input type="range" min="1" max="7" value={days} onChange={(e) => setDays(parseInt(e.target.value))} className="w-full accent-green-600" />
            </div>
            <div className="flex-1">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-2">Servings: {servings}</label>
              <input type="range" min="1" max="8" value={servings} onChange={(e) => setServings(parseInt(e.target.value))} className="w-full accent-green-600" />
            </div>
          </div>
          <button
            onClick={generate}
            disabled={loading}
            className="w-full py-3 bg-green-gradient text-white text-sm font-bold rounded-2xl flex items-center justify-center gap-2 btn-press shadow-green disabled:opacity-60"
          >
            {loading ? <><Loader2 size={16} className="animate-spin" /> Planning your week…</> : <><Sparkles size={16} /> Generate Meal Plan</>}
          </button>
        </div>

        {plan && (
          <div className="grid lg:grid-cols-5 gap-6">
            {/* Plan */}
            <div className="lg:col-span-3 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-bold text-gray-900">Your {plan.days_count}-Day Plan</h2>
                <button onClick={rebuildList} disabled={rebuilding} className="text-xs font-semibold text-green-700 bg-green-50 hover:bg-green-100 px-3 py-1.5 rounded-lg flex items-center gap-1.5 btn-press">
                  {rebuilding ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />} Rebuild list
                </button>
              </div>
              {plan.plan.map((day) => (
                <div key={day.day} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                  <div className="px-4 py-2.5 bg-gray-50 border-b border-gray-100">
                    <p className="font-bold text-gray-800 text-sm">{day.day}</p>
                  </div>
                  <div className="divide-y divide-gray-50">
                    {day.meals.map((meal) => (
                      <div key={meal.id} className={`px-4 py-3 flex items-start gap-3 ${enabled[meal.id] ? '' : 'opacity-40'}`}>
                        <button
                          onClick={() => toggleMeal(meal.id)}
                          className={`mt-0.5 w-5 h-5 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                            enabled[meal.id] ? 'bg-green-500 border-green-500' : 'border-gray-300'
                          }`}
                        >
                          {enabled[meal.id] && <Check size={13} className="text-white" />}
                        </button>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold text-green-700 bg-green-50 px-2 py-0.5 rounded-full uppercase tracking-wide">{meal.type}</span>
                            <p className="text-sm font-semibold text-gray-800">{meal.dish}</p>
                          </div>
                          <p className="text-xs text-gray-400 mt-1">{(meal.ingredients || []).join(' · ')}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Shopping list */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm sticky top-20">
                <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
                  <ShoppingCart size={16} className="text-green-600" />
                  <h3 className="font-bold text-gray-800 text-sm">Smart Shopping List</h3>
                  <span className="ml-auto text-xs text-gray-400">{shoppingList.length} items</span>
                </div>
                <div className="max-h-[420px] overflow-y-auto p-3 space-y-2">
                  {shoppingList.length === 0 ? (
                    <p className="text-xs text-gray-400 text-center py-8">No items — enable some meals and rebuild.</p>
                  ) : shoppingList.map((it, idx) => (
                    <div key={it.id} className="flex items-center gap-2 bg-gray-50 rounded-xl p-2">
                      <div className="w-9 h-9 rounded-lg bg-white border border-gray-100 overflow-hidden flex-shrink-0">
                        <img src={it.image_url} alt="" className="w-full h-full object-contain" onError={(e) => { e.target.style.display = 'none' }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-gray-800 truncate">{it.name}</p>
                        <p className="text-[10px] text-gray-400">₹{it.price} · for {(it.for_ingredients || []).join(', ')}</p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button onClick={() => adjustQty(idx, -1)} className="w-5 h-5 rounded bg-gray-200 flex items-center justify-center"><Minus size={10} /></button>
                        <span className="text-xs font-bold w-4 text-center">{it.quantity || 1}</span>
                        <button onClick={() => adjustQty(idx, 1)} className="w-5 h-5 rounded bg-green-gradient text-white flex items-center justify-center"><Plus size={10} /></button>
                      </div>
                      <button onClick={() => removeItem(idx)} className="text-gray-300 hover:text-red-400 p-1"><Trash2 size={12} /></button>
                    </div>
                  ))}
                </div>
                {plan.unmatched?.length > 0 && (
                  <p className="px-4 pb-2 text-[10px] text-amber-600">Not in catalog: {plan.unmatched.join(', ')}</p>
                )}
                <div className="p-4 border-t border-gray-100">
                  <div className="flex justify-between mb-3">
                    <span className="text-sm font-medium text-gray-500">Total</span>
                    <span className="text-lg font-bold gradient-text">₹{listTotal.toFixed(0)}</span>
                  </div>
                  <button
                    onClick={addAllToCart}
                    disabled={addedAll || shoppingList.length === 0}
                    className="w-full py-3 bg-green-gradient text-white text-sm font-bold rounded-2xl flex items-center justify-center gap-2 btn-press shadow-green disabled:opacity-60"
                  >
                    {addedAll ? <><Check size={16} /> Added to cart!</> : <><ShoppingCart size={16} /> Add all to cart</>}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
