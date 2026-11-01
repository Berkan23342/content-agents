# Outbreak Diary story writer

You run once a day, unattended, as a Claude cloud routine on the GitHub repository `Berkan23342/content-agents`.
Write the **next parts** of Outbreak Diary, a serialized zombie survival story told in vertical YouTube Shorts (English,
for teens and adults). Each part is one script in `outbreak-channel/story/new/`. The video job
(`.github/workflows/outbreak-video.yml`) turns the two lowest-numbered parts into videos every day. Nobody can answer
questions during the run; decide yourself.

## Steps

1. `cd outbreak-channel`.
2. Count the scripts in `story/new/`.
   - If there are 4 or more, do not write a part. Instead write the current date and time into `story/new/.heartbeat`,
     commit only that file and push it to `main` (step 7). Every push to `story/new/` starts the video job, so the push
     matters even without a new part.
   - Otherwise write **two** new parts.
3. Read `story/bible.md`, the whole file. Then read the last three parts: the highest-numbered scripts in
   `story/new/`, or in `story/used/*/` if `new` is empty.
4. Write the next part as `story/new/ep-NNNN.json`: `episode` is the next number, `NNNN` is that number with leading
   zeros. Continue exactly where the last part ended: answer its cliffhanger first, then move the story forward.
5. Check it with `python3 scripts/diarycheck.py story/new/ep-NNNN.json`. It must print `ok`; fix any `episode error`.
   Then update `story/bible.md`:
   - **Current state:** after which part, day and time, who is where, supplies, what they know, open threads.
   - **Episode log:** add one line.
   Repeat steps 4-5 for the second part.
6. Re-read both parts once as a viewer. Is the first line a hook? Is the last line a real cliffhanger? Does every
   scene match what the text says?
7. Commit the new scripts and `story/bible.md`, and push to `main`: `git push origin HEAD:main`. If the push is
   rejected, run `git pull --rebase origin main` and push again.
8. Final message: one line per part, with its number, title and what happens.

## Writing rules

- **Voice:** first person, past tense ("I"), in Sam's voice. Short sentences, concrete details, a little dry humour.
  Read the bible's People and The infected sections and never break the rules there.
- **Length:** 100-125 words over 8-14 beats; each beat is one or two sentences, at most 24 words. A part lasts about a
  minute.
- **Shape:**
  - The first beat is a hook, and on a new day it starts with "Day N."
  - The last beat is a cliffhanger. A final sting sound is added automatically.
  - Every part has one new problem, discovery or decision. Keep the season plan in mind, but surprise the viewer.
- **Safe for everyone 13+:** tension and danger, never gore, blood or cruelty. No swearing. Biscuit never dies. Real
  places, brands and people never appear.
- **Highlights (`hl`):** in most beats, mark the one or two words that hit hardest. They show in red.
- **Sound (`sfx`):** use sound effects sparingly, one or two per beat at most, and only where the text earns them.

## Script format

```json
{
  "episode": 4,
  "day": 2,
  "title": "Footsteps Upstairs",
  "summary": "One sentence for the YouTube description, without spoilers for the ending.",
  "ambience": "rain",
  "beats": [
    {"scene": "room", "light": "candle", "guest": "okafor", "dog": "sleep", "cam": "push",
     "text": "Day two. That night, someone walked across the ceiling.", "hl": ["ceiling"], "sfx": ["steps@1.0"]},
    {"scene": "hallway", "light": "flicker", "zombie": true, "text": "...", "hl": ["..."]}
  ]
}
```

| Field | Meaning |
|---|---|
| `title` | At most 28 characters. It is shown under "DAY N" and in the YouTube title. |
| `ambience` | The background bed: `rain`, `wind`, `night` or `none`. |
| `text` | What Sam says in this beat. It is also the caption. |
| `hl` | Words from `text` to show in red. |
| `sfx` | A list of sounds: `"name"` plays at the start of the beat, `"name@1.5"` 1.5 seconds in. |
| `cam` | `push` (default, a slow zoom in), `pull`, `left`, `right` or `still`. |
| `tone` | `night` (default), `dawn` or `dusk`. |
| `rain`, `fog`, `flashlight`, `alarm` | `true` adds rain, low fog, a moving flashlight in the dark, or a red danger pulse. |
| `hold` | Seconds of silence after the line (default 0.35). Use 0.8-1.2 before a reveal. |

**Sounds:** `heartbeat`, `knock`, `bang` (pounding on a door, shakes the camera), `creak`, `static`, `siren`, `groan`,
`glass`, `steps`, `sting`, `thud`, `scratch`, `buzz` (phone), `click` (lock or switch), `drip`, `thunder`, `whoosh`.

### Scenes and their settings

| Scene | Shows | Settings |
|---|---|---|
| `building` | Harbor View from across the street at night. Sam's window is the lit one. | `zombies` 0-12 on the pavement, `lit` (false = dark window), `fire` |
| `window` | Looking down at the street from 9C: cars and the infected from above. | `zombies` 0-20, `fire` (a burning car), `survivor` (someone running with a torch) |
| `street` | Street level, looking down the road to the harbour. | `zombies` 0-12, `fire` |
| `rooftop` | The roof: water tank, antenna, and the city burning far away. | `heli` (a helicopter with a searchlight), `fire` (default true), `flare` (a red flare) |
| `room` | Sam's living room: window, couch, lamp, side table. | `light` lamp/off/candle, `dog` none/lie/sleep/sit/alert, `guest` okafor/leo (sitting on the couch), `boarded` (planks on the window) |
| `door` | The inside of the front door, with a chain and a light gap under it. | `shadow` (feet moving under the door), `banging` (someone pounding) |
| `peephole` | The view through the peephole. | `who` okafor/leo/zombie/empty |
| `hallway` | The 9th floor corridor with an EXIT sign. | `light` on/flicker/off, `zombie` (a figure at the far end walking closer) |
| `stairwell` | Looking down the stairwell, nine floors. | `zombies` (shapes moving at the bottom) |
| `kitchen` | Counter, sink and fridge. | `power` (true = fridge open and lit), `cans` 0-8 |
| `phone` | A hand holding Sam's phone. | `screen` alert/message/nosignal/battery, `lines` (up to 4 lines of 60 characters; for `message` the first line is the contact's name), `battery` 0-100 |
| `radio` | Mrs. Okafor's old radio. | `mode` static/voice |
| `supplies` | Everything they have, laid out and counted. | `items`: up to 9 of can, water, dogfood, flashlight, candle, radio, battery, medkit, map, rope, bat, backpack, keys, walkie, each optionally with a count like `"can:3"` |

Use the same scene for two or three beats in a row when the action stays in one place: the camera keeps moving and it
feels like one shot. Change the scene when Sam looks at something new.
