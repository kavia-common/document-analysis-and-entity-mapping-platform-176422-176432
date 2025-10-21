import 'whatwg-fetch';

// Ensure TextEncoder/TextDecoder are present in the Jest (Node) environment BEFORE other setups (e.g., MSW)
const { TextEncoder, TextDecoder } = require('util');
if (!global.TextEncoder) global.TextEncoder = TextEncoder;
if (!global.TextDecoder) global.TextDecoder = TextDecoder;

// Ensure fetch exists on global for Node (jsdom may already provide window.fetch via whatwg-fetch)
if (typeof global.fetch === 'undefined' && typeof window !== 'undefined' && window.fetch) {
  global.fetch = window.fetch;
}

/**
 * If your project uses MSW for API mocking in tests, ensure the server import and lifecycle hooks
 * (server.listen(), server.resetHandlers(), server.close()) are placed AFTER the polyfills above.
 * Example:
 *
 * import { server } from './mocks/server';
 * beforeAll(() => server.listen());
 * afterEach(() => server.resetHandlers());
 * afterAll(() => server.close());
 */
