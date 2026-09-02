/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'sovereign-dark': '#1a1a1a',
        'sovereign-surface': '#242424',
        'sovereign-border': '#8fb03e',
        'nav-olive': '#57692c',
        'toolbar-dark': '#2b2b2b',
        'accent-green': '#8fb03e',
        'accent-amber': '#f59e0b',
        'accent-cyan': '#8fb03e',
        'accent-emerald': '#8fb03e',
        danger: '#ef4444',
        warning: '#f59e0b',
        link: '#4a9eff',
      },
      borderRadius: {
        DEFAULT: '0px',
        none: '0px',
        sm: '0px',
        md: '0px',
        lg: '0px',
        xl: '0px',
        '2xl': '0px',
        '3xl': '0px',
        full: '0px',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in': 'slide-in 0.3s ease-out forwards',
        'fade-up': 'fade-up 0.5s ease-out forwards',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 10px rgba(143, 176, 62, 0.5)' },
          '50%': { opacity: '.5', boxShadow: '0 0 20px rgba(143, 176, 62, 0.8)' },
        },
        'slide-in': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}
