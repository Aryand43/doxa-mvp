/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend origin without trailing slash. Empty = same-origin (/api/ai, /health). */
  readonly VITE_API_BASE_URL?: string;
  /** Set to "true" to enable API Inspector + console logging in production builds. */
  readonly VITE_ENABLE_API_DEBUG?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
