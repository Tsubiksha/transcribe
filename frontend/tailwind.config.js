/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#F8FAFC",
        line: "rgba(255,255,255,0.1)",
        mist: "#0F172A",
        accent: "#8B5CF6",
        coral: "#F97316"
      },
      boxShadow: {
        glow: "0 0 32px rgba(99,102,241,0.28)"
      }
    }
  },
  plugins: []
};
