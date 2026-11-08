"""Keeps ideas/approved.md in step with the weekly idea issues (.github/workflows/ideas.yml). Standard library only.

  python3 ideas/sync.py issue   ideas/proposals/2026-W46.md     prints the body of the GitHub issue for a proposal
  python3 ideas/sync.py approve 2026-W46 < issue-body.md          writes the ticked ideas of that week into approved.md

A proposal line looks like `- [ ] kids-2026w46-1 | Title | one line in English | Türkçe kısa özet`. The channel owner
ticks the ideas they like in the issue; the writer agents use approved ideas first and mark a script that uses one
with "idea": "<id>".
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APPROVED = os.path.join(HERE, "approved.md")
LINE = re.compile(r"^- \[( |x|X)\] ([a-z]+-\d{4}w\d{2}-\d+) \| (.*)$")
HEADER = """# Approved ideas

The channel owner ticks ideas in the weekly "Haftalık fikirler" issue on GitHub; they land here. The writer agents use
the first approved idea of their channel that no script uses yet, and mark that script with "idea": "<id>".
"""


def issue_body(proposal):
    lines = open(proposal).read().splitlines()
    intro = ["Bu haftanın fikirleri. Beğendiklerinin kutusunu işaretle; ajanlar önce onları yazar. "
             "Hiçbirini seçmezsen kendileri karar verir.", ""]
    return "\n".join(intro + lines) + "\n"


def approve(week, body):
    ticked = []
    for line in body.splitlines():
        m = LINE.match(line.strip())
        if m and m.group(1).lower() == "x":
            ticked.append(f"- {m.group(2)} | {m.group(3)}")
    sections = {}
    if os.path.exists(APPROVED):
        current = None
        for line in open(APPROVED).read().splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                sections[current] = []
            elif current and line.startswith("- "):
                sections[current].append(line)
    sections[week] = ticked
    out = [HEADER]
    for name in sorted(sections, reverse=True):
        if sections[name]:
            out += [f"## {name}", "", *sections[name], ""]
    with open(APPROVED, "w") as fh:
        fh.write("\n".join(out))
    print(f"{week}: {len(ticked)} approved")


def main():
    if sys.argv[1] == "issue":
        sys.stdout.write(issue_body(sys.argv[2]))
    elif sys.argv[1] == "approve":
        approve(sys.argv[2], sys.stdin.read())


if __name__ == "__main__":
    main()
