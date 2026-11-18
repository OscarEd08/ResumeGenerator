---
description: Tailor the CV to one job from data/jobs.json and render it to public/cv
argument-hint: <job-id>
allowed-tools: Bash(.venv/Scripts/python cv/tailor.py:*), Bash(.venv/bin/python cv/tailor.py:*), Read, Write, Edit
---

Tailor the CV to job `$ARGUMENTS` and hand the user the PDF.

The user only wants the file. Run the steps below without narrating them, asking questions or offering options. Don't commit, push, run npm or start a server unless the user asks. Work from the repository root and use `.venv/Scripts/python` (`.venv/bin/python` outside Windows).

## 1. Context

Run `.venv/Scripts/python cv/tailor.py context $ARGUMENTS`. It prints JSON with:
- `job`: the posting and its weighted keyword `terms`.
- `language`: `en` for jobs abroad, `es` for Peru.
- `entries`: every bank entry, with its highlights ranked by `relevance` and the keywords each one `covers`.
- `base`: the base headline and summary.
- `skills`: the bank's skill groups.
- `selection_path`: where to write the selection.

If the job is not found, say so in one line and stop. Jobs are pruned from `data/jobs.json` after 30 days.

## 2. Selection

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

What to include:
- Put first the bullets and skills that cover the job's keywords.
- Keep at least one bullet for each experience and project entry.
- Aim for about 7 bullets for the current role and 1-3 for each of the others, so the CV fits in 2 pages.
- `education` is optional in English. In Spanish, list it with a translated `text`.
- Copy `skills` items exactly from the bank's `details` under the same `label`. You may drop items, but never add any.

Never invent anything:
- A bullet without `text` prints its highlight verbatim, using `text_es` in Spanish.
- A `text` may only shorten, merge, reorder or translate what its cited highlights say. It must not add technologies, numbers, scope, results or claims.
- Cite ids from the same entry only, and never cite one twice.
- The summary may only mention technologies and facts that are in the bank.
- Respect each entry's `client_confidential` note.

To get it right the first time, prefer verbatim bullets. Write a merged `text` only when the page limit forces it.

## 3. Build

Run `.venv/Scripts/python cv/tailor.py build $ARGUMENTS`. It validates the selection, renders the PDF, runs the ATS checks and the 2-page limit, and copies the PDF with a readable name to `cv/out/`.

If it fails, fix only what each error names and run `build` again:
- An unknown id or an id from another entry: cite the right id.
- A number or technology that is not in the sources: drop that detail.
- More than 2 pages: drop the lowest-ranked bullets.

Never edit `data/profile.json` or the generated YAML to get past an error.

## 4. Reply

Reply in the user's language with exactly these lines and nothing else:

```
CV listo: <absolute path from the build's "CV:" line>
Keywords: <covered>/<total> cubiertas<; faltan: <missing>, if any>
```

Add one more line only if `build` lists keywords "not in the profile". That line names them as gaps for the user. Never add them to the CV.
