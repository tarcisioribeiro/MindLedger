/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Oxygen',
          'Ubuntu',
          'Cantarell',
          'Fira Sans',
          'Droid Sans',
          'Helvetica Neue',
          'sans-serif',
        ],
      },
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        success: {
          DEFAULT: 'hsl(var(--success))',
          foreground: 'hsl(var(--success-foreground))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          foreground: 'hsl(var(--warning-foreground))',
        },
        info: {
          DEFAULT: 'hsl(var(--info))',
          foreground: 'hsl(var(--info-foreground))',
        },
        category: {
          finance: 'hsl(var(--category-finance))',
          health: 'hsl(var(--category-health))',
          studies: 'hsl(var(--category-studies))',
          spiritual: 'hsl(var(--category-spiritual))',
          exercise: 'hsl(var(--category-exercise))',
          nutrition: 'hsl(var(--category-nutrition))',
          work: 'hsl(var(--category-work))',
          leisure: 'hsl(var(--category-leisure))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'dialog-overlay-show': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'dialog-overlay-hide': {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },
        'dialog-content-show': {
          from: {
            opacity: '0',
            transform: 'translate(-50%, -48%) scale(0.96)',
          },
          to: {
            opacity: '1',
            transform: 'translate(-50%, -50%) scale(1)',
          },
        },
        'dialog-content-hide': {
          from: {
            opacity: '1',
            transform: 'translate(-50%, -50%) scale(1)',
          },
          to: {
            opacity: '0',
            transform: 'translate(-50%, -48%) scale(0.96)',
          },
        },
        'slide-up-fade': {
          from: {
            opacity: '0',
            transform: 'translate(-50%, -45%) scale(0.95)',
          },
          to: {
            opacity: '1',
            transform: 'translate(-50%, -50%) scale(1)',
          },
        },
        'slide-down-fade': {
          from: {
            opacity: '0',
            transform: 'translate(-50%, -55%) scale(0.95)',
          },
          to: {
            opacity: '1',
            transform: 'translate(-50%, -50%) scale(1)',
          },
        },
        'bounce-in': {
          '0%': {
            opacity: '0',
            transform: 'translate(-50%, -50%) scale(0.3)',
          },
          '50%': {
            transform: 'translate(-50%, -50%) scale(1.05)',
          },
          '70%': {
            transform: 'translate(-50%, -50%) scale(0.9)',
          },
          '100%': {
            opacity: '1',
            transform: 'translate(-50%, -50%) scale(1)',
          },
        },
        'shake': {
          '0%, 100%': { transform: 'translate(-50%, -50%) translateX(0)' },
          '10%, 30%, 50%, 70%, 90%': { transform: 'translate(-50%, -50%) translateX(-4px)' },
          '20%, 40%, 60%, 80%': { transform: 'translate(-50%, -50%) translateX(4px)' },
        },
        // Animações para Toast
        'toast-slide-in-right': {
          from: {
            opacity: '0',
            transform: 'translateX(100%)',
          },
          to: {
            opacity: '1',
            transform: 'translateX(0)',
          },
        },
        'toast-slide-out-right': {
          from: {
            opacity: '1',
            transform: 'translateX(0)',
          },
          to: {
            opacity: '0',
            transform: 'translateX(100%)',
          },
        },
        'toast-slide-in-bottom': {
          from: {
            opacity: '0',
            transform: 'translateY(100%)',
          },
          to: {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        'toast-fade-in': {
          from: {
            opacity: '0',
            transform: 'scale(0.95)',
          },
          to: {
            opacity: '1',
            transform: 'scale(1)',
          },
        },
        'toast-fade-out': {
          from: {
            opacity: '1',
            transform: 'scale(1)',
          },
          to: {
            opacity: '0',
            transform: 'scale(0.95)',
          },
        },
      },
      animation: {
        'dialog-overlay-show': 'dialog-overlay-show 150ms cubic-bezier(0.16, 1, 0.3, 1)',
        'dialog-overlay-hide': 'dialog-overlay-hide 150ms cubic-bezier(0.16, 1, 0.3, 1)',
        'dialog-content-show': 'dialog-content-show 200ms cubic-bezier(0.16, 1, 0.3, 1)',
        'dialog-content-hide': 'dialog-content-hide 200ms cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-up-fade': 'slide-up-fade 300ms cubic-bezier(0.16, 1, 0.3, 1)',
        'slide-down-fade': 'slide-down-fade 300ms cubic-bezier(0.16, 1, 0.3, 1)',
        'bounce-in': 'bounce-in 400ms cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'shake': 'shake 400ms cubic-bezier(0.36, 0.07, 0.19, 0.97)',
        // Animações para Toast
        'toast-slide-in-right': 'toast-slide-in-right 300ms cubic-bezier(0.21, 1.02, 0.73, 1)',
        'toast-slide-out-right': 'toast-slide-out-right 200ms cubic-bezier(0.06, 0.71, 0.55, 1)',
        'toast-slide-in-bottom': 'toast-slide-in-bottom 300ms cubic-bezier(0.21, 1.02, 0.73, 1)',
        'toast-fade-in': 'toast-fade-in 200ms ease-out',
        'toast-fade-out': 'toast-fade-out 150ms ease-in',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
