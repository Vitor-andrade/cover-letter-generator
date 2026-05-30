import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Build output is served by FastAPI from src/clg/api/static.
// During dev, API calls are proxied to the local backend.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../src/clg/api/static",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
