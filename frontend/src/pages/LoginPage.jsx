import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, Lock, Eye, EyeOff, Zap, Check, Sparkles, ShieldCheck } from 'lucide-react'
import gsap from 'gsap'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const leftRef = useRef(null)
  const cardRef = useRef(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.login-anim', {
        opacity: 0, y: 30, duration: 0.7, stagger: 0.08, ease: 'power3.out',
      })
      gsap.from(cardRef.current, {
        opacity: 0, x: 40, duration: 0.8, ease: 'power3.out', delay: 0.1,
      })
      gsap.from('.chip-anim', {
        opacity: 0, scale: 0.85, duration: 0.5, stagger: 0.08, ease: 'back.out(1.7)', delay: 0.4,
      })
    })
    return () => ctx.revert()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.email, form.password)
      navigate('/chat')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const features = [
    'Natural-language product discovery',
    'AI bargaining & dynamic pricing',
    'Voice-first hands-free shopping',
    'Smart group carts with consensus',
  ]

  return (
    <div className="min-h-screen flex relative overflow-hidden bg-ink-gradient">
      {/* floating orbs */}
      <div className="absolute top-[-10%] left-[-5%] w-[40rem] h-[40rem] rounded-full blur-3xl opacity-30 animate-float"
        style={{ background: 'radial-gradient(circle, #A3E635, transparent 65%)' }} />
      <div className="absolute top-[20%] right-[10%] w-[28rem] h-[28rem] rounded-full blur-3xl opacity-25 animate-float"
        style={{ background: 'radial-gradient(circle, #7C5CFC, transparent 65%)', animationDelay: '1.2s' }} />
      <div className="absolute bottom-[-15%] right-[-5%] w-[36rem] h-[36rem] rounded-full blur-3xl opacity-25 animate-float"
        style={{ background: 'radial-gradient(circle, #2DD4BF, transparent 65%)', animationDelay: '2s' }} />

      {/* Left brand panel */}
      <div ref={leftRef} className="hidden lg:flex lg:w-1/2 flex-col justify-center px-16 relative z-10">
        <div className="max-w-md">
          <div className="login-anim flex items-center gap-3 mb-12">
            <div className="w-14 h-14 bg-green-gradient rounded-2xl flex items-center justify-center shadow-glow-green">
              <Zap className="w-7 h-7 text-white" fill="white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white font-display tracking-tight">QuickBot</h1>
              <p className="text-green-400 text-xs font-semibold tracking-[0.2em] uppercase">Premium AI Shopping</p>
            </div>
          </div>

          <h2 className="login-anim text-5xl font-bold text-white mb-4 leading-[1.1] font-display">
            Shop by <span className="gradient-text-gold">intent</span>,<br />not by search.
          </h2>
          <p className="login-anim text-gray-400 text-base mb-10 leading-relaxed">
            The world's first conversational commerce agent — it understands what you need, negotiates the price, and checks out for you.
          </p>

          <div className="space-y-3.5 mb-10">
            {features.map((f, i) => (
              <div key={i} className="login-anim flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-green-gradient flex items-center justify-center flex-shrink-0 shadow-green">
                  <Check size={13} className="text-white" />
                </div>
                <p className="text-gray-200 text-sm">{f}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { emoji: '🎬', text: 'Movie night under ₹300' },
              { emoji: '💪', text: 'High-protein gym pack' },
              { emoji: '🤝', text: 'Negotiate a better deal' },
              { emoji: '🥗', text: 'Healthy vegan options' },
            ].map((q, i) => (
              <div key={i} className="chip-anim glass-dark rounded-2xl p-3.5 flex items-center gap-2.5">
                <span className="text-2xl">{q.emoji}</span>
                <p className="text-gray-200 text-xs font-medium leading-tight">{q.text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form */}
      <div className="flex-1 flex items-center justify-center p-6 relative z-10">
        <div ref={cardRef} className="w-full max-w-md">
          <div className="glass rounded-[28px] p-8 shadow-2xl">
            <div className="flex items-center justify-center gap-2 mb-6 lg:hidden">
              <div className="w-9 h-9 bg-green-gradient rounded-xl flex items-center justify-center">
                <Zap size={18} className="text-white" fill="white" />
              </div>
              <span className="text-xl font-bold gradient-text font-display">QuickBot</span>
            </div>

            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs font-semibold mb-4">
              <Sparkles size={12} /> Welcome back
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-1 font-display">Sign in</h2>
            <p className="text-gray-500 text-sm mb-6">Continue your premium shopping journey</p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm flex items-center gap-2">
                <span>⚠️</span> {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email</label>
                <div className="relative input-glow rounded-xl">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={17} />
                  <input
                    id="login-email"
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border-2 border-gray-100 rounded-xl focus:outline-none focus:border-green-500 bg-white/70 focus:bg-white transition-all text-gray-900 text-sm"
                    placeholder="you@example.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1.5">Password</label>
                <div className="relative input-glow rounded-xl">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={17} />
                  <input
                    id="login-password"
                    type={showPw ? 'text' : 'password'}
                    required
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    className="w-full pl-10 pr-11 py-3 border-2 border-gray-100 rounded-xl focus:outline-none focus:border-green-500 bg-white/70 focus:bg-white transition-all text-gray-900 text-sm"
                    placeholder="Enter your password"
                  />
                  <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                    {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              </div>

              <button
                id="login-submit"
                type="submit"
                disabled={loading}
                className="btn-premium w-full py-3.5 bg-green-gradient text-white font-bold rounded-xl hover:opacity-95 transition-all btn-press disabled:opacity-60 shadow-green text-sm mt-2"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Signing in…
                  </span>
                ) : 'Sign In →'}
              </button>
            </form>

            <div className="flex items-center justify-center gap-1.5 mt-4 text-gray-400 text-[11px]">
              <ShieldCheck size={12} /> Secured with JWT encryption
            </div>

            <p className="text-center mt-4 text-gray-500 text-sm">
              Don't have an account?{' '}
              <Link to="/register" className="text-green-600 font-semibold hover:underline">Create one free</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
