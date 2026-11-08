"""Word-timed captions for narrated videos (Outbreak Diary, Brain Snack). Needs numpy."""
import re

import numpy as np


def chunks_for(text, hl, t0, t1, f, talk=False):
    """Splits a line into 1-3 word captions, timed by word length and punctuation across [t0, t1] seconds."""
    tokens = text.split()
    weights = []
    for w in tokens:
        k = len(re.sub(r"[^A-Za-z0-9]", "", w)) + 2
        k += 6 if w.endswith("...") else 5 if w[-1] in ".!?" else 3 if w[-1] in ",;:" else 0
        weights.append(k)
    edges = np.concatenate([[0], np.cumsum(weights)]) / sum(weights) * (t1 - t0) + t0
    marked = {w.lower() for h in hl for w in re.findall(r"[A-Za-z0-9']+", h)}
    out, cur = [], []
    for i, w in enumerate(tokens):
        cur.append(i)
        if len(cur) == 3 or len(" ".join(tokens[j] for j in cur)) > 14 or w[-1] in ".!?,;:" or i == len(tokens) - 1:
            out.append(cur)
            cur = []
    chunks = []
    for k, idx in enumerate(out):
        at = edges[idx[0]]
        until = edges[out[k + 1][0]] if k + 1 < len(out) else edges[idx[-1] + 1] + 0.3
        ws = [tokens[j] for j in idx]
        chunks.append({"words": ws, "hl": [re.sub(r"[^A-Za-z0-9']", "", w).lower() in marked for w in ws],
                       "at": f(at), "until": f(until), "talk": talk})
    return chunks
