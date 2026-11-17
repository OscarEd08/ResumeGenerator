import { describe, expect, it } from 'vitest';
import {
  DEFAULT_FILTER,
  matchesFilter,
  parseFilter,
  serializeFilter,
  type FilterJob,
} from '../../src/lib/ui/filter';

const job = (over: Partial<FilterJob> = {}): FilterJob => ({
  title: 'Senior .NET Engineer',
  company: 'Andes Digital',
  location: 'Lima, Perú',
  matched: ['dotnet', 'angular'],
  market: 'peru',
  score: 80,
  ...over,
});
const ctx = { status: 'nueva' as const, isNew: false };

describe('matchesFilter', () => {
  it('matches everything with the default filter', () => {
    expect(matchesFilter(job(), DEFAULT_FILTER, ctx)).toBe(true);
  });

  it('filters by market', () => {
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, market: 'abroad' }, ctx)).toBe(false);
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, market: 'peru' }, ctx)).toBe(true);
  });

  it('filters by minimum score (zone)', () => {
    expect(matchesFilter(job({ score: 84 }), { ...DEFAULT_FILTER, minScore: 85 }, ctx)).toBe(false);
    expect(matchesFilter(job({ score: 85 }), { ...DEFAULT_FILTER, minScore: 85 }, ctx)).toBe(true);
    expect(matchesFilter(job({ score: 69 }), { ...DEFAULT_FILTER, minScore: 70 }, ctx)).toBe(false);
  });

  it('keeps only new jobs when onlyNew is set', () => {
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, onlyNew: true }, ctx)).toBe(false);
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, onlyNew: true }, { ...ctx, isNew: true })).toBe(true);
  });

  it('filters by status', () => {
    const f = { ...DEFAULT_FILTER, status: 'preseleccionada' as const };
    expect(matchesFilter(job(), f, ctx)).toBe(false);
    expect(matchesFilter(job(), f, { ...ctx, status: 'preseleccionada' })).toBe(true);
  });

  it('searches title, company, location and keywords ignoring case and accents', () => {
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, q: 'peru' }, ctx)).toBe(true);
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, q: 'ANDES' }, ctx)).toBe(true);
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, q: 'angular' }, ctx)).toBe(true);
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, q: 'net lima' }, ctx)).toBe(true);
    expect(matchesFilter(job(), { ...DEFAULT_FILTER, q: 'java' }, ctx)).toBe(false);
  });
});

describe('parseFilter / serializeFilter', () => {
  it('round-trips a filter through the query string', () => {
    const f = { market: 'abroad', minScore: 70, onlyNew: true, status: 'descartada', q: 'azure' } as const;
    expect(parseFilter(new URLSearchParams(serializeFilter(f)))).toEqual(f);
  });

  it('serializes the default filter to an empty string', () => {
    expect(serializeFilter(DEFAULT_FILTER)).toBe('');
  });

  it('ignores unknown or invalid values', () => {
    const f = parseFilter(new URLSearchParams('mercado=mars&min=12&estado=zzz&nuevas=x'));
    expect(f).toEqual(DEFAULT_FILTER);
  });
});
