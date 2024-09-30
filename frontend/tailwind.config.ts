import type { Config } from 'tailwindcss';

const defaultTheme = require('tailwindcss/defaultTheme');

export default {
  content: ['./public/index.html', './src/**/*.{vue,ts,js}'],
  theme: {
    fontFamily: {
      sans: ['"Plus Jakarta Sans"', ...defaultTheme.fontFamily.sans],
      display: ['"Raleway"', ...defaultTheme.fontFamily.sans],
      roboto: ['"Roboto"', ...defaultTheme.fontFamily.sans],
    },
    extend: {
      gridTemplateColumns: {
        week: '100px repeat(7, 1fr)',
        day: '100px 1fr',
        context: '28px 1fr',
      },
      maxWidth: {
        '2xs': '16rem',
      },
      maxHeight: {
        lg: '32rem',
        xl: '36rem',
      },
      scale: {
        102: '1.02',
        98: '0.98',
      },
      strokeWidth: {
        3: '3',
      },
      colors: {
        'tb-red': {
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        'blue': {
          50: '#DDEDFF',
          100: '#C8DFFF',
          200: '#A7C9FF',
          300: '#85B2FF',
          400: '#688AEA',
          500: '#4A62D4',
          600: '#2E46B9',
          700: '#1D3297',
          800: '#162676',
          900: '#1B1763',
        }
      },
      boxShadow: {
        light: '0 0 0 1px transparent,0 5px 10px 0 #c8dfff;',
      },
    },
  },
  darkMode: 'class',
  plugins: [require('@tailwindcss/forms')],
} satisfies Config;
