/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'ab-bg':     '#0d1b2e',
        'ab-dark':   '#071629',
        'ab-card':   '#0f2137',
        'ab-border': '#1a3a5c',
        'ab-accent': '#00c896',
        'ab-hover':  '#00a87e',
        'ab-red':    '#e53935',
        'ab-muted':  '#7fb5d5',
        'ab-hint':   '#4a7a9b',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
