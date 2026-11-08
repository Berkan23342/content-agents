"""Checks a Brain Snack script (snacks/new/*.json) without rendering anything. Standard library only.

  python3 scripts/snackcheck.py snacks/new/2026-11-09-why-sky-blue.json

Prints "ok" with a rough length estimate, or the first problem found. scripts/snack.py uses the same checks.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "shared"))
from novelty import overlap  # noqa: E402

FORMATS = {"why", "mystery", "real"}
KINDS = {"hook", "emoji", "pair", "steps", "number", "choice", "fact", "scale", "clues", "suspects"}
MOTIONS = {"bounce", "spin", "zoom", "shake", "float"}
WORDS = (90, 160)
BEATS = (7, 14)
TOO_SIMILAR = 0.2


class SnackError(ValueError):
    pass


def words(text):
    return re.findall(r"[A-Za-z0-9']+", text)


def _item(where, it, label_max=24):
    if not isinstance(it, dict) or not it.get("emoji") or len(it["emoji"]) > 16:
        raise SnackError(f"{where}: every item needs a short 'emoji'")
    if any(0x1F1E6 <= ord(ch) <= 0x1F1FF or ord(ch) == 0x26A0 for ch in it["emoji"]):
        raise SnackError(f"{where}: no flags and no ⚠ (they do not draw everywhere)")
    if len(it.get("label", "")) > label_max:
        raise SnackError(f"{where}: label {it.get('label')!r} is longer than {label_max} characters")


def _items(where, items, lo=2, hi=4):
    if not isinstance(items, list) or not lo <= len(items) <= hi:
        raise SnackError(f"{where}: needs {lo}-{hi} items")
    for it in items:
        _item(where, it)


def check_snack(spec):
    """Raises SnackError when a script would not fit the video or the format."""
    for key in ("format", "title", "summary", "beats"):
        if key not in spec:
            raise SnackError(f"missing '{key}'")
    if spec["format"] not in FORMATS:
        raise SnackError(f"format must be one of {sorted(FORMATS)}")
    if len(spec["title"]) > 60:
        raise SnackError("title is longer than 60 characters")
    beats = spec["beats"]
    if not BEATS[0] <= len(beats) <= BEATS[1]:
        raise SnackError(f"use {BEATS[0]}-{BEATS[1]} beats, this one has {len(beats)}")
    total = 0
    kinds = []
    for i, b in enumerate(beats, 1):
        where = f"beat {i}"
        if not b.get("text"):
            raise SnackError(f"{where}: needs 'text' (what the host says)")
        n = len(words(b["text"]))
        if n > 26:
            raise SnackError(f"{where}: {n} words, keep a beat to 26")
        total += n
        v = b.get("visual") or {}
        kind = v.get("kind")
        if kind not in KINDS:
            raise SnackError(f"{where}: visual kind must be one of {sorted(KINDS)}")
        kinds.append(kind)
        if kind == "hook":
            _item(where, {"emoji": v.get("emoji")})
            if not v.get("text") or len(v["text"]) > 40:
                raise SnackError(f"{where}: a hook needs 'text' of at most 40 characters")
        elif kind == "emoji":
            _item(where, v)
            if v.get("motion", "bounce") not in MOTIONS:
                raise SnackError(f"{where}: motion must be one of {sorted(MOTIONS)}")
        elif kind == "pair":
            _item(where, v.get("a") or {})
            _item(where, v.get("b") or {})
        elif kind in ("steps", "clues"):
            _items(where, v.get("items"))
        elif kind == "number":
            if not isinstance(v.get("value"), (int, float)) or not v.get("unit") or len(v["unit"]) > 24:
                raise SnackError(f"{where}: a number needs a numeric 'value' and a 'unit' of at most 24 characters")
        elif kind == "choice":
            if not v.get("question") or len(v["question"]) > 60:
                raise SnackError(f"{where}: a choice needs a 'question' of at most 60 characters")
            _items(where, v.get("options"))
            if not isinstance(v.get("answer"), int) or not 0 <= v["answer"] < len(v["options"]):
                raise SnackError(f"{where}: 'answer' is the index of the right option")
            if not b.get("reveal") or len(words(b["reveal"])) > 24:
                raise SnackError(f"{where}: a choice beat needs 'reveal', what the host says with the answer (at most 24 words)")
            total += len(words(b["reveal"]))
        elif kind == "fact":
            _item(where, {"emoji": v.get("emoji")})
            if not v.get("text") or len(v["text"]) > 90:
                raise SnackError(f"{where}: a fact needs 'text' of at most 90 characters")
        elif kind == "scale":
            _items(where, v.get("items"))
            if any(not isinstance(it.get("size"), (int, float)) or it["size"] <= 0 for it in v["items"]):
                raise SnackError(f"{where}: every scale item needs a positive 'size'")
        elif kind == "suspects":
            _items(where, v.get("items"))
            if "pick" in v and v["pick"] is not None and not 0 <= v["pick"] < len(v["items"]):
                raise SnackError(f"{where}: 'pick' is the index of the culprit")
        text_words = {w.lower() for w in words(b["text"] + " " + b.get("reveal", ""))}
        for h in b.get("hl", []):
            if any(w.lower() not in text_words for w in words(h)):
                raise SnackError(f"{where}: highlight {h!r} is not in the text")
    if kinds[0] != "hook":
        raise SnackError("the first beat is a 'hook'")
    if len(set(kinds)) < 5:
        raise SnackError(f"use at least 5 kinds of visual, this one has {len(set(kinds))}")
    for i in range(1, len(kinds)):
        if kinds[i] == kinds[i - 1]:
            raise SnackError(f"beats {i} and {i + 1} are both '{kinds[i]}': change one of them")
    if spec["format"] in ("why", "real") and "choice" not in kinds:
        raise SnackError("a why or real snack needs a 'choice' beat: the viewer guesses before the answer")
    if spec["format"] == "why" and "fact" not in kinds:
        raise SnackError("a why snack ends with a 'fact' beat (the bonus fact)")
    if spec["format"] == "mystery":
        if "clues" not in kinds or "suspects" not in kinds or "choice" not in kinds:
            raise SnackError("a mystery needs 'suspects', 'clues' and 'choice' (the viewer's guess) beats")
        if not any(b["visual"]["kind"] == "suspects" and b["visual"].get("pick") is not None for b in beats):
            raise SnackError("a mystery ends with a 'suspects' beat whose 'pick' is the culprit")
    if not WORDS[0] <= total <= WORDS[1]:
        raise SnackError(f"{total} words in all, aim for {WORDS[0]}-{WORDS[1]} (about 50-70 seconds)")
    return total


def snack_text(spec):
    return spec["title"] + ". " + " ".join(b["text"] + " " + b.get("reveal", "") for b in spec["beats"])


def check_against(path, spec):
    """No title twice and no script too close to an earlier one. Raises SnackError."""
    path = os.path.abspath(path)
    text = snack_text(spec)
    for p in glob.glob(os.path.join(ROOT, "snacks", "new", "*.json")) + glob.glob(os.path.join(ROOT, "snacks", "used", "*", "*.json")):
        if os.path.abspath(p) == path:
            continue
        other = json.load(open(p))
        if other["title"].strip().lower() == spec["title"].strip().lower():
            raise SnackError(f"the title {spec['title']!r} was already used ({os.path.basename(p)})")
        score = overlap(text, snack_text(other))
        if score >= TOO_SIMILAR:
            raise SnackError(f"too similar to {os.path.basename(p)} ({score:.0%} of phrases repeat)")


def main():
    for path in sys.argv[1:]:
        try:
            spec = json.load(open(path))
            total = check_snack(spec)
            check_against(path, spec)
        except (SnackError, json.JSONDecodeError) as e:
            raise SystemExit(f"snack error in {path}: {e}")
        print(f"ok: {path} ({total} words, about {total * 0.45 + 8:.0f} s)")


if __name__ == "__main__":
    main()
