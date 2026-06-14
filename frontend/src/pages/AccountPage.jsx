import React, { useEffect, useState } from 'react'
import { MapPin, CreditCard, Plus, Trash2, Star, Check, Loader2 } from 'lucide-react'
import Header from '../components/Layout/Header'
import { addressAPI, paymentAPI } from '../services/api'

const PAYMENT_TYPES = [
  { type: 'cod', label: 'Cash on Delivery' },
  { type: 'upi', label: 'UPI' },
  { type: 'card', label: 'Card' },
  { type: 'netbanking', label: 'Net Banking' },
]

export default function AccountPage() {
  const [addresses, setAddresses] = useState([])
  const [methods, setMethods] = useState([])
  const [loading, setLoading] = useState(true)

  const blankAddr = { full_name: '', phone: '', line1: '', line2: '', city: '', state: '', pincode: '' }
  const [addrForm, setAddrForm] = useState(blankAddr)
  const [savingAddr, setSavingAddr] = useState(false)

  const [pmType, setPmType] = useState('cod')
  const [pmDetails, setPmDetails] = useState('')
  const [savingPm, setSavingPm] = useState(false)

  const load = async () => {
    try {
      const [a, m] = await Promise.all([addressAPI.list(), paymentAPI.list()])
      setAddresses(a.data)
      setMethods(m.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const saveAddress = async (e) => {
    e.preventDefault()
    if (!addrForm.line1.trim()) return
    setSavingAddr(true)
    try {
      await addressAPI.create({ ...addrForm, is_default: addresses.length === 0 })
      setAddrForm(blankAddr)
      await load()
    } finally {
      setSavingAddr(false)
    }
  }

  const savePayment = async () => {
    setSavingPm(true)
    try {
      const label = PAYMENT_TYPES.find((p) => p.type === pmType)?.label || pmType
      await paymentAPI.create({
        type: pmType,
        label: pmDetails ? `${label} (${pmDetails})` : label,
        details: pmDetails,
        is_default: methods.length === 0,
      })
      setPmDetails('')
      await load()
    } finally {
      setSavingPm(false)
    }
  }

  const input = 'w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-green-400'

  return (
    <div className="min-h-screen">
      <Header />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">My Account</h1>
        <p className="text-gray-500 text-sm mb-6">
          Save your delivery address and payment method once — then just say "buy this" and QuickBot handles the rest.
        </p>

        {loading ? (
          <div className="flex justify-center py-20"><Loader2 className="animate-spin text-green-500" size={32} /></div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {/* Addresses */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <MapPin size={18} className="text-green-600" />
                <h2 className="font-bold text-gray-900">Delivery Addresses</h2>
              </div>

              {addresses.map((a) => (
                <div key={a.id} className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">
                  <div className="flex justify-between items-start">
                    <div>
                      {a.full_name && <p className="font-semibold text-sm text-gray-900">{a.full_name}</p>}
                      <p className="text-sm text-gray-600">{a.one_line}</p>
                      {a.phone && <p className="text-xs text-gray-400 mt-1">📞 {a.phone}</p>}
                    </div>
                    <button onClick={() => addressAPI.remove(a.id).then(load)} className="p-1.5 text-gray-300 hover:text-red-500">
                      <Trash2 size={15} />
                    </button>
                  </div>
                  <div className="mt-3">
                    {a.is_default ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-green-700 bg-green-50 px-2.5 py-1 rounded-full">
                        <Check size={12} /> Default
                      </span>
                    ) : (
                      <button
                        onClick={() => addressAPI.setDefault(a.id).then(load)}
                        className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-green-700"
                      >
                        <Star size={12} /> Set as default
                      </button>
                    )}
                  </div>
                </div>
              ))}

              <form onSubmit={saveAddress} className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm space-y-2.5">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Add new address</p>
                <div className="grid grid-cols-2 gap-2">
                  <input className={input} placeholder="Full name" value={addrForm.full_name} onChange={(e) => setAddrForm({ ...addrForm, full_name: e.target.value })} />
                  <input className={input} placeholder="Phone" value={addrForm.phone} onChange={(e) => setAddrForm({ ...addrForm, phone: e.target.value })} />
                </div>
                <input className={input} placeholder="House / Street *" value={addrForm.line1} onChange={(e) => setAddrForm({ ...addrForm, line1: e.target.value })} />
                <input className={input} placeholder="Area / Landmark" value={addrForm.line2} onChange={(e) => setAddrForm({ ...addrForm, line2: e.target.value })} />
                <div className="grid grid-cols-3 gap-2">
                  <input className={input} placeholder="City" value={addrForm.city} onChange={(e) => setAddrForm({ ...addrForm, city: e.target.value })} />
                  <input className={input} placeholder="State" value={addrForm.state} onChange={(e) => setAddrForm({ ...addrForm, state: e.target.value })} />
                  <input className={input} placeholder="Pincode" value={addrForm.pincode} onChange={(e) => setAddrForm({ ...addrForm, pincode: e.target.value })} />
                </div>
                <button disabled={savingAddr} className="w-full py-2.5 bg-green-gradient text-white text-sm font-semibold rounded-xl flex items-center justify-center gap-1.5 btn-press shadow-green disabled:opacity-60">
                  <Plus size={15} /> {savingAddr ? 'Saving...' : 'Save Address'}
                </button>
              </form>
            </div>

            {/* Payment methods */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <CreditCard size={18} className="text-green-600" />
                <h2 className="font-bold text-gray-900">Payment Methods</h2>
              </div>

              {methods.map((m) => (
                <div key={m.id} className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm flex justify-between items-center">
                  <div>
                    <p className="font-semibold text-sm text-gray-900">{m.label}</p>
                    {m.is_default ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-green-700 bg-green-50 px-2.5 py-1 rounded-full mt-1">
                        <Check size={12} /> Default
                      </span>
                    ) : (
                      <button onClick={() => paymentAPI.setDefault(m.id).then(load)} className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-green-700 mt-1">
                        <Star size={12} /> Set as default
                      </button>
                    )}
                  </div>
                  <button onClick={() => paymentAPI.remove(m.id).then(load)} className="p-1.5 text-gray-300 hover:text-red-500">
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}

              <div className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm space-y-2.5">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Add payment method</p>
                <div className="grid grid-cols-2 gap-2">
                  {PAYMENT_TYPES.map((p) => (
                    <button
                      key={p.type}
                      onClick={() => setPmType(p.type)}
                      className={`py-2 px-3 rounded-xl border text-sm font-medium transition-all ${
                        pmType === p.type ? 'border-green-500 bg-green-50/60 text-green-700' : 'border-gray-200 text-gray-600'
                      }`}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
                {pmType !== 'cod' && (
                  <input
                    className={input}
                    placeholder={pmType === 'upi' ? 'name@upi (optional)' : pmType === 'card' ? '•••• 4242 (optional)' : 'Detail (optional)'}
                    value={pmDetails}
                    onChange={(e) => setPmDetails(e.target.value)}
                  />
                )}
                <button disabled={savingPm} onClick={savePayment} className="w-full py-2.5 bg-green-gradient text-white text-sm font-semibold rounded-xl flex items-center justify-center gap-1.5 btn-press shadow-green disabled:opacity-60">
                  <Plus size={15} /> {savingPm ? 'Saving...' : 'Save Payment Method'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
