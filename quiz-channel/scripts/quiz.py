"""Plans and voices the daily Brain Snack Quiz Shorts: vertical, 30-50 seconds, five questions from easy to hard.

Formats rotate so that the two Shorts of a day are always different:
  flags      guess the flag (flag-icons SVGs; easy, medium, then one hard flag)
  trivia     general knowledge, from packs in quizzes/new (written by the quiz writer routine, see AGENT.md)
  math       quick math, generated here, so the code works out every answer
  truefalse  true or false with a one-line explanation, from packs in quizzes/new

Voice, effects, mixing and the master come from the kids channel's scripts (kids-channel/scripts/episode.py and audio.py).
Writes build/<date>-q<slot>/{props,meta}.json and public/audio/<date>-q<slot>.wav.
Run with ../kids-channel/.venv/bin/python scripts/quiz.py --date YYYY-MM-DD --slot 1|2 [--format flags|trivia|math|truefalse]
"""
import argparse
import datetime as dt
import glob
import json
import os
import random
import shutil
import sys
import wave
from fractions import Fraction

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "kids-channel", "scripts"))

from episode import DRUMS, SR, Builder, Midi, mix, render_midi  # noqa: E402
from quizcheck import PackError, check_pack  # noqa: E402

BUILD = os.path.join(ROOT, "build")
PUBLIC = os.path.join(ROOT, "public")
QUIZ_DIR = os.path.join(ROOT, "quizzes")
FLAGS = os.path.join(ROOT, "node_modules", "flag-icons", "flags", "4x3")
COUNTRIES = json.load(open(os.path.join(ROOT, "data", "countries.json")))
BY_CODE = {c["code"]: c for c in COUNTRIES}

FORMATS = ["flags", "trivia", "math", "truefalse"]
FIRST_QUIZ = dt.date(2026, 11, 1)
HOST = "af_bella"
HOST_SPEED = 1.05
THINK = 3.0  # seconds on the clock
THEMES = {
    "flags": {"a": "#2563EB", "b": "#7C3AED", "accent": "#FACC15"},
    "trivia": {"a": "#7C3AED", "b": "#DB2777", "accent": "#22D3EE"},
    "math": {"a": "#0891B2", "b": "#4F46E5", "accent": "#FB923C"},
    "truefalse": {"a": "#EA580C", "b": "#BE185D", "accent": "#FACC15"},
}


def format_for(day, slot):
    return FORMATS[(2 * (day - FIRST_QUIZ).days + slot - 1) % len(FORMATS)]


# ---------------------------------------------------------------- flags
# flags people mix up, used as wrong answers so the quiz is not too easy
LOOKALIKES = {
    "id": ["mc", "pl"], "mc": ["id", "pl"], "pl": ["id", "mc"], "td": ["ro", "md"], "ro": ["td", "md"],
    "ie": ["ci", "it"], "ci": ["ie", "it"], "it": ["mx", "ie"], "mx": ["it", "ie"], "nl": ["lu", "fr"],
    "lu": ["nl", "fr"], "au": ["nz"], "nz": ["au"], "no": ["is", "dk"], "is": ["no", "fi"], "se": ["fi", "dk"],
    "dk": ["ch", "no"], "ch": ["dk", "at"], "co": ["ec", "ve"], "ec": ["co", "ve"], "ve": ["co", "ec"],
    "sn": ["ml", "gn"], "ml": ["sn", "gn"], "gn": ["ml", "sn"], "si": ["sk", "ru"], "sk": ["si", "ru"],
    "ru": ["si", "sk"], "hu": ["it", "bg"], "bg": ["hu"], "ar": ["uy", "sv"], "uy": ["ar", "gr"], "gr": ["uy"],
    "ni": ["sv", "hn"], "sv": ["ni", "hn"], "hn": ["ni", "sv"], "ae": ["kw", "jo"], "kw": ["ae", "jo"],
    "jo": ["kw", "ae"], "qa": ["bh"], "bh": ["qa"], "tr": ["tn"], "tn": ["tr"], "be": ["de"], "de": ["be"],
    "jp": ["bd", "kr"], "bd": ["jp"], "at": ["lv", "pe"], "lv": ["at"], "pe": ["at", "ca"],
}
FLAG_LEVELS = [1, 1, 2, 2, 3]
FLAG_SAY = ["Number one!", "Number two!", "Number three!", "Number four!", "Last one! This one is hard!"]


def nth_flag(level, i):
    """The i-th flag of a level: every flag comes once per round, in a fresh order each round."""
    pool = [c for c in COUNTRIES if c["level"] == level]
    cycle, pos = divmod(i, len(pool))
    random.Random(f"flags-{level}-{cycle}").shuffle(pool)
    return pool[pos]


def flag_questions(day, slot, rng):
    k = 2 * (day - FIRST_QUIZ).days + slot - 1
    shown = sum(1 for j in range(max(0, k)) if FORMATS[j % len(FORMATS)] == "flags")  # flags Shorts before this one
    per = {lvl: FLAG_LEVELS.count(lvl) for lvl in set(FLAG_LEVELS)}
    seen = {lvl: 0 for lvl in per}
    qs = []
    for n, lvl in enumerate(FLAG_LEVELS):
        c = nth_flag(lvl, shown * per[lvl] + seen[lvl])
        seen[lvl] += 1
        wrong = [BY_CODE[x] for x in LOOKALIKES.get(c["code"], [])][:2]
        same = [x for x in COUNTRIES if x["region"] == c["region"] and x is not c and x not in wrong]
        rng.shuffle(same)
        options = [c] + wrong + same[: 3 - len(wrong)]
        rng.shuffle(options)
        qs.append({"kind": "flag", "text": "Which country is this?", "say": FLAG_SAY[n], "flag": f"flags/{c['code']}.svg",
                   "options": [o["name"] for o in options], "answer": options.index(c), "reveal": f"{c['name']}!"})
    return qs


# ---------------------------------------------------------------- math
def choices(rng, answer, wrong):
    """Four options: the answer, the given wrong answers (common mistakes first), then near misses."""
    opts = [answer]
    for w in wrong:
        if w not in opts and (not isinstance(w, (int, float)) or w > 0):
            opts.append(w)
    step = 1
    while len(opts) < 4:
        for w in (answer + step, answer - step):
            if w not in opts and w > 0 and len(opts) < 4:
                opts.append(w)
        step += 1
    opts = opts[:4]
    rng.shuffle(opts)
    return [str(o) for o in opts], opts.index(answer)


def math_questions(rng):
    qs = []

    def add(text, say, answer, wrong, kind="math", shown=None):
        options, idx = choices(rng, answer, wrong)
        qs.append({"kind": kind, "text": text, "say": say, "options": options if shown is None else [shown(o) for o in options],
                   "answer": idx, "reveal": f"{options[idx] if shown is None else shown(options[idx])}!"})

    a, b = rng.randint(6, 9), rng.randint(6, 9)
    add(f"{a} × {b}", f"What is {a} times {b}?", a * b, [a * b + a, a * b - b, a * b + 2])

    pct, base = rng.choice([(10, 70), (10, 90), (20, 40), (20, 60), (25, 80), (25, 120), (50, 86), (75, 40), (75, 80)])
    ans = pct * base // 100
    add(f"{pct}% of {base}", f"What is {pct} percent of {base}?", ans, [ans + 10, ans * 2, base - ans])

    kind = rng.choice(["add", "double", "squares", "growing", "fib"])
    if kind == "add":
        s, d = rng.randint(2, 9), rng.randint(3, 9)
        seq = [s + d * i for i in range(5)]
        nxt, wrong = s + 5 * d, [s + 5 * d + 1, s + 5 * d - d // 2, s + 6 * d]
    elif kind == "double":
        s, r = rng.choice([(1, 2), (3, 2), (5, 2), (2, 3), (1, 3)])
        seq = [s * r ** i for i in range(5)]
        nxt, wrong = s * r ** 5, [seq[-1] + (seq[-1] - seq[-2]), s * r ** 5 + r, s * r ** 5 - s]
    elif kind == "squares":
        s = rng.randint(1, 4)
        seq = [(s + i) ** 2 for i in range(5)]
        nxt, wrong = (s + 5) ** 2, [seq[-1] + (seq[-1] - seq[-2]), (s + 5) ** 2 + 2, (s + 5) * 2]
    elif kind == "growing":
        s = rng.randint(1, 5)
        seq = [s]
        for i in range(1, 5):
            seq.append(seq[-1] + i)
        nxt, wrong = seq[-1] + 5, [seq[-1] + 4, seq[-1] + 6, seq[-1] + 2]
    else:
        x, y = rng.choice([(1, 2), (2, 3), (1, 3), (2, 4)])
        seq = [x, y]
        while len(seq) < 5:
            seq.append(seq[-1] + seq[-2])
        nxt, wrong = seq[-1] + seq[-2], [seq[-1] + (seq[-1] - seq[-2]), seq[-1] * 2, seq[-1] + seq[-2] + 1]
    add(", ".join(map(str, seq)) + ", ?", ", ".join(map(str, seq)) + "... what comes next?", nxt, wrong)

    if rng.random() < 0.5:
        x, y, z = rng.randint(2, 9), rng.randint(2, 6), rng.randint(3, 9)
        add(f"{x} + {y} × {z}", f"What is {x} plus {y} times {z}?", x + y * z, [(x + y) * z, x + y + z, x * y + z])
    else:
        z = rng.randint(2, 5)
        y = z * rng.randint(2, 6)
        x = rng.randint(y // z + 4, 30)
        add(f"{x} − {y} ÷ {z}", f"What is {x} minus {y} divided by {z}?", x - y // z, [(x - y) // z if (x - y) > 0 else x + 1, x - y + z, x - z])

    hard = rng.choice(["fraction", "rate", "big", "square"])
    if hard == "fraction":
        p, q = rng.choice([(Fraction(1, 2), Fraction(1, 4)), (Fraction(1, 3), Fraction(1, 6)), (Fraction(1, 2), Fraction(1, 3)),
                           (Fraction(3, 4), Fraction(1, 8))])
        ans = p + q
        right = f"{ans.numerator}/{ans.denominator}"
        # the usual mistakes: adding tops and bottoms, multiplying the bottoms, halving the answer
        options = list(dict.fromkeys([right, f"{p.numerator + q.numerator}/{p.denominator + q.denominator}",
                                      f"{p.numerator + q.numerator}/{p.denominator * q.denominator}",
                                      f"{ans.numerator}/{ans.denominator * 2}"]))
        rng.shuffle(options)
        say = f"What is {p.numerator} over {p.denominator}, plus {q.numerator} over {q.denominator}?"
        qs.append({"kind": "math", "text": f"{p.numerator}/{p.denominator} + {q.numerator}/{q.denominator}", "say": say,
                   "options": options, "answer": options.index(right), "reveal": f"{right.replace('/', ' over ')}!"})
    elif hard == "rate":
        n, price, m = rng.choice([(3, 6, 7), (4, 12, 5), (5, 15, 8), (2, 7, 6), (6, 18, 4)])
        thing = rng.choice(["pens", "apples", "cookies", "tickets", "stickers"])
        ans = price // n * m
        add(f"{n} {thing} cost ${price}. How much do {m} {thing} cost?", f"{n} {thing} cost {price} dollars. How much do {m} cost?",
            ans, [price + m - n, ans + price // n, price * m // n + 2], kind="choice", shown=lambda o: f"${o}")
    elif hard == "big":
        a, b = rng.choice([(12, 15), (11, 14), (13, 12), (15, 15), (14, 12), (25, 16)])
        add(f"{a} × {b}", f"What is {a} times {b}?", a * b, [a * b + 10, a * b - a, a * (b - 1) + 2])
    else:
        r = rng.randint(11, 15)
        add(f"The square root of {r * r}?", f"What is the square root of {r * r}?", r, [r + 1, r - 1, r * r // 10],
            kind="choice")
    return qs


# ---------------------------------------------------------------- packs (trivia, true or false)
def take_pack(kind, date, slot):
    """The pack this Short already used (on a re-run), else the oldest unused pack of that kind."""
    mine = sorted(glob.glob(os.path.join(QUIZ_DIR, "used", date, f"q{slot}-*.json")))
    for path in mine + sorted(glob.glob(os.path.join(QUIZ_DIR, "new", "*.json"))):
        try:
            spec = json.load(open(path))
            check_pack(spec)
        except (PackError, json.JSONDecodeError) as e:
            print(f"skipping {os.path.basename(path)}: {e}")
            continue
        if spec["type"] == kind:
            return path, spec
    return None, None


def pack_questions(spec):
    if spec["type"] == "trivia":
        return [{"kind": "choice", "text": q["q"], "say": q["q"], "options": q["options"], "answer": q["answer"],
                 "reveal": f"{q['options'][q['answer']]}!"} for q in spec["questions"]]
    return [{"kind": "tf", "text": q["q"], "say": q["q"], "options": ["TRUE", "FALSE"], "answer": 0 if q["answer"] else 1,
             "note": q["note"], "reveal": f"{'True' if q['answer'] else 'False'}! {q['note']}"} for q in spec["questions"]]


def two_lines(title):
    words = title.upper().split()
    if len(title) <= 10 or len(words) == 1:
        return [title.upper()]
    best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
    return [" ".join(words[:best]), " ".join(words[best:])]


# ---------------------------------------------------------------- music: an original quiz-show groove
CHORDS = {"C": (48, 4), "D": (50, 4), "Dm": (50, 3), "Em": (52, 3), "F": (53, 4), "G": (55, 4), "Am": (57, 3), "Bb": (58, 4)}
PROGRESSIONS = [["Am", "F", "C", "G"], ["C", "G", "Am", "F"], ["F", "G", "Em", "Am"], ["Dm", "Bb", "F", "C"]]
QUIZ_BPM = 116
EPIANO, VIBES, SYNTH_BASS, WARM_PAD = 4, 11, 38, 89


def quiz_music(length_s, work, seed):
    rng = random.Random(seed)
    prog = rng.choice(PROGRESSIONS)
    beat = 60 / QUIZ_BPM
    m = Midi(QUIZ_BPM)
    for ch, prog_no in ((0, VIBES), (1, EPIANO), (2, SYNTH_BASS), (3, WARM_PAD)):
        m.program(ch, prog_no)
    for ch, vol, pan in ((0, 70, 84), (1, 80, 44), (2, 100, 64), (3, 60, 64), (DRUMS, 90, 64)):
        m.control(ch, 7, vol)
        m.control(ch, 10, pan)
    t, bar = 0.0, 0
    while t < length_s + 1:
        root, third = CHORDS[prog[bar % 4]]
        triad = [root, root + third, root + 7]
        for p in triad:
            m.note(3, p - 12, t, 4 * beat, 34)
        for k in range(4):  # off-beat stabs
            for p in triad:
                m.note(1, p, t + k * beat + beat / 2, beat * 0.3, 50)
        for k in range(8):  # bass on the eighths, octave jump on the off-beats
            m.note(2, root - 12 + (12 if k % 2 else 0), t + k * beat / 2, beat * 0.4, 88 if k % 2 == 0 else 70)
        arp = triad + [root + 12]
        for k in range(16):  # soft sixteenth arpeggio
            m.note(0, arp[(k * 3 + bar) % 4] + 12, t + k * beat / 4, beat / 5, 34 + (10 if k % 4 == 0 else 0))
        for k in range(4):
            at = t + k * beat
            m.note(DRUMS, 36, at, 0.1, 96 if k % 2 == 0 else 70)
            if k % 2 == 1:
                m.note(DRUMS, 39, at, 0.1, 80)
            m.note(DRUMS, 42, at + beat / 2, 0.05, 44)
            m.note(DRUMS, 42, at, 0.05, 30)
        if bar % 4 == 3:
            m.note(DRUMS, 46, t + 3.5 * beat, 0.2, 50)
        t += 4 * beat
        bar += 1
    music = render_midi(m, os.path.join(work, "music"))
    n = int(length_s * SR)
    music = np.pad(music, ((0, max(0, n - len(music))), (0, 0)))[:n]
    return music / (np.max(np.abs(music)) + 1e-9)


# ---------------------------------------------------------------- the Short
HOOKS = {
    "flags": (["GUESS THE", "FLAG!"], "Guess the flag! Can you get all five?"),
    "math": (["QUICK", "MATH!"], "Quick math! Can you solve all five?"),
}
TITLES = {
    "flags": ["Guess the Flag! 🌍 Can You Get 5/5?", "Flag Quiz 🌍 How Many Can You Name?", "Can You Guess These Flags? 🌍 Easy to Hard"],
    "math": ["Quick Math Quiz 🧮 Can You Solve All 5?", "Math Challenge 🧮 Easy to Hard", "Can You Solve These in 3 Seconds? 🧮"],
    "trivia": ["{t} 🧠 Can You Get 5/5?", "{t} 🧠 How Many Can You Get?", "{t} 🧠 Test Your Brain!"],
    "truefalse": ["True or False? {t} ✅❌", "True or False: {t} 🧠", "{t}: True or False? ✅❌"],
}
TAGS = {
    "flags": ["flag quiz", "guess the flag", "geography quiz", "countries"],
    "math": ["math quiz", "math challenge", "brain teaser", "mental math"],
    "trivia": ["trivia", "general knowledge quiz", "trivia questions"],
    "truefalse": ["true or false", "true or false quiz", "fun facts"],
}


def build(day, slot, fmt):
    rng = random.Random(f"quiz-{day}-{slot}")
    pack_path, pack = None, None
    if fmt in ("trivia", "truefalse"):
        pack_path, pack = take_pack(fmt, day.isoformat(), slot)
        if not pack:
            print(f"no {fmt} pack in quizzes/new, making a {'flags' if fmt == 'trivia' else 'math'} quiz instead")
            fmt = "flags" if fmt == "trivia" else "math"
    if fmt == "flags":
        qs = flag_questions(day, slot, rng)
        title, hook_say = HOOKS["flags"]
    elif fmt == "math":
        qs = math_questions(rng)
        title, hook_say = HOOKS["math"]
    else:
        qs = pack_questions(pack)
        title = ["TRUE OR", "FALSE?"] if fmt == "truefalse" else two_lines(pack["title"])
        hook_say = (f"True or false? {pack['title']}! Can you get all five?" if fmt == "truefalse"
                    else f"{pack['title']}! Can you get all five?")

    b = Builder()
    say = lambda at, text: b.say(at, text, voice=HOST, speed=HOST_SPEED)  # noqa: E731
    b.sfx.append((0.05, "whoosh"))
    end = 0.25 + say(0.25, hook_say) + 0.3
    b.scene(0, end, type="hook", title=title, sub="CAN YOU GET 5/5?")
    b.t = end
    for i, q in enumerate(qs):
        start = b.t
        b.sfx.append((start + 0.05, "whoosh"))
        cur = 0.3 + say(start + 0.3, q["say"]) + 0.15
        timer_at = cur
        for k in range(int(THINK)):
            b.sfx.append((start + cur + k, "tick"))
        reveal = cur + THINK
        b.sfx.append((start + reveal, "ding"))
        b.sfx.append((start + reveal + 0.05, "sparkle"))
        cur = reveal + 0.25 + say(start + reveal + 0.25, q["reveal"]) + 0.45
        b.scene(start, start + cur, type="question", kind=q["kind"], n=i + 1, text=q["text"], flag=q.get("flag"),
                options=q["options"], answer=q["answer"], timerAt=b.f(timer_at), timerLen=b.f(timer_at + THINK) - b.f(timer_at),
                revealAt=b.f(reveal), note=q.get("note"))
        b.t = start + cur
    start = b.t
    b.sfx.append((start + 0.1, "cheer"))
    end = start + 0.2 + say(start + 0.2, "How many did you get? Comment your score!") + 1.4
    b.scene(start, end, type="end")
    b.t = end
    b.music = [(0, b.t, lambda length, work: quiz_music(length, work, f"music-{day}-{slot}"))]
    b.music_gain = 0.22

    name = pack["title"] if pack else ""
    meta = {
        "title": rng.choice(TITLES[fmt]).format(t=name) + " #shorts",
        "description": "\n".join([
            "How many did you get? Comment your score below! 👇",
            "A new quiz every day on Brain Snack Quiz. Follow so you don't miss one!",
            "",
            "#quiz #trivia #shorts #" + TAGS[fmt][0].replace(" ", ""),
        ]),
        "tags": TAGS[fmt] + ["quiz", "trivia", "brain snack quiz"],
    }
    return b, qs, fmt, pack_path, meta


def write_audio(b, work, name):
    """Mixes the Short's audio into public/audio/<name>.wav and returns its path for staticFile()."""
    data = mix(b, work)
    folder = os.path.join(PUBLIC, "audio")
    os.makedirs(folder, exist_ok=True)
    for old in glob.glob(os.path.join(folder, "*.wav")):
        os.remove(old)  # keep the Remotion bundle small
    with wave.open(os.path.join(folder, f"{name}.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())
    return f"audio/{name}.wav"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=dt.date.today().isoformat())
    p.add_argument("--slot", type=int, choices=[1, 2], default=1)
    p.add_argument("--format", choices=FORMATS, help="override the daily rotation")
    a = p.parse_args()
    day = dt.date.fromisoformat(a.date)
    name = f"{a.date}-q{a.slot}"
    work = os.path.join(BUILD, name)
    os.makedirs(work, exist_ok=True)
    b, qs, fmt, pack_path, meta = build(day, a.slot, a.format or format_for(day, a.slot))

    shutil.rmtree(os.path.join(PUBLIC, "flags"), ignore_errors=True)
    os.makedirs(os.path.join(PUBLIC, "flags"))
    for q in qs:
        if q.get("flag"):
            shutil.copy(os.path.join(FLAGS, os.path.basename(q["flag"])), os.path.join(PUBLIC, q["flag"]))
    props = {"durationInFrames": b.f(b.t), "audio": write_audio(b, work, name), "theme": THEMES[fmt], "total": len(qs),
             "scenes": b.scenes}
    with open(os.path.join(work, "props.json"), "w") as fh:
        json.dump(props, fh)
    with open(os.path.join(work, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    if pack_path and os.path.dirname(pack_path) != os.path.join(QUIZ_DIR, "used", a.date):  # archive the pack
        used = os.path.join(QUIZ_DIR, "used", a.date)
        os.makedirs(used, exist_ok=True)
        os.rename(pack_path, os.path.join(used, f"q{a.slot}-{os.path.basename(pack_path)}"))
    print(f"quiz {a.slot} {fmt} {a.date}: {b.t:.1f}s, {len(qs)} questions, answers {[q['answer'] for q in qs]}")


if __name__ == "__main__":
    main()
