import { isStatus, type Status } from './status';

export type Market = 'all' | 'abroad' | 'peru';
export type MinScore = 0 | 70 | 85;

export interface Filter {
  market: Market;
  minScore: MinScore;
  onlyNew: boolean;
  status: 'all' | Status;
  q: string;
}

export interface FilterJob {
  title: string;
  company: string;
  location: string;
  matched: string[];
  market: 'peru' | 'abroad';
  score: number;
}

export const DEFAULT_FILTER: Filter = { market: 'all', minScore: 0, onlyNew: false, status: 'all', q: '' };

/** Lowercases and strips diacritics so "Perú" matches "peru". */
export function normalize(text: string): string {
  return text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

export function searchText(job: FilterJob): string {
  return normalize([job.title, job.company, job.location, ...job.matched].join(' '));
}

export function matchesFilter(
  job: FilterJob,
  filter: Filter,
  ctx: { status: Status; isNew: boolean },
  haystack: string = searchText(job),
): boolean {
  if (filter.market !== 'all' && job.market !== filter.market) return false;
  if (job.score < filter.minScore) return false;
  if (filter.onlyNew && !ctx.isNew) return false;
  if (filter.status !== 'all' && ctx.status !== filter.status) return false;
  const terms = normalize(filter.q).split(/\s+/).filter(Boolean);
  return terms.every((term) => haystack.includes(term));
}

/** Query-string keys are Spanish because the URL is user-facing. */
export function parseFilter(params: URLSearchParams): Filter {
  const market = params.get('mercado');
  const min = Number(params.get('min'));
  const status = params.get('estado');
  return {
    market: market === 'abroad' || market === 'peru' ? market : 'all',
    minScore: min === 70 || min === 85 ? min : 0,
    onlyNew: params.get('nuevas') === '1',
    status: isStatus(status) ? status : 'all',
    q: params.get('q') ?? '',
  };
}

export function serializeFilter(filter: Filter): string {
  const params = new URLSearchParams();
  if (filter.market !== 'all') params.set('mercado', filter.market);
  if (filter.minScore) params.set('min', String(filter.minScore));
  if (filter.onlyNew) params.set('nuevas', '1');
  if (filter.status !== 'all') params.set('estado', filter.status);
  if (filter.q) params.set('q', filter.q);
  return params.toString();
}
