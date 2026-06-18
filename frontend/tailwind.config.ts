import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#e6f7f2",
          100: "#cceedd",
          200: "#99ddbb",
          300: "#66cc99",
          400: "#3dbb80",
          500: "#1D9E75",
          600: "#0F6E56",
          700: "#0a5a46",
          800: "#074635",
          900: "#04342C",
          950: "#03261f",
        },
        accent: {
          50: "#fdf2ee",
          100: "#f9d6c8",
          200: "#f5baa2",
          300: "#f19e7c",
          400: "#ed8256",
          500: "#D85A30",
          600: "#c24d26",
          700: "#a03e1e",
          800: "#7e3017",
          900: "#5c2210",
        },
        surface: {
          50: "#fafafa",
          100: "#f0efed",
          200: "#e3e1dd",
          300: "#c5c2bc",
          400: "#a3a098",
          500: "#73716b",
          600: "#52514c",
          700: "#403f3b",
          800: "#262624",
          900: "#171716",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      backgroundImage: {
        "gradient-primary": "linear-gradient(135deg, #0F6E56 0%, #1D9E75 50%, #26b081 100%)",
        "gradient-primary-subtle": "linear-gradient(135deg, #e6f7f2 0%, #cceedd 100%)",
        "gradient-accent": "linear-gradient(135deg, #D85A30 0%, #ed8256 100%)",
        "gradient-success": "linear-gradient(135deg, #10b981 0%, #34d399 100%)",
        "gradient-danger": "linear-gradient(135deg, #ef4444 0%, #f43f5e 100%)",
        "gradient-card": "linear-gradient(135deg, #ffffff 0%, #fafafa 100%)",
        "gradient-hero": "linear-gradient(135deg, #e6f7f2 0%, #cceedd 25%, #e6f7f2 50%, #fdf2ee 75%, #f9d6c8 100%)",
        "gradient-sidebar": "linear-gradient(180deg, #04342C 0%, #0F6E56 50%, #1D9E75 100%)",
        "gradient-header": "linear-gradient(135deg, #ffffff 0%, #fafafa 100%)",
        "gradient-shimmer": "linear-gradient(90deg, transparent, rgba(29, 158, 117, 0.08), transparent)",
      },
      boxShadow: {
        "soft": "0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.03)",
        "elegant": "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(0, 0, 0, 0.02)",
        "elevated": "0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(0, 0, 0, 0.02)",
        "glow-primary": "0 0 24px rgba(29, 158, 117, 0.25)",
        "glow-accent": "0 0 24px rgba(216, 90, 48, 0.25)",
        "glow-success": "0 0 20px rgba(16, 185, 129, 0.15)",
        "modal": "0 25px 60px -15px rgba(0, 0, 0, 0.3)",
        "card-hover": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05)",
        "inner-glow": "inset 0 1px 2px 0 rgba(29, 158, 117, 0.06)",
      },
      borderRadius: {
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "fade-in-up": "fadeInUp 0.5s ease-out",
        "fade-in-down": "fadeInDown 0.3s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "slide-in-left": "slideInLeft 0.3s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
        "shimmer": "shimmer 2s infinite linear",
        "float": "float 3s ease-in-out infinite",
        "spin-slow": "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        fadeInDown: {
          "0%": { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
      transitionTimingFunction: {
        "spring": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "smooth": "cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [],
} satisfies Config;
