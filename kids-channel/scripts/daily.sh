#!/bin/bash
# Makes and uploads the Bubbly Kids TV videos for a date (default: today):
#   learn  the learning episode (scripts/episode.py), due from 10:00
#   fun    the story / surprise-egg / dance / shadow video (scripts/fun.py), due from 18:00
# Run by launchd at 10:00 and 18:00 (see scripts/com.bubblykidstv.daily.plist). Each run makes whatever is
# due and not uploaded yet, so a Mac that slept through 10:00 catches up when it wakes.
#   DATE=2026-11-02 KIND=fun PRIVACY=private UPLOAD=0 scripts/daily.sh
#   KIND=fun PUBLISH_AT=2026-11-02T15:00:00Z scripts/daily.sh   (upload now, YouTube publishes it at that time)
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

DATE="${DATE:-$(date +%F)}"
KIND="${KIND:-auto}"
PRIVACY="${PRIVACY:-public}"
UPLOAD="${UPLOAD:-1}"
PUBLISH_AT="${PUBLISH_AT:-}"
FUN_HOUR=18
mkdir -p logs out/episodes
LOG="logs/$DATE.log"
exec >>"$LOG" 2>&1
echo "=== $(date) videos for $DATE ($KIND)"

notify() { osascript -e "display notification \"$1\" with title \"Bubbly Kids TV\"" || true; }
trap 'notify "Günlük video başarısız ($DATE). Kayıt: kids-channel/$LOG"' ERR

# one run at a time (a lock older than 3 hours is left over from a crash)
LOCK=logs/.lock
if [ -z "${LOCKED:-}" ]; then
	find "$LOCK" -maxdepth 0 -mmin +180 -exec rmdir {} \; 2>/dev/null || true
	if ! mkdir "$LOCK" 2>/dev/null; then
		echo "another run is in progress"
		exit 0
	fi
	trap 'rmdir "$LOCK"' EXIT
fi

caffeinate -i -w $$ &

# Chrome sometimes fails to start right after the Mac wakes up; try a few times before giving up
retry() {
	local n=1
	until "$@"; do
		if [ $n -ge 3 ]; then
			return 1
		fi
		echo "attempt $n failed, retrying in 60s: $1 $2 $3"
		n=$((n + 1))
		sleep 60
	done
}

make_video() {
	local kind=$1 id=$DATE script=episode.py
	if [ "$kind" = fun ]; then
		id="$DATE-fun"
		script=fun.py
	fi
	if grep -q "^$id.mp4 " logs/uploaded.txt 2>/dev/null; then
		echo "$id already uploaded"
		return 0
	fi
	echo "--- $id"
	.venv/bin/python "scripts/$script" --date "$DATE"
	# --timeout: the Fredoka font is fetched from Google Fonts, which can be slow
	retry npx remotion render src/index.tsx Episode "out/episodes/$id.mp4" --props="build/$id/props.json" --timeout=120000 --log=error
	retry npx remotion still src/index.tsx Thumbnail "out/episodes/$id.jpg" --props="build/$id/props.json" \
		--image-format=jpeg --scale=0.6667 --timeout=120000 --log=error

	if [ "$UPLOAD" = "1" ]; then
		.venv/bin/python scripts/upload_youtube.py --video "out/episodes/$id.mp4" --meta "build/$id/meta.json" \
			--thumbnail "out/episodes/$id.jpg" --privacy "$PRIVACY" ${PUBLISH_AT:+--publish-at "$PUBLISH_AT"} --log logs/uploaded.txt
		notify "Yeni video yüklendi: $(tail -1 logs/uploaded.txt | cut -d' ' -f2)"
	fi
}

if [ "$KIND" = auto ]; then
	trap - ERR  # the child runs report their own failures
	DATE="$DATE" KIND=learn LOCKED=1 bash "$0" || echo "learn video failed"
	if [ "$DATE" != "$(date +%F)" ] || [ "$((10#$(date +%H)))" -ge "$FUN_HOUR" ]; then
		DATE="$DATE" KIND=fun LOCKED=1 bash "$0" || echo "fun video failed"
	fi
else
	make_video "$KIND"
fi

# keep the disk small: a week of videos, two weeks of build files
find out/episodes -name '*.mp4' -mtime +7 -delete
find build -mindepth 1 -maxdepth 1 -type d -name '20*' -mtime +14 -exec rm -rf {} +
echo "=== done $(date)"
