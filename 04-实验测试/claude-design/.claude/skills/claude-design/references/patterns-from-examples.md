# Concrete Design Patterns

Proven patterns extracted from high-quality HTML artifacts. This document explains **why** each
pattern works — the **implementation** is in `assets/base-dark.css`, ready to copy into your project.

## Table of Contents
- [When to Use Vanilla HTML/CSS vs React](#when-to-use-vanilla-htmlcss-vs-react)
- [Design Token Structure](#design-token-structure)
- [Surface Hierarchy (Dark Theme)](#surface-hierarchy-dark-theme)
- [Surface Hierarchy (Light Theme)](#surface-hierarchy-light-theme)
- [Section Architecture](#section-architecture)
- [Component Patterns](#component-patterns)
- [Chinese / CJK Typography](#chinese--cjk-typography)

---

## When to Use Vanilla HTML/CSS vs React

**Vanilla HTML/CSS** when:
- Content is static or mostly static (documents, reports, analysis pages)
- Interactivity is limited to hover states, anchor links, or simple onclick navigation
- The artifact is a single-page information architecture (e.g. technical analysis, deck-as-scrollpage)
- No complex state management needed

**React + Babel** when:
- Rich interactivity: forms, filters, real-time updates, complex state
- Tweaks system needed (multiple adjustable parameters)
- Component reuse across multiple variants or options
- Dynamic data rendering, sorting, filtering

The wrong choice makes things worse. A static analysis document in React is heavier, slower, and
harder to maintain. A complex interactive prototype in vanilla HTML becomes a tangle of DOM manipulation.

---

## Design Token Structure

Define all visual decisions as CSS custom properties upfront. This is the single most impactful
pattern for design consistency.

### Multi-Family Color System

When content has semantic categories (layers, phases, status types), define a color family for each
with 3 variants: main, dark, and light/background.

```css
:root {
  /* Surface hierarchy — 4 levels minimum */
  --bg: #0d1117;      /* deepest background */
  --bg2: #161b22;     /* cards, elevated surfaces */
  --bg3: #21262d;     /* hover states, active surfaces */
  --bg4: #2d333b;     /* highest elevation */

  /* Border hierarchy */
  --border: rgba(255,255,255,0.08);   /* subtle dividers */
  --border2: rgba(255,255,255,0.18);  /* emphasized borders, hover */

  /* Text hierarchy — 3 levels */
  --text: #e6edf3;    /* primary content */
  --muted: #7d8590;   /* secondary, labels, captions */
  --faint: #3d444d;   /* tertiary, decorative, disabled */

  /* Semantic color families (example: 5 categories) */
  --c1: #1D9E75;      /* main */
  --c1d: #0F6E56;     /* dark — for badges, headers */
  --c1b: #E1F5EE;     /* light — for light-theme backgrounds */

  --c2: #378ADD;
  --c2d: #185FA5;
  --c2b: #E6F1FB;

  /* ... repeat for each category */

  /* Typography */
  --font: system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --mono: 'SF Mono', 'Cascadia Code', Consolas, 'Courier New', monospace;
}
```

### Why Three Variants Per Color

| Variant | Use Case | Example |
|---|---|---|
| Main (`--c1`) | Text labels, tag text, inline accents | `color: var(--c1)` |
| Dark (`--c1d`) | Badge backgrounds, header backgrounds | `background: var(--c1d); color: light-text` |
| Light (`--c1b`) | Light-theme card backgrounds, subtle fills | `background: var(--c1b)` |

---

## Surface Hierarchy (Dark Theme)

Dark themes need at least 4 surface levels to create depth without borders:

```
┌─────────────────────────────────────────┐
│  --bg (#0d1117)     Page background     │
│  ┌───────────────────────────────────┐  │
│  │  --bg2 (#161b22)  Cards, panels   │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  --bg3 (#21262d)  Hover      │  │  │
│  │  │  ┌───────────────────────┐  │  │  │
│  │  │  │  --bg4 (#2d333b)  Max │  │  │  │
│  │  │  └───────────────────────┘  │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

Key patterns:
- **Nav**: `rgba(bg, 0.94)` + `backdrop-filter: blur(12px)` for sticky headers
- **Cards**: `--bg2` with `1px solid var(--border)`
- **Card hover**: `--bg3` + `border-color: var(--border2)` + `translateY(-2px)`
- **Transition sections**: `linear-gradient(180deg, var(--bg2), var(--bg))` for visual breaks

---

## Surface Hierarchy (Light Theme)

```css
:root {
  --bg: #ffffff;
  --bg2: #f6f8fa;    /* cards */
  --bg3: #eef1f5;    /* hover */
  --bg4: #dde1e6;    /* max elevation */
  --border: rgba(0,0,0,0.08);
  --border2: rgba(0,0,0,0.15);
  --text: #1a1a1a;
  --muted: #656d76;
  --faint: #b1bac4;
}
```

---

## Section Architecture

Long-form technical content benefits from a repeating section pattern:

```
HERO → FLOW OVERVIEW → [SECTION + TRANSITION]... → SUMMARY
```

### Hero Section
```html
<section class="hero">
  <div class="badge"><span class="dot"></span> Context Label · Date</div>
  <h1>Main Title with <em>Gradient Keyword</em></h1>
  <p class="subtitle">One-sentence description. Specific, not generic.</p>
  <div class="tag-row">
    <span class="tag" style="color:var(--c1);...">Category 1</span>
    <span class="tag" style="color:var(--c2);...">Category 2</span>
  </div>
</section>
```

Key: The `<em>` in the title uses a gradient text treatment for emphasis:
```css
h1 em {
  font-style: normal;
  background: linear-gradient(90deg, var(--c1), var(--c2), var(--c3));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Flow Overview (Horizontal Process)
```html
<div class="flow-track">
  <div class="flow-box" style="border-color:rgba(color, 0.3)">
    <div class="tag" style="color:var(--c1)">STEP 1</div>
    <div class="name">Step Name</div>
    <div class="subtitle">Brief description</div>
    <div class="detail">Technical details<br>in monospace</div>
  </div>
  <div class="flow-arrow">
    <span class="icon">→</span>
    <span class="label">What happens between</span>
  </div>
  <!-- repeat -->
</div>
```

CSS: `display:flex; align-items:stretch; gap:0` for the track; each box is `flex:1; min-width:0`.

### Content Section Pattern
```html
<section class="layer-sec" id="section-id">
  <!-- Header: badge + title -->
  <div class="header">
    <span class="id-badge" style="background:var(--c1d);color:light">ID</span>
    <h2>Section Title <small>Subtitle</small></h2>
  </div>

  <!-- Definition: border-left accent quote -->
  <p class="definition" style="border-color:var(--c1)">
    Core definition. One paragraph. Uses <strong>bold</strong> for the key phrase.
  </p>

  <!-- Card grid: 2 or 3 columns -->
  <div class="grid3">
    <div class="card">
      <div class="card-title">CARD HEADING</div>
      <ul><li>Item with <strong>bold</strong> emphasis</li></ul>
    </div>
    <!-- more cards -->
  </div>

  <!-- Optional: code block -->
  <div class="codeblock">
    <div class="cb-head">
      <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
      filename.py · description
    </div>
    <div class="cb-body"><!-- syntax highlighted code --></div>
  </div>
</section>
```

### Transition / Gate Section
Between content sections, use transition sections to explain the relationship:
```html
<section class="transition-sec">
  <span class="pill" style="background:var(--c1d);color:light">A → B · Gate Name</span>
  <h3>N criteria — What qualifies?</h3>
  <p>Explanation of the transition logic.</p>
  <div class="gate">
    <span class="gate-item pass">✓ Passes when...</span>
    <span class="gate-item fail">✗ Rejected when...</span>
    <span class="gate-item note">· Neutral observation</span>
  </div>
</section>
```

Gate items use semantic colors:
```css
.pass { color: var(--c1); border-color: rgba(c1, 0.35); background: rgba(c1, 0.06); }
.fail { color: #f85149; border-color: rgba(248,81,73,0.35); background: rgba(248,81,73,0.06); }
.note { color: var(--muted); border-color: var(--border); }
```

### Summary Table
```html
<table class="summary-table">
  <thead>
    <tr><th>Column 1</th><th>Column 2</th>...</tr>
  </thead>
  <tbody>
    <tr>
      <td style="color:var(--c1);font-weight:600">Row label</td>
      <td>Content</td>
      <td><code>monospace detail</code></td>
      <td class="status-pass">✓ Done</td>
    </tr>
  </tbody>
</table>
```

Table CSS: `border-collapse:collapse`, background on `th`, `border-bottom` on `td`, subtle `tr:hover`.

---

## Component Patterns

### Code Block with Syntax Highlighting

Use span classes for syntax colors — no external library needed. The classes (`.kw`, `.fn`,
`.str`, `.cm`, `.num`, `.op`) are defined in `base-dark.css`. Hand-apply these spans to code
in `.cb-body` elements. Tedious but produces perfect results without external dependencies.

### All Component CSS

The following components are fully implemented in `assets/base-dark.css` — use the class names
directly instead of writing CSS from scratch:

| Class | What it renders |
|---|---|
| `.hero-badge`, `.dot` | Status badge with green indicator dot |
| `.ltag` | Semantic category tag (set colors inline) |
| `.pill` | Small monospace inline badge |
| `.layer-id-badge` | Section header badge (set bg/color inline) |
| `.card`, `.card-title` | Content card with title |
| `.codeblock`, `.cb-head`, `.cb-body`, `.cb-dot` | Code block with traffic-light header |
| `.gate-item`, `.gi-pass`, `.gi-fail`, `.gi-note` | Pass/fail/note badges in gate sections |
| `.step-num` | Numbered step circle (set bg/color inline) |
| `.impl`, `.plan` | Status indicators (green / muted) |

---

## Chinese / CJK Typography

```css
:root {
  --font: system-ui, -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
body {
  line-height: 1.65;  /* wider than 1.5 for CJK readability */
}
```

- `PingFang SC` for macOS/iOS Chinese
- `Microsoft YaHei` for Windows Chinese
- CJK text needs `line-height: 1.6-1.8` (wider than Latin)
- Use `lang="zh"` on `<html>` for proper font selection
