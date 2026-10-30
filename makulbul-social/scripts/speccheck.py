"""Checks a day's spec.json and caption.txt before rendering. Standard library only.

  python3 scripts/speccheck.py content/2026-10-31

Prints "ok" or the problems found (exit code 1).
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICE = re.compile(r"(\d[\d.,]*\s*(tl|₺|lira)\b|₺|\bfiyat\w*\b|\ben ucuz\b|\bindirim\w*\b)", re.I)


def words(text):
    return len(str(text).split())


def check(spec, caption):
    errors = []

    def need(cond, msg):
        if not cond:
            errors.append(msg)

    fmt = spec.get("format")
    need(fmt in ("compare", "myth", "versus", "tips", "fact"), "format must be compare, myth, versus, tips or fact")
    need(isinstance(spec.get("key"), str) and ":" in spec.get("key", ""), "key missing (e.g. 'tips:ikinci-el-telefon')")
    need(isinstance(spec.get("title"), str) and spec.get("title"), "title missing (short label for the history)")
    if fmt == "compare":
        need(spec.get("category") in ("telefon", "laptop"), "category must be telefon or laptop")
        need(words(spec.get("hook", "")) <= 7, "hook: max 7 words")
        for side in ("a", "b"):
            p = spec.get(side, {})
            need(len(p.get("short", "")) <= 10 and p.get("short"), f"{side}.short: 1-10 characters")
            need(len(p.get("name", "")) <= 22 and p.get("name"), f"{side}.name: 1-22 characters")
        rows = spec.get("rows", [])
        need(3 <= len(rows) <= 5, "rows: 3-5")
        for r in rows:
            need(r.get("win") in ("a", "b", "tie"), "row.win must be a, b or tie")
            need(len(r.get("label", "")) <= 16, f"row label too long: {r.get('label')!r}")
            need(len(r.get("a", "")) <= 12 and len(r.get("b", "")) <= 12, f"row values max 12 characters: {r}")
        need(words(spec.get("verdict", "")) <= 14, "verdict: max 14 words")
    elif fmt == "myth":
        need(words(spec.get("claim", "")) <= 7, "claim: max 7 words")
        need(words(spec.get("truth", "")) <= 12, "truth: max 12 words")
        need(2 <= len(spec.get("points", [])) <= 4, "points: 2-4")
        need(all(words(p) <= 7 for p in spec.get("points", [])), "each point: max 7 words")
    elif fmt == "versus":
        opts = spec.get("options", [])
        need(len(opts) == 2, "options: exactly 2")
        for o in opts:
            need(len(o.get("title", "")) <= 10, f"option title max 10 characters: {o.get('title')!r}")
            need(len(o.get("lines", [])) == 3 and all(words(l) <= 4 for l in o.get("lines", [])), "each option: 3 lines of max 4 words")
        need(words(spec.get("question", "")) <= 7, "question: max 7 words")
    elif fmt == "tips":
        items = spec.get("items", [])
        need(3 <= len(items) <= 4, "items: 3-4")
        need(all(words(i.get("big", "")) <= 3 and words(i.get("small", "")) <= 9 for i in items), "item: big max 3 words, small max 9 words")
        need(words(spec.get("title", "")) <= 8, "title: max 8 words")
    elif fmt == "fact":
        need(words(spec.get("big", "")) <= 9, "big: max 9 words")
        need(words(spec.get("small", "")) <= 14, "small: max 14 words")

    text = json.dumps(spec, ensure_ascii=False) + "\n" + caption
    m = PRICE.search(text)
    need(m is None, f"no prices or discounts allowed (found {m.group(0)!r})" if m else "")
    need(0 < len(caption) <= 2000, "caption.txt: 1-2000 characters")
    need("makulbul.com" in caption, "caption must mention makulbul.com")
    hist = os.path.join(ROOT, "content", "history.json")
    if os.path.exists(hist) and spec.get("key"):
        need(spec["key"] not in {h["key"] for h in json.load(open(hist))}, f"key {spec['key']!r} was already posted")
    return errors


def main():
    day = sys.argv[1]
    spec = json.load(open(os.path.join(day, "spec.json")))
    cap_path = os.path.join(day, "caption.txt")
    caption = open(cap_path).read().strip() if os.path.exists(cap_path) else ""
    errors = check(spec, caption)
    if errors:
        print("\n".join(f"- {e}" for e in errors))
        raise SystemExit(1)
    print(f"ok: {spec['format']} {spec['key']}")


if __name__ == "__main__":
    main()
