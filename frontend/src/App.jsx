import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { CartProvider } from './context/CartContext'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ChatPage from './pages/ChatPage'
import ProductsPage from './pages/ProductsPage'
import PaymentPage from './pages/PaymentPage'
import AccountPage from './pages/AccountPage'
import OrdersPage from './pages/OrdersPage'
import MealPlannerPage from './pages/MealPlannerPage'
import GroupCartPage from './pages/GroupCartPage'
import PageTransition from './components/effects/PageTransition'

function Spinner() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-4">
          <div className="absolute inset-0 border-4 border-green-500/20 rounded-full" />
          <div className="absolute inset-0 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
        </div>
        <p className="text-gray-500 font-medium font-display tracking-wide">Loading QuickBot…</p>
      </div>
    </div>
  )
}

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Spinner />
  if (!user) return <Navigate to="/login" replace />
  return children
}

function AuthRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Spinner />
  if (user) return <Navigate to="/chat" replace />
  return children
}

function AppRoutes() {
  return (
    <PageTransition>
      <Routes>
        <Route path="/login"    element={<AuthRoute><LoginPage /></AuthRoute>} />
        <Route path="/register" element={<AuthRoute><RegisterPage /></AuthRoute>} />
        <Route path="/chat"     element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
        <Route path="/products" element={<ProtectedRoute><ProductsPage /></ProtectedRoute>} />
        <Route path="/payment/:orderId" element={<ProtectedRoute><PaymentPage /></ProtectedRoute>} />
        <Route path="/account"  element={<ProtectedRoute><AccountPage /></ProtectedRoute>} />
        <Route path="/orders"   element={<ProtectedRoute><OrdersPage /></ProtectedRoute>} />
        <Route path="/meal-plan" element={<ProtectedRoute><MealPlannerPage /></ProtectedRoute>} />
        <Route path="/group"     element={<ProtectedRoute><GroupCartPage /></ProtectedRoute>} />
        <Route path="/group/:code" element={<ProtectedRoute><GroupCartPage /></ProtectedRoute>} />
        <Route path="*"         element={<Navigate to="/chat" replace />} />
      </Routes>
    </PageTransition>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <AppRoutes />
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
