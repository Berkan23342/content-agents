"""Chatterbox narration for Outbreak Diary. It needs PyTorch, so it runs in its own Python environment
(.venv-cb locally, see the workflow for the server) and scripts/diary.py calls it with a list of lines.

  .venv-cb/bin/python scripts/voice_cb.py jobs.json

jobs.json is a list of {"text", "ref", "out", "exaggeration", "cfg", "seed"}; "ref" is a short WAV whose voice is
copied (voices/*.wav, all made with Kokoro). Each "out" is written as a WAV at Chatterbox's sample rate.
Chatterbox (MIT licence) adds an inaudible watermark to everything it makes.
"""
import json
import os
import sys
import time

import soundfile as sf
import torch
from chatterbox.tts import ChatterboxTTS


def main():
    jobs = json.load(open(sys.argv[1]))
    device = os.environ.get("CB_DEVICE", "cpu")
    model = ChatterboxTTS.from_pretrained(device=device)
    for i, job in enumerate(jobs, 1):
        t0 = time.time()
        torch.manual_seed(job.get("seed", 0))
        wav = model.generate(job["text"], audio_prompt_path=job["ref"], exaggeration=job["exaggeration"],
                             cfg_weight=job["cfg"])
        sf.write(job["out"] + ".tmp.wav", wav.squeeze(0).numpy(), model.sr)
        os.replace(job["out"] + ".tmp.wav", job["out"])
        print(f"voice {i}/{len(jobs)}: {wav.shape[-1] / model.sr:.1f}s in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
