"""Plans and voices the daily Bubbly Kids TV YouTube Shorts: two vertical 25-45 second games a day.

Games rotate so that the two Shorts of a day are always different:
  shadow  guess the shadow: an animal sound or a hint, 3-2-1, the reveal
  egg     surprise eggs: count to three, crack, what's inside?
  count   how many? count the things together

Writes build/<date>-short<slot>/{props,meta}.json and public/audio/<date>-short<slot>.wav (same layout as scripts/fun.py).
Run with .venv/bin/python scripts/short.py --date YYYY-MM-DD --slot 1|2 [--game shadow|egg|count]
"""
import argparse
import datetime as dt
import os
import random

from episode import BUILD, COUNTABLES, GENTLE_SONGS, NUMBER_WORDS, PALETTE, Builder, an, write_audio, write_json
from fun import ACCENTS, CAST, COLOR_WORDS, CRITTERS, EGG_PATTERNS, HINTS, TOYS, icon

GAMES = ["shadow", "egg", "count"]
FIRST_SHORT = dt.date(2026, 11, 1)
ROUNDS = 3


def game_for(day, slot):
    return GAMES[(2 * (day - FIRST_SHORT).days + slot - 1) % len(GAMES)]


def countdown(b, start, cur, words):
    """Says the words one per beat with a tick; returns the tick frames (relative to start) and the time after."""
    frames = []
    for w in words:
        frames.append(b.f(cur))
        b.sfx.append((start + cur, "tick"))
        cur += max(b.say(start + cur, w) + 0.1, 0.62)
    return frames, cur


def animal_sound(b, start, cur, ic, fallback):
    """The animal says its sound in its own voice (the narrator says it for animals without a story voice)."""
    voice, pitch, sound, _ = CAST.get(ic, ("af_heart", 1.0, fallback, ""))
    return b.say(start + cur, sound, voice=voice, speed=0.9, pitch=pitch)


# ---------------------------------------------------------------- games
def game_shadow(b, rng):
    picks = [("animal", c) for c in rng.sample(CRITTERS, 2)] + [("thing", (k, *HINTS[k])) for k in rng.sample(list(HINTS), 1)]
    rng.shuffle(picks)
    prompts = ["Guess the shadow! Who is hiding?", "Who is this one?", "Last one! Who am I?"]
    found = []
    for i, (kind, item) in enumerate(picks):
        start = b.t
        b.sfx.append((start + 0.05, "whoop"))
        cur = 0.35
        cur += b.say(start + cur, prompts[i]) + 0.25
        if kind == "animal":
            ic, name, _, bubble, color = item
            cur += b.say(start + cur, "Listen!") + 0.15
            cur += animal_sound(b, start, cur, ic, bubble) + 0.35
        else:
            ic, name, color, hint = item
            bubble = "Ta-da!"
            cur += b.say(start + cur, hint) + 0.35
        counts, cur = countdown(b, start, cur, ("Three!", "Two!", "One!"))
        reveal = cur + 0.05
        b.sfx.append((start + reveal, "sparkle"))
        b.sfx.append((start + reveal, "pop"))
        name_at = reveal + 0.4
        cur = name_at + b.say(start + name_at, f"It's {an(name)} {name}!") + 0.2
        bubble_at = cur
        cur += (animal_sound(b, start, cur, ic, bubble) if kind == "animal" else 0.5) + 0.6
        hero = icon(ic, color)
        b.scene(start, start + cur, type="shadow", hero=hero, counts=counts, revealAt=b.f(reveal),
                name={"text": name.upper(), "color": color, "at": b.f(name_at)},
                bubble={"text": bubble, "color": color, "at": b.f(bubble_at)})
        b.t = start + cur
        found.append(hero)
    return found, "Great guessing!"


def game_egg(b, rng):
    picks = [("animal", c) for c in rng.sample(CRITTERS, 2)] + [("toy", t) for t in rng.sample(TOYS, 1)]
    rng.shuffle(picks)
    colors = rng.sample(COLOR_WORDS, ROUNDS)
    found = []
    for i, (kind, item) in enumerate(picks):
        start = b.t
        cname, chex = colors[i]
        pattern, _ = rng.choice(EGG_PATTERNS)
        _, ahex = rng.choice(ACCENTS)
        if kind == "animal":
            ic, name, _, bubble, color = item
        else:
            ic, name, color, line, bubble = item
            color = color or rng.choice(PALETTE)
        b.sfx.append((start + 0.05, "whoop"))
        cur = 0.35
        egg = f"{an(cname).capitalize()} {cname} egg!"
        cur += b.say(start + cur, f"Surprise egg! {egg} What's inside?" if i == 0 else f"{egg} What's inside?") + 0.2
        ticks, cur = countdown(b, start, cur, ("One!", "Two!", "Three!"))
        open_at = cur + 0.05
        b.sfx.append((start + open_at, "pop"))
        b.sfx.append((start + open_at + 0.08, "sparkle"))
        name_at = open_at + 0.6
        cur = name_at + b.say(start + name_at, f"It's {an(name)} {name}!") + 0.2
        bubble_at = cur
        cur += (animal_sound(b, start, cur, ic, bubble) if kind == "animal" else b.say(start + cur, line)) + 0.6
        hero = icon(ic, color)
        b.scene(start, start + cur, type="egg", egg={"kind": "egg", "value": f"{pattern}|{ahex}", "color": chex},
                ticks=ticks, openAt=b.f(open_at), hero=hero, name={"text": name.upper(), "color": color, "at": b.f(name_at)},
                bubble={"text": bubble, "color": color, "at": b.f(bubble_at)})
        b.t = start + cur
        found.append(hero)
    return found, "So many surprises!"


def game_count(b, rng):
    things = rng.sample(COUNTABLES, ROUNDS)
    sizes = [rng.choice(r) for r in ((3, 4), (5, 6), (7, 8, 9))]
    found = []
    for i, ((ic, one, many, color), n) in enumerate(zip(things, sizes)):
        start = b.t
        color = color or rng.choice(PALETTE)
        b.sfx.append((start + 0.05, "whoop"))
        cur = 0.35
        cur += b.say(start + cur, f"How many {many} can you see?") + 0.2
        cur += b.say(start + cur, "Let's count!") + 0.15
        counts = []
        for k in range(1, n + 1):
            counts.append(b.f(cur))
            b.sfx.append((start + cur, "pop"))
            cur += max(b.say(start + cur, f"{NUMBER_WORDS[k]}!") + 0.08, 0.6)
        answer_at = cur + 0.15
        b.sfx.append((start + answer_at, "sparkle"))
        cur = answer_at + b.say(start + answer_at, f"{NUMBER_WORDS[n]} {many}!") + 0.8
        hero = icon(ic, color)
        b.scene(start, start + cur, type="count", item=hero, n=n, counts=counts,
                answer={"text": f"{n} {many.upper()}!", "color": PALETTE[(n - 1) % 7], "at": b.f(answer_at)})
        b.t = start + cur
        found.append(hero)
    return found, "Great counting!"


GAME = {"shadow": game_shadow, "egg": game_egg, "count": game_count}
HEADER = {"shadow": "Guess the Shadow", "egg": "Surprise Eggs", "count": "Count with me"}
BACKGROUNDS = {"shadow": ["day", "park", "dusk"], "egg": ["day", "night", "park"], "count": ["day", "park", "farm"]}
TITLES = {
    "shadow": ["Guess the Shadow! Who Is Hiding? 🔍", "Can You Guess Who I Am? 🐾 Shadow Game", "Who Am I? Guess the Shadow 🔍"],
    "egg": ["Surprise Eggs! What's Inside? 🥚", "Open the Surprise Eggs! 🥚 Animals & Toys", "What's Inside the Egg? 🥚 Surprise!"],
    "count": ["How Many Can You Count? 🔢", "Count With Me! 🔢 Counting Game", "Let's Count Together! 🔢 How Many?"],
}
ABOUT = {
    "shadow": "Look at the shadow, listen to the clue, count down 3, 2, 1... who is hiding? 🔍",
    "egg": "Crack open colorful surprise eggs and find animals and toys inside! 🥚",
    "count": "How many can you see? Count along from one to nine! 🔢",
}
TAGS = {
    "shadow": ["guess the shadow", "who am i", "guessing game for kids", "animal sounds"],
    "egg": ["surprise eggs", "surprise eggs for kids", "learn animals", "learn colors"],
    "count": ["counting for kids", "count to 10", "learn numbers", "how many"],
}


def build(day, slot, game):
    rng = random.Random(f"short-{day}-{slot}")
    b = Builder()
    found, top = GAME[game](b, rng)
    start = b.t
    b.sfx.append((start + 0.1, "ding"))
    b.sfx.append((start + 0.3, "cheer"))
    d = b.say(start + 0.3, top)
    bye_at = 0.3 + d + 0.25
    end = start + bye_at + b.say(start + bye_at, "Bye bye!") + 1.0
    b.scene(start, end, type="end", heroes=found, text=top, byeAt=b.f(bye_at))
    b.t = end
    b.music = [(0, b.t, rng.choice(GENTLE_SONGS), "gentle" if game == "shadow" else "dance")]
    b.music_gain = 0.32 if game == "shadow" else 0.4
    meta = {
        "title": f"{rng.choice(TITLES[game])} #shorts",
        "description": "\n".join([
            ABOUT[game],
            "",
            "Bubbly Kids TV makes a learning video, a fun video and new Shorts every day for toddlers and preschoolers.",
            "Music: public-domain nursery melodies. Characters: original Bubbly Kids TV.",
            "",
            "#shorts #kids #toddlers #preschool #bubblykidstv",
        ]),
        "tags": TAGS[game] + ["kids shorts", "toddler learning", "preschool", "bubbly kids tv"],
    }
    props = {"bg": rng.choice(BACKGROUNDS[game]), "header": HEADER[game]}
    return b, props, meta


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=dt.date.today().isoformat())
    p.add_argument("--slot", type=int, choices=[1, 2], default=1)
    p.add_argument("--game", choices=GAMES, help="override the daily rotation")
    a = p.parse_args()
    day = dt.date.fromisoformat(a.date)
    game = a.game or game_for(day, a.slot)
    name = f"{a.date}-short{a.slot}"
    work = os.path.join(BUILD, name)
    os.makedirs(work, exist_ok=True)
    b, props, meta = build(day, a.slot, game)
    wav_rel = write_audio(b, work, name)
    write_json(work, {"durationInFrames": b.f(b.t), "audio": wav_rel, "scenes": b.scenes, **props}, meta)
    print(f"short {a.slot} {game} {a.date}: {b.t:.1f}s, {len(b.scenes)} scenes, {len(b.voices)} lines")


if __name__ == "__main__":
    main()
