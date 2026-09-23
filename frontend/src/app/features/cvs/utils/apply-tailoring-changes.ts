import { TailoringChange } from '../../tailoring/models/tailoring.model';
import { CandidateProfile } from '../models/candidate-profile.model';

/**
 * Projects a completed TailoringPlan's accepted changes onto the
 * original CandidateProfile, so the tailored CV can be rendered through
 * the exact same CvDocumentRenderer/template engine as any other CV
 * (section 11: "rendered through the same template engine used by the
 * editor"). Only ACCEPTED changes are applied - a rejected change (one
 * the backend's Truth Layer could not verify) leaves the original text
 * untouched, which is the whole point of that validation step.
 *
 * fact_id follows the backend's own `"<kind>:<index>"` scheme
 * (domain/truth/fact_extraction.py) - this only ever writes into the
 * one field each fact type's `value` actually represents there.
 * Education is intentionally not rewritten: its fact value is a derived
 * "degree - institution" composite, not a single profile field, and the
 * current tailoring engine never targets it in practice (see
 * README "Known limitations").
 */
export function applyTailoringChanges(
  profile: CandidateProfile,
  changes: readonly TailoringChange[],
): CandidateProfile {
  let next = profile;

  for (const change of changes) {
    if (!change.accepted) continue;
    const [kind, indexRaw] = change.fact_id.split(':');
    const index = Number(indexRaw);
    if (!Number.isInteger(index) || index < 0) continue;

    switch (kind) {
      case 'skill':
        next = replaceAt(next, 'skills', index, (item) => ({ ...item, raw_text: change.final_text }));
        break;
      case 'experience':
        next = replaceAt(next, 'experiences', index, (item) => ({ ...item, description: change.final_text }));
        break;
      case 'project':
        next = replaceAt(next, 'projects', index, (item) => ({ ...item, name: change.final_text }));
        break;
      case 'certification':
        next = replaceAt(next, 'certifications', index, (item) => ({ ...item, name: change.final_text }));
        break;
      case 'language':
        next = replaceAt(next, 'languages', index, (item) => ({ ...item, name: change.final_text }));
        break;
      default:
        break;
    }
  }

  return next;
}

function replaceAt<K extends keyof CandidateProfile>(
  profile: CandidateProfile,
  key: K,
  index: number,
  update: (item: CandidateProfile[K] extends (infer Item)[] ? Item : never) => unknown,
): CandidateProfile {
  const list = profile[key] as unknown[];
  if (!Array.isArray(list) || index >= list.length) return profile;
  const nextList = [...list];
  nextList[index] = update(nextList[index] as never);
  return { ...profile, [key]: nextList };
}
