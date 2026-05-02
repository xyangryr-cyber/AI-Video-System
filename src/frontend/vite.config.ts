import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwind from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react(), tailwind()],
  resolve: {
    alias: {
      "@frontend": fileURLToPath(new URL("./", import.meta.url)),
      "@shared": fileURLToPath(new URL("../shared", import.meta.url)),
      "react": fileURLToPath(new URL("./node_modules/react", import.meta.url)),
      "react-dom": fileURLToPath(new URL("./node_modules/react-dom", import.meta.url)),
      "react/jsx-runtime": fileURLToPath(new URL("./node_modules/react/jsx-runtime.js", import.meta.url)),
      "react/jsx-dev-runtime": fileURLToPath(new URL("./node_modules/react/jsx-dev-runtime.js", import.meta.url)),
      "@testing-library/react": fileURLToPath(new URL("./node_modules/@testing-library/react", import.meta.url)),
      "@testing-library/user-event": fileURLToPath(new URL("./node_modules/@testing-library/user-event", import.meta.url)),
      "mock-socket": fileURLToPath(new URL("./node_modules/mock-socket", import.meta.url)),
      "@tanstack/react-query": fileURLToPath(new URL("./node_modules/@tanstack/react-query", import.meta.url)),
      "react-router-dom": fileURLToPath(new URL("./node_modules/react-router-dom", import.meta.url)),
      "dayjs": fileURLToPath(new URL("./node_modules/dayjs", import.meta.url)),
      "zustand": fileURLToPath(new URL("./node_modules/zustand", import.meta.url)),
    },
    conditions: ["browser"],
  },
  server: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
        bypass(req) {
          if (req.url && /\.(ts|tsx|js|jsx)(\?.*)?$/.test(req.url)) {
            return req.url;
          }
        },
      },
      "/ws": {
        target: (process.env.VITE_API_TARGET || "http://localhost:8000").replace(/^http/, "ws"),
        ws: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
    include: [
      "../../tests/unit/frontend/**/*.test.{ts,tsx}",
      "src/**/*.test.{ts,tsx}",
    ],
  },
});
