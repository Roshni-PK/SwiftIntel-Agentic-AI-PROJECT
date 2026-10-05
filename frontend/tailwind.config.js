/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        slate: {
          50: '#f7f8fc', 100: '#f0f2f7', 200: '#e2e5ed', 300: '#c7cbd6',
          400: '#747b8c', 500: '#626a7a', 600: '#4e5667', 700: '#d9dce5',
          800: '#e7e9ef', 850: '#f4f5f9', 900: '#ffffff', 950: '#f7f8fc'
        },
        white: '#172033'
      }
    },
  },
  plugins: [],
}
