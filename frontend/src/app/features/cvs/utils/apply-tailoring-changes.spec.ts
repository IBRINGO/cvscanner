import { TailoringChange } from '../../tailoring/models/tailoring.model';
import { CandidateProfile } from '../models/candidate-profile.model';
import { applyTailoringChanges } from './apply-tailoring-changes';

function profile(): CandidateProfile {
  return {
    full_name: 'Jordan Rivera',
    email: null,
    phone: null,
    location: null,
    links: [],
    summary: null,
    experiences: [
      {
        title: 'Backend Engineer',
        company: 'Acme',
        start_date_raw: '2020',
        end_date_raw: null,
        description: 'Built internal tooling.',
        achievements: [],
        technologies: [],
        seniority: null,
        evidence: null,
      },
    ],
    education: [],
    projects: [],
    certifications: [],
    languages: [],
    skills: [{ raw_text: 'python', skill: null, evidence: null }],
  };
}

function change(overrides: Partial<TailoringChange> = {}): TailoringChange {
  return {
    fact_id: 'experience:0',
    recommendation_title: 'Clarify wording',
    original_text: 'Built internal tooling.',
    final_text: 'Built internal tooling using REST APIs.',
    diff: [],
    accepted: true,
    rejection_reasons: [],
    ...overrides,
  };
}

describe('applyTailoringChanges', () => {
  it('writes an accepted experience change into that experience entry only', () => {
    const result = applyTailoringChanges(profile(), [change()]);
    expect(result.experiences[0].description).toBe('Built internal tooling using REST APIs.');
    expect(result.experiences[0].title).toBe('Backend Engineer');
  });

  it('never applies a rejected change - the original text is preserved', () => {
    const result = applyTailoringChanges(profile(), [change({ accepted: false })]);
    expect(result.experiences[0].description).toBe('Built internal tooling.');
  });

  it('writes a skill change by index without touching other skills', () => {
    const base = profile();
    base.skills.push({ raw_text: 'django', skill: null, evidence: null });
    const result = applyTailoringChanges(base, [
      change({ fact_id: 'skill:1', final_text: 'Django', original_text: 'django' }),
    ]);
    expect(result.skills[0].raw_text).toBe('python');
    expect(result.skills[1].raw_text).toBe('Django');
  });

  it('ignores an out-of-range or malformed fact_id instead of throwing', () => {
    expect(() =>
      applyTailoringChanges(profile(), [
        change({ fact_id: 'experience:9' }),
        change({ fact_id: 'not-a-real-kind:0' }),
        change({ fact_id: 'garbage' }),
      ]),
    ).not.toThrow();
  });

  it('does not mutate the original profile object', () => {
    const original = profile();
    const originalDescription = original.experiences[0].description;
    applyTailoringChanges(original, [change()]);
    expect(original.experiences[0].description).toBe(originalDescription);
  });
});
