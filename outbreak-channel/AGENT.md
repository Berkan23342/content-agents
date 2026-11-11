# Outbreak Diary story writer

You run once a day, unattended, as a Claude cloud routine on the GitHub repository `Berkan23342/content-agents`.
Outbreak Diary is a YouTube channel of serialized zombie survival stories told in vertical Shorts (English, for teens
and adults). Several stories run side by side; `outbreak-channel/story/series.json` lists them. Each story has its
own folder `story/<id>/` with a `bible.md`, the waiting scripts in `new/` and the published ones in `used/<date>/`.
Every day the video job (`.github/workflows/outbreak-video.yml`) publishes the next part of every story. Nobody can
answer questions during the run; decide yourself.

**Part N of a story is always Day N of that story.** The video shows "DAY N" from the part number, so never put two
days in one part or one day in two parts. The day is on screen from the first frame: **never open a part with
"Day N."** The first second decides whether a viewer stays (see Shape below).

## Steps

1. `cd outbreak-channel`, read `story/series.json` and run `python3 scripts/diarycheck.py --seasons`. It shows every
   slot's story, how far it is, and whether a new story is due (see Seasons). Fix any `problem:` line it prints.
2. For every story, count the scripts in `story/<id>/new/`. A story with 2 or more needs nothing, and so does a story
   whose finale is already written. Any other story needs parts until it has 2 (never past its finale). If no story needs anything, write the current date and time into
   `story/harbor-view/new/.heartbeat`, commit only that file and push it (step 6). Every push to a `new/` folder starts
   the video job, so the push matters even without a new part.
3. For each story that needs parts:
   - Read its `bible.md`, the whole file.
   - Read its last three parts: the highest-numbered scripts in `new/`, or in `used/*/` if `new` is empty.
   - If the part you are about to write is the day an earlier vote decides, read `story/votes.json` (see Viewers
     decide).
   - Once a week, read the Outbreak Diary part of `../stats/latest.md` (see Our own numbers).
4. Write the next part as `story/<id>/new/ep-NNNN.json`, where `episode` is the next number. Continue exactly where the
   last part ended: answer its cliffhanger first, then move the story forward. Use only the scenes the story's bible
   allows.
5. Check it with `python3 scripts/diarycheck.py story/<id>/new/ep-NNNN.json`. It must print `ok`; fix any
   `episode error`. The checker also refuses a part that:
   - skips or repeats a part number,
   - reuses a title or a trend link,
   - shares too many phrases with any earlier script.

   The video job refuses such a part too, so a repeat is never published. Then update the story's `bible.md`:
   - **Current state:** after which part (= day), who is where, supplies, what they know, open threads.
   - **Episode log:** add one line.
   Repeat steps 4-5 until every story has 2 parts waiting.
6. Re-read the new parts once as a viewer:
   - Would someone who has never seen the story stop scrolling at the first line?
   - Is the last line a real cliffhanger?
   - Does every scene match the text?
   - Is part N really day N?
7. Commit the new scripts and the updated bibles, and push to `main`: `git push origin HEAD:main`. If the push is
   rejected, run `git pull --rebase origin main` and push again.
8. Final message: one line per new part, giving the story, part number, title and what happens.

## Seasons: every story ends, and a new one begins

Our numbers (2026-11-10): Day 1 of a story brings most of the views and nearly all the new subscribers (Harbor View
Day 1: 1,255 views and 8 subscribers; later days 100-200 views). A viewer who lands on Day 9 often swipes away. So
stories are short seasons of 10-15 days, and a fresh Day 1 arrives every week or two.

- Every serial has `"finale": N` in `story/series.json`: Day N is its last part. The checker refuses Day N+1.
- **Writing the finale.** Follow the bible's Season plan. Answer the big questions, give the characters a real
  ending and close on one strong image. No cliffhanger that needs another day; the end card says THE END.
- **The next story.** As soon as a story's finale script exists (`--seasons` says "the NEXT STORY ... is due now"),
  create the story that takes over its slot, in the same run:
  1. **Premise.** Use an approved `outbreak-...` idea for a new serial if there is one; else build one from
     `trends/latest.md`, made our own (never copy). It must be clear in one line and grab in one second: a place, a
     person, a rule or a threat ("the infected follow light, and my job is the lighthouse").
  2. **Folder.** `story/<new-id>/` with `bible.md` (same sections as the other bibles: The world, The infected,
     People, Season plan ending on its finale, Voices, Rules for every part, Places, Current state, Episode log) and
     `new/`.
  3. **series.json.** Append an entry after the ending story, with the same `slot`, `publish` and `weekdays`. Give it
     its own `name`, `about`, `tagline` (one line of at most 42 characters, shown at the top of every part for viewers
     who land in the middle), `finale` (10-15), `grade` (a colour unlike the others), and:
     - `narrator`: one of `nicole`, `isabella`, `heart`, `grace`, `ruth`, `tess`, not one telling another running
       story;
     - `frame`: `diary`, `camcorder`, `journal` or `broadcast` (a narrator on air: her voice sounds like a radio), not
       one another running story uses;
     - `cast`: the speaking characters. Their voice files are in `voices/`; a new character borrows one with
       `"voices": {"marta": "woman"}` (male characters may use male voices).
  4. **Day 1 and Day 2.** Write both into `new/`. Day 1 must work for someone who knows nothing: the premise in the
     first two beats, a strong hook first, and a cliffhanger last.
  5. Run `--seasons` again: no `problem:` lines. A story's slot stays empty (and the video job fails loudly) if its
     successor is missing when the finale is out, so never leave this for later.
- **The full-story video.** The day after a finale is published, `.github/workflows/outbreak-film.yml` turns the
  whole season into one horizontal video (all days, with chapters), because Shorts views do not count towards
  YouTube's watch hours. When you write a finale, also add to that story's entry in `series.json`:
  `"film": {"title": "...", "intro": "...", "outro": "..."}`. `--seasons` reports a `problem:` until it is there.
  - `title`: what the story is, in at most 60 characters, a phrase a viewer would search for ("Trapped on the 9th
    Floor With My Dog"). The video is called "<title> | The Full Zombie Story, All N Days".
  - `intro`: two or three sentences the narrator says at the very start: who she is, where she was when it began, and
    that these are all N days. No spoilers.
  - `outro`: one or two sentences after the last day, ending with "A new story has already begun on Outbreak Diary."
- The ending story keeps its folder; never delete it.

## Viewers decide

Comments push a video in YouTube's feed, and a story the viewers steer is a reason to follow it. So about twice a
season a serial asks the viewers to choose, and the story really follows the majority.

- **Asking.** In the part for Day N, add `"vote": {"question": "Which way do we go?", "options": ["BRIDGE",
  "STAIRS"], "decides": N+3}`.
  - The answer comes on Day N+3, because Days N+1 and N+2 are already written when the votes are counted. So ask about
    a decision that is a few days away ("Ruth says the bridge will hold. Dev says the stairs. We go in three days.
    Which way?"), never about tomorrow's cliffhanger. Days N+1 and N+2 must not decide it.
  - Both options are real and the story can go on either way. No vote can kill an animal or end the story badly.
  - The options are two single words in capitals, 3-10 letters. The last beat asks the question out loud and names
    both words (it can still be the cliffhanger). The video ends on a voting card instead of "Follow for Day N+1",
    and the description tells viewers to comment one word.
  - Never on Day 1, never in a special, never past the finale (N+3 must be at most the finale), and no new vote until
    the last one has been answered. The checker refuses a vote while the channel cannot read comments yet
    (`story/votes.json` `"_reader"`); then write the part without one.
- **Answering.** Every morning `scripts/votes.py` counts the comments into `story/votes.json` (one vote per person).
  When you write Day N+3, read the story's entry for Day N and add
  `"voted": {"from": N, "pick": "BRIDGE", "votes": {"BRIDGE": 7, "STAIRS": 3}}`, copying the counted `votes` exactly.
  The story follows the option with the most votes (a tie: you choose between the tied ones). If nobody voted, leave
  `"votes": {}` and choose yourself. The video then shows "YOU VOTED: BRIDGE · 7 – 3" at the start of the day; the
  narration stays in the story (the narrator does not talk about comments).
- Record each vote and its result in the bible's Episode log.

## Our own numbers

`../stats/latest.md` (written every Monday from our channels' public numbers) shows how our own parts did: views two
days after publishing, likes and comments, by story, Day 1s apart, specials, and every recent part with its event.
Read the Outbreak Diary part once a week. Lean towards what scored best (kinds of hook, events, places, specials'
kinds) and away from the weakest. Look for patterns over several parts, never one lucky video, and keep every variety
rule.

## Approved ideas

`ideas/approved.md` (repository root) lists ideas the channel owner approved each week. An `outbreak-...` idea is
either a premise for a special or a direction for one of the serials (the idea says which). Use approved ideas before
your own:
- Write the first approved idea that no script uses yet, as the next special or as the next part of that serial.
- Keep the serial's continuity.
- Record it in the script as `"idea": "<id>"`.

## Specials and trends

- **Trends.** `trends/latest.md` (at the repository root) lists the fastest-growing zombie and horror Shorts of the
  last month, updated every Monday and Thursday. Read the `outbreak` table before writing. Notice what works: premises
  built on a rule ("if you hear three knocks, don't open"), what-ifs, a clear goal, a hook in the first second. Use those
  ideas in our own stories.
- **Never copy.** Never reuse anyone's script, title, characters, pictures or music. Never retell another video's plot
  beat by beat. Take a premise or a hook and build something new in our world.
- **Specials** (`story/specials/`) are one-part stories, complete in about a minute. They are published on Tuesdays;
  keep 2 waiting like every story.
  - Each special has its own narrator (always a woman) and its own characters, in the same rainy city of Port Ellis or
    near it.
  - The idea starts from a trending premise in `trends/latest.md`, made our own. Record it in
    `"inspired_by": "<link> (premise only: ...)"`.
  - Set `"narrator"` to one of `grace`, `ruth`, `tess` (the serials keep `nicole`, `isabella`, `heart`), a different
    one from the last special.
  - Set `"kind"`, how the special is told, a different one from the last special. Each kind has its own look:
    - `story`: a survivor tells it, like the serials (the diary look).
    - `broadcast`: the narrator is a radio or TV presenter on an emergency broadcast. Her voice sounds like a radio, the
      screen shows LIVE, EMERGENCY BROADCAST and a news ticker. Write it as a broadcast that slowly goes wrong.
    - `found`: a phone recording someone left behind (REC light, timecode). The narrator talks to the camera.
    - `journal`: pages of a handwritten journal someone found (paper edges, handwriting). Dated entries, short.
  - Speakers in specials are `man`, `woman`, `boy`, `girl` and `announcer`.
  - The video shows the specials' name instead of a day. The first line is a strong hook and the last line a twist;
    the video ends with "THE END...?". The specials have no bible; read the earlier ones in `story/specials/` so you never repeat
    an idea.

## Every part is about something different

- Set `"event"` to what the part is mostly about: `supplies`, `shelter`, `escape`, `rescue`, `stranger`, `sickness`,
  `weather`, `signal`, `loss`, `discovery`, `trap`, `horde`, `journey`, `repair`, `plan`, `quiet`, `split`,
  `reunion`.
- Never the same event as the story's previous part. The checker also refuses an event that 3 of the waiting or
  recently published parts (all stories) already have: then the channel would tell the same day twice.
- Each story has its own look (story/series.json `frame`): Harbor View is a diary, Floor 41 a phone recording (REC,
  timecode), Pine Hollow a handwritten journal. Write in a way that fits: Floor 41's narrator can talk to the phone,
  Pine Hollow's writes short dated entries.

## Writing rules

- **Voice:** first person, past tense ("I"), in the story's narrator's voice. Short sentences, concrete details, a
  little dry humour. Read the bible's People and The infected sections and never break the rules there.
- **Length:** 100-125 words over 8-14 beats; each beat is one or two sentences, at most 24 words. A part lasts about a
  minute.
- **Shape:**
  - The first beat is the hook, heard in the first second, with no title card before it. Open on the moment itself:
    danger, a sound, a choice, a question ("Marek opened the cupboard. Under his arm, wriggling, was Biscuit."). Never
    start with "Day N."; the checker refuses it, because the day is on screen.
  - The hook also has to work for a new viewer who missed earlier days: name what is at stake, not an in-joke.
  - The last beat is a cliffhanger (on a finale: the ending). A final sting sound is added automatically.
  - Every part has one new problem, discovery or decision. Keep the season plan in mind, but surprise the viewer.
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
