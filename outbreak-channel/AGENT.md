# Outbreak Diary story writer

You run once a day, unattended, as a Claude cloud routine on the GitHub repository `Berkan23342/content-agents`.
Outbreak Diary is a YouTube channel of zombie survival stories told in vertical Shorts (English, for teens and adults).
Nobody can answer questions during the run; decide yourself.

**Since 2026-11-19 every video is a complete one-part story** (the channel owner: "tek bölümlük, ama hikâyesi
sarmalı"). The serials (Harbor View, Floor 41, Pine Hollow, Dead Air, Last Light, Route 9) are retired: never write
another part of them. Why: a viewer who landed on Day 9 of a serial swiped away, so YouTube stopped showing the
channel; our best videos were always the ones a stranger could follow from the first second (Harbor View Day 1: 1,256
views; the first one-part story: 203). Two stories go out every day (20:00 and 03:00 Istanbul time, US lunch and
evening), both from `story/specials/`.

## Steps

1. `cd outbreak-channel` and run `python3 scripts/diarycheck.py --seasons`: it shows `specials` and how many stories
   are waiting. Fix any `problem:` line it prints.
2. Count the scripts in `story/specials/new/`. Keep **4 waiting** (two days). If 4 or more are waiting, write the
   current date and time into `story/specials/new/.heartbeat`, commit only that file and push it (step 6): every push
   to a `new/` folder starts the video job. Otherwise write stories until 4 are waiting (at most 4 in one run).
3. Before writing, read the titles, summaries and first beats of every script in `story/specials/new/` and
   `story/specials/used/*/` so you never repeat a premise, a twist or a title; read `trends/latest.md` (the `outbreak`
   table) and, once a week, the Outbreak Diary part of `../stats/latest.md`.
4. Write each story as `story/specials/new/ep-NNNN.json`, `episode` being the next number (see One-part stories and
   the Script format below).
5. Check each with `python3 scripts/diarycheck.py story/specials/new/ep-NNNN.json`. It must print `ok`; fix any
   `episode error`. The checker also refuses a repeated title, a trend link used before, a story too similar to an
   earlier one, the same kind or narrator as the previous story, and an over-used event.
6. Re-read every new story once as a stranger scrolling past, then commit them and push to `main`:
   `git push origin HEAD:main`. If the push is rejected, run `git pull --rebase origin main` and push again.
7. Final message: one line per new story: number, title, kind, narrator, and the premise in one sentence.

## One-part stories: complete, and gripping from the first second

- **One idea per story, told whole in about a minute.** A premise a stranger understands in one breath, built on a
  rule, a threat or an impossible choice: "If you hear three knocks, don't open." "The infected follow light, and my job
  is the lighthouse." "My daughter's school bus is the last one out, and I'm the driver."
- **Shape (the spiral):** the hook in the first beat (the danger or the rule, said at once; no lead-in, no "Day N."),
  then each beat raises the stakes or tightens the trap, a turn in the middle (the rule breaks, a mistake, a stranger),
  and an ending that pays off the hook: a twist the viewer did not see coming but that the first beats set up, or one
  strong final image. No "to be continued": the story must feel finished. The video ends on "THE END...?".
- **Every story is new:** a new narrator character, a new place in or near the rainy city of Port Ellis, its own
  characters. Never continue a retired serial, never reuse a twist.
- **Narrator** (`"narrator"`): one of `nicole`, `isabella`, `heart`, `grace`, `ruth`, `tess`, always a woman, a
  different one from the previous story.
- **Kind** (`"kind"`), how it is told, a different one from the previous story; each has its own look:
  - `story`: a survivor tells it (the diary look).
  - `broadcast`: a radio or TV presenter on an emergency broadcast that slowly goes wrong (radio voice, LIVE banner,
    news ticker).
  - `found`: a phone recording someone left behind (REC light, timecode); the narrator talks to the camera.
  - `journal`: pages of a handwritten journal someone found; dated entries, short.
- **Event** (`"event"`): what the story is mostly about: `supplies`, `shelter`, `escape`, `rescue`, `stranger`,
  `sickness`, `weather`, `signal`, `loss`, `discovery`, `trap`, `horde`, `journey`, `repair`, `plan`, `quiet`,
  `split`, `reunion`. Not the previous story's, and not one already in 3 of the waiting and recent stories.
- **Speakers** in these stories are `man`, `woman`, `boy`, `girl` and `announcer`.
- **Trends:** about every other story starts from a premise that is working in `trends/latest.md`, made our own.
  Record it as `"inspired_by": "<link> (premise only: ...)"`. **Never copy:** never reuse anyone's script, title,
  characters, pictures or music, and never retell another video's plot beat by beat.
- **Approved ideas:** `ideas/approved.md` (repository root) lists ideas the channel owner approved. Write an approved
  `outbreak-...` idea that no script uses yet before your own, and record it as `"idea": "<id>"`.

## Writing rules

- **Voice:** first person, past tense ("I"), in the narrator's voice (a `broadcast` may be present tense). Short
  sentences, concrete details, a little dry humour.
- **Length:** 100-125 words over 8-14 beats; each beat is one or two sentences, at most 24 words. A part lasts about a
  minute.
- **Shape:**
  - The first beat is the hook, heard in the first second, with no title card before it. Open on the moment itself:
    danger, a sound, a choice, a question ("Three knocks. Then nothing. Then three knocks again."). Never start with
    "Day N."; the checker refuses it.
  - Name what is at stake at once; a stranger knows nothing.
  - The last beat is the twist or the final image that ends the story. A final sting sound is added automatically.
- **Safe for everyone 13+:** tension and danger, never gore, blood or cruelty. No swearing. Animals never die. Real
  places, brands and people never appear.
- **Highlights (`hl`):** in most beats, mark the one or two words that hit hardest. They show in red.
- **Sound (`sfx`):** use sound effects sparingly, one or two per beat at most, and only where the text earns them.

## Script format

```json
{
  "episode": 4,
  "title": "Footsteps Upstairs",
  "summary": "One sentence for the YouTube description, without spoilers for the ending.",
  "ambience": "rain",
  "event": "stranger",
  "beats": [
    {"scene": "room", "light": "candle", "guest": "okafor", "dog": "sleep", "cam": "push",
     "text": "Someone was walking across my ceiling. I live on the top floor.", "hl": ["ceiling"], "sfx": ["steps@1.0"]},
    {"scene": "hallway", "light": "flicker", "zombie": true, "text": "...", "hl": ["..."]}
  ]
}
```

| Field | Meaning |
|---|---|
| `episode` | The part number, which is also the day. There is no separate `day` field. |
| `title` | At most 28 characters. It goes into the YouTube title after "Day N:". |
| `ambience` | The background bed: `rain`, `wind`, `night` or `none`. |
| `event` | What the part is mostly about (see "Every part is about something different"). |
| `kind`, `narrator` | Specials only: how it is told and who tells it (see Specials). |
| `vote` | Optional: this part asks the viewers to choose (see Viewers decide). |
| `voted` | Required on the day a vote decides: what the viewers chose (see Viewers decide). |
| `text` | What Sam says in this beat. It is also the caption. |
| `hl` | Words from `text` to show in red. |
| `sfx` | A list of sounds: `"name"` plays at the start of the beat, `"name@1.5"` 1.5 seconds in. |
| `cam` | `push` (default, a slow zoom in), `pull`, `left`, `right` or `still`. |
| `tone` | `night` (default), `dawn` or `dusk`. |
| `rain`, `fog`, `flashlight`, `alarm` | `true` adds rain, low fog, a moving flashlight in the dark, or a red danger pulse. |
| `hold` | Seconds of silence after the line (default 0.35). Use 0.8-1.2 before a reveal. |
| `speaker` | A character from the story's cast says `text` in their own voice; see the Voices section of its bible. Leave it out for narration. The narrator is always the woman telling the story. |

**Sounds:** `heartbeat`, `knock`, `bang` (pounding on a door, shakes the camera), `creak`, `static`, `siren`, `groan`,
`glass`, `steps`, `sting`, `thud`, `scratch`, `buzz` (phone), `click` (lock or switch), `drip`, `thunder`, `whoosh`.

### Scenes and their settings

Each story's bible says which scenes belong to it. For example, `room`, `building` and `peephole` are Sam's apartment
in Harbor View.

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
| `tower` | Meridian Tower from the street: a glass skyscraper with floor 41 lit. | `zombies` 0-12 at the base, `fire`, `heli` |
| `office` | The open-plan office on floor 41, with the city behind the glass. | `light` on/flicker/off, `zombie` (a shape behind the meeting room's frosted glass), `guest` dev, `fire` (default true) |
| `elevator` | Elevator doors with the floor number above. | `doors` closed/open/gap (hands reaching through), `floor` 0-52, `power` (false = red emergency light) |
| `forest` | Pine woods at night around the lake. | `zombies` 0-12 between the trees, `cabin` (the cabin's lit window far away), `fire` |
| `cabin` | The ranger cabin: log walls, a stone fireplace, a window on the woods. | `light` fire/lantern/off, `guest` ava, `zombie` (a figure outside the window) |
| `truck` | Inside Nora's pickup at night, the road in the headlights. | `zombies` 0-8 in the lights, `lights` (headlights, default true), `wipers` |
| `lake` | The lake at night: far shore, a dock, the moon on the water. | `zombies` 0-8 (heads rising from the water), `canoe` |
| `gas_station` | A gas station on an empty road at night. | `zombies` 0-10, `light` on/flicker/off, `car` |
| `supermarket` | A supermarket aisle. | `zombies` 0-5 down the aisle, `light` on/flicker/off, `empty` (bare shelves) |
| `hospital` | A hospital corridor with a gurney and swing doors. | `zombies` 0-5, `light` on/flicker/off |
| `school` | A school corridor lined with lockers. | `zombies` 0-5, `light` on/flicker/off |
| `subway` | Inside a subway car (works as a bus or train too). | `zombies` 0-5, `light` on/flicker/off (off = red emergency light), `moving` |
| `skybridge` | A glass bridge between two towers, high over the city. | `zombies` 0-5, `light` on/flicker/off, `cracks` |
| `lobby` | An apartment lobby: mailboxes, the lift, glass front doors. | `zombies` 0-4 (pressing on the glass), `light` on/flicker/off, `broken` |

**Variety.**
- Use the same scene for two or three beats in a row when the action stays in one place. The video cuts between a wide
  shot and close-ups, so this feels like one scene filmed from several angles.
- Change the scene when the narrator looks at something new.
- A part needs at least 4 different scenes (a special at least 3), and no scene may fill more than 40% of the beats.
- A part must not use almost the same set of places as the story's previous part. The checker enforces all of this.
- Take the characters somewhere new often: the lake, the gas station, the supermarket, the school, the hospital, the
  subway, the skybridge or the lobby. Each place is drawn a little differently in every part, and every story has its
  own colour.
