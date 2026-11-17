# Bertoni Solutions — Experience Inventory

Source material for polishing the LinkedIn profile and the CV.
Built from the git history and repository files of three projects: **Proquinorte**, **GlobalCertifica**, and **bertoni-ai-standards**.

**Evidence legend**

| Mark | Meaning |
|---|---|
| ✅ | Verified in the repositories (commit, PR, or file) |
| ⚠️ | Partially verified; the current CV wording overstates or differs |
| ❓ | Stated in the current CV but not found in the repositories; keep only if you can back it with your own measurements |

> **Confidentiality check:** before publishing client names (Proquinorte, GlobalCertifica), confirm with Bertoni that they can be named publicly. If not, use the descriptive labels shown under each project heading.

---

## Role at Bertoni Solutions

- **Company:** Bertoni Solutions GmbH, Baar (Zug), Switzerland. Remote from Lima, Peru.
- **Progression (from the LinkedIn profile):**
  - .NET Developer: Jan 2024 – Sep 2024
  - Software Developer: Sep 2024 – Jul 2025
  - Semi Senior Software Developer: Jul 2025 – present
- **Work model:** client projects for European companies, Azure DevOps (boards, repos, pipelines), Scrum.

### Contribution footprint

| Project | Repositories | Your non-merge commits | Active period |
|---|---|---|---|
| Proquinorte | 6 | ~1,474 | May 2024 – Oct 2026 |
| GlobalCertifica | 2 | ~562 | Oct 2024 – Mar 2026 |
| bertoni-ai-standards | 1 | 50 (sole author) | Oct 2026 |

You are the top contributor of the main Proquinorte repository (`eShopBusinessCentral`).

---

## 1. Proquinorte

**Descriptive label (if the client cannot be named):** B2B/B2C multi-store e-commerce for laboratory and healthcare supplies, integrated with Microsoft Dynamics 365 Business Central.

**Stack:**
- **Application:** .NET 9, ASP.NET Core, nopCommerce 4.90.6, Razor, jQuery.
- **Search:** Meilisearch, with a .NET search microservice.
- **Serverless:** Azure Functions v4 (isolated worker) and Durable Functions.
- **ERP:** Business Central extension in AL.
- **Azure infrastructure:** Bicep, Azure Front Door Standard + WAF, Azure DNS, App Service, Blob Storage, Key Vault, Application Insights, Azure Monitor.
- **Quality and delivery:** Azure DevOps Pipelines, Playwright E2E, xUnit, SonarQube.

### Achievements by theme

#### 1.1 Search engine (Meilisearch microservice in .NET) ✅
- Built the search microservice from scratch:
  - DTOs, matching strategies, ranking rules, and autocomplete suggestions (#1157, #1178).
  - Client-certificate (mTLS) authentication between the store and the search API (#1163, #1204).
- Implemented multi-search and federated search across several indexes:
  - Disjunctive multi-search (#1964).
  - Federated result counts (#2008), later refined to sum per-index estimated totals (#2142).
- Added per-store search routing via a request header for the multi-store setup (#1452).
- Added an index-status endpoint (#1394) and a standardized API response with centralized exception handling (#1475).
- Built a dedicated index and API for the antibody catalog: endpoints, SKU lookup, attribute filtering (#1362, #1463).
- Tuned relevance:
  - Rank exactness before attributes (#2287).
  - Promote the product-family alternative on an exact SKU match (#2255).
  - Prefix-match ranking for autocomplete (#2242).
- **Metric ✅:** reduced Meilisearch **P95 latency on broad search terms from ~1.6 s to ~150 ms** (#1991, May 2026).
  - The commit says "back to ~150 ms", so this restored performance after a regression. Phrase it as "cut P95 search latency from ~1.6 s to ~150 ms".
- Added store-aware output caching for product autocomplete (#2083, #2093, #2263).

#### 1.2 Nightly indexation with Azure Durable Functions ✅
- Built timer-triggered nightly index generation, migrated to Durable Functions orchestrations (#1239).
- Made the orchestrations scale and recover safely:
  - Chunked, cursor-based processing (#1598).
  - Product-family fan-out made resumable with `ContinueAsNew`, to bound orchestration history at scale (#2062).
  - Guard against duplicate rebuilds on gateway timeouts, i.e. idempotency (#2157).
- Added deleted-SKU processing and change-sync functions for the antibody index (#1463).
- Built a queue-based image optimization pipeline: multiple target widths, with a daily backfill limit (#1493, #1671).
- Added monitoring of nopCommerce scheduled tasks (#2349).

#### 1.3 Storefront and business features (nopCommerce) ✅
- **Storefront foundation (2024):** login by customer code, checkout and order detail, product filtering and sorting, transactional e-mails for forms, chatbot and guided-tour UI (#85, #935).
- **Quotes and offers:** offer history, "add all offer products to cart"; Portugal store launch (#1124); VAT handling (#1116, #1305); SKU encryption in routes (#1325).
- **Recurring orders with asynchronous processing (#1356):** incident management for delivery notes (#1354), promo codes and gifts (#1366), recurring-order vendors (#1650).
- **Contact groups and web groups:** customer-specific catalogs, aligned with Business Central (#1963–#2015).
- **SEO and Core Web Vitals:**
  - Product sitemaps generated from the search indexes by a scheduled task, paginated (#2047).
  - Store-host canonical URLs (#2092).
  - Deferred widget loading and CLS/LCP fixes (#2151).

#### 1.4 B2B PunchOut (cXML) ✅ ⚠️
- Implemented cXML PunchOut so corporate buyers can shop from their own procurement systems (ERP/e-procurement) (#1361, module `Nop.Punchout`):
  - Browser form post back to the buyer system.
  - Persistence of the customer discount group.
  - Order audit in Business Central.
- ⚠️ Failure alerts are **e-mail notifications to the ticketing channel**, not a direct ticketing-system integration. Suggested wording: "automatic failure notifications to the support ticket queue".

#### 1.5 Resilience and observability ✅ ⚠️
- Added resilience pipelines (Microsoft.Extensions.Resilience) with **circuit breakers and timeouts** on the outbound clients to Business Central and Meilisearch (#2093):
  - Circuit breaker: 50% failure ratio, 15 s break.
  - Timeout: 30 s.
- Instrumented server- and browser-side telemetry in Application Insights, including an outbound-call telemetry handler (#2079, #2093).
- Created availability tests from 3 regions every 15 min, with client-side latency alerts (#2079).
- Preloaded the Meilisearch client certificate at startup through a warm-up hosted service, to avoid first-request latency (#2119).
- Added a Key Vault secret cache with a TTL (#2119) and a geo-IP cache (#2122).
- ⚠️ **Exponential retries:** found only in a search proof-of-concept, not in production. Remove "reintentos exponenciales" from the CV, or say "circuit breakers and timeouts".
- ⚠️ **Warm-up:** applies to the certificate, not to the HTTP clients. Suggested wording: "certificate warm-up at startup to avoid cold-start latency".

#### 1.6 Azure infrastructure as code and edge security ✅
- Wrote the **Bicep** infrastructure:
  - Azure Front Door, a WAF module, QA and PROD environments (#2086, #2156).
  - DNS zone as code (#2567).
  - Monitoring alerts and action groups.
- Configured **WAF rules**:
  - Per-IP rate limiting (350 req / 5 min).
  - Blocking of requests with no User-Agent.
  - A datacenter IP block list, with verified crawler IP ranges (#2156, #2344).
  - App-level crawler rate limiting moved to the WAF (#2253).
- Led the **DNS migration to Azure DNS** and the apex/www cutover to Front Door, with an apex redirect (#2567). Added certificate-expiry monitoring for the apex domain (#2580).
- Wrote WAF traffic-surge alerts and an operational runbook (#2527), plus a production deployment plan with rollback (#2252).
- Validated the WAF behavior with Playwright flows (#2156).

#### 1.7 CI/CD and test automation ✅
- Built infrastructure pipelines: a CI pipeline that runs Bicep validate and what-if on pull requests, and a CD pipeline with QA/PROD environments and approval gates (`infra-ci.yaml`, `infra-cd.yaml`).
- Built a **pull-request validation pipeline** for the store (#2030).
- Built a **Playwright E2E suite** that runs after deployment and on a weekly schedule (#2139), and ported it to nopCommerce 4.90 (#2362).
- Added Azure Pipelines for the search service and the Functions (#1649).

#### 1.8 Platform upgrade: nopCommerce 4.90.6 on .NET 9 ✅ ⚠️
- Led the upgrade of a heavily customized nopCommerce store to **4.90.6 on .NET 9** (Aug 2026):
  - Transferred **587 conflict-free files** (#2356).
  - Reintegrated **92 heavily rewritten customized files** (#2364).
  - Migrated custom permissions and the admin menu.
  - Cleaned up nullable warnings (#2517).
- Moved application secrets to **Azure Key Vault** (#1360, #1361, #2119, #2329).
- ⚠️ The Key Vault work was a separate effort from the upgrade. Present them as two achievements, not one.

#### 1.9 Business Central extension (AL) ✅ ⚠️
- Maintained the Business Central extension through **134 releases** (v1.0.0.134).
- Built API pages and queries for prices per SKU and customer, search, categories, and checkout (#233, #565, #901).
- Centralized promotion, gift, and pricing logic in codeunits (`CUPromo` #1366; `CUPrices`, optimized and extended with line discounts #2093, #2269).
- Built recurring-order logic (`CURecurrentOrder` #1356) and contact/customer handling with web-account enablement (#1483, #1484).
- Added product attributes and traceability (#1362, #1488), and paginated query utilities with recursive web-group matching (#1963).
- ⚠️ **Paginated APIs to import blobs/attributes** and **automatic customer resolution** were not clearly found. Pagination exists as a generic utility (`CUApiQueryUtils`), and customer handling exists in `CUCustomer`/`CUContact`. Adjust the wording to match.

### Claims in the current CV to review

| Claim in CV | Status | Recommendation |
|---|---|---|
| Catalog of 500,000+ SKUs | ❓ | Not documented in the repositories. Keep only if you have a reliable source, such as an index stats screenshot. |
| Search response 6–7 s → < 1 s | ❓ | Not documented. The verified alternative is **P95 ~1.6 s → ~150 ms** (#1991). |
| Exponential retries | ⚠️ | Only in a POC. Use "circuit breakers and timeouts". |
| Named HTTP clients with warm-up | ⚠️ | The warm-up is for the client certificate. |
| Multilingual autocomplete with family fallbacks | ⚠️ | Autocomplete exists; family promotion is in search and sitemaps, not in autocomplete. |
| Ticketing alerts on checkout failure | ⚠️ | E-mail notifications to the ticket channel. |
| Key Vault as part of the nopCommerce migration | ⚠️ | Separate initiative. |

---

## 2. GlobalCertifica

**Descriptive label (if the client cannot be named):** multi-tenant SaaS platform to issue and verify digital credentials and badges (Open Badges), for organizations and educational institutions.

**Stack:**
- **Backend:** ABP Framework 8.2 (DDD, layered architecture), .NET, Entity Framework Core, OpenIddict.
- **Frontend:** Angular.
- **Azure:** Blob Storage, Azure Communication Services.
- **Delivery:** Docker, Azure DevOps CI/CD, SonarQube.
- **Integrations:** Microsoft and Google OAuth.

**Role:** full-stack developer across backend and frontend. About 560 commits over 17 months, the third largest contributor.

### Achievements by theme

#### 2.1 Authentication and onboarding ✅
- Implemented Microsoft and Google OAuth login, plus password recovery and update flows (#24226, #24227).
- Built part of the initial Angular frontend: login, template list and creation, a Blob Storage service.

#### 2.2 Credential lifecycle ✅
- Built credential templates, learning paths (collections, #26587), credential preview and print, and credential lists (#23835, #23839, #24012).
- Built credential sharing and a public view of assignments (#24841), a revoked-credentials report (#24776), and an image-to-PDF service (#25049).
- Moved e-mail delivery to background jobs (#24811).

#### 2.3 Multi-tenant organizations, subscriptions, and billing ✅
- Built organization admin management (#24106), sub-organizations, and super-user flows (#24826).
- Built the subscription and plan model:
  - Subscription service and API (#24209), organization subscriptions (#24678), subscription history.
  - Consumed credits tracking (#26522) and benefit gifting.
  - Plan reports with discounts (#26743).
- Built role management (#26548).

#### 2.4 GDPR compliance: data retention and account deletion ✅
This is a strong differentiator for European clients.
- Designed and implemented GDPR features:
  - Configurable **data retention policies** (entity, seeding, and service in `DataRetentionService`).
  - **Processing restriction** and **data masking/anonymization**.
  - A scheduled **data deletion job**, plus user **self-service account deletion** (#26407).
- Added **audit logging** for account deletion and profile changes (#26576, #26578, #26685).

#### 2.5 Reporting and UX ✅
- Built report generation with loading states (#26742, #26749), an organization autocomplete and a reusable multi-select component (#26725), organization filtering (#26847), and a URL navigation-state service.

#### 2.6 Proof of concept: electronic PDF signing ✅
- Built an **Azure Function (.NET 8)** that signs PDF documents with iText and BouncyCastle, protected by an API key (e-sign PoC, Feb 2026).

### Not yours (do not claim)
- The Moodle/LTI integration and the Azure WebJobs were built by other team members.
- No automated tests authored by you were found in this project.

---

## 3. bertoni-ai-standards

**What it is:** an internal **Claude Code plugin marketplace** that standardizes AI-assisted software development at Bertoni Solutions. It covers skills, specialized subagents, templates, git hooks, and technology profiles.

**Stack:** Claude Code plugins (skills, subagents, hooks), Bash, AWK, Azure DevOps Pipelines, gitleaks.

**Role:** sole author and maintainer. 50 commits, v1.0.1 → v1.3.0, in October 2026.

### Achievements ✅
- **Designed an 8-step AI-assisted SDLC with a human approval gate at every step:**
  1. Requirement
  2. Design
  3. Technical plan
  4. Azure DevOps work items
  5. Implementation
  6. Code review
  7. PR + QA handoff
  8. Release
- **Built 4 plugins:** a core plugin plus technology profiles for .NET, Angular, and SQL Server.
- **Wrote 12 skills:** requirement, plan, work-items, pr, qa-handoff, standards, testing, security, azure-devops, code-review, playwright, init.
- **Wrote 9 specialized subagents:** requirement, design, technical planner, work items, implementer, reviewer, PR, QA, release.
  - Each agent has a model and reasoning-effort tier (Opus / Sonnet / Haiku) to balance quality and cost.
  - Projects can override the tier per work type or activity.
- **Built a project bootstrap command** (`/bertoni:init`, `init.sh` + `merge-settings.awk`):
  - It scaffolds standards into any repository and merges settings without overwriting local customizations.
  - It has a `--refresh` mode for upgrades.
- **Built governance and security guardrails:**
  - Permission allow/ask/deny lists, which deny access to secrets, production, and protected-branch pushes.
  - gitleaks secret scanning in a pre-commit hook, and a commit-message hook.
  - A session hook that warns when a project's standards are out of date.
- **Built a pull-request validation pipeline template** that comments on the PR with what failed and how to fix it.
- **Wrote corporate templates:** PR, QA handoff, technical plan, user story, work items, ADR, testing strategy, security policy, and lint/format configs.
- **Wrote test suites** for hooks, init, and the PR pipeline: 4 Bash suites, ~1,580 lines.

---

## Skills inventory for LinkedIn

Tag each skill on the Bertoni position. Order the profile's top skills by relevance.

| Area | Skills |
|---|---|
| Core | C#, .NET, ASP.NET Core, REST APIs, Entity Framework Core |
| Frontend | Angular, TypeScript, JavaScript, Razor |
| Cloud (Azure) | Azure Functions, Azure Durable Functions, Azure Front Door, Azure WAF, Azure Key Vault, Application Insights, Azure Monitor, Azure DNS, Azure Blob Storage, App Service |
| Infrastructure & DevOps | Bicep, Infrastructure as Code, Azure DevOps, Azure Pipelines, CI/CD, Docker |
| Search | Meilisearch, Search Engines, Relevance Tuning |
| Architecture | Domain-Driven Design, ABP Framework, Microservices, Serverless, Resilience Patterns (Circuit Breaker), Multi-tenant SaaS |
| ERP & integration | Microsoft Dynamics 365 Business Central, AL, cXML PunchOut, B2B Integrations, OAuth |
| E-commerce | nopCommerce, Technical SEO, Core Web Vitals |
| Quality | Playwright, End-to-End Testing, SonarQube, Code Review |
| Security & compliance | Web Application Firewall, GDPR, Secret Management |
| AI-assisted development | Claude Code, AI Agents, Prompt Engineering, Developer Tooling, Generative AI |
