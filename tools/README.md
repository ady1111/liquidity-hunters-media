# Liquidity Hunters content tools

Reference scripts used to make daily posts. Adapt the levels, titles and text to each day's chart.

- `make_posts.py <out_dir> <data.json>` – 1080x1350 chart and explainer images (dark theme, Inter font).
- `reel.py render <out_dir>` – 1080x1920 30fps reel built from 4H candles in `data.json` (next to the script); writes one mp4 per scene plus `list.txt` for the ffmpeg concat demuxer. `reel.py preview <out_dir>` writes still frames to check first.
- `beat.py <out.wav>` – original, copyright-free 16s trap beat (140 BPM) with an impact at `SWEEP` seconds. Never use real songs.

`data.json` format: `{"btc": {"o":[],"h":[],"l":[],"c":[]}, "gold": {...}}`, last 60 4H bars each.

Mux: `ffmpeg -f concat -safe 0 -i list.txt -i beat.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 44100 -c:a aac -b:a 192k -shortest -movflags +faststart reel.mp4`

Files go in `posts/YYYY-MM-DD-*.png` and `videos/YYYY-MM-DD-*.mp4`; public URL: `https://raw.githubusercontent.com/ady1111/liquidity-hunters-media/main/<path>`.
