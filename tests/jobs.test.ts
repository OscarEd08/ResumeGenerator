import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { jobsFileSchema, ZONE_THRESHOLDS, zoneFor, type JobsFile } from '../src/lib/jobs-schema';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function loadRaw(): unknown {
  return JSON.parse(readFileSync(resolve(repoRoot, 'data/jobs.json'), 'utf8'));
}

function load(): JobsFile {
  return jobsFileSchema.parse(loadRaw());
}

describe('data/jobs.json', () => {
  it('parses against the zod schema', () => {
    const result = jobsFileSchema.safeParse(loadRaw());
    expect(result.success, result.success ? '' : JSON.stringify(result.error.issues, null, 2)).toBe(true);
  });

  it('has unique job ids', () => {
    const ids = load().jobs.map((j) => j.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('keeps scores within 0-100 and sorted descending', () => {
    const scores = load().jobs.map((j) => j.score);
    for (const score of scores) {
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    }
    expect(scores).toEqual([...scores].sort((a, b) => b - a));
  });

  it('assigns zones consistent with the thresholds', () => {
    for (const job of load().jobs) {
      expect(job.zone, job.id).toBe(zoneFor(job.score));
    }
  });

  it('matches the zone thresholds in jobs/config.yaml', () => {
    const config = readFileSync(resolve(repoRoot, 'jobs/config.yaml'), 'utf8');
    expect(config).toMatch(new RegExp(`\\n\\s+apply: ${ZONE_THRESHOLDS.apply}\\b`));
    expect(config).toMatch(new RegExp(`\\n\\s+review: ${ZONE_THRESHOLDS.review}\\b`));
  });

  it('credits sources whose terms require attribution', () => {
    for (const job of load().jobs) {
      if (['remotive', 'remoteok', 'himalayas'].includes(job.source)) {
        expect(job.attribution, job.id).not.toBeNull();
      }
    }
  });

  it('rejects a job with an out-of-range score', () => {
    const file = load();
    if (file.jobs.length === 0) return;
    const broken = { ...file, jobs: [{ ...file.jobs[0], score: 101 }] };
    expect(jobsFileSchema.safeParse(broken).success).toBe(false);
  });
});
