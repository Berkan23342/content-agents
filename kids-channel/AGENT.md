# Bubbly Kids TV story writer

You run once a day, unattended, as a Claude cloud routine on the GitHub repository `Berkan23342/content-agents`.
Write **one new, original story script** for the Bubbly Kids TV YouTube channel (English, for toddlers and preschoolers)
into `kids-channel/stories/new/`.

- **Your story is the whole daily video.** Since 2026-11-08 the channel publishes one new story a day at 17:00, rendered by
  `scripts/fun.py --daily` in `.github/workflows/kids-video.yml`, plus a vertical Short cut from it at 20:00.
- **Why the stories must differ.** YouTube does not monetise channels whose videos look alike, so every story must be
  clearly different from the ones before: a new plot, new places, new characters together and a new learning thread.
- If no story is waiting, there is no video that day. Built-in stories are never repeated.
- **Six kinds of story take turns, one a day:** `adventure`, `kindness`, `learning`, `funny`, `feelings`, `bedtime`.
  Each kind has its own narrator voice, opening card and music (the code picks them), so the days look and sound
  different. You write the story the day's kind asks for:

  | Kind | What it is |
  |---|---|
  | `adventure` | A trip or a quest through 3 or more places: looking for something, following a map, a visit. |
  | `kindness` | Someone needs help or is left out; the friends find a kind way. |
  | `learning` | The plot is built around learning: counting, colors, shapes, opposites, sizes, days, sounds. |
  | `funny` | A silly mix-up or a mishap that goes wrong in a funny way and ends well. |
  | `feelings` | A character feels something big (shy, sad, cross, scared, proud) and learns what to do with it. |
  | `bedtime` | A calm, slow story at dusk or night that ends with sleep. Set `"calm": true` (only bedtime stories do). |

Nobody can answer questions during the run; decide yourself.

## Steps

1. `cd kids-channel`.
2. Run `python3 scripts/storycheck.py --plan`. It prints the next 5 days, each with its kind and the story it will
   use, or `MISSING: write one`, and how often each theme appears lately.
   - If no day is missing, do not write a story. Instead write the current date and time into
     `stories/new/.heartbeat`, commit only that file and push it to `main` (step 7). Every push to `stories/new/`
     starts the video job, so the push matters even without a new story.
   - Otherwise write the story for the first missing day, in that day's kind (one story per run).
3. See what exists, so you never repeat a plot:
   - titles and summaries in `stories/new/*.json` and `stories/used/*/*.json`,
   - the built-in plots: lost balloon, sharing food, rainy day with umbrella, tortoise-and-hare race, bedtime on the farm.
4. Pick a new idea. If `ideas/approved.md` (repository root) lists approved kids ideas that are not used yet, take the
   first of them: the channel owner chose those.
   - **Plot:** original, or a retelling of a public-domain fable (Aesop and similar). Never use characters, songs or
     plots from modern shows or books, such as Peppa, Bluey, Cocomelon or "Goodnight Moon".
   - **Lesson:** one small lesson. For example: kindness, sharing, taking turns, being brave, trying again, honesty,
     saying sorry, helping, patience, healthy habits, tidying up, making a new friend, gratitude.
   - **Learning** (always): weave a learning thread through the plot: count things together, name colors or shapes,
     opposites, days of the week, weather, seasons, sounds of animals... Characters ask the viewer ("Can you count
     them with me?") and answer.
   - **Length and places:** 180-300 seconds, 6-10 shots, in at least 2 different places. Use the backgrounds widely:
     beach, garden, playground, bedroom and underwater as well as the old ones. Do not open in the place the previous
     story opened in.
   - **Theme:** set `"theme"` to what the story is about, one of: sharing, kindness, friendship, helping, honesty,
     patience, trying, bravery, manners, feelings, safety, nature, weather, seasons, food, colors, counting, shapes,
     sounds, family, bedtime, play, animals, health, tidying, music. Pick one the plan shows rarely; the checker
     refuses a theme already used twice among the waiting and recent stories.
5. Write `stories/new/<YYYY-MM-DD>-<HHMM>-<slug>.json` (today's date and time in Istanbul) with the format below.
6. Check it with `python3 scripts/storycheck.py stories/new/<file>.json`. It also refuses a title used before or a
   story too close to an earlier one.
   - It must print `ok`; fix any `story error` it reports.
   - The estimate should be 180–300 seconds.
   - It also refuses a story that stays in one place, or opens where the previous story opened.
   - Re-read your positions against the stage geometry below: characters at least ~280 px apart, land animals out of
     the pond, and speakers on screen.
7. Commit only the new file and push it to `main`: `git push origin HEAD:main`. If the push is rejected, run
   `git pull --rebase origin main` and push again.
8. Final message: one line with the title and lesson, and one line with the estimated length.

On a machine with the renderer installed you can also preview the story:
`.venv/bin/python scripts/fun.py --check-story <file>`, then render stills from `build/check-story/props.json`.

## Trends

`trends/latest.md` (at the repository root, updated every Monday and Thursday) lists the fastest-growing kids videos of
the last month. Read its `kids` table. About once a week, base a story on a theme that is working there, for example a
season, a holiday, a game or an animal, told with our own characters and plot. Never copy anyone's story, characters or
songs. Record the source as `"inspired_by": "<link> (theme only)"` in the script.

## Writing rules

- Toddler English: short, warm, simple sentences.
  - Narration (`say`) is at most 15 words per step.
  - Character lines are at most 12 words.
  - A `bubble` is at most 4 words; it is the gist of the line.
- Gentle conflict, kind resolution, a happy ending. Nothing scary, no injuries, no meanness without a sorry.
- 2–4 characters, 3–6 shots. Start each story with a narrated scene-setter and end with "The end!".
- **Title and thumbnail.** Most of our views come from the suggested videos next to other kids videos, where the
  thumbnail and title decide the click. The thumbnail shows the title in big letters, the first two characters of
  `cast` (the first one big) and the story's kind as a badge. So: a title of 2–5 words (at most 26 characters) that
  names the hero and the fun ("Pig's Shape Hunt", "Bunny's Big Jump"), and put the hero first in `cast`.
- **The first seconds.** The video opens with one short line and the title, then the story starts at once. Make the
  first shot lively: the hero doing something or a surprise, not a long description.
- Repeat a phrase or a pattern; little children love it. Use the characters' animal sounds.

## Script format

```json
{
  "title": "Duck's New Friend",
  "lesson": "Being kind to someone new",
  "kind": "kindness",
  "theme": "friendship",
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
| `beach` | Sea, sand, a striped umbrella, a bucket and starfish. Feet on the sand at y=900. |
| `garden` | Picket fence, a row of carrots, a watering can (right). |
| `playground` | A slide on the left (x≈180-560) and swings on the right (x≈1340-1880). Stand in between. |
| `bedroom` | Indoors: window with the moon, bed on the right (x≈1260-1860), bookshelf left (x≈260-480). Calm and bedtime stories. |
| `underwater` | Under the sea: fish, bubbles, seaweed and coral. For an adventure or a dream; land animals still stand on the sand at y=900. |

The look also changes by itself: the season follows the video's date (autumn leaves, winter snow, spring flowers) and
the sky and sun vary from day to day. The camera leans towards whoever is speaking.

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
