"""Checks an Outbreak Diary episode script (story/new/*.json) without rendering anything. Standard library only.

  python3 scripts/diarycheck.py story/new/ep-0004.json

Prints "ok" with a rough length estimate, or the first problem found. scripts/diary.py uses the same checks.
"""
import json
import re
import sys

BOOL = "bool"
SCENES = {  # scene: {param: allowed values, a (min, max) range, BOOL, or "lines"/"items"}
    "building": {"zombies": (0, 12), "lit": BOOL, "fire": BOOL},
    "window": {"zombies": (0, 20), "fire": BOOL, "survivor": BOOL},
    "street": {"zombies": (0, 12), "fire": BOOL},
    "rooftop": {"heli": BOOL, "fire": BOOL, "flare": BOOL},
    "room": {"light": {"lamp", "off", "candle"}, "dog": {"none", "lie", "sleep", "sit", "alert"}, "guest": {"okafor", "leo"}, "boarded": BOOL},
    "door": {"shadow": BOOL, "banging": BOOL},
    "peephole": {"who": {"okafor", "leo", "zombie", "empty"}},
    "hallway": {"light": {"on", "flicker", "off"}, "zombie": BOOL},
    "stairwell": {"zombies": BOOL},
    "kitchen": {"power": BOOL, "cans": (0, 8)},
    "phone": {"screen": {"alert", "message", "nosignal", "battery"}, "lines": "lines", "battery": (0, 100)},
    "radio": {"mode": {"static", "voice"}},
    "supplies": {"items": "items"},
    "tower": {"zombies": (0, 12), "fire": BOOL, "heli": BOOL},
    "office": {"light": {"on", "flicker", "off"}, "zombie": BOOL, "guest": {"dev"}, "fire": BOOL},
    "elevator": {"doors": {"closed", "open", "gap"}, "floor": (0, 52), "power": BOOL},
    "forest": {"zombies": (0, 12), "cabin": BOOL, "fire": BOOL},
    "cabin": {"light": {"fire", "lantern", "off"}, "guest": {"ava"}, "zombie": BOOL},
    "truck": {"zombies": (0, 8), "lights": BOOL, "wipers": BOOL},
}
ITEMS = {"can", "water", "dogfood", "flashlight", "candle", "radio", "battery", "medkit", "map", "rope", "bat", "backpack",
         "keys", "walkie"}
SFX = {"heartbeat", "knock", "bang", "creak", "static", "siren", "groan", "glass", "steps", "sting", "thud", "scratch",
       "buzz", "click", "drip", "thunder", "whoosh"}
BEAT_KEYS = {"scene", "text", "hl", "sfx", "cam", "tone", "rain", "fog", "flashlight", "alarm", "hold"}
CAMS = {"push", "pull", "left", "right", "still"}
TONES = {"night", "dawn", "dusk"}
AMBIENCE = {"rain", "wind", "night", "none"}
MAX_BEAT_WORDS = 24
WORDS = (85, 130)
BEATS = (8, 16)


class DiaryError(ValueError):
    pass


def words(text):
    return re.findall(r"[A-Za-z0-9']+", text)


def sfx_name(entry):
    """'bang' or 'bang@0.8' (seconds after the beat starts)."""
    name, _, at = str(entry).partition("@")
    if name not in SFX:
        raise DiaryError(f"unknown sound {name!r}, use {sorted(SFX)}")
    if at:
        try:
            float(at)
        except ValueError:
            raise DiaryError(f"bad time in {entry!r}, write it like 'bang@0.8'")
    return name


def check_episode(spec):
    """Raises DiaryError with a readable message when an episode uses something the renderer does not have."""
    for key in ("episode", "title", "summary", "beats"):
        if key not in spec:
            raise DiaryError(f"missing '{key}'")
    if not isinstance(spec["episode"], int):
        raise DiaryError("'episode' is a whole number")
    if spec.get("day", spec["episode"]) != spec["episode"]:
        raise DiaryError("part N is always Day N: leave 'day' out")
    if len(spec["title"]) > 28:
        raise DiaryError(f"title is {len(spec['title'])} characters, keep it to 28")
    if spec.get("ambience", "night") not in AMBIENCE:
        raise DiaryError(f"ambience must be one of {sorted(AMBIENCE)}")
    beats = spec["beats"]
    if not BEATS[0] <= len(beats) <= BEATS[1]:
        raise DiaryError(f"use {BEATS[0]}-{BEATS[1]} beats, this episode has {len(beats)}")
    total = 0
    for i, b in enumerate(beats, 1):
        where = f"beat {i}"
        scene = b.get("scene")
        if scene not in SCENES:
            raise DiaryError(f"{where}: scene must be one of {sorted(SCENES)}")
        if not b.get("text"):
            raise DiaryError(f"{where}: needs 'text'")
        n = len(words(b["text"]))
        if n > MAX_BEAT_WORDS:
            raise DiaryError(f"{where}: {n} words, keep a beat to {MAX_BEAT_WORDS}")
        total += n
        allowed = SCENES[scene]
        for key, value in b.items():
            if key in BEAT_KEYS:
                continue
            if key not in allowed:
                raise DiaryError(f"{where}: {scene} has no '{key}', it takes {sorted(allowed) or 'nothing'}")
            rule = allowed[key]
            if rule == BOOL and not isinstance(value, bool):
                raise DiaryError(f"{where}: '{key}' is true or false")
            if isinstance(rule, tuple) and not (isinstance(value, int) and rule[0] <= value <= rule[1]):
                raise DiaryError(f"{where}: '{key}' is a whole number {rule[0]}-{rule[1]}")
            if isinstance(rule, set) and value not in rule:
                raise DiaryError(f"{where}: '{key}' must be one of {sorted(rule)}")
            if rule == "lines" and (not isinstance(value, list) or len(value) > 4 or any(len(str(l)) > 60 for l in value)):
                raise DiaryError(f"{where}: 'lines' is a list of up to 4 lines of 60 characters")
            if rule == "items":
                if not isinstance(value, list) or not 1 <= len(value) <= 9:
                    raise DiaryError(f"{where}: 'items' is a list of 1-9 items")
                for it in value:
                    name, _, count = str(it).partition(":")
                    if name not in ITEMS or (count and not count.isdigit()):
                        raise DiaryError(f"{where}: item {it!r}: use {sorted(ITEMS)}, optionally with a count like 'can:3'")
        for s in b.get("sfx", []):
            sfx_name(s)
        if b.get("cam", "push") not in CAMS:
            raise DiaryError(f"{where}: cam must be one of {sorted(CAMS)}")
        if b.get("tone", "night") not in TONES:
            raise DiaryError(f"{where}: tone must be one of {sorted(TONES)}")
        text_words = {w.lower() for w in words(b["text"])}
        for h in b.get("hl", []):
            if any(w.lower() not in text_words for w in words(h)):
                raise DiaryError(f"{where}: highlight {h!r} is not in the text")
    if not WORDS[0] <= total <= WORDS[1]:
        raise DiaryError(f"{total} words in all, aim for {WORDS[0]}-{WORDS[1]} (about 45-65 seconds)")
    return total


def estimate_seconds(total_words):
    return total_words * 0.5 + 3.5  # measured on parts 1-3, with the pauses and the end card


def main():
    for path in sys.argv[1:]:
        try:
            total = check_episode(json.load(open(path)))
        except (DiaryError, json.JSONDecodeError) as e:
            raise SystemExit(f"episode error in {path}: {e}")
        print(f"ok: {path} ({total} words, about {estimate_seconds(total):.0f} s)")


if __name__ == "__main__":
    main()
