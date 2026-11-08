# Content agents

Daily, fully automatic content for four projects. It runs in the cloud, so no computer needs to be on.

| What | Who makes the idea | Who renders and posts |
|---|---|---|
| **Bubbly Kids TV** (YouTube, kids): a learning video at 10:00, a fun video at 18:00 and two vertical Shorts at 13:00 and 21:00, Istanbul time | Claude cloud routine writes a new story script to `kids-channel/stories/new/` every morning | `.github/workflows/kids-video.yml` |
| **Brain Snack Quiz** (YouTube, general audience): a Brain Snack on Mondays ("Why?"), Wednesdays ("Mystery") and Fridays ("Real life") at 19:00 Istanbul time | A Claude cloud routine writes each script to `quiz-channel/snacks/new/`; the host is voiced by Chatterbox | `.github/workflows/quiz-video.yml` |
| **Outbreak Diary** (YouTube, teens and adults): serialized zombie survival stories running side by side (`story/series.json`), one new day of each every day, plus a one-part Special every Tuesday and Friday | A Claude cloud routine writes the next parts to `outbreak-channel/story/<story>/new/` and keeps each story's `bible.md` up to date | `.github/workflows/outbreak-video.yml` |
| **Makulbul** (Instagram + TikTok): one reel a day | Claude cloud routine researches and writes `makulbul-social/content/<day>/spec.json` + `caption.txt` | `.github/workflows/makulbul.yml` (runs on that push) |

- `kids-channel/`: Remotion + Kokoro TTS + FluidSynth video pipeline. `AGENT.md` is the story writer's guide.
- `quiz-channel/`: Remotion Brain Snacks (`src/Snack.tsx`, `scripts/snack.py`, checked by `scripts/snackcheck.py`); it borrows the sound effects and mixing from `kids-channel/scripts/` and the voice engine from `outbreak-channel/`. `AGENT.md` is the snack writer's guide. The old template quiz (`scripts/quiz.py`, `src/Quiz.tsx`) is retired since 2026-11-08.
- `outbreak-channel/`: Remotion story Shorts in a flat, dark vector style, with synthesized horror sounds (`scripts/dread.py`). `AGENT.md` is the story writer's guide.
- `trends/`: twice a week (`.github/workflows/trends.yml`) `scan.py` lists the fastest-growing videos in our niches in `trends/latest.md`; the writer agents borrow topics, premises and hooks from it, never scripts or pictures.
- `makulbul-social/`: Remotion reels and posts in the makulbul.com style. `AGENT.md` is the content agent's guide.

Credentials live only in GitHub Actions secrets: `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_TOKEN` (Bubbly Kids TV), `QUIZ_YOUTUBE_TOKEN` (Brain Snack Quiz), `OUTBREAK_YOUTUBE_TOKEN` (Outbreak Diary), `INSTAGRAM_JSON`, `TIKTOK_JSON`.
A channel token is made once on a Mac with `kids-channel/.venv/bin/python kids-channel/scripts/upload_youtube.py --sign-in --token <file>` (pick the channel on Google's page), then `gh secret set <NAME> < <file>`.

## Weekly idea approval

Every Sunday a Claude routine writes `ideas/proposals/<year>-W<week>.md`: six ideas each for the kids channel and for
Outbreak Diary, each with a short Turkish summary. `.github/workflows/ideas.yml` opens it as a GitHub issue ("Haftalık
fikirler") with a checkbox per idea. Ticking boxes, for example in the GitHub phone app, writes the approved ideas to
`ideas/approved.md`. The writer agents use approved ideas first; with nothing approved they decide for themselves.
