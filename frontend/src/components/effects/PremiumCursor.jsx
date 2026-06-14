import React, { useEffect, useRef } from 'react'

/**
 * PremiumCursor — a refined agency-style cursor:
 *   • a small solid dot that tracks the pointer instantly
 *   • a larger outer ring that eases (lerp) behind it
 *   • uses mix-blend-mode: difference so it stays visible on any background
 *   • grows / fills when hovering interactive elements (buttons, links, inputs)
 * Disabled on touch / reduced-motion. Native cursor is hidden via body.has-custom-cursor.
 */
export default function PremiumCursor() {
  const dotRef = useRef(null)
  const ringRef = useRef(null)

  useEffect(() => {
    if (window.matchMedia('(pointer: coarse)').matches) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    document.body.classList.add('has-custom-cursor')

    const dot = dotRef.current
    const ring = ringRef.current
    const pos = { x: window.innerWidth / 2, y: window.innerHeight / 2 }
    const ringPos = { ...pos }
    let raf
    let hovering = false
    let down = false

    const onMove = (e) => {
      pos.x = e.clientX
      pos.y = e.clientY
      dot.style.transform = `translate(${pos.x}px, ${pos.y}px) translate(-50%, -50%)`
      // hover detection
      const el = e.target
      const interactive = el.closest('a, button, [role="button"], input, textarea, select, label, .cursor-pointer')
      hovering = Boolean(interactive)
    }

    const onDown = () => { down = true }
    const onUp = () => { down = false }

    const render = () => {
      // ease the ring toward the pointer
      ringPos.x += (pos.x - ringPos.x) * 0.18
      ringPos.y += (pos.y - ringPos.y) * 0.18
      const scale = (hovering ? 1.9 : 1) * (down ? 0.8 : 1)
      ring.style.transform = `translate(${ringPos.x}px, ${ringPos.y}px) translate(-50%, -50%) scale(${scale})`
      ring.style.opacity = hovering ? '1' : '0.6'
      dot.style.opacity = hovering ? '0' : '1'
      raf = requestAnimationFrame(render)
    }

    window.addEventListener('mousemove', onMove)
    window.addEventListener('mousedown', onDown)
    window.addEventListener('mouseup', onUp)
    render()

    return () => {
      document.body.classList.remove('has-custom-cursor')
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mousedown', onDown)
      window.removeEventListener('mouseup', onUp)
      cancelAnimationFrame(raf)
    }
  }, [])

  return (
    <>
      <div ref={ringRef} className="cursor-ring" aria-hidden="true" />
      <div ref={dotRef} className="cursor-dot" aria-hidden="true" />
    </>
  )
}
