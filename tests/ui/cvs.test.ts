import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { listCvs, readTailoredMeta } from '../../src/lib/ui/cvs';

const jobs = [{ id: 'job-b9c6199b', title: 'Senior Full-Stack Developer', company: 'Resourceful' }];

describe('listCvs', () => {
  it('lists the base CV first with its PNG pages in order', () => {
    const cvs = listCvs(['base_2.png', 'base.pdf', 'base_1.png'], jobs);
    expect(cvs).toEqual([
      { id: 'base', title: 'CV base', company: null, pdf: 'base.pdf', pages: ['base_1.png', 'base_2.png'], isBase: true,
        downloadName: 'Oscar_Pairazaman_CV.pdf', letter: null },
    ]);
  });

  it('titles a tailored CV with its job when the id matches', () => {
    const cvs = listCvs(['base.pdf', 'job-b9c6199b.pdf', 'job-b9c6199b_1.png'], jobs, () => null);
    expect(cvs[1]).toEqual({
      id: 'job-b9c6199b',
      title: 'Senior Full-Stack Developer',
      company: 'Resourceful',
      pdf: 'job-b9c6199b.pdf',
      pages: ['job-b9c6199b_1.png'],
      isBase: false,
      downloadName: 'job-b9c6199b.pdf',
      letter: null,
    });
  });

  it('falls back to the file stem when no job matches', () => {
    const cvs = listCvs(['base.pdf', 'job-deadbeef.pdf'], jobs);
    expect(cvs[1]).toMatchObject({ id: 'job-deadbeef', title: 'job-deadbeef', company: null, pages: [] });
  });

  it('ignores non-PDF files without a PDF and sorts pages numerically', () => {
    const files = ['x.txt', 'orphan_1.png', 'base.pdf', 'base_10.png', 'base_2.png'];
    expect(listCvs(files, jobs)).toEqual([
      { id: 'base', title: 'CV base', company: null, pdf: 'base.pdf', pages: ['base_2.png', 'base_10.png'], isBase: true,
        downloadName: 'Oscar_Pairazaman_CV.pdf', letter: null },
    ]);
  });
});

describe('tailored CV sidecar', () => {
  it('titles a tailored CV from its sidecar once the job was pruned from jobs.json', () => {
    const readMeta = (id: string) => (id === 'job-deadbeef' ? { title: 'Old .NET role', company: 'Acme' } : null);
    const cvs = listCvs(['base.pdf', 'job-deadbeef.pdf', 'job-deadbeef_1.png'], jobs, readMeta);
    expect(cvs[1]).toMatchObject({ id: 'job-deadbeef', title: 'Old .NET role', company: 'Acme', pages: ['job-deadbeef_1.png'] });
  });

  it('downloads a tailored CV under the friendly name from its sidecar, even while the job is live', () => {
    const readMeta = () => ({ title: 'Stale', company: 'Stale', fileName: 'Oscar_Pairazaman_CV_Resourceful.pdf' });
    expect(listCvs(['job-b9c6199b.pdf'], jobs, readMeta)[0].downloadName).toBe('Oscar_Pairazaman_CV_Resourceful.pdf');
    expect(listCvs(['job-b9c6199b.pdf'], jobs, () => null)[0].downloadName).toBe('job-b9c6199b.pdf');
  });

  it('prefers the live job over the sidecar', () => {
    const readMeta = () => ({ title: 'Stale title', company: 'Stale company' });
    const cvs = listCvs(['job-b9c6199b.pdf'], jobs, readMeta);
    expect(cvs[0]).toMatchObject({ title: 'Senior Full-Stack Developer', company: 'Resourceful' });
  });

  it('reads cv/tailored/<id>.meta.json and ignores missing or malformed files', () => {
    const dir = mkdtempSync(join(tmpdir(), 'cv-meta-'));
    try {
      writeFileSync(join(dir, 'job-11111111.meta.json'), JSON.stringify({ id: 'job-11111111', title: 'Backend .NET', company: 'Beta' }));
      writeFileSync(join(dir, 'job-22222222.meta.json'), '{ not json');
      writeFileSync(join(dir, 'job-33333333.meta.json'), JSON.stringify({ title: '' }));
      expect(readTailoredMeta('job-11111111', dir)).toEqual({ title: 'Backend .NET', company: 'Beta', fileName: null, letterFileName: null });
      expect(readTailoredMeta('job-22222222', dir)).toBeNull();
      expect(readTailoredMeta('job-33333333', dir)).toBeNull();
      expect(readTailoredMeta('job-44444444', dir)).toBeNull();
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});

describe('cover letters', () => {
  it('attaches a cover letter found in public/cv/letters, under its friendly name', () => {
    const readMeta = () => ({ title: 'T', company: 'Acme', fileName: null, letterFileName: 'Oscar_Pairazaman_Cover_Letter_Acme.pdf' });
    const [cv] = listCvs(['job-b9c6199b.pdf'], jobs, readMeta, ['job-b9c6199b.pdf']);
    expect(cv.letter).toEqual({ pdf: 'letters/job-b9c6199b.pdf', downloadName: 'Oscar_Pairazaman_Cover_Letter_Acme.pdf' });
  });

  it('has no letter when none was generated, and the base CV never has one', () => {
    expect(listCvs(['job-b9c6199b.pdf'], jobs, () => null, [])[0].letter).toBeNull();
    expect(listCvs(['base.pdf'], jobs, () => null, ['base.pdf'])[0].letter).toBeNull();
  });
});
