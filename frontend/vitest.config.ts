import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Test-only configuration, kept separate from vite.config.ts so product
// build settings and test settings never bleed into each other.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
