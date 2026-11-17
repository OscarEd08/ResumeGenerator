# Experiencia en Bertoni Solutions — material para CV y LinkedIn

> Fuente: análisis de los repositorios `nexo-industrial`, `boyless-bros-demo`, `CERV/checkpoint-vision` y `bertoni-ai-standards` (git log, código, ADRs, docs). Fecha: 2026-11-02.
> Todos los números son verificables en los repos salvo que se marque *(estimado)*.
> Complementa `bertoni-experience.md` (Proquinorte, GlobalCertifica).

---

## 1. Resumen para el CV (perfil profesional)

**Versión CV (español):**
> Desarrollador .NET / Angular con foco en arquitectura limpia y desarrollo asistido por IA. En Bertoni Solutions lidero técnicamente el estándar corporativo de SDLC con agentes de IA (Claude Code) y construyo demos y pilotos para clientes en minería, distribución industrial y comercio exterior: integraciones con Azure OpenAI, Azure Content Understanding y visión computacional, desplegadas en Azure con IaC y pipelines de Azure DevOps. Entrego con TDD estricto (más de 3,000 tests automatizados en un solo proyecto) y arquitectura validada por tests.

**Headline LinkedIn (inglés, recomendado):**
> Software Engineer (.NET · Angular · Azure) | AI-assisted SDLC & LLM integrations | Clean Architecture · TDD

**About LinkedIn (inglés):**
> I build .NET and Angular systems on Azure, and I design how teams ship them with AI agents. At Bertoni Solutions I authored the company's AI-assisted SDLC standard — a Claude Code plugin with 9 specialized agents, human approval gates and automated review — and used it to deliver client pilots in weeks instead of months: a B2B operations platform with an LLM assistant (18 requirements, 3,000+ automated tests in 25 days), an AI invoice reader for a mining company, and a computer-vision vehicle checkpoint. I care about clean architecture, test-first development and measurable cost/accuracy trade-offs when choosing AI models.

---

## 2. Bullets por proyecto (listos para pegar)

### 2.1 bertoni-ai-standards — Estándar corporativo de SDLC asistido por IA
*Plugin marketplace interno de Claude Code · Oct 2026 · Autor único y líder técnico (decisor en ADR 0001)*

**CV (español):**
- Diseñé y desarrollé el estándar corporativo de Bertoni para entrega de software con agentes de IA: plugin de Claude Code con **13 skills, 9 subagentes** (requerimiento → diseño → plan técnico → work items → implementación → code review → PR → QA → release) y hooks de gobierno; **v1.0 → v1.8 en 18 releases y 131 commits**.
- Definí y documenté (ADR) la **entrega autónoma hasta PR abierto** con revisión humana obligatoria: piloto en la nube completado en **~29 min** con 2 rondas de review automático, frente a 3 h 45 min y USD 52 del primer intento.
- Implementé **guardrails de seguridad y costo**: ningún agente aprueba, mergea ni despliega; reglas deny sobre ramas protegidas y resource groups productivos; escaneo de secretos (gitleaks); tope de **USD 8 por PR** en review; selección de modelo por rol (Haiku/Sonnet) para optimizar costo.
- Integré **Azure DevOps** (Boards y Repos vía `az` CLI) como fuente de verdad con **sincronización bidireccional a GitHub** para sesiones cloud de Claude, sin secretos ni PRs en GitHub.
- Cubrí el propio plugin con **12 suites de tests (~4,700 líneas, ~900 aserciones)** ejecutadas como build validation en Azure Pipelines, con `az`/`gh` simulados para correr sin red.

**Stack:** Claude Code (plugins, skills, subagents, hooks), Bash/POSIX sh, AWK, Python (python-docx), Azure DevOps (Boards, Repos, Pipelines), GitHub, gitleaks, Playwright.

---

### 2.2 Nexo Industrial — Plataforma B2B de operaciones con asistente IA
*Demo/piloto para distribuidor industrial peruano · Oct 2026 · Desarrollador full-stack (único autor)*

**CV (español):**
- Desarrollé de punta a punta una plataforma B2B de operaciones (pedidos, inventario, portal de clientes, control de garita y balanza, facturas de proveedores, dashboard) en **.NET 10 + Angular 22**, entregando **18 requerimientos y 36 ADRs en 25 días (876 commits)**.
- Diseñé un **monolito modular de 12 módulos** (Domain / Application / Contracts / Infrastructure / Endpoints), con un esquema SQL por módulo, eventos de integración en memoria y **reglas de arquitectura verificadas con ArchUnitNET**.
- Implementé un **asistente con IA** sobre Microsoft.Extensions.AI y Azure OpenAI (gpt-4.1) con *function calling* de solo lectura, acción confirmada por el usuario, grounding de citas, defensa contra prompt injection (OWASP LLM01), timeout y cuota diaria.
- Automaticé la **lectura de facturas** con Azure Content Understanding y conciliación contra órdenes de compra.
- Apliqué TDD estricto: **1,747 tests xUnit, 1,025 tests Vitest y 238 E2E con Playwright**, usando Testcontainers (SQL Server, Azurite).
- Desplegué en **Azure Container Apps con Bicep** (Azure SQL, Storage, Microsoft Foundry, managed identity, Entra ID, alertas de presupuesto) y pipelines de **Azure DevOps** con validación selectiva de PR, gitleaks y escaneo de dependencias.
- Usé el SDLC con agentes de IA (8 agentes con gates humanos): el tiempo real fue **0.09x–0.14x del estimado** en los primeros requerimientos, según la estimación documentada en el repo.

**Stack:** .NET 10, ASP.NET Core Minimal APIs, EF Core 10, SQL Server 2022, Angular 22 (signals), TypeScript, Tailwind 4, spartan-ng, Microsoft.Extensions.AI, Azure OpenAI, Azure Content Understanding, xUnit v3, NSubstitute, Testcontainers, ArchUnitNET, Vitest, Playwright, Bicep, Azure Container Apps, Azure DevOps.

---

### 2.3 Boyles Invoice Demo — Lector de facturas de importación con IA
*POC para Boyles Bros Diamantina (minería, Perú) · Oct 2026 · Desarrollador y responsable técnico*

**CV (español):**
- Construí y desplegué en **6 días** un lector de facturas de importación con IA para un equipo contable que registra a mano **200–300 facturas al mes**: extrae 18 campos (Incoterm, FOB/flete/seguro/CIF, pesos, carta de crédito, etc.) y las líneas de detalle de PDFs digitales o escaneados, en español o inglés.
- Integré **Azure Content Understanding (GPT-4.1)** con analyzers propios, confianza por campo, resaltado de la fuente en el PDF y validaciones deterministas (FOB + flete + seguro = CIF, peso neto ≤ bruto, Incoterms 2020).
- Lideré una **evaluación de modelos** (gpt-4.1, gpt-4.1-mini, gpt-5.4-mini, extracción directa con LLM) contra un ground truth revisado manualmente: identifiqué una alternativa con **la misma precisión (91.4%, 100% en campos críticos) y ~3.6x menor costo por factura**, motivada por la deprecación de gpt-4.1.
- Apliqué **arquitectura limpia** (puertos y adaptadores, reglas de capas testeadas) y **591 tests** (xUnit, bUnit), más smoke tests con Playwright sobre el build publicado.
- Endurecí la seguridad tras una auditoría: CSP con nonce, rate limiting, presupuesto de extracciones por sesión y por día, cookies `__Host-` y managed identity sin llaves.
- Entregué al cliente la documentación funcional y de arquitectura, los diagramas, la guía de Content Understanding y los scripts de consumo y costo con Azure Monitor.

**Stack:** .NET 10, Blazor (Interactive Server), Azure Content Understanding, Microsoft Foundry, GPT-4.1, PDF.js, ClosedXML, Azure App Service, Managed Identity, Azure DevOps Pipelines (workload identity federation), xUnit, bUnit, NSubstitute, Playwright.

---

### 2.4 Checkpoint Vision (CERV) — Inspección vehicular con visión computacional
*Demo comercial para un integrador minero · Oct–Nov 2026 · Desarrollador (único autor)*

**CV (español):**
- Desarrollé una demo de **inspección automática de camionetas en garitas mineras**: detecta 8 elementos de seguridad obligatorios (circulina, extintor, tacos, pértiga, etc.), lee placa y código de unidad con OCR y emite un semáforo verde/ámbar/rojo con barrera simulada.
- Implementé el servicio de inferencia en **Python/FastAPI** con detección *zero-shot* **OWLv2** (sin dataset ni GPU) y **RapidOCR (ONNX)** detrás de una interfaz intercambiable, preparado para migrar a un modelo entrenado (RF-DETR en Azure ML).
- Construí la app web en **Blazor .NET 10**: reglas versionadas, auditoría de ingresos manuales, revisión del supervisor que alimenta una cola de reentrenamiento (*human-in-the-loop*), dashboard con exportación a Excel y **modo video con detección de movimiento** que dispara la inspección automáticamente.
- Diseñé la **sincronización offline-first** (patrón outbox, rutas idempotentes en Azure Blob, reintentos con backoff) para operar sin conectividad.
- Ajusté la inferencia hasta lograr **7–11 s por inspección en CPU** (objetivo < 20 s) y que las 7 escenas de prueba dieran el resultado esperado.
- Orquesté el desarrollo con **3 agentes de IA en paralelo sobre git worktrees** (inferencia, web, tooling) unidos por un contrato compartido: **75 commits y ~250 tests** (xUnit + pytest) en 2 días de trabajo.
- Definí la infraestructura en **Bicep (Azure Container Apps con scale-to-zero, ACR, managed identity)** y el pipeline de Azure DevOps, con un costo estimado de USD 0–5 al mes.

**Stack:** Python 3.12, FastAPI, PyTorch, Hugging Face Transformers (OWLv2), OpenCV, ONNX Runtime, RapidOCR, .NET 10, Blazor, EF Core (SQLite), Azure Blob Storage, Docker Compose, Bicep, Azure Container Apps, Azure DevOps, pytest, xUnit.

---

## 3. Bullet resumen (si el CV tiene poco espacio)

Si solo cabe un bloque para Bertoni, usa esto bajo el puesto actual:

- Autor del **estándar corporativo de SDLC asistido por IA** (plugin de Claude Code: 9 agentes, 13 skills, gates humanos, integración con Azure DevOps), adoptado como base de los proyectos de la empresa.
- Entregué **3 pilotos y demos para clientes en 1 mes** con ese estándar: plataforma B2B con asistente LLM (.NET 10 / Angular 22, 3,000+ tests), lector de facturas con Azure Content Understanding (evaluación de modelos con ~3.6x de ahorro) e inspección vehicular con visión computacional (OWLv2 + OCR).
- Despliegues en **Azure con IaC (Bicep)**, managed identity y pipelines de Azure DevOps; TDD y arquitectura limpia o modular validada con tests.
- *(Más los bullets ya existentes de Proquinorte y GlobalCertifica.)*

---

## 4. Skills para agregar al CV y LinkedIn

| Categoría | Skills nuevas o reforzadas por estos proyectos |
|---|---|
| **IA / LLM** | Azure OpenAI, Microsoft.Extensions.AI, function calling / tool use, grounding, prompt-injection defense, Azure Content Understanding, Document AI, evaluación de modelos (precisión vs. costo), Microsoft Foundry |
| **Visión computacional** | OWLv2 (zero-shot detection), OCR (RapidOCR / ONNX), OpenCV, Hugging Face Transformers, PyTorch, human-in-the-loop |
| **Desarrollo asistido por IA** | Claude Code (plugins, skills, subagents, hooks), orquestación multi-agente, spec-driven development, agentes en paralelo con git worktrees, gobierno de agentes y control de costos |
| **Backend** | .NET 10, ASP.NET Core Minimal APIs, Blazor, EF Core 10, SQL Server, Python / FastAPI |
| **Frontend** | Angular 22 (signals), TypeScript, Tailwind CSS 4, spartan-ng |
| **Arquitectura** | Monolito modular, Clean / Hexagonal Architecture, DDD, eventos de integración, patrón outbox, ADRs |
| **Testing** | TDD, xUnit, NSubstitute, bUnit, Testcontainers, ArchUnitNET (architecture tests), Vitest, Playwright, pytest |
| **Cloud / DevOps** | Azure Container Apps, App Service, Azure SQL, Blob Storage, ACR, Managed Identity, Entra ID, Bicep (IaC), Azure DevOps (Boards, Repos, Pipelines), Docker, gitleaks |

**Top skills de LinkedIn sugeridas (reemplazan "Search Engine, Git, .NET"):** .NET · Azure · AI-Assisted Development (o "Large Language Models")

---

## 5. Cómo presentarlos honestamente (importante)

Son demos y pilotos, y eso está bien, **siempre que el CV no los venda como producción**. Para que una entrevista técnica no te tome por sorpresa:

| Proyecto | Qué decir | Qué NO decir |
|---|---|---|
| Todos | "Demo / piloto para cliente", "POC", "propuesta comercial" | "En producción", "usado por N usuarios" |
| Nexo | El asistente IA está integrado y testeado con un cliente simulado | Que se validó con el modelo real (está **pendiente** en `docs/assistant/demo-evaluation.md`) |
| Nexo | El ERP está detrás de un puerto (`IErpConnector`) | Que se integró con un ERP real (es `DemoErpConnector`) |
| Boyles | Desplegado en Azure, probado con facturas reales del cliente | Integración con A+ (está simulada) |
| CERV | 7/7 escenas correctas **en escenas sintéticas** | Cifras de precisión en campo (`PRODUCT.md` dice explícitamente que no se afirmen) |
| CERV | Infra definida en Bicep y pipeline listo | Que está desplegado (según el log aún no se había desplegado) |
| Boyles | Autoría: 26 commits como "Oscar Pairazaman" y 34 como "oscarrBS" (tu cuenta de GitHub, usada en las ejecuciones de agentes) | — |

**Sobre "construido con agentes de IA":** es tu mayor diferencial, pero preséntalo como **"diseñé y dirigí"** el flujo, no como "la IA lo hizo". La evidencia que lo respalda está en los repos: specs, ADRs, gates humanos, reviews numerados y evidencia RED/GREEN.

---

## 6. Pendientes antes de publicar

- [ ] Confirmar cómo describir cada proyecto públicamente: los nombres de cliente (Boyles Bros, CERV) podrían requerir anonimizarse, por ejemplo "empresa minera peruana" o "integrador minero". **Consulta a Bertoni.**
- [ ] Decidir el idioma del CV: el de LinkedIn de referencia (Diego) está en inglés y recibe más ofertas.
- [ ] Revisar las fechas: todo esto ocurrió entre oct y nov 2026, dentro del puesto actual en Bertoni.
- [ ] Pendientes del inventario anterior: Cloud Store 2024 se solapa con Bertoni, corregir "Sug" → "Zug", y quitar las métricas no verificadas (500k SKUs, 6–7 s → < 1 s).
