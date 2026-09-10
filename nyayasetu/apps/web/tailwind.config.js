/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FBFAF7",
        ink: "#16233A",
        brand: {
          DEFAULT: "#2E5266",
          light: "#3F6D85",
          dark: "#1E3A48",
        },
        sage: "#DCE3DE",
        severity: {
          informational: "#4C6B8A",
          attention: "#B8863B",
          urgent: "#C2622A",
          emergency: "#A3312A",
        },
      },
      fontFamily: {
        serif: ["Lora", "Georgia", "serif"],
        sans: [
          "Inter",
          "-apple-system",
          "Segoe UI",
          "Noto Sans",
          "Noto Sans Devanagari",
          "sans-serif",
        ],
      },
      maxWidth: {
        prose: "72ch",
      },
    },
  },
  plugins: [],
};
