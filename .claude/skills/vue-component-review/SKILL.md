---
name: vue-component-review
description: Analyze Vue 3 single-file components and produce a ranked, read-only report of performance, code-reuse and structure improvements, with file:line references and a concrete suggested fix for each. Use this skill whenever the user asks to review, audit, analyze, optimize, refactor-plan or "clean up" Vue components or the client code, asks why a Vue view feels slow or re-renders too much, asks what is duplicated across components, wants shared components or composables identified, or asks whether a .vue file is too big, even if they never say "review" or name this skill.
---

# Vue component review

Find the changes that would most improve a Vue 3 codebase's performance and reuse, and report them so the user can decide what to apply. This skill only reads and reports. It never edits files: the user picks which suggestions are worth the churn, and in this repo any `.vue` edit must go through the `vue-expert` agent anyway (see CLAUDE.md).

Why report-only: refactors that touch reactivity or shared components can change behavior in ways a static read can't prove. A ranked list with evidence lets the user approve the risky ones deliberately.

## 1. Pick the target

Use what the user named (a file, a folder, "the dashboard"). With no target, review `client/src`. If the target is a whole app, say so up front and expect to report only the highest-impact items.

## 2. Run the scan first

```bash
python3 -I .claude/skills/vue-component-review/scripts/scan_vue.py <path> [--min-files N]
```

It prints per-file sizes, mechanical signals (index or missing `v-for` keys, unguarded `Date` reads, hard-coded colours, emoji in templates, deep watchers, functions called many times from a template, mixed Options/Composition API) and cross-file duplication (same-named helpers, identical CSS rules). Use `--json` if you want to process it.

Why a script: counting and comparing across dozens of files is exactly where eyeballing goes wrong. The script gives exact, repeatable facts; your job is the judgment it cannot do.

Treat every signal as a lead, not a finding. The script cannot tell a static three-item list from a reorderable one, or a cheap formatter from an expensive filter.

## 3. Read before you claim

Open the flagged code before reporting it. A finding you did not verify is a guess presented as a fact, and the user will lose trust in the whole report after one wrong item. Specifically:

- For a duplication claim, read both copies. "Same name" is not "same behavior" (the scan labels identical vs different bodies; the different ones are often the interesting case, because the copies have drifted).
- For a performance claim, find what the code does per render or per change. Say what triggers the cost, not just that a pattern exists.
- For a keys claim, check whether the list can reorder, insert or delete. An index key on a static list is harmless and should be left out of the report.

`references/checks.md` has the full checklist with the reasoning behind each check and the usual fix. Read it when you are deciding whether something is a real problem or choosing a fix.

## 4. Rank by impact

Order findings by (user-visible benefit x how many places it helps) divided by risk and effort. A shared modal shell replacing seven copies outranks a single missing `v-show`. Correctness issues (missing or index keys on dynamic lists, unguarded date parsing) rank above pure tidiness because they cause bugs, not just clutter.

Cap the report at roughly ten findings. A long flat list gets skimmed and nothing gets done; anything beyond the top ten goes in a one-line "also noticed" tail.

## 5. Write the report

Use this structure so reports are comparable between runs:

```
# Vue component review: <target>

## Summary
<2-3 sentences: what was reviewed, the biggest theme, how many findings>

## Findings
### 1. <short title>  [Performance | Reuse | Structure | Conventions] · impact: high|medium|low · effort: S|M|L
- Where: `path/File.vue:123` (and other locations)
- What: <what the code does today, in one or two sentences>
- Why it matters: <the concrete cost or risk>
- Suggested fix: <specific: name the new component/composable/computed and what moves into it>
- Risk: <what could break, and how to check it>

(repeat, ranked)

## Also noticed
<one line each, low priority>

## Not worth changing
<signals you checked and deliberately dismissed, with the reason>
```

The "Not worth changing" section is deliberate: it shows the scan's leads were examined, and stops the next reviewer from re-raising them.

Report to the user in the conversation. Do not write the report into the repo unless asked: the repository is public, so a file there is public too.

## Rules that keep the report useful

- Suggest, with names. "Extract a `BaseModal.vue` holding the overlay, Escape/click-outside close and header; each modal keeps only its body" is actionable. "Consider reducing duplication" is not.
- Respect the project's conventions when proposing fixes: Composition API with `setup()`, unique keys, scoped styles, design tokens from `client/src/styles`, no emoji in UI. If CLAUDE.md files exist, read them; they override the generic advice here.
- Do not propose a change you could not justify with something visible in the code. No speculative micro-optimizations: a `computed` over ten rows is not a finding.
- If the user then wants fixes applied, hand `.vue` changes to the `vue-expert` agent and name the findings to apply.
