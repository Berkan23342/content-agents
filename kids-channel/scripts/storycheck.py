"""Checks a Bubbly Kids TV story script (stories/new/*.json) without rendering anything. Standard library only.

  python3 scripts/storycheck.py stories/new/2026-11-01-ducks-new-friend.json

Prints "ok" with a rough length estimate, or the first problem found. scripts/fun.py uses the same checks.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "shared"))
from novelty import overlap  # noqa: E402

CHARACTERS = {"chick", "bunny", "duck", "cat", "pig", "sheep", "frog", "dog", "cow", "lion", "owl", "turtle", "bear"}
SCRIPT_BGS = {"day", "park", "farm", "forest", "pond", "dusk", "night", "rain"}
SCRIPT_ACTS = {"jump", "shake", "spin", "sleep", "wake", "wave"}
SCRIPT_SFX = {"whoop", "pop", "tick", "ding", "sparkle", "whoosh", "boing", "thunder", "splash"}
PROP_ICONS = {"apple", "heart", "carrot", "pumpkin", "sun", "star", "leaf", "fish", "drop", "grapes", "flower", "icecream",
              "ball", "gift", "cake", "banana", "strawberry", "orange", "cookie", "egg", "jellyfish", "kite", "moon", "nest",
              "crown", "rainbow", "tree", "umbrella", "van", "watermelon", "xylophone", "yoyo", "balloon"}


class StoryError(ValueError):
    pass


def check_story(spec):
    """Raises StoryError with a readable message when a story script uses something the renderer does not have."""
    for key in ("title", "summary", "lesson", "shots"):
        if key not in spec:
            raise StoryError(f"missing '{key}'")
    for i, shot in enumerate(spec["shots"]):
        where = f"shot {i + 1}"
        if shot.get("bg") not in SCRIPT_BGS:
            raise StoryError(f"{where}: bg must be one of {sorted(SCRIPT_BGS)}")
        on_stage = {a["name"] for a in shot.get("actors", [])}
        props = {p["id"] for p in shot.get("props", [])}
        for a in shot.get("actors", []):
            if a["name"] not in CHARACTERS:
                raise StoryError(f"{where}: unknown character {a['name']!r}, use {sorted(CHARACTERS)}")
        for p in shot.get("props", []):
            if p.get("icon") not in PROP_ICONS:
                raise StoryError(f"{where}: unknown prop icon {p.get('icon')!r}, use {sorted(PROP_ICONS)}")
        for j, st in enumerate(shot["steps"]):
            kind = next(iter(st))
            w = f"{where} step {j + 1} ({kind})"
            who = st.get(kind) if kind in ("line", "enter", "move", "leave", "arrive", "act") else None
            if kind == "enter":
                if who not in CHARACTERS:
                    raise StoryError(f"{w}: unknown character {who!r}")
                on_stage.add(who)
            elif who is not None and who != "all" and who not in on_stage:
                raise StoryError(f"{w}: {who!r} is not on stage in this shot (add it to 'actors' or 'enter' it first)")
            if kind == "act" and st.get("kind") not in SCRIPT_ACTS:
                raise StoryError(f"{w}: kind must be one of {sorted(SCRIPT_ACTS)}")
            if kind == "line" and st.get("act") and st["act"] not in SCRIPT_ACTS:
                raise StoryError(f"{w}: act must be one of {sorted(SCRIPT_ACTS)}")
            if kind == "sfx" and st["sfx"] not in SCRIPT_SFX:
                raise StoryError(f"{w}: sfx must be one of {sorted(SCRIPT_SFX)}")
            if kind == "prop":
                if st.get("icon") not in PROP_ICONS:
                    raise StoryError(f"{w}: unknown prop icon {st.get('icon')!r}")
                props.add(st["prop"])
            if kind in ("prop_move", "hide") and st[kind] not in props:
                raise StoryError(f"{w}: unknown prop id {st[kind]!r}")
            if kind not in ("say", "line", "enter", "move", "leave", "arrive", "act", "prop", "prop_move", "hide", "sfx", "pause"):
                raise StoryError(f"{w}: unknown step type")



TOO_SIMILAR = 0.25  # share of three-word runs shared with an earlier story (today's stories share at most 0.05)


def story_text(spec):
    parts = [spec["title"], spec["summary"]]
    for shot in spec["shots"]:
        for st in shot["steps"]:
            parts.append(st.get("say") or st.get("text") or "")
    return " ".join(parts)


def check_against(path, spec):
    """No title twice and no story too close to an earlier one (waiting or published). Raises StoryError."""
    path = os.path.abspath(path)
    text = story_text(spec)
    for p in glob.glob(os.path.join(ROOT, "stories", "new", "*.json")) + glob.glob(os.path.join(ROOT, "stories", "used", "*", "*.json")):
        if os.path.abspath(p) == path:
            continue
        try:
            other = json.load(open(p))
        except json.JSONDecodeError:
            continue
        if other.get("title", "").strip().lower() == spec["title"].strip().lower():
            raise StoryError(f"the title {spec['title']!r} was already used ({os.path.basename(p)})")
        score = overlap(text, story_text(other))
        if score >= TOO_SIMILAR:
            raise StoryError(f"too similar to {os.path.basename(p)} ({score:.0%} of phrases repeat); write a new plot")


def estimate_seconds(spec):
    """Rough length: speech at ~2.4 words/s plus pauses, walks and shot transitions."""
    t = 0.0
    for shot in spec["shots"]:
        t += 1.1
        for st in shot["steps"]:
            kind = next(iter(st))
            if kind in ("say", "line"):
                words = len((st.get("say") or st.get("text") or "").split())
                t += words / 2.4 + st.get("gap", 0.4) + 0.3
            elif kind == "pause":
                t += st["pause"]
            elif kind in ("enter", "move", "leave") and st.get("wait"):
                t += 1.8
            elif kind == "arrive":
                t += 0.8
    return t


def main():
    with open(sys.argv[1]) as fh:
        spec = json.load(fh)
    try:
        check_story(spec)
        check_against(sys.argv[1], spec)
    except StoryError as e:
        raise SystemExit(f"story error: {e}")
    t = estimate_seconds(spec)
    print(f"ok: {spec['title']!r}, about {t:.0f} s, {len(spec['shots'])} shots")
    if not 60 <= t <= 170:
        print("warning: aim for 70-150 seconds")


if __name__ == "__main__":
    main()
