---
description: Write a one-page cover letter for one job from data/jobs.json and publish it
argument-hint: <job-id>
allowed-tools: Bash(.venv/Scripts/python cv/tailor.py:*), Bash(.venv/bin/python cv/tailor.py:*), Read, Write, Edit
---

Write the cover letter for job `$ARGUMENTS`, publish it to `main` and hand the user the PDF.

The user only wants the file, published. Run the steps below without narrating them, asking questions or offering options. The user has pre-authorized step 4 (commit and push to `main`), so don't ask before it. Do no other git operation, and don't run npm or start a server. Work from the repository root and use `.venv/Scripts/python` (`.venv/bin/python` outside Windows).

## 1. Context

Run `.venv/Scripts/python cv/tailor.py context $ARGUMENTS`. It prints the job (`description`, keyword `terms`), the `language` (`en` abroad, `es` for Peru) and the bank `entries`, with the highlights ranked by relevance to this job.

If `cv/tailored/$ARGUMENTS.selection.json` exists, read it too, so the letter stresses the same facts as the CV.

If the job is not found, say so in one line and stop.

## 2. Letter

Write `cv/tailored/$ARGUMENTS.letter.json` in the context's `language`:

```json
{
  "job_id": "$ARGUMENTS",
  "greeting": "Dear Hiring Team,",
  "paragraphs": ["...", "...", "..."],
  "closing": "Sincerely,"
}
```

In Spanish, use "Estimado equipo de selección:" and "Atentamente,".

The letter has 3-4 short paragraphs and fewer than 300 words:
1. The role you are applying for, and why your profile fits it. Tie this to 2-3 requirements in the posting.
2. One or two concrete achievements from the top-ranked highlights that prove that fit.
3. Optionally, how you work: AI-assisted delivery, testing, ownership. Use it only if the posting values it.
4. A short close that offers a conversation.

Never invent anything:
- Every fact about the user must come from the bank's highlights.
- Mention only technologies and numbers that appear in the bank; the build rejects any others. You may name the company and the role. Don't write claims about the company that aren't in the posting.
- Respect each entry's `client_confidential` note.
- Write in plain sentences, with no bullet lists, no markdown and no placeholders such as "[Company]".

## 3. Build

Run `.venv/Scripts/python cv/tailor.py letter $ARGUMENTS`.

It validates the letter, renders it on one page in the CV's typeface and header, checks the PDF text, and writes `public/cv/letters/$ARGUMENTS.pdf` plus a copy with a readable name in `cv/out/`.

If it fails, fix only what each error names and run it again. Never edit `data/profile.json` to get past an error.

## 4. Publish

Run `.venv/Scripts/python cv/tailor.py publish $ARGUMENTS`. It commits only this job's CV and letter files and pushes them to `origin/main`.

If it fails, still hand over the PDF in step 5 and add one line that quotes the error.

## 5. Reply

Reply in the user's language with exactly these lines and nothing else:

```
Carta lista: <absolute path from the "Carta:" line>
Publicada en main (<commit>); la web se actualiza en ~2 min.
```
