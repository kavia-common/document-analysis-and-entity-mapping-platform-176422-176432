import 'whatwg-fetch';

// Ensure TextEncoder/TextDecoder are present in the Jest (Node) environment BEFORE other setups (e.g., MSW)
const { TextEncoder, TextDecoder } = require('util');
if (!global.TextEncoder) global.TextEncoder = TextEncoder;
if (!global.TextDecoder) global.TextDecoder = TextDecoder;

// Ensure fetch exists on global for Node
if (typeof global.fetch === 'undefined' && typeof window !== 'undefined' && window.fetch) {
  global.fetch = window.fetch;
}

// Note: Keep any existing MSW server setup (if present) below these polyfills so that libraries relying on them work correctly.
