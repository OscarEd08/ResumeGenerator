import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { EVIDENCE_LEVELS, profileSchema, type Profile } from '../src/lib/profile-schema';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const profilePath = resolve(repoRoot, 'data/profile.json');

function loadRaw(): unknown {
  return JSON.parse(readFileSync(profilePath, 'utf8'));
}

function loadProfile(): Profile {
  return profileSchema.parse(loadRaw());
}

function allHighlights(profile: Profile) {
  return [
    ...profile.experience.flatMap((e) => e.highlights),
    ...profile.projects.flatMap((p) => p.highlights),
    ...profile.education.flatMap((e) => e.highlights),
  ];
}

const YEAR_MONTH = /^\d{4}-(0[1-9]|1[0-2])$/;
const YEAR_OR_YEAR_MONTH = /^\d{4}(-(0[1-9]|1[0-2]))?$/;

describe('data/profile.json', () => {
  it('parses against the zod schema', () => {
    const result = profileSchema.safeParse(loadRaw());
    expect(result.success, result.success ? '' : JSON.stringify(result.error.issues, null, 2)).toBe(true);
  });

  it('contains experience entries and highlights', () => {
    const profile = loadProfile();
    expect(profile.experience.length).toBeGreaterThan(0);
    expect(allHighlights(profile).length).toBeGreaterThan(0);
  });

  it('has unique highlight ids', () => {
    const ids = allHighlights(loadProfile()).map((h) => h.id);
    const duplicates = ids.filter((id, i) => ids.indexOf(id) !== i);
    expect(duplicates).toEqual([]);
  });

  it('has unique experience and project ids', () => {
    const profile = loadProfile();
    const ids = [...profile.experience, ...profile.projects, ...profile.education].map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('only uses allowed evidence values', () => {
    const raw = loadRaw() as { experience: { highlights: { evidence: string }[] }[]; projects: { highlights: { evidence: string }[] }[] };
    const values = [...raw.experience, ...raw.projects].flatMap((e) => e.highlights.map((h) => h.evidence));
    const invalid = values.filter((v) => !(EVIDENCE_LEVELS as readonly string[]).includes(v));
    expect(invalid).toEqual([]);
  });

  it('points every highlight source to an existing doc file', () => {
    const missing = allHighlights(loadProfile())
      .map((h) => h.source.path)
      .filter((p) => !existsSync(resolve(repoRoot, p)));
    expect(missing).toEqual([]);
  });

  it('points every highlight source to a heading that exists in that doc', () => {
    const headingsByPath = new Map<string, string[]>();
    const missing = allHighlights(loadProfile())
      .filter((h) => {
        if (!headingsByPath.has(h.source.path)) {
          const doc = readFileSync(resolve(repoRoot, h.source.path), 'utf8');
          headingsByPath.set(h.source.path, doc.split(/\r?\n/).filter((l) => /^#{1,6}\s/.test(l)));
        }
        return !headingsByPath.get(h.source.path)!.some((line) => line.includes(h.source.section));
      })
      .map((h) => `${h.id} -> ${h.source.path} # ${h.source.section}`);
    expect(missing).toEqual([]);
  });

  it('uses well-formed dates (YYYY-MM, end may be "present") with start <= end', () => {
    const profile = loadProfile();
    const dated = [
      ...profile.experience,
      ...profile.experience.flatMap((e) => (e.progression ?? []).map((r) => ({ ...r, id: `${e.id}:${r.position}` }))),
      ...profile.projects,
    ];
    for (const entry of dated) {
      expect(entry.start_date, entry.id).toMatch(YEAR_MONTH);
      if (entry.end_date !== 'present') {
        expect(entry.end_date, entry.id).toMatch(YEAR_MONTH);
        expect(entry.start_date <= entry.end_date, entry.id).toBe(true);
      }
    }
    // Education may only state years (YYYY) as in the reference CV.
    for (const entry of profile.education) {
      expect(entry.start_date, entry.id).toMatch(YEAR_OR_YEAR_MONTH);
      if (entry.end_date !== 'present') {
        expect(entry.end_date, entry.id).toMatch(YEAR_OR_YEAR_MONTH);
        expect(entry.start_date <= entry.end_date, entry.id).toBe(true);
      }
    }
  });

  it('rejects an invalid evidence value through the schema', () => {
    const raw = loadRaw() as { experience: { highlights: { evidence: string }[] }[] };
    raw.experience[0]!.highlights[0]!.evidence = 'unverified';
    expect(profileSchema.safeParse(raw).success).toBe(false);
  });

  it('rejects a malformed date through the schema', () => {
    const raw = loadRaw() as { experience: { start_date: string }[] };
    raw.experience[0]!.start_date = '2024/01';
    expect(profileSchema.safeParse(raw).success).toBe(false);
  });
});
