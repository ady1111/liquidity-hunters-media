"""Signal reel: 1080x1920, 30fps, ~15s.
usage: python3 signal_reel.py preview|render <cfg.json> <out_dir>
cfg: {"label":"BTCUSDT","tf":"1H","side":"LONG"|"SHORT","dec":0,
      "o":[],"h":[],"l":[],"c":[]   (last ~60 bars, oldest first),
      "entry":77650,"sl":77100,"tp1":78800,"tp2":79800,
      "event_bar":30,"event_price":76326,"event_text":"Sell-side swept\\n76.3K",
      "zones":[{"kind":"OB","label":"1H Bullish OB","x0":50,"lo":77538,"hi":77682},
               {"kind":"FVG","label":"1H Bullish FVG","x0":51,"lo":77596,"hi":77663}],
      "zone_text":"1H Bullish OB + FVG",
      "reacts":[{"lo":78241,"hi":78418,"text":"1H Bear FVG"},{"price":78804,"text":"Buy-side liquidity"}],  # where price may react
      "skip":0,  # drop this many oldest bars (indices in cfg are BEFORE skipping)
      "why":["Swept the 76.3K lows","1H order block + FVG","Long from the FVG"],
      "invalid":"1H close below 77,100"}
Every number must come from the real candles. Writes <out_dir>/video.mp4 (silent).
Impact moments for beat2 --hits: 7.0 (levels drop), 8.9 (reaction points), 11.5 (summary card).
"""
import json, sys, os, subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import font_manager as fm

for f in fm.findSystemFonts():
    if "Inter" in f:
        try: fm.fontManager.addfont(f)
        except Exception: pass
plt.rcParams["font.family"] = "Inter"

BG = "#0B0F14"; PANEL = "#121821"; FG = "#E8EDF2"; MUTED = "#8A97A6"
UP = "#26C281"; DN = "#EF4E5B"; GOLD = "#F5B83D"
ZCOL = {"OB": "#3AA0FF", "FVG": "#B07CFF"}
W, H, FPS, DUR = 1080, 1920, 30, 15.0
T_CHART, T_LEVELS, T_REACT, T_CARD = 2.0, 7.0, 8.9, 11.5

mode, cfgp, out = sys.argv[1], sys.argv[2], sys.argv[3]
C = json.load(open(cfgp))
SK = C.get("skip", 0)
o, h, l, c = (C[k][SK:] for k in "ohlc")
if C.get("event_bar") is not None: C["event_bar"] -= SK
for z in C.get("zones", []): z["x0"] -= SK
RE = C.get("reacts", [])
N = len(c); LONG = C["side"].upper() == "LONG"
SIDE_COL = UP if LONG else DN
dec = C.get("dec", 0)
fmt = lambda v: f"{v:,.{dec}f}"
E, SL, TP1, TP2 = C["entry"], C["sl"], C["tp1"], C.get("tp2")
risk = abs(E - SL)
rr1 = abs(TP1 - E) / risk
rr2 = abs(TP2 - E) / risk if TP2 else None
lo_all = min(min(l), SL, TP1, TP2 or TP1); hi_all = max(max(h), SL, TP1, TP2 or TP1)
pad = (hi_all - lo_all) * 0.08
YL = (lo_all - pad, hi_all + pad)

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)

def chrome(t):
    fig.text(0.07, 0.03, "LIQUIDITY HUNTERS", color=FG, fontsize=26, fontweight="heavy")
    fig.text(0.93, 0.03, "Not financial advice", color=MUTED, fontsize=19, ha="right")
    ax = fig.add_axes([0, 0.992, 1, 0.008]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((0, 0), t / DUR, 1, color=GOLD))

def hook(t):
    fig.text(0.5, 0.66, C["label"], color=MUTED, fontsize=46, fontweight="bold", ha="center")
    fig.text(0.5, 0.57, f"{C['side'].upper()} SIGNAL", color=SIDE_COL, fontsize=96, fontweight="heavy", ha="center")
    fig.text(0.5, 0.50, f"R:R up to 1:{(rr2 or rr1):.1f}", color=FG, fontsize=56, fontweight="heavy", ha="center")
    fig.text(0.5, 0.42, "Entry, stop & targets inside", color=GOLD, fontsize=38, fontweight="bold", ha="center")

def chart(n_vis, lv, shake=0, za=0, ra=0):
    dx = shake * np.sin(n_vis * 7) * 0.004
    ax = fig.add_axes([0.05 + dx, 0.30, 0.80, 0.52])
    ax.set_facecolor(PANEL)
    for s_ in ax.spines.values(): s_.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=17, length=0); ax.set_xticks([]); ax.yaxis.tick_right()
    ax.grid(axis="y", color="#1E2733", lw=1.2)
    ax.set_xlim(-1, N + 14); ax.set_ylim(*YL)
    full = int(n_vis); frac = n_vis - full
    for i in range(min(N, full + 1)):
        a = 1 if i < full else ease(frac)
        if a <= 0: continue
        col = UP if c[i] >= o[i] else DN
        cl = o[i] + (c[i] - o[i]) * a
        hi = max(o[i], cl) + (h[i] - max(o[i], c[i])) * a
        lo_ = min(o[i], cl) - (min(o[i], c[i]) - l[i]) * a
        ax.plot([i, i], [lo_, hi], color=col, lw=2, zorder=3, alpha=a)
        ax.add_patch(Rectangle((i - 0.36, min(o[i], cl)), 0.72, max(abs(cl - o[i]), (YL[1]-YL[0])*0.001), color=col, zorder=4, alpha=a))
    ev = C.get("event_bar")
    if ev is not None and n_vis > ev + 1:
        a = ease((n_vis - ev - 1) / 3)
        ax.annotate(C["event_text"], xy=(ev, C["event_price"]), xytext=(max(ev - 16, 0), C["event_price"] - (YL[1]-YL[0]) * 0.07),
                    color=GOLD, fontsize=21, fontweight="bold", alpha=a,
                    arrowprops=dict(arrowstyle="->", color=GOLD, lw=2.5, alpha=a), zorder=7)
    if za > 0:
        for k, z in enumerate(C.get("zones", [])):
            col = ZCOL.get(z["kind"], GOLD); a = ease((za - 0.3 * k) / 0.5)
            if a <= 0: continue
            ax.add_patch(Rectangle((z["x0"] - 0.4, z["lo"]), N + 13 - z["x0"], z["hi"] - z["lo"], color=col, alpha=0.30 * a, zorder=2, lw=0))
            ax.plot([z["x0"] - 0.4, N + 12.6], [z["hi"]] * 2, color=col, lw=1.5, alpha=a, zorder=2)
            ax.plot([z["x0"] - 0.4, N + 12.6], [z["lo"]] * 2, color=col, lw=1.5, alpha=a, zorder=2)
            above = (k % 2 == 1)
            ax.text(z["x0"] - 1.5, z["hi"] if above else z["lo"], z["label"], color=col, fontsize=19, fontweight="heavy",
                    ha="right", va="bottom" if above else "top", alpha=a, zorder=9,
                    bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec=col, lw=1.5, alpha=0.9 * a))
    if ra > 0: reacts(ax, ra)
    if lv > 0:
        x0 = N - 1; x1 = x0 + 15 * ease(lv)
        ax.add_patch(Rectangle((x0, min(E, SL)), x1 - x0, risk, color=DN, alpha=0.22 * ease(lv), zorder=1))
        top = TP2 or TP1
        ax.add_patch(Rectangle((x0, min(E, top)), x1 - x0, abs(top - E), color=UP, alpha=0.18 * ease(lv), zorder=1))
        rows = [(E, GOLD, f"ENTRY {fmt(E)}", 0.0), (SL, DN, f"SL {fmt(SL)}", 0.25),
                (TP1, UP, f"TP1 {fmt(TP1)}", 0.5)] + ([(TP2, UP, f"TP2 {fmt(TP2)}", 0.75)] if TP2 else [])
        for y, col, txt, d in rows:
            a = ease((lv - d) / 0.25)
            if a <= 0: continue
            ax.plot([x0 - 6, x1], [y, y], color=col, lw=3, alpha=a, zorder=5)
            ax.text(x1, y, txt, color=BG, fontsize=18, fontweight="bold", ha="right", va="center", alpha=a,
                    bbox=dict(boxstyle="round,pad=0.35", fc=col, ec="none", alpha=a), zorder=8)

def reacts(ax, ra):
    for k, r in enumerate(RE):
        a = ease((ra - 0.35 * k) / 0.4)
        if a <= 0: continue
        pulse = 1 + 0.6 * max(0, 1 - (ra - 0.35 * k) / 0.6)
        if "lo" in r:
            ax.add_patch(Rectangle((-1, r["lo"]), N + 15, r["hi"] - r["lo"], color=GOLD, alpha=0.20 * a, zorder=1, lw=0))
            y = (r["lo"] + r["hi"]) / 2; txt = f"REACTS? {fmt(r['lo'])}-{fmt(r['hi'])}  {r['text']}"
        else:
            y = r["price"]; txt = f"REACTS? {fmt(y)}  {r['text']}"
        ax.plot([-1, N + 14], [y, y], color=GOLD, lw=2 * pulse, ls=":", alpha=a, zorder=6)
        ax.text(0, y, txt, color=BG, fontsize=17 * min(pulse, 1.15), fontweight="heavy", ha="left", va="center", alpha=a, zorder=10,
                bbox=dict(boxstyle="round,pad=0.3", fc=GOLD, ec="none", alpha=a))

def card(t):
    a = ease(t / 0.35)
    fig.text(0.07, 0.86, f"{C['label']} · {C['tf']}", color=GOLD, fontsize=32, fontweight="bold", alpha=a)
    fig.text(0.07, 0.80, f"{C['side'].upper()} SETUP", color=SIDE_COL, fontsize=84, fontweight="heavy", alpha=a, va="center")
    rows = [("Entry", fmt(E), GOLD), ("Stop loss", fmt(SL), DN), ("Target 1", f"{fmt(TP1)}   (1:{rr1:.1f})", UP)]
    if TP2: rows.append(("Target 2", f"{fmt(TP2)}   (1:{rr2:.1f})", UP))
    y = 0.70
    for i, (k, v, col) in enumerate(rows):
        b = ease((t - 0.15 * i) / 0.3)
        fig.text(0.07, y, k, color=MUTED, fontsize=34, alpha=b)
        fig.text(0.93, y, v, color=col, fontsize=44, fontweight="heavy", ha="right", alpha=b)
        y -= 0.058
    b = ease((t - 0.6) / 0.3)
    if C.get("zone_text"):
        fig.text(0.07, y, "Zone", color=MUTED, fontsize=34, alpha=b)
        fig.text(0.93, y, C["zone_text"], color=ZCOL["FVG"], fontsize=36, fontweight="heavy", ha="right", alpha=b)
        y -= 0.058
    y -= 0.02
    b = ease((t - 0.8) / 0.3)
    fig.text(0.07, y, "Why:", color=FG, fontsize=32, fontweight="bold", alpha=b); y -= 0.045
    for w_ in C["why"]:
        fig.text(0.07, y, "• " + w_, color=FG, fontsize=30, alpha=b); y -= 0.042
    y -= 0.015
    if RE:
        pts = " & ".join(fmt(r.get("lo", r.get("price"))) for r in RE)
        fig.text(0.07, y, "Reactions to watch: " + pts, color=GOLD, fontsize=28, fontweight="bold", alpha=b); y -= 0.042
    fig.text(0.07, y, "Invalid if " + C["invalid"], color=DN, fontsize=28, fontweight="bold", alpha=b)
    fig.text(0.5, 0.095, "Follow for daily signals", color=GOLD, fontsize=40, fontweight="heavy", ha="center", alpha=ease((t - 1.6) / 0.3))

def frame(i):
    t = i / FPS
    fig.clf(); fig.set_facecolor(BG)
    if t < T_CHART:
        hook(t)
    elif t < T_CARD:
        n_vis = min(N, (t - T_CHART) / (T_LEVELS - T_CHART - 0.3) * N)
        lv = (t - T_LEVELS) / 1.6 if t >= T_LEVELS else 0
        shake = max(0, 1 - (t - T_LEVELS) / 0.4) if t >= T_LEVELS else 0
        a = 1
        fig.text(0.07, 0.905, f"{C['label']} · {C['tf']}", color=GOLD, fontsize=30, fontweight="bold")
        fig.text(0.07, 0.86, f"{C['side'].upper()} SIGNAL", color=SIDE_COL, fontsize=62, fontweight="heavy", va="center")
        za = (t - (T_LEVELS - 1.8)) / 1.0 if t >= T_LEVELS - 1.8 else 0
        ra = (t - T_REACT) if (RE and t >= T_REACT) else 0
        chart(n_vis, lv, shake, za, ra)
        cap = C["why"][0] if t < T_LEVELS - 1.8 else (C["why"][1] if t < T_LEVELS else C["why"][2])
        if RE and t >= T_REACT: cap = "Watch these reaction points"
        fig.text(0.5, 0.22, cap, color=FG, fontsize=42, fontweight="heavy", ha="center")
        if 0 < t - T_LEVELS < 0.25:
            fig.patches.append(Rectangle((0, 0), 1, 1, transform=fig.transFigure, color=SIDE_COL, alpha=0.18 * (1 - (t - T_LEVELS) / 0.25)))
    else:
        card(t - T_CARD)
    chrome(t)

if mode == "preview":
    for t in (0.0, 4.5, 6.6, 8.4, 10.8, 14.5):
        frame(int(t * FPS)); fig.savefig(f"{out}/prev_{t:04.1f}.png", facecolor=BG)
else:
    tmp = f"{out}/video.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        frame(i); fig.canvas.draw()
        p.stdin.write(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].tobytes())
    p.stdin.close(); assert p.wait() == 0
    os.replace(tmp, f"{out}/video.mp4"); print("ok")
