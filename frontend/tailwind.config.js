export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07111f",
        ocean: "#0f766e",
        aurora: "#22d3ee",
        saffron: "#f59e0b",
        coral: "#e11d48",
        steel: "#526176",
        paper: "#eef5f9",
        midnight: "#07111f"
      },
      boxShadow: {
        crisp: "0 16px 42px rgba(7, 17, 31, 0.10)",
        glow: "0 18px 55px rgba(34, 211, 238, 0.18)"
      }
    }
  },
  plugins: []
};
