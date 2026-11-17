# Proyectos personales — material para CV y LinkedIn

> Fuente: análisis de los repos `OscarEd08/personal-finance-app` y `OscarEd08/pulso-tech` (git log, código, specs, ADRs, documentos de entrega). Fecha: 2026-11-02.
> Todos los números son verificables en los repos salvo que se marque *(estimado)*.
> Complementa `cv-bertoni-proyectos.md`.

---

## 1. Por qué suman

Los proyectos de Bertoni muestran **.NET / Azure / IA corporativa**. Estos dos completan el perfil con algo que hoy no aparece en tu CV:

- **Stack JavaScript / TypeScript moderno:** Next.js 16, React 19, Astro 7, Vendure (NestJS), PostgreSQL y Turso.
- **Producto de punta a punta como dueño:** decisiones de producto, seguridad, despliegue y operación (VPS propio, Vercel).
- **IA integrada en un producto propio**, con criterio de costo y elección de modelo (Gemini y embeddings), y experimentos de fine-tuning on-device.
- **Desarrollo asistido por IA multi-herramienta:** Claude Code, Codex, Hermes y Copilot, con specs, worktrees y agentes verificadores.

---

## 2. Bullets por proyecto (listos para pegar)

### 2.1 Personal Finance App — Finanzas personales con IA y local-first
*Proyecto personal · Jul – Sep 2026 · Autor único · [github.com/OscarEd08/personal-finance-app](https://github.com/OscarEd08/personal-finance-app)*

**CV (español):**
- Diseñé y desarrollé una **PWA multiusuario de finanzas personales** donde los gastos se registran en lenguaje natural o por voz ("Compré un café por $3"). **Gemini** los convierte en transacciones estructuradas, usando solo las categorías, monedas y medios de pago del propio usuario.
- Construí un **modo local-first sin cuenta**: SQLite en el navegador (wa-sqlite sobre una capa de archivos OPFS propia), migraciones en el cliente, Web Locks, export/import en JSON y vinculación posterior de los datos locales con la cuenta en la nube.
- Implementé el producto en **Next.js 16 (App Router, Server Actions, Cache Components, partial prerendering) y React 19**, con **Turso (libSQL) y Drizzle ORM** (16 migraciones), y autenticación con NextAuth v5 (Google OAuth) usando sesiones revocables en base de datos.
- Modelé reglas de negocio reales: ciclos de facturación con fecha de corte configurable por tarjeta, varias monedas, gastos fijos con historial de precio, metas por categoría y un registro aparte de gastos de terceros que se comparte por WhatsApp.
- Protegí el endpoint público de IA con **rate limiting en 3 niveles** (dispositivo, IP y global), contadores hasheados compartidos entre instancias serverless y una configuración que falla cerrada.
- Preparé **búsqueda semántica** guardando embeddings (gemini-embedding-001, 768 dimensiones) como vectores en libSQL, y elegí los modelos documentando costo y límites del free tier.
- Apliqué **TDD estricto** con inyección de dependencias en lugar de mocks: **~2,100 tests (Vitest)** en 149 archivos, que corren contra libSQL real en memoria.
- Hice cumplir una **arquitectura feature-first** (ADR-0001) con reglas de límites en ESLint, y desarrollé con **spec-driven development (OpenSpec: 20 specs, 25 cambios archivados)** y agentes de IA en paralelo sobre git worktrees: **611 commits y 114 PRs en 3 meses**.
- Investigué el **fine-tuning de un modelo pequeño on-device** para extraer transacciones en español (dataset sintético en Python y Colab). *Experimental.*

**Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui, Turso/libSQL, Drizzle ORM, NextAuth v5, Google Gemini (3.5 Flash-Lite, embeddings), wa-sqlite + OPFS, Serwist (PWA), Vitest, ESLint boundaries, Vercel, OpenSpec, Claude Code.

---

### 2.2 Pulso Tech — E-commerce headless para tienda de accesorios
*Freelance para cliente (tienda peruana de accesorios tecnológicos) · Oct 2026 – actualidad · Desarrollador full-stack, único responsable técnico · En desarrollo y pruebas con el cliente (pre-lanzamiento)*

**CV (español):**
- Desarrollé para un cliente un e-commerce headless que **en 2 semanas ya estaba desplegado en su entorno de pruebas**. Reemplaza el catálogo en PDF de la tienda por una tienda online con carrito, checkout por WhatsApp, búsqueda con autocompletado y Libro de Reclamaciones.
- Implementé el backend en **Vendure 3.8 (NestJS) y PostgreSQL 16**, con 5 plugins propios (checkout, reclamos, ofertas, configuración de tienda, API guard) y 12 migraciones con expand/contract para poder revertir los deploys.
- Desarrollé el storefront en **Astro 7 (híbrido), con islas Preact, Tailwind 4 y GraphQL tipado (gql.tada)**. Las páginas de catálogo se prerenderizan y un **servicio propio las reconstruye** cuando el admin edita el catálogo y cada día por cron, con debounce, un solo build a la vez y swap atómico de la release.
- Monté la **infraestructura y el CI/CD**:
  - Docker Compose con límites de memoria e imágenes en GHCR escaneadas con **Trivy**.
  - GitHub Actions con acciones fijadas por SHA y deploy por **Tailscale OIDC** a un SSH forced command, sin puertos de entrada abiertos.
  - Dump de base de datos antes de cada deploy, smoke test y **rollback automático**.
  - Backups nocturnos cifrados (restic) en Cloudflare R2.
- Apliqué **seguridad de nivel producción**:
  - CSP con hashes SHA-256 de los scripts.
  - Cloudflare Turnstile que falla cerrado.
  - Allow-list de operaciones GraphQL, sin introspección y con un límite de 16 KB por request.
  - Tokens de confirmación hasheados y comparados en tiempo constante.
  - Gate de `npm audit` con excepciones que vencen.
- Aseguré la calidad con **~1,200 tests** *(estimado)*: Vitest, Playwright con accesibilidad (axe-core), **Lighthouse CI con presupuesto (LCP < 2.5 s, CLS < 0.1)** y una prueba de contrato del esquema GraphQL en CI.
- Cuidé el SEO (JSON-LD, sitemap, noindex en las páginas de sesión) y el consentimiento antes de cargar analítica (GA4 y Meta).
- Escribí un **parser propio de PDF** (streams ASCII85, Flate y DCT) que extrajo las 38 fotos del catálogo y las asoció a su SKU.
- Desarrollé con **agentes de IA (Claude Code, Codex y Hermes)** guiados por un `AGENTS.md` compartido, skills propias, specs por entrega y un **agente verificador independiente** por cada ola de trabajo: **356 commits y 6 ADRs**.

**Stack:** Vendure 3.8, NestJS, PostgreSQL 16, Astro 7, Preact, Tailwind CSS 4, GraphQL (gql.tada), Nanostores, MiniSearch, Node 24, TypeScript, Docker Compose, GitHub Actions, GHCR, Trivy, Tailscale, Cloudflare (Turnstile, R2), restic, Vitest, Playwright, axe-core, Lighthouse CI, dependency-cruiser.

---

## 3. Versión corta (sección "Proyectos" del CV)

- **Personal Finance App** (Next.js 16, React 19, Turso, Gemini). PWA de finanzas con registro de gastos en lenguaje natural por IA y modo local-first con SQLite en el navegador. 611 commits, ~2,100 tests, TDD y spec-driven development.
- **Pulso Tech — Freelance** (Vendure, Astro, PostgreSQL, Docker). E-commerce headless para una tienda de accesorios tecnológicos, desplegado en su entorno de pruebas en 2 semanas, con CI/CD seguro (Trivy, Tailscale OIDC, rollback automático), Lighthouse CI y ~1,200 tests.

---

## 4. Skills nuevas que estos proyectos agregan

| Categoría | Skills |
|---|---|
| **Frontend** | Next.js 16 (App Router, Server Actions, PPR, Cache Components), React 19, Astro 7, Preact, Tailwind 4, shadcn/ui, PWA (Serwist) |
| **Backend** | Node.js, NestJS / Vendure (headless commerce), GraphQL, NextAuth |
| **Datos** | PostgreSQL, Turso/libSQL, Drizzle ORM, SQLite en el navegador (wa-sqlite / OPFS), local-first, migraciones expand/contract |
| **IA** | Google Gemini (structured output), embeddings y búsqueda vectorial, selección de modelos por costo, fine-tuning de modelos pequeños (experimental) |
| **DevOps** | Docker Compose, GitHub Actions, GHCR, Trivy, Tailscale, Cloudflare (Turnstile, R2), Vercel, backups con restic, rollback automático |
| **Calidad** | Vitest, Playwright, axe-core (accesibilidad), Lighthouse CI, contract testing de GraphQL, ESLint boundaries, dependency-cruiser |
| **Seguridad** | CSP con hashes, rate limiting, OAuth, sesiones revocables, escaneo de dependencias e imágenes |
| **IA en el desarrollo** | Claude Code, Codex, Copilot, OpenSpec (spec-driven), agentes en paralelo con git worktrees, agentes verificadores |

---

## 5. Cómo presentarlos honestamente

| Proyecto | Qué decir | Qué NO decir |
|---|---|---|
| Personal Finance | "MVP funcional", "PWA desplegable en Vercel" | Que tiene usuarios o que está publicado: **no se pudo confirmar una URL en vivo** |
| Personal Finance | El fine-tuning on-device como "investigación" o "experimento" | Que el modelo propio está en producción |
| Personal Finance | Importación bancaria y bot de WhatsApp como roadmap | Que ya existen (solo están planificados) |
| Personal Finance | — | CI/CD: el repo **no tiene pipeline**. Si te preguntan, explica que los tests corren en local o en el deploy de Vercel |
| Pulso Tech | "Freelance para cliente, en desarrollo y pruebas (pre-lanzamiento)" | "En producción" o métricas de tráfico y ventas: aún no hay dominio ni lanzamiento público |
| Pulso Tech | La IA se usó para **construirlo** | Que el producto tiene funciones de IA (no las tiene) |

---

## 6. Pendientes antes de publicar

- [ ] **Personal Finance:** confirmar si `personal-finance-app.vercel.app` está en vivo. Si lo está, agrega el link: un demo navegable vale mucho en el CV.
- [x] **Pulso Tech:** se presenta como **freelance para cliente** (confirmado: el negocio es de otra persona).
- [ ] **Pulso Tech:** pide permiso al cliente antes de nombrar la tienda o enlazar el repo; si no lo da, usa "tienda peruana de accesorios tecnológicos".
- [ ] **Pulso Tech:** en el CV, ponlo como experiencia aparte ("Freelance · Oct 2026 – actualidad") y no dentro de "Proyectos personales".
- [ ] **Pulso Tech:** cuando salga a producción con dominio, agrega la URL y alguna métrica real, por ejemplo el puntaje de Lighthouse o los primeros pedidos.
- [ ] Revisar que ambos repos de GitHub estén **públicos y con un README presentable** si los vas a enlazar. Antes de hacerlos públicos, revisa el historial en busca de secretos (por ejemplo con gitleaks).
- [ ] Fijar los dos repos en tu perfil de GitHub y LinkedIn (sección "Destacados").
