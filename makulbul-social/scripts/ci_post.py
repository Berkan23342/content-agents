"""Renders and publishes every content/<day>/ that has a spec.json but was not published yet (GitHub Actions).

  python3 scripts/ci_post.py

The daily agent only writes spec.json and caption.txt; this does the rest and records the day in content/history.json.
"""
import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*cmd):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode == 0


def main():
    failed = False
    for spec_path in sorted(glob.glob(os.path.join(ROOT, "content", "*", "spec.json"))):
        day = os.path.dirname(spec_path)
        rel = os.path.relpath(day, ROOT)
        pub = os.path.join(day, "published.json")
        if os.path.exists(pub):
            continue
        if not run(sys.executable, "scripts/speccheck.py", rel):
            failed = True
            continue
        if not run(sys.executable, "scripts/render.py", rel):
            failed = True
            continue
        run(sys.executable, "scripts/publish.py", rel)
        spec = json.load(open(spec_path))
        if not os.path.exists(pub):  # no platform configured yet: remember the idea anyway
            json.dump({"instagram": {"status": "skipped"}, "tiktok": {"status": "skipped"}}, open(pub, "w"))
        run(sys.executable, "scripts/data.py", "log", rel, spec["format"], spec["key"], spec["title"])
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
