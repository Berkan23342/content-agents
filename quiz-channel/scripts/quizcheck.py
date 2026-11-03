"""Checks a Brain Snack Quiz question pack (quizzes/new/*.json) without rendering anything. Standard library only.

  python3 scripts/quizcheck.py quizzes/new/2026-11-01-space.json

Prints "ok" or the first problem found. scripts/quiz.py uses the same checks.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "shared"))
from novelty import words  # noqa: E402

PACK_TYPES = {"trivia", "truefalse"}
QUESTIONS = 5
MAX_TITLE = 22  # the hook shows it in big letters
MAX_QUESTION = 110
MAX_OPTION = 24
MAX_NOTE = 60


class PackError(ValueError):
    pass


def check_pack(spec):
    """Raises PackError with a readable message when a pack would not fit the video."""
    for key in ("type", "title", "questions"):
        if key not in spec:
            raise PackError(f"missing '{key}'")
    if spec["type"] not in PACK_TYPES:
        raise PackError(f"type must be one of {sorted(PACK_TYPES)}")
    if len(spec["title"]) > MAX_TITLE:
        raise PackError(f"title is {len(spec['title'])} characters, keep it to {MAX_TITLE}")
    qs = spec["questions"]
    if len(qs) != QUESTIONS:
        raise PackError(f"a pack has exactly {QUESTIONS} questions, this one has {len(qs)}")
    for i, q in enumerate(qs, 1):
        where = f"question {i}"
        if not q.get("q") or len(q["q"]) > MAX_QUESTION:
            raise PackError(f"{where}: 'q' must be 1-{MAX_QUESTION} characters")
        if spec["type"] == "trivia":
            opts = q.get("options", [])
            if len(opts) != 4 or len(set(o.lower() for o in opts)) != 4:
                raise PackError(f"{where}: needs 4 different options")
            if any(not o or len(o) > MAX_OPTION for o in opts):
                raise PackError(f"{where}: options must be 1-{MAX_OPTION} characters")
            if not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < 4:
                raise PackError(f"{where}: 'answer' is the index 0-3 of the right option")
        else:
            if not isinstance(q.get("answer"), bool):
                raise PackError(f"{where}: 'answer' must be true or false")
            if not q.get("note") or len(q["note"]) > MAX_NOTE:
                raise PackError(f"{where}: 'note' (the short explanation) must be 1-{MAX_NOTE} characters")
    answers = [q["answer"] for q in qs]
    if len(set(answers)) == 1:
        raise PackError("all five answers are the same; mix them up")


STOP = {"a", "an", "the", "is", "are", "was", "of", "in", "on", "to", "and", "or", "what", "which", "who", "how", "many",
        "does", "do", "it", "its", "that", "this", "has", "have", "for", "by", "with", "can", "be", "as", "at", "most"}


def _content(text):
    return {w for w in words(text) if w not in STOP}


def _same_question(a, b):
    """Two questions ask the same thing: same answer and mostly the same important words."""
    true_false = isinstance(a["answer"], bool)
    if (a["answer"] if true_false else a["_answer"]) != (b["answer"] if true_false else b["_answer"]):
        return False
    ca, cb = _content(a["q"]), _content(b["q"])
    score = len(ca & cb) / max(1, len(ca | cb))
    return score >= (0.75 if true_false else 0.5)


def _with_answers(spec):
    out = []
    for q in spec["questions"]:
        q = dict(q)
        if not isinstance(q["answer"], bool):
            q["_answer"] = q["options"][q["answer"]].strip().lower()
        out.append(q)
    return out


def check_against(path, spec):
    """No pack title twice, and no question that an earlier pack already asked. Raises PackError."""
    path = os.path.abspath(path)
    mine = _with_answers(spec)
    for p in glob.glob(os.path.join(ROOT, "quizzes", "new", "*.json")) + glob.glob(os.path.join(ROOT, "quizzes", "used", "*", "*.json")):
        if os.path.abspath(p) == path:
            continue
        try:
            other = json.load(open(p))
        except json.JSONDecodeError:
            continue
        if other.get("type") == spec["type"] and other.get("title", "").strip().lower() == spec["title"].strip().lower():
            raise PackError(f"the title {spec['title']!r} was already used ({os.path.basename(p)})")
        if other.get("type") != spec["type"]:
            continue
        for i, q in enumerate(mine, 1):
            for o in _with_answers(other):
                if _same_question(q, o):
                    raise PackError(f"question {i} repeats {os.path.basename(p)}: {o['q']!r}")


def main():
    for path in sys.argv[1:]:
        try:
            spec = json.load(open(path))
            check_pack(spec)
            check_against(path, spec)
        except (PackError, json.JSONDecodeError) as e:
            raise SystemExit(f"pack error in {path}: {e}")
        print(f"ok: {path}")


if __name__ == "__main__":
    main()
