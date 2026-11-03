#!/usr/bin/env python3
"""Scan Vue single-file components for mechanical review signals.

Usage: python scan_vue.py [PATH ...] [--json] [--min-files N]

PATH is a .vue file or a directory (default: client/src). Output is a list of
*signals*, not verdicts: each one needs a human-style judgment (a static list
can legitimately use an index key; a helper may be duplicated on purpose). The
script exists so the counting and cross-file comparison are exact, which is
tedious and error-prone to do by eye across dozens of files.

Standard library only.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# CLAUDE.md thresholds for "extract a component / composable".
TEMPLATE_LIMIT = 100
SCRIPT_LIMIT = 150

EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-⛿✅❌⭐]")
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
DATE_CALL_RE = re.compile(r"\.(getMonth|getFullYear|getDate|getDay)\(\)")
FUNC_DEF_RE = re.compile(
    r"^\s*(?:const\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>|(?:async\s+)?function\s+(\w+)\s*\()"
)
# Names that are framework/i18n plumbing, not component logic.
IGNORED_TEMPLATE_CALLS = {"t", "$t", "emit", "$emit"}


def block_ranges(lines):
    """Return {block: (first_line, last_line)} (0-based, content only).

    SFC blocks start at column 0, so a line-based scan is enough and, unlike a
    regex over the whole file, is not confused by nested <template v-slot> tags.
    """
    ranges = {}
    i = 0
    while i < len(lines):
        m = re.match(r"<(template|script|style)\b[^>]*>\s*$", lines[i])
        if m:
            name, start = m.group(1), i + 1
            j = start
            while j < len(lines) and not lines[j].startswith(f"</{name}>"):
                j += 1
            ranges.setdefault(name, (start, j))
            i = j
        i += 1
    return ranges


def balanced_body(lines, start_idx):
    """Text of the first {...} block at or after start_idx (brace matching)."""
    depth, out, started = 0, [], False
    for line in lines[start_idx:]:
        for ch in line:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                depth -= 1
        if started:
            out.append(line)
            if depth <= 0:
                break
    return "\n".join(out)


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def opening_tag(lines, idx, limit=8):
    """Opening tag text for the element whose attribute is on line idx (may span lines)."""
    k = idx
    while k > 0 and "<" not in lines[k]:
        k -= 1
    return " ".join(lines[k : min(k + limit, len(lines))]).split(">")[0] if k <= idx else lines[idx]


def scan_file(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    ranges = block_ranges(lines)
    findings = []  # (category, line_no (1-based), message)

    def span(name):
        a, b = ranges.get(name, (0, 0))
        return a, b

    t0, t1 = span("template")
    s0, s1 = span("script")
    y0, y1 = span("style")
    sizes = {"template": t1 - t0, "script": s1 - s0, "style": y1 - y0, "total": len(lines)}

    if sizes["template"] > TEMPLATE_LIMIT:
        findings.append(("structure", t0 + 1, f"template is {sizes['template']} lines (guideline: split above {TEMPLATE_LIMIT})"))
    if sizes["script"] > SCRIPT_LIMIT:
        findings.append(("structure", s0 + 1, f"script is {sizes['script']} lines (guideline: extract above {SCRIPT_LIMIT})"))

    # --- v-for keys -------------------------------------------------------
    for i in range(t0, t1):
        m = re.search(r'v-for="([^"]+)"', lines[i])
        if not m:
            continue
        expr = m.group(1)
        parts = re.match(r"\(?\s*(\w+)\s*(?:,\s*(\w+))?\s*\)?\s+(?:in|of)\s+(.+)", expr)
        index_var = parts.group(2) if parts else None
        tag = opening_tag(lines, i)
        key = re.search(r'(?::|v-bind:)key="([^"]+)"', tag)
        if not key:
            # <template v-for> carries its key on children; only flag real elements.
            if not re.search(r"<template\b", tag):
                findings.append(("keys", i + 1, f"v-for without :key  ({expr})"))
        elif index_var and key.group(1).strip() == index_var:
            findings.append(("keys", i + 1, f"v-for keyed by index '{index_var}'  ({expr})"))

    # --- unguarded Date reads ---------------------------------------------
    for i in range(s0, s1):
        m = DATE_CALL_RE.search(lines[i])
        if m:
            window = "\n".join(lines[max(s0, i - 8) : i + 1])
            if "isNaN" not in window and "isValid" not in window:
                findings.append(("dates", i + 1, f".{m.group(1)}() with no isNaN/validity check in the 8 lines above"))

    # --- hard-coded colours (style block + inline) --------------------------
    hex_lines = []
    for i in list(range(y0, y1)) + list(range(t0, t1)):
        line = lines[i]
        if HEX_RE.search(line) and not re.match(r"\s*--[\w-]+\s*:", line) and "var(" not in line:
            hex_lines.append(i + 1)
    if hex_lines:
        shown = ", ".join(map(str, hex_lines[:6])) + (" ..." if len(hex_lines) > 6 else "")
        findings.append(("tokens", hex_lines[0], f"{len(hex_lines)} hard-coded hex colour line(s): {shown}"))

    # --- emoji in UI --------------------------------------------------------
    for i in range(t0, t1):
        if EMOJI_RE.search(lines[i]):
            findings.append(("conventions", i + 1, "emoji in template (project rule: no emojis in UI)"))

    # --- Options/Composition mixing ----------------------------------------
    script_text = "\n".join(lines[s0:s1])
    if re.search(r"\bsetup\s*\(", script_text) and re.search(r"^\s*(data\s*\(|methods\s*:|computed\s*:\s*\{)", script_text, re.M):
        findings.append(("structure", s0 + 1, "mixes setup() with Options API (data/methods/computed)"))

    # --- deep watchers -------------------------------------------------------
    for i in range(s0, s1):
        if re.search(r"deep\s*:\s*true", lines[i]):
            findings.append(("performance", i + 1, "deep watcher: traverses the whole object on every mutation"))

    # --- script functions + how often the template calls them -----------------
    funcs = {}
    for i in range(s0, s1):
        m = FUNC_DEF_RE.match(lines[i])
        if m:
            name = m.group(1) or m.group(2)
            funcs[name] = (i + 1, norm(balanced_body(lines, i)))
    # Only calls that run during render matter. Event handlers (@click="fn(x)") run
    # once per event, so strip them or every click handler looks like a render cost.
    template_text = re.sub(r'(?:@|v-on:)[\w:.-]+="[^"]*"', "", "\n".join(lines[t0:t1]))
    for name, (ln, _) in funcs.items():
        if name in IGNORED_TEMPLATE_CALLS:
            continue
        calls = len(re.findall(rf"(?<![\w.$]){re.escape(name)}\(", template_text))
        if calls >= 3:
            findings.append(("performance", ln, f"'{name}()' is called {calls}x in the template; it re-runs on every render (candidate for computed or precomputed data)"))

    # --- style rules, for cross-file duplication -------------------------------
    rules = {}
    style_text = "\n".join(lines[y0:y1])
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", style_text):
        decls = sorted(d.strip() for d in body.split(";") if d.strip())
        if len(decls) >= 3:  # tiny rules are coincidence, not duplication
            rules[norm(sel)] = ";".join(decls)

    return {
        "path": str(path),
        "sizes": sizes,
        "findings": findings,
        "funcs": {k: v for k, v in funcs.items()},
        "rules": rules,
    }


def cross_file(results, min_files):
    """Duplicated helper functions and identical CSS rules across files."""
    out = []
    by_func = defaultdict(list)
    for r in results:
        for name, (ln, body) in r["funcs"].items():
            by_func[name].append((r["path"], ln, body))
    for name, occ in sorted(by_func.items()):
        if len(occ) >= 2:
            identical = len({b for _, _, b in occ}) == 1
            where = ", ".join(f"{p}:{ln}" for p, ln, _ in occ)
            kind = "identical body" if identical else "same name, different bodies"
            out.append(("reuse", f"function '{name}' defined in {len(occ)} files ({kind}): {where}"))

    by_rule = defaultdict(list)
    for r in results:
        for sel, body in r["rules"].items():
            by_rule[(sel, body)].append(r["path"])
    for (sel, _), paths in sorted(by_rule.items(), key=lambda kv: -len(kv[1])):
        if len(paths) >= min_files:
            out.append(("reuse", f"identical CSS rule '{sel}' in {len(paths)} files: {', '.join(paths)}"))
    return out


def collect(paths):
    files = []
    for p in paths:
        p = Path(p)
        if not p.exists():
            sys.exit(f"Path not found: {p}")
        files +=sorted(p.rglob("*.vue")) if p.is_dir() else [p]
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", default=["client/src"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-files", type=int, default=3, help="report identical CSS rules found in at least N files")
    args = ap.parse_args()

    files = collect(args.paths)
    if not files:
        sys.exit("No .vue files found under: " + ", ".join(args.paths))
    results = [scan_file(f) for f in files]
    shared = cross_file(results, args.min_files)

    if args.json:
        slim = [{k: v for k, v in r.items() if k not in ("funcs", "rules")} for r in results]
        print(json.dumps({"files": slim, "cross_file": shared}, indent=2))
        return

    print(f"Scanned {len(results)} .vue file(s)\n")
    print(f"{'file':<52} {'tmpl':>5} {'script':>6} {'style':>5}  signals")
    for r in sorted(results, key=lambda r: -r["sizes"]["total"]):
        s = r["sizes"]
        print(f"{r['path']:<52} {s['template']:>5} {s['script']:>6} {s['style']:>5}  {len(r['findings'])}")
    print()
    for r in results:
        if r["findings"]:
            print(r["path"])
            for cat, ln, msg in sorted(r["findings"], key=lambda f: f[1]):
                print(f"  {r['path']}:{ln}  [{cat}] {msg}")
    if shared:
        print("\nCross-file duplication")
        for cat, msg in shared:
            print(f"  [{cat}] {msg}")


if __name__ == "__main__":
    main()
