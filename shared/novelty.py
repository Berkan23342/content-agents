"""How new is a piece of writing compared with what the channels already have? Standard library only.

The checkers (outbreak-channel/scripts/diarycheck.py, quiz-channel/scripts/quizcheck.py,
kids-channel/scripts/storycheck.py) use it so the writer agents cannot repeat themselves.
"""
import re


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def shingles(text, n=3):
    w = words(text)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def overlap(a, b, n=3):
    """Share of the shorter text's n-word runs that also appear in the other one (0 = all new, 1 = copied)."""
    sa, sb = shingles(a, n), shingles(b, n)
    return len(sa & sb) / max(1, min(len(sa), len(sb)))


def jaccard(a, b):
    """Word-set similarity of two short texts, such as two quiz questions."""
    sa, sb = set(words(a)), set(words(b))
    return len(sa & sb) / max(1, len(sa | sb))


def closest(text, others, measure=overlap):
    """(score, name) of the most similar of `others`, a list of (name, text)."""
    return max(((measure(text, t), name) for name, t in others), default=(0.0, None))
