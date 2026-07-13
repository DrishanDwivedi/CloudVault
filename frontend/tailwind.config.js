/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        outfit: ['"Outfit"', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#f0f4ff',
          100: '#e1e9ff',
          200: '#c7d7ff',
          300: '#9ebaff',
          400: '#6b90ff',
          500: '#3b5eff',
          600: '#253fff',
          655: '#1e35f0',
          700: '#1427eb',
          800: '#0f1ec5',
          900: '#101fa2',
          950: '#060a5c',
        },
        slate: {
          350: '#9ba8bf',
          450: '#7e8da3',
          550: '#5f6f85',
          650: '#475569',
          850: '#172033',
        },
        rose: {
          450: '#f2506e',
        },
      },
      scale: {
        '98': '0.98',
      },
    },
  },
  plugins: [],
}
