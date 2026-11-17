import type { Salary } from '../jobs-schema';

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
 * Hand-drawn discard strike in an 800x14 box (close to a row's real aspect, so round caps stay round): a slightly bowed line whose ends and bow vary per id,
 * so no two struck frames share the same stroke.
 */
export function strikePath(id: string): string {
  let h = 7;
  for (const ch of id) h = (h * 131 + ch.charCodeAt(0)) >>> 0;
  const pick = (shift: number, span: number) => ((h >>> shift) % (span * 2 + 1)) - span;
  const r = (n: number) => Math.round(n * 10) / 10;
  const y0 = r(7 + pick(0, 3) * 0.9);
  const y1 = r(7 + pick(5, 3) * 0.9);
  const bow = r(7 + pick(10, 4) * 0.8);
  return `M8 ${y0}C240 ${bow} 528 ${r((bow + y1) / 2)} 792 ${y1}`;
}
