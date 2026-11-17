/** NUEVA mark: a job stays new from its roll until the owner opens or decides on it. Dates are `YYYY-MM-DD`. */
import { statusOf, type Status, type StatusMap } from './status';

export interface Visit {
  current: string;
  previous: string | null;
}

export const VISIT_KEY = 'rg:visit';
export const OPENED_KEY = 'rg:opened';

/** Advances the visit record once per day; the previous day's date is the "new since" threshold. */
export function rollVisit(stored: Visit | null, today: string): Visit {
  if (!stored) return { current: today, previous: null };
  if (stored.current === today) return stored;
  return { current: today, previous: stored.current };
}

export function parseVisit(raw: string | null): Visit | null {
  try {
    const v = raw ? JSON.parse(raw) : null;
    if (v && typeof v.current === 'string' && (v.previous === null || typeof v.previous === 'string')) {
      return { current: v.current, previous: v.previous };
    }
  } catch {
    /* corrupt storage reads as a first visit */
  }
  return null;
}

export interface NoveltyContext {
  today: string;
  visit: Visit | null;
  opened: ReadonlySet<string>;
  latestRoll?: string;
  /** The frame's status; any decision (not `nueva`) counts as having opened it. */
  status?: Status;
}

export function isNew(job: { id: string; first_seen: string }, ctx: NoveltyContext): boolean {
  if (ctx.status && ctx.status !== 'nueva') return false;
  if (ctx.opened.has(job.id)) return false;
  if (job.first_seen >= ctx.today) return true;
  const since = ctx.visit?.previous ?? ctx.latestRoll ?? null;
  return since !== null && job.first_seen >= since;
}

/** NUEVOS in the roll meta: the same rule as the per-frame mark, so every page shows the same number. */
export function countNew(
  jobs: readonly { id: string; first_seen: string }[],
  ctx: Omit<NoveltyContext, 'status'> & { statuses: StatusMap },
): number {
  return jobs.filter((job) => isNew(job, { ...ctx, status: statusOf(ctx.statuses, job.id) })).length;
}

/** Local calendar date as `YYYY-MM-DD`. */
export function localToday(now: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/**
 * How the owner meets a frame. Showing it in the desktop panel, opening its detail page or changing its
 * status all count as opening it; only seeing it in the strip keeps the NUEVA mark.
 */
export type FrameEvent = 'strip' | 'panel' | 'detail' | 'status';

export function opensFrame(event: FrameEvent): boolean {
  return event !== 'strip';
}

export function withOpened(opened: ReadonlySet<string>, id: string): Set<string> {
  const next = new Set(opened);
  next.add(id);
  return next;
}

export function parseOpened(raw: string | null): Set<string> {
  try {
    const list = JSON.parse(raw ?? '[]');
    return new Set(Array.isArray(list) ? list.filter((x): x is string => typeof x === 'string') : []);
  } catch {
    return new Set();
  }
}
