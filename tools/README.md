# Liquidity Hunters content tools

Reference scripts used to make daily posts. Adapt the levels, titles and text to each day's chart.

- **TikTok photo posts must be JPEG (or WebP): PNG is rejected. Save images as `.jpg` (`savefig(..., pil_kwargs={"quality": 92})` or convert with PIL) and schedule the `.jpg` URL.**
- `make_posts.py <out_dir> <data.json>` – 1080x1350 chart and explainer images (dark theme, Inter font).
- `reel.py render <out_dir>` – 1080x1920 30fps reel built from 4H candles in `data.json` (next to the script); writes one mp4 per scene plus `list.txt` for the ffmpeg concat demuxer. `reel.py preview <out_dir>` writes still frames to check first.
- **`reel2.py preview|render <cfg.json> <out_dir>` – DEFAULT for reels (attention-first v2).** Hook fully visible on frame 0 (no fade-in) with the outcome teased behind it, zoom punch + screen shake + color flash on each of the two liquidity events (T1=6.4s, T2=10.4s), TRAP #1/#2 stamps, live price counter, big centered captions, progress bar, and an outro with the real move size plus a comment question ("Bounce or lower? Comment"). Config example: `tools/examples/2026-11-01-gold-cfg.json` (events = bar index in the window + zoom center price; levels = real equal highs/lows). Every number on screen must come from the candles.
- `beat2.py <out.wav> --seed N --bpm 124-140 --key dm|am|em --hook 1.5 --hits 6.4,10.4` – original beat for reel2: hit on frame 0, drop at the hook end, impacts on both events. Vary seed/bpm/key daily.
- `reel.py` (v1, older calmer style) – kept for reference.
- `beat.py <out.wav>` – original, copyright-free 16s trap beat (140 BPM) with an impact at `SWEEP` seconds. Never use real songs.

`data.json` format: `{"btc": {"o":[],"h":[],"l":[],"c":[]}, "gold": {...}}`, last 60 4H bars each.

Mux v2: `ffmpeg -i out/video.mp4 -i beat.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 44100 -c:a aac -b:a 192k -shortest -movflags +faststart reel.mp4`

Mux v1: `ffmpeg -f concat -safe 0 -i list.txt -i beat.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 44100 -c:a aac -b:a 192k -shortest -movflags +faststart reel.mp4`

Files go in `posts/YYYY-MM-DD-*.jpg` and `videos/YYYY-MM-DD-*.mp4`; public URL: `https://raw.githubusercontent.com/ady1111/liquidity-hunters-media/main/<path>`.

TikTok captions: lead with a curiosity/trap hook line, end with a two-choice comment question ("Bounce or lower? Comment 👇"). Still no signals or promises.
