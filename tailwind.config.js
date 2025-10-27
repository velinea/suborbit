/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./suborbit/templates/**/*.html", "./suborbit/static/js/**/*.js"],
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
  plugins: [],
};
