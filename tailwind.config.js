/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'surface-0': '#1c1610',
        'surface-1': '#22180f',
        'surface-2': '#c8a97e',
        'surface-3': '#dfc99a',
        'surface-edge': '#0f0b08',
        'paper-0': '#f5edd8',
        'paper-1': '#ede0c4',
        'paper-2': '#dfd0b0',
        'paper-edge': '#c4b090',
        'ink-primary': '#715d3f',
        'ink-secondary': 'rgba(112, 85, 45, 0.62)',
        'ink-ghost': 'rgba(107, 88, 58, 0.32)',
        'ink-dark': '#7a643e',
        strong: '#4a7c52',
        medium: '#c4822a',
        weak: '#7a6e5a',
        dissonant: '#b84830',
        borrowed: '#5a6e82',
        same: '#7a8a6a',
        accent: '#c4822a',
        'accent-warm': '#d4603a',
      },
      fontFamily: {
        display: ['"Special Elite"', '"Courier Prime"', 'monospace'],
        mono: ['"DM Mono"', 'monospace'],
        reading: ['"Courier Prime"', 'monospace'],
        grotesk: ['"Space Grotesk"', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        paper: '0 10px 28px -18px rgba(0,0,0,0.9)',
        card: '0 10px 24px -18px rgba(0,0,0,0.8)',
        canvas: '0 12px 26px -18px rgba(0,0,0,0.8)',
        tape: '0 1px 3px rgba(0,0,0,0.45)',
      },
      backgroundImage: {
        grain:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.55' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.08' fill='black'/%3E%3C/svg%3E\")",
      },
      borderRadius: {
        tape: '3px',
        card: '4px',
        pill: '2px',
      },
    },
  },
  plugins: [],
}
