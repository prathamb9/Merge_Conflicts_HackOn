/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          green: '#0C831F',
          'green-light': '#1CC649',
          'green-dark': '#075212',
          emerald: '#059669',
          teal: '#0d9488',
          gold: '#D4A437',
          'gold-light': '#F4C430',
          ink: '#0A0E0A',
          dark: '#0F1A12',
        },
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'Plus Jakarta Sans', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-in-out',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.22, 1, 0.36, 1)',
        'slide-in-right': 'slideInRight 0.35s ease-out',
        'bounce-subtle': 'bounceSubtle 0.6s ease-in-out',
        'aurora': 'aurora 18s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s linear infinite',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
        'spin-slow': 'spin 14s linear infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(28px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        slideInRight: { '0%': { transform: 'translateX(100%)', opacity: '0' }, '100%': { transform: 'translateX(0)', opacity: '1' } },
        bounceSubtle: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-4px)' } },
        aurora: {
          '0%, 100%': { transform: 'translate(0,0) rotate(0deg) scale(1)' },
          '33%': { transform: 'translate(4%,-3%) rotate(8deg) scale(1.12)' },
          '66%': { transform: 'translate(-3%,4%) rotate(-6deg) scale(1.05)' },
        },
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-10px)' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        glowPulse: {
          '0%,100%': { boxShadow: '0 0 20px rgba(28,198,73,0.25)' },
          '50%': { boxShadow: '0 0 40px rgba(28,198,73,0.5)' },
        },
      },
      boxShadow: {
        card: '0 4px 24px rgba(15, 26, 18, 0.06)',
        'card-hover': '0 18px 50px rgba(15, 26, 18, 0.14)',
        green: '0 8px 24px rgba(12, 131, 31, 0.28)',
        'glow-green': '0 0 32px rgba(28, 198, 73, 0.35)',
        'glow-gold': '0 0 28px rgba(212, 164, 55, 0.35)',
        glass: '0 8px 32px rgba(15, 26, 18, 0.10), inset 0 1px 0 rgba(255,255,255,0.6)',
      },
      backdropBlur: { xs: '2px' },
    },
  },
  plugins: [],
}
