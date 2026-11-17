# docs/ — source of truth

The Markdown files in this folder are the **source of truth** for the profile. Everything else (`data/profile.json`, the website, generated CVs) is derived from them. Update the docs first; never edit derived data by hand without updating the docs.

| File | Covers |
|---|---|
| `bertoni-experience.md` | Bertoni Solutions: Proquinorte, GlobalCertifica, bertoni-ai-standards |
| `cv-bertoni-proyectos.md` | Bertoni Solutions: AI standards, Nexo, Boyles, CERV (Spanish) |
| `cv-proyectos-personales.md` | Personal Finance App, Pulso Tech freelance (Spanish) |
| `previous-experience.md` | Contact data, older jobs, education and skills, transcribed from the reference CV |
| `Oscar_Pairazaman_CV.pdf` | Reference CV: content and layout template |

## Regenerating `data/profile.json`

Ask Claude Code: *"Re-sync `data/profile.json` from `docs/*.md` following `docs/README.md`."* Then run:

```sh
npm run validate:profile   # schema check (src/lib/profile-schema.ts)
npm test                   # ids unique, evidence values, sources exist, dates
```

## Sync rules

- **❓ (not verified):** never enters the bank.
- **⚠️ (partial):** enters with `evidence: "partial"`, using the corrected wording the doc suggests.
- **✅ / unmarked:** enters with `evidence: "verified"`.
- Never invent facts, numbers or technologies that are not in the docs.
- Every highlight has a stable kebab-case `id` (keep existing ids when rewording), English `text`, optional Spanish `text_es`, lowercase `tags`, and a `source` pointing to the doc path and section heading.
- Respect the "what NOT to say" tables (demos are not production) and keep client names out of highlight text when the docs flag them as confidential.
