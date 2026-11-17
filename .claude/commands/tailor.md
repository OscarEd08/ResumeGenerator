---
description: Tailor the CV to one job from data/jobs.json and render it to public/cv
argument-hint: <job-id>
allowed-tools: Bash(.venv/Scripts/python cv/tailor.py:*), Bash(.venv/bin/python cv/tailor.py:*), Read, Write, Edit
---

Tailor the CV to job `$ARGUMENTS`. Work from the repository root. Use `.venv/Scripts/python` on Windows and `.venv/bin/python` elsewhere.

## 1. Read the context

Run `.venv/Scripts/python cv/tailor.py context $ARGUMENTS`.

It prints JSON with:
- `job`: the posting and its weighted keyword `terms`.
- `language`: `en` for jobs abroad, `es` for Peru.
- `entries`: every bank entry, with its highlights ranked by how many job keywords they cover (`relevance`, `covers`).
- `selection_path`: where to write the selection.
- `base`: the base headline and summary.
- `skills`: the bank's skill groups.

If the job is not found, stop and say so. Jobs are pruned from `data/jobs.json` after 30 days.

## 2. Write the selection file

Write `cv/tailored/$ARGUMENTS.selection.json`:

```json
{
  "job_id": "$ARGUMENTS",
  "summary": "3-4 sentences in the CV language, aimed at this job",
  "experience": {
    "<entry-id>": [
      { "ids": ["<highlight-id>"] },
      { "ids": ["<highlight-id>", "<highlight-id>"], "text": "one bullet condensed from both" }
    ]
  },
  "projects": { "<entry-id>": [ { "ids": ["<highlight-id>"] } ] },
  "education": { "<entry-id>": [ { "ids": ["<highlight-id>"], "text": "only needed in Spanish" } ] },
  "skills": [ { "label": "Backend", "details": ["C#", ".NET"] } ]
}
```

Choosing content (S1):
- Lead each entry with the bullets that cover the job's keywords and responsibilities. Order skill groups and items so the job's stack comes first.
- Every experience and project entry keeps at least one bullet, so the timeline has no gaps.
- Keep about as much text as `cv/base.yaml` (about 7 bullets for the current role and 1-3 for the others). The CV must fit in 2 pages.
- `education` is optional in English. Leave it out to print every education highlight. In Spanish, list it with a translated `text`.
- `skills` items must be copied exactly from the bank's `details` under the same `label`. Drop items or groups that do not help, but never add new ones.

Never invent (S2):
- A bullet without `text` prints its highlight verbatim (`text_es` in Spanish).
- A `text` may only shorten, merge, reorder or translate what its cited highlights say. Do not add technologies, numbers, scope, results or claims they do not contain.
- Cite only ids from that same entry. Never cite an id twice.
- Write in the context's `language`. For Spanish, use `text_es` when it exists. Otherwise translate faithfully in `text`.
- The summary may only mention technologies and facts that are in the bank.
- Respect each entry's `client_confidential` note. Never print internal client or project names that it says to keep out.

## 3. Build

Run `.venv/Scripts/python cv/tailor.py build $ARGUMENTS`.

The build checks the selection, writes `cv/tailored/$ARGUMENTS.yaml` and renders the PDF and PNGs. Then it runs the ATS checks and the 2-page limit, and publishes to `public/cv/`.

If it fails, read the errors, fix the selection and run `build` again:
- An unknown id or a cross-entry id: cite the right id.
- A number or technology not in its sources: drop that detail.
- More than 2 pages: drop or shorten bullets.

Never fix a rejection by editing `data/profile.json` or the generated YAML.

## 4. Report

Relay the build output: the covered and missing keywords, the page count and the file paths.

Keywords listed as "not in the profile" are gaps to mention to the user. Never add them to the CV.

The site lists the new CV on `/cvs` and previews it at `/cv/$ARGUMENTS` after the next `npm run build` or `npm run dev`.
