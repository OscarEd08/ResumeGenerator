/**
 * Progressive enhancement for every page: per-job status, NUEVA marks, copy buttons,
 * and (on the list page) filters plus the desktop detail panel.
 * The static HTML is complete without this script or without storage.
 */
import { matchesFilter, normalize, parseFilter, serializeFilter, type Filter } from '../lib/ui/filter';
import { isNew, localToday, OPENED_KEY, parseVisit, rollVisit, VISIT_KEY, type Visit } from '../lib/ui/novelty';
import { applyStatus, isStatus, readStatuses, STATUS_KEY, statusOf, type StatusMap } from '../lib/ui/status';

function load(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function save(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* storage unavailable: state lives for this page view only */
  }
}

function readOpened(): Set<string> {
  try {
    const list = JSON.parse(load(OPENED_KEY) ?? '[]');
    return new Set(Array.isArray(list) ? list.filter((x) => typeof x === 'string') : []);
  } catch {
    return new Set();
  }
}

const today = localToday();
const latestRoll = document.body.dataset.roll ?? today;
let statuses: StatusMap = readStatuses(load(STATUS_KEY));
const opened = readOpened();
const visit: Visit = rollVisit(parseVisit(load(VISIT_KEY)), today);
save(VISIT_KEY, JSON.stringify(visit));

const jobNodes = () => document.querySelectorAll<HTMLElement>('[data-job]');

function jobIsNew(el: HTMLElement): boolean {
  const id = el.dataset.job!;
  return isNew({ id, first_seen: el.dataset.firstSeen ?? '' }, { today, visit, opened, latestRoll });
}

function paintStatus(): void {
  for (const el of jobNodes()) el.dataset.status = statusOf(statuses, el.dataset.job!);
  for (const btn of document.querySelectorAll<HTMLButtonElement>('[data-set-status]')) {
    const id = btn.closest<HTMLElement>('[data-status-for]')?.dataset.statusFor;
    if (id) btn.setAttribute('aria-pressed', String(statusOf(statuses, id) === btn.dataset.setStatus));
  }
}

function paintNovelty(): void {
  let count = 0;
  for (const el of document.querySelectorAll<HTMLElement>('[data-job][data-first-seen]')) {
    const fresh = jobIsNew(el);
    if (fresh && el.matches('.frame')) count++;
    el.querySelector<HTMLElement>('[data-new-mark]')?.toggleAttribute('hidden', !fresh);
  }
  const counter = document.querySelector<HTMLElement>('[data-new-count]');
  if (counter && document.querySelector('.frame')) counter.textContent = String(count);
}

function markOpened(id: string): void {
  if (opened.has(id)) return;
  opened.add(id);
  save(OPENED_KEY, JSON.stringify([...opened]));
}

/* Status buttons (list panel and detail page). */
document.addEventListener('click', (event) => {
  const btn = (event.target as Element).closest<HTMLButtonElement>('[data-set-status]');
  if (!btn) return;
  const id = btn.closest<HTMLElement>('[data-status-for]')?.dataset.statusFor;
  const status = btn.dataset.setStatus;
  if (!id || !isStatus(status)) return;
  const before = statusOf(statuses, id);
  statuses = applyStatus(statuses, id, status);
  save(STATUS_KEY, JSON.stringify(statuses));
  paintStatus();
  if (before !== 'preseleccionada' && statusOf(statuses, id) === 'preseleccionada') {
    for (const ring of document.querySelectorAll(`[data-job="${id}"] .ring`)) {
      ring.classList.remove('draw');
      void (ring as SVGElement).getBoundingClientRect();
      ring.classList.add('draw');
    }
  }
  applyFilter?.();
});

/* Copy buttons: Clipboard API, falling back to selecting the command text. */
document.addEventListener('click', async (event) => {
  const btn = (event.target as Element).closest<HTMLButtonElement>('[data-copy]');
  if (!btn) return;
  const text = btn.dataset.copy!;
  const done = (label: string) => {
    const original = btn.dataset.label ?? btn.textContent ?? '';
    btn.dataset.label = original;
    btn.textContent = label;
    btn.classList.toggle('copied', label === 'Copiado');
    setTimeout(() => {
      btn.textContent = original;
      btn.classList.remove('copied');
    }, 1800);
  };
  try {
    await navigator.clipboard.writeText(text);
    done('Copiado');
  } catch {
    const code = btn.parentElement?.querySelector('code');
    if (code) {
      const range = document.createRange();
      range.selectNodeContents(code);
      const sel = window.getSelection();
      sel?.removeAllRanges();
      sel?.addRange(range);
    }
    done('Selecciona y copia');
  }
});

/* Detail page: opening a job clears its NUEVA mark. */
const page = document.querySelector<HTMLElement>('[data-detail-page]');
if (page?.dataset.job) markOpened(page.dataset.job);

/* List page: filters, empty states and the desktop detail panel. */
let applyFilter: (() => void) | null = null;
const strip = document.querySelector<HTMLElement>('[data-strip]');
if (strip) initList(strip);

function initList(strip: HTMLElement): void {
  const form = document.querySelector<HTMLFormElement>('[data-filters]')!;
  const search = form.querySelector<HTMLInputElement>('input[name="q"]')!;
  const estado = form.querySelector<HTMLSelectElement>('select[name="estado"]')!;
  const rows = [...strip.querySelectorAll<HTMLElement>('.frame')];
  const shown = document.querySelector<HTMLElement>('[data-shown]');
  const empty = document.querySelector<HTMLElement>('[data-empty-filter]');
  const panels = document.querySelector<HTMLElement>('[data-panels]');
  const desktop = window.matchMedia('(min-width: 761px)');
  let filter: Filter = parseFilter(new URLSearchParams(location.search));

  const haystacks = new Map(rows.map((r) => [r, normalize(r.dataset.search ?? '')]));

  function paintControls(): void {
    for (const b of form.querySelectorAll<HTMLButtonElement>('[data-market]')) {
      b.setAttribute('aria-pressed', String(b.dataset.market === filter.market));
    }
    for (const b of form.querySelectorAll<HTMLButtonElement>('[data-min]')) {
      b.setAttribute('aria-pressed', String(Number(b.dataset.min) === filter.minScore));
    }
    form.querySelector('[data-only-new]')?.setAttribute('aria-pressed', String(filter.onlyNew));
    if (search.value !== filter.q) search.value = filter.q;
    estado.value = filter.status;
    for (const a of document.querySelectorAll<HTMLAnchorElement>('[data-nav]')) {
      const isShortlist = a.dataset.nav === 'preseleccionadas';
      const active = isShortlist ? filter.status === 'preseleccionada' : filter.status !== 'preseleccionada';
      if (a.dataset.nav === 'ofertas' || isShortlist) {
        if (active) a.setAttribute('aria-current', 'page');
        else a.removeAttribute('aria-current');
      }
    }
  }

  applyFilter = () => {
    let visible = 0;
    for (const row of rows) {
      const job = {
        title: '',
        company: '',
        location: '',
        matched: [],
        market: row.dataset.market as 'peru' | 'abroad',
        score: Number(row.dataset.score),
      };
      const ok = matchesFilter(
        job,
        filter,
        { status: statusOf(statuses, row.dataset.job!), isNew: jobIsNew(row) },
        haystacks.get(row),
      );
      row.hidden = !ok;
      if (ok) visible++;
    }
    if (shown) shown.textContent = String(visible);
    if (empty) empty.hidden = visible > 0 || rows.length === 0;
    paintControls();
  };

  function commit(next: Partial<Filter>): void {
    filter = { ...filter, ...next };
    const qs = serializeFilter(filter);
    history.replaceState(null, '', qs ? `?${qs}${location.hash}` : location.pathname + location.hash);
    applyFilter!();
  }

  form.addEventListener('submit', (e) => e.preventDefault());
  form.addEventListener('click', (e) => {
    const b = (e.target as Element).closest<HTMLButtonElement>('button');
    if (!b) return;
    if (b.dataset.market) commit({ market: b.dataset.market as Filter['market'] });
    else if (b.dataset.min) {
      const min = Number(b.dataset.min) as Filter['minScore'];
      commit({ minScore: filter.minScore === min ? 0 : min });
    } else if (b.hasAttribute('data-only-new')) commit({ onlyNew: !filter.onlyNew });
  });
  search.addEventListener('input', () => commit({ q: search.value }));
  estado.addEventListener('change', () => commit({ status: estado.value as Filter['status'] }));
  document.querySelector('[data-clear-filters]')?.addEventListener('click', () => {
    commit({ market: 'all', minScore: 0, onlyNew: false, status: 'all', q: '' });
  });

  function select(id: string, opts: { focus?: boolean; open?: boolean } = {}): void {
    if (!panels) return;
    for (const p of panels.querySelectorAll<HTMLElement>('[data-panel]')) p.hidden = p.dataset.panel !== id;
    for (const r of rows) {
      const on = r.dataset.job === id;
      r.classList.toggle('sel', on);
      const link = r.querySelector('a[data-select]');
      if (on) link?.setAttribute('aria-current', 'true');
      else link?.removeAttribute('aria-current');
    }
    if (opts.open !== false) {
      markOpened(id);
      paintNovelty();
    }
    if (opts.focus) panels.querySelector<HTMLElement>(`[data-panel="${id}"] h2`)?.focus({ preventScroll: true });
  }

  strip.addEventListener('click', (e) => {
    const link = (e.target as Element).closest<HTMLAnchorElement>('a[data-select]');
    if (!link || !desktop.matches || e.metaKey || e.ctrlKey || e.shiftKey) return;
    e.preventDefault();
    const id = link.closest<HTMLElement>('.frame')!.dataset.job!;
    history.replaceState(null, '', `${location.search}#${id}`);
    select(id, { focus: e.detail === 0 });
  });

  applyFilter();
  const initial = location.hash.slice(1);
  const first = rows.find((r) => !r.hidden) ?? rows[0];
  if (desktop.matches && (initial || first)) {
    const id = rows.some((r) => r.dataset.job === initial) ? initial : first!.dataset.job!;
    if (id) select(id, { open: Boolean(initial) });
  }
}

paintStatus();
paintNovelty();
