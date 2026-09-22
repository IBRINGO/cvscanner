import { formatEnumLabel } from './format-label';

describe('formatEnumLabel', () => {
  it('title-cases a simple snake case value', () => {
    expect(formatEnumLabel('SENIOR')).toBe('Senior');
  });

  it('splits multi-word values', () => {
    expect(formatEnumLabel('PROGRAMMING_LANGUAGE')).toBe('Programming Language');
  });

  it('keeps known acronyms upper-cased', () => {
    expect(formatEnumLabel('AI_ML')).toBe('AI ML');
  });

  it('returns an empty string for null or undefined', () => {
    expect(formatEnumLabel(null)).toBe('');
    expect(formatEnumLabel(undefined)).toBe('');
  });
});
