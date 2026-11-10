"""Checks a Brain Snack script (snacks/new/*.json) without rendering anything, and plans the coming days. Standard
library only.

  python3 scripts/snackcheck.py snacks/new/2026-11-09-why-sky-blue.json   "ok", or the first problem found
  python3 scripts/snackcheck.py --plan [days]                             the format of each coming day, and its script

scripts/snack.py uses the same checks and the same plan.
"""
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "shared"))
from novelty import overlap  # noqa: E402

# The formats take turns, one a day, so the same one comes back every 8 days and on a different weekday each time.
ROTATION = ["why", "how", "mystery", "myth", "real", "whatif", "teaser", "origin"]
FIRST_DAY = dt.date(2026, 11, 9)  # a "why" day
FORMATS = set(ROTATION)
# what a snack is about; the same topic at most twice among the waiting scripts and the last few used ones
TOPICS = {
    "body", "mind", "health", "space", "earth", "weather", "ocean", "nature", "animals", "food", "technology",
    "home", "history", "language", "money", "travel", "sport", "music", "art", "work", "school", "city", "transport",
}
TOPIC_LIMIT = 2
RECENT_USED = 6
KINDS = {"hook", "emoji", "pair", "steps", "number", "choice", "fact", "scale", "clues", "suspects"}
MOTIONS = {"bounce", "spin", "zoom", "shake", "float"}
WORDS = (70, 100)  # with the guess timer and the outro: about 35-45 seconds (our best quizzes were 35-42 s)
BEATS = (5, 9)
TITLE_START = 2  # a title must not start with the same two words as any of the last 3 snacks
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
    for key in ("format", "title", "summary", "topic", "beats"):
        if key not in spec:
            raise SnackError(f"missing '{key}'")
    if spec["format"] not in FORMATS:
        raise SnackError(f"format must be one of {sorted(FORMATS)}")
    if spec["topic"] not in TOPICS:
        raise SnackError(f"topic must be one of {sorted(TOPICS)}")
    if len(spec["title"]) > 60:
        raise SnackError("title is longer than 60 characters")
    if not spec["title"].rstrip().endswith("?") or not re.search(r"\byou(r|'re|'d)?\b", spec["title"], re.I):
        raise SnackError("the title is a question to the viewer: it ends with '?' and says 'you' or 'your' "
                         "(e.g. 'Which Exit Would You Take?')")
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
    if "?" not in beats[0]["text"]:
        raise SnackError("beat 1 asks the snack's question out loud (with '?'): the viewer starts guessing in the first "
                         "second, while the choice's options are already on screen")
    if kinds.count("choice") != 1:
        raise SnackError("use exactly one 'choice' beat: the hook asks it, the choice reveals it")
    at = kinds.index("choice")
    if at < 2:
        raise SnackError("put at least one beat between the hook and the 'choice', so the answer is earned")
    if len(kinds) - 1 - at > 3:
        raise SnackError("at most 3 beats after the 'choice': the video ends soon after the answer")
    if len(set(kinds)) < 4:
        raise SnackError(f"use at least 4 kinds of visual, this one has {len(set(kinds))}")
    for i in range(1, len(kinds)):
        if kinds[i] == kinds[i - 1]:
            raise SnackError(f"beats {i} and {i + 1} are both '{kinds[i]}': change one of them")
    if "choice" not in kinds:
        raise SnackError("every snack needs a 'choice' beat: the viewer guesses before the answer")
    if spec["format"] == "how" and "steps" not in kinds:
        raise SnackError("a how snack shows the mechanism as a 'steps' beat")
    if spec["format"] == "myth" and "pair" not in kinds:
        raise SnackError("a myth snack puts the belief against the truth in a 'pair' beat")
    if spec["format"] in ("whatif", "teaser", "origin") and "steps" not in kinds:
        raise SnackError({"whatif": "a what-if shows the chain of what would happen as a 'steps' beat",
                          "teaser": "a teaser explains the solution step by step in a 'steps' beat",
                          "origin": "an origin story shows how it changed over time in a 'steps' beat"}[spec["format"]])
    if spec["format"] == "why" and "fact" not in kinds:
        raise SnackError("a why snack ends with a 'fact' beat (the bonus fact)")
    if spec["format"] == "mystery":
        if "clues" not in kinds or "suspects" not in kinds or "choice" not in kinds:
            raise SnackError("a mystery needs 'suspects', 'clues' and 'choice' (the viewer's guess) beats")
        if not any(b["visual"]["kind"] == "suspects" and b["visual"].get("pick") is not None for b in beats):
            raise SnackError("a mystery ends with a 'suspects' beat whose 'pick' is the culprit")
    if not WORDS[0] <= total <= WORDS[1]:
        raise SnackError(f"{total} words in all, aim for {WORDS[0]}-{WORDS[1]} (about 35-45 seconds)")
    return total


def snack_text(spec):
    return spec["title"] + ". " + " ".join(b["text"] + " " + b.get("reveal", "") for b in spec["beats"])


def waiting():
    return sorted(glob.glob(os.path.join(ROOT, "snacks", "new", "*.json")))


def used():
    """Used scripts, oldest first (by the date folder they were used on)."""
    return sorted(glob.glob(os.path.join(ROOT, "snacks", "used", "*", "*.json")))


def check_against(path, spec, topics=True):
    """No title twice, no script too close to an earlier one, no topic over-used lately (only checked when writing).
    Raises SnackError."""
    path = os.path.abspath(path)
    text = snack_text(spec)
    recent = [p for p in waiting() + used()[-RECENT_USED:] if os.path.abspath(p) != path]
    same = [os.path.basename(p) for p in recent if json.load(open(p)).get("topic") == spec["topic"]]
    if topics and len(same) >= TOPIC_LIMIT:
        raise SnackError(f"topic '{spec['topic']}' is already in {', '.join(same)}: pick another topic")
    for p in waiting() + used():
        if os.path.abspath(p) == path:
            continue
        other = json.load(open(p))
        if other["title"].strip().lower() == spec["title"].strip().lower():
            raise SnackError(f"the title {spec['title']!r} was already used ({os.path.basename(p)})")
        score = overlap(text, snack_text(other))
        if score >= TOO_SIMILAR:
            raise SnackError(f"too similar to {os.path.basename(p)} ({score:.0%} of phrases repeat)")
    start = lambda t: " ".join(words(t.lower())[:TITLE_START])  # noqa: E731
    mine = date_of(path)
    before = sorted((date_of(p), p) for p in waiting() + used() if os.path.abspath(p) != path and date_of(p) < mine)[-3:]
    for _, p in before:
        if start(json.load(open(p))["title"]) == start(spec["title"]):
            raise SnackError(f"the title starts like {os.path.basename(p)}'s ('{start(spec['title'])} ...'); "
                             "vary how titles open")


def date_of(path):
    """The day a script is for: snacks/new/<date>-..., or the folder snacks/used/<date>/."""
    m = re.match(r"\d{4}-\d{2}-\d{2}", os.path.basename(path)) or re.match(r"\d{4}-\d{2}-\d{2}", os.path.basename(os.path.dirname(path)))
    return m.group(0) if m else "9999"


def format_for(date):
    return ROTATION[(dt.date.fromisoformat(date) - FIRST_DAY).days % len(ROTATION)]


def plan(start, days):
    """[(date, format, script path or None)]: each coming day gets the oldest waiting script of its format."""
    pool = {}
    for p in waiting():
        try:
            pool.setdefault(json.load(open(p))["format"], []).append(p)
        except (json.JSONDecodeError, KeyError):
            continue
    out = []
    for i in range(days):
        date = (dt.date.fromisoformat(start) + dt.timedelta(days=i)).isoformat()
        fmt = format_for(date)
        done = glob.glob(os.path.join(ROOT, "snacks", "used", date, "*.json"))
        if done:
            out.append((date, fmt, done[0]))
        else:
            out.append((date, fmt, pool[fmt].pop(0) if pool.get(fmt) else None))
    return out


def main():
    if sys.argv[1:2] == ["--plan"]:
        days = int(sys.argv[2]) if len(sys.argv) > 2 else len(ROTATION)
        today = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date().isoformat()  # Istanbul
        for date, fmt, path in plan(max(today, FIRST_DAY.isoformat()), days):
            print(f"{date} {fmt:8} {os.path.relpath(path, ROOT) if path else 'MISSING: write one'}")
        topics = {}
        for p in waiting() + used()[-RECENT_USED:]:
            t = json.load(open(p)).get("topic")
            topics[t] = topics.get(t, 0) + 1
        print("recent topics (at most %d each): %s" % (TOPIC_LIMIT, ", ".join(f"{t} {n}" for t, n in sorted(topics.items(), key=str))))
        return
    for path in sys.argv[1:]:
        try:
            spec = json.load(open(path))
            total = check_snack(spec)
            check_against(path, spec)
        except (SnackError, json.JSONDecodeError) as e:
            raise SystemExit(f"snack error in {path}: {e}")
        print(f"ok: {path} ({total} words, about {total * 0.34 + 9:.0f} s)")


if __name__ == "__main__":
    main()
