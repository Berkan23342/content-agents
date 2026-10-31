# Content agents

Daily, fully automatic content for two projects. It runs in the cloud, so no computer needs to be on.

| What | Who makes the idea | Who renders and posts |
|---|---|---|
| **Bubbly Kids TV** (YouTube, kids): a learning video at 10:00, a fun video at 18:00 and two vertical Shorts at 13:00 and 21:00, Istanbul time | Claude cloud routine writes a new story script to `kids-channel/stories/new/` every morning | `.github/workflows/kids-video.yml` |
| **Makulbul** (Instagram + TikTok): one reel a day | Claude cloud routine researches and writes `makulbul-social/content/<day>/spec.json` + `caption.txt` | `.github/workflows/makulbul.yml` (runs on that push) |

- `kids-channel/`: Remotion + Kokoro TTS + FluidSynth video pipeline. `AGENT.md` is the story writer's guide.
- `makulbul-social/`: Remotion reels and posts in the makulbul.com style. `AGENT.md` is the content agent's guide.

Credentials live only in GitHub Actions secrets: `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_TOKEN`, `INSTAGRAM_JSON`, `TIKTOK_JSON`.
