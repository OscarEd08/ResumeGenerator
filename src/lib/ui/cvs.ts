/** Generated CVs found in `public/cv/`: `<stem>.pdf` plus optional `<stem>_<n>.png` page renders. */
export interface CvEntry {
  id: string;
  title: string;
  company: string | null;
  pdf: string;
  pages: string[];
  isBase: boolean;
}

export const BASE_CV_ID = 'base';

export function listCvs(files: string[], jobs: { id: string; title: string; company: string }[]): CvEntry[] {
  const byId = new Map(jobs.map((job) => [job.id, job]));
  const stems = files.filter((f) => f.endsWith('.pdf')).map((f) => f.slice(0, -4));
  const entries = stems.map((stem): CvEntry => {
    const job = byId.get(stem);
    const pages = files
      .map((f) => ({ f, m: f.match(/^(.+)_(\d+)\.png$/) }))
      .filter(({ m }) => m?.[1] === stem)
      .sort((a, b) => Number(a.m![2]) - Number(b.m![2]))
      .map(({ f }) => f);
    const isBase = stem === BASE_CV_ID;
    return {
      id: stem,
      title: isBase ? 'CV base' : (job?.title ?? stem),
      company: job?.company ?? null,
      pdf: `${stem}.pdf`,
      pages,
      isBase,
    };
  });
  return entries.sort((a, b) => Number(b.isBase) - Number(a.isBase) || a.id.localeCompare(b.id));
}
