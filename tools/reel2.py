"""Attention-first 9:16 reel (v2). Usage:
  python3 reel2.py preview <cfg.json> <out_dir>   -> still frames at key moments
  python3 reel2.py render  <cfg.json> <out_dir>   -> <out_dir>/video.mp4 (silent; mux with beat.wav)
Style rules: hook fully visible on frame 0 (no fade-in), chart teased behind the hook,
zoom punch + screen shake + flash on each liquidity event, live price counter,
big captions, progress bar, and a comment question at the end. 16s total.
Event times (for beat.py impacts) are printed on render: T1, T2.
"""
import json, sys, subprocess, os
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
COL = {"up": UP, "dn": DN, "gold": GOLD, "muted": MUTED, "fg": FG}
W, H, FPS, DUR = 1080, 1920, 30, 16.0

cfg = json.load(open(sys.argv[2]))
raw = json.load(open(cfg["data"]))[cfg["key"]]
K = cfg["bars"]
o, h, l, c = (np.array(raw[k][-K:], float) for k in "ohlc")
N = K
FMT = cfg.get("fmt", "{:,.0f}")
E1, E2 = cfg["events"]            # each: i, y, stamp, caption, color
YLO, YHI = cfg["ylim"]

# ---- timeline ----
HOOK = 1.5
T1, HOLD = 6.4, 1.0               # event 1 candle completes at T1, then hold
T2 = 10.4
OUTRO = 12.0

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

def n_vis(t):
    if t < HOOK: return 0
    if t < T1: return (E1["i"] + 1) * (t - HOOK) / (T1 - HOOK)
    if t < T1 + HOLD: return E1["i"] + 1
    if t < T2: return E1["i"] + 1 + (E2["i"] - E1["i"]) * (t - T1 - HOLD) / (T2 - T1 - HOLD)
    if t < T2 + 0.8: return E2["i"] + 1
    return min(N, E2["i"] + 1 + (N - E2["i"] - 1) * (t - T2 - 0.8) / (OUTRO - T2 - 0.8 - 0.2))

def zoom(t):
    z = 0
    for Te in (T1, T2):
        if Te - 0.15 <= t < Te + 1.3:
            dt = t - Te
            z = max(z, ease((dt + 0.15) / 0.3) if dt < 0.6 else 1 - ease((dt - 0.6) / 0.7))
    return z

def shake(t):
    s = 0
    for Te in (T1, T2):
        if 0 <= t - Te < 0.45: s = max(s, (1 - (t - Te) / 0.45))
    return s

def flash(t):
    a = 0
    for Te, col in ((T1, COL[E1["color"]]), (T2, COL[E2["color"]])):
        if 0 <= t - Te < 0.25: a, cc = 0.35 * (1 - (t - Te) / 0.25), col
    return (a, cc) if a else (0, None)

fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)
rng = np.random.default_rng(3)

def candles(ax, nv, alpha=1.0):
    full = int(nv); frac = nv - full
    for i in range(min(N, full + 1)):
        a = (1 if i < full else ease(frac)) * alpha
        if a <= 0: continue
        col = UP if c[i] >= o[i] else DN
        k = 1 if i < full else ease(frac)
        cl = o[i] + (c[i] - o[i]) * k
        hi = max(o[i], cl) + (h[i] - max(o[i], c[i])) * k
        lo = min(o[i], cl) - (min(o[i], c[i]) - l[i]) * k
        ax.plot([i, i], [lo, hi], color=col, lw=3, zorder=3, alpha=a)
        ax.add_patch(Rectangle((i - 0.36, min(o[i], cl)), 0.72, max(abs(cl - o[i]), (YHI - YLO) * 0.002),
                               color=col, zorder=4, alpha=a))

def axes(rect):
    ax = fig.add_axes(rect); ax.set_facecolor(PANEL)
    for s_ in ax.spines.values(): s_.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=18, length=0)
    ax.set_xticks([]); ax.yaxis.tick_right()
    ax.grid(axis="y", color="#1E2733", lw=1.2)
    return ax

def stamp(x, y, txt, col, a, rot=-6, size=64):
    fig.text(x, y, txt, color=BG, fontsize=size, fontweight="heavy", ha="center", va="center", rotation=rot,
             alpha=a, bbox=dict(boxstyle="round,pad=0.25", fc=col, ec="none", alpha=a), zorder=20)

def caption(lines, t0, t):
    y = 0.215
    for k, (txt, col, sz) in enumerate(lines):
        a = ease((t - t0 - 0.12 * k) / 0.15)
        if a <= 0: continue
        fig.text(0.5, y, txt, color=col, fontsize=sz * (1 + 0.12 * (1 - a)), fontweight="heavy", ha="center", va="center", alpha=a)
        y -= 0.06

def chrome(t):
    fig.text(0.07, 0.035, "LIQUIDITY HUNTERS", color=FG, fontsize=26, fontweight="heavy")
    fig.text(0.93, 0.035, "Not financial advice", color=MUTED, fontsize=19, ha="right")
    fig.patches.append(Rectangle((0, 0.994), t / DUR, 0.006, transform=fig.transFigure, fc=GOLD, ec="none"))

def frame(fi):
    t = fi / FPS
    fig.clf(); fig.set_facecolor(BG)
    chrome(t)
    if t < HOOK:   # hook: visible from frame 0, chart outcome teased behind
        ax = axes([0.06, 0.30, 0.86, 0.50]); ax.set_xlim(-1, N + 9); ax.set_ylim(YLO, YHI)
        candles(ax, N, alpha=0.22); ax.tick_params(labelright=False)
        p = 1 + 0.08 * (1 - ease(t / 0.25))
        for txt, y, col, sz in cfg["hook"]:
            fig.text(0.5, y, txt, color=COL.get(col, FG), fontsize=sz * p, fontweight="heavy", ha="center", va="center")
        if t > 0.6: stamp(0.5, 0.37, cfg["hook_stamp"], DN, ease((t - 0.6) / 0.15), size=46 * (1 + 0.3 * (1 - ease((t - 0.6) / 0.2))))
        return
    if t >= OUTRO:
        tt = t - OUTRO
        ax = axes([0.06, 0.30, 0.86, 0.50]); ax.set_xlim(-1, N + 9); ax.set_ylim(YLO, YHI)
        candles(ax, N, alpha=0.18); ax.tick_params(labelright=False)
        for k, (txt, y, col, sz) in enumerate(cfg["outro"]):
            a = ease((tt - 0.35 * k) / 0.2)
            if a > 0: fig.text(0.5, y, txt, color=COL.get(col, FG), fontsize=sz * (1 + 0.15 * (1 - a)), fontweight="heavy",
                               ha="center", va="center", alpha=a)
        return
    # main chart with camera
    sh = shake(t); dx, dy = (rng.uniform(-1, 1, 2) * 0.012 * sh) if sh else (0, 0)
    ax = axes([0.06 + dx, 0.30 + dy, 0.86, 0.50])
    nv = n_vis(t)
    ev = E1 if t < (T1 + T2) / 2 + 0.6 else E2
    z = zoom(t)
    x0, x1 = -1, N + 9
    zx0, zx1 = ev["i"] - 14, ev["i"] + 7
    span = (YHI - YLO) * 0.42
    ax.set_xlim(x0 + (zx0 - x0) * z, x1 + (zx1 - x1) * z)
    ax.set_ylim(YLO + (ev["y"] - span / 2 - YLO) * z, YHI + (ev["y"] + span / 2 - YHI) * z)
    for zn in cfg.get("zones", []):   # optional FVG / OB boxes: y0, y1, from, show_at, label, color
        a = ease((nv - zn["show_at"]) / 1.5)
        if a <= 0: continue
        ax.add_patch(Rectangle((zn["from"] - 0.4, zn["y0"]), N + 9 - zn["from"], zn["y1"] - zn["y0"],
                               fc=COL[zn["color"]], ec=COL[zn["color"]], lw=2, alpha=0.18 * a, zorder=1))
        ax.text(N + 8, (zn["y0"] + zn["y1"]) / 2, zn["label"] + " ", color=COL[zn["color"]], fontsize=22,
                fontweight="heavy", ha="right", va="center", alpha=a, zorder=6)
    candles(ax, nv)
    for lv in cfg["levels"]:
        a = ease((nv - lv["show_at"]) / 2)
        if a <= 0: continue
        Te = {1: T1, 2: T2}.get(lv.get("event"))
        hit = max(0, 1 - abs(t - Te) / 0.5) if Te else 0
        ax.plot([lv.get("from", -1), N + 9], [lv["y"], lv["y"]], color=COL[lv["color"]], lw=3 + 6 * hit, ls="--", alpha=a, zorder=2)
        y0, y1 = ax.get_ylim(); pad = (y1 - y0) * 0.06
        if not (y0 + pad < lv["y"] < y1 - pad): continue
        ax.text(0.01, lv["y"], " " + lv["label"] + " ", transform=ax.get_yaxis_transform(), color=BG, fontsize=20,
                fontweight="bold", va="bottom" if lv.get("above") else "top", alpha=a,
                bbox=dict(boxstyle="round,pad=0.3", fc=COL[lv["color"]], ec="none", alpha=a), zorder=6)
    # live price counter
    last = min(int(np.ceil(nv)) - 1, N - 1)
    if last >= 0:
        k = nv - int(nv) if nv < N else 1
        px = c[last] if k == 0 or nv >= N else o[last] + (c[last] - o[last]) * ease(k)
        if t >= T2 - 0.2 and t < T2 + 0.8: px = (h if E2.get("px") == "h" else l)[E2["i"]]  # wick extreme at event 2
        colp = DN if px < o[0] else UP
        fig.text(0.93, 0.905, FMT.format(px), color=colp, fontsize=46, fontweight="heavy", ha="right", va="center")
    fig.text(0.07, 0.905, cfg["kicker"], color=GOLD, fontsize=30, fontweight="bold", va="center")
    fig.text(0.07, 0.855, cfg["title"], color=FG, fontsize=50, fontweight="heavy", va="center")
    fa, fc = flash(t)
    if fa: fig.patches.append(Rectangle((0, 0), 1, 1, transform=fig.transFigure, fc=fc, ec="none", alpha=fa, zorder=30))
    for Te, e in ((T1, E1), (T2, E2)):
        if Te <= t < Te + 1.6:
            a = ease((t - Te) / 0.12) * (1 - ease((t - Te - 1.3) / 0.3))
            stamp(0.5, 0.70, e["stamp"], COL[e["color"]], a, size=70 * (1 + 0.35 * (1 - ease((t - Te) / 0.18))))
    if t < T1: caption(cfg["captions"][0], HOOK, t)
    elif t < T2: caption(cfg["captions"][1], T1, t)
    else: caption(cfg["captions"][2], T2, t)

def grab():
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[:, :, :3].tobytes()

if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    if mode == "preview":
        for t in cfg.get("preview_times", [0.0, 0.8, 4.0, T1 + 0.1, T1 + 0.7, 9.0, T2 + 0.1, T2 + 1.2, 11.9, 13.0, 15.5]):
            frame(int(t * FPS)); fig.savefig(f"{out}/p_{t:05.2f}.png", facecolor=BG)
    else:
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                              "-pix_fmt", "yuv420p", f"{out}/video.mp4"], stdin=subprocess.PIPE)
        for i in range(int(DUR * FPS)):
            frame(i); p.stdin.write(grab())
        p.stdin.close(); assert p.wait() == 0
        print(f"ok T1={T1} T2={T2}")
