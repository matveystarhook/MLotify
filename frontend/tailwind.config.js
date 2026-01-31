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
        // Apple-style dark colors
        dark: {
          bg: '#000000',
          surface: '#1C1C1E',
          elevated: '#2C2C2E',
          card: '#1C1C1E',
          border: '#38383A',
        },
        gray: {
          50: '#F2F2F7',
          100: '#E5E5EA',
          200: '#D1D1D6',
          300: '#C7C7CC',
          400: '#AEAEB2',
          500: '#8E8E93',
          600: '#636366',
          700: '#48484A',
          800: '#3A3A3C',
          900: '#2C2C2E',
        },
        primary: {
          50: '#EBF5FF',
          100: '#E1EFFE',
          200: '#C3DDFD',
          300: '#A4CAFE',
          400: '#76A9FA',
          500: '#3B82F6', // iOS Blue
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        accent: {
          green: '#30D158', // iOS Green
          blue: '#0A84FF',  // iOS Blue
          indigo: '#5E5CE6', // iOS Indigo
          purple: '#BF5AF2', // iOS Purple
          pink: '#FF375F',   // iOS Pink
          red: '#FF453A',    // iOS Red
          orange: '#FF9F0A', // iOS Orange
          yellow: '#FFD60A', // iOS Yellow
        }
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      fontSize: {
        'xs': ['11px', { lineHeight: '16px', letterSpacing: '0.06px' }],
        'sm': ['13px', { lineHeight: '18px', letterSpacing: '-0.08px' }],
        'base': ['15px', { lineHeight: '20px', letterSpacing: '-0.24px' }],
        'lg': ['17px', { lineHeight: '22px', letterSpacing: '-0.41px' }],
        'xl': ['20px', { lineHeight: '25px', letterSpacing: '-0.45px' }],
        '2xl': ['24px', { lineHeight: '28px', letterSpacing: '-0.45px' }],
        '3xl': ['28px', { lineHeight: '34px', letterSpacing: '-0.5px' }],
        '4xl': ['34px', { lineHeight: '41px', letterSpacing: '-0.5px' }],
        '5xl': ['40px', { lineHeight: '48px', letterSpacing: '-0.6px' }],
      },
      spacing: {
        '4.5': '1.125rem',
        '5.5': '1.375rem',
      },
      borderRadius: {
        'ios': '10px',
        'ios-lg': '13px',
        'ios-xl': '16px',
        'ios-2xl': '20px',
      },
      boxShadow: {
        'ios': '0 2px 16px rgba(0, 0, 0, 0.12)',
        'ios-sm': '0 1px 8px rgba(0, 0, 0, 0.08)',
        'ios-lg': '0 4px 24px rgba(0, 0, 0, 0.16)',
        'glow-blue': '0 0 20px rgba(10, 132, 255, 0.3)',
        'glow-green': '0 0 20px rgba(48, 209, 88, 0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        'slide-up': 'slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
        'slide-down': 'slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        'scale-in': 'scaleIn 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        'bounce-subtle': 'bounceSubtle 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(16px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
      },
      backdropBlur: {
        'xs': '2px',
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '24px',
        '3xl': '40px',
      },
    },
  },
  plugins: [],
}