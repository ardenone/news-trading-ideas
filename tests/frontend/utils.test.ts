import { describe, it, expect } from 'vitest';
import { formatDate, getConfidenceColor, getPriorityIcon, truncateText } from '../../src/frontend/src/lib/utils';

describe('Utility Functions', () => {
  describe('formatDate', () => {
    it('formats recent dates correctly', () => {
      const now = new Date();
      const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

      expect(formatDate(fiveMinutesAgo.toISOString())).toBe('5 minutes ago');
    });

    it('formats just now correctly', () => {
      const now = new Date();
      expect(formatDate(now.toISOString())).toBe('just now');
    });
  });

  describe('getConfidenceColor', () => {
    it('returns correct colors for confidence levels', () => {
      expect(getConfidenceColor('high')).toContain('text-green-600');
      expect(getConfidenceColor('medium')).toContain('text-yellow-600');
      expect(getConfidenceColor('low')).toContain('text-gray-600');
    });
  });

  describe('getPriorityIcon', () => {
    it('returns fire emoji for high source count', () => {
      expect(getPriorityIcon(10)).toBe('🔥');
    });

    it('returns lightning emoji for medium source count', () => {
      expect(getPriorityIcon(5)).toBe('⚡');
    });

    it('returns newspaper emoji for low source count', () => {
      expect(getPriorityIcon(2)).toBe('📰');
    });
  });

  describe('truncateText', () => {
    it('truncates text longer than max length', () => {
      const longText = 'This is a very long text that should be truncated';
      expect(truncateText(longText, 20)).toBe('This is a very long ...');
    });

    it('does not truncate text shorter than max length', () => {
      const shortText = 'Short text';
      expect(truncateText(shortText, 20)).toBe('Short text');
    });
  });
});
