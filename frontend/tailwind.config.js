export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        ocean: "#2563eb",
        aurora: "#10b981",
        saffron: "#f59e0b",
        coral: "#e11d48",
        steel: "#5b677a",
        paper: "#f4f7fb",
        midnight: "#10201b"
      },
      boxShadow: {
        crisp: "0 14px 34px rgba(15, 23, 42, 0.08)",
        glow: "0 14px 38px rgba(37, 99, 235, 0.18)"
      }
    }
  },
  plugins: []
};
