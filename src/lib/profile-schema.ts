import { z } from 'zod';

/**
 * Schema of the profile bank (`data/profile.json`).
 *
 * The bank is derived from `docs/*.md` (the source of truth). Field names
 * intentionally mirror RenderCV entry fields (company, position, location,
 * start_date, end_date, highlights, institution, area, degree, label/details)
 * so a tailored CV can be emitted as RenderCV YAML with a direct mapping.
 */

export const EVIDENCE_LEVELS = ['verified', 'partial'] as const;

/** `YYYY-MM`. */
export const yearMonth = z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/, 'Expected YYYY-MM');
/** `YYYY-MM` or `"present"`. */
export const endDate = z.union([yearMonth, z.literal('present')]);
/** `YYYY` or `YYYY-MM` (education often only states years). */
const yearOrYearMonth = z.string().regex(/^\d{4}(-(0[1-9]|1[0-2]))?$/, 'Expected YYYY or YYYY-MM');

const kebabId = z.string().regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, 'Expected a kebab-case id');
const tag = z.string().regex(/^[a-z0-9][a-z0-9.+#/-]*$/, 'Tags must be lowercase keywords');

export const sourceSchema = z.strictObject({
  /** Repository-relative path to the doc, e.g. `docs/bertoni-experience.md`. */
  path: z.string().regex(/^docs\/[^\s]+\.md$/, 'Expected a docs/*.md path'),
  /** Heading of the doc section the claim comes from. */
  section: z.string().min(1),
});

export const highlightSchema = z.strictObject({
  id: kebabId,
  /** English, CV-ready wording. */
  text: z.string().min(1),
  /** Spanish wording, when the source provides one. */
  text_es: z.string().min(1).optional(),
  tags: z.array(tag).min(1),
  evidence: z.enum(EVIDENCE_LEVELS),
  /** Internal project/client label the highlight belongs to (may be confidential, see entry note). */
  project: z.string().min(1).optional(),
  source: sourceSchema,
});

const roleStepSchema = z.strictObject({
  position: z.string().min(1),
  start_date: yearMonth,
  end_date: endDate,
});

export const experienceSchema = z.strictObject({
  id: kebabId,
  company: z.string().min(1),
  position: z.string().min(1),
  location: z.string().min(1).optional(),
  start_date: yearMonth,
  end_date: endDate,
  /** One-line context shown under the entry (RenderCV `summary`). */
  summary: z.string().min(1).optional(),
  /** Title progression inside the same company, oldest first. */
  progression: z.array(roleStepSchema).optional(),
  /** Present when the docs flag client names as possibly confidential. */
  client_confidential: z.string().min(1).optional(),
  highlights: z.array(highlightSchema).min(1),
});

export const projectSchema = z.strictObject({
  id: kebabId,
  name: z.string().min(1),
  summary: z.string().min(1).optional(),
  url: z.url().optional(),
  start_date: yearMonth,
  end_date: endDate,
  stack: z.array(z.string().min(1)).min(1),
  client_confidential: z.string().min(1).optional(),
  highlights: z.array(highlightSchema).min(1),
});

export const educationSchema = z.strictObject({
  id: kebabId,
  institution: z.string().min(1),
  degree: z.string().min(1),
  area: z.string().min(1),
  location: z.string().min(1).optional(),
  start_date: yearOrYearMonth,
  end_date: z.union([yearOrYearMonth, z.literal('present')]),
  highlights: z.array(highlightSchema),
});

export const languageSchema = z.strictObject({
  language: z.string().min(1),
  level: z.string().min(1),
});

export const basicsSchema = z.strictObject({
  name: z.string().min(1),
  headline: z.string().min(1),
  summary: z.string().min(1).optional(),
  location: z.string().min(1),
  email: z.email(),
  phone: z.string().regex(/^\+\d[\d ]+$/, 'Expected international phone format'),
  linkedin: z.string().regex(/^[A-Za-z0-9-]+$/, 'LinkedIn username only, not a URL'),
  github: z.string().regex(/^[A-Za-z0-9-]+$/).optional(),
  languages: z.array(languageSchema).min(1),
});

/** Skill groups, in the order of the reference PDF. */
export const SKILL_GROUPS = [
  'Backend',
  'Frontend',
  'Data',
  'Cloud and delivery',
  'Quality',
  'AI-assisted development',
  'Languages',
] as const;

export const skillGroupSchema = z.strictObject({
  label: z.enum(SKILL_GROUPS),
  details: z.array(z.string().min(1)).min(1),
});

export const profileSchema = z.strictObject({
  $schema_version: z.literal(1),
  basics: basicsSchema,
  experience: z.array(experienceSchema).min(1),
  projects: z.array(projectSchema),
  education: z.array(educationSchema),
  skills: z.array(skillGroupSchema).min(1),
});

export type EvidenceLevel = (typeof EVIDENCE_LEVELS)[number];
export type Highlight = z.infer<typeof highlightSchema>;
export type Experience = z.infer<typeof experienceSchema>;
export type Project = z.infer<typeof projectSchema>;
export type Education = z.infer<typeof educationSchema>;
export type Profile = z.infer<typeof profileSchema>;
