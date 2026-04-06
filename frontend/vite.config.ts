import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/agent-tools": "http://localhost:8000",
      "/products": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
