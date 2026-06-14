import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, User } from 'lucide-react'
import ProductRecommendation from './ProductRecommendation'

export default function MessageBubble({ message, onBuyNow }) {
  const navigate = useNavigate()
  const isBot = message.role === 'assistant'

  const timeStr = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : ''

  return (
    <div className={`flex gap-3 animate-fade-in ${isBot ? 'justify-start' : 'justify-end'}`}>
      {/* Bot avatar */}
      {isBot && (
        <div className="w-8 h-8 bg-green-gradient rounded-xl flex items-center justify-center flex-shrink-0 shadow-green mt-1">
          <Zap size={13} className="text-white" fill="white" />
        </div>
      )}

      <div className={`max-w-[85%] ${!isBot ? 'order-first' : ''}`}>
        {isBot ? (
          <div>
            <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-card border border-gray-100">
              <p className="text-gray-800 text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
            </div>

            {/* Checkout State Banners */}
            {message.current_state === 'COLLECTING_INFO' && message.missing_details?.length > 0 && (
              <div className="mt-2 flex items-center gap-2 p-3 bg-amber-50 rounded-xl border border-amber-200 animate-fade-in">
                <span className="text-lg">📋</span>
                <div className="flex-1">
                  <p className="text-amber-800 text-xs font-bold">Info needed to complete your order</p>
                  <p className="text-amber-600 text-[10px] mt-0.5">
                    Missing: {message.missing_details.join(', ').replace(/_/g, ' ')}
                  </p>
                </div>
              </div>
            )}

            {message.current_state === 'CHECKOUT_READY' && message.action === 'REDIRECT_TO_PAYMENT' && (
              <div className="mt-2 flex items-center gap-2 p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200 animate-fade-in">
                <span className="text-lg">✅</span>
                <div className="flex-1">
                  <p className="text-green-800 text-xs font-bold">Order ready for payment!</p>
                  <p className="text-green-600 text-[10px] mt-0.5">
                    {message.checkout_items?.length || 0} item(s) confirmed
                  </p>
                </div>
                {message.order_id && (
                  <button
                    onClick={() => navigate(`/payment/${message.order_id}`)}
                    className="px-3 py-1.5 bg-green-gradient text-white text-xs font-bold rounded-lg shadow-green hover:opacity-90 transition-all btn-press"
                  >
                    Proceed to Payment →
                  </button>
                )}
              </div>
            )}

            {/* Emotional / situational Care Kit banner */}
            {message.kit_title && (
              <div className="mt-2 flex items-center gap-2 p-3 bg-gradient-to-r from-rose-50 to-pink-50 rounded-xl border border-rose-200 animate-fade-in">
                <span className="text-xl">🧺</span>
                <div className="flex-1">
                  <p className="text-rose-800 text-xs font-bold">{message.kit_title}</p>
                  <p className="text-rose-500 text-[10px] mt-0.5">A complete kit curated for your moment</p>
                </div>
              </div>
            )}

            {(message.recommendations?.length > 0 || message.cart_optimization || message.amazon_departments?.length > 0) && (
              <ProductRecommendation
                recommendations={message.recommendations}
                total={message.total}
                reasoning={message.reasoning}
                recipeMode={message.recipe_mode}
                skippedIngredients={message.skipped_ingredients}
                cartOptimization={message.cart_optimization}
                amazonDepartments={message.amazon_departments}
                onBuyNow={onBuyNow}
              />
            )}
          </div>
        ) : (
          <div className="bg-green-gradient text-white px-4 py-3 rounded-2xl rounded-tr-none shadow-green">
            <p className="text-sm leading-relaxed">{message.content}</p>
          </div>
        )}
        {timeStr && (
          <p className={`text-xs text-gray-400 mt-1 ${isBot ? 'ml-1' : 'text-right mr-1'}`}>{timeStr}</p>
        )}
      </div>

      {/* User avatar */}
      {!isBot && (
        <div className="w-8 h-8 bg-gray-100 rounded-xl flex items-center justify-center flex-shrink-0 mt-1 border border-gray-200">
          <User size={14} className="text-gray-500" />
        </div>
      )}
    </div>
  )
}
