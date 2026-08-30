/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    'app/templates/**/*.html',
    'app/templates/**/*.htm',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#059669',
        secondary: '#10b981',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-in': 'slideIn 0.2s ease-out',
        'bounce-subtle': 'bounceSubtle 0.6s ease-in-out',
      },
    },
  },
  plugins: [],
}
