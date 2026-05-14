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
          primary:        '#1C2B3A',  // Deep slate — nav, headers, footers
          'primary-dark': '#122130',  // Darker slate — hover states
          'primary-mid':  '#243649',  // Mid slate — gradient midpoint
          'primary-muted':'#2E4257',  // Muted slate — mobile menu
          secondary:      '#FF6B2B',  // Safety orange — primary CTA buttons
          'secondary-dark':'#E05520', // Deeper orange — hover on CTA
          accent:         '#FFE5D9',  // Soft peach — highlights, tags
          'accent-dark':  '#FCCFBB',  // Deeper peach — hover on accent
        },
        risk: {
          low:      '#16a34a',
          medium:   '#ca8a04',
          high:     '#ea580c',
          critical: '#dc2626',
        },

        // Legacy aliases — kept so nothing breaks
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