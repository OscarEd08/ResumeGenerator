import type { Salary, WorkMode } from '../jobs-schema';

export function frameCode(index: number): string {
  return String(index + 1).padStart(3, '0');
}

/** Deterministic hand tilt in degrees (-8..8) so every mark looks drawn, not stamped. */
export function tilt(id: string): number {
  let h = 0;
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return (h % 17) - 8;
}

const DAY_MS = 86_400_000;

export function ageLabel(posted: string | null, today: string): string {
  if (!posted) return 'sin fecha';
  const days = Math.round((Date.parse(today) - Date.parse(posted)) / DAY_MS);
  if (days <= 0) return 'hoy';
  return `hace ${days} d`;
}

const PERIOD_LABEL: Record<string, string> = {
  yearly: 'año',
  monthly: 'mes',
  weekly: 'semana',
  daily: 'día',
  hourly: 'hora',
};

function amount(n: number): string {
  return n >= 1000 ? `${Math.round(n / 1000)}k` : String(n);
}

export function salaryLabel(salary: Salary | null): string | null {
  if (!salary || (salary.min === null && salary.max === null)) return null;
  const cur = salary.currency ? `${salary.currency} ` : '';
  const per = salary.period ? ` / ${PERIOD_LABEL[salary.period]}` : '';
  let range: string;
  if (salary.min !== null && salary.max !== null && salary.min !== salary.max) {
    range = `${amount(salary.min)}–${amount(salary.max)}`;
  } else if (salary.min !== null && salary.max === null) {
    range = `desde ${amount(salary.min)}`;
  } else if (salary.min === null && salary.max !== null) {
    range = `hasta ${amount(salary.max)}`;
  } else {
    range = amount(salary.min!);
  }
  return `${cur}${range}${per}`;
}

/** Human labels for the pipeline's keyword slugs; unknown slugs pass through. */
const KEYWORD_LABEL: Record<string, string> = {
  dotnet: '.NET',
  csharp: 'C#',
  angular: 'Angular',
  'rest-api': 'REST API',
  'sql-server': 'SQL Server',
  azure: 'Azure',
  typescript: 'TypeScript',
  javascript: 'JavaScript',
  'ci-cd': 'CI/CD',
  microservices: 'Microservicios',
  react: 'React',
  docker: 'Docker',
  git: 'Git',
  'github-actions': 'GitHub Actions',
  python: 'Python',
  aws: 'AWS',
  kubernetes: 'Kubernetes',
  java: 'Java',
  bicep: 'Bicep',
  'entity-framework': 'Entity Framework',
  nextjs: 'Next.js',
  postgresql: 'PostgreSQL',
  kafka: 'Kafka',
  mongodb: 'MongoDB',
  spring: 'Spring',
  terraform: 'Terraform',
  llm: 'LLM',
  nodejs: 'Node.js',
  gcp: 'GCP',
  golang: 'Go',
  laravel: 'Laravel',
  php: 'PHP',
  ruby: 'Ruby',
  vue: 'Vue',
  'key-vault': 'Key Vault',
  tdd: 'TDD',
  'aspnet-core': 'ASP.NET Core',
  'aspnet-mvc': 'ASP.NET MVC',
  css: 'CSS',
  html: 'HTML',
  'azure-devops': 'Azure DevOps',
  'application-insights': 'App Insights',
  'clean-architecture': 'Clean Architecture',
  ddd: 'DDD',
  oauth: 'OAuth',
  blazor: 'Blazor',
  xunit: 'xUnit',
  nunit: 'NUnit',
  abp: 'ABP',
  rabbitmq: 'RabbitMQ',
  redis: 'Redis',
  'service-bus': 'Service Bus',
  'azure-openai': 'Azure OpenAI',
  graphql: 'GraphQL',
  signalr: 'SignalR',
  'azure-functions': 'Azure Functions',
  elasticsearch: 'Elasticsearch',
  angularjs: 'AngularJS',
  mysql: 'MySQL',
  vitest: 'Vitest',
  'vb-net': 'VB.NET',
};

const WORK_MODE_LABEL: Record<WorkMode, string> = {
  remote: 'Remoto',
  hybrid: 'Híbrido',
  onsite: 'Presencial',
  unknown: 'Modalidad no indicada',
};

/** "Remoto" / "Híbrido" / "Presencial", plus "con reubicación" when the posting offers relocation. */
export function workModeLabel(mode: WorkMode, relocation: boolean): string {
  return relocation ? `${WORK_MODE_LABEL[mode]} con reubicación` : WORK_MODE_LABEL[mode];
}

export function keywordLabel(slug: string): string {
  return KEYWORD_LABEL[slug] ?? slug;
}

export function dateLabel(iso: string | null): string {
  if (!iso) return 'sin fecha';
  const [y, m, d] = iso.split('-').map(Number);
  const months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
  return `${d} ${months[m - 1]} ${y}`;
}

/**
 * Grease-pencil cross-out in an 800x40 box laid over a row: it starts at the title's x-height (y≈17),
 * wobbles through three curves while drifting down toward the score, overshoots both ends and ends in a
 * small flick. Every bend comes from the id, so no two struck frames share the same stroke.
 */
export function strikePath(id: string): string {
  let h = 2166136261;
  for (const ch of id) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
  const rnd = (k: number, span: number) => {
    let x = Math.imul(h ^ (k * 0x9e3779b1), 0x85ebca6b) >>> 0;
    x = Math.imul(x ^ (x >>> 13), 0xc2b2ae35) >>> 0;
    return ((x >>> 8) / 0xffffff) * 2 * span - span;
  };
  const r = (n: number) => Math.round(Math.min(40, Math.max(0, n)) * 10) / 10;
  const y0 = r(17 + rnd(1, 2));
  const y1 = r(20 + rnd(2, 3));
  const y2 = r(24 + rnd(3, 3));
  const y3 = r(28 + rnd(4, 3));
  const lift = r(y3 - 4 - rnd(5, 1.5));
  return (
    `M4 ${y0}` +
    `C110 ${r(y0 - 6 + rnd(6, 2))} 200 ${r(y1 + 7 + rnd(7, 2))} 300 ${y1}` +
    `C390 ${r(y1 - 6 + rnd(8, 2))} 470 ${r(y2 + 6 + rnd(9, 2))} 560 ${y2}` +
    `C640 ${r(y2 - 5 + rnd(10, 2))} 720 ${r(y3 + 4 + rnd(11, 2))} 784 ${y3}` +
    `Q794 ${r(y3 + 1)} 798 ${lift}`
  );
}
