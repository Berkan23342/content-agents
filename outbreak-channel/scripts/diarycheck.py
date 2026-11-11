"""Checks an Outbreak Diary episode script (story/new/*.json) without rendering anything. Standard library only.

  python3 scripts/diarycheck.py story/new/ep-0004.json
  python3 scripts/diarycheck.py --seasons     every slot: which story runs, how far it is, and what to write next

Prints "ok" with a rough length estimate, or the first problem found. scripts/diary.py uses the same checks.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "shared"))
from novelty import overlap  # noqa: E402

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
    "lake": {"zombies": (0, 8), "canoe": BOOL},
    "gas_station": {"zombies": (0, 10), "light": {"on", "flicker", "off"}, "car": BOOL},
    "supermarket": {"zombies": (0, 5), "light": {"on", "flicker", "off"}, "empty": BOOL},
    "hospital": {"zombies": (0, 5), "light": {"on", "flicker", "off"}},
    "school": {"zombies": (0, 5), "light": {"on", "flicker", "off"}},
    "subway": {"zombies": (0, 5), "light": {"on", "flicker", "off"}, "moving": BOOL},
    "skybridge": {"zombies": (0, 5), "light": {"on", "flicker", "off"}, "cracks": BOOL},
    "lobby": {"zombies": (0, 4), "light": {"on", "flicker", "off"}, "broken": BOOL},
}
ITEMS = {"can", "water", "dogfood", "flashlight", "candle", "radio", "battery", "medkit", "map", "rope", "bat", "backpack",
         "keys", "walkie"}
SFX = {"heartbeat", "knock", "bang", "creak", "static", "siren", "groan", "glass", "steps", "sting", "thud", "scratch",
       "buzz", "click", "drip", "thunder", "whoosh"}
BEAT_KEYS = {"scene", "text", "hl", "sfx", "cam", "tone", "rain", "fog", "flashlight", "alarm", "hold", "speaker"}
CAMS = {"push", "pull", "left", "right", "still"}
TONES = {"night", "dawn", "dusk"}
AMBIENCE = {"rain", "wind", "night", "none"}
NARRATORS = {"nicole", "isabella", "heart", "grace", "ruth", "tess"}  # women's voices in voices/
# What a part is mostly about. A part never has the same event as its story's previous part, and no event fills more
# than 3 of the parts waiting plus the last 6 published (all stories), so the channel does not tell the same day twice.
EVENTS = {
    "supplies", "shelter", "escape", "rescue", "stranger", "sickness", "weather", "signal", "loss", "discovery",
    "trap", "horde", "journey", "repair", "plan", "quiet", "split", "reunion",
}
EVENT_LIMIT = 3
RECENT_USED = 6
# A special (a one-part story) is told in one of these ways; each has its own look (scripts/diary.py SPECIAL_FRAME).
SPECIAL_KINDS = {"story", "broadcast", "found", "journal"}
SPECIAL_NARRATORS = {"grace", "ruth", "tess"}  # the series keep nicole, isabella and heart
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


def check_episode(spec, cast=None):
    """Raises DiaryError with a readable message when an episode uses something the renderer does not have.
    cast: the characters of this story who can speak a line ("speaker"), from story/series.json."""
    for key in ("episode", "title", "summary", "beats"):
        if key not in spec:
            raise DiaryError(f"missing '{key}'")
    if not isinstance(spec["episode"], int):
        raise DiaryError("'episode' is a whole number")
    if spec.get("day", spec["episode"]) != spec["episode"]:
        raise DiaryError("part N is always Day N: leave 'day' out")
    if spec.get("narrator", "heart") not in NARRATORS:
        raise DiaryError(f"narrator must be one of {sorted(NARRATORS)} (the narrator is always a woman)")
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
        if "speaker" in b and cast is not None and b["speaker"] not in cast:
            raise DiaryError(f"{where}: speaker must be one of this story's cast {cast}")
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
    check_vote_fields(spec)
    return total


VOTE_AHEAD = 3  # a vote on Day N decides Day N+3: Days N+1 and N+2 are already written when the votes come in


def check_vote_fields(spec):
    """The shape of 'vote' (this part asks the viewers) and 'voted' (this part follows their answer)."""
    vote = spec.get("vote")
    if vote is not None:
        shape = 'write it as "vote": {"question": "Which way do we go?", "options": ["BRIDGE", "STAIRS"], "decides": N+3}'
        if not isinstance(vote, dict) or set(vote) != {"question", "options", "decides"}:
            raise DiaryError(f"'vote': {shape}")
        q = vote["question"]
        if not (isinstance(q, str) and 8 <= len(q) <= 48 and q.endswith("?")):
            raise DiaryError("vote 'question': one short question of 8-48 characters, ending with '?'")
        opts = vote["options"]
        if not (isinstance(opts, list) and len(opts) == 2 and opts[0] != opts[1]
                and all(isinstance(o, str) and re.fullmatch(r"[A-Z]{3,10}", o) for o in opts)):
            raise DiaryError('vote \'options\': two different words in capitals, 3-10 letters each, like ["BRIDGE", "STAIRS"]')
        if spec["episode"] == 1:
            raise DiaryError("no vote on Day 1: new viewers need the story first")
        if vote["decides"] != spec["episode"] + VOTE_AHEAD:
            raise DiaryError(f"vote 'decides' must be {spec['episode'] + VOTE_AHEAD}: the next two days are already written "
                             "when the votes are counted, so the answer comes on Day N+3")
        last = {w.upper() for w in words(spec["beats"][-1]["text"])}
        if any(o not in last for o in opts):
            raise DiaryError(f"the last beat must ask the question out loud and name both options ({opts[0]} and {opts[1]})")
    voted = spec.get("voted")
    if voted is not None:
        counts = voted.get("votes", {}) if isinstance(voted, dict) else None
        if not (isinstance(voted, dict) and set(voted) <= {"from", "pick", "votes"} and isinstance(voted.get("from"), int)
                and isinstance(voted.get("pick"), str) and isinstance(counts, dict)
                and all(isinstance(v, int) and v >= 0 for v in counts.values())):
            raise DiaryError('\'voted\': write it as {"from": N, "pick": "BRIDGE", "votes": {"BRIDGE": 7, "STAIRS": 3}}')
        if voted["from"] != spec["episode"] - VOTE_AHEAD:
            raise DiaryError(f"'voted' answers the vote of Day {spec['episode'] - VOTE_AHEAD}, so 'from' is that day")


TOO_SIMILAR = 0.2  # share of three-word runs shared with an earlier script (today's scripts share at most 0.03)


def script_text(spec):
    return spec["title"] + ". " + " ".join(b["text"] for b in spec["beats"])


def check_against(path, spec):
    """The checks that need every other script: part numbers in order, and nothing repeated.
    Raises DiaryError. path is the script's file in story/<id>/new/ or story/<id>/used/<date>/."""
    path = os.path.abspath(path)
    story_dir = os.path.join(ROOT, "story", os.path.relpath(path, os.path.join(ROOT, "story")).split(os.sep)[0])
    others = []
    for p in glob.glob(os.path.join(ROOT, "story", "*", "new", "*.json")) + glob.glob(os.path.join(ROOT, "story", "*", "used", "*", "*.json")):
        if os.path.abspath(p) != path:
            try:
                others.append((p, json.load(open(p))))
            except json.JSONDecodeError:
                continue
    mine = [(p, o) for p, o in others if os.path.abspath(p).startswith(story_dir + os.sep)]
    numbers = sorted([o["episode"] for _, o in mine] + [spec["episode"]])
    if len(set(numbers)) != len(numbers):
        raise DiaryError(f"part {spec['episode']} already exists in this story")
    if numbers != list(range(1, len(numbers) + 1)):
        raise DiaryError(f"parts must go 1, 2, 3... without gaps; this story would have {numbers}")
    m = re.search(r"ep-(\d+)\.json$", path)
    if m and int(m.group(1)) != spec["episode"]:
        raise DiaryError(f"the file name says part {int(m.group(1))} but 'episode' is {spec['episode']}")
    finale = (series_of(path) or {}).get("finale")
    if finale and spec["episode"] > finale:
        raise DiaryError(f"this story ends on Day {finale}; start the next story instead (see Seasons in AGENT.md)")
    check_vote_order(spec, [o for _, o in mine], series_of(path) or {})
    for p, o in mine:
        if o["title"].strip().lower() == spec["title"].strip().lower():
            raise DiaryError(f"the title {spec['title']!r} was already used ({os.path.basename(p)})")
    link = spec.get("inspired_by", "").split(" ")[0]
    if link and any(o.get("inspired_by", "").split(" ")[0] == link for _, o in others):
        raise DiaryError(f"another script was already inspired by {link}; pick a different trend")
    text = script_text(spec)
    for p, o in others:
        score = overlap(text, script_text(o))
        if score >= TOO_SIMILAR:
            raise DiaryError(f"too similar to {os.path.relpath(p, ROOT)} ({score:.0%} of phrases repeat); write something new")


def check_vote_order(spec, mine, series):
    """Votes in a story: never in a special or past the finale, one open question at a time, and the part a vote decides
    must say what the viewers chose ('voted')."""
    vote, n = spec.get("vote"), spec["episode"]
    if vote:
        if series.get("label"):
            raise DiaryError("a special is a single part, so there is no later day to decide: votes are for the serials")
        if series.get("finale") and vote["decides"] > series["finale"]:
            raise DiaryError(f"this vote would decide Day {vote['decides']}, after the finale (Day {series['finale']}); "
                             "ask earlier in the season, or not at all")
    for o in mine:
        a, z = o["episode"], (o.get("vote") or {}).get("decides")
        if vote and z and a < n <= z:
            raise DiaryError(f"Day {a} already asked the viewers and Day {z} gives the answer; no new vote before Day {z + 1}")
    asked = next((o for o in mine if (o.get("vote") or {}).get("decides") == n), None)
    voted = spec.get("voted")
    if asked and not voted:
        raise DiaryError(f"Day {asked['episode']} asked the viewers {asked['vote']['question']!r}; this part gives the answer, "
                         "so add 'voted' (see Viewers decide in AGENT.md)")
    if voted:
        if not asked:
            raise DiaryError(f"'voted', but Day {voted['from']} asked the viewers nothing")
        options = asked["vote"]["options"]
        if voted["pick"] not in options or set(voted.get("votes", {})) - set(options):
            raise DiaryError(f"'voted' must use Day {asked['episode']}'s options {options}")


VOTES_FILE = os.path.join(ROOT, "story", "votes.json")


def check_votes(path, spec):
    """For the writers: the part a vote decides follows the votes counted in story/votes.json (scripts/votes.py)."""
    votes = json.load(open(VOTES_FILE)) if os.path.exists(VOTES_FILE) else {}
    if spec.get("vote") and not votes.get("_reader", {}).get("ok"):
        raise DiaryError("the channel cannot read comments yet (story/votes.json \"_reader\"), so a vote could not be "
                         "counted: write this part without 'vote'")
    voted = spec.get("voted")
    if not voted:
        return
    sid = (series_of(path) or {}).get("id")
    tally = votes.get(sid, {}).get(str(voted["from"]), {})
    counts = tally.get("votes", {})
    if not sum(counts.values()):
        if sum(voted.get("votes", {}).values()):
            raise DiaryError(f"story/votes.json has no votes for Day {voted['from']}: leave 'votes' empty and choose yourself")
        return
    if voted.get("votes") != counts:
        raise DiaryError(f"copy the counted votes from story/votes.json exactly: \"votes\": {json.dumps(counts)}")
    top = max(counts.values())
    if counts.get(voted["pick"], 0) != top:
        raise DiaryError(f"the viewers chose {' or '.join(k for k, v in counts.items() if v == top)}; the story follows them")


def _recent(path):
    """Scripts waiting in every story, plus the last few published (by publishing date), without `path`."""
    waiting = glob.glob(os.path.join(ROOT, "story", "*", "new", "*.json"))
    used = sorted(glob.glob(os.path.join(ROOT, "story", "*", "used", "*", "*.json")), key=lambda p: os.path.basename(os.path.dirname(p)))
    out = []
    for p in waiting + used[-RECENT_USED:]:
        if os.path.abspath(p) != os.path.abspath(path):
            try:
                out.append((p, json.load(open(p))))
            except json.JSONDecodeError:
                continue
    return out


def check_variety(path, spec):
    """For the writers: a part has to be different from the last ones. At least 4 places (3 in a special), no place
    in more than 40% of the beats, not the same set of places as the story's previous part, an event that is not the
    previous part's and not over-used lately; a special changes its kind and its narrator every time. Raises DiaryError."""
    scenes = [b["scene"] for b in spec["beats"]]
    special = "specials" in os.path.abspath(path).split(os.sep)
    if re.match(r"\s*day\b", spec["beats"][0]["text"], re.I):
        raise DiaryError("beat 1 starts with the day; the day is on screen already, so open on the moment itself "
                         "(the hook: danger, a sound, a question)")
    if spec.get("event") not in EVENTS:
        raise DiaryError(f"'event' (what this part is mostly about) must be one of {sorted(EVENTS)}")
    same = [os.path.relpath(p, ROOT) for p, o in _recent(path) if o.get("event") == spec["event"]]
    if len(same) >= EVENT_LIMIT:
        raise DiaryError(f"event '{spec['event']}' is already in {', '.join(same)}; pick another kind of day")
    if special:
        if spec.get("kind") not in SPECIAL_KINDS:
            raise DiaryError(f"a special needs 'kind', one of {sorted(SPECIAL_KINDS)}")
        if spec.get("narrator") not in SPECIAL_NARRATORS:
            raise DiaryError(f"a special picks its own 'narrator', one of {sorted(SPECIAL_NARRATORS)}")
    need = 3 if special else 4
    if len(set(scenes)) < need:
        raise DiaryError(f"only {len(set(scenes))} different scenes; use at least {need} so the part does not look the same throughout")
    top = max(set(scenes), key=scenes.count)
    if scenes.count(top) > max(3, int(len(scenes) * 0.4)):
        raise DiaryError(f"'{top}' fills {scenes.count(top)} of {len(scenes)} beats; spread the part over more places")
    story = os.path.dirname(os.path.dirname(os.path.abspath(path)))
    if story.endswith("used"):
        story = os.path.dirname(story)
    earlier = []
    for p in glob.glob(os.path.join(story, "new", "*.json")) + glob.glob(os.path.join(story, "used", "*", "*.json")):
        if os.path.abspath(p) != os.path.abspath(path):
            o = json.load(open(p))
            if o["episode"] < spec["episode"]:
                earlier.append(o)
    previous = max(earlier, key=lambda o: o["episode"]) if earlier else None
    if previous and not special:
        last = {b["scene"] for b in previous["beats"]}
        mine = set(scenes)
        if len(mine & last) / len(mine | last) >= 0.8:
            raise DiaryError(f"almost the same places as the previous part ({sorted(last)}); take the story somewhere new")
    if previous and previous.get("event") == spec["event"]:
        raise DiaryError(f"the previous part was also '{spec['event']}'; make this day about something else")
    if previous and special:
        if previous.get("kind") == spec["kind"]:
            raise DiaryError(f"the previous special was also a '{spec['kind']}'; tell this one another way")
        if previous.get("narrator") == spec["narrator"]:
            raise DiaryError(f"the previous special was also told by {spec['narrator']}; pick another narrator")


def estimate_seconds(total_words):
    return total_words * 0.5 + 3.5  # measured on parts 1-3, with the pauses and the end card


SERIES_FILE = os.path.join(ROOT, "story", "series.json")
FRAMES = {"diary", "camcorder", "journal", "broadcast"}


def series_of(path):
    """The story/series.json entry of the story a script belongs to (story/<id>/...)."""
    parts = os.path.abspath(path).split(os.sep)
    story = parts[parts.index("story") + 1] if "story" in parts else None
    return next((s for s in json.load(open(SERIES_FILE)) if s["id"] == story), None)


def cast_for(path):
    """The speaking cast of the story a script belongs to (story/<id>/...)."""
    s = series_of(path)
    return s["cast"] if s else None


def published(sid):
    return max((json.load(open(p))["episode"] for p in glob.glob(os.path.join(ROOT, "story", sid, "used", "*", "*.json"))),
               default=0)


def waiting(sid):
    return sorted(json.load(open(p))["episode"] for p in glob.glob(os.path.join(ROOT, "story", sid, "new", "*.json")))


def check_series():
    """story/series.json: every story can be voiced and drawn, and the stories that run together look and sound
    different. Returns a list of problems."""
    problems, S = [], json.load(open(SERIES_FILE))
    voices = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, "voices", "*.wav"))}
    for s in S:
        for key in ("id", "name", "slot", "publish", "about", "narrator", "cast", "frame"):
            if key not in s:
                problems.append(f"{s.get('id')}: missing '{key}'")
        if s.get("narrator") not in NARRATORS:
            problems.append(f"{s.get('id')}: narrator must be one of {sorted(NARRATORS)}")
        if s.get("frame") not in FRAMES:
            problems.append(f"{s.get('id')}: frame must be one of {sorted(FRAMES)}")
        for who in s.get("cast", []):
            if s.get("voices", {}).get(who, who) not in voices:
                problems.append(f"{s.get('id')}: cast member {who!r} has no voice; add \"voices\": {{\"{who}\": <one of {sorted(voices)}>}}")
        if not os.path.exists(os.path.join(ROOT, "story", s.get("id", "?"), "bible.md")) and not s.get("label"):
            problems.append(f"{s.get('id')}: story/{s.get('id')}/bible.md is missing")
        if not s.get("label") and not s.get("tagline"):
            problems.append(f"{s.get('id')}: needs a 'tagline' (one line, at most 42 characters)")
        if len(s.get("tagline", "")) > 42:
            problems.append(f"{s.get('id')}: tagline is longer than 42 characters")
        fin = s.get("finale")
        if fin and (fin in waiting(s["id"]) or published(s["id"]) >= fin):
            film = s.get("film") or {}
            if not all(isinstance(film.get(k), str) and film[k] for k in ("title", "intro", "outro")):
                problems.append(f"{s['id']}: its finale is written, so add \"film\": {{\"title\", \"intro\", \"outro\"}} for the "
                                "full-story video (Seasons in AGENT.md)")
            elif len(film["title"]) > 60:
                problems.append(f"{s['id']}: film title is longer than 60 characters")
    serials = [s for s in S if not s.get("label")]
    running = [s for s in serials if not (s.get("finale") and published(s["id"]) >= s["finale"])]
    current = {}
    for s in running:
        current.setdefault(s["slot"], s)
    upcoming = [s for s in running if current[s["slot"]] is not s]
    for s in upcoming:
        others = [o for o in current.values() if o["slot"] != s["slot"]]
        if any(o["frame"] == s["frame"] for o in others):
            problems.append(f"{s['id']}: frame '{s['frame']}' is already used by a story running beside it; pick another")
        if any(o["narrator"] == s["narrator"] for o in others):
            problems.append(f"{s['id']}: narrator '{s['narrator']}' already tells a story running beside it; pick another")
        prev = current[s["slot"]]
        for key in ("publish", "weekdays"):
            if s.get(key) != prev.get(key):
                problems.append(f"{s['id']}: '{key}' must match {prev['id']} (same slot {s['slot']})")
    return problems


def seasons():
    """What the writer needs to know about every slot."""
    S = json.load(open(SERIES_FILE))
    for slot in sorted({s["slot"] for s in S}):
        mine = [s for s in S if s["slot"] == slot]
        for s in mine:
            done, wait, fin = published(s["id"]), waiting(s["id"]), s.get("finale")
            if fin and done >= fin:
                state = f"finished (Day {fin})"
            elif fin:
                state = f"published {done}/{fin}, waiting {wait or 'none'}"
            else:
                state = f"published {done}, waiting {wait or 'none'}" + ("" if s.get("label") else ", NO FINALE SET")
            print(f"{slot} {s['id']:<14} {state}")
        last = mine[-1]
        fin = last.get("finale")
        if fin and fin in waiting(last["id"]) + [published(last["id"])] and published(last["id"]) <= fin:
            print(f"   -> {last['id']} has its finale written: the NEXT STORY for slot {slot} is due now (Seasons in AGENT.md)")
    for p in check_series():
        print("problem:", p)


def main():
    if sys.argv[1:] == ["--seasons"]:
        seasons()
        return
    for path in sys.argv[1:]:
        try:
            spec = json.load(open(path))
            total = check_episode(spec, cast_for(path))
            check_against(path, spec)
            if os.sep + "new" + os.sep in os.path.abspath(path):  # only parts still being written; published ones stand
                check_variety(path, spec)
                check_votes(path, spec)
        except (DiaryError, json.JSONDecodeError) as e:
            raise SystemExit(f"episode error in {path}: {e}")
        print(f"ok: {path} ({total} words, about {estimate_seconds(total):.0f} s)")


if __name__ == "__main__":
    main()
