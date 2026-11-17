import { describe, expect, it } from 'vitest';
import { applyStatus, readStatuses, statusOf } from '../../src/lib/ui/status';

describe('applyStatus', () => {
  it('sets a status for a job', () => {
    expect(applyStatus({}, 'job-1', 'preseleccionada')).toEqual({ 'job-1': 'preseleccionada' });
  });

  it('toggles back to nueva when the same status is applied again', () => {
    expect(applyStatus({ 'job-1': 'descartada' }, 'job-1', 'descartada')).toEqual({});
  });

  it('replaces a different status', () => {
    expect(applyStatus({ 'job-1': 'preseleccionada' }, 'job-1', 'postulada')).toEqual({ 'job-1': 'postulada' });
  });

  it('removes the entry when set to nueva and does not mutate the input', () => {
    const before = { 'job-1': 'postulada' as const };
    expect(applyStatus(before, 'job-1', 'nueva')).toEqual({});
    expect(before).toEqual({ 'job-1': 'postulada' });
  });
});

describe('statusOf / readStatuses', () => {
  it('defaults to nueva', () => {
    expect(statusOf({}, 'job-x')).toBe('nueva');
  });

  it('parses stored JSON and drops invalid entries', () => {
    expect(readStatuses('{"a":"postulada","b":"bogus","c":3}')).toEqual({ a: 'postulada' });
  });

  it('survives missing or corrupt storage', () => {
    expect(readStatuses(null)).toEqual({});
    expect(readStatuses('{not json')).toEqual({});
    expect(readStatuses('[1,2]')).toEqual({});
  });
});
