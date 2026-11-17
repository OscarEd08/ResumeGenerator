import { z } from 'zod';

/**
 * Schema of `data/jobs.json`, written by the Python pipeline (`python -m jobs.run`).
 * Mirrors `jobs/models.py` exactly; keep both in sync.
 */

/** Zone thresholds; must match `scoring.zones` in `jobs/config.yaml`. */
export const ZONE_THRESHOLDS = { apply: 85, review: 70 } as const;

export const ZONES = ['apply', 'review', 'low'] as const;
export const MARKETS = ['peru', 'abroad'] as const;
export const WORK_MODES = ['remote', 'hybrid', 'onsite'] as const;
export type WorkMode = (typeof WORK_MODES)[number];

export const SOURCES = ['linkedin', 'indeed', 'glassdoor', 'google', 'remotive', 'remoteok', 'himalayas'] as const;
export const PERIODS = ['yearly', 'monthly', 'weekly', 'daily', 'hourly'] as const;

/** `YYYY-MM-DD`. */
const isoDate = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Expected YYYY-MM-DD');

export const salarySchema = z.strictObject({
  min: z.number().nullable(),
  max: z.number().nullable(),
  currency: z.string().nullable(),
  period: z.enum(PERIODS).nullable(),
});

/** Credit required by the source's API terms: show `name` and link to `url` (no rel="nofollow"). */
export const attributionSchema = z.strictObject({
  name: z.string().min(1),
  url: z.url(),
});

export const jobSchema = z.strictObject({
  /** Stable id used by `/tailor <job-id>`. */
  id: z.string().regex(/^job-[0-9a-f]{8}$/, 'Expected job-<8 hex>'),
  title: z.string().min(1),
  company: z.string().min(1),
  location: z.string().min(1),
  remote: z.boolean(),
  /** Derived at scoring time; on-site postings are kept only when they offer relocation. */
  work_mode: z.enum(WORK_MODES),
  relocation: z.boolean(),
  /** ISO-2 country, null when unknown or multi-country. */
  country: z.string().regex(/^[A-Z]{2}$/).nullable(),
  salary: salarySchema.nullable(),
  /** Apply link (for Himalayas: the `applicationLink`, unchanged). */
  url: z.url(),
  source: z.enum(SOURCES),
  attribution: attributionSchema.nullable(),
  posted_at: isoDate.nullable(),
  expires_at: isoDate.nullable(),
  first_seen: isoDate,
  last_seen: isoDate,
  /** Plain text, trimmed. */
  description: z.string(),
  score: z.number().int().min(0).max(100),
  zone: z.enum(ZONES),
  matched: z.array(z.string().min(1)),
  missing: z.array(z.string().min(1)),
  reasons: z.array(z.string().min(1)),
  market: z.enum(MARKETS),
});

export const sourceSummarySchema = z.strictObject({
  name: z.string().min(1),
  count: z.number().int().min(0),
  error: z.string().min(1).optional(),
});

export const jobsFileSchema = z.strictObject({
  generated_at: z.iso.datetime(),
  sources: z.array(sourceSummarySchema),
  jobs: z.array(jobSchema),
});

export function zoneFor(score: number): (typeof ZONES)[number] {
  if (score >= ZONE_THRESHOLDS.apply) return 'apply';
  if (score >= ZONE_THRESHOLDS.review) return 'review';
  return 'low';
}

export type Salary = z.infer<typeof salarySchema>;
export type Attribution = z.infer<typeof attributionSchema>;
export type Job = z.infer<typeof jobSchema>;
export type SourceSummary = z.infer<typeof sourceSummarySchema>;
export type JobsFile = z.infer<typeof jobsFileSchema>;
