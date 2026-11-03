# Review checks

Each check says what to look for, why it matters, and the usual fix. The scan script surfaces leads for many of these; the judgment is yours.

Contents: Performance, Code reuse, Structure, Conventions

## Performance

**Derived data computed in a function called from the template.**
A function called in the template runs on every render of that component, and a computed property is cached until its inputs change. This only matters when the function does real work: filtering, sorting, grouping or reducing a collection (`getForecastsByTrend()` called twelve times, each filtering the whole list). Cheap pure formatters (`formatDate(x)`, `formatMoney(x)`) are idiomatic in templates and not worth reporting.
Fix: a `computed` that returns the derived structure once (for example a grouped object), and the template reads from it. Also check for `v-for` bodies that call a collection function per row, which multiplies the cost.

**Work repeated inside `v-for`.**
Anything that rebuilds an array or object per row (`.filter`, `.find`, `new Date`) turns O(n) into O(n x m). Fix: precompute a lookup map in a computed, or shape the data once when it loads.

**`v-if` on content that toggles often.**
`v-if` destroys and recreates the subtree; `v-show` keeps it and toggles CSS. Prefer `v-show` for frequently toggled, costly-to-build subtrees (charts, large tables), `v-if` for rarely shown or conditionally expensive ones. Only report when the toggle is demonstrably frequent (tabs, hover panels, sort toggles).

**Watchers that over-trigger.**
`deep: true` walks the whole object on every mutation; a watcher on several sources that reloads data can fire repeatedly from one user action. Fix: watch the specific field, or debounce when the watcher triggers a network call. Check that multiple filter changes in one tick do not cause multiple identical requests.

**Large reactive structures that never change.**
Big static arrays or lookup tables wrapped in `ref` or `reactive` pay for proxying they do not need. Fix: `shallowRef` or `markRaw`, or a plain module-level constant. Report only when the data is large (hundreds of items or more).

**Everything loaded up front.**
Heavy, rarely opened components (large modals, report views) imported statically are in the first bundle. Fix: `defineAsyncComponent` or a lazy route import. Report only for big components that most visits never reach.

**Event listeners and timers never removed.**
Document-level listeners and `setInterval` added in `onMounted` without an `onUnmounted` cleanup leak and stack up across navigations. This is a correctness bug as much as performance, so rank it high.

## Code reuse

**Repeated component shells.**
When several components share the same overlay, close button, Escape and click-outside handling, header and footer, that is one component with slots. The signal is the same `close()` body and the same overlay CSS in many files. Fix: a `BaseModal.vue` (slots for header, body and footer) plus, if needed, a small composable for the dismissal behaviour. State which parts differ so the extraction is realistic.

**Same-named helpers with different bodies.**
`formatDate`, `translateCategory`, `translatePriority` defined per component usually started as copies and drifted, so the same date shows differently on different screens. That is a consistency bug, not just duplication. Read the copies, say how they differ, and propose one implementation (in `utils/` for pure functions, in a composable when it needs i18n or shared state).

**Identical CSS rules across files.**
The same card, badge, table or info-grid rule in three or more components belongs in shared styles using the existing design tokens. Fix: move to the shared stylesheet or a shared component; do not just copy the rule once more.

**Repeated data-loading boilerplate.**
Several views with the same loading / error / reload-on-filter-change shape can share a composable (`useAsyncData(fetcher, deps)`). Report when the pattern is repeated three or more times and the copies are near-identical.

**Repeated markup patterns.**
Stat tiles, status badges and similar table cells repeated across views are candidates for small presentational components. Report only when the markup is genuinely the same, and say which props would vary.

## Structure

- **Oversized components.** The repo's guideline is to consider extraction when the template exceeds about 100 lines or the logic about 150. Size alone is not a finding. Say what the natural seams are (a chart, a table, a filter block, a modal) and what would move.
- **Mixed Options and Composition API** in one component makes the reactivity model harder to follow. Fix: convert the Options parts, or leave as is if the component is about to be rewritten.
- **Mutating props.** Assigning to a prop (or to a field of a prop object) hides data flow. Fix: emit an event and let the owner update, or copy into local state.
- **Logic that belongs in a composable.** Several `ref`s plus watchers plus handlers forming one feature (a dropdown, a form, a filter) are a composable waiting to be extracted, especially if two components already contain the same feature.
- **Prop drilling** through more than two levels for state used far below: consider a composable with shared state, as the repo already does for filters.

## Conventions (this repo)

These come from the project's CLAUDE.md files; re-read them if in doubt, since they win over this list.

- `v-for` needs a unique stable `:key`, not the index. An index key is only acceptable for a list that never reorders, inserts or deletes. Report dynamic lists only.
- Validate dates before `.getMonth()` and similar. An invalid string yields `NaN` and wrong buckets or a crash.
- No emoji in the UI. Colours and spacing come from the design tokens in `client/src/styles`; hard-coded hex values in components drift from the palette.
- Non-obvious logic gets a comment.
- Data loading shows loading and error states; check that the template handles both.
