# React + Babel Setup for HTML Artifacts

## Required Script Tags

Always use these exact pinned versions with integrity hashes. Never use unpinned versions like `react@18`.

```html
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js"
  integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L"
  crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"
  integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm"
  crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js"
  integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y"
  crossorigin="anonymous"></script>
```

## Loading Component Files

Import component scripts with standard `<script>` tags. Do NOT use `type="module"` — it breaks things.

```html
<!-- Load component files -->
<script type="text/babel" src="components.jsx"></script>
<script type="text/babel" src="sections.jsx"></script>

<!-- Main app script (loaded last) -->
<script type="text/babel">
  const { useState } = React;
  // ... your app code using components from above files
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(<App />);
</script>
```

## Critical: Style Object Naming

Each Babel script file gets its own scope. If multiple files define `const styles = { ... }`, they
collide when exported to window scope. Always use component-specific names:

```jsx
// BAD - will break when multiple files use this
const styles = { container: { padding: 20 } };

// GOOD - unique per component
const headerStyles = { container: { padding: 20 } };
const cardStyles = { container: { padding: 16 } };
```

This is non-negotiable — style name collisions cause silent breakages that are hard to debug.

## Critical: Sharing Components Between Files

Each `<script type="text/babel">` gets its own scope. To share components between files,
export them to `window` at the end of each component file:

```jsx
// components.jsx
const Button = ({ children, onClick, variant = 'primary' }) => {
  const buttonStyles = {
    primary: { background: '#2563eb', color: 'white' },
    secondary: { background: '#e5e7eb', color: '#1f2937' },
  };
  return (
    <button onClick={onClick} style={{ ...baseStyle, ...buttonStyles[variant] }}>
      {children}
    </button>
  );
};

const Card = ({ children, title }) => (
  <div style={cardStyles.wrapper}>
    {title && <h3 style={cardStyles.title}>{title}</h3>}
    {children}
  </div>
);

// Export to window so other scripts can use them
Object.assign(window, { Button, Card });
```

Then in your main script or other files, these are available as globals:

```jsx
// main app script
const App = () => (
  <div>
    <Card title="Welcome">
      <Button onClick={() => alert('clicked')}>Click me</Button>
    </Card>
  </div>
);
```

## Minimal HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Design</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Your-Font', sans-serif; }
    #root { min-height: 100vh; }
  </style>
</head>
<body>
  <div id="root"></div>

  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js"
    integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L"
    crossorigin="anonymous"></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"
    integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm"
    crossorigin="anonymous"></script>
  <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js"
    integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y"
    crossorigin="anonymous"></script>

  <!-- Component files -->
  <script type="text/babel" src="components.jsx"></script>

  <!-- Main app -->
  <script type="text/babel">
    const { useState, useEffect, useRef } = React;

    const App = () => {
      return (
        <div style={{ minHeight: '100vh' }}>
          {/* Your design here */}
        </div>
      );
    };

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
```
