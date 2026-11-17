"""Deterministic helpers behind the `/tailor <job-id>` Claude Code command.

Usage (from the repo root):
    python cv/tailor.py context <job-id>   # job + bank bullets ranked by the job's keywords (JSON)
    python cv/tailor.py build <job-id>     # validate the selection, write YAML, render, check, report

The command (.claude/commands/tailor.md) runs `context`, writes the selection file
`cv/tailored/<job-id>.selection.json` and runs `build`. Choosing and wording bullets is Claude's
job; everything this script does is deterministic:

- `build` rejects any bullet that cites an id that is not in data/profile.json, cites an id of
  another entry, or rephrases a highlight with numbers or technologies its sources do not contain.
- The YAML reuses cv/base.yaml's header, entry headers, design and layout (zero-width-space tricks
  included); only the summary, bullets and skills come from the selection.
- English for jobs abroad, Spanish (`text_es`) for Peru.
- The PDF must pass the ATS checks of cv/build.py and fit in 2 pages before it is published to
  public/cv/, where the site lists it.

Selection file format (JSON):
    {
      "summary": "...",                        # required, plain text in the CV language
      "headline": "...",                       # optional, defaults to base.yaml's headline
      "experience": {"<entry-id>": [{"ids": ["<highlight-id>", ...], "text": "optional rephrase"}]},
      "projects": {"<entry-id>": [...]},       # same shape; every experience/project entry needs >= 1 bullet
      "education": {"<entry-id>": [...]},      # optional, defaults to every education highlight
      "skills": [{"label": "Backend", "details": ["C#", ...]}]   # optional, items from the bank only
    }
A bullet without `text` prints its highlight verbatim (`text_es` in Spanish); a bullet that merges
several ids needs a `text`.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
import types
from datetime import date
from pathlib import Path

import pypdf
from ruamel.yaml import YAML

CV_DIR = Path(__file__).resolve().parent
REPO_ROOT = CV_DIR.parent
for _path in (CV_DIR, REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import build  # noqa: E402  (cv/build.py: rendering + ATS checks)

PROFILE_PATH = REPO_ROOT / "data" / "profile.json"
JOBS_PATH = REPO_ROOT / "data" / "jobs.json"
BASE_YAML = CV_DIR / "base.yaml"
TAILORED_DIR = CV_DIR / "tailored"
PUBLIC_CV = REPO_ROOT / "public" / "cv"
MAX_PAGES = 2
EXCLUDED_MARK = "❓"  # claims flagged with this mark in docs/*.md never reach the bank or the CV


def _import_jobs_scoring():
    """Reuse the job pipeline's keyword logic (jobs/scoring.py, jobs/config.py).

    jobs/config.py loads its YAML with PyYAML, which only the job pipeline's venv installs. The CV
    venv has ruamel.yaml, whose safe loader reads jobs/config.yaml identically, so it stands in.
    """
    try:
        import yaml  # noqa: F401
    except ModuleNotFoundError:
        shim = types.ModuleType("yaml")
        shim.safe_load = lambda text: YAML(typ="safe").load(text)
        sys.modules["yaml"] = shim
    from jobs import config, scoring

    return config, scoring


jobs_config, scoring = _import_jobs_scoring()

# --- Spanish copy for the fixed parts of the reference layout ----------------------------------

SECTION_TITLES_ES = {
    "PROFESSIONAL EXPERIENCE": "EXPERIENCIA PROFESIONAL",
    "PERSONAL PROJECT": "PROYECTO PERSONAL",
    "EDUCATION": "EDUCACIÓN",
    "TECHNOLOGIES AND SKILLS": "TECNOLOGÍAS Y HABILIDADES",
}
HEADER_TEXT_ES = {
    "Lima, Peru": "Lima, Perú",
    "Remote from Lima, Peru": "Remoto desde Lima, Perú",
    "*E-commerce project for a technology accessories retailer · Development and testing stage*":
        "*Proyecto e-commerce para un retailer de accesorios tecnológicos · Etapa de desarrollo y pruebas*",
    "Personal Finance Application": "Aplicación de Finanzas Personales",
    "Bachelor’s Degree in Software Engineering": "Bachiller en Ingeniería de Software",
}
SKILL_LABELS_ES = {
    "Data": "Datos",
    "Cloud and delivery": "Cloud y entrega",
    "Quality": "Calidad",
    "AI-assisted development": "Desarrollo asistido por IA",
    "Languages": "Idiomas",
}
SKILL_DETAILS_ES = {
    "REST APIs and integrations": "APIs REST e integraciones",
    "relational data modeling": "modelado de datos relacional",
    "code reviews": "revisiones de código",
    "agent workflows": "flujos de trabajo con agentes",
    "specification-driven development": "desarrollo guiado por especificaciones",
    "Spanish - Native": "Español - Nativo",
    "English - B2": "Inglés - B2",
}
LOCALE_ES = {"language": "spanish", "present": "Presente"}
LANGUAGE_NAMES = {"en": "English", "es": "Spanish"}

SELECTION_KEYS = {"job_id", "summary", "headline", "experience", "projects", "education", "skills"}
BULLET_KEYS = {"ids", "text"}

# --- Loading ------------------------------------------------------------------------------------


def _read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_profile(path: Path = PROFILE_PATH) -> dict:
    return _read_json(path)


def load_jobs(path: Path = JOBS_PATH) -> list[dict]:
    return _read_json(path)["jobs"]


def load_base(path: Path = BASE_YAML) -> dict:
    return YAML(typ="safe").load(Path(path).read_text(encoding="utf-8"))


def load_scoring_config():
    return jobs_config.load_config()


def find_job(jobs: list[dict], job_id: str) -> dict | None:
    return next((job for job in jobs if job["id"] == job_id), None)


def language_for(job: dict) -> str:
    """S5: Spanish for Peru, English for jobs abroad."""
    return "es" if job.get("market") == "peru" else "en"


# --- Bank helpers -------------------------------------------------------------------------------

SECTIONS = ("experience", "projects", "education")


def highlight_index(profile: dict) -> dict[str, dict]:
    """Highlight id -> {"section", "entry", "highlight"}."""
    return {
        highlight["id"]: {"section": section, "entry": entry["id"], "highlight": highlight}
        for section in SECTIONS
        for entry in profile.get(section, [])
        for highlight in entry["highlights"]
    }


def _numbers(text: str) -> set[str]:
    """Numbers with thousands/decimal separators removed, so 1,747 (en) matches 1.747 (es)."""
    return {re.sub(r"[.,]", "", n) for n in re.findall(r"\d+(?:[.,]\d+)*", text)}


def _highlight_terms(highlight: dict, cfg) -> set[str]:
    terms = {tag for tag in highlight.get("tags", []) if tag in cfg.synonyms}
    for key in ("text", "text_es"):
        if highlight.get(key):
            terms |= scoring.find_terms(highlight[key], cfg)
    return terms


def _bank_texts(profile: dict) -> list[str]:
    texts = [h[key] for item in highlight_index(profile).values() for h in [item["highlight"]]
             for key in ("text", "text_es") if h.get(key)]
    texts += [profile["basics"].get("summary", ""), profile["basics"].get("headline", "")]
    texts += [d for group in profile.get("skills", []) for d in group["details"]]
    texts += [s for project in profile.get("projects", []) for s in project.get("stack", [])]
    return texts


def _profile_terms(profile: dict, cfg) -> set[str]:
    terms = set(scoring.build_vocabulary(profile, cfg))
    for text in _bank_texts(profile):
        terms |= scoring.find_terms(text, cfg)
    return terms


# --- S2: validation -----------------------------------------------------------------------------


def _check_free_text(label: str, text, profile_terms: set[str], bank_numbers: set[str], cfg) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return [f"{label}: must be a non-empty string"]
    errors = []
    if EXCLUDED_MARK in text:
        errors.append(f"{label}: contains {EXCLUDED_MARK} (excluded claims stay out)")
    extra_terms = sorted(scoring.find_terms(text, cfg) - profile_terms)
    if extra_terms:
        errors.append(f"{label}: mentions technologies the bank does not back: {', '.join(extra_terms)}")
    extra_numbers = sorted(_numbers(text) - bank_numbers)
    if extra_numbers:
        errors.append(f"{label}: has numbers that are not in the bank: {', '.join(extra_numbers)}")
    return errors


def _check_bullet(where: str, bullet, entry_id: str, index: dict, seen: set[str], lang: str, cfg) -> list[str]:
    if not isinstance(bullet, dict) or not isinstance(bullet.get("ids"), list) or not bullet["ids"]:
        return [f"{where}: each bullet needs a non-empty `ids` list"]
    errors = [f"{where}: unknown bullet key '{key}'" for key in sorted(set(bullet) - BULLET_KEYS)]
    ids = bullet["ids"]
    sources = []
    for hid in ids:
        if hid in seen:
            errors.append(f"{where}: '{hid}' is cited more than once")
        seen.add(hid)
        item = index.get(hid)
        if item is None:
            errors.append(f"{where}: '{hid}' is not in the bank (data/profile.json)")
        elif item["entry"] != entry_id:
            errors.append(f"{where}: '{hid}' belongs to '{item['entry']}', not '{entry_id}'")
        else:
            sources.append(item["highlight"])
    if len(sources) != len(ids):
        return errors

    text = bullet.get("text")
    if text is None:
        if len(ids) > 1:
            errors.append(f"{where}: a bullet merging {', '.join(ids)} needs a `text`")
        elif lang == "es" and not sources[0].get("text_es"):
            errors.append(f"{where}: '{ids[0]}' has no text_es; give the bullet a Spanish `text`")
        return errors
    if not isinstance(text, str) or not text.strip():
        return [*errors, f"{where}: `text` must be a non-empty string"]

    source_texts = [h[key] for h in sources for key in ("text", "text_es") if h.get(key)]
    if EXCLUDED_MARK in text:
        errors.append(f"{where}: contains {EXCLUDED_MARK} (excluded claims stay out)")
    extra_numbers = sorted(_numbers(text) - set().union(*map(_numbers, source_texts)))
    if extra_numbers:
        errors.append(f"{where}: bullet citing {', '.join(ids)} adds numbers not in its sources: {', '.join(extra_numbers)}")
    source_terms = set().union(*(_highlight_terms(h, cfg) for h in sources))
    extra_terms = sorted(scoring.find_terms(text, cfg) - source_terms)
    if extra_terms:
        errors.append(f"{where}: bullet citing {', '.join(ids)} adds technologies not in its sources: {', '.join(extra_terms)}")
    return errors


def validate_selection(selection: dict, profile: dict, lang: str, cfg) -> list[str]:
    """Every reason the selection could put an unbacked claim on the CV. Empty means valid."""
    if not isinstance(selection, dict):
        return ["the selection must be a JSON object"]
    errors = [f"unknown top-level key '{key}'" for key in sorted(set(selection) - SELECTION_KEYS)]
    index = highlight_index(profile)
    profile_terms = _profile_terms(profile, cfg)
    bank_numbers = set().union(*map(_numbers, _bank_texts(profile)))

    errors += _check_free_text("summary", selection.get("summary"), profile_terms, bank_numbers, cfg)
    if "headline" in selection:
        errors += _check_free_text("headline", selection["headline"], profile_terms, bank_numbers, cfg)

    seen: set[str] = set()
    for section in SECTIONS:
        chosen = selection.get(section)
        if chosen is None and section == "education":
            continue
        if not isinstance(chosen, dict):
            errors.append(f"`{section}` must map entry ids to bullet lists")
            continue
        entry_ids = [entry["id"] for entry in profile.get(section, [])]
        errors += [f"{section}: '{key}' is not an entry in the bank" for key in chosen if key not in entry_ids]
        for entry_id in entry_ids:
            bullets = chosen.get(entry_id)
            if section != "education" and not bullets:
                errors.append(f"{section}: '{entry_id}' needs at least one bullet (every role stays on the CV)")
                continue
            if bullets is not None and not isinstance(bullets, list):
                errors.append(f"{section}.{entry_id}: must be a list of bullets")
                continue
            for n, bullet in enumerate(bullets or [], 1):
                errors += _check_bullet(f"{section}.{entry_id}[{n}]", bullet, entry_id, index, seen, lang, cfg)

    if "skills" in selection:
        errors += _check_skills(selection["skills"], profile)
    if lang == "es":
        errors += _check_education_language(selection, profile)
    return errors


def _check_skills(skills, profile: dict) -> list[str]:
    if not isinstance(skills, list) or not skills:
        return ["skills: must be a non-empty list of {label, details}"]
    bank = {group["label"]: group["details"] for group in profile["skills"]}
    errors, labels = [], set()
    for group in skills:
        label = group.get("label") if isinstance(group, dict) else None
        if label not in bank:
            errors.append(f"skills: '{label}' is not a skill group in the bank")
            continue
        if label in labels:
            errors.append(f"skills: '{label}' appears more than once")
        labels.add(label)
        details = group.get("details")
        if not isinstance(details, list) or not details:
            errors.append(f"skills: '{label}' needs a non-empty `details` list")
            continue
        errors += [f"skills: '{d}' is not under '{label}' in the bank" for d in details if d not in bank[label]]
    return errors


def _check_education_language(selection: dict, profile: dict) -> list[str]:
    """Education entries left out of the selection print every highlight verbatim; in Spanish they need text_es."""
    chosen = selection.get("education") or {}
    return [
        f"education: '{h['id']}' has no text_es; list the education bullets with a Spanish `text`"
        for entry in profile.get("education", []) if entry["id"] not in chosen
        for h in entry["highlights"] if not h.get("text_es")
    ]


# --- S3 / S5: YAML generation -------------------------------------------------------------------


def _bullet_text(bullet: dict, index: dict, lang: str) -> str:
    if bullet.get("text"):
        return bullet["text"]
    highlight = index[bullet["ids"][0]]["highlight"]
    return highlight["text_es"] if lang == "es" else highlight["text"]


def _translate(value, lang: str):
    return HEADER_TEXT_ES.get(value, value) if lang == "es" and isinstance(value, str) else value


def _entry_header(base_entries: list, key: str, profile_entry: dict, section: str) -> dict:
    """The reference layout's entry (base.yaml) without its bullets, or one built from the bank."""
    match = next((e for e in base_entries if isinstance(e, dict) and e.get(key) == profile_entry[key]), None)
    if match is not None:
        return {k: copy.deepcopy(v) for k, v in match.items() if k != "highlights"}
    if section == "experience":
        return {"company": profile_entry["company"], "location": profile_entry.get("location", "​"),
                "position": profile_entry["position"], "start_date": profile_entry["start_date"],
                "end_date": profile_entry["end_date"]}
    if section == "projects":
        return {"name": profile_entry["name"], "summary": " · ".join(profile_entry["stack"][:5])}
    return {"institution": profile_entry["institution"], "area": f"{profile_entry['degree']} in {profile_entry['area']}",
            "location": profile_entry.get("location", "​"),
            "date": f"{profile_entry['start_date']} - {profile_entry['end_date']}"}


def _skills_lines(skills: list[dict], lang: str) -> list[dict]:
    lines = []
    for group in skills:
        details = [SKILL_DETAILS_ES.get(d, d) if lang == "es" else d for d in group["details"]]
        separator = " · " if group["label"] == "Languages" else ", "
        label = SKILL_LABELS_ES.get(group["label"], group["label"]) if lang == "es" else group["label"]
        lines.append({"label": label, "details": separator.join(details) + "."})
    return lines


def render_yaml(selection: dict, profile: dict, base: dict, lang: str) -> dict:
    """RenderCV document: base.yaml's header, entry headers and design with the selected content."""
    index = highlight_index(profile)
    base_sections = base["cv"]["sections"]
    summary_title, experience_title, project_title, education_title, skills_title = list(base_sections)

    def title(name: str) -> str:
        return SECTION_TITLES_ES.get(name, name) if lang == "es" else name

    cv = {k: copy.deepcopy(v) for k, v in base["cv"].items() if k != "sections"}
    cv["location"] = _translate(cv["location"], lang)
    if selection.get("headline"):
        cv["headline"] = selection["headline"]

    def entries(section: str, base_title: str, key: str) -> list[dict]:
        rendered = []
        for profile_entry in profile.get(section, []):
            bullets = (selection.get(section) or {}).get(profile_entry["id"])
            if bullets is None and section == "education":
                bullets = [{"ids": [h["id"]]} for h in profile_entry["highlights"]]
            if not bullets:
                continue
            header = _entry_header(base_sections[base_title], key, profile_entry, section)
            header = {k: _translate(v, lang) for k, v in header.items()}
            header["highlights"] = [_bullet_text(b, index, lang) for b in bullets]
            rendered.append(header)
        return rendered

    sections = {
        summary_title: [f"*{selection['summary']}*"],
        title(experience_title): entries("experience", experience_title, "company"),
        title(project_title): entries("projects", project_title, "name"),
        title(education_title): entries("education", education_title, "institution"),
        title(skills_title): _skills_lines(selection.get("skills") or profile["skills"], lang),
    }
    cv["sections"] = {name: content for name, content in sections.items() if content}
    locale = copy.deepcopy(base.get("locale", {})) if lang == "en" else dict(LOCALE_ES)
    return {"cv": cv, "design": copy.deepcopy(base["design"]), "locale": locale}


def write_yaml(doc: dict, path: Path, job_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = YAML()
    yaml.width = 4096
    yaml.allow_unicode = True
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"# Tailored CV for {job_id}. Generated by cv/tailor.py from {job_id}.selection.json;\n"
                     "# edit the selection and rerun `python cv/tailor.py build` instead of this file.\n")
        yaml.dump(doc, handle)


# --- S1: context --------------------------------------------------------------------------------


def job_terms(job: dict, cfg) -> dict[str, float]:
    """The job's weighted tech terms, extracted exactly as the job scorer does."""
    terms = scoring.extract_terms(job["title"], job.get("description", ""), cfg)
    return dict(sorted(terms.items(), key=lambda item: (-item[1], item[0])))


def build_context(job: dict, profile: dict, cfg) -> dict:
    lang = language_for(job)
    terms = job_terms(job, cfg)
    entries = []
    for section in SECTIONS:
        for entry in profile.get(section, []):
            ranked = []
            for position, highlight in enumerate(entry["highlights"]):
                covers = [t for t in terms if t in _highlight_terms(highlight, cfg)]
                weight = 1.0 if highlight["evidence"] == "verified" else 0.8
                item = {"id": highlight["id"], "relevance": round(sum(terms[t] for t in covers) * weight, 3),
                        "covers": covers, "evidence": highlight["evidence"], "text": highlight["text"]}
                if highlight.get("text_es"):
                    item["text_es"] = highlight["text_es"]
                ranked.append((position, item))
            ranked.sort(key=lambda pair: (-pair[1]["relevance"], pair[0]))
            summary = {"section": section, "id": entry["id"],
                       "title": entry.get("company") or entry.get("name") or entry.get("institution")}
            for key in ("position", "start_date", "end_date", "client_confidential"):
                if entry.get(key):
                    summary[key] = entry[key]
            summary["highlights"] = [item for _, item in ranked]
            entries.append(summary)
    return {
        "job": {key: job.get(key) for key in ("id", "title", "company", "location", "market", "score",
                                              "matched", "missing", "description")} | {"terms": terms},
        "language": lang,
        "language_reason": f"market={job.get('market')}: write the CV in {LANGUAGE_NAMES[lang]}"
                           + (" (use text_es; translate highlights without it)" if lang == "es" else ""),
        "selection_path": (TAILORED_DIR / f"{job['id']}.selection.json").relative_to(REPO_ROOT).as_posix(),
        "base": {"headline": profile["basics"]["headline"], "summary": profile["basics"].get("summary", "")},
        "skills": profile["skills"],
        "entries": entries,
    }


# --- S7: coverage report ------------------------------------------------------------------------


def coverage(job: dict, text: str, profile: dict, cfg) -> dict[str, list[str]]:
    terms = job_terms(job, cfg)
    on_cv = scoring.find_terms(text, cfg)
    profile_terms = _profile_terms(profile, cfg)
    missing = [t for t in terms if t not in on_cv]
    return {
        "covered": [t for t in terms if t in on_cv],
        "missing": missing,
        "missing_in_bank": [t for t in missing if t in profile_terms],
        "missing_not_in_profile": [t for t in missing if t not in profile_terms],
    }


def _labels(terms: list[str], cfg) -> str:
    return ", ".join(cfg.label(t) for t in terms) or "none"


def _display(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


# --- CLI ----------------------------------------------------------------------------------------


class TailorError(Exception):
    pass


def _job_or_fail(job_id: str, jobs_path: Path) -> dict:
    job = find_job(load_jobs(jobs_path), job_id)
    if job is None:
        raise TailorError(f"{job_id} is not in {_display(jobs_path)} (jobs are pruned after 30 days).")
    return job


def cmd_context(args) -> int:
    job = _job_or_fail(args.job_id, args.jobs)
    context = build_context(job, load_profile(args.profile), load_scoring_config())
    print(json.dumps(context, ensure_ascii=False, separators=(",", ":")))
    return 0


def cmd_build(args) -> int:
    job = _job_or_fail(args.job_id, args.jobs)
    profile, cfg, lang = load_profile(args.profile), load_scoring_config(), language_for(job)
    selection_path = args.selection or args.tailored_dir / f"{job['id']}.selection.json"
    if not selection_path.is_file():
        raise TailorError(f"Selection file not found: {_display(selection_path)}. Run `context` and write it first.")
    try:
        selection = _read_json(selection_path)
    except json.JSONDecodeError as error:
        raise TailorError(f"{_display(selection_path)} is not valid JSON: {error}") from error
    errors = validate_selection(selection, profile, lang, cfg)
    if isinstance(selection, dict) and selection.get("job_id") not in (None, job["id"]):
        errors.append(f"job_id is '{selection['job_id']}', expected '{job['id']}'")
    if errors:
        raise TailorError("The selection was rejected:\n" + "\n".join(f"  - {e}" for e in errors))

    doc = render_yaml(selection, profile, load_base(), lang)
    yaml_path = args.tailored_dir / f"{job['id']}.yaml"
    write_yaml(doc, yaml_path, job["id"])

    with tempfile.TemporaryDirectory(prefix="tailor_") as staging:
        try:
            rendered = build.build(yaml_path, Path(staging))
        except (FileNotFoundError, RuntimeError) as error:
            raise TailorError(str(error)) from error
        pdf = rendered[0]
        pages = len(pypdf.PdfReader(pdf).pages)
        if pages > MAX_PAGES:
            raise TailorError(f"The CV has {pages} pages; the limit is {MAX_PAGES}. "
                              "Drop or shorten bullets in the selection and rebuild.")
        problems = build.ats_problems(pdf, doc["cv"], doc["locale"])
        if problems:
            raise TailorError("The PDF failed the ATS checks:\n" + "\n".join(f"  - {p}" for p in problems))
        text = build.normalize(build.pdf_text(pdf))
        published = build.publish(rendered, args.out, job["id"])

    report = coverage(job, text, profile, cfg)
    meta = {"id": job["id"], "title": job["title"], "company": job["company"], "market": job.get("market"),
            "language": lang, "generated_at": date.today().isoformat(), "pages": pages,
            "covered": report["covered"], "missing": report["missing"]}
    meta_path = args.tailored_dir / f"{job['id']}.meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    total = len(report["covered"]) + len(report["missing"])
    print(f"Tailored CV for {job['id']}: {job['title']} at {job['company']} ({LANGUAGE_NAMES[lang]}, market {job.get('market')})")
    print(f"Covered keywords: {_labels(report['covered'], cfg)} ({len(report['covered'])}/{total})")
    print(f"Missing keywords: {_labels(report['missing'], cfg)}")
    if report["missing_in_bank"]:
        print(f"  in the bank but not on this CV: {_labels(report['missing_in_bank'], cfg)}")
    if report["missing_not_in_profile"]:
        print(f"  not in the profile (do not add): {_labels(report['missing_not_in_profile'], cfg)}")
    print(f"Pages: {pages}")
    print("Files:")
    for path in [selection_path, yaml_path, meta_path, *published]:
        print(f"  {_display(path)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Tailor the CV to one job from data/jobs.json.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, helptext in (("context", "print the job and the ranked bank bullets as JSON"),
                           ("build", "validate the selection, render the CV and report coverage")):
        cmd = sub.add_parser(name, help=helptext)
        cmd.add_argument("job_id", help="job id from data/jobs.json, e.g. job-b9c6199b")
        cmd.add_argument("--jobs", type=Path, default=JOBS_PATH, help="jobs file (default: data/jobs.json)")
        cmd.add_argument("--profile", type=Path, default=PROFILE_PATH, help="bank (default: data/profile.json)")
        if name == "build":
            cmd.add_argument("--selection", type=Path, help="selection file (default: cv/tailored/<job-id>.selection.json)")
            cmd.add_argument("--tailored-dir", type=Path, default=TAILORED_DIR, help="where the YAML and meta go")
            cmd.add_argument("--out", type=Path, default=PUBLIC_CV, help="where the PDF and PNGs go (default: public/cv)")
    args = parser.parse_args(argv)
    try:
        return cmd_context(args) if args.command == "context" else cmd_build(args)
    except TailorError as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
