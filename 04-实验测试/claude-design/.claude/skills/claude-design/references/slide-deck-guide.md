# Slide Deck Guide

## Architecture

Every slide deck uses a fixed-size canvas (default 1920x1080, 16:9) wrapped in a full-viewport stage
that letterboxes via `transform: scale()`. Navigation controls live OUTSIDE the scaled element so they
remain usable on small screens.

## Using the DeckStage Asset

Copy `assets/deck-stage.js` into your project. It's a self-contained web component that handles:
- Auto-scaling to fit any viewport with letterboxing
- Keyboard navigation (arrow keys, space)
- Touch/swipe navigation
- Slide count overlay
- localStorage persistence of current slide position
- `data-screen-label` attributes on each slide for comment context
- `noscale` attribute support for export workflows
- Posts `slideIndexChanged` message for speaker notes sync

Do NOT re-implement this from scratch — always use the asset file.

### Usage

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Presentation</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { width: 100%; height: 100%; overflow: hidden; background: #000; }
  </style>
</head>
<body>
  <script src="deck-stage.js"></script>

  <deck-stage>
    <section data-screen-label="01 Title">
      <!-- Slide 1 content -->
    </section>
    <section data-screen-label="02 Agenda">
      <!-- Slide 2 content -->
    </section>
    <section data-screen-label="03 Key Points">
      <!-- Slide 3 content -->
    </section>
  </deck-stage>
</body>
</html>
```

### Programmatic API

```js
const deck = document.querySelector('deck-stage');
deck.goToSlide(2);        // jump to slide 3 (0-indexed internally)
deck.next();              // advance one slide
deck.prev();              // go back one slide
deck.currentSlide;        // get current index
deck.slideCount;          // total number of slides
```

## Slide Numbering

Slide numbers are **1-indexed**. Use labels like "01 Title", "02 Agenda" matching the slide counter
the user sees. When a user says "slide 5", they mean the 5th slide (label "05"), never array index [4].

## Speaker Notes

Only add speaker notes when the user explicitly asks. When using them, put less text on slides and
focus on impactful visuals. Speaker notes should be full scripts in conversational language.

```html
<script type="application/json" id="speaker-notes">
[
  "Welcome everyone. Today we're going to talk about...",
  "Let me walk you through the agenda for today's session...",
  "This is our first key point. Notice how..."
]
</script>
```

The DeckStage component automatically posts `{ slideIndexChanged: N }` on every navigation,
which syncs speaker notes in environments that support them.

## Design Tips for Slides

- Text never smaller than 24px on a 1920x1080 canvas
- Use 1-2 background colors max across the deck
- Create a type system upfront: section headers, titles, body text, captions
- Use different background colors for section starters
- Use full-bleed image layouts when imagery is central
- On text-heavy slides, commit to adding imagery or meaningful placeholders
- Build intentional visual variety and rhythm across the deck
