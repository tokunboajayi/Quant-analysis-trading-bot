/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cockpit: {
          bg: '#0a0a0f',
          'bg-elevated': '#12121a',
          border: '#1f1f2e',
          text: '#e5e5e5',
          'text-dim': '#6b7280',
          accent: '#3b82f6',
          success: '#22c55e',
          warning: '#eab308',
          danger: '#ef4444',
        },
        gauge: {
          bg: '#1a1a24',
          bezel: '#2a2a3a',
          needle: '#f97316',
          redline: '#ef4444',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
