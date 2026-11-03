---
name: saas-sidebar-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a vertical left sidebar instead of a top nav bar, a consistent spacing scale, and a polished professional look. Use this skill whenever the user wants to restyle, modernize, polish or "make it look professional" in a Vue 3 app, move navigation from a top bar to a sidebar, add a dashboard shell or app layout, or introduce design tokens and consistent spacing, even if they never say "SaaS" or "sidebar".
---

# SaaS sidebar redesign for Vue 3

Turn an existing Vue 3 app into a modern SaaS-style interface: a fixed left sidebar for navigation, a content area with a consistent page structure, and one shared set of design tokens. The goal is a visual and layout change only. The app must behave exactly as before.

Why this matters: a redesign that quietly breaks routes, filters or translations costs more than it gains. Treat behavior as frozen and only touch markup and CSS.

## 1. Audit before changing anything

Read these so the redesign fits the app instead of fighting it:

- The router file (usually `main.js` or `router/index.js`): the list of routes is the sidebar's item list.
- The root layout (`App.vue`): the current top nav, and everything else living in the header (filters, language switcher, profile menu, notifications). Each of those must be relocated, never dropped.
- Global styles and any existing tokens (CSS custom properties, colour palette, fonts).
- Two or three representative views to learn the page patterns: headers, cards, tables, stat tiles, forms, modals, badges.
- Project instructions (`CLAUDE.md`, etc.). Project rules override this skill's defaults: if the project fixes a palette, forbids emojis, requires CSS-only charts or requires a specific subagent for `.vue` files, follow that. When the project defines colours, map them onto the tokens below instead of inventing new ones.
- Whether the app uses i18n (`t('...')`). If so, every new label goes through it, in every locale file.

Summarize the audit in a few lines and state the plan before editing.

## 2. Establish design tokens

Create one global stylesheet of CSS custom properties (see `references/tokens-and-layout.md` for a starter) and import it once from the entry file. All spacing, colour, radius, shadow and type sizes in the redesign come from these tokens. Consistency comes from having one scale: pick spacing from the 4px-based scale and avoid one-off pixel values.

Stick to plain CSS variables and scoped CSS. Do not add Tailwind or a component library unless the user asks.

## 3. Build the shell

Replace the top nav with a two-column layout: sidebar plus main content. The details and a template are in `references/tokens-and-layout.md`. In short:

- Sidebar about 240px wide, full height, fixed, with the brand at the top, nav items in the middle (grouped if there are many), and the utilities (language, profile, anything moved out of the old header) at the bottom.
- Nav items are `<router-link>`s with an inline SVG icon and a label. Active state is clear (tinted background plus stronger text), and `aria-current="page"` is set. No icon library; hand-written inline SVG keeps the dependency list unchanged.
- Main area has a page header (title, optional description, actions), then content in a max-width container with consistent padding.
- Controls that applied to the whole app (global filters) go in a slim toolbar under the page header, not the sidebar, because they act on page content.
- Below about 768px the sidebar becomes an off-canvas drawer opened by a menu button, with a backdrop, closing on route change and on Escape.

## 4. Migrate the pages

Apply one shared vocabulary to every view so pages feel like one product:

- Page header: title, subtitle, actions area.
- Card: surface, 1px border, radius from tokens, section title, consistent inner padding.
- Stat tile, table (header row, row hover, right-aligned numbers, comfortable row height), badge (status colours), buttons (primary, secondary, ghost, disabled and focus states), form controls.
- Empty, loading and error states share the same look.

Put shared patterns in the global stylesheet or a small number of shared components rather than copying CSS into every view. Convert views one at a time, keep each view's script untouched, and keep existing class names where views or tests depend on them.

## 5. Polish checklist

- Spacing only from the scale; gaps between cards and sections identical across pages.
- One type scale; titles, section titles, body and captions are visibly distinct.
- Colour: neutral surfaces, one accent, status colours reserved for status. Text meets contrast requirements.
- Visible `:focus-visible` rings, keyboard-reachable nav, real `<nav>` and `<main>` landmarks.
- Subtle transitions (150ms) on hover and active states; none on layout.
- Check the widest table and the longest label for overflow.

## 6. Verify

1. Run the build (`npm run build`) and fix errors.
2. Load every route and confirm it renders inside the new shell with no console errors.
3. Confirm behavior is unchanged: filters still drive data, language switching works, modals open, links navigate.
4. Check desktop width and a narrow width (about 390px), including the drawer.
5. If browser automation is available, take screenshots of each route; otherwise ask the user to look and say which routes you could not check.

Report what changed, which files, and anything you could not verify. Do not commit unless asked.

## What not to do

- Do not change routes, API calls, data logic, store state or translation keys other than adding new labels.
- Do not delete header features (filters, language, profile); relocate them.
- Do not introduce a new dependency to get a look that plain CSS can deliver.
- Do not restyle only the shell and leave pages in the old look; the pages are where the polish is visible.
