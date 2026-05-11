# Tweaks System

The Tweaks system adds in-page controls that let users adjust design parameters live — colors, fonts,
spacing, copy, layout variants, feature flags, whatever makes sense for the design.

## When to Use

- When the user asks for multiple variations of a single element within a larger design
- When exploring design dimensions (color palette, typography, density, layout)
- By default: always add a couple creative tweaks to expose interesting possibilities,
  even if the user didn't ask

## Implementation

### 1. Define Tweak Defaults

Place tweakable defaults in a clearly marked block in your HTML. Use JSON-valid syntax:

```html
<script>
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "primaryColor": "#2563eb",
  "fontSize": 16,
  "borderRadius": 8,
  "dark": false,
  "layout": "grid",
  "density": "comfortable"
}/*EDITMODE-END*/;
</script>
```

The block between `/*EDITMODE-BEGIN*/` and `/*EDITMODE-END*/` must be valid JSON (double-quoted keys
and strings). There should be exactly one such block in the root HTML file.

### 2. Build the Tweaks Panel

Design a compact floating panel (bottom-right corner is conventional). The panel should be:
- Visually distinct from the design being tweaked
- Small and non-intrusive
- Hidden by default (toggled via a button or keyboard shortcut)

```jsx
const TweaksPanel = ({ tweaks, onChange, visible }) => {
  if (!visible) return null;

  const panelStyles = {
    position: 'fixed', bottom: 20, right: 20,
    background: 'rgba(0,0,0,0.9)', color: '#fff',
    borderRadius: 12, padding: 20, width: 280,
    fontFamily: 'system-ui', fontSize: 13,
    zIndex: 9999, backdropFilter: 'blur(20px)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
  };

  return (
    <div style={panelStyles}>
      <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600 }}>Tweaks</h3>

      {/* Color picker */}
      <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        Primary Color
        <input type="color" value={tweaks.primaryColor}
          onChange={e => onChange({ primaryColor: e.target.value })} />
      </label>

      {/* Slider */}
      <label style={{ display: 'block', marginBottom: 12 }}>
        Font Size: {tweaks.fontSize}px
        <input type="range" min={12} max={24} value={tweaks.fontSize}
          onChange={e => onChange({ fontSize: Number(e.target.value) })}
          style={{ width: '100%' }} />
      </label>

      {/* Toggle */}
      <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        Dark Mode
        <input type="checkbox" checked={tweaks.dark}
          onChange={e => onChange({ dark: e.target.checked })} />
      </label>

      {/* Dropdown */}
      <label style={{ display: 'block', marginBottom: 12 }}>
        Layout
        <select value={tweaks.layout} onChange={e => onChange({ layout: e.target.value })}
          style={{ width: '100%', marginTop: 4 }}>
          <option value="grid">Grid</option>
          <option value="list">List</option>
          <option value="masonry">Masonry</option>
        </select>
      </label>
    </div>
  );
};
```

### 3. State Management

Use React state initialized from the defaults, and persist changes:

```jsx
const App = () => {
  const [tweaks, setTweaks] = useState({ ...TWEAK_DEFAULTS });
  const [showTweaks, setShowTweaks] = useState(false);

  const handleTweakChange = (updates) => {
    setTweaks(prev => {
      const next = { ...prev, ...updates };
      // Persist to localStorage
      localStorage.setItem('design-tweaks', JSON.stringify(next));
      return next;
    });
  };

  // Restore from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('design-tweaks');
    if (saved) setTweaks(JSON.parse(saved));
  }, []);

  // Toggle with keyboard shortcut
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 't' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setShowTweaks(prev => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <div>
      {/* Your design, using tweaks values */}
      <MyDesign {...tweaks} />

      {/* Toggle button */}
      <button onClick={() => setShowTweaks(!showTweaks)}
        style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 10000,
                 width: 40, height: 40, borderRadius: '50%', border: 'none',
                 background: '#2563eb', color: '#fff', cursor: 'pointer',
                 fontSize: 18, display: showTweaks ? 'none' : 'flex',
                 alignItems: 'center', justifyContent: 'center' }}>
        T
      </button>

      <TweaksPanel tweaks={tweaks} onChange={handleTweakChange} visible={showTweaks} />
    </div>
  );
};
```

## Design Tips

- Keep the tweaks surface small — a floating panel, not a sidebar
- Hide controls entirely when tweaks are off; the design should look final
- Group related tweaks (all color tweaks together, all spacing together)
- Use appropriate input types: color picker for colors, slider for numeric ranges, toggle for booleans
- Provide sensible defaults and ranges
- Label everything clearly — the user should understand what each tweak does at a glance
