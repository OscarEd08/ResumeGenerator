/** NUEVA mark: a job stays new from its roll until the owner opens it. Dates are `YYYY-MM-DD`. */
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

export function isNew(
  job: { id: string; first_seen: string },
  ctx: { today: string; visit: Visit | null; opened: Set<string>; latestRoll?: string },
): boolean {
  if (ctx.opened.has(job.id)) return false;
  if (job.first_seen >= ctx.today) return true;
  const since = ctx.visit?.previous ?? ctx.latestRoll ?? null;
  return since !== null && job.first_seen >= since;
}

/** Local calendar date as `YYYY-MM-DD`. */
export function localToday(now: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}
