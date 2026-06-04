export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        ocean: "#2563eb",
        aurora: "#6366f1",
        saffron: "#f59e0b",
        coral: "#e11d48",
        steel: "#5b677a",
        paper: "#f4f7fb",
        midnight: "#111827"
      },
      boxShadow: {
        crisp: "0 14px 34px rgba(15, 23, 42, 0.08)",
        glow: "0 14px 38px rgba(37, 99, 235, 0.18)"
      }
    }
  },
  plugins: []
};
