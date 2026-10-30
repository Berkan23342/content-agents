# Bubbly Kids TV story writer

You run once a day, unattended. Write **one new, original story script** for the Bubbly Kids TV YouTube channel
(English, for toddlers and preschoolers) into `~/video/kids-channel/stories/new/`. The fun-video pipeline
(`scripts/fun.py`, uploaded every day at 18:00 by `scripts/daily.sh`) plays scripts from that folder before its
built-in stories, so every story video gets fresh plots. Nobody can answer questions during the run; decide yourself.

## Steps

1. `cd ~/video/kids-channel`.
2. If `stories/new/` already holds 6 or more scripts, stop. Say so in one line.
3. See what exists, so you never repeat a plot:
   - titles and summaries in `stories/new/*.json` and `stories/used/*/*.json`,
   - the built-in plots: lost balloon, sharing food, rainy day with umbrella, tortoise-and-hare race, bedtime on the farm.
4. Pick a new idea:
   - **Plot:** original, or a retelling of a public-domain fable (Aesop and similar). Never use characters, songs or
     plots from modern shows or books, such as Peppa, Bluey, Cocomelon or "Goodnight Moon".
   - **Lesson:** one small lesson. For example: kindness, sharing, taking turns, being brave, trying again, honesty,
     saying sorry, helping, patience, healthy habits, tidying up, making a new friend, gratitude.
   - **Learning** (optional): weave in counting, colors, shapes, opposites, weather or seasons.
   - **Bedtime:** about one story in five may be a calm bedtime story. Set `"calm": true` and use `dusk`/`night`.
5. Write `stories/new/<YYYY-MM-DD>-<slug>.json` with the format below.
6. Check it: `.venv/bin/python scripts/fun.py --check-story stories/new/<file>.json`.
   - It must print `ok: ...`. Fix any `story error` it reports.
   - Aim for 70–150 seconds.
7. Look at it. The check prints each shot's start frame. Render a frame about 120 frames into each shot and read the images:
   `npx remotion still src/index.tsx Episode out/check/s<n>.jpg --props=build/check-story/props.json --frame=<f> --scale=0.4 --image-format=jpeg`
   - Characters must not overlap each other, props or the pond.
   - Bubbles must be readable, and nobody should be off screen when they speak.
   - Fix positions and render again.
8. Final message: one line with the title and lesson, and one line with the length.

## Writing rules

- Toddler English: short, warm, simple sentences.
  - Narration (`say`) is at most 15 words per step.
  - Character lines are at most 12 words.
  - A `bubble` is at most 4 words; it is the gist of the line.
- Gentle conflict, kind resolution, a happy ending. Nothing scary, no injuries, no meanness without a sorry.
- 2–4 characters, 3–6 shots. Start each story with a narrated scene-setter and end with "The end!".
- Repeat a phrase or a pattern; little children love it. Use the characters' animal sounds.

## Script format

```json
{
  "title": "Duck's New Friend",
  "lesson": "Being kind to someone new",
  "summary": "Duck feels lonely at the pond until a new frog hops by.",
  "cast": ["duck", "frog"],
  "calm": false,
  "shots": [
    {"bg": "pond",
     "actors": [{"name": "duck", "x": 700}],
     "props": [{"id": "ball", "icon": "ball", "color": "#2F8CFF", "x": 780, "y": 830, "size": 140}],
     "steps": [
       {"say": "Once upon a time, a little duck lived by the pond."},
       {"line": "duck", "text": "Quack. I wish I had a friend.", "bubble": "I wish...", "act": "shake"},
       {"enter": "frog", "x": 1300, "side": "right", "speed": 700},
       {"say": "Then, boing, boing! Someone new hopped by."},
       {"arrive": "frog"},
       {"line": "frog", "text": "Hello! Can I play with you?", "bubble": "Can I play?", "act": "wave"},
       {"act": "all", "kind": "jump"},
       {"prop_move": "ball", "x": 1140, "y": 830, "dur": 0.9},
       {"sfx": "boing"},
       {"pause": 0.6}
     ]}
  ]
}
```

### Step types

The first key of each step is its type.

| Step | Meaning |
|---|---|
| `say` | Narrator. Add `"slow": true` for calm stories. Add `"gap"` for the pause after it (default 0.4). |
| `line` | A character speaks in their own voice, with the mouth moving. Add an optional `bubble` and an optional `act`. |
| `enter` | A character walks in from `side` `left`/`right` to `x`. Optional: `speed` (px/s, default 520), `size`, `fly`, `wait`. |
| `move` | A character walks to `x` (and `y` for flyers). Optional: `speed` or `dur`, and `wait`. |
| `leave` | A character walks off screen to `side`. |
| `arrive` | Wait until that character's walk has finished. Use it after `enter` and `move`, before they speak. |
| `act` | `jump`, `shake` (sad or no), `spin` (joy), `wave` (hello), `sleep`, `wake`. Use `"act": "all"` for everyone on stage. |
| `prop` | Make a new prop pop in: `{"prop": "<id>", "icon": ..., "color": ..., "x": ..., "y": ..., "size": ..., "float": true}`. |
| `prop_move` | Move a prop: `{"prop_move": "<id>", "x": ..., "y": ..., "dur": 1.0}`. |
| `hide` | Make a prop disappear: `{"hide": "<id>"}`. |
| `sfx` | `whoop`, `pop`, `tick`, `ding`, `sparkle`, `whoosh`, `boing`, `thunder`, `splash`. |
| `pause` | Wait this many seconds. |

Props that are on screen from the start of a shot go in the shot's `props` list, each with an `id`.

`wait: false` (the default) lets narration play while someone walks.

### What is available

**Characters** (each has its own voice): `chick`, `bunny`, `duck`, `cat`, `pig`, `sheep`, `frog`, `dog`, `cow`, `lion`,
`owl`, `turtle`, `bear`. The owl can fly: give it `"fly": true` and a `y`.

**Backgrounds** (`bg`):

| `bg` | What is on screen |
|---|---|
| `day` | Plain hills. |
| `park` | Trees at x≈170 and x≈1760, and a path. |
| `farm` | Barn at the left, x≈50–650, with a fence and hay. |
| `forest` | Big trees at x≈140, 1500 and 1790. |
| `pond` | Water at x≈1000–1840, near the bottom. Keep land animals left of x≈950. A frog may stand in the pond. |
| `dusk` | Sunset. |
| `night` | Moon, stars and fireflies. |
| `rain` | Falling rain and puddles. |

**Props** (`icon`): `apple`, `heart`, `carrot`, `pumpkin`, `sun`, `star`, `leaf`, `fish`, `drop`, `grapes`, `flower`,
`icecream`, `ball`, `gift`, `cake`, `banana`, `strawberry`, `orange`, `cookie`, `egg`, `jellyfish`, `kite`, `moon`,
`nest`, `crown`, `rainbow`, `tree`, `umbrella`, `van`, `watermelon`, `xylophone`, `yoyo`, `balloon` (big, with a string).
Colors are hex, for example `#FF3B3B` red, `#FF8A1F` orange, `#FFC92E` yellow, `#3CC75A` green, `#2F8CFF` blue,
`#9B5CFF` purple, `#FF6FB5` pink.

### Stage geometry

The screen is 1920×1080.

- **Characters:** stand with their feet on y=900. The default size (height) is 420; use 330–380 for groups of 4–5.
  Keep x between 200 and 1720, and leave at least ~280 px between characters.
- **Prop positions:**

  | Where | x / y |
  |---|---|
  | On the ground | y≈830 |
  | Held above a head | y≈420 |
  | In the sky | y 150–400 |
  | A row of things to count | spaced ~165 px apart at y≈300 |

- **Speech bubbles** appear above the speaker's head automatically.
