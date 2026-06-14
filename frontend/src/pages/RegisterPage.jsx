import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { User, Mail, Lock, Eye, EyeOff, Zap, Sparkles } from 'lucide-react'
import gsap from 'gsap'
import { useAuth } from '../context/AuthContext'

const InputField = ({ id, label, type = 'text', icon: Icon, value, onChange, placeholder }) => (
  <div>
    <label className="block text-sm font-semibold text-gray-700 mb-1.5">{label}</label>
    <div className="relative input-glow rounded-xl">
      <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={17} />
      <input
        id={id} type={type} required value={value} onChange={onChange}
        className="w-full pl-10 pr-4 py-3 border-2 border-gray-100 rounded-xl focus:outline-none focus:border-green-500 bg-white/70 focus:bg-white transition-all text-gray-900 text-sm"
        placeholder={placeholder}
      />
    </div>
  </div>
)

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const cardRef = useRef(null)

  useEffect(() => {
    if (cardRef.current) {
      gsap.fromTo(cardRef.current, { opacity: 0, y: 36, scale: 0.97 },
        { opacity: 1, y: 0, scale: 1, duration: 0.7, ease: 'power3.out' })
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) return setError('Passwords do not match')
    if (form.password.length < 6) return setError('Password must be at least 6 characters')
    setLoading(true)
    try {
      await register(form.username, form.email, form.password)
      navigate('/chat')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden bg-ink-gradient">
      <div className="absolute top-[-10%] right-[-5%] w-[38rem] h-[38rem] rounded-full blur-3xl opacity-30 animate-float"
        style={{ background: 'radial-gradient(circle, #A3E635, transparent 65%)' }} />
      <div className="absolute bottom-[-15%] left-[-5%] w-[34rem] h-[34rem] rounded-full blur-3xl opacity-25 animate-float"
        style={{ background: 'radial-gradient(circle, #7C5CFC, transparent 65%)', animationDelay: '2s' }} />

      <div ref={cardRef} className="w-full max-w-md relative z-10">
        <div className="glass rounded-[28px] p-8 shadow-2xl">
          <div className="flex items-center justify-center gap-2 mb-5">
            <div className="w-11 h-11 bg-green-gradient rounded-xl flex items-center justify-center shadow-glow-green">
              <Zap size={21} className="text-white" fill="white" />
            </div>
            <span className="text-2xl font-bold gradient-text font-display">QuickBot</span>
          </div>

          <div className="flex justify-center mb-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-50 text-green-700 text-xs font-semibold">
              <Sparkles size={12} /> Free forever
            </div>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-1 font-display">Create account</h2>
          <p className="text-gray-500 text-sm text-center mb-6">Start your AI shopping journey today</p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">⚠️ {error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <InputField id="reg-username" label="Username" icon={User}
              value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })}
              placeholder="johndoe" />

            <InputField id="reg-email" label="Email" type="email" icon={Mail}
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com" />

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Password</label>
              <div className="relative input-glow rounded-xl">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" size={17} />
                <input
                  id="reg-password" type={showPw ? 'text' : 'password'} required
                  value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                  className="w-full pl-10 pr-11 py-3 border-2 border-gray-100 rounded-xl focus:outline-none focus:border-green-500 bg-white/70 focus:bg-white transition-all text-gray-900 text-sm"
                  placeholder="Min. 6 characters"
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400">
                  {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </div>

            <InputField id="reg-confirm" label="Confirm Password" type="password" icon={Lock}
              value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })}
              placeholder="Repeat your password" />

            <button
              id="reg-submit" type="submit" disabled={loading}
              className="btn-premium w-full py-3.5 bg-green-gradient text-white font-bold rounded-xl hover:opacity-95 transition-all btn-press disabled:opacity-60 shadow-green text-sm"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Creating account…
                </span>
              ) : 'Create Account →'}
            </button>
          </form>

          <p className="text-center mt-5 text-gray-500 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-green-600 font-semibold hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
