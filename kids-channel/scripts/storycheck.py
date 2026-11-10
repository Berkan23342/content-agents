"""Checks a Bubbly Kids TV story script (stories/new/*.json) without rendering anything, and plans the coming days.
Standard library only.

  python3 scripts/storycheck.py stories/new/2026-11-01-ducks-new-friend.json   "ok", or the first problem found
  python3 scripts/storycheck.py --plan [days]                                  each coming day's kind and its story

scripts/fun.py uses the same checks and the same plan.
"""
import datetime as dt
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "shared"))
from novelty import overlap  # noqa: E402

CHARACTERS = {"chick", "bunny", "duck", "cat", "pig", "sheep", "frog", "dog", "cow", "lion", "owl", "turtle", "bear"}
SCRIPT_BGS = {"day", "park", "farm", "forest", "pond", "dusk", "night", "rain", "beach", "garden", "playground", "bedroom", "underwater"}
SCRIPT_ACTS = {"jump", "shake", "spin", "sleep", "wake", "wave"}
SCRIPT_SFX = {"whoop", "pop", "tick", "ding", "sparkle", "whoosh", "boing", "thunder", "splash"}
PROP_ICONS = {"apple", "heart", "carrot", "pumpkin", "sun", "star", "leaf", "fish", "drop", "grapes", "flower", "icecream",
              "ball", "gift", "cake", "banana", "strawberry", "orange", "cookie", "egg", "jellyfish", "kite", "moon", "nest",
              "crown", "rainbow", "tree", "umbrella", "van", "watermelon", "xylophone", "yoyo", "balloon"}


# The daily story's kind takes turns, one a day; each kind has its own narrator, music and opening (scripts/fun.py
# KIND_STYLE), so no two days in a row look and sound alike.
ROTATION = ["adventure", "kindness", "learning", "funny", "feelings", "bedtime"]
FIRST_DAY = dt.date(2026, 11, 9)
KINDS = set(ROTATION)
# what a story is about; the same theme at most twice among the waiting stories and the last few published
THEMES = {
    "sharing", "kindness", "friendship", "helping", "honesty", "patience", "trying", "bravery", "manners", "feelings",
    "safety", "nature", "weather", "seasons", "food", "colors", "counting", "shapes", "sounds", "family", "bedtime",
    "play", "animals", "health", "tidying", "music",
}
THEME_LIMIT = 2
RECENT_USED = 6


class StoryError(ValueError):
    pass


def check_story(spec):
    """Raises StoryError with a readable message when a story script uses something the renderer does not have."""
    for key in ("title", "summary", "lesson", "shots"):
        if key not in spec:
            raise StoryError(f"missing '{key}'")
    if len(spec["title"]) > 26 or len(spec["title"].split()) > 5:
        raise StoryError("the title is written big on the thumbnail: at most 5 words and 26 characters")
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


def waiting():
    return sorted(glob.glob(os.path.join(ROOT, "stories", "new", "*.json")))


def used():
    """Published stories, oldest first (by the date they were used on)."""
    return sorted(glob.glob(os.path.join(ROOT, "stories", "used", "*", "*.json")))


def kind_for(date):
    return ROTATION[(dt.date.fromisoformat(date) - FIRST_DAY).days % len(ROTATION)]


def check_variety(path, spec):
    """For the writer: a story has a kind and a theme, the theme is not over-used lately, a bedtime story is calm, the
    story moves between places, and it does not open where the last story opened. Raises StoryError."""
    if spec.get("kind") not in KINDS:
        raise StoryError(f"'kind' must be one of {sorted(KINDS)} (the day's kind, see --plan)")
    if spec.get("theme") not in THEMES:
        raise StoryError(f"'theme' (what the story is about) must be one of {sorted(THEMES)}")
    if (spec["kind"] == "bedtime") != bool(spec.get("calm")):
        raise StoryError("a bedtime story sets \"calm\": true, and only a bedtime story does")
    recent = [p for p in waiting() + used()[-RECENT_USED:] if os.path.abspath(p) != os.path.abspath(path)]
    same = [os.path.basename(p) for p in recent if json.load(open(p)).get("theme") == spec["theme"]]
    if len(same) >= THEME_LIMIT:
        raise StoryError(f"theme '{spec['theme']}' is already in {', '.join(same)}; pick another theme")
    bgs = [shot["bg"] for shot in spec["shots"]]
    if len(spec["shots"]) >= 3 and len(set(bgs)) < 2:
        raise StoryError("the whole story stays in one place; move part of it somewhere else")
    top = max(set(bgs), key=bgs.count)
    if len(bgs) >= 4 and bgs.count(top) > len(bgs) * 0.6:
        raise StoryError(f"'{top}' is used for {bgs.count(top)} of {len(bgs)} shots; spread the story over more places")
    path = os.path.abspath(path)
    others = sorted(p for p in glob.glob(os.path.join(ROOT, "stories", "new", "*.json")) + glob.glob(os.path.join(ROOT, "stories", "used", "*", "*.json"))
                    if os.path.abspath(p) != path and os.path.basename(p) < os.path.basename(path))
    if others:
        last = json.load(open(max(others, key=os.path.basename)))
        if last["shots"][0]["bg"] == bgs[0]:
            raise StoryError(f"the previous story also opened in '{bgs[0]}'; open somewhere else")


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


def plan(start, days):
    """[(date, kind, story path or None)]: each coming day gets the oldest waiting story of its kind."""
    pool = {}
    for p in waiting():
        try:
            pool.setdefault(json.load(open(p)).get("kind"), []).append(p)
        except json.JSONDecodeError:
            continue
    out = []
    for i in range(days):
        date = (dt.date.fromisoformat(start) + dt.timedelta(days=i)).isoformat()
        kind = kind_for(date)
        done = glob.glob(os.path.join(ROOT, "stories", "used", date, "*.json"))
        if done:
            out.append((date, kind, sorted(done)[0]))
        else:
            out.append((date, kind, pool[kind].pop(0) if pool.get(kind) else None))
    return out


def main():
    if sys.argv[1:2] == ["--plan"]:
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        today = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date().isoformat()  # Istanbul
        for date, kind, path in plan(max(today, FIRST_DAY.isoformat()), days):
            print(f"{date} {kind:9} {os.path.relpath(path, ROOT) if path else 'MISSING: write one'}")
        themes = {}
        for p in waiting() + used()[-RECENT_USED:]:
            t = json.load(open(p)).get("theme")
            themes[t] = themes.get(t, 0) + 1
        print("recent themes (at most %d each): %s" % (THEME_LIMIT, ", ".join(f"{t} {n}" for t, n in sorted(themes.items(), key=str))))
        return
    with open(sys.argv[1]) as fh:
        spec = json.load(fh)
    try:
        check_story(spec)
        check_against(sys.argv[1], spec)
        if os.sep + "new" + os.sep in os.path.abspath(sys.argv[1]):  # stories still waiting; published ones stand
            check_variety(sys.argv[1], spec)
    except StoryError as e:
        raise SystemExit(f"story error: {e}")
    t = estimate_seconds(spec)
    print(f"ok: {spec['title']!r}, about {t:.0f} s, {len(spec['shots'])} shots")
    if not 150 <= t <= 320:
        print("warning: aim for 180-300 seconds (the daily video is one story)")


if __name__ == "__main__":
    main()
