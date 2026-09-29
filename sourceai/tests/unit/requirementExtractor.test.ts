// tests/unit/requirementExtractor.test.ts
import { describe, it, expect, jest } from '@jest/globals';
import { extractRequirements } from '@/services/agent/requirementExtractor';
import { generateTextWithFallback } from '@/services/aiRouter';

// Mock the module
jest.mock('@/services/aiRouter');

// Get the mocked function with correct types
const mockedGenerateText = jest.mocked(generateTextWithFallback);

describe('requirementExtractor', () => {
  it('should extract product and quantity', async () => {
    mockedGenerateText.mockResolvedValue(
      JSON.stringify({ product: 't-shirt', quantity: 500 })
    );
    const result = await extractRequirements('Find 500 t-shirts');
    expect(result.product).toBe('t-shirt');
    expect(result.quantity).toBe(500);
  });

  it('should handle missing fields', async () => {
    mockedGenerateText.mockResolvedValue(
      JSON.stringify({ product: 'shoes' })
    );
    const result = await extractRequirements('I need shoes');
    expect(result.product).toBe('shoes');
    expect(result.quantity).toBeUndefined();
  });

  it('should throw on malformed JSON', async () => {
    mockedGenerateText.mockResolvedValue('Not JSON');
    await expect(extractRequirements('test')).rejects.toThrow();
  });
});