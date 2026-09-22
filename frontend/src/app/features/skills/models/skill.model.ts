export type SkillDomain =
  | 'SOFTWARE_DEVELOPMENT'
  | 'DATA_AND_AI'
  | 'CLOUD_AND_INFRASTRUCTURE'
  | 'ENGINEERING_PRACTICES';

export type SkillRelationType =
  | 'PARENT_OF'
  | 'CHILD_OF'
  | 'PART_OF_ECOSYSTEM'
  | 'RELATED_TO'
  | 'ALTERNATIVE_TO'
  | 'BUILDS_ON';

export interface SkillRef {
  canonical_name: string;
  category: string;
  domain: SkillDomain;
  description: string | null;
}

export interface RelatedSkill {
  skill: SkillRef;
  relation_type: SkillRelationType;
}

export interface SkillDetail {
  canonical_name: string;
  category: string;
  domain: SkillDomain;
  aliases: string[];
  ecosystem: string | null;
  description: string | null;
  parent: SkillRef | null;
  children: SkillRef[];
  ecosystem_siblings: SkillRef[];
  explicit: RelatedSkill[];
}
