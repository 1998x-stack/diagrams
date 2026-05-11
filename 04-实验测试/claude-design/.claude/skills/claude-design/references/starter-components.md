# Starter Components

Ready-made scaffolds for common design frames. Copy the component code you need into your project.

## Table of Contents
- [DesignCanvas](#designcanvas) — Side-by-side option grid
- [iOS Frame](#ios-frame) — iPhone bezel with status bar
- [Android Frame](#android-frame) — Android bezel with status bar
- [macOS Window](#macos-window) — Desktop window with traffic lights
- [Browser Window](#browser-window) — Browser chrome with tabs and address bar
- [Animation Stage](#animation-stage) — Timeline-based animation engine

---

## DesignCanvas

A grid layout with labeled cells for presenting 2+ static design options side-by-side. Use for purely
visual explorations (color, type, static layout).

```jsx
const DesignCanvas = ({ columns = 3, gap = 24, children, title }) => {
  const canvasStyles = {
    wrapper: {
      padding: 40, minHeight: '100vh',
      background: '#f5f5f5', fontFamily: 'system-ui',
    },
    title: {
      fontSize: 28, fontWeight: 700, marginBottom: 32,
      color: '#1a1a1a', textAlign: 'center',
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: `repeat(${columns}, 1fr)`,
      gap: gap, maxWidth: 1400, margin: '0 auto',
    },
  };

  return (
    <div style={canvasStyles.wrapper}>
      {title && <h1 style={canvasStyles.title}>{title}</h1>}
      <div style={canvasStyles.grid}>{children}</div>
    </div>
  );
};

const CanvasCell = ({ label, sublabel, children }) => {
  const cellStyles = {
    card: {
      background: '#fff', borderRadius: 12,
      overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    },
    content: { padding: 0 },
    footer: {
      padding: '12px 16px', borderTop: '1px solid #eee',
      fontSize: 13, color: '#666',
    },
    label: { fontWeight: 600, color: '#1a1a1a' },
    sublabel: { fontSize: 12, color: '#999', marginTop: 2 },
  };

  return (
    <div style={cellStyles.card}>
      <div style={cellStyles.content}>{children}</div>
      <div style={cellStyles.footer}>
        <div style={cellStyles.label}>{label}</div>
        {sublabel && <div style={cellStyles.sublabel}>{sublabel}</div>}
      </div>
    </div>
  );
};

Object.assign(window, { DesignCanvas, CanvasCell });
```

Usage:
```jsx
<DesignCanvas title="Button Variants" columns={3}>
  <CanvasCell label="Option A" sublabel="Rounded, filled">
    <div style={{ padding: 40, textAlign: 'center' }}>
      <button style={{ background: '#2563eb', color: '#fff', padding: '12px 24px',
                       borderRadius: 24, border: 'none' }}>Get Started</button>
    </div>
  </CanvasCell>
  <CanvasCell label="Option B" sublabel="Square, outlined">
    <div style={{ padding: 40, textAlign: 'center' }}>
      <button style={{ background: 'transparent', color: '#2563eb', padding: '12px 24px',
                       borderRadius: 4, border: '2px solid #2563eb' }}>Get Started</button>
    </div>
  </CanvasCell>
</DesignCanvas>
```

---

## iOS Frame

iPhone bezel with dynamic island, status bar, and home indicator.

```jsx
const IosFrame = ({ children, time = '9:41', dark = false }) => {
  const bg = dark ? '#000' : '#fff';
  const fg = dark ? '#fff' : '#000';

  const frameStyles = {
    device: {
      width: 393, height: 852, borderRadius: 47, overflow: 'hidden',
      background: bg, position: 'relative',
      boxShadow: '0 0 0 2px #1a1a1a, 0 20px 60px rgba(0,0,0,0.3)',
    },
    statusBar: {
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '16px 24px 0', height: 54, color: fg, fontSize: 15, fontWeight: 600,
    },
    dynamicIsland: {
      width: 126, height: 37, background: '#000', borderRadius: 20,
      position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
      zIndex: 10,
    },
    content: {
      position: 'absolute', top: 54, left: 0, right: 0, bottom: 34,
      overflow: 'auto',
    },
    homeIndicator: {
      position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)',
      width: 134, height: 5, background: fg, borderRadius: 3, opacity: 0.3,
    },
  };

  return (
    <div style={frameStyles.device}>
      <div style={frameStyles.dynamicIsland} />
      <div style={frameStyles.statusBar}>
        <span>{time}</span>
        <span style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ fontSize: 12 }}>5G</span>
          <span>100%</span>
        </span>
      </div>
      <div style={frameStyles.content}>{children}</div>
      <div style={frameStyles.homeIndicator} />
    </div>
  );
};

Object.assign(window, { IosFrame });
```

---

## Android Frame

Android device bezel with status bar and navigation bar.

```jsx
const AndroidFrame = ({ children, time = '12:00', dark = false }) => {
  const bg = dark ? '#121212' : '#fff';
  const fg = dark ? '#fff' : '#000';

  const frameStyles = {
    device: {
      width: 412, height: 892, borderRadius: 24, overflow: 'hidden',
      background: bg, position: 'relative',
      boxShadow: '0 0 0 2px #1a1a1a, 0 20px 60px rgba(0,0,0,0.3)',
    },
    statusBar: {
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '8px 16px', height: 36, color: fg, fontSize: 13,
    },
    content: {
      position: 'absolute', top: 36, left: 0, right: 0, bottom: 48,
      overflow: 'auto',
    },
    navBar: {
      position: 'absolute', bottom: 0, left: 0, right: 0, height: 48,
      display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 48,
    },
    navPill: {
      width: 72, height: 4, background: fg, borderRadius: 2, opacity: 0.5,
    },
  };

  return (
    <div style={frameStyles.device}>
      <div style={frameStyles.statusBar}>
        <span>{time}</span>
        <span style={{ display: 'flex', gap: 8, fontSize: 11 }}>
          <span>WiFi</span>
          <span>100%</span>
        </span>
      </div>
      <div style={frameStyles.content}>{children}</div>
      <div style={frameStyles.navBar}>
        <div style={frameStyles.navPill} />
      </div>
    </div>
  );
};

Object.assign(window, { AndroidFrame });
```

---

## macOS Window

Desktop window with traffic light buttons (close, minimize, maximize).

```jsx
const MacWindow = ({ children, title = 'Untitled', width = 800, height = 600 }) => {
  const windowStyles = {
    frame: {
      width, borderRadius: 10, overflow: 'hidden',
      boxShadow: '0 8px 40px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.1)',
      background: '#fff',
    },
    titleBar: {
      height: 38, background: '#f6f6f6', borderBottom: '1px solid #ddd',
      display: 'flex', alignItems: 'center', padding: '0 12px',
      position: 'relative',
    },
    trafficLights: {
      display: 'flex', gap: 8,
    },
    dot: (color) => ({
      width: 12, height: 12, borderRadius: '50%', background: color,
    }),
    titleText: {
      position: 'absolute', left: '50%', transform: 'translateX(-50%)',
      fontSize: 13, fontWeight: 500, color: '#4a4a4a',
    },
    content: {
      height: height - 38, overflow: 'auto',
    },
  };

  return (
    <div style={windowStyles.frame}>
      <div style={windowStyles.titleBar}>
        <div style={windowStyles.trafficLights}>
          <div style={windowStyles.dot('#ff5f57')} />
          <div style={windowStyles.dot('#ffbd2e')} />
          <div style={windowStyles.dot('#27c93f')} />
        </div>
        <span style={windowStyles.titleText}>{title}</span>
      </div>
      <div style={windowStyles.content}>{children}</div>
    </div>
  );
};

Object.assign(window, { MacWindow });
```

---

## Browser Window

Browser chrome with tab bar and address bar.

```jsx
const BrowserWindow = ({ children, url = 'https://example.com', title = 'Page', width = 900 }) => {
  const browserStyles = {
    frame: {
      width, borderRadius: 10, overflow: 'hidden',
      boxShadow: '0 8px 40px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.1)',
      background: '#fff',
    },
    tabBar: {
      height: 36, background: '#dee1e6', display: 'flex', alignItems: 'flex-end',
      padding: '0 8px', gap: 1,
    },
    tab: {
      height: 30, padding: '0 16px', background: '#fff', borderRadius: '8px 8px 0 0',
      display: 'flex', alignItems: 'center', fontSize: 12, color: '#333', maxWidth: 200,
    },
    addressBar: {
      height: 40, background: '#fff', borderBottom: '1px solid #ddd',
      display: 'flex', alignItems: 'center', padding: '0 12px', gap: 8,
    },
    urlInput: {
      flex: 1, height: 28, background: '#f1f3f4', borderRadius: 14,
      border: 'none', padding: '0 12px', fontSize: 13, color: '#333',
    },
    content: { overflow: 'auto' },
  };

  return (
    <div style={browserStyles.frame}>
      <div style={browserStyles.tabBar}>
        <div style={browserStyles.tab}>{title}</div>
      </div>
      <div style={browserStyles.addressBar}>
        <span style={{ fontSize: 16, color: '#999', cursor: 'pointer' }}>&larr;</span>
        <span style={{ fontSize: 16, color: '#999', cursor: 'pointer' }}>&rarr;</span>
        <span style={{ fontSize: 16, color: '#999', cursor: 'pointer' }}>&#8635;</span>
        <div style={browserStyles.urlInput}>{url}</div>
      </div>
      <div style={browserStyles.content}>{children}</div>
    </div>
  );
};

Object.assign(window, { BrowserWindow });
```

---

## Animation Stage

Timeline-based animation engine with scrubber, play/pause, and easing functions.

```jsx
const useTime = (duration = 5000, loop = true) => {
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(true);
  const startRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    if (!playing) return;
    startRef.current = performance.now() - time * duration;

    const tick = (now) => {
      const elapsed = now - startRef.current;
      let t = elapsed / duration;
      if (loop) t = t % 1;
      else t = Math.min(t, 1);
      setTime(t);
      if (t < 1 || loop) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [playing, duration, loop]);

  return { time, playing, setPlaying, setTime };
};

const Easing = {
  linear: t => t,
  easeIn: t => t * t,
  easeOut: t => t * (2 - t),
  easeInOut: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
  spring: t => 1 - Math.cos(t * Math.PI * 2) * Math.exp(-t * 5),
};

const interpolate = (t, from, to, easing = Easing.easeInOut) => {
  const e = easing(t);
  if (typeof from === 'number') return from + (to - from) * e;
  return from; // for non-numeric, just switch at t > 0.5
};

const Sprite = ({ children, start = 0, end = 1, time }) => {
  if (time < start || time > end) return null;
  const localTime = (time - start) / (end - start);
  return children(localTime);
};

const Stage = ({ children, width = 1920, height = 1080, duration = 5000 }) => {
  const { time, playing, setPlaying, setTime } = useTime(duration);

  const stageStyles = {
    wrapper: { width: '100vw', height: '100vh', background: '#000',
               display: 'flex', flexDirection: 'column', alignItems: 'center',
               justifyContent: 'center' },
    canvas: { width, height, position: 'relative', overflow: 'hidden',
              transformOrigin: 'center', background: '#fff' },
    scrubber: { position: 'fixed', bottom: 20, left: '50%', transform: 'translateX(-50%)',
                display: 'flex', gap: 12, alignItems: 'center', zIndex: 100 },
  };

  useEffect(() => {
    const scale = Math.min(window.innerWidth / width, window.innerHeight / (height + 80));
    document.querySelector('.anim-canvas').style.transform = `scale(${scale})`;
  }, []);

  return (
    <div style={stageStyles.wrapper}>
      <div className="anim-canvas" style={stageStyles.canvas}>
        {typeof children === 'function' ? children(time) : children}
      </div>
      <div style={stageStyles.scrubber}>
        <button onClick={() => setPlaying(!playing)}
          style={{ border: 'none', background: 'rgba(255,255,255,0.2)', color: '#fff',
                   width: 36, height: 36, borderRadius: '50%', cursor: 'pointer' }}>
          {playing ? '||' : '▶'}
        </button>
        <input type="range" min={0} max={1} step={0.001} value={time}
          onChange={e => { setPlaying(false); setTime(Number(e.target.value)); }}
          style={{ width: 300 }} />
        <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, fontFamily: 'monospace' }}>
          {(time * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  );
};

Object.assign(window, { Stage, Sprite, useTime, Easing, interpolate });
```

Usage:
```jsx
<Stage duration={4000}>
  {(time) => (
    <>
      <Sprite start={0} end={0.5} time={time}>
        {(t) => (
          <h1 style={{
            position: 'absolute', top: '40%', left: '50%',
            transform: `translate(-50%, -50%)`,
            opacity: Easing.easeOut(t),
            fontSize: interpolate(t, 48, 72, Easing.spring),
          }}>
            Hello World
          </h1>
        )}
      </Sprite>
    </>
  )}
</Stage>
```
