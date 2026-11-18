/** Build-time data access for pages. Node-only (reads `public/cv/`). */
import { readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import rawJobs from '../../../data/jobs.json';
import { jobsFileSchema, type Job, type JobsFile } from '../jobs-schema';
import { listCvs, type CvEntry } from './cvs';
import { frameCode } from './format';

export interface FramedJob extends Job {
  frame: string;
}

let cached: { file: JobsFile; jobs: FramedJob[] } | null = null;

/** Jobs sorted by score (desc), then most recently seen; each gets its frame code. */
export function loadJobs(): { file: JobsFile; jobs: FramedJob[] } {
  if (cached) return cached;
  const file = jobsFileSchema.parse(rawJobs);
  const jobs = [...file.jobs]
    .sort((a, b) => b.score - a.score || b.first_seen.localeCompare(a.first_seen) || a.id.localeCompare(b.id))
    .map((job, i) => ({ ...job, frame: frameCode(i) }));
  cached = { file, jobs };
  return cached;
}

/** Date of the newest roll (latest `first_seen`), or the generation date when empty. */
export function latestRoll(file: JobsFile): string {
  if (file.jobs.length === 0) return file.generated_at.slice(0, 10);
  return file.jobs.reduce((max, j) => (j.first_seen > max ? j.first_seen : max), '');
}

export function loadCvs(): CvEntry[] {
  let files: string[] = [];
  try {
    files = readdirSync(resolve(process.cwd(), 'public/cv'));
  } catch {
    files = [];
  }
  let letters: string[] = [];
  try {
    letters = readdirSync(resolve(process.cwd(), 'public/cv/letters'));
  } catch {
    letters = [];
  }
  return listCvs(files, loadJobs().jobs, undefined, letters);
}

/** BASE_URL is "/ResumeGenerator" (no trailing slash); join paths safely. */
export function href(path = ''): string {
  const base = import.meta.env.BASE_URL.replace(/\/?$/, '/');
  return base + path.replace(/^\//, '');
}
