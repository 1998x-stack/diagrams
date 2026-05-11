# Design Principles

## No Filler Content

Never pad a design with placeholder text, dummy sections, or informational material just to fill space.
Every element should earn its place. If a section feels empty, that's a design problem to solve with
layout and composition — not by inventing content.

Ask before adding material. If you think additional sections, pages, copy, or content would improve the
design, ask the user first. They know their audience and goals better than you.

## Avoid AI Slop Tropes

These patterns scream "AI-generated" and undermine design credibility:

| Pattern | Why It's Bad | Better Alternative |
|---|---|---|
| Gradient backgrounds | Overused, lacks intention | Solid colors from the brand palette |
| Emoji everywhere | Cheap, unprofessional (unless brand uses them) | Purposeful iconography or nothing |
| Left-border accent cards | Generic, cookie-cutter | Thoughtful card designs from the design system |
| SVG-drawn imagery | Always looks amateurish | Placeholder boxes labeled "image: [description]" |
| Overused fonts (Inter, Roboto, Arial, Fraunces, system-ui) | Generic, unmemorable | Distinctive type choices that reflect the brand |
| Rounded-corner containers with accent borders | Default AI aesthetic | Match the existing design system's card treatment |
| Unnecessary data/stats/numbers | "Data slop" — filler metrics | Only show data the user specifically needs |
| Aggressive iconography | Visual noise | Icons only when they genuinely aid comprehension |

## Color Usage

1. **Define ALL colors as CSS custom properties.** Every color in your artifact should be a
   `var(--name)`. A lone hardcoded `#hex` that appears once is a smell — it means you skipped
   the system step.
2. **Use brand colors first.** Pull from the design system or brand palette.
3. **Build color families.** When content has semantic categories (layers, phases, statuses),
   give each category three variants: main, dark (for badge backgrounds), and light (for fills).
   Use `rgba(main-color, 0.08)` for subtle backgrounds and `rgba(main-color, 0.35)` for borders.
4. **If palette is too restrictive**, use `oklch()` for harmonious extensions.
5. **Never invent colors from scratch** without anchoring them to existing brand values.

```css
:root {
  /* Surface hierarchy */
  --bg: #0d1117; --bg2: #161b22; --bg3: #21262d; --bg4: #2d333b;
  --border: rgba(255,255,255,0.08); --border2: rgba(255,255,255,0.18);
  --text: #e6edf3; --muted: #7d8590; --faint: #3d444d;

  /* Semantic color family example */
  --c1: #1D9E75;                                    /* main */
  --c1d: #0F6E56;                                   /* dark — badge backgrounds */
  --c1b: #E1F5EE;                                   /* light — light-theme fills */
  /* Use rgba for derived values:
     border: rgba(29,158,117,0.35)
     background: rgba(29,158,117,0.08) */
}
```

## Typography

- **Slides (1920x1080):** Never smaller than 24px. Headings should be significantly larger (48-120px).
- **Mobile mockups:** Hit targets never less than 44px.
- **Print documents:** 12pt minimum.
- Create a type system upfront: define scales for headings, body, captions, labels.
- Use `text-wrap: pretty` for better text wrapping.

## Create a Visual System

Before building, define your visual vocabulary in `:root` CSS variables:

1. **Surface hierarchy** — At least 4 background levels for depth (`--bg` through `--bg4`)
2. **Text hierarchy** — 3 levels: primary (`--text`), secondary (`--muted`), tertiary (`--faint`)
3. **Border hierarchy** — 2 levels: subtle (`--border`) and emphasized (`--border2`)
4. **Type scale** — Sizes for hero titles (42px+), section titles (28px), body (14-16px),
   labels (11-13px), code (11-13px monospace)
5. **Spacing scale** — Consistent values (4, 8, 12, 16, 20, 24, 32, 48, 64, 80)
6. **Component patterns** — Cards, badges, tags, code blocks, tables

Use this system to create **intentional variety and rhythm**:
- Different background colors for section starters
- Transition sections between major content sections (gradient background, gate items)
- Alternating grid layouts (2-col, 3-col) to avoid monotony
- Consistent spacing to create professional rhythm
- Sticky nav with `backdrop-filter: blur(12px)` and semi-transparent background

## Interaction Details

Small interaction details separate professional from amateur:

```css
/* Card hover — lift + border highlight */
.card { transition: border-color 0.2s, transform 0.15s, background 0.15s; }
.card:hover { border-color: var(--border2); background: var(--bg3); transform: translateY(-2px); }

/* Sticky nav with blur */
nav { position: sticky; top: 0; z-index: 100;
      background: rgba(13,17,23,0.94); backdrop-filter: blur(12px); }

/* Scroll fade-in */
@keyframes fadeUp { from { opacity:0; transform:translateY(16px) } to { opacity:1; transform:translateY(0) } }
.section { animation: fadeUp 0.4s ease both; }

/* Table row hover */
.table tr:hover td { background: rgba(255,255,255,0.015); }
```

## Advanced CSS

Surprise the user with what CSS can do:

```css
/* Perceptual color mixing */
color-mix(in oklch, var(--brand) 30%, white)

/* Text that wraps nicely */
text-wrap: pretty;
text-wrap: balance;

/* Fluid typography */
font-size: clamp(1rem, 2vw + 0.5rem, 2.5rem);

/* Subgrid for perfect alignment */
display: grid;
grid-template-columns: subgrid;

/* Container queries */
@container (min-width: 600px) { ... }

/* View transitions */
view-transition-name: hero;

/* Scroll-driven animations */
animation-timeline: view();

/* Custom properties with @property for typed values */
@property --angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}
```

## Placeholders Over Bad Attempts

If you don't have an icon, asset, or component — draw a placeholder. In hi-fi design, a clearly labeled
placeholder is better than a bad attempt at the real thing.

```jsx
const Placeholder = ({ width, height, label }) => (
  <div style={{
    width, height, background: '#f0f0f0', border: '2px dashed #ccc',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    borderRadius: 8, color: '#999', fontSize: 13, fontFamily: 'system-ui',
  }}>
    {label || `${width}x${height}`}
  </div>
);
```

## Don't Use scrollIntoView

It can mess up the web app. Use other DOM scroll methods if scrolling is needed:

```js
// Instead of element.scrollIntoView()
container.scrollTop = element.offsetTop - container.offsetTop;
// or
container.scrollTo({ top: targetPosition, behavior: 'smooth' });
```

## Design from Context, Not from Scratch

Good hi-fi designs are rooted in existing design context. Always try to acquire:
- Theme/color tokens (theme.ts, colors.ts, tokens.css)
- Existing components
- Global stylesheets and layout scaffolds
- Screenshots of existing UI

Mocking a full product from scratch is a last resort. Ask the user for reference materials if you
can't find them.

When adding to an existing UI, study the visual vocabulary first: copywriting style, color palette,
tone, hover/click states, animation styles, shadow + card + layout patterns, density. Match them.

## Page Structure for Long-Form Content

Effective long-form technical content follows a rhythm:

```
NAV (sticky, blur backdrop)
└── HERO (badge, title with gradient keyword, subtitle, tag row)
└── FLOW OVERVIEW (horizontal process boxes with arrow connectors)
└── SECTION 1 (badge+title, definition, card grid, code block)
    └── TRANSITION (pill label, title, description, gate items)
└── SECTION 2 (same pattern)
    └── TRANSITION
└── ...
└── SUMMARY (comparison table, footer)
```

The repeating section+transition pattern creates a reading rhythm. The reader always knows where
they are and what comes next. Transition sections explicitly explain the relationship between
adjacent content sections, which is far better than just stacking sections and hoping the reader
connects the dots.

## Max Width and Padding

```css
.page { max-width: 1160px; margin: 0 auto; padding: 0 40px; }
```

Content should never stretch to full viewport width — constrain it. 1060-1200px is the sweet spot
for readability. 40px side padding prevents content from touching viewport edges on tablet.
