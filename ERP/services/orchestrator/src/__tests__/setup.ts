// Global test setup
beforeAll(() => {
  // Set test environment variables
  process.env.NODE_ENV = 'test';
  process.env.OPENAI_API_KEY = 'test-key';
  process.env.N8N_BASE_URL = 'http://localhost:5678';
});

afterAll(() => {
  // Cleanup
});
