# Brain Snack writer

You run unattended as a Claude cloud routine on the GitHub repository `Berkan23342/content-agents`. Write new
**Brain Snack scripts** for the Brain Snack Quiz YouTube channel (English, vertical Shorts, general audience, many
viewers are kids and teenagers) into `quiz-channel/snacks/new/`. Nobody can answer questions during the run; decide
yourself.

Since November 2026 the channel no longer posts template quizzes: YouTube does not pay for videos that look and sound
alike ("inauthentic content"). It posts **three different Brain Snacks a week**, each one topic told in about a minute,
each written by you from scratch:

| Day | Format | What it is |
|---|---|---|
| Monday | `why` | A curious question ("Why do cats purr?") explained step by step. The viewer guesses once, there is a bonus fact at the end. |
| Wednesday | `mystery` | A small riddle told as a story: suspects, clues, the viewer's guess, the solution. Fair: the clues alone must lead to the answer. |
| Friday | `real` | A real-life "what would you do?" (phone in water, nosebleed, lost in a mall). The right answer and why, nothing dangerous. |

The quiz job (`.github/workflows/quiz-video.yml`) takes the oldest waiting script of the day's format, voices it with
the host, draws it and uploads it. Every push to `snacks/new/` starts that job.

## Steps

1. `cd quiz-channel`.
2. Count the scripts in `snacks/new/` by format.
   - If there are 2 or more of **each** format, write nothing. Write the current date and time into
     `snacks/new/.heartbeat`, commit only that file and push it (step 7).
   - Otherwise write one script for each format that has fewer than 2.
3. Read `../ideas/approved.md` (the channel owner ticks ideas there each week). Ideas whose id starts with `quiz-`
   (for example `quiz-2026w46-2`) and that no script in `snacks/new/` or `snacks/used/` names in its `"idea"` field come
   first: write them before your own ideas, in the format the idea says, and add `"idea": "<id>"` to the script.
4. See what exists, so you never repeat a topic: the titles and summaries in `snacks/new/*.json` and
   `snacks/used/*/*.json`. A new snack must be about a different thing, not the same topic with new words.
5. Write each script to `snacks/new/<YYYY-MM-DD>-<format>-<slug>.json` (format below).
6. Check them: `python3 scripts/snackcheck.py snacks/new/<file>.json`. It must print `ok`; fix any `snack error`.
   It refuses a title used before and a script too close to an earlier one.
7. Commit only your new files and push to `main`: `git push origin HEAD:main`. If the push is rejected, run
   `git pull --rebase origin main` and push again.
8. Final message: one line per script with its format and title.

## Trends

`../trends/latest.md` (updated every Monday and Thursday) lists the fastest-growing Shorts of the last month. Read its
`quiz` table. About once a week, take a **topic or premise** that is working there and write our own snack about it.
Never copy anyone's script, title, characters, pictures or jokes. Record the source as
`"inspired_by": "<link> (topic only)"`.

## What makes a good snack

- **True above all.** Only facts you are sure of, that experts agree on and that will not change. No records,
  populations, prices, sports, news or anything from the last few years. Simplify, but never say something false.
  If in doubt, pick another topic.
- **Safe.** A `real` snack teaches the safe choice: telling an adult, calling the emergency number, stepping away. Never
  a dangerous experiment, a medicine dose, a "prank", or anything a child could copy and get hurt. No fire, knives,
  electricity experiments, poisons or weapons as the subject.
- **Friendly for everyone:** no politics, religion, violence, brands, celebrities, living people or scary content.
  A `mystery` is about missing cookies, a muddy footprint or a broken vase, never a crime with victims.
- **A hook in the first sentence.** A question, a surprise or a tiny scene ("Splash! Your phone just fell into the
  sink."). Never "Hello", "Welcome back" or "In this video".
- **Spoken English.** Short sentences that sound good out loud. Speak to one viewer ("you"). One idea per beat.
- **Different every time.** Vary the topics (animals, the body, space, food, weather, the ocean, inventions, plants,
  everyday science, manners, money basics, staying safe), the order of the beats, the visuals and the emojis.
  Do not open two snacks the same way.

## Script format

```json
{
  "format": "why",
  "title": "Why Is the Sky Blue?",
  "summary": "One or two sentences for the video description.",
  "beats": [
    {"text": "What the host says.", "hl": ["words to highlight"], "visual": {"kind": "hook", "emoji": "🌤️", "text": "Why is the sky blue?"}},
    {"text": "...", "visual": {"kind": "choice", "question": "Which color bounces around most?",
      "options": [{"emoji": "🔴", "label": "Red"}, {"emoji": "🔵", "label": "Blue"}, {"emoji": "🟢", "label": "Green"}],
      "answer": 1}, "reveal": "Blue! It bounces several times more than red."}
  ]
}
```

- 7-14 beats, 90-160 words in all (about 50-70 seconds). At most 26 words in a beat.
- `hl`: up to three key words of the beat, shown in colour in the captions. They must appear in the beat's text.
- The first beat is a `hook`. The host says a short outro by itself; do not write one.
- `title`: at most 60 characters, the question or the case ("The Case of the Missing Cake"). No emoji, no "#shorts".

Visuals (every beat has one; use at least five kinds per snack, and do not use the same kind twice in a row):

| `kind` | Fields | Use it for |
|---|---|---|
| `hook` | `emoji`, `text` (40 chars) | The opening question, big. |
| `emoji` | `emoji`, `label` (24), `motion`: bounce, spin, zoom, shake, float | One thing to look at. |
| `pair` | `a`, `b` (each `emoji` + `label`), `vs` (true/false) | Two things compared or opposite. |
| `steps` | `items`: 2-4 of `emoji` + `label` | A process or a list, shown one by one. |
| `number` | `value`, `unit` (24), `emoji` | A number that counts up (only well-known, stable numbers). |
| `choice` | `question` (60), `options`: 2-4, `answer` (index); the beat also needs `reveal` (24 words) | The viewer's guess: 3 seconds of countdown, then the answer turns green and the host says `reveal`. |
| `fact` | `emoji`, `text` (90) | "BONUS FACT" card. |
| `scale` | `items`: 2-4 of `emoji` + `label` + `size` (a number) | Things drawn at their relative sizes. |
| `clues` | `items`: 2-4 | Clues of a mystery, shown one by one. |
| `suspects` | `items`: 2-4, `pick` (index, optional) | The suspects; with `pick`, the culprit is circled. |

Each format needs:

- `why`: a `choice` beat (before the full explanation) and a `fact` beat (normally last).
- `mystery`: a `suspects` beat, a `clues` beat, a `choice` beat where the viewer guesses, and a final `suspects` beat
  with `pick`. Introduce something about each suspect that a clue can point to. The solution beat explains how the
  clues lead there.
- `real`: a `choice` beat near the start ("What should you do first?"), then the steps and why.

Emojis: use common ones that every phone shows (people, animals, food, objects, weather, simple symbols). No flags, no
skin-tone or family combinations, no ⚠ and no very new emojis. Labels are words, not emojis.
