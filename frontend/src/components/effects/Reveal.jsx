import React, { useEffect, useRef } from 'react'
import gsap from 'gsap'

/**
 * Reveal — GSAP entrance animation that triggers when the element scrolls into
 * view (via IntersectionObserver, so no extra GSAP plugin needed).
 *
 * Props:
 *   as        - element tag (default 'div')
 *   delay     - seconds before animation
 *   y         - initial vertical offset (px)
 *   once      - only animate the first time (default true)
 */
export default function Reveal({
  as: Tag = 'div',
  children,
  className = '',
  delay = 0,
  y = 26,
  duration = 0.7,
  once = true,
  ...rest
}) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    gsap.set(el, { opacity: 0, y, willChange: 'transform, opacity' })

    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) { gsap.set(el, { opacity: 1, y: 0 }); return }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            gsap.to(el, {
              opacity: 1,
              y: 0,
              duration,
              delay,
              ease: 'power3.out',
            })
            if (once) io.unobserve(el)
          } else if (!once) {
            gsap.to(el, { opacity: 0, y, duration: 0.3 })
          }
        })
      },
      { threshold: 0.12 }
    )
    io.observe(el)
    return () => io.disconnect()
  }, [delay, y, duration, once])

  return (
    <Tag ref={ref} className={className} {...rest}>
      {children}
    </Tag>
  )
}
