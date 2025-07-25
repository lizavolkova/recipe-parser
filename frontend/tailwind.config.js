/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      './pages/**/*.{js,ts,jsx,tsx,mdx}',
      './components/**/*.{js,ts,jsx,tsx,mdx}',
      './app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
      extend: {
        animation: {
          'bounce': 'bounce 2s infinite',
          'spin': 'spin 1s linear infinite',
        },
        keyframes: {
          bounce: {
            '0%, 100%': {
              transform: 'translateY(-25%)',
              animationTimingFunction: 'cubic-bezier(0.8,0,1,1)',
            },
            '50%': {
              transform: 'none',
              animationTimingFunction: 'cubic-bezier(0,0,0.2,1)',
            },
          }
        },
        backgroundImage: {
          'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
          'gradient-conic':
            'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        },
      },
    },
    plugins: [],
  }
