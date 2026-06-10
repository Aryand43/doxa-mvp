// Test-only setup: register jest-dom matchers and unmount React trees
// between tests. No product code lives here.
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

afterEach(() => {
  cleanup();
});
