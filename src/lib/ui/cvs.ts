import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

/** Generated CVs found in `public/cv/`: `<stem>.pdf` plus optional `<stem>_<n>.png` page renders. */
export interface CvEntry {
  id: string;
  title: string;
  company: string | null;
  pdf: string;
  pages: string[];
  isBase: boolean;
  /** File name the download saves as, e.g. `Oscar_Pairazaman_CV_Acme.pdf`. */
  downloadName: string;
  /** Cover letter rendered by `tailor.py letter`, when one exists. */
  letter: { pdf: string; downloadName: string } | null;
}

/** Title and company that `cv/tailor.py build` stores next to a tailored CV, so it outlives its job. */
export interface CvMeta {
  title: string;
  company: string | null;
  /** Friendly PDF name chosen by `tailor.py build`; null in sidecars written before it existed. */
  fileName: string | null;
  /** Friendly cover letter name chosen by `tailor.py letter`; null until a letter exists. */
  letterFileName?: string | null;
}

export const BASE_CV_ID = 'base';
export const BASE_DOWNLOAD_NAME = 'Oscar_Pairazaman_CV.pdf';

const TAILORED_DIR = resolve(process.cwd(), 'cv/tailored');

/** Reads `cv/tailored/<id>.meta.json`; null when it is missing or has no title. */
export function readTailoredMeta(id: string, dir: string = TAILORED_DIR): CvMeta | null {
  try {
    const meta = JSON.parse(readFileSync(join(dir, `${id}.meta.json`), 'utf-8')) as {
      title?: unknown;
      company?: unknown;
      file_name?: unknown;
      letter_file_name?: unknown;
    };
    if (typeof meta.title !== 'string' || meta.title === '') return null;
    return {
      title: meta.title,
      company: typeof meta.company === 'string' && meta.company ? meta.company : null,
      fileName: typeof meta.file_name === 'string' && meta.file_name.endsWith('.pdf') ? meta.file_name : null,
      letterFileName:
        typeof meta.letter_file_name === 'string' && meta.letter_file_name.endsWith('.pdf') ? meta.letter_file_name : null,
    };
  } catch {
    return null;
  }
}

export function listCvs(
  files: string[],
  jobs: { id: string; title: string; company: string }[],
  readMeta: (id: string) => CvMeta | null = readTailoredMeta,
  /** File names in `public/cv/letters/` (`<id>.pdf`). */
  letters: string[] = [],
): CvEntry[] {
  const letterIds = new Set(letters.filter((f) => f.endsWith('.pdf')).map((f) => f.slice(0, -4)));
  const byId = new Map(jobs.map((job) => [job.id, job]));
  const stems = files.filter((f) => f.endsWith('.pdf')).map((f) => f.slice(0, -4));
  const entries = stems.map((stem): CvEntry => {
    const isBase = stem === BASE_CV_ID;
    // Jobs are pruned from jobs.json after 30 days; the sidecar keeps the CV titled after that.
    const meta = isBase ? null : readMeta(stem);
    const job = byId.get(stem) ?? meta;
    const pages = files
      .map((f) => ({ f, m: f.match(/^(.+)_(\d+)\.png$/) }))
      .filter(({ m }) => m?.[1] === stem)
      .sort((a, b) => Number(a.m![2]) - Number(b.m![2]))
      .map(({ f }) => f);
    return {
      id: stem,
      title: isBase ? 'CV base' : (job?.title ?? stem),
      company: job?.company ?? null,
      pdf: `${stem}.pdf`,
      pages,
      isBase,
      downloadName: isBase ? BASE_DOWNLOAD_NAME : (meta?.fileName ?? `${stem}.pdf`),
      letter:
        !isBase && letterIds.has(stem)
          ? { pdf: `letters/${stem}.pdf`, downloadName: meta?.letterFileName ?? `${stem}-cover-letter.pdf` }
          : null,
    };
  });
  return entries.sort((a, b) => Number(b.isBase) - Number(a.isBase) || a.id.localeCompare(b.id));
}
