import React, { useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import gsap from 'gsap'

/**
 * PageTransition — smooth GSAP fade/slide whenever the route changes.
 * Wraps the routed content; re-animates on pathname change.
 */
export default function PageTransition({ children }) {
  const ref = useRef(null)
  const location = useLocation()

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) return
    gsap.fromTo(
      el,
      { opacity: 0, y: 16 },
      { opacity: 1, y: 0, duration: 0.45, ease: 'power2.out' }
    )
  }, [location.pathname])

  return (
    <div ref={ref} style={{ minHeight: '100%' }}>
      {children}
    </div>
  )
}
