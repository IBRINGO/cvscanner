const ACRONYMS = new Set(['ai', 'ml', 'ci', 'cd']);

/**
 * Turns a backend SCREAMING_SNAKE_CASE enum value into a readable label:
 * "PROGRAMMING_LANGUAGE" -> "Programming Language", "AI_ML" -> "AI ML".
 * Shared across every feature that renders a raw enum value (categories,
 * seniority, education level, language proficiency, requirement type) so
 * the formatting rule lives in exactly one place (section 54).
 */
export function formatEnumLabel(value: string | null | undefined): string {
  if (!value) return '';
  return value
    .toLowerCase()
    .split('_')
    .map((word) => (ACRONYMS.has(word) ? word.toUpperCase() : (word[0]?.toUpperCase() ?? '') + word.slice(1)))
    .join(' ');
}
