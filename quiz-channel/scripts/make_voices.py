"""Makes the hosts' reference voices (voices/<name>.wav) with Kokoro. Chatterbox copies these voices when it reads a
snack (scripts/snack.py HOSTS). Run once after adding a host; the WAVs are committed.

  ../kids-channel/.venv/bin/python scripts/make_voices.py [name ...]
"""
import os
import sys

import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOKORO = os.path.join(os.path.dirname(ROOT), "kids-channel", "assets", "kokoro")
# a lively, varied paragraph: Chatterbox copies the tone as well as the voice
TEXT = ("Okay, here's something you probably never noticed. Every single day, you use it without thinking. "
        "But once you see how it really works, you'll never look at it the same way again. Ready? Let's go!")
VOICES = {  # host name -> Kokoro voice (all female; Outbreak Diary uses nicole, isabella and heart)
    "bella": "af_bella", "sarah": "af_sarah", "emma": "bf_emma", "aoede": "af_aoede",
    "kore": "af_kore", "alice": "bf_alice", "lily": "bf_lily", "sky": "af_sky",
}


def main():
    from kokoro_onnx import Kokoro

    k = Kokoro(os.path.join(KOKORO, "kokoro-v1.0.onnx"), os.path.join(KOKORO, "voices-v1.0.bin"))
    for name in sys.argv[1:] or VOICES:
        voice = VOICES[name]
        samples, sr = k.create(TEXT, voice=voice, speed=1.0, lang="en-gb" if voice.startswith("b") else "en-us")
        out = os.path.join(ROOT, "voices", f"{name}.wav")
        sf.write(out, samples, sr)
        print(f"{out}: {len(samples) / sr:.1f}s")


if __name__ == "__main__":
    main()
