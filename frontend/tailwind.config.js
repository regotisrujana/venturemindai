export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18181b",
        ocean: "#be185d",
        aurora: "#f59e0b",
        saffron: "#f59e0b",
        coral: "#e11d48",
        steel: "#625f6b",
        paper: "#fbf7fa",
        midnight: "#18181b"
      },
      boxShadow: {
        crisp: "0 14px 34px rgba(15, 23, 42, 0.08)",
        glow: "0 14px 38px rgba(190, 24, 93, 0.18)"
      }
    }
  },
  plugins: []
};
