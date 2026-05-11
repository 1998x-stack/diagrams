/**
 * deck-stage.js — Slide deck web component.
 *
 * Usage:
 *   <script src="deck-stage.js"></script>
 *   <deck-stage>
 *     <section data-screen-label="01 Title">...</section>
 *     <section data-screen-label="02 Agenda">...</section>
 *   </deck-stage>
 *
 * Features:
 *   - Auto-scales 1920x1080 canvas to fit any viewport (letterboxing)
 *   - Keyboard navigation (arrows, space)
 *   - Touch swipe navigation
 *   - Slide counter overlay
 *   - localStorage persistence of current slide
 *   - Posts slideIndexChanged message for speaker notes sync
 *   - Supports `noscale` attribute to disable scaling (for PPTX export)
 */
class DeckStage extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._current = 0;
    this._slides = [];
    this._key = 'deck-slide-' + (this.id || location.pathname);
  }

  connectedCallback() {
    this._slides = Array.from(this.querySelectorAll(':scope > section'));
    const saved = localStorage.getItem(this._key);
    if (saved !== null) {
      this._current = Math.min(parseInt(saved, 10), this._slides.length - 1);
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: flex; align-items: center; justify-content: center;
          width: 100vw; height: 100vh; background: #000;
          overflow: hidden; position: relative;
        }
        :host([noscale]) .stage { transform: none !important; }
        .stage {
          width: 1920px; height: 1080px; position: relative;
          overflow: hidden; transform-origin: center center;
          background: #fff;
        }
        ::slotted(section) {
          position: absolute; inset: 0;
          display: none; width: 1920px; height: 1080px; overflow: hidden;
        }
        ::slotted(section.active) {
          display: flex; flex-direction: column;
        }
        .controls {
          position: absolute; bottom: 20px; left: 50%;
          transform: translateX(-50%);
          display: flex; gap: 12px; z-index: 100;
        }
        .controls button {
          width: 48px; height: 48px; border-radius: 50%; border: none;
          background: rgba(255,255,255,0.15); color: #fff;
          font-size: 20px; cursor: pointer;
          backdrop-filter: blur(8px); transition: background 0.2s;
        }
        .controls button:hover { background: rgba(255,255,255,0.3); }
        .counter {
          position: absolute; bottom: 24px; right: 24px;
          color: rgba(255,255,255,0.5);
          font: 14px/1 system-ui; z-index: 100;
        }
      </style>
      <div class="stage"><slot></slot></div>
      <div class="controls">
        <button class="prev" aria-label="Previous slide">←</button>
        <button class="next" aria-label="Next slide">→</button>
      </div>
      <div class="counter"></div>
    `;

    this._stage = this.shadowRoot.querySelector('.stage');
    this._counter = this.shadowRoot.querySelector('.counter');

    this.shadowRoot.querySelector('.prev').addEventListener('click', () => this.prev());
    this.shadowRoot.querySelector('.next').addEventListener('click', () => this.next());

    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); this.next(); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); this.prev(); }
    });

    let touchStartX = 0;
    this.addEventListener('touchstart', (e) => { touchStartX = e.touches[0].clientX; });
    this.addEventListener('touchend', (e) => {
      const dx = e.changedTouches[0].clientX - touchStartX;
      if (Math.abs(dx) > 50) { dx < 0 ? this.next() : this.prev(); }
    });

    this._resize();
    window.addEventListener('resize', () => this._resize());
    this._goTo(this._current);
  }

  _resize() {
    if (this.hasAttribute('noscale')) return;
    const sx = window.innerWidth / 1920;
    const sy = window.innerHeight / 1080;
    this._stage.style.transform = `scale(${Math.min(sx, sy)})`;
  }

  _goTo(i) {
    this._current = Math.max(0, Math.min(i, this._slides.length - 1));
    this._slides.forEach((s, idx) => s.classList.toggle('active', idx === this._current));
    this._counter.textContent = `${this._current + 1} / ${this._slides.length}`;
    localStorage.setItem(this._key, this._current);
    window.parent.postMessage({ slideIndexChanged: this._current }, '*');
  }

  next() { this._goTo(this._current + 1); }
  prev() { this._goTo(this._current - 1); }
  goToSlide(i) { this._goTo(i); }
  get currentSlide() { return this._current; }
  get slideCount() { return this._slides.length; }
}

customElements.define('deck-stage', DeckStage);
