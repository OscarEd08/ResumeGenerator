/** Per-job status kept in the browser. `nueva` is the implicit default and is never stored. */
export const STATUSES = ['nueva', 'preseleccionada', 'postulada', 'descartada'] as const;
export type Status = (typeof STATUSES)[number];
export type StatusMap = Record<string, Exclude<Status, 'nueva'>>;

export const STATUS_KEY = 'rg:status';

export function isStatus(value: unknown): value is Status {
  return typeof value === 'string' && (STATUSES as readonly string[]).includes(value);
}

export function statusOf(map: StatusMap, id: string): Status {
  return map[id] ?? 'nueva';
}

/** Applying the status a job already has toggles it back to `nueva`. Returns a new map. */
export function applyStatus(map: StatusMap, id: string, status: Status): StatusMap {
  const next = { ...map };
  if (status === 'nueva' || map[id] === status) delete next[id];
  else next[id] = status;
  return next;
}

/** Parses the stored JSON; anything unreadable yields an empty map. */
export function readStatuses(raw: string | null): StatusMap {
  if (!raw) return {};
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return {};
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {};
  const out: StatusMap = {};
  for (const [id, value] of Object.entries(parsed)) {
    if (isStatus(value) && value !== 'nueva') out[id] = value;
  }
  return out;
}
