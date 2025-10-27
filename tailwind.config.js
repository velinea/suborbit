/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./suborbit/templates/**/*.html",
    "./suborbit/static/js/**/*.js"
  ],
  safelist: [
    "group",
    "group-hover:opacity-100",
    "group-hover:opacity-70",
    "opacity-0",
    "opacity-70",
    "bg-gray-900/80",
    "bg-gray-900/90",
    "z-10",
    "z-20",
    "z-30",
    "absolute",
    "relative"
  ],
  theme: {
    extend: {
      keyframes: {
        fadeIn: {
          "0%": { opacity: 0, transform: "scale(0.98)" },
          "100%": { opacity: 1, transform: "scale(1)" },
        },
      },
      animation: {
        fadeIn: "fadeIn 0.6s ease-out forwards",
      },
    },
  },
  plugins: [
    require("@tailwindcss/line-clamp"),
  ],
};
