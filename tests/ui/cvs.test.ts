import { describe, expect, it } from 'vitest';
import { listCvs } from '../../src/lib/ui/cvs';

const jobs = [{ id: 'job-b9c6199b', title: 'Senior Full-Stack Developer', company: 'Resourceful' }];

describe('listCvs', () => {
  it('lists the base CV first with its PNG pages in order', () => {
    const cvs = listCvs(['base_2.png', 'base.pdf', 'base_1.png'], jobs);
    expect(cvs).toEqual([
      { id: 'base', title: 'CV base', company: null, pdf: 'base.pdf', pages: ['base_1.png', 'base_2.png'], isBase: true },
    ]);
  });

  it('titles a tailored CV with its job when the id matches', () => {
    const cvs = listCvs(['base.pdf', 'job-b9c6199b.pdf', 'job-b9c6199b_1.png'], jobs);
    expect(cvs[1]).toEqual({
      id: 'job-b9c6199b',
      title: 'Senior Full-Stack Developer',
      company: 'Resourceful',
      pdf: 'job-b9c6199b.pdf',
      pages: ['job-b9c6199b_1.png'],
      isBase: false,
    });
  });

  it('falls back to the file stem when no job matches', () => {
    const cvs = listCvs(['base.pdf', 'job-deadbeef.pdf'], jobs);
    expect(cvs[1]).toMatchObject({ id: 'job-deadbeef', title: 'job-deadbeef', company: null, pages: [] });
  });

  it('ignores non-PDF files without a PDF and sorts pages numerically', () => {
    const files = ['x.txt', 'orphan_1.png', 'base.pdf', 'base_10.png', 'base_2.png'];
    expect(listCvs(files, jobs)).toEqual([
      { id: 'base', title: 'CV base', company: null, pdf: 'base.pdf', pages: ['base_2.png', 'base_10.png'], isBase: true },
    ]);
  });
});
