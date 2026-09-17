/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './landing.html',
    './crear-empresa.html',
  ],
  theme: {
    extend: {
      colors: {
        teal: '#2DD4BF',
        'teal-dark': '#14B8A6',
        navy: '#0F172A',
        'navy-dark': '#020617',
        orange: '#F97316',
        violet: '#8B5CF6',
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4,0,0.6,1) infinite',
      },
      keyframes: {
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
      },
    },
  },
  plugins: [],
};
