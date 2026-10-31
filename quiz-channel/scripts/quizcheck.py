"""Checks a Brain Snack Quiz question pack (quizzes/new/*.json) without rendering anything. Standard library only.

  python3 scripts/quizcheck.py quizzes/new/2026-11-01-space.json

Prints "ok" or the first problem found. scripts/quiz.py uses the same checks.
"""
import json
import sys

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


def main():
    for path in sys.argv[1:]:
        try:
            check_pack(json.load(open(path)))
        except (PackError, json.JSONDecodeError) as e:
            raise SystemExit(f"pack error in {path}: {e}")
        print(f"ok: {path}")


if __name__ == "__main__":
    main()
