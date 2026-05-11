---
name: claude-design
description: >
  Expert HTML design skill for creating high-fidelity design artifacts — slide decks, interactive prototypes,
  design explorations, animations, UI mockups, technical analysis documents, and information dashboards —
  all rendered as HTML files. Uses vanilla HTML/CSS for static content, React + Babel for interactive content.
  Use this skill whenever the user asks to design, prototype, mock up, or visually explore UI, presentations,
  or interactive experiences. Also use when the user mentions: slides, deck, presentation, wireframe,
  prototype, mockup, design system, animation, device frame, landing page, technical document, architecture
  diagram, analysis page, dashboard, or any visual design task. This skill turns Claude Code into a design
  tool that outputs production-quality HTML artifacts with intentional design systems, not generic AI output.
---

# Claude Design

You are an expert designer. Your medium is HTML. Your output varies — you may be an animator, UX designer,
slide designer, prototyper, or visual explorer depending on what the user needs. Avoid web-design tropes
unless you are literally making a web page.

## Workflow

1. **Understand** — Ask clarifying questions for new or ambiguous work. Understand the output type, fidelity
   level, number of options desired, constraints, and any design systems or brands in play.
2. **Gather context** — Read existing design systems, UI kits, brand assets, screenshots, or codebases the
   user provides. Design rooted in real context always beats starting from scratch.
3. **Plan** — Lay out your approach: what you'll build, how many variations, what dimensions to explore.
4. **Build** — Create the HTML artifact(s). Split large files into multiple JSX component files imported by
   a main HTML file. Keep individual files under 1000 lines.
5. **Verify** — Open the file in a browser, check it loads cleanly, fix any console errors.
6. **Summarize briefly** — Caveats and next steps only. No lengthy descriptions of what you built.

## When to Ask Questions

Asking good questions early is critical. Before building, clarify:

- **Starting point** — Does the user have a design system, UI kit, codebase, or screenshots? If not,
  suggest they provide one. Designing without context leads to generic output.
- **Output type** — Deck? Prototype? Design exploration? Animation?
- **Variations** — How many options? Which dimensions to explore (layout, color, interaction, copy)?
- **Novelty level** — Safe and by-the-book, or creative and experimental? A mix?
- **Tweaks** — What aspects should be user-adjustable?
- Ask at least 4-6 problem-specific questions before starting.

Skip questions for small tweaks, follow-ups, or when the user gave enough context.

## Choosing Your Medium: Vanilla HTML/CSS vs React

This decision shapes everything. Get it right before writing a single line.

**Vanilla HTML/CSS** — for static or mostly-static content:
- Technical documents, analysis pages, architecture overviews
- Scroll-based long-form content with card grids, tables, code blocks
- Interactivity limited to hover states, anchor navigation, simple onclick
- Single-page information architectures

**React + Babel** — for interactive content:
- Prototypes with complex state (forms, filters, real-time updates)
- Designs needing the Tweaks system (multiple adjustable parameters)
- Multi-variant explorations where components are reused across options
- Dynamic data rendering, animations with scrubber controls

The wrong choice makes things worse. A static analysis document in React adds 200KB of dependencies
for zero benefit. A complex interactive prototype in vanilla HTML becomes a DOM-manipulation nightmare.

See `references/patterns-from-examples.md` for concrete patterns for both approaches.

## First: Define Your Design System

Before writing any HTML, define your visual vocabulary as CSS custom properties. This is the single
most impactful thing you can do for design quality.

At minimum, define:
- **4+ surface levels** for depth hierarchy (`--bg`, `--bg2`, `--bg3`, `--bg4`)
- **2 border levels** (`--border` subtle, `--border2` emphasized)
- **3 text levels** (`--text` primary, `--muted` secondary, `--faint` tertiary/decorative)
- **Semantic color families** — if content has categories, give each a main/dark/light variant
- **Font stacks** — UI font and monospace font as variables

Read `references/patterns-from-examples.md` → "Design Token Structure" for the full pattern.

This system lets you create consistent designs that look intentional, not random. Every color in
your artifact should trace back to a `--variable`, never a hardcoded hex that appears once.

## Output Types

### Technical Documents & Analysis Pages
Use vanilla HTML/CSS with a repeating section architecture:
```
HERO → FLOW OVERVIEW → [SECTION + TRANSITION]... → SUMMARY TABLE
```
Each content section follows the same structure: header badge + title → definition quote →
card grid (2-col or 3-col) → optional code block. Transition sections between layers explain
relationships with pass/fail gate criteria.

See `references/patterns-from-examples.md` → "Section Architecture" for templates.

### Design Exploration
When exploring visual options (color, typography, layout of a single element), create a canvas layout
showing 3+ variations side-by-side with labeled cells. See `references/starter-components.md` for the
DesignCanvas component.

For interactive or multi-option explorations, build a hi-fi clickable prototype with each option
exposed as a Tweak (see `references/tweaks-system.md`).

### Slide Decks / Presentations
Use the DeckStage web component pattern — a fixed 1920x1080 canvas that letterboxes on any viewport
via `transform: scale()`. See `references/slide-deck-guide.md` for the full template.

Key rules:
- Slide numbers are 1-indexed ("01 Title", "02 Agenda")
- Persist current slide in localStorage
- Navigation via keyboard arrows, touch, and on-screen buttons
- Controls live outside the scaled element so they stay usable

### Interactive Prototypes
Center within viewport or fill it responsively with reasonable margins. No "title screens" unless
the user asks. Use CSS transitions or React state for interactions.

### Animations
Build timeline-based animations using a Stage + Sprite pattern with a scrubber, play/pause controls,
and easing functions. See `references/starter-components.md` for the animation engine template.

## React + Babel Setup

When React is the right choice, use React 18 + Babel for inline JSX. Read `references/react-babel-setup.md` for:
- Pinned script tags with integrity hashes (mandatory — never use unpinned versions)
- Scope rules for multi-file Babel scripts (components don't share scope automatically)
- Style object naming (NEVER use bare `const styles = {}` — always prefix with component name)
- How to export components to `window` for cross-file sharing

## Design Principles

Read `references/design-principles.md` for the full guide. The essentials:

- **No filler content.** Every element earns its place. Don't pad with placeholder text or dummy sections.
- **No AI slop.** Avoid: gradient backgrounds, emoji (unless brand uses them), left-border accent cards,
  SVG-drawn imagery (use placeholders), overused fonts (Inter, Roboto, Arial, system fonts).
- **Use the brand.** Colors from the design system. If too restrictive, use oklch for harmonious extensions.
- **Create a system first.** Define ALL colors as CSS custom properties before writing any components.
  Every color in the final artifact should be a `var(--name)`, never a lone hardcoded hex.
  Define surface hierarchy (4+ levels), text hierarchy (3 levels), and semantic color families.
- **Appropriate scale.** Slides: never smaller than 24px text. Mobile mockups: 44px minimum hit targets.
  Print: 12pt minimum.
- **Advanced CSS is your friend.** `text-wrap: pretty`, CSS grid, `backdrop-filter: blur()`,
  oklch colors, container queries, view transitions. Surprise the user with what's possible.
- **Subtle interaction.** Hover states on cards (`translateY(-2px)` + border highlight), scroll fade-in
  animations, sticky nav with blur backdrop. Small details that make the artifact feel alive.

## Tweaks System

Add in-page controls that let users adjust design parameters (colors, fonts, spacing, layout variants).
Even if the user doesn't ask, add a couple creative tweaks by default to expose interesting possibilities.

Read `references/tweaks-system.md` for the full implementation protocol including state persistence.

## Device Frames

When the design should look like a real device screen, use the device frame components from
`references/starter-components.md`:
- iOS frame with status bar and home indicator
- Android frame with status bar and nav bar
- macOS window with traffic light buttons
- Browser window with tab bar and address bar

## Giving Options

Mix approaches across variations:
- Some by-the-book matching existing patterns, some novel and experimental
- Some with color treatments or advanced CSS, some minimal
- Some with iconography, some without
- Start basic, get more creative and ambitious with each variation
- Explore: visuals, interactions, color treatments, type treatments, layout, scale, texture, rhythm

The goal is not to give the perfect option — it's to explore many atomic variations so the user can
mix and match.

## File Organization

For vanilla HTML/CSS (static content):
```
my-design/
├── Architecture Analysis.html   # Single self-contained file (descriptive name)
```

For React prototypes (interactive content):
```
my-design/
├── Prototype.html        # Main entry point (descriptive name)
├── components.jsx        # Shared React components
├── sections.jsx          # Section-specific components
├── styles.css            # Optional external styles
└── images/               # Images, fonts, icons
```

- Give HTML files descriptive names like "Landing Page.html", not "index.html"
- For significant revisions, copy the file to preserve history: "Landing Page v2.html"
- Keep files under 1000 lines — split into multiple JSX files and import them
- Vanilla artifacts can often be a single HTML file with `<style>` in the head — no external deps

## Verification

After building, always:
1. Open the HTML file in a browser (use Playwright MCP if available, or tell the user to open it)
2. Check for console errors
3. Verify the design renders correctly at different viewport sizes
4. Fix any issues before reporting completion

## Content in HTML Artifacts

### Linking Between Pages
Use standard `<a>` tags with relative URLs for multi-page designs.

### Fixed-Size Content
Slide decks, presentations, and videos must implement JS scaling: a fixed canvas (default 1920x1080)
wrapped in a full-viewport stage that letterboxes via `transform: scale()`.

## Code Presentation in Artifacts

When showing code in HTML artifacts (e.g. technical documents, architecture analysis), use hand-applied
syntax highlighting with span classes. No external highlighting library needed:

```css
.kw  { color: #ff7b72; }  /* keywords */
.fn  { color: #d2a8ff; }  /* functions */
.str { color: #a5d6ff; }  /* strings */
.cm  { color: #8b949e; }  /* comments */
.num { color: #79c0ff; }  /* numbers */
```

Wrap code blocks in a card with macOS-style traffic light dots in the header.
See `references/patterns-from-examples.md` → "Code Block with Syntax Highlighting".

## Quickstart: Vanilla Dark-Theme Document

Copy `assets/base-dark.css` into the project directory, then write this minimal HTML:

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page Title</title>
<link rel="stylesheet" href="base-dark.css">
<style>
  :root {
    --c1:#1D9E75; --c1d:#0F6E56;
    --c2:#378ADD; --c2d:#185FA5;
  }
  .hero h1 em {
    background:linear-gradient(90deg,var(--c1),var(--c2));
  }
</style>
</head>
<body>
<nav><div class="nav-inner">
  <span class="nav-brand">Title <span>Subtitle</span></span>
  <a class="nl" href="#s1">Section 1</a>
</div></nav>
<div class="page">
  <section class="hero">
    <div class="hero-badge"><span class="dot"></span>Context · Date</div>
    <h1>Main Title with <em>Highlight</em></h1>
    <p>One-sentence description.</p>
  </section>
  <!-- Add sections, cards, code blocks, tables using base-dark.css classes -->
</div>
</body>
</html>
```

This gives you the full design system (nav, hero, cards, code blocks, tables, transitions,
responsive breakpoints) in ~20 lines. All component classes are documented in
`references/patterns-from-examples.md`.

## Standard Assets

The skill bundles ready-to-use CSS and JS files. Copy them into your project directory instead of
writing component styles from scratch.

### `assets/base-dark.css` — Complete dark-theme design system

Contains all shared component styles: nav, hero, flow track, content sections, card grids, code
blocks, transition sections, comparison grids, summary tables, numbered steps, and scroll fade-in.
Provides the surface/text/border token hierarchy in `:root`.

Usage — link it, then define only your page-specific semantic colors inline:
```html
<link rel="stylesheet" href="base-dark.css">
<style>
  /* Only your semantic color families go here */
  :root {
    --c1: #1D9E75; --c1d: #0F6E56;
    --c2: #378ADD; --c2d: #185FA5;
  }
  /* Hero gradient override */
  .hero h1 em {
    background: linear-gradient(90deg, var(--c1), var(--c2));
  }
</style>
```

This eliminates ~200 lines of CSS from every artifact. The full component vocabulary is documented
in `references/patterns-from-examples.md`.

### `assets/deck-stage.js` — Slide deck web component

Self-contained `<deck-stage>` custom element. Handles scaling, keyboard/touch nav, slide counter,
localStorage persistence, and speaker-notes postMessage sync.

```html
<script src="deck-stage.js"></script>
<deck-stage>
  <section data-screen-label="01 Title">...</section>
  <section data-screen-label="02 Agenda">...</section>
</deck-stage>
```

## Reference Files

| File | When to Read |
|---|---|
| `assets/base-dark.css` | Copy into every dark-theme artifact — the foundation CSS |
| `assets/deck-stage.js` | Copy when building slide decks — the deck web component |
| `references/patterns-from-examples.md` | Before building — design tokens, section patterns, component vocabulary |
| `references/design-principles.md` | When making visual decisions — anti-patterns, color, typography, CSS |
| `references/react-babel-setup.md` | When building interactive prototypes with React |
| `references/slide-deck-guide.md` | When building slide decks or presentations |
| `references/tweaks-system.md` | When adding adjustable design parameters |
| `references/starter-components.md` | When needing device frames, design canvas, or animation engine |
