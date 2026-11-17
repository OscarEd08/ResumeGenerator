// CLI: validate data/profile.json against the zod schema.
// Run with `npm run validate:profile` (Node >= 22.18 strips TypeScript types natively).
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { profileSchema } from './profile-schema.ts';

const profilePath = resolve(process.cwd(), 'data/profile.json');

let raw: unknown;
try {
  raw = JSON.parse(readFileSync(profilePath, 'utf8'));
} catch (error) {
  console.error(`Cannot read ${profilePath}: ${(error as Error).message}`);
  process.exit(1);
}

const result = profileSchema.safeParse(raw);
if (!result.success) {
  console.error('data/profile.json is INVALID:');
  for (const issue of result.error.issues) {
    console.error(`  - ${issue.path.join('.') || '(root)'}: ${issue.message}`);
  }
  process.exit(1);
}

const profile = result.data;
const entries = [...profile.experience, ...profile.projects, ...profile.education];
const highlights = entries.flatMap((e) => e.highlights);
const partial = highlights.filter((h) => h.evidence === 'partial').length;
console.log(
  `data/profile.json is valid: ${profile.experience.length} experience, ${profile.projects.length} projects, ` +
    `${profile.education.length} education, ${highlights.length} highlights (${partial} partial).`,
);
