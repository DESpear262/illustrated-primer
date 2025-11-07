/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: { 900: '#111216' },
        parchment: { 50: '#F8F5EC', 100: '#F1EAD5' },
        brass: { 600: '#B08D57' },
        verdigris: { 500: '#2A8F8A' },
        navy: { 700: '#1F2C44' },
        garnet: { 600: '#8F1D2C' },
        smoke: { 300: '#D8D5CC' },
      },
      borderRadius: {
        xl: '12px',
        '2xl': '20px',
      },
      boxShadow: {
        brass: '0 6px 18px rgba(20,18,16,.18)',
        'brass-dark': '0 8px 22px rgba(0,0,0,.35)',
        'inner-bevel': '0 1px 0 rgba(176,141,87,.35) inset',
      },
      fontFamily: {
        'headline': ['"Spectral SC"', '"IM Fell English SC"', 'Georgia', 'serif'],
        'body': ['"Source Serif 4"', 'Georgia', 'serif'],
        'mono': ['"JetBrains Mono"', 'monospace'],
      },
      spacing: {
        '4': '4px',
        '8': '8px',
        '12': '12px',
        '16': '16px',
        '24': '24px',
        '32': '32px',
        '48': '48px',
      },
      transitionDuration: {
        '120': '120ms',
        '200': '200ms',
        '240': '240ms',
      },
      transitionTimingFunction: {
        'material': 'cubic-bezier(0.2, 0.0, 0.2, 1)',
      },
    },
  },
  plugins: [],
}

