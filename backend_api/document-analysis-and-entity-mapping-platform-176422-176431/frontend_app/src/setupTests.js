import 'whatwg-fetch';

// Polyfill TextEncoder/TextDecoder for Node/Jest environment
try {
  // Node 18+ exposes util TextEncoder/TextDecoder
  const { TextEncoder, TextDecoder } = require('util');
  if (!global.TextEncoder) {
    global.TextEncoder = TextEncoder;
  }
  if (!global.TextDecoder) {
    // utf-8 default like browsers
    global.TextDecoder = TextDecoder;
  }
} catch (e) {
  // ignore if not available; tests that need it will skip
}

// Ensure fetch is present (whatwg-fetch adds window.fetch; map to global for Node)
if (typeof global.fetch === 'undefined' && typeof window !== 'undefined' && window.fetch) {
  global.fetch = window.fetch;
}
