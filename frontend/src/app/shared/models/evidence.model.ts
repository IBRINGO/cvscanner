/**
 * Provenance for one extracted fact. `confidence` is EXTRACTION
 * confidence (how sure the parser is that it read/classified the text
 * correctly) - it is never a claim about whether the underlying fact is
 * true. See backend domain/documents/evidence.py for the full rationale.
 */
export interface Evidence {
  page_number: number | null;
  section: string | null;
  text: string;
  confidence: number;
  extraction_method: 'PARSER' | 'RULE' | 'REGEX' | 'MANUAL' | 'LLM' | 'HYBRID';
}

export interface SkillRef {
  canonical_name: string;
  category: string;
}
