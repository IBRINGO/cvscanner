import { CandidateProfile } from './candidate-profile.model';
import { CvSectionRef } from './cv-document.model';

export interface EditorSnapshot {
  profile: CandidateProfile;
  sectionOrder: CvSectionRef[];
  hiddenSectionIds: string[];
}
