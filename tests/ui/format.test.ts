import { describe, expect, it } from 'vitest';
import { ageLabel, workModeLabel, frameCode, salaryLabel, strikePath, tilt } from '../../src/lib/ui/format';

describe('frameCode', () => {
  it('pads the 1-based index to three digits', () => {
    expect(frameCode(0)).toBe('001');
    expect(frameCode(118)).toBe('119');
  });
});

describe('tilt', () => {
  it('is deterministic per id and bounded', () => {
    expect(tilt('job-b9c6199b')).toBe(tilt('job-b9c6199b'));
    for (const id of ['job-00000000', 'job-ffffffff', 'job-472826c7', 'job-a874f990']) {
      expect(Math.abs(tilt(id))).toBeLessThanOrEqual(8);
    }
    expect(new Set(['job-1', 'job-2', 'job-3', 'job-4'].map(tilt)).size).toBeGreaterThan(1);
  });
});

describe('ageLabel', () => {
  it('describes the posting age in Spanish', () => {
    expect(ageLabel('2026-11-16', '2026-11-16')).toBe('hoy');
    expect(ageLabel('2026-11-15', '2026-11-16')).toBe('hace 1 d');
    expect(ageLabel('2026-11-01', '2026-11-16')).toBe('hace 15 d');
    expect(ageLabel(null, '2026-11-16')).toBe('sin fecha');
  });
});

describe('salaryLabel', () => {
  it('formats ranges, single bounds and missing salaries', () => {
    expect(salaryLabel({ min: 80000, max: 100000, currency: 'USD', period: 'yearly' })).toBe('USD 80k–100k / año');
    expect(salaryLabel({ min: 5000, max: null, currency: 'PEN', period: 'monthly' })).toBe('PEN desde 5k / mes');
    expect(salaryLabel({ min: null, max: 40, currency: 'USD', period: 'hourly' })).toBe('USD hasta 40 / hora');
    expect(salaryLabel(null)).toBeNull();
    expect(salaryLabel({ min: null, max: null, currency: 'USD', period: null })).toBeNull();
  });
});

describe('strikePath', () => {
  const ids = ['job-0fff297c', 'job-7e3bdcf5', 'job-049a58de', 'job-17cb282e', 'job-a874f990'];
  const numbers = (d: string) => d.match(/-?[\d.]+/g)!.map(Number);
  const ys = (d: string) => numbers(d).filter((_, i) => i % 2 === 1);

  it('is deterministic per id and varies between ids', () => {
    for (const id of ids) expect(strikePath(id)).toBe(strikePath(id));
    expect(new Set(ids.map(strikePath)).size).toBe(ids.length);
  });

  it('is a wobbling hand stroke, not a ruled line: three curves and a visible bend', () => {
    for (const id of ids) {
      const d = strikePath(id);
      expect(d.match(/C/g)?.length).toBeGreaterThanOrEqual(3);
      const y = ys(d);
      expect(Math.max(...y) - Math.min(...y)).toBeGreaterThanOrEqual(8);
    }
  });

  it('overshoots both ends of its 800x40 box margin and starts at title x-height', () => {
    for (const id of ids) {
      const n = numbers(strikePath(id));
      expect(n[0]).toBeLessThanOrEqual(6);
      expect(Math.max(...n.filter((_, i) => i % 2 === 0))).toBeGreaterThanOrEqual(794);
      for (const y of ys(strikePath(id))) expect(y >= 0 && y <= 40).toBe(true);
      expect(n[1]).toBeGreaterThanOrEqual(13);
      expect(n[1]).toBeLessThanOrEqual(21);
    }
  });
});

describe('workModeLabel', () => {
  it('names the work mode in Spanish and flags relocation', () => {
    expect(workModeLabel('remote', false)).toBe('Remoto');
    expect(workModeLabel('hybrid', false)).toBe('Híbrido');
    expect(workModeLabel('onsite', true)).toBe('Presencial con reubicación');
    expect(workModeLabel('hybrid', true)).toBe('Híbrido con reubicación');
  });
});
