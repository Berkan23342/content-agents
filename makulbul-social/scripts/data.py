"""Product data and idea history for the daily Makulbul content agent.

  python3 scripts/data.py products               refresh data/products.json from makulbul.com (in-stock phones and laptops)
  python3 scripts/data.py find "iphone 16"       search products by name
  python3 scripts/data.py compare "<name A>" "<name B>"   suggested spec rows for a compare reel (no prices)
  python3 scripts/data.py pairs telefon 10       random product pairs never compared before
  python3 scripts/data.py history [N]            last N posted ideas
  python3 scripts/data.py used KEY               exit 0 if an idea key was already posted
  python3 scripts/data.py key "<name A>" "<name B>"   history key of a compare pair
  python3 scripts/data.py log content/<day> FORMAT KEY "Title"   record a finished day in content/history.json
"""
import json
import os
import random
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS = os.path.join(ROOT, "data", "products.json")
HISTORY = os.path.join(ROOT, "content", "history.json")
API = "https://makulbul.com/api/products"


def load_products():
    with open(PRODUCTS) as fh:
        return json.load(fh)


def refresh():
    out = []
    for category in ("telefon", "laptop"):
        url = API + ("?category=laptop" if category == "laptop" else "")
        with urllib.request.urlopen(url, timeout=60) as r:
            for p in json.load(r):
                out.append({"id": p["id"], "name": p["canonical_name"], "brand": p["brand"], "category": category, "specs": p["specs"]})
    os.makedirs(os.path.dirname(PRODUCTS), exist_ok=True)
    with open(PRODUCTS, "w") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"{len(out)} products saved")


def find(query):
    q = query.lower().split()
    return [p for p in load_products() if all(w in p["name"].lower() for w in q)]


def one(query):
    hits = find(query)
    exact = [p for p in hits if p["name"].lower() == query.lower()]
    if exact:
        return exact[0]
    if not hits:
        raise SystemExit(f"no product matches {query!r}")
    return hits[0]


IP_RANK = {"IP68": 6, "IP67": 5, "IP66": 4, "IP65": 3, "IP64": 2, "IP54": 1, "IP53": 1, "IP52": 0}


def _num(v):
    if isinstance(v, (int, float)):
        return v
    m = re.search(r"[\d.]+", str(v or ""))
    return float(m.group()) if m else None


def _pixels(res):
    m = re.match(r"(\d+)\s*x\s*(\d+)", str(res or ""))
    return int(m.group(1)) * int(m.group(2)) if m else None


# label, spec key, unit, better ("high" / "low" / "rank" / "bool" / None for no winner)
PHONE_ROWS = [
    ("Pil", "battery_mah", " mAh", "high"),
    ("Hızlı şarj", "wired_charging_watts", " W", "high"),
    ("Ana kamera", "main_camera_mp", " MP", "high"),
    ("Ön kamera", "front_camera_mp", " MP", "high"),
    ("Ekran parlaklığı", "screen_nits", " nit", "high"),
    ("Yenileme hızı", "refresh_rate_hz", " Hz", "high"),
    ("Ağırlık", "weight_g", " g", "low"),
    ("Depolama", "storage_gb", " GB", "high"),
    ("RAM", "ram_gb", " GB", "high"),
    ("Suya dayanıklılık", "ip_rating", "", "rank"),
    ("Ekran", "screen_inch", "\"", None),
    ("Stereo hoparlör", "has_stereo_speakers", "", "bool"),
    ("NFC", "has_nfc", "", "bool"),
    ("5G", "has_5g", "", "bool"),
]
LAPTOP_ROWS = [
    ("RAM", "ram_gb", " GB", "high"),
    ("Depolama", "storage_gb", " GB", "high"),
    ("Pil", "battery_wh", " Wh", "high"),
    ("Ağırlık", "weight_g", " g", "low"),
    ("Ekran yenileme", "refresh_rate_hz", " Hz", "high"),
    ("Çözünürlük", "screen_resolution", "", "pixels"),
    ("İşlemci çekirdeği", "cpu_cores", "", "high"),
    ("Kamera", "webcam_mp", " MP", "high"),
    ("Aydınlatmalı klavye", "has_backlit_keyboard", "", "bool"),
    ("Parmak izi", "has_fingerprint", "", "bool"),
    ("Ekran", "screen_inch", "\"", None),
]


def compare(qa, qb, limit=5):
    a, b = one(qa), one(qb)
    rows = []
    for label, key, unit, better in (PHONE_ROWS if a["category"] == "telefon" else LAPTOP_ROWS):
        va, vb = a["specs"].get(key), b["specs"].get(key)
        if va is None or vb is None:
            continue
        if better == "bool":
            sa, sb = ("Var" if va else "Yok"), ("Var" if vb else "Yok")
            win = "tie" if va == vb else ("a" if va else "b")
        else:
            sa, sb = f"{va}{unit}", f"{vb}{unit}"
            if better == "high":
                win = "tie" if _num(va) == _num(vb) else ("a" if _num(va) > _num(vb) else "b")
            elif better == "low":
                win = "tie" if _num(va) == _num(vb) else ("a" if _num(va) < _num(vb) else "b")
            elif better == "rank":
                ra, rb = IP_RANK.get(va, 0), IP_RANK.get(vb, 0)
                win = "tie" if ra == rb else ("a" if ra > rb else "b")
            elif better == "pixels":
                pa, pb = _pixels(va), _pixels(vb)
                win = "tie" if pa == pb else ("a" if (pa or 0) > (pb or 0) else "b")
            else:
                win = "tie"
        rows.append({"label": label, "a": sa, "b": sb, "win": win})
    # differences make better content; keep ties only to fill up
    rows.sort(key=lambda r: r["win"] == "tie")
    print(json.dumps({"category": a["category"], "a": {"name": a["name"], "chip": a["specs"].get("chip") or a["specs"].get("cpu")},
                      "b": {"name": b["name"], "chip": b["specs"].get("chip") or b["specs"].get("cpu")},
                      "rows": rows[:limit], "all_rows": rows}, ensure_ascii=False, indent=1))


def history():
    if not os.path.exists(HISTORY):
        return []
    with open(HISTORY) as fh:
        return json.load(fh)


def pair_key(a, b):
    return "compare:" + "|".join(sorted([a.lower(), b.lower()]))


def pairs(category, n):
    used = {h["key"] for h in history()}
    items = [p for p in load_products() if p["category"] == category]
    out = []
    for _ in range(2000):
        a, b = random.sample(items, 2)
        if a["brand"] == b["brand"] and random.random() < 0.6:
            continue  # prefer cross-brand match-ups
        k = pair_key(a["name"], b["name"])
        if k not in used and k not in {pair_key(x, y) for x, y in out}:
            out.append((a["name"], b["name"]))
        if len(out) >= n:
            break
    for a, b in out:
        print(f"{a}  vs  {b}")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "products":
        refresh()
    elif cmd == "find":
        for p in find(" ".join(sys.argv[2:])):
            print(f"{p['category']:8} {p['name']}")
    elif cmd == "compare":
        compare(sys.argv[2], sys.argv[3])
    elif cmd == "pairs":
        pairs(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10)
    elif cmd == "history":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        for h in history()[-n:]:
            print(f"{h['date']}  {h['format']:8} {h['key']:50} {h['title']}")
    elif cmd == "key":
        print(pair_key(one(sys.argv[2])["name"], one(sys.argv[3])["name"]))
    elif cmd == "log":
        day_dir, fmt_, key, title = sys.argv[2:6]
        pub_path = os.path.join(day_dir, "published.json")
        published = json.load(open(pub_path)) if os.path.exists(pub_path) else {}
        caption = open(os.path.join(day_dir, "caption.txt")).read().strip().splitlines()[0]
        items = [h for h in history() if h["date"] != os.path.basename(day_dir.rstrip("/"))]
        items.append({"date": os.path.basename(day_dir.rstrip("/")), "format": fmt_, "key": key, "title": title, "hook": caption,
                      "published": {k: v.get("status") for k, v in published.items()}})
        with open(HISTORY, "w") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=1)
        print(f"logged {key}")
    elif cmd == "used":
        raise SystemExit(0 if any(h["key"] == sys.argv[2] for h in history()) else 1)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
