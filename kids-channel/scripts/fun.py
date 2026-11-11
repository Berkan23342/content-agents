"""Plans and voices the daily "fun" Bubbly Kids TV video (5+ minutes), uploaded next to the learning episode.

Formats rotate by episode number:
  story   two short animated stories (original plots, plus a retelling of Aesop's public-domain race fable)
  eggs    surprise eggs: patterned eggs crack open to reveal animals and toys
  dance   a sensory dance party with freeze-dance breaks, set to public-domain melodies
  shadow  guess the shadow: a silhouette, a hint, a countdown, then the reveal

Writes build/<date>-fun/{props,meta}.json and public/audio/<date>-fun.wav (same layout as scripts/episode.py).
Run with .venv/bin/python scripts/fun.py --date YYYY-MM-DD [--format story|eggs|dance|shadow]
"""
import argparse
import datetime as dt
import glob
import json
import math
import os
import random

import numpy as np
import soundfile as sf

from storycheck import CHARACTERS, PROP_ICONS, StoryError, check_against, check_story, estimate_seconds, kind_for
from episode import (ANIMALS, BUILD, DANCE_BPM, FIRST_EPISODE, FPS, GENTLE_SONGS, MIN_SECONDS, NUMBER_WORDS, PALETTE, SR,
                     Builder, an, fmt, look_for, write_audio, write_json)

FORMATS = ["story", "eggs", "dance", "story", "shadow"]

GROUND = 900  # where the characters' feet touch the grass
SIZE = 420  # full-body character height
OFF_L, OFF_R = -260, 2180

# name: (Kokoro voice, pitch lift, sound, colour). Mostly female voices; the user wants only a few male ones.
CAST = {
    "chick": ("af_bella", 1.25, "Cheep cheep!", "#FF8A1F"),
    "bunny": ("af_kore", 1.2, "Hop hop!", "#FF6FB5"),
    "duck": ("af_aoede", 1.15, "Quack quack!", "#FF8A1F"),
    "cat": ("af_sarah", 1.12, "Meow!", "#F08A24"),
    "pig": ("bf_emma", 1.1, "Oink oink!", "#FF6FB5"),
    "sheep": ("bf_isabella", 1.12, "Baa baa!", "#9B5CFF"),
    "frog": ("af_nova", 1.18, "Ribbit!", "#3CC75A"),
    "dog": ("af_jessica", 1.05, "Woof woof!", "#A0632F"),
    "cow": ("af_river", 0.96, "Moo!", "#2F8CFF"),
    "lion": ("am_fenrir", 0.95, "Roar!", "#E8962F"),
    "owl": ("bf_lily", 1.0, "Hoo hoo!", "#A0632F"),
    "turtle": ("bm_george", 0.97, "Hello!", "#2F8F45"),
    "bear": ("am_fenrir", 1.02, "Grrr!", "#9A6235"),
}

# animals with a sound line, for eggs and shadows: icon, name, line, bubble, colour
assert set(CAST) == CHARACTERS, "keep storycheck.CHARACTERS in sync with CAST"

CRITTERS = list(ANIMALS) + [
    ("bunny", "bunny", "The bunny goes hop, hop, hop!", "Hop hop!", "#FF6FB5"),
    ("bear", "bear", "The bear says grrr!", "Grrr!", "#9A6235"),
    ("turtle", "turtle", "The turtle goes slow and steady!", "Hello!", "#2F8F45"),
]

COLOR_WORDS = [("red", "#FF3B3B"), ("blue", "#2F8CFF"), ("yellow", "#FFC92E"), ("purple", "#9B5CFF"),
               ("green", "#3CC75A"), ("pink", "#FF6FB5"), ("orange", "#FF8A1F")]


def icon(name, color=None):
    return {"kind": "icon", "value": name, "color": color or CAST.get(name, (0, 0, 0, "#FF8A1F"))[3]}


def body(hero):
    return {**hero, "body": True}


def mouth(clip):
    """Per-frame mouth opening 0-9 from the loudness of a voice clip, for lip-sync."""
    step = SR / FPS
    n = max(1, int(len(clip) / step))
    rms = np.array([np.sqrt(np.mean(clip[int(k * step):int((k + 1) * step)] ** 2)) for k in range(n)])
    top = np.percentile(rms, 90) + 1e-6
    return "".join(str(min(9, int(v / top * 9))) for v in rms)


# ---------------------------------------------------------------- story staging
class Shot:
    """One story shot: a backdrop, a cast on stage and a timeline of lines and moves (seconds from the shot start)."""

    def __init__(self, b, bg):
        self.b, self.bg = b, bg
        self.start = b.t
        self.cur = 0.5
        self.actors, self.names, self.props, self.bubbles = [], {}, [], []
        self.cam = []  # {"at", "until", "x"}: the camera leans towards whoever is speaking

    @staticmethod
    def fr(sec):
        return round(sec * FPS)

    def add(self, name, x, y=GROUND, size=SIZE, fly=False, asleep=False):
        a = {"hero": icon(name), "size": size, "keys": [{"t": 0, "x": x, "y": y}], "acts": [], "fly": fly, "talk": []}
        if asleep:
            a["acts"].append({"t": 0, "kind": "sleep"})
        self.names[name] = len(self.actors)
        self.actors.append(a)

    def _go(self, keys, x, y, at, dur):
        last = keys[-1]
        t0 = max(at, last["t"] / FPS)
        if last["t"] < self.fr(t0):
            keys.append({"t": self.fr(t0), "x": last["x"], "y": last["y"]})
        keys.append({"t": self.fr(t0 + dur), "x": x, "y": last["y"] if y is None else y})
        return t0 + dur

    def move(self, name, x, y=None, speed=520, dur=None, at=None, wait=False):
        """Walks (or flies) an actor to (x, y); returns the arrival time."""
        keys = self.actors[self.names[name]]["keys"]
        last = keys[-1]
        dist = math.hypot(x - last["x"], (last["y"] if y is None else y) - last["y"])
        end = self._go(keys, x, y, self.cur if at is None else at, dur or max(0.6, dist / speed))
        if wait:
            self.cur = end
        return end

    def enter(self, name, x, side="left", size=SIZE, speed=520, wait=True, y=GROUND):
        self.add(name, OFF_L if side == "left" else OFF_R, y, size)
        return self.move(name, x, speed=speed, wait=wait)

    def leave(self, name, side="right", speed=620, wait=False):
        return self.move(name, OFF_R if side == "right" else OFF_L, speed=speed, wait=wait)

    def act(self, name, kind, at=None):
        self.actors[self.names[name]]["acts"].append({"t": self.fr(self.cur if at is None else at), "kind": kind})

    def say(self, text, gap=0.4, speed=0.92):
        d = self.b.say(self.start + self.cur, text, speed=speed)
        self.cur += d + gap
        return d

    def x_at(self, name, sec):
        """Where an actor stands at a moment (linear between its keys; close enough for the camera)."""
        keys, f = self.actors[self.names[name]]["keys"], self.fr(sec)
        if f <= keys[0]["t"]:
            return keys[0]["x"]
        for a, b in zip(keys, keys[1:]):
            if f < b["t"]:
                return a["x"] + (b["x"] - a["x"]) * (f - a["t"]) / max(1, b["t"] - a["t"])
        return keys[-1]["x"]

    def line(self, name, text, bubble=None, act=None, gap=0.35, gain=1.0):
        voice, pitch, _, color = CAST[name]
        d = self.b.say(self.start + self.cur, text, voice=voice, speed=0.9, pitch=pitch, gain=gain)
        self.cam.append({"at": self.fr(self.cur), "until": self.fr(self.cur + d), "x": round(self.x_at(name, self.cur))})
        self.actors[self.names[name]]["talk"].append({"at": self.fr(self.cur), "m": mouth(self.b.voices[-1][1])})
        if bubble:
            self.bubbles.append({"actor": self.names[name], "text": bubble, "color": color,
                                 "at": self.fr(self.cur), "until": self.fr(self.cur + d + 0.35)})
        if act:
            self.act(name, act)
        self.cur += d + gap
        return d

    def sfx(self, kind, at=None):
        self.b.sfx.append((self.start + (self.cur if at is None else at), kind))

    def prop(self, hero, x, y, size=200, at=None, float_=False):
        self.props.append({"hero": hero, "size": size, "keys": [{"t": 0, "x": x, "y": y}],
                           "at": self.fr(self.cur if at is None else at), "float": float_})
        return len(self.props) - 1

    def prop_move(self, i, x, y, dur, at=None, wait=False):
        end = self._go(self.props[i]["keys"], x, y, self.cur if at is None else at, dur)
        if wait:
            self.cur = end
        return end

    def hide(self, i, at=None):
        self.props[i]["until"] = self.fr(self.cur if at is None else at)

    def wait_until(self, sec):
        self.cur = max(self.cur, sec)

    def pause(self, sec):
        self.cur += sec

    def done(self, tail=0.6):
        end = self.start + self.cur + tail
        self.b.scene(self.start, end, type="story", bg=self.bg, actors=self.actors, props=self.props, bubbles=self.bubbles, title=None,
                     cam=self.cam)
        self.b.t = end


def cap(name):
    return name.capitalize()


# ---------------------------------------------------------------- stories
def story_balloon(b, rng):
    hero = rng.choice(["chick", "bunny", "cat", "pig", "duck"])
    cname, chex = rng.choice(COLOR_WORDS)
    friends = rng.sample([a for a in ["cow", "pig", "sheep", "dog", "frog", "duck", "cat", "lion", "bear"] if a != hero], 3)
    H = cap(hero)
    balloon = {"kind": "balloon", "value": "", "color": chex}

    s = Shot(b, "park")
    arrive = s.enter(hero, 760, wait=False)
    bal = s.prop(balloon, OFF_L + 160, GROUND - SIZE - 40, size=300, at=0, float_=True)
    s.prop_move(bal, 920, GROUND - SIZE - 40, arrive - s.cur, at=s.cur)
    s.say(f"Once upon a time, a little {hero} had a shiny {cname} balloon.")
    s.wait_until(arrive)
    s.line(hero, f"I love my {cname} balloon!", "I love my balloon!", act="jump")
    s.sfx("whoosh")
    s.prop_move(bal, 2150, -320, 2.6)
    s.say("But then... whoosh! The wind blew very hard!")
    s.line(hero, "Oh no! My balloon! Come back!", "Oh no!", act="shake")
    s.say(f"The balloon flew far, far away. {H} went to look for it.")
    s.leave(hero, wait=True)
    s.done(0.2)

    clues = [("over the pond", "pond"), ("to the park", "park"), ("into the forest", "forest")]
    places = ["farm", "pond", "park"]
    for i, f in enumerate(friends):
        s = Shot(b, places[i])
        s.add(f, 1320)
        arrive = s.enter(hero, 640, wait=False)
        s.say(f"{H} walked and walked, and met {an(f)} {f}.")
        s.wait_until(arrive)
        s.line(hero, f"Hello, {cap(f)}! Have you seen my {cname} balloon?", "Have you seen my balloon?", act="wave")
        clue = clues[i][0]
        s.line(f, f"{CAST[f][2]} Yes! It flew {clue}!", f"It flew {clue}!", act="jump")
        s.line(hero, f"Thank you, {cap(f)}!", "Thank you!", act="jump")
        s.leave(hero, wait=True)
        s.done(0.2)

    s = Shot(b, "forest")
    bal = s.prop(balloon, 1560, 330, size=260, at=0, float_=True)
    s.add("owl", 1250, size=330, fly=True)
    arrive = s.enter(hero, 620, wait=False)
    s.say(f"{H} walked into the forest. Look! There is the {cname} balloon, up in a tall tree!")
    s.wait_until(arrive)
    s.line(hero, "My balloon! But it's so high. I can't reach it!", "It's so high!", act="shake")
    s.line("owl", "Hoo hoo! Don't worry. I can help you!", "I can help!", act="jump")
    s.sfx("whoop")
    up = s.move("owl", 1470, 480, dur=1.6)
    s.say("Owl flapped and flew up, up, up!")
    s.wait_until(up)
    t = s.cur
    down = s.move("owl", 880, GROUND, dur=2.2, at=t)
    s.prop_move(bal, 900, GROUND - 330 - 140, 2.2, at=t)
    s.say("And Owl brought the balloon back down!")
    s.wait_until(down)
    s.sfx("sparkle")
    s.line(hero, "My balloon! Thank you, Owl!", "Thank you, Owl!", act="jump")
    for k, f in enumerate(friends):
        s.enter(f, [1200, 1450, 1700][k], side="right", size=360, speed=760, wait=False)
        s.pause(0.45)
    s.pause(1.2)
    s.say("All the friends came to see. Everyone was so happy!")
    for k, who in enumerate(friends + [hero, "owl"]):
        s.act(who, "jump", at=s.cur + k * 0.15)
    s.sfx("ding")
    s.say("Friends always help each other. The end!")
    s.done(1.4)
    return {"title": "The Lost Balloon", "cast": [hero, "owl"] + friends[:1],
            "lesson": "Friends help each other", "summary": f"A little {hero} follows the wind to find a lost {cname} balloon."}


FOODS = [("apple", "apple", "apples", "#FF3B3B"), ("orange", "orange", "oranges", "#FF8A1F"), ("cookie", "cookie", "cookies", "#C98B55"),
         ("strawberry", "strawberry", "strawberries", "#FF3B4F"), ("banana", "banana", "bananas", "#FFD93D")]
GIFTS = [("gift", "#FF6FB5", "a present"), ("flower", "#9B5CFF", "a pretty flower"), ("cake", "#FF6FB5", "a yummy cake"),
         ("icecream", "#FF6FB5", "an ice cream"), ("balloon", "#2F8CFF", "a balloon"), ("ball", "#FF3B3B", "a ball")]


def story_sharing(b, rng):
    hero = rng.choice(["bear", "pig", "bunny", "dog"])
    name, one, many, color = rng.choice(FOODS)
    n = 4
    friends = rng.sample([a for a in ["cat", "duck", "chick", "sheep", "frog", "cow", "lion", "owl"] if a != hero], n)
    H = cap(hero)
    xs = [560 + (k - (n - 1) / 2) * 165 for k in range(n)]
    food = icon(name, color)

    s = Shot(b, "park")
    arrive = s.enter(hero, 560, wait=False)
    s.say(f"One sunny day, {H} found some yummy {many}!")
    s.wait_until(arrive)
    s.say("Let's count them together!")
    for k in range(n):
        s.prop(food, xs[k], 300, size=150)
        s.sfx("pop")
        s.say(f"{NUMBER_WORDS[k + 1]}!", gap=0.3)
    s.line(hero, f"{NUMBER_WORDS[n]} {many}! All for me! Yummy!", f"{NUMBER_WORDS[n]} {many}!", act="jump")
    s.done(0.3)

    left = n
    for f in friends:
        s = Shot(b, "park")
        s.add(hero, 560)
        foods = [s.prop(food, xs[k], 300, size=150, at=0) for k in range(left)]
        arrive = s.enter(f, 1320, side="right", wait=False)
        s.wait_until(arrive - 0.3)
        s.line(f, f"{CAST[f][2]} Hello, {H}! I am so hungry!", "I'm so hungry!", act="shake")
        s.say(f"{H} thought for a moment...", gap=0.7)
        s.line(hero, f"Here you go, {cap(f)}! One {one} for you!", "One for you!", act="jump")
        give = foods[-1]
        s.sfx("whoop")
        s.prop_move(give, 1200, GROUND - 150, 1.1, wait=True)
        left -= 1
        s.line(f, f"Thank you, {H}! You are so kind!", "Thank you!", act="jump")
        s.say(f"Now {H} has {NUMBER_WORDS[left].lower()} {one if left == 1 else many}.")
        t = s.cur
        end = s.leave(f, wait=False)
        s.prop_move(give, OFF_R - 120, GROUND - 150, end - t, at=t)
        s.wait_until(end - 0.8)
        s.done(0.2)

    s = Shot(b, "park")
    s.add(hero, 560)
    s.line(hero, f"Oh! No more {many} for me.", f"No more {many}!", act="shake")
    s.say("But then... look who came back!")
    spots = [1020, 1260, 1500, 1740]
    for k, f in enumerate(friends):
        s.enter(f, spots[k], side="right", size=340, speed=800, wait=False)
        s.pause(0.4)
    s.pause(1.4)
    for k, (g, gc, words) in enumerate(rng.sample(GIFTS, n)):
        f = friends[k]
        gi = s.prop(icon(g, gc), spots[k], GROUND - 340 - 70, size=130)
        s.sfx("pop")
        s.line(f, f"Here, {H}! I brought you {words}!", "For you!", act="jump")
        s.prop_move(gi, xs[k], 300, 1.0)
    s.pause(0.8)
    s.line(hero, "Wow! Thank you, friends! I love you all!", "Thank you, friends!", act="jump")
    s.say("When we share, everyone is happy.")
    for k, who in enumerate(friends + [hero]):
        s.act(who, "jump", at=s.cur + k * 0.15)
    s.sfx("ding")
    s.say("Sharing is caring! The end!")
    s.done(1.4)
    return {"title": "Sharing Is Caring", "cast": [hero] + friends[:2], "lesson": "Sharing is caring",
            "summary": f"{H} shares {many} with hungry friends, and counts down from {NUMBER_WORDS[n].lower()} to zero."}


STAR_SPOTS = [(300, 210), (620, 130), (930, 240), (1180, 120), (1400, 300), (160, 380)]


def story_bedtime(b, rng):
    animals = rng.sample(["cow", "sheep", "pig", "duck", "chick", "cat", "dog", "bunny"], 5)
    xs = [360, 660, 960, 1260, 1560]
    star = icon("star", "#FFE14D")

    s = Shot(b, "dusk")
    for k, a in enumerate(animals):
        s.add(a, xs[k], size=330)
    s.say("The sun is going down on the little farm.", speed=0.86)
    s.say("The sky is orange and pink. It's almost time for bed.", speed=0.86)
    s.line(animals[0], "Aaah... I'm so sleepy!", "I'm sleepy!", gain=0.85)
    s.say("Let's say goodnight to all our friends.", speed=0.86)
    s.done(0.6)

    for k, a in enumerate(animals):
        s = Shot(b, "night")
        for j, z in enumerate(animals[:k]):
            s.add(z, xs[j], size=330, asleep=True)
        for j in range(k):
            s.prop(star, *STAR_SPOTS[j], size=90, at=0, float_=True)
        s.add(a, xs[k], size=330)
        s.say(f"Goodnight, little {a}.", speed=0.84, gap=0.5)
        s.line(a, f"{CAST[a][2]} Goodnight!", "Goodnight!", gain=0.8)
        s.act(a, "sleep")
        s.pause(0.8)
        s.prop(star, *STAR_SPOTS[k], size=90, float_=True)
        s.sfx("sparkle")
        s.say(f"{NUMBER_WORDS[k + 1]} little star{'' if k == 0 else 's'}, twinkling in the sky.", speed=0.84)
        s.done(0.8)

    s = Shot(b, "night")
    for j, z in enumerate(animals):
        s.add(z, xs[j], size=330, asleep=True)
    for j in range(len(animals)):
        s.prop(star, *STAR_SPOTS[j], size=90, at=0, float_=True)
    s.say("The moon is shining. The stars are twinkling.", speed=0.84, gap=0.8)
    s.say("All the animals are fast asleep.", speed=0.84, gap=1.0)
    s.say("Sweet dreams, little one. Goodnight.", speed=0.82)
    s.done(3.0)
    return {"title": "Goodnight, Little Farm", "cast": animals[:3], "lesson": "A calm bedtime routine",
            "summary": "The farm animals say goodnight one by one while the stars come out."}


def story_rain(b, rng):
    a, c = rng.sample(["cat", "dog", "bunny", "pig", "bear", "sheep"], 2)
    A, C = cap(a), cap(c)
    ball = icon("ball", rng.choice(PALETTE))

    s = Shot(b, "park")
    s.enter(a, 600, wait=False)
    arrive = s.enter(c, 1320, side="right", wait=False)
    s.say(f"{A} and {C} were playing ball in the park.")
    s.wait_until(arrive)
    bl = s.prop(ball, 780, GROUND - 70, size=140)
    for k, (who, text, bub) in enumerate([(a, "Catch the ball!", "Catch!"), (c, "Got it! Your turn!", "Your turn!"), (a, "Wheee! This is fun!", "Wheee!")]):
        s.line(who, text, bub, act="jump")
        s.sfx("boing")
        s.prop_move(bl, 1140 if k % 2 == 0 else 780, GROUND - 70, 0.9, wait=True)
    s.done(0.3)

    s = Shot(b, "rain")
    s.add(a, 520)
    s.add(c, 1400)
    s.sfx("thunder", at=0.3)
    s.say("Oh! Dark clouds! Drip, drop, drip, drop. It's raining!")
    s.act(a, "shake")
    s.act(c, "shake", at=s.cur + 0.2)
    s.line(a, "Oh no! We're getting all wet!", "We're getting wet!")
    umb = s.prop(icon("umbrella", "#FF6FB5"), OFF_L, GROUND - SIZE - 80, size=340, at=0)
    t = s.cur
    arrive = s.enter("duck", 960, wait=False)
    s.prop_move(umb, 960, GROUND - SIZE - 80, arrive - t, at=t)
    s.wait_until(arrive)
    s.line("duck", "Quack quack! Come under my umbrella!", "Come under my umbrella!", act="jump")
    s.move(a, 760)
    s.move(c, 1160, wait=True)
    s.say("Duck shared the umbrella. Now everyone is nice and dry!")
    s.line(c, "Thank you, Duck!", "Thank you!", act="jump")
    s.done(0.4)

    s = Shot(b, "rain")
    s.prop(icon("umbrella", "#FF6FB5"), 960, GROUND - SIZE - 120, size=560, at=0)
    for who, x in ((a, 760), ("duck", 960), (c, 1160)):
        s.add(who, x)
    arrive = s.enter("frog", 330, wait=False)
    s.say("Then Frog came hopping by.")
    s.wait_until(arrive)
    s.line("frog", "Ribbit! I love the rain! Splash, splash!", "Splash, splash!", act="jump")
    for k in range(2):
        s.sfx("splash")
        s.act("frog", "jump")
        s.pause(0.8)
    s.say("Let's count the raindrops!")
    for k in range(5):
        s.prop(icon("drop", "#2F8CFF"), 360 + k * 300, 200 + (k % 2) * 60, size=120, float_=True)
        s.sfx("pop")
        s.say(f"{NUMBER_WORDS[k + 1]}!", gap=0.3)
    s.done(0.4)

    s = Shot(b, "park")
    for who, x in ((a, 560), ("duck", 820), (c, 1080), ("frog", 1340)):
        s.add(who, x, size=380)
    s.say("The rain stopped, and the sun came out again!")
    s.prop(icon("rainbow"), 960, 330, size=640)
    s.sfx("sparkle")
    s.say("Look! A beautiful rainbow!")
    s.say("Red, orange, yellow, green, blue, and purple!")
    for k, who in enumerate([a, "duck", c, "frog"]):
        s.act(who, "jump", at=s.cur + k * 0.15)
    s.line(a, "Hooray! What a fun rainy day!", "Hooray!")
    s.sfx("ding")
    s.say("The end!")
    s.done(1.4)
    return {"title": "Rainy Day Fun", "cast": [a, "duck", c], "lesson": "Sharing an umbrella and finding a rainbow",
            "summary": f"{A} and {C} get caught in the rain, Duck shares an umbrella, and a rainbow appears."}


def story_race(b, rng):
    friends = rng.sample(["cow", "pig", "sheep", "duck", "dog", "cat", "frog", "chick"], 2)

    s = Shot(b, "park")
    arrive = s.enter("bunny", 1250, side="right", speed=1100, wait=False)
    s.wait_until(arrive)
    s.line("bunny", "I'm the fastest in the whole park! Who wants to race me?", "Who wants to race?", act="jump")
    arrive = s.enter("turtle", 640, speed=260, wait=False)
    s.say("Slowly, slowly, Turtle came along.")
    s.wait_until(arrive)
    s.line("turtle", "I will race you, Bunny!", "I will race you!", act="wave")
    s.line("bunny", "Ha ha ha! You are so slow, Turtle!", "Ha ha! You're so slow!", act="spin")
    s.line("turtle", "Slow and steady, Bunny. Let's race!", "Let's race!")
    s.done(0.4)

    s = Shot(b, "park")
    s.add("turtle", 300)
    s.add("bunny", 600)
    s.add(friends[0], 1500, size=360)
    s.add(friends[1], 1740, size=360)
    for word in ("Ready...", "Set..."):
        s.sfx("tick")
        s.say(word, gap=0.3)
    s.sfx("whoosh")
    s.say("Go!", gap=0.1)
    s.move("bunny", OFF_R, speed=1700)
    slow = s.move("turtle", 1000, speed=110)
    s.say("Zoom! Bunny ran super fast!")
    s.say("And Turtle walked... slow... and steady.", speed=0.85)
    s.wait_until(slow)
    s.done(0.3)

    s = Shot(b, "forest")
    s.enter("bunny", 1340, speed=1500, wait=True)
    s.line("bunny", "Turtle is so slow! I have time for a little nap.", "Nap time!")
    s.act("bunny", "sleep")
    s.say("Bunny closed both eyes and fell fast asleep. Zzz...")
    arrive = s.enter("turtle", 640, speed=150, wait=False)
    s.say("Then along came Turtle. Step, step, step.")
    s.wait_until(arrive)
    s.line("turtle", "Slow and steady... slow and steady.", "Slow and steady!")
    gone = s.leave("turtle", speed=200)
    s.say("Turtle walked right past the sleeping bunny!")
    s.wait_until(gone - 3)
    s.done(0.3)

    s = Shot(b, "park")
    s.add(friends[0], 1420, size=360)
    s.add(friends[1], 1680, size=360)
    arrive = s.enter("turtle", 1080, speed=170, wait=False)
    s.line(friends[0], f"{CAST[friends[0]][2]} Look! Turtle is almost here!", "Look!", act="jump")
    s.line(friends[1], "Go, Turtle, go!", "Go, Turtle, go!", act="jump")
    s.wait_until(arrive)
    s.sfx("ding")
    s.prop(icon("crown", "#FFC92E"), 1080, GROUND - SIZE - 50, size=150)
    s.say("Hooray! Turtle won the race!")
    for k, who in enumerate(["turtle"] + friends):
        s.act(who, "jump", at=s.cur + k * 0.15)
    s.pause(0.6)
    s.enter("bunny", 700, speed=1500, wait=True)
    s.line("bunny", "Oh no! I took a nap, and you won! Good job, Turtle!", "You won, Turtle!", act="shake")
    s.line("turtle", "Thank you, Bunny! Let's be friends!", "Let's be friends!", act="jump")
    s.say("Slow and steady wins the race. The end!")
    s.done(1.4)
    return {"title": "The Big Race", "cast": ["bunny", "turtle"], "lesson": "Slow and steady wins the race",
            "summary": "A speedy bunny and a steady turtle race through the park (a retelling of Aesop's fable)."}


STORIES = {"balloon": story_balloon, "sharing": story_sharing, "rain": story_rain, "race": story_race, "bedtime": story_bedtime}
STORY_TITLES = {"balloon": "The Lost Balloon", "sharing": "Sharing Is Caring", "rain": "Rainy Day Fun",
                "race": "The Big Race", "bedtime": "Goodnight, Little Farm"}


# ---------------------------------------------------------------- stories written as JSON scripts (by the daily agent)
STORY_DIR = os.path.join(os.path.dirname(BUILD), "stories")
def prop_hero(p):
    if p["icon"] == "balloon":
        return {"kind": "balloon", "value": "", "color": p.get("color", "#FF3B3B")}
    return icon(p["icon"], p.get("color"))


def story_script(spec):
    """Turns a checked story script into a story function like the built-in ones."""
    def play(b, rng):
        for shot in spec["shots"]:
            s = Shot(b, shot["bg"])
            arrive = {}
            props = {}
            for a in shot.get("actors", []):
                s.add(a["name"], a.get("x", 960), y=a.get("y", GROUND), size=a.get("size", SIZE), fly=a.get("fly", False), asleep=a.get("asleep", False))
            for p in shot.get("props", []):
                props[p["id"]] = s.prop(prop_hero(p), p["x"], p["y"], size=p.get("size", 160), at=0, float_=p.get("float", False))
            for st in shot["steps"]:
                kind = next(iter(st))
                gap = st.get("gap", 0.4)
                if kind == "say":
                    s.say(st["say"], gap=gap, speed=0.86 if st.get("slow") else 0.92)
                elif kind == "line":
                    s.line(st["line"], st["text"], st.get("bubble"), act=st.get("act"), gap=gap)
                elif kind == "enter":
                    s.add(st["enter"], OFF_L if st.get("side", "left") == "left" else OFF_R, y=st.get("y", GROUND),
                          size=st.get("size", SIZE), fly=st.get("fly", False))
                    arrive[st["enter"]] = s.move(st["enter"], st.get("x", 960), st.get("y"), speed=st.get("speed", 520), wait=st.get("wait", False))
                elif kind == "move":
                    arrive[st["move"]] = s.move(st["move"], st["x"], st.get("y"), speed=st.get("speed", 520), dur=st.get("dur"), wait=st.get("wait", False))
                elif kind == "leave":
                    arrive[st["leave"]] = s.leave(st["leave"], st.get("side", "right"), speed=st.get("speed", 620), wait=st.get("wait", False))
                elif kind == "arrive":
                    s.wait_until(arrive.get(st["arrive"], s.cur))
                elif kind == "act":
                    names = list(s.names) if st["act"] == "all" else [st["act"]]
                    for k, n in enumerate(names):
                        s.act(n, st["kind"], at=s.cur + k * 0.15)
                elif kind == "prop":
                    props[st["prop"]] = s.prop(prop_hero(st), st["x"], st["y"], size=st.get("size", 160), float_=st.get("float", False))
                elif kind == "prop_move":
                    s.prop_move(props[st["prop_move"]], st["x"], st["y"], st.get("dur", 1.0), wait=st.get("wait", False))
                elif kind == "hide":
                    s.hide(props[st["hide"]])
                elif kind == "sfx":
                    s.sfx(st["sfx"])
                elif kind == "pause":
                    s.pause(st["pause"])
            s.done(shot.get("tail", 0.6))
        return {"title": spec["title"], "cast": spec.get("cast") or [a["name"] for a in spec["shots"][0].get("actors", [])][:3],
                "lesson": spec["lesson"], "summary": spec["summary"]}
    return play


def load_script(path):
    with open(path) as fh:
        spec = json.load(fh)
    check_story(spec)
    return spec


def scripted_stories(date, limit, want=None):
    """Story scripts for a date: the ones already used for it, or the oldest waiting in stories/new, those of the
    day's kind (`want`) first."""
    used = os.path.join(STORY_DIR, "used", date)
    if os.path.isdir(used):
        paths = sorted(glob.glob(os.path.join(used, "*.json")))
    else:
        def kind(p):
            try:
                return json.load(open(p)).get("kind")
            except ValueError:
                return None
        paths = sorted(glob.glob(os.path.join(STORY_DIR, "new", "*.json")), key=lambda p: (kind(p) != want, p))[:limit]
    out = []
    for path in paths:
        try:
            spec = load_script(path)
            if os.path.dirname(path) != used:  # a new story must not repeat an earlier one
                check_against(path, spec)
            out.append((path, spec))
        except (StoryError, ValueError, KeyError) as e:
            print(f"skipping story {os.path.basename(path)}: {e}")
    return out


def intro(b, bg, title, heroes, lines, top="Bubbly Kids TV", start=1.2, **style):
    b.sfx.append((0.2, "whoop"))
    cur = start
    for text in lines:
        cur += b.say(cur, text) + 0.3
    end = cur + 0.6
    b.scene(0, end, type="title", bg=bg, top=top, title=title, heroes=heroes, **style)
    b.chapters.append((0, "Hello friends!"))
    b.t = end


def outro(b, bg, top):
    start = b.t
    b.chapters.append((start, "Bye bye!"))
    b.sfx.append((start + 0.3, "ding"))
    b.sfx.append((start + 0.5, "cheer"))
    d = b.say(start + 0.3, f"{top} Thank you for watching Bubbly Kids TV!")
    bye_at = 0.3 + d + 0.35
    d2 = b.say(start + bye_at, "Bye bye! See you next time!")
    end = start + bye_at + d2 + 2.6
    b.scene(start, end, type="outro", byeAt=b.f(bye_at), heroes=[], top=top, bg=bg)
    b.t = end


def dance_break(b, rng, crew, moves_pool):
    """Two sections of freeze-free dancing between stories; the music segment starts with it, on the beat."""
    start = b.t
    section = 8 * 4 * 60 / DANCE_BPM
    b.chapters.append((start, "Dance break!"))
    b.sfx.append((start + 0.1, "whoop"))
    b.say(start + 0.3, "Dance break! Let's stand up and dance!")
    for k in range(2):
        text, moves = moves_pool[k]
        at = 0.3 if k == 0 else 0.15
        if k:
            b.say(start + k * section + at, text)
        b.scene(start + k * section, start + (k + 1) * section, type="dance", bg="party", beat0=0, bpm=DANCE_BPM, crew=crew,
                formation=["line", "wave"][k], moves=moves, freezes=[],
                callouts=[{"text": "Dance break!" if k == 0 else text, "color": RAINBOW_TEXT[(k * 3) % 7], "at": b.f(at)}])
    b.t = start + 2 * section


STORY_SIZES = [(2, 1), (3, 1), (3, 2), (4, 2)]  # stories, dance breaks


SCRIPTS = []  # (path, spec) of the scripted stories chosen for this run, set by main()


def fmt_story(b, rng, ep_no, size):
    count, breaks = STORY_SIZES[size]
    order = list(STORIES)
    random.Random("bubbly-stories").shuffle(order)
    story_no = sum(1 for k in range(1, ep_no) if FORMATS[(k - 1) % len(FORMATS)] == "story")
    plays, titles, calm = {}, {}, set()
    keys = []
    for path, spec in SCRIPTS[:count]:
        key = "script:" + os.path.basename(path)
        plays[key], titles[key] = story_script(spec), spec["title"]
        if spec.get("calm"):
            calm.add(key)
        keys.append(key)
    for k in range(len(order)):
        if len(keys) >= count:
            break
        key = order[(story_no * 2 + k) % len(order)]
        plays[key], titles[key] = STORIES[key], STORY_TITLES[key]
        keys.append(key)
    calm.add("bedtime")
    keys.sort(key=lambda k: k in calm)  # the calm story always goes last
    titles = [titles[k] for k in keys]
    intro(b, "park", ["Story Time!"], [],
          ["Hello, friends! Welcome to Bubbly Kids TV!",
           f"It's story time! Today's stories are: {', and '.join(titles)}. Let's go!"])
    songs = list(GENTLE_SONGS)
    rng.shuffle(songs)
    stories = []
    crews = rng.sample(CREWS, 2)
    for i, key in enumerate(keys):
        if 0 < i <= breaks and key not in calm:
            start = b.t
            dance_break(b, rng, crews[i - 1], rng.sample(CALLOUTS, 2))
            b.music.append((start, b.t, rng.choice(DANCE_SONGS), "dance"))
        start = b.t
        b.chapters.append((start, titles[i]))
        card = len(b.scenes)
        b.sfx.append((start + 0.2, "sparkle"))
        d = b.say(start + 0.6, f"Story number {NUMBER_WORDS[i + 1].lower()}: {titles[i]}!")
        b.scene(start, start + d + 1.6, type="title", bg="dusk" if key in calm else "park", top=f"Story {i + 1}",
                title=[titles[i]], heroes=[])
        b.t = start + d + 1.6
        info = plays[key](b, rng)
        b.scenes[card]["heroes"] = [body(icon(c)) for c in info["cast"]]
        b.music.append((start, b.t, "twinkle" if key in calm else songs[i % len(songs)], "lullaby" if key in calm else "gentle"))
        stories.append(info)
    b.scenes[0]["heroes"] = [body(icon(c)) for c in dict.fromkeys(c for s in stories for c in s["cast"][:2])][:5]
    outro(b, "dusk" if keys[-1] in calm else "day", "The end!")
    s0, _, song, style = b.music[-1]
    b.music[-1] = (s0, b.t, song, style)
    b.music[0] = (0, *b.music[0][1:])
    b.music_gain = 0.24

    t1 = stories[0]["title"]
    others = " & ".join(s["title"] for s in stories[1:])
    meta = {
        "title": f"{t1} & {others} | Story Time for Kids | Bubbly Kids TV",
        "lines": [f"📖 {s['title']}: {s['summary']} ({s['lesson']}.)" for s in stories],
        "intro": f"Story time with Bubbly Kids TV! 🎈 {len(stories)} gentle animated stories for toddlers and preschoolers.",
        "tags": ["kids stories", "story time", "bedtime stories", "stories for toddlers", "animated stories for kids",
                 "moral stories", "preschool", "cartoon for kids", "bubbly kids tv"],
    }
    thumb = {"title": ["Story Time!", t1], "heroes": [body(icon(c)) for c in stories[0]["cast"][:3]], "bg": "park"}
    return meta, thumb


# Each kind of daily story (scripts/storycheck.py ROTATION) has its own narrator, opening and music.
# narrators: Kokoro's best women's voices, in order of preference; a voice a character of the story uses is skipped
KIND_STYLE = {
    "adventure": dict(narrators=["af_heart", "af_nicole", "bf_emma"], label="Adventure Time!", color="#FF8A1F", rays="#FFE14D",
                      songs=["yankee", "macdonald"], hello="Are you ready for an adventure?"),
    "kindness": dict(narrators=["af_bella", "af_heart", "af_nicole"], label="A Kindness Story", color="#FF6FB5", rays="#FFD1E8",
                     songs=["mary", "london"], hello="Today's story is about being kind."),
    "learning": dict(narrators=["bf_emma", "af_nicole", "af_heart"], label="Let's Learn!", color="#2F8CFF", rays="#BDE3FF",
                     songs=["ode", "frere"], hello="Let's learn something new together!"),
    "funny": dict(narrators=["af_nicole", "af_bella", "af_heart"], label="A Funny Story", color="#3CC75A", rays="#D6F5C8",
                  songs=["macdonald", "hotcross"], hello="Get ready to giggle!"),
    "feelings": dict(narrators=["af_heart", "bf_emma", "af_bella"], label="A Feelings Story", color="#9B5CFF", rays="#E3D4FF",
                     songs=["london", "twinkle"], hello="Today's story is about feelings."),
    "bedtime": dict(narrators=["af_heart:0.6+bf_emma:0.4", "af_bella", "af_heart"], label="Bedtime Story", color="#5B6BFF",
                    rays="#C9D2FF", songs=["twinkle"], hello="It's time for a calm bedtime story."),
}


def narrator_for(kind, specs):
    cast = {CAST[c][0] for s in specs for c in s.get("cast", []) if c in CAST}
    options = KIND_STYLE[kind]["narrators"]
    return next((v for v in options if not set(p.partition(":")[0] for p in v.split("+")) & cast), options[-1])


def fmt_daily(b, rng, ep_no, specs, kind=None, weekly=False):
    """The daily video since 2026-11-08: new stories from the story writer, told from start to end. Usually one long
    story; while short stories from before the change are waiting, two or three of them. (The rotation of eggs, dance and
    shadow templates was dropped: YouTube treats look-alike videos as inauthentic.)"""
    outdoor = lambda bg: bg if bg not in ("night", "bedroom", "underwater") else "day"  # noqa: E731
    calm = bool(specs[-1].get("calm"))
    first_bg = specs[0]["shots"][0]["bg"]
    titles = [s["title"] for s in specs]
    heroes = [body(icon(c)) for c in dict.fromkeys(c for s in specs for c in s.get("cast", [])[:2])][:3]
    style = KIND_STYLE.get(kind or specs[0].get("kind") or "adventure", KIND_STYLE["adventure"])
    if weekly:  # Sunday's video: the whole week's stories, one after another
        style = dict(style, label="This Week's Stories", hello="Hello friends!")
    badge = {"badge": style["label"], "badgeColor": style["color"], "rays": style["rays"]}  # for the thumbnail
    # a short opening: viewers (and the suggested-videos panel) judge the first seconds, so one line and the title
    if weekly:
        intro(b, outdoor(first_bg), [f"{len(specs)} Stories", "in One!"], heroes,
              [f"Hello friends! Here are all {NUMBER_WORDS[len(specs)].lower()} stories from this week, one after another!"],
              top=style["label"], topColor=style["color"], rays=style["rays"], start=0.5)
    else:
        intro(b, outdoor(first_bg), [titles[0]] if len(specs) == 1 else ["Story Time!"], heroes,
              [f"{style['hello']} Today's story is {titles[0]}!" if len(specs) == 1
               else f"{style['hello']} We have {len(specs)} new stories today!"],
              top=style["label"], topColor=style["color"], rays=style["rays"], start=0.5)
    b.music = [(0, b.t, rng.choice(style["songs"]), "lullaby" if calm and len(specs) == 1 else "gentle")]
    infos = []
    b.stories = []  # (title, start, end) of each story, so the day's Short can name the story it comes from
    for i, spec in enumerate(specs):
        start = b.t
        b.chapters.append((start, spec["title"]))
        if len(specs) > 1:
            b.sfx.append((start + 0.2, "sparkle"))
            d = b.say(start + 0.6, f"Story number {NUMBER_WORDS[i + 1].lower()}: {spec['title']}!")
            b.scene(start, start + d + 1.6, type="title", bg=outdoor(spec["shots"][0]["bg"]), top=f"Story {i + 1}",
                    title=[spec["title"]], heroes=[body(icon(c)) for c in spec.get("cast", [])[:3]])
            b.t = start + d + 1.6
        infos.append(story_script(spec)(b, rng))
        b.stories.append({"title": spec["title"], "from": b.f(start), "until": b.f(b.t)})
        if i:
            b.music.append((start, b.t, "twinkle" if spec.get("calm") else rng.choice(GENTLE_SONGS),
                            "lullaby" if spec.get("calm") else "gentle"))
        else:
            b.music[0] = (0, b.t, "twinkle" if spec.get("calm") else b.music[0][2], "lullaby" if spec.get("calm") else "gentle")
    outro(b, "dusk" if calm else outdoor(specs[-1]["shots"][-1]["bg"]), "The end!")
    s0, _, song, style = b.music[-1]
    b.music[-1] = (s0, b.t, song, style)
    b.music_gain = 0.24
    meta = {
        "title": f"{' & '.join(titles)} | Animated Story for Kids | Bubbly Kids TV",
        "lines": [f"📖 {s['title']}: {s['summary']} ({s['lesson']}.)" for s in specs],
        "intro": f"Brand-new animated {'story' if len(specs) == 1 else 'stories'} from Bubbly Kids TV for toddlers and preschoolers. 🎈",
        "tags": ["kids stories", "story time", "animated stories for kids", "stories for toddlers", "moral stories",
                 "preschool", "cartoon for kids", "bubbly kids tv"],
    }
    thumb = {"title": [titles[0]], "heroes": [body(icon(c)) for c in infos[0]["cast"][:2]], "bg": outdoor(first_bg),
             **badge}
    if weekly:
        meta["title"] = f"{len(specs)} Stories for Kids: {titles[0]}, {titles[1]} & More | Bubbly Kids TV"
        meta["intro"] = (f"All {len(specs)} stories from this week on Bubbly Kids TV, one after another: about "
                         f"{round(b.t / 60)} minutes of animated stories for toddlers and preschoolers. 🎈")
        thumb = dict(thumb, title=[f"{len(specs)} Stories in One!"],
                     heroes=[body(icon(i["cast"][0])) for i in infos[:2] if i.get("cast")])
    return meta, thumb


EGG_PATTERNS = [("dots", "dots"), ("stripes", "stripes"), ("zigzag", "zigzags"), ("stars", "stars"), ("hearts", "hearts")]
ACCENTS = [("white", "#FFFFFF"), ("yellow", "#FFE14D"), ("pink", "#FFA8D2"), ("blue", "#8CCBFF"), ("green", "#9BE89B")]
TOYS = [  # icon, name, colour, line, bubble
    ("ball", "bouncy ball", None, "Boing, boing! Let's play!", "Boing!"),
    ("balloon", "balloon", None, "It floats up, up, up!", "Up, up!"),
    ("star", "star", "#FFC92E", "Twinkle, twinkle! So shiny!", "Twinkle!"),
    ("icecream", "ice cream", "#FF6FB5", "Yummy! It's cold and sweet!", "Yum!"),
    ("cake", "cake", None, "A birthday cake! Yummy!", "Yummy!"),
    ("gift", "present", None, "A present! What a surprise!", "Wow!"),
    ("kite", "kite", None, "It flies high in the sky!", "Whee!"),
    ("yoyo", "yo-yo", None, "Up and down, up and down!", "Whee!"),
    ("van", "toy van", "#FF3B3B", "Beep beep! Here it comes!", "Beep beep!"),
    ("crown", "crown", "#FFC92E", "A shiny golden crown!", "Shiny!"),
    ("rainbow", "rainbow", "#9B5CFF", "So many pretty colors!", "Wow!"),
    ("strawberry", "strawberry", "#FF3B4F", "Sweet and red! Yum!", "Yum!"),
    ("banana", "banana", "#E8B400", "A yellow banana! Yum!", "Yum!"),
    ("xylophone", "xylophone", "#2F8CFF", "Ding, ding, ding! Let's make music!", "Ding!"),
    ("cookie", "cookie", "#C98B55", "Crunch, crunch! Yummy!", "Crunch!"),
    ("watermelon", "watermelon", "#3CC75A", "Big and juicy!", "Yum!"),
]


EGG_BGS = ["day", "garden", "playground", "beach", "park", "underwater", "bedroom", "farm"]
SHADOW_BGS = ["day", "park", "garden", "playground", "beach", "bedroom"]  # light places, so the shadow stands out


def fmt_eggs(b, rng, ep_no, count):
    n_animals = round(count * 0.6)
    picks = [("animal", c) for c in rng.sample(CRITTERS, min(n_animals, len(CRITTERS)))]
    picks += [("toy", t) for t in rng.sample(TOYS, count - len(picks))]
    rng.shuffle(picks)
    egg_heroes = [{"kind": "egg", "value": f"{p[0]}|{a[1]}", "color": c[1]}
                  for p, a, c in zip(rng.sample(EGG_PATTERNS, 3), rng.sample(ACCENTS, 3), rng.sample(COLOR_WORDS, 3))]
    intro(b, "day", ["Surprise Eggs!"], egg_heroes,
          ["Hello, friends! Welcome to Bubbly Kids TV!", "Look! Surprise eggs! What's inside? Let's open them together!"])
    prompts = ["What's inside? Let's count to three!", "What can it be? Let's open it!", "Is it an animal? Is it a toy? Let's see!"]
    b.chapters.append((b.t, "Open the surprise eggs"))
    found = []
    for i, (kind, item) in enumerate(picks):
        start = b.t
        cname, chex = rng.choice(COLOR_WORDS)
        pattern, pword = rng.choice(EGG_PATTERNS)
        aname, ahex = rng.choice(ACCENTS)
        if kind == "animal":
            ic, name, line, bubble, color = item
            hero = icon(ic, color)
        else:
            ic, name, color, line, bubble = item
            color = color or rng.choice(PALETTE)
            hero = icon(ic, color)
        b.sfx.append((start + 0.1, "whoop"))
        cur = 0.8
        cur += b.say(start + cur, f"{an(cname).capitalize()} {cname} egg with {aname} {pword}!") + 0.3
        cur += b.say(start + cur, prompts[i % len(prompts)]) + 0.2
        ticks = []
        for w in ("One!", "Two!", "Three!"):
            ticks.append(b.f(cur))
            b.sfx.append((start + cur, "tick"))
            cur += max(b.say(start + cur, w) + 0.15, 0.7)
        open_at = cur + 0.1
        b.sfx.append((start + open_at, "pop"))
        b.sfx.append((start + open_at + 0.08, "sparkle"))
        cur = open_at + 0.7
        name_at = cur
        cur += b.say(start + cur, f"It's {an(name)} {name}!") + 0.3
        bubble_at = cur
        cur += b.say(start + cur, line) + 0.9
        b.scene(start, start + cur, type="egg", bg=EGG_BGS[(i + ep_no) % len(EGG_BGS)], egg={"kind": "egg", "value": f"{pattern}|{ahex}", "color": chex},
                ticks=ticks, openAt=b.f(open_at), hero=hero, name={"text": name.upper(), "color": color, "at": b.f(name_at)},
                bubble={"text": bubble, "color": color, "at": b.f(bubble_at)})
        b.t = start + cur
        found.append((hero, name))
    animals = [(h, n) for (h, n), (k, _) in zip(found, picks) if k == "animal"][:8]
    b.chapters.append((b.t, "Who did we find?"))
    b.review("We found them!", "#FF6FB5", "Look at all the animals we found!",
             [(h, n.capitalize(), f"{n.capitalize()}!") for h, n in animals])
    outro(b, "day", "So many surprises!")
    songs = list(GENTLE_SONGS)
    rng.shuffle(songs)
    third = b.t / 3
    b.music = [(k * third, (k + 1) * third, songs[k], "gentle") for k in range(3)]
    names = [n for _, n in found]
    meta = {
        "title": f"Surprise Eggs! {cap(names[0])}, {cap(names[1])} & {cap(names[2])} | Learn Animals & Colors | Bubbly Kids TV",
        "lines": ["🥚 Inside the eggs: " + ", ".join(names), "🎨 Colors and patterns on every egg", "🐮 Animal names and sounds"],
        "intro": "Surprise eggs with Bubbly Kids TV! 🎈 Crack open colorful eggs and find animals, toys and yummy treats.",
        "tags": ["surprise eggs", "surprise eggs for kids", "learn animals", "animal sounds", "learn colors", "toddler learning",
                 "preschool", "kids video", "bubbly kids tv"],
    }
    thumb = {"title": ["Surprise Eggs!", "What's Inside?"],
             "heroes": [egg_heroes[0], found[0][0], egg_heroes[1], found[1][0], egg_heroes[2]], "bg": "day"}
    return meta, thumb


HINTS = {  # icon: (name, colour, hint)
    "apple": ("apple", "#FF3B3B", "I am round and red. I grow on a tree!"),
    "sun": ("sun", "#FFC92E", "I am big and bright. I shine in the sky!"),
    "moon": ("moon", "#FFC92E", "I come out at night!"),
    "fish": ("fish", "#2F8CFF", "I swim in the water!"),
    "carrot": ("carrot", "#FF8A1F", "I am orange. Bunnies love to eat me!"),
    "umbrella": ("umbrella", "#9B5CFF", "You need me on a rainy day!"),
    "icecream": ("ice cream", "#FF6FB5", "I am cold and sweet. Yum!"),
    "tree": ("tree", "#3CC75A", "I am tall, with lots of green leaves!"),
    "kite": ("kite", "#FF8A1F", "I fly high in the windy sky!"),
    "van": ("van", "#FF3B3B", "I have four wheels. Beep beep!"),
    "balloon": ("balloon", "#2F8CFF", "I float up, up, up!"),
    "star": ("star", "#FFC92E", "I twinkle in the night sky!"),
    "banana": ("banana", "#E8B400", "I am long and yellow!"),
    "cake": ("cake", "#FF6FB5", "I have candles on top!"),
    "crown": ("crown", "#FFC92E", "Kings and queens wear me!"),
    "flower": ("flower", "#9B5CFF", "I grow in the garden and smell so nice!"),
    "pumpkin": ("pumpkin", "#FF8A1F", "I am big, round and orange!"),
    "strawberry": ("strawberry", "#FF3B4F", "I am small, red and sweet!"),
}


def fmt_shadow(b, rng, ep_no, count):
    n_animals = round(count * 0.55)
    picks = [("animal", c) for c in rng.sample(CRITTERS, min(n_animals, len(CRITTERS)))]
    picks += [("thing", (k, *HINTS[k])) for k in rng.sample(list(HINTS), count - len(picks))]
    rng.shuffle(picks)
    shadows = [dict(icon(c[1][0], c[1][4] if c[0] == "animal" else c[1][2]), shadow=True) for c in picks[:3]]
    intro(b, "day", ["Guess the Shadow!"], shadows,
          ["Hello, friends! Welcome to Bubbly Kids TV!", "Let's play a guessing game! Look at the shadow. Who is hiding?"])
    prompts = ["Who am I? Can you guess?", "Who is hiding?", "Look at the shadow. What can it be?"]
    b.chapters.append((b.t, "Guess the shadow"))
    found = []
    for i, (kind, item) in enumerate(picks):
        start = b.t
        b.sfx.append((start + 0.1, "whoop"))
        cur = 0.7
        cur += b.say(start + cur, prompts[i % len(prompts)]) + 0.35
        if kind == "animal":
            ic, name, line, bubble, color = item
            cur += b.say(start + cur, "Listen!") + 0.2
            voice, pitch, sound, _ = CAST.get(ic, ("af_heart", 1.0, bubble, color))
            cur += b.say(start + cur, f"{sound} {sound}", voice=voice, speed=0.9, pitch=pitch) + 0.4
        else:
            ic, name, color, hint = item
            bubble = "Ta-da!"
            cur += b.say(start + cur, hint) + 0.4
        counts = []
        for w in ("Three!", "Two!", "One!"):
            counts.append(b.f(cur))
            b.sfx.append((start + cur, "tick"))
            cur += max(b.say(start + cur, w) + 0.12, 0.72)
        reveal = cur + 0.1
        b.sfx.append((start + reveal, "sparkle"))
        b.sfx.append((start + reveal, "pop"))
        cur = reveal + 0.5
        name_at = cur
        cur += b.say(start + cur, f"It's {an(name)} {name}!") + 0.3
        bubble_at = cur
        if kind == "animal" and ic in CAST:
            voice, pitch, _, _ = CAST[ic]
            cur += b.say(start + cur, f"Hello! I'm {an(name)} {name}!", voice=voice, speed=0.9, pitch=pitch) + 0.9
        else:
            cur += 1.4
        hero = icon(ic, color)
        b.scene(start, start + cur, type="shadow", bg=SHADOW_BGS[(i + ep_no) % len(SHADOW_BGS)], hero=hero, counts=counts, revealAt=b.f(reveal),
                name={"text": name.upper(), "color": color, "at": b.f(name_at)},
                bubble={"text": bubble, "color": color, "at": b.f(bubble_at)})
        b.t = start + cur
        found.append((hero, name))
    outro(b, "day", "Great guessing!")
    songs = list(GENTLE_SONGS)
    rng.shuffle(songs)
    third = b.t / 3
    b.music = [(k * third, (k + 1) * third, songs[k], "gentle") for k in range(3)]
    names = [n for _, n in found]
    meta = {
        "title": f"Guess the Shadow! Who Am I? {cap(names[0])}, {cap(names[1])} & More | Bubbly Kids TV",
        "lines": ["🔍 Hidden shadows: " + ", ".join(names), "🐮 Animal sound clues", "🔢 Count down 3, 2, 1 for every reveal"],
        "intro": "Guess the shadow with Bubbly Kids TV! 🎈 Listen to the clue, count down, and see who is hiding.",
        "tags": ["guess the shadow", "guessing game for kids", "animal sounds", "who am i", "toddler learning", "preschool",
                 "kids quiz", "bubbly kids tv"],
    }
    thumb = {"title": ["Guess the Shadow!", "Who Am I?"],
             "heroes": [dict(found[0][0], shadow=True), found[1][0], dict(found[2][0], shadow=True)], "bg": "day"}
    return meta, thumb


CREWS = [
    [icon("apple", "#FF3B3B"), icon("banana"), icon("strawberry"), icon("orange", "#FF8A1F")],
    [icon("grapes", "#9B5CFF"), icon("watermelon"), icon("banana"), icon("apple", "#FF3B3B"), icon("strawberry")],
    [icon("carrot", "#FF8A1F"), icon("pumpkin", "#FF8A1F"), icon("carrot", "#FF8A1F")],
    [icon("icecream", "#FF6FB5"), icon("cookie", "#C98B55"), icon("cake", "#FF6FB5")],
    [icon("cat"), icon("dog"), icon("pig"), icon("bunny")],
    [icon("duck"), icon("chick"), icon("frog"), icon("sheep"), icon("cow")],
    [{"kind": "balloon", "value": "", "color": c} for c in PALETTE[:5]],
    [{"kind": "shape", "value": s, "color": c} for s, c in zip(["circle", "star", "heart", "triangle", "square"], PALETTE[1:])],
    [icon("lion"), icon("bear"), icon("zebra", "#5B5B6B")],
]
CALLOUTS = [("Let's bounce!", ["bounce"]), ("Wiggle, wiggle!", ["wiggle", "bounce"]), ("Spin around!", ["spin"]),
            ("Jump, jump, jump!", ["jump"]), ("Sway side to side!", ["sway"]), ("Clap your hands!", ["pop", "bounce"]),
            ("Shake, shake, shake!", ["wiggle"])]
FORMATIONS = ["line", "wave", "center", "circle", "conga"]
DANCE_SONGS = ["yankee", "twinkle", "macdonald", "ode", "london", "mary", "frere", "hotcross"]


def fmt_dance(b, rng, ep_no, sections):
    beat = 60 / DANCE_BPM
    bar = 4 * beat
    section = 8 * bar
    crews = rng.sample(CREWS, len(CREWS))
    intro_end = 4 * bar
    b.say(1.0, "Hello, friends! It's dance party time!")
    b.say(4.4, "Let's dance with our friends!")
    b.scene(0, intro_end, type="title", bg="party", top="Bubbly Kids TV", title=["Dance Party!"],
            heroes=[body(h) if h["kind"] != "balloon" else h for h in crews[0][:3]])
    b.chapters.append((0, "Dance party!"))
    t = intro_end
    songs = list(DANCE_SONGS)
    rng.shuffle(songs)
    last_moves = None
    for i in range(sections):
        start = t
        crew = crews[i % len(crews)]
        text, moves = rng.choice([c for c in CALLOUTS if c[1] != last_moves])
        last_moves = moves
        formation = FORMATIONS[(i + rng.randrange(5)) % 5] if len(crew) > 2 else "line"
        callouts = [{"text": text, "color": RAINBOW_TEXT[i % len(RAINBOW_TEXT)], "at": b.f(0.15)}]
        b.say(start + 0.15, text)
        freezes = []
        if i % 3 == 1:
            fz = start + 4 * bar
            b.mutes.append((fz, fz + bar))
            b.say(fz + 0.05, "Freeze!")
            b.say(fz + bar - 0.9, "And dance!")
            freezes.append({"at": b.f(fz - start), "until": b.f(fz + bar - start)})
            callouts.append({"text": "FREEZE!", "color": "#7FD0FF", "at": b.f(fz - start)})
        if i % 2 == 0:
            b.chapters.append((start, text.rstrip("!")))
        b.scene(start, start + section, type="dance", bg="party", beat0=-b.f(start), bpm=DANCE_BPM, crew=crew, formation=formation,
                moves=moves, callouts=callouts, freezes=freezes)
        t = start + section
    b.t = t
    outro(b, "party", "Great dancing!")
    # the medley: a new tune every two sections, always starting on a bar line
    b.music = []
    edges = [0.0] + [intro_end + k * 2 * section for k in range(1, (sections + 1) // 2)] + [b.t]
    for k in range(len(edges) - 1):
        b.music.append((edges[k], edges[k + 1], songs[k % len(songs)], "dance"))
    b.music_gain = 0.5
    meta = {
        "title": "Dance Party with Fruit Friends! Freeze Dance for Kids | Bubbly Kids TV",
        "lines": ["💃 Bounce, wiggle, spin and jump with fruits, animals and balloons",
                  "🧊 Freeze dance: when the music stops, freeze!", "🎵 Upbeat versions of classic public-domain nursery tunes"],
        "intro": "Dance party with Bubbly Kids TV! 🎈 A colorful sensory dance video for babies, toddlers and preschoolers.",
        "tags": ["dance party for kids", "freeze dance", "sensory video", "baby sensory", "kids dance", "toddler dance",
                 "brain break", "bubbly kids tv"],
    }
    thumb = {"title": ["Dance Party!", "Freeze Dance"], "heroes": [body(h) if h["kind"] != "balloon" else h for h in crews[0][:4]], "bg": "party"}
    return meta, thumb


RAINBOW_TEXT = ["#FF3B3B", "#FF8A1F", "#FFC92E", "#3CC75A", "#2F8CFF", "#9B5CFF", "#FF6FB5"]


def build(day, kind, size):
    ep_no = (day - FIRST_EPISODE).days + 1
    rng = random.Random(f"fun-{ep_no}")
    b = Builder()
    if kind == "story":
        meta, thumb = fmt_story(b, rng, ep_no, size)
    elif kind == "eggs":
        meta, thumb = fmt_eggs(b, rng, ep_no, size)
    elif kind == "shadow":
        meta, thumb = fmt_shadow(b, rng, ep_no, size)
    else:
        meta, thumb = fmt_dance(b, rng, ep_no, size)
    return b, meta, thumb, ep_no


def description(b, meta, ep_no):
    return "\n".join([
        meta["intro"],
        "",
        *meta["lines"],
        "",
        "⏱ Chapters",
        *[f"{fmt(t)} {name}" for t, name in b.chapters],
        "",
        "A new story every day on Bubbly Kids TV, and every Sunday the whole week's stories in one video!",
        "Music: public-domain nursery melodies. Characters and stories: original Bubbly Kids TV.",
        "",
        "#kidsvideos #toddlers #preschool #bubblykidstv",
    ])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=dt.date.today().isoformat())
    p.add_argument("--format", choices=sorted(set(FORMATS)), help="override the daily rotation")
    p.add_argument("--check-story", help="build just this story script into build/check-story (for previews)")
    p.add_argument("--daily", action="store_true", help="the daily video: one new story, into build/<date>-story")
    p.add_argument("--short", action="store_true", help="the vertical Short cut from the day's story, into build/<date>-story-short")
    p.add_argument("--weekly", action="store_true", help="Sunday's video: the past week's stories, into build/<date>-weekly")
    a = p.parse_args()
    if a.check_story:
        return check_only(a.check_story)
    if a.daily:
        return daily(a.date)
    if a.short:
        return story_short(a.date)
    if a.weekly:
        return weekly(a.date)
    day = dt.date.fromisoformat(a.date)
    ep_no = (day - FIRST_EPISODE).days + 1
    kind = a.format or FORMATS[(ep_no - 1) % len(FORMATS)]
    name = f"{a.date}-fun"
    work = os.path.join(BUILD, name)
    os.makedirs(work, exist_ok=True)

    if kind == "story":
        SCRIPTS[:] = scripted_stories(a.date, 3)
    size, step, limit = {"story": (1, 1, 3), "eggs": (16, 2, 26), "shadow": (18, 2, 30), "dance": (18, 1, 22)}[kind]
    while True:
        b, meta, thumb, ep_no = build(day, kind, size)
        if b.t >= MIN_SECONDS or size >= limit:
            break
        size += step

    wav_rel = write_audio(b, work, name)
    season, look = look_for(day, "fun")
    props = {"durationInFrames": b.f(b.t), "audio": wav_rel, "scenes": b.scenes, "thumb": thumb, "season": season, "look": look}
    write_json(work, props, {"title": meta["title"][:100], "description": description(b, meta, ep_no), "tags": meta["tags"]})
    if kind == "story":  # archive the scripts this video used
        used = os.path.join(STORY_DIR, "used", a.date)
        for path, _ in SCRIPTS[:STORY_SIZES[size][0]]:
            if os.path.dirname(path) != used:
                os.makedirs(used, exist_ok=True)
                os.rename(path, os.path.join(used, os.path.basename(path)))
    print(f"fun {kind} {ep_no} {a.date}: {b.t:.1f}s, {len(b.scenes)} scenes, {len(b.voices)} lines")


def daily(date):
    day = dt.date.fromisoformat(date)
    ep_no = (day - FIRST_EPISODE).days + 1
    kind = kind_for(date)
    scripts = scripted_stories(date, 3, kind)
    if not scripts:  # better no video than a repeat of a built-in story
        raise SystemExit("no new story waiting in stories/new")
    picked = []
    for path, spec in scripts:  # one long story, or a few short ones until the video is about three minutes
        picked.append((path, spec))
        if sum(estimate_seconds(s) for _, s in picked) >= 150:
            break
    name = f"{date}-story"
    work = os.path.join(BUILD, name)
    os.makedirs(work, exist_ok=True)
    b = Builder()
    kind = picked[0][1].get("kind") or kind  # the look of the story itself, when the day had to take another kind
    b.narrator = narrator_for(kind, [s for _, s in picked])
    meta, thumb = fmt_daily(b, random.Random(f"daily-{date}"), ep_no, [s for _, s in picked], kind)
    wav_rel = write_audio(b, work, name)
    season, look = look_for(day, "story")
    props = {"durationInFrames": b.f(b.t), "audio": wav_rel, "scenes": b.scenes, "thumb": thumb, "season": season, "look": look,
             "stories": b.stories}
    write_json(work, props, {"title": meta["title"][:100], "description": description(b, meta, ep_no), "tags": meta["tags"]})
    used = os.path.join(STORY_DIR, "used", date)
    for path, _ in picked:
        if os.path.dirname(path) != used:
            os.makedirs(used, exist_ok=True)
            os.rename(path, os.path.join(used, os.path.basename(path)))
    print(f"daily story {date}: {[s['title'] for _, s in picked]}, {b.t:.1f}s, {len(b.scenes)} scenes")


WEEKLY_MIN = 3
WEEKLY_MAX = len(NUMBER_WORDS) - 1  # "Story number ten" is the last one we can say


def weekly(date):
    """Sunday's video: the stories of the seven days before, one after another (chapters in the description), for the
    viewers who watch stories back to back. They are told again from their scripts in stories/used/, by one narrator.
    With fewer than WEEKLY_MIN stories there is no weekly video (nothing is written)."""
    day = dt.date.fromisoformat(date)
    specs = []
    for k in range(7, 0, -1):
        for path in sorted(glob.glob(os.path.join(STORY_DIR, "used", (day - dt.timedelta(days=k)).isoformat(), "*.json"))):
            try:
                specs.append(load_script(path))
            except (StoryError, ValueError, KeyError) as e:
                print(f"skipping story {os.path.basename(path)}: {e}")
    specs = specs[-WEEKLY_MAX:]
    if len(specs) < WEEKLY_MIN:
        print(f"only {len(specs)} stories in the week before {date}: no weekly video")
        return
    ep_no = (day - FIRST_EPISODE).days + 1
    name = f"{date}-weekly"
    work = os.path.join(BUILD, name)
    os.makedirs(work, exist_ok=True)
    b = Builder()
    kind = kind_for(date)
    b.narrator = narrator_for(kind, specs)
    meta, thumb = fmt_daily(b, random.Random(f"weekly-{date}"), ep_no, specs, kind, weekly=True)
    wav_rel = write_audio(b, work, name)
    season, look = look_for(day, "weekly")
    props = {"durationInFrames": b.f(b.t), "audio": wav_rel, "scenes": b.scenes, "thumb": thumb, "season": season, "look": look,
             "stories": b.stories}
    write_json(work, props, {"title": meta["title"][:100], "description": description(b, meta, ep_no), "tags": meta["tags"]})
    print(f"weekly {date}: {len(specs)} stories, {b.t / 60:.1f} min, {len(b.scenes)} scenes")


SHORT_SECONDS = (30, 58)


def story_short(date):
    """A vertical Short from the day's story: the run of shots (30-58 s) with the most talking, ending if possible on
    the story's last shot. The video follows whoever is speaking (src/StoryShort.tsx). Each Short is a different
    moment of a different story, never a template."""
    src = os.path.join(BUILD, f"{date}-story")
    props = json.load(open(os.path.join(src, "props.json")))
    shots = [s for s in props["scenes"] if s["type"] == "story"]
    lo, hi = SHORT_SECONDS[0] * FPS, SHORT_SECONDS[1] * FPS
    best = None
    for i in range(len(shots)):
        total = 0
        for j in range(i, len(shots)):
            total += shots[j]["duration"]
            if total > hi:
                break
            if total >= lo:
                score = sum(len(s.get("cam", [])) for s in shots[i:j + 1]) + (3 if j == len(shots) - 1 else 0)
                if best is None or score > best[0]:
                    best = (score, i, j)
    if best:
        pick = shots[best[1]:best[2] + 1]
    else:  # one long shot: its first 58 seconds
        pick = [max(shots, key=lambda s: s["duration"])]
    t0 = pick[0]["from"]
    t1 = min(pick[-1]["from"] + pick[-1]["duration"], t0 + hi)
    scenes = []
    for s in pick:
        s = dict(s, **{"from": s["from"] - t0})
        s["duration"] = min(s["duration"], t1 - t0 - s["from"])
        scenes.append(s)
    data, sr = sf.read(os.path.join(os.path.dirname(BUILD), "public", props["audio"]), dtype="float32")
    clip = data[int(t0 / FPS * sr):int(t1 / FPS * sr)].copy()
    ramp = int(0.3 * sr)
    clip[:ramp] *= np.linspace(0, 1, ramp)[:, None]
    clip[-ramp:] *= np.linspace(1, 0, ramp)[:, None]
    name = f"{date}-story-short"
    work = os.path.join(BUILD, name)
    os.makedirs(work, exist_ok=True)
    sf.write(os.path.join(os.path.dirname(BUILD), "public", "audio", f"{name}.wav"), clip, sr, subtype="PCM_16")
    title = next((s["title"] for s in props.get("stories", []) if s["from"] <= t0 < s["until"]), props["thumb"]["title"][-1])
    short = {"durationInFrames": t1 - t0, "audio": f"audio/{name}.wav", "title": title, "scenes": scenes,
             "season": props.get("season"), "look": props.get("look")}
    meta = {"title": f"{title} 🎈 Kids Story #shorts"[:100],
            "description": "\n".join([f"A moment from today's story, {title}. Watch the whole story on Bubbly Kids TV!", "",
                                       "#shorts #kidsstories #toddlers #preschool #bubblykidstv"]),
            "tags": ["kids story", "kids shorts", "story time", "toddler", "preschool", "bubbly kids tv"]}
    write_json(work, short, meta)
    print(f"story short {date}: {(t1 - t0) / FPS:.1f}s from {t0 / FPS:.1f}s, {len(scenes)} shots")


def check_only(path):
    """Builds one story script on its own so its frames can be previewed with `npx remotion still`."""
    try:
        spec = load_script(path)
    except StoryError as e:
        raise SystemExit(f"story error: {e}")
    b = Builder()
    rng = random.Random(1)
    d = b.say(0.6, f"{spec['title']}!")
    b.scene(0, d + 1.6, type="title", bg="dusk" if spec.get("calm") else "park", top="Story", title=[spec["title"]],
            heroes=[body(icon(c)) for c in spec.get("cast", [])[:3]])
    b.t = d + 1.6
    story_script(spec)(b, rng)
    b.music = [(0, b.t, "twinkle" if spec.get("calm") else "mary", "lullaby" if spec.get("calm") else "gentle")]
    b.music_gain = 0.24
    work = os.path.join(BUILD, "check-story")
    os.makedirs(work, exist_ok=True)
    wav_rel = write_audio(b, work, "check-story")
    starts = [sc["from"] for sc in b.scenes]
    write_json(work, {"durationInFrames": b.f(b.t), "audio": wav_rel, "scenes": b.scenes,
                      "thumb": {"title": [spec["title"]], "heroes": [], "bg": "park"}}, {})
    print(f"ok: {spec['title']!r} {b.t:.1f}s, {len(b.scenes) - 1} shots, shot start frames {starts[1:]}")
    if not 60 <= b.t <= 200:
        print("warning: aim for 60-200 seconds")


if __name__ == "__main__":
    main()
