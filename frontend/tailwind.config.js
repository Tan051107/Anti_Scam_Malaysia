/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ─────────────────────────────────────────
        // MAIN THEME — change these to retheme the whole app
        // ─────────────────────────────────────────
        brand: {
          primary:   '#003893',   // navbar, headers, buttons          → bg-brand-primary
          secondary: '#CC0001',   // accents, badges, CTA buttons      → bg-brand-secondary
          accent:    '#FFCC00',   // highlights, active states          → bg-brand-accent
        },

        // Risk level colors
        risk: {
          low:      '#16a34a',    // green
          medium:   '#ca8a04',    // yellow
          high:     '#ea580c',    // orange
          critical: '#dc2626',    // red
        },

        // Keep the original malaysia.* aliases for backward compatibility
        malaysia: {
          red:    '#CC0001',
          blue:   '#003893',
          yellow: '#FFCC00',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
