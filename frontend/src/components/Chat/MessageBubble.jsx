import React from 'react'
import { Zap, User } from 'lucide-react'
import ProductRecommendation from './ProductRecommendation'

export default function MessageBubble({ message }) {
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
            {(message.recommendations?.length > 0 || message.cart_optimization || message.amazon_departments?.length > 0) && (
              <ProductRecommendation
                recommendations={message.recommendations}
                total={message.total}
                reasoning={message.reasoning}
                recipeMode={message.recipe_mode}
                skippedIngredients={message.skipped_ingredients}
                cartOptimization={message.cart_optimization}
                amazonDepartments={message.amazon_departments}
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
