import { describe, expect, it } from 'vitest';
import { ageLabel, frameCode, salaryLabel, tilt } from '../../src/lib/ui/format';

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
