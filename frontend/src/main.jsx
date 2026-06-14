import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import PremiumCursor from './components/effects/PremiumCursor.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <PremiumCursor />
    <App />
  </React.StrictMode>
)
