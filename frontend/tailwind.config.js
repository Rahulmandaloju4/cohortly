/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0F172A',      // Slate 900
          sidebar: '#1E293B',   // Slate 800
          border: '#334155',    // Slate 700
          primary: '#2563EB',   // Blue 600
          primaryHover: '#1D4ED8', // Blue 700
          accent: '#3B82F6',    // Blue 500
          surface: '#FFFFFF',
          background: '#F8FAFC',// Slate 50
          success: '#10B981',   // Emerald 500
          warning: '#F59E0B',   // Amber 500
          danger: '#EF4444',    // Rose 500
          purple: '#8B5CF6',    // Violet 500
        }
      }
    },
  },
  plugins: [],
}
