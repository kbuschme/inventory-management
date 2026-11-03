# Tokens and layout starter

Starting points to adapt, not to paste blindly. If the project already has a palette, map its colours onto these variable names instead of replacing them.

## Contents
- Design tokens
- App shell template
- Sidebar and layout CSS
- Shared page patterns

## Design tokens

```css
:root {
  /* Spacing: 4px base. Use only these. */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;

  /* Neutrals (slate). Swap for the project palette if one exists. */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-muted: #64748b;

  /* One accent, plus status colours reserved for status. */
  --color-accent: #2563eb;
  --color-accent-soft: #eff6ff;
  --color-success: #16a34a;
  --color-warning: #ca8a04;
  --color-danger: #dc2626;

  /* Sidebar */
  --sidebar-width: 240px;
  --sidebar-bg: #0f172a;
  --sidebar-text: #cbd5e1;
  --sidebar-text-active: #ffffff;
  --sidebar-item-active-bg: rgba(255, 255, 255, 0.08);

  /* Shape and depth */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  /* Type scale */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --text-xs: 12px;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 20px;
  --text-xl: 24px;

  --transition: 150ms ease;
}
```

## App shell template

Adapt the nav items from the router, and move any old header utilities into `sidebar-footer` or the toolbar.

```vue
<template>
  <div class="app-shell">
    <button class="menu-button" aria-label="Open navigation" @click="navOpen = true">
      <!-- inline SVG menu icon -->
    </button>

    <div v-if="navOpen" class="sidebar-backdrop" @click="navOpen = false"></div>

    <aside class="sidebar" :class="{ open: navOpen }">
      <div class="sidebar-brand">App name</div>
      <nav class="sidebar-nav" aria-label="Main">
        <router-link v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item">
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><!-- path --></svg>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <!-- language switcher, profile menu, etc. moved from the old header -->
      </div>
    </aside>

    <main class="main">
      <!-- global filters toolbar, if any -->
      <div class="content"><router-view /></div>
    </main>
  </div>
</template>
```

`router-link` adds `router-link-exact-active` and `aria-current="page"` automatically, so style `.nav-item.router-link-exact-active` for the active state. Close the drawer in a route watcher (`watch(() => route.path, ...)`) and on `keydown.esc`.

## Sidebar and layout CSS

```css
.app-shell { min-height: 100vh; background: var(--color-bg); color: var(--color-text); font-family: var(--font-sans); }

.sidebar {
  position: fixed; inset: 0 auto 0 0; width: var(--sidebar-width);
  display: flex; flex-direction: column;
  background: var(--sidebar-bg); color: var(--sidebar-text);
  padding: var(--space-4); gap: var(--space-4); z-index: 40;
}
.sidebar-brand { font-size: var(--text-base); font-weight: 600; color: var(--sidebar-text-active); padding: var(--space-2) var(--space-3); }
.sidebar-nav { display: flex; flex-direction: column; gap: var(--space-1); flex: 1; overflow-y: auto; }
.nav-item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm);
  color: var(--sidebar-text); text-decoration: none; font-size: var(--text-sm);
  transition: background var(--transition), color var(--transition);
}
.nav-item:hover { background: var(--sidebar-item-active-bg); color: var(--sidebar-text-active); }
.nav-item.router-link-exact-active { background: var(--sidebar-item-active-bg); color: var(--sidebar-text-active); font-weight: 600; }
.nav-item:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
.nav-icon { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; }

.main { margin-left: var(--sidebar-width); min-width: 0; }
.content { max-width: 1280px; padding: var(--space-6); margin: 0 auto; }

.menu-button, .sidebar-backdrop { display: none; }

@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); transition: transform var(--transition); }
  .sidebar.open { transform: translateX(0); }
  .sidebar-backdrop { display: block; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5); z-index: 30; }
  .menu-button { display: inline-flex; position: fixed; top: var(--space-3); left: var(--space-3); z-index: 20; }
  .main { margin-left: 0; }
  .content { padding: var(--space-5) var(--space-4); padding-top: var(--space-7); }
}
```

`min-width: 0` on `.main` stops wide tables from stretching the page; let tables scroll inside their own container.

## Shared page patterns

Define these once globally and reuse them in every view:

- `.page-header`: flex row, title (`--text-xl`, 600) with muted subtitle (`--text-sm`), actions right-aligned, `margin-bottom: var(--space-5)`.
- `.card`: `background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-5); box-shadow: var(--shadow-sm);`, with `margin-bottom: var(--space-5)`.
- `.stat-grid`: `display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--space-4);`.
- Tables: header row in `--color-text-muted`, `--text-xs`, uppercase; cells `padding: var(--space-3) var(--space-4)`; 1px row dividers; numbers right-aligned.
- `.badge`: pill, `--text-xs`, soft tinted background with matching text for success, warning, danger and info.
- Buttons: primary (accent fill), secondary (border), ghost; all `--radius-sm`, `--text-sm`, `padding: var(--space-2) var(--space-4)`, `:disabled` at reduced opacity, `:focus-visible` ring.
