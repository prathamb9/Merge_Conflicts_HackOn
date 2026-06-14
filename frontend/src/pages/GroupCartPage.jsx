import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Users, Plus, ThumbsUp, Trash2, Copy, Check, Loader2, Search, Sparkles,
  ShoppingCart, Leaf, AlertTriangle, RefreshCw, Share2,
} from 'lucide-react'
import Header from '../components/Layout/Header'
import { groupAPI, productsAPI } from '../services/api'
import { useCart } from '../context/CartContext'

// ── Landing: create or join ───────────────────────────────────────────────────
function GroupLanding({ onCreated }) {
  const navigate = useNavigate()
  const [name, setName] = useState('Weekend Party Cart')
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)

  const create = async () => {
    setBusy(true)
    try {
      const res = await groupAPI.create(name)
      navigate(`/group/${res.data.code}`)
    } finally { setBusy(false) }
  }
  const join = async () => {
    if (!code.trim()) return
    navigate(`/group/${code.trim().toUpperCase()}`)
  }

  return (
    <div className="max-w-md mx-auto mt-10 space-y-5">
      <div className="text-center">
        <div className="w-14 h-14 rounded-2xl bg-green-gradient flex items-center justify-center mx-auto mb-3 shadow-green">
          <Users size={26} className="text-white" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Group Cart</h1>
        <p className="text-sm text-gray-500 mt-1">Shop together. Vote on items. Our AI resolves dietary conflicts so everyone's happy.</p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-3">
        <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Start a new group</label>
        <input value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-green-400" placeholder="Group name" />
        <button onClick={create} disabled={busy} className="w-full py-3 bg-green-gradient text-white text-sm font-bold rounded-2xl flex items-center justify-center gap-2 btn-press shadow-green disabled:opacity-60">
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />} Create Group
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-3">
        <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Join with a code</label>
        <div className="flex gap-2">
          <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} className="flex-1 px-3 py-2.5 rounded-xl border border-gray-200 text-sm font-bold tracking-widest focus:outline-none focus:border-green-400" placeholder="ABC123" maxLength={6} />
          <button onClick={join} className="px-5 py-2.5 bg-gray-900 text-white text-sm font-bold rounded-xl btn-press">Join</button>
        </div>
      </div>
    </div>
  )
}

// ── Inline product search to add items ────────────────────────────────────────
function AddItemSearch({ code, onAdded }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const timer = useRef(null)

  const search = (val) => {
    setQ(val)
    clearTimeout(timer.current)
    if (!val.trim()) { setResults([]); return }
    timer.current = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await productsAPI.list({ search: val, limit: 6 })
        setResults(res.data.products || [])
      } finally { setLoading(false) }
    }, 350)
  }

  const add = async (pid) => {
    await groupAPI.addItem(code, pid)
    setQ(''); setResults([])
    onAdded()
  }

  return (
    <div className="relative">
      <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 focus-within:border-green-400">
        <Search size={15} className="text-gray-400" />
        <input value={q} onChange={(e) => search(e.target.value)} className="flex-1 bg-transparent text-sm focus:outline-none" placeholder="Search products to propose…" />
        {loading && <Loader2 size={14} className="animate-spin text-gray-400" />}
      </div>
      {results.length > 0 && (
        <div className="absolute z-20 left-0 right-0 mt-1 bg-white rounded-xl border border-gray-100 shadow-lg max-h-72 overflow-y-auto">
          {results.map((p) => (
            <button key={p.id} onClick={() => add(p.id)} className="w-full flex items-center gap-3 p-2.5 hover:bg-gray-50 text-left border-b border-gray-50 last:border-0">
              <div className="w-9 h-9 rounded-lg bg-gray-50 overflow-hidden flex-shrink-0">
                <img src={p.image_url} alt="" className="w-full h-full object-contain" onError={(e) => { e.target.style.display = 'none' }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-gray-800 truncate">{p.name}</p>
                <p className="text-[10px] text-gray-400">₹{p.price} {p.is_vegetarian ? '· 🌿 veg' : '· 🍖 non-veg'}</p>
              </div>
              <Plus size={15} className="text-green-600" />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main group room ───────────────────────────────────────────────────────────
function GroupRoom({ code }) {
  const navigate = useNavigate()
  const { fetchCart, setIsOpen } = useCart()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [pushing, setPushing] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const res = await groupAPI.get(code)
      setData(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not load group')
    }
  }, [code])

  // initial join + poll every 4s for real-time updates
  useEffect(() => {
    let active = true
    groupAPI.join(code).then((res) => { if (active) setData(res.data) }).catch(() => refresh())
    const iv = setInterval(refresh, 4000)
    return () => { active = false; clearInterval(iv) }
  }, [code, refresh])

  const vote = async (itemId) => { const r = await groupAPI.vote(code, itemId); setData(r.data) }
  const remove = async (itemId) => { const r = await groupAPI.removeItem(code, itemId); setData(r.data) }

  const copyCode = () => {
    navigator.clipboard?.writeText(`${window.location.origin}/group/${code}`)
    setCopied(true); setTimeout(() => setCopied(false), 1500)
  }

  const pushToCart = async () => {
    setPushing(true)
    try {
      await groupAPI.checkoutToCart(code)
      await fetchCart()
      setIsOpen(true)
    } finally { setPushing(false) }
  }

  if (error) return <div className="text-center py-20 text-red-500">{error}</div>
  if (!data) return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-green-500" size={32} /></div>

  const c = data.consensus

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900">{data.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-400">Share code:</span>
            <span className="text-sm font-bold tracking-widest text-green-700 bg-green-50 px-2 py-0.5 rounded-lg">{data.code}</span>
            <button onClick={copyCode} className="text-gray-400 hover:text-green-600">
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>
        {/* Members */}
        <div className="flex items-center gap-2">
          <div className="flex -space-x-2">
            {data.members.map((m) => (
              <div key={m.id} title={`${m.display_name}${m.is_vegan ? ' (vegan)' : m.is_vegetarian ? ' (veg)' : ''}`}
                className={`w-8 h-8 rounded-full border-2 border-white flex items-center justify-center text-white text-xs font-bold ${
                  m.is_vegan ? 'bg-green-600' : m.is_vegetarian ? 'bg-green-500' : 'bg-gray-500'
                }`}>
                {m.display_name.charAt(0).toUpperCase()}
              </div>
            ))}
          </div>
          <span className="text-xs text-gray-500 flex items-center gap-1"><Users size={13} /> {data.members.length} shopping</span>
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-5">
        {/* Items + voting */}
        <div className="lg:col-span-3 space-y-4">
          <AddItemSearch code={code} onAdded={refresh} />

          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-bold text-gray-800 text-sm">Proposed Items ({data.items.length})</h3>
              <button onClick={refresh} className="text-gray-400 hover:text-green-600"><RefreshCw size={14} /></button>
            </div>
            <div className="p-3 space-y-2">
              {data.items.length === 0 ? (
                <p className="text-xs text-gray-400 text-center py-8">No items yet — search above to propose products for the group to vote on.</p>
              ) : data.items.map((it) => (
                <div key={it.item_id} className="flex items-center gap-3 bg-gray-50 rounded-xl p-2.5">
                  <div className="w-11 h-11 rounded-lg bg-white border border-gray-100 overflow-hidden flex-shrink-0">
                    <img src={it.product?.image_url} alt="" className="w-full h-full object-contain" onError={(e) => { e.target.style.display = 'none' }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{it.product?.name || it.product_name}</p>
                    <p className="text-[10px] text-gray-400">
                      ₹{it.product?.price} · by {it.added_by} {it.product?.is_vegetarian ? '· 🌿' : '· 🍖'}
                    </p>
                  </div>
                  <button
                    onClick={() => vote(it.item_id)}
                    className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all btn-press ${
                      it.voted_by_me ? 'bg-green-gradient text-white shadow-green' : 'bg-white border border-gray-200 text-gray-600'
                    }`}
                  >
                    <ThumbsUp size={12} /> {it.vote_count}
                  </button>
                  <button onClick={() => remove(it.item_id)} className="text-gray-300 hover:text-red-400 p-1"><Trash2 size={13} /></button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Consensus panel */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm sticky top-20 overflow-hidden">
            <div className="px-4 py-3 bg-gradient-to-r from-violet-50 to-indigo-50 border-b border-gray-100 flex items-center gap-2">
              <Sparkles size={16} className="text-violet-600" />
              <h3 className="font-bold text-gray-800 text-sm">AI Consensus</h3>
            </div>
            <div className="p-4 space-y-3">
              <p className="text-xs text-gray-600 leading-relaxed">{c.message}</p>

              {/* Conflicts resolved */}
              {c.conflicts?.length > 0 && (
                <div className="space-y-1.5">
                  {c.conflicts.map((cf, i) => (
                    <div key={i} className="flex items-start gap-1.5 bg-amber-50 border border-amber-100 rounded-lg p-2">
                      <AlertTriangle size={12} className="text-amber-600 mt-0.5 flex-shrink-0" />
                      <p className="text-[10px] text-amber-700">
                        {cf.alternative
                          ? <>Swapped <b>{cf.original.name}</b> → <b>{cf.alternative.name}</b> ({cf.reason})</>
                          : <><b>{cf.original.name}</b> flagged: {cf.reason}</>}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* Final cart */}
              {c.final_cart?.length > 0 && (
                <div>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Group-Approved Cart</p>
                  <div className="space-y-1.5 max-h-52 overflow-y-auto">
                    {c.final_cart.map((p, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="text-gray-700 truncate max-w-[70%] flex items-center gap-1">
                          {p.is_vegetarian && <Leaf size={10} className="text-green-500" />}
                          {p.name}
                        </span>
                        <span className="font-bold text-gray-900">₹{p.price}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-between pt-2 border-t border-gray-100">
                <span className="text-sm font-medium text-gray-500">Total</span>
                <span className="text-lg font-bold gradient-text">₹{c.final_total?.toFixed(0)}</span>
              </div>

              <button
                onClick={pushToCart}
                disabled={pushing || !c.final_cart?.length}
                className="w-full py-3 bg-green-gradient text-white text-sm font-bold rounded-2xl flex items-center justify-center gap-2 btn-press shadow-green disabled:opacity-60"
              >
                {pushing ? <Loader2 size={16} className="animate-spin" /> : <ShoppingCart size={16} />}
                Add approved cart to mine
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function GroupCartPage() {
  const { code } = useParams()
  return (
    <div className="min-h-screen">
      <Header />
      <div className="px-4 py-8">
        {code ? <GroupRoom code={code} /> : <GroupLanding />}
      </div>
    </div>
  )
}
