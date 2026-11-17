// CLI: validate data/jobs.json against the zod schema.
// Run with `npm run validate:jobs` (Node >= 22.18 strips TypeScript types natively).
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { jobsFileSchema, zoneFor } from './jobs-schema.ts';

const jobsPath = resolve(process.cwd(), 'data/jobs.json');

let raw: unknown;
try {
  raw = JSON.parse(readFileSync(jobsPath, 'utf8'));
} catch (error) {
  console.error(`Cannot read ${jobsPath}: ${(error as Error).message}`);
  process.exit(1);
}

const result = jobsFileSchema.safeParse(raw);
if (!result.success) {
  console.error('data/jobs.json is INVALID:');
  for (const issue of result.error.issues) {
    console.error(`  - ${issue.path.join('.') || '(root)'}: ${issue.message}`);
  }
  process.exit(1);
}

const { jobs, sources } = result.data;
const problems: string[] = [];
const ids = new Set<string>();
for (const job of jobs) {
  if (ids.has(job.id)) problems.push(`duplicate id ${job.id}`);
  ids.add(job.id);
  if (job.zone !== zoneFor(job.score)) problems.push(`${job.id}: zone ${job.zone} does not match score ${job.score}`);
}
if (problems.length) {
  console.error('data/jobs.json is INVALID:');
  for (const problem of problems) console.error(`  - ${problem}`);
  process.exit(1);
}

const count = (zone: string) => jobs.filter((j) => j.zone === zone).length;
const failed = sources.filter((s) => s.error).map((s) => s.name);
console.log(
  `data/jobs.json is valid: ${jobs.length} jobs (apply ${count('apply')}, review ${count('review')}, low ${count('low')}), ` +
    `${sources.length} sources${failed.length ? ` (errors: ${failed.join(', ')})` : ''}.`,
);
