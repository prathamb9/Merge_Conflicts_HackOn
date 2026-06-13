import React, { useState, useEffect, useRef } from 'react'
import { Send, Zap, Trash2, ArrowRight, Settings, Sliders, ShieldCheck, Heart, Sparkles, Scale } from 'lucide-react'
import Header from '../components/Layout/Header'
import CartSidebar from '../components/Cart/CartSidebar'
import MessageBubble from '../components/Chat/MessageBubble'
import { chatAPI, profileAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello ${user?.username || 'there'}! 👋 I'm QuickBot, your quick commerce shopping buddy. What are we shopping for today?`,
      timestamp: new Date().toISOString()
    }
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)

  // Preferences state
  const [preferences, setPreferences] = useState({
    is_vegetarian: false,
    is_vegan: false,
    is_high_protein: false,
    weight_loss_mode: false,
    budget_preference: 500,
    favorite_categories: []
  })
  const [prefLoading, setPrefLoading] = useState(false)
  const [prefSuccess, setPrefSuccess] = useState(false)

  // Fetch user profile on mount
  useEffect(() => {
    async function loadProfile() {
      try {
        const res = await profileAPI.get()
        if (res.data) {
          setPreferences(res.data)
        }
      } catch (err) {
        console.error('Error fetching profile:', err)
      }
    }
    loadProfile()
  }, [])

  // Auto-scroll messages to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Send message
  const handleSend = async (e, overrideText) => {
    if (e) e.preventDefault()
    const textToSend = (overrideText ?? input).trim()
    if (!textToSend || sending) return

    const userMessage = {
      role: 'user',
      content: textToSend,
      timestamp: new Date().toISOString()
    }

    setMessages((prev) => [...prev, userMessage])
    if (!overrideText) setInput('')
    setSending(true)

    // Prepare message history formatted for backend (role, content)
    // Send only the text and roles to save bandwidth/context
    const chatHistory = messages.map((m) => ({
      role: m.role,
      content: m.content
    }))

    try {
      const res = await chatAPI.send(userMessage.content, chatHistory)
      
      const botMessage = {
        role: 'assistant',
        content: res.data.message,
        recommendations: res.data.recommendations || [],
        total: res.data.total,
        reasoning: res.data.reasoning,
        recipe_mode: res.data.recipe_mode || false,
        skipped_ingredients: res.data.skipped_ingredients || [],
        cart_optimization: res.data.cart_optimization || null,
        amazon_departments: res.data.amazon_departments || [],
        timestamp: new Date().toISOString()
      }
      
      setMessages((prev) => [...prev, botMessage])
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: err.response?.data?.detail
          ? `Sorry, something went wrong: ${err.response.data.detail}`
          : 'Sorry, I could not reach the recommendation service. Please check that the backend is running and try again.',
        timestamp: new Date().toISOString()
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setSending(false)
    }
  }

  // Pre-configured quick suggestions
  const suggestions = [
    { text: 'Movie night snacks under ₹300', emoji: '🍿' },
    { text: 'Healthy high-protein gym breakfast', emoji: '💪' },
    { text: 'I want to cook paneer butter masala for 3 people', emoji: '🍳' },
    { text: 'Fresh fruits and salads on budget', emoji: '🍓' },
    { text: 'Need a tea break for 3 people', emoji: '☕' },
    { text: 'Party snacks for IPL match night', emoji: '🏏' },
  ]

  const handleSuggestionClick = (text) => {
    setInput(text)
  }

  // Save profile preferences
  const handleSavePreferences = async () => {
    setPrefLoading(true)
    setPrefSuccess(false)
    try {
      const res = await profileAPI.update(preferences)
      setPreferences(res.data)
      setPrefSuccess(true)
      setTimeout(() => setPrefSuccess(false), 2000)

      // Instantly refresh recommendations to reflect the new budget/preferences.
      // Reuse the user's most recent query if available, otherwise use a generic one.
      const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')
      const regenQuery = lastUserMsg
        ? lastUserMsg.content
        : `Suggest items for me within my ₹${preferences.budget_preference} budget`
      handleSend(null, regenQuery)
    } catch (err) {
      console.error('Error saving profile:', err)
    } finally {
      setPrefLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: "Chat cleared! How else can I assist you with shopping today?",
        timestamp: new Date().toISOString()
      }
    ])
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      <CartSidebar />

      {/* Main Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto px-4 py-6 flex gap-6 overflow-hidden h-[calc(100vh-64px)]">
        
        {/* Left/Chat Column */}
        <div className="flex-1 bg-white rounded-3xl border border-gray-100 flex flex-col overflow-hidden shadow-sm relative">
          
          {/* Top Info Bar */}
          <div className="px-6 py-3 border-b border-gray-100 flex justify-between items-center bg-white z-10">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse" />
              <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">QuickBot AI Assistant</span>
            </div>
            <button
              onClick={clearChat}
              className="text-xs text-gray-400 hover:text-red-500 font-semibold flex items-center gap-1 transition-colors px-2 py-1 hover:bg-red-50 rounded-lg"
            >
              <Trash2 size={12} /> Clear Chat
            </button>
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 chat-scroll bg-gray-50/30">
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
            
            {/* Thinking Indicator */}
            {sending && (
              <div className="flex gap-3 animate-fade-in justify-start">
                <div className="w-8 h-8 bg-green-gradient rounded-xl flex items-center justify-center flex-shrink-0 shadow-green mt-1">
                  <Zap size={13} className="text-white animate-pulse" fill="white" />
                </div>
                <div className="bg-white rounded-2xl rounded-tl-none px-5 py-4 shadow-card border border-gray-100 flex flex-col gap-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-green-700">
                    <Sparkles size={12} className="animate-spin text-green-600" />
                    Analyzing catalog & compiling recommendations...
                  </div>
                  <div className="loading-dots mt-1.5">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick suggestions on empty or limited context */}
          {messages.length === 1 && (
            <div className="px-6 py-2 bg-white border-t border-gray-50">
              <p className="text-xs font-bold text-gray-400 mb-2">Try asking for:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {suggestions.map((sug, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestionClick(sug.text)}
                    className="p-2.5 rounded-xl border border-gray-100 bg-gray-50 hover:bg-green-50/50 hover:border-green-200 text-left text-xs font-semibold text-gray-700 transition-all flex items-center gap-2 group btn-press"
                  >
                    <span className="text-lg group-hover:scale-110 transition-transform">{sug.emoji}</span>
                    <span className="truncate">{sug.text}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Bottom Chat Input Form */}
          <form onSubmit={handleSend} className="p-4 border-t border-gray-100 bg-white">
            <div className="flex gap-3 bg-gray-50 rounded-2xl p-2 border border-gray-100 input-glow">
              <input
                id="chat-input"
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={sending}
                placeholder="Ask QuickBot for recommendations, or try 'cook paneer butter masala for 3'..."
                className="flex-1 bg-transparent px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:outline-none"
              />
              <button
                id="chat-submit"
                type="submit"
                disabled={!input.trim() || sending}
                className="w-10 h-10 bg-green-gradient text-white rounded-xl flex items-center justify-center shadow-green hover:opacity-90 disabled:opacity-50 transition-all btn-press flex-shrink-0"
              >
                <Send size={15} />
              </button>
            </div>
            <p className="text-[10px] text-gray-400 text-center mt-2">
              🤖 QuickBot uses weather, time, and your profile to personalize recommendations. Try a recipe!
            </p>
          </form>

        </div>

        {/* Right Preferences Sidebar */}
        <div className="hidden lg:block w-80 bg-white rounded-3xl border border-gray-100 p-6 shadow-sm overflow-y-auto">
          <div className="flex items-center gap-2.5 mb-5 pb-3 border-b border-gray-100">
            <Sliders size={18} className="text-green-600" />
            <h3 className="font-bold text-gray-900 text-base">Shopping Assistant Filter</h3>
          </div>

          <div className="space-y-6">
            
            {/* Diet Prefs */}
            <div>
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-3">Dietary Mode</label>
              <div className="space-y-2">
                {[
                  { key: 'is_vegetarian', label: '🌿 Vegetarian', desc: 'Exclude meat & fish' },
                  { key: 'is_vegan', label: '🌱 Vegan', desc: '100% plant-based items' },
                  { key: 'is_high_protein', label: '💪 High Protein', desc: 'Focus on fitness & gym food' },
                  { key: 'weight_loss_mode', label: '⚖️ Weight Loss', desc: 'Prefer light, low-calorie, toned options' },
                ].map((item) => (
                  <button
                    key={item.key}
                    onClick={() => setPreferences({ ...preferences, [item.key]: !preferences[item.key] })}
                    className={`w-full p-3 rounded-2xl border text-left transition-all ${
                      preferences[item.key]
                        ? item.key === 'weight_loss_mode'
                          ? 'bg-purple-50/70 border-purple-500 text-purple-800'
                          : 'bg-green-50/70 border-green-500 text-green-800'
                        : 'bg-white border-gray-100 hover:border-gray-200 text-gray-700'
                    }`}
                  >
                    <p className="font-semibold text-xs">{item.label}</p>
                    <p className={`text-[10px] mt-0.5 ${
                      preferences[item.key]
                        ? item.key === 'weight_loss_mode' ? 'text-purple-600' : 'text-green-600'
                        : 'text-gray-400'
                    }`}>{item.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Budget Pref */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Default Budget</label>
                <span className="text-sm font-bold text-green-700">₹{preferences.budget_preference}</span>
              </div>
              <input
                id="pref-budget"
                type="range"
                min="500"
                max="200000"
                step="500"
                value={preferences.budget_preference}
                onChange={(e) => setPreferences({ ...preferences, budget_preference: parseInt(e.target.value) })}
                className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-600 focus:outline-none"
              />
              <div className="flex justify-between text-[10px] text-gray-400 mt-1 font-medium">
                <span>₹500</span>
                <span>₹2,00,000</span>
              </div>
            </div>

            {/* Favorite Categories */}
            <div>
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-2">Favorite Categories</label>
              <div className="grid grid-cols-2 gap-2">
                {['Snacks', 'Beverages', 'Dairy', 'Breakfast', 'Fruits', 'Vegetables', 'Healthy', 'Instant', 'Bakery'].map((cat) => {
                  const isFav = preferences.favorite_categories?.includes(cat)
                  return (
                    <button
                      key={cat}
                      onClick={() => {
                        const next = isFav
                          ? preferences.favorite_categories.filter((c) => c !== cat)
                          : [...(preferences.favorite_categories || []), cat]
                        setPreferences({ ...preferences, favorite_categories: next })
                      }}
                      className={`py-1.5 px-2.5 text-xs font-semibold rounded-xl border text-center transition-all ${
                        isFav
                          ? 'bg-green-500 border-green-500 text-white shadow-sm'
                          : 'bg-white border-gray-100 hover:border-gray-200 text-gray-600'
                      }`}
                    >
                      {cat}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Update Profile Button */}
            <div className="pt-2">
              <button
                onClick={handleSavePreferences}
                disabled={prefLoading}
                className="w-full py-3 bg-green-gradient text-white text-xs font-bold rounded-2xl flex items-center justify-center gap-1.5 hover:opacity-90 transition-all btn-press shadow-green"
              >
                {prefLoading ? 'Saving...' : prefSuccess ? 'Preferences Saved! ✓' : 'Save Preference Filters'}
              </button>
            </div>

            <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100 flex gap-2">
              <ShieldCheck size={16} className="text-green-600 flex-shrink-0 mt-0.5" />
              <p className="text-[10px] text-gray-400 leading-normal">
                QuickBot uses weather, time of day, and your dietary preferences to personalize every recommendation. Try asking to cook a recipe!
              </p>
            </div>
            
          </div>
        </div>

      </div>
    </div>
  )
}
