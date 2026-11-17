---
version: 1
slug: "src-pages-index-astro"
primary_target: "src/pages/index.astro"
related_targets: []
---

# Surface: job cockpit (ofertas, detalle, preview de CV, CV base)

Scope: the whole site (`src/pages/**`). Mode: Operate. Spanish UI. Single user; desktop first, must be comfortable on a phone.
Task: scan scored jobs, decide fast, copy `/tailor <job-id>`, preview the tailored PDF, download it, track status (nueva / preseleccionada / postulada / descartada) in localStorage.
Constraints: static Astro on GitHub Pages; no blue, red, or Claude colors; avoid corporate dashboard, generic AI template, decoration.
Chosen sketch: `.impeccable/mocks/decision/r1-assigned.html` (code-led).

## Direction contract

THESIS: Choosing jobs is editing a contact sheet: every frame visible, picks circled in grease pencil, rejects crossed out. Refuses the card-grid job board and the KPI dashboard.
OWN-WORLD: Near-black ground #111214, raised panel #1c1d20, 1px rules #2a2c30, paper text #f2f2ee, muted #8a8d93, one grease-pencil yellow #e8d44d reserved for marks and the primary action. Familjen Grotesk for UI, Azeret Mono for frame codes and figures. No shadows, no gradients, radius ≤ 8px.
STORY: The owner sees today's roll, knows which frames are worth it from score and keyword fit, circles a few, copies the tailor command, and later checks the PDF preview before applying.
FIRST VIEWPORT: Top bar (brand, nav: Ofertas, Preseleccionadas, CVs, CV base; roll meta). Left: filters then the frame strip rows (frame code, title+company+location+age, stack, exact-length score bar, score). Right: detail panel with big score, keyword chips (missing dashed), why-it-fits, `/tailor` command with yellow Copiar. Phone: strip full width, detail as a pushed page.
FORM: contact sheet, position 3 of 7 on the grounded list; seed:39e8753e28d679cc. Signature move: shortlisting draws a hand-drawn yellow ellipse around the score; discarding strikes the row with a yellow line; new/changed frames keep a NUEVA mark until opened. Raises kept: score bar length equals score; 1px rules only; columns never move.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
