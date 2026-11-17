---
name: OP / Empleos
description: A personal job cockpit read like a photographer's contact sheet; picks circled, rejects crossed out in grease pencil.
colors:
  ground: "#111214"
  panel: "#1c1d20"
  frame-hover: "#17181b"
  rule: "#2a2c30"
  rule-strong: "#3a3d42"
  paper: "#f2f2ee"
  soft: "#c9cbcf"
  muted: "#8a8d93"
  dim: "#6f7278"
  mark: "#e8d44d"
  mark-hover: "#f0df6a"
  ink-on-mark: "#111214"
typography:
  display-figure:
    fontFamily: "Azeret Mono, ui-monospace, monospace"
    fontSize: "72px"
    fontWeight: 600
    lineHeight: 1
  headline:
    fontFamily: "Familjen Grotesk, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Familjen Grotesk, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  row-title:
    fontFamily: "Familjen Grotesk, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.45
  body:
    fontFamily: "Familjen Grotesk, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "tnum"
  section-label:
    fontFamily: "Familjen Grotesk, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.3
  meta:
    fontFamily: "Familjen Grotesk, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.45
  row-figure:
    fontFamily: "Azeret Mono, ui-monospace, monospace"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1
  frame-code:
    fontFamily: "Azeret Mono, ui-monospace, monospace"
    fontSize: "12px"
    fontWeight: 500
  mark-tag:
    fontFamily: "Azeret Mono, ui-monospace, monospace"
    fontSize: "11px"
    fontWeight: 600
    letterSpacing: "0.04em"
rounded:
  page: "2px"
  tag: "3px"
  focus: "4px"
  chip: "5px"
  control: "6px"
  command: "8px"
spacing:
  hair: "4px"
  xs: "6px"
  sm: "8px"
  md: "16px"
  lg: "22px"
  xl: "28px"
  gutter: "36px"
  gutter-phone: "16px"
components:
  button:
    backgroundColor: "transparent"
    textColor: "{colors.soft}"
    rounded: "{rounded.control}"
    padding: "7px 14px"
    height: "36px"
  button-hover:
    textColor: "{colors.paper}"
  button-pressed:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink-on-mark}"
  button-primary:
    backgroundColor: "{colors.mark}"
    textColor: "{colors.ink-on-mark}"
    rounded: "{rounded.control}"
    padding: "7px 14px"
    height: "36px"
  button-primary-hover:
    backgroundColor: "{colors.mark-hover}"
  filter-chip:
    backgroundColor: "transparent"
    textColor: "{colors.soft}"
    rounded: "{rounded.control}"
    padding: "5px 12px"
    height: "34px"
  keyword-chip:
    textColor: "{colors.paper}"
    rounded: "{rounded.chip}"
    padding: "3px 9px"
  keyword-chip-missing:
    textColor: "{colors.muted}"
    rounded: "{rounded.chip}"
    padding: "3px 9px"
  mark-tag-new:
    backgroundColor: "{colors.mark}"
    textColor: "{colors.ink-on-mark}"
    typography: "{typography.mark-tag}"
    rounded: "{rounded.tag}"
    padding: "2px 6px"
  search-input:
    backgroundColor: "transparent"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "7px 12px"
    height: "36px"
  frame-row:
    backgroundColor: "transparent"
    padding: "14px 12px 14px 4px"
  frame-row-selected:
    backgroundColor: "{colors.panel}"
  detail-panel:
    backgroundColor: "{colors.panel}"
    padding: "28px"
    width: "440px"
  tailor-command:
    backgroundColor: "transparent"
    typography: "{typography.body}"
    rounded: "{rounded.command}"
    padding: "8px 8px 8px 14px"
---

# Design System: OP / Empleos

## Overview

**Creative North Star: "The Contact Sheet"**

Choosing jobs is editing a roll of film. Every frame of today's roll is visible at once as a dense numbered strip on a near-black ground; nothing is hidden behind cards or KPI tiles. The editor's only instrument is a grease pencil: one yellow that circles the keepers, crosses out the rejects, and marks the frames not yet looked at. Everything else is neutral gray so those marks carry all the signal.

Density is high and calm: 1px rules separate rows, figures sit in a monospaced face so columns line up, and the layout never reflows when state changes. Marks are drawn, not stamped: each ring and strike is tilted or bent by a deterministic per-job seed, so no two look identical, and both draw themselves in once when applied. The interface is flat: depth is a single tonal step from ground to panel, never a shadow.

**Key Characteristics:**
- Near-black ground, one raised panel tone, 1px hairline rules.
- One grease-pencil yellow for marks, focus, and the single primary action per view.
- Familjen Grotesk for words, Azeret Mono for frame codes, scores, counts, and commands.
- Hand-drawn SVG ring (shortlist) and strike (discard), seeded per job.
- Score bars whose filled length equals the score exactly.
- Columns fixed; status changes repaint, never reflow.

## Colors

A cold neutral darkroom with one warm grease-pencil yellow; no blue, no red, no terracotta or cream anywhere.

### Primary
- **Grease-Pencil Yellow** (mark): the only chromatic color. Shortlist ring, discard strike, NUEVA tag, primary button (Copiar, Descargar PDF), focus outline, text selection, caret, focused search border, skip link.
- **Pencil Highlight** (mark-hover): primary button hover only.
- **Ink on Mark** (ink-on-mark): text on yellow and on the inverted (pressed) paper button; same value as the ground.

### Neutral
- **Darkroom Ground** (ground): page background, sticky top bar.
- **Contact Panel** (panel): the detail aside, the selected frame row, select menu options.
- **Frame Hover** (frame-hover): row hover tint on the strip and the CV list, one half-step between ground and panel.
- **Hairline** (rule): row separators, section dividers, score-bar track.
- **Strong Hairline** (rule-strong): control borders (buttons, chips, inputs, command box), discarded score-bar fill, scrollbar thumb.
- **Paper** (paper): primary text, score-bar fill, active nav underline, pressed-button fill, POSTULADA outline tag.
- **Soft Paper** (soft): button text at rest, section labels, long-form reading text (reasons, description), secondary links.
- **Muted Graphite** (muted): metadata, frame codes, counts, placeholders, missing-keyword chips, nav at rest.
- **Dim Graphite** (dim): discarded rows only, so struck frames recede under the yellow strike.

### Named Rules
**The Grease Pencil Rule.** Yellow is a mark, never a surface or decoration. It appears only where the editor has marked something (ring, strike, NUEVA), where focus is, or on the one primary action of a view.

**The No Status Color Rule.** Job states are never color-coded with hues. Shortlisted is a ring, discarded is a strike plus dimming, applied is a paper-outlined tag. No green/red/amber semantics.

## Typography

**Display Font:** none separate; the largest element is a figure, set in Azeret Mono.
**Body Font:** Familjen Grotesk (with system-ui, sans-serif), variable 400–700, self-hosted woff2.
**Label/Mono Font:** Azeret Mono (with ui-monospace, monospace), 500–600, self-hosted woff2.

**Character:** a compact, slightly quirky grotesk for every word a person reads, against a wide technical mono for everything that is a number or an identifier, the way a contact sheet's edge print sits beside handwritten notes.

### Hierarchy
- **Display figure** (Azeret Mono 600, 72px, 1): the big score in the detail panel and job page; the only oversized element.
- **Headline** (600, 26px, 1.2, -0.01em): page titles (Ofertas, CVs, CV page). Job page title is 28px (24px on phone).
- **Title** (600, 22px, 1.2, -0.01em, balanced): job title in the detail panel.
- **Row title** (600, 15px): frame and CV list titles, single line with ellipsis on desktop, two-line clamp on phone.
- **Body** (400, 14px, 1.45, tabular numerals): default UI text. Reading text caps at 65–70ch, description at line-height 1.6.
- **Section label** (600, 13px, 1.3, sentence case, soft): headings inside the detail (Palabras clave, Por qué encaja, Adaptar CV).
- **Meta** (400, 13px, muted): company · location · age lines, stack column, hints.
- **Row figure** (Azeret Mono 600, 22px): row scores.
- **Frame code** (Azeret Mono 500, 12px, muted): frame numbers, CV ids, page counts, folios.
- **Mark tag** (Azeret Mono 600, 11px, 0.04em, uppercase): NUEVA and POSTULADA only.

### Named Rules
**The Edge Print Rule.** Numbers and identifiers (scores, frame codes, counts, commands, the roll line, source footer) are Azeret Mono; words are Familjen Grotesk. Never set a sentence in mono or a score in the grotesk.

**The Sentence Case Rule.** Section labels and buttons are sentence case. Uppercase is reserved for the mark tags and the edge-print roll line in the top bar.

## Layout

Desktop is a two-column cockpit: the strip fills the left (`minmax(0,1fr)`), a fixed 440px detail panel sits right (380px under 1100px), sticky under the 60px top bar and scrolling on its own. Page gutter is 36px, 16px at ≤760px.

The frame row is a fixed five-column grid: frame code 44px, who (title + meta) flexible, stack 170px, score bar 160px, score 64px, with 16px gaps and 14px vertical padding. At ≤1280px the stack column drops (40 / 1fr / 120 / 60). At ≤760px the row becomes a two-area grid (who + bar on the left, score on the right, 56px), min-height 72px, the frame code moves inline into the meta line, and the bar thins to 4px.

At ≤760px: the detail panel is hidden and a frame opens its own page; filters stack (full-width search, then a single horizontally scrolling chip rail with no visible scrollbar); the top bar scrolls horizontally, the brand shortens to "OP"; every button and chip grows to 44px minimum height; CV actions split full width.

Spacing rhythm is small and steady: 6 and 8px inside groups, 10–16px between controls, 22px between detail sections, 28px panel padding, 32px between CV pages.

### Named Rules
**The Fixed Columns Rule.** Columns never move. Status, filtering, and selection change color and marks only; no row changes height or column widths on interaction.

**The Exact Bar Rule.** A score bar's fill width is exactly the score in percent of its track. No scaling, no minimum width, no gradient.

## Elevation & Depth

Flat. There are no shadows anywhere, including the CV page images, which sit as bare paper on the ground with a 2px corner. Depth is expressed with one tonal step (ground to panel) and 1px rules; the sticky top bar and panel separate from content with a hairline border, not a shadow.

### Named Rules
**The Hairline Rule.** Separation is a 1px rule (hairline or strong hairline) or a tone step. No shadows, no gradients, no glows.

## Shapes

Gently squared: every radius is 8px or less. Command box 8px, buttons, chips, and inputs 6px, keyword chips 5px, focus outline 4px, mark tags and score-bar tracks 3px, CV page images 2px. Borders are always 1px; the missing-keyword chip is the one dashed border. The only curves with character are the hand-drawn marks: the ring is an open, overshooting ellipse stroke with round caps; the strike is a wobbling, drifting line with a flick at the end.

## Components

### Buttons
Quiet outlines that invert when pressed.
- **Shape:** gently squared (6px), 1px strong-hairline border, 36px min height (44px on phone), 7px 14px padding, weight 500.
- **Default:** transparent, soft text. Hover lifts border to muted and text to paper (160ms, expo-out ease).
- **Pressed (toggle):** `aria-pressed="true"` inverts to a paper fill with ink text. Used by status controls and filter chips.
- **Primary:** yellow fill, ink text, weight 600; hover to the pencil highlight; focus outline switches to paper so it stays visible on yellow. At most one per view (Copiar, Descargar PDF).
- **Copied state:** Copiar briefly becomes a paper-filled "Copiado".
- **Disabled:** 50% opacity, not-allowed cursor.

### Chips
- **Filter chips:** the button vocabulary at 34px, 5px 12px padding; score thresholds (≥ 85, ≥ 70) set in mono 13px. The Estado select wears the same chip with a muted chevron.
- **Keyword chips:** 1px strong-hairline, 5px radius, 3px 9px, paper text for matched; **missing** keywords are dashed with muted text and a screen-reader "Falta:" prefix.

### Inputs / Fields
- **Search:** transparent, 1px strong-hairline, 6px radius, 36px (44px on phone), muted placeholder.
- **Focus:** the border turns yellow with the outline tight (offset 0). Global focus elsewhere is a 2px yellow outline, 2px offset.

### Navigation
Top bar 60px, sticky, ground background, hairline bottom. Brand "OP / EMPLEOS" in mono 600 15px, 0.08em tracking. Nav links in the grotesk 500, muted at rest, paper on hover; the current page gets paper text and a 2px paper underline running the full bar height. The roll line ("ROLLO … · N CUADROS · N NUEVOS") sits right in mono 13px muted and hides under 1100px.

### Frame Row (signature)
The strip is an ordered list of frames with a hairline top and between rows. Hover tints to frame-hover, the selected frame takes the panel tone. The whole row is the link (title pseudo-element covers it), with an inset yellow focus outline. Title row carries the NUEVA tag (yellow fill) until opened and a POSTULADA tag (paper outline) when applied. Discarded rows dim every text cell to dim graphite and the bar fill to strong hairline, then the strike draws across.

### Score and Ring (signature)
A mono figure (22px in rows, 72px in the detail). When shortlisted, an SVG ellipse in yellow (2.4 stroke in rows, 1.3 at the big size, round caps) surrounds it, rotated by a per-job tilt between -8 and 8 degrees. Applying it draws the stroke in over 420ms (`stroke-dashoffset` 1 to 0, expo-out); on load it appears already drawn.

### Strike (signature)
A yellow 1.75 stroke, round caps, laid over the row from the title's x-height drifting toward the score, overshooting both ends. Its bends come from the job id. Draws in over 420ms like the ring.

### Tailor Command
A 1px strong-hairline box with 8px radius holding the `/tailor <id>` command in mono 14px (select-all) and the yellow Copiar button at its right edge.

### CV Page Preview
Each rendered page is shown whole within the viewport height (aspect 1240:1754), white paper on the ground, 2px corner, no frame or shadow, 32px apart, with a mono "n / total" folio under multi-page CVs. Header: title, mono id and page count, a quiet "Abrir PDF" and the primary "Descargar PDF".

### Empty States
Hairline top, 17px paper title, muted explanation capped at 60ch, optionally one quiet button (Quitar filtros).

### Motion
One easing (`cubic-bezier(0.16, 1, 0.3, 1)`), 160ms for hover and color transitions, 420ms for the ring and strike draws. Under `prefers-reduced-motion: reduce` all transitions and animations collapse to 0.01ms, so marks appear already drawn.

## Do's and Don'ts

### Do:
- **Do** keep yellow (#e8d44d) to marks, focus, selection, and one primary action per view.
- **Do** express job state with marks: ring for shortlisted, strike plus dimming for discarded, paper-outlined tag for applied, yellow NUEVA tag for unseen.
- **Do** seed every hand-drawn mark from the job id so no two look stamped.
- **Do** set scores, frame codes, counts, and commands in Azeret Mono; everything else in Familjen Grotesk.
- **Do** separate with 1px rules and a single tonal step; keep radii at 8px or less.
- **Do** give every control a 44px minimum height at ≤760px.
- **Do** keep score-bar fill length equal to the score.

### Don't:
- **Don't** use blue, red, terracotta/coral orange, or warm cream anywhere in the interface.
- **Don't** add shadows, gradients, or glows, including on CV page images.
- **Don't** turn the strip into a card grid or add KPI tiles; the strip is the overview.
- **Don't** color-code job states with hue (no green/amber/red pills).
- **Don't** use yellow as a fill for panels, section backgrounds, or decoration.
- **Don't** reflow columns or change row height when status or filters change.
- **Don't** use dim graphite for live reading text; it belongs only to discarded frames.
