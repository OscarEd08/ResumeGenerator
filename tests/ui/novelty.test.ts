import { describe, expect, it } from 'vitest';
import { isNew, opensFrame, parseOpened, rollVisit, withOpened } from '../../src/lib/ui/novelty';

describe('rollVisit', () => {
  it('starts a first visit with no previous date', () => {
    expect(rollVisit(null, '2026-11-16')).toEqual({ current: '2026-11-16', previous: null });
  });

  it('keeps the same record on a second visit the same day', () => {
    const v = { current: '2026-11-16', previous: '2026-11-10' };
    expect(rollVisit(v, '2026-11-16')).toEqual(v);
  });

  it('moves current to previous on a new day', () => {
    expect(rollVisit({ current: '2026-11-16', previous: null }, '2026-11-18')).toEqual({
      current: '2026-11-18',
      previous: '2026-11-16',
    });
  });
});

describe('isNew', () => {
  const visit = { current: '2026-11-18', previous: '2026-11-16' };

  it('marks jobs first seen today', () => {
    expect(isNew({ id: 'a', first_seen: '2026-11-18' }, { today: '2026-11-18', visit: null, opened: new Set() })).toBe(true);
  });

  it('marks jobs first seen on or after the previous visit', () => {
    expect(isNew({ id: 'a', first_seen: '2026-11-16' }, { today: '2026-11-18', visit, opened: new Set() })).toBe(true);
    expect(isNew({ id: 'a', first_seen: '2026-11-15' }, { today: '2026-11-18', visit, opened: new Set() })).toBe(false);
  });

  it('marks the latest roll as new on a first visit', () => {
    const ctx = { today: '2026-11-20', visit: { current: '2026-11-20', previous: null }, opened: new Set<string>(), latestRoll: '2026-11-16' };
    expect(isNew({ id: 'a', first_seen: '2026-11-16' }, ctx)).toBe(true);
    expect(isNew({ id: 'a', first_seen: '2026-11-15' }, ctx)).toBe(false);
  });

  it('clears the mark once the job was opened', () => {
    expect(isNew({ id: 'a', first_seen: '2026-11-18' }, { today: '2026-11-18', visit, opened: new Set(['a']) })).toBe(false);
  });
});

describe('opening a frame', () => {
  it('records the id once and clears its mark', () => {
    const opened = withOpened(new Set<string>(), 'a');
    expect([...withOpened(opened, 'a')]).toEqual(['a']);
    expect(isNew({ id: 'a', first_seen: '2026-11-18' }, { today: '2026-11-18', visit: null, opened })).toBe(false);
  });

  it('does not mutate the previous set', () => {
    const before = new Set(['a']);
    withOpened(before, 'b');
    expect([...before]).toEqual(['a']);
  });

  it('clears the mark for every way of opening a frame', () => {
    for (const event of ['panel', 'detail', 'status'] as const) expect(opensFrame(event)).toBe(true);
    expect(opensFrame('strip')).toBe(false);
  });
});

describe('parseOpened', () => {
  it('reads a stored list of ids, ignoring non-strings', () => {
    expect([...parseOpened('["a",1,"b"]')]).toEqual(['a', 'b']);
  });

  it('reads missing or corrupt storage as nothing opened', () => {
    expect(parseOpened(null).size).toBe(0);
    expect(parseOpened('{oops').size).toBe(0);
    expect(parseOpened('{"a":1}').size).toBe(0);
  });
});
