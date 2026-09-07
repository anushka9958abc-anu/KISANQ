/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        forest: "#143528",
        leaf: "#2f6b45",
        moss: "#6b8f71",
        gold: "#c5922a",
        cream: "#f3ead6",
        soil: "#3a2718",
        straw: "#e7d7a8",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Source Sans 3", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
