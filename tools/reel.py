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
W, H, FPS = 1080, 1920, 30
S = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(f"{S}/data.json"))["btc"]
o, h, l, c = (d[k] for k in "ohlc")
N = len(c)
LO_I = int(np.argmin(l)); LO = l[LO_I]
SSL, BSL = 79370, 82000

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3

fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)

def base():
    fig.clf(); fig.set_facecolor(BG)
    fig.text(0.07, 0.035, "LIQUIDITY HUNTERS", color=FG, fontsize=26, fontweight="heavy")
    fig.text(0.93, 0.035, "Not financial advice", color=MUTED, fontsize=19, ha="right")

def header(kicker, title, a=1, dy=0):
    fig.text(0.07, 0.915 - dy, kicker, color=GOLD, fontsize=28, fontweight="bold", alpha=a)
    fig.text(0.07, 0.865 - dy, title, color=FG, fontsize=58, fontweight="heavy", alpha=a, va="center")

def chart(n_vis, ssl_a=0, flash=0, arrow_a=0, bsl_a=0, bsl_draw=1.0):
    ax = fig.add_axes([0.06, 0.30, 0.86, 0.50])
    ax.set_facecolor(PANEL)
    for s_ in ax.spines.values(): s_.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=18, length=0)
    ax.set_xticks([]); ax.yaxis.tick_right()
    ax.grid(axis="y", color="#1E2733", lw=1.2)
    ax.set_xlim(-1, N + 8); ax.set_ylim(75800, 85300)
    full = int(n_vis); frac = n_vis - full
    for i in range(min(N, full + 1)):
        a = 1 if i < full else ease(frac)
        if a <= 0: continue
        col = UP if c[i] >= o[i] else DN
        cl = o[i] + (c[i] - o[i]) * a
        hi = max(o[i], cl) + (h[i] - max(o[i], c[i])) * a
        lo_ = min(o[i], cl) - (min(o[i], c[i]) - l[i]) * a
        ax.plot([i, i], [lo_, hi], color=col, lw=2.2, zorder=3, alpha=a)
        ax.add_patch(Rectangle((i - 0.36, min(o[i], cl)), 0.72, max(abs(cl - o[i]), 8), color=col, zorder=4, alpha=a))
    if ssl_a > 0:
        lw = 3 + 5 * flash
        ax.plot([-1, N + 8], [SSL, SSL], color=DN, lw=lw, ls="--", alpha=ssl_a, zorder=2)
        if ssl_a > 0.5: ax.text(N + 7.5, SSL, "Sell-side liquidity 79.4K", color=BG, fontsize=19, fontweight="bold", ha="right", va="center",
                alpha=ssl_a, bbox=dict(boxstyle="round,pad=0.4", fc=DN, ec="none", alpha=ssl_a), zorder=6)
    if bsl_a > 0:
        x1 = -1 + (N + 9) * ease(bsl_draw)
        ax.plot([-1, x1], [BSL, BSL], color=UP, lw=3.5, ls="--", alpha=bsl_a, zorder=2)
        ax.text(N + 7.5, BSL, "Buy-side liquidity 82K", color=BG, fontsize=19, fontweight="bold", ha="right", va="center",
                alpha=bsl_a * ease(bsl_draw), bbox=dict(boxstyle="round,pad=0.4", fc=UP, ec="none", alpha=bsl_a * ease(bsl_draw)), zorder=6)
    if arrow_a > 0:
        ax.annotate("Stops taken\n76.3K", xy=(LO_I, LO), xytext=(LO_I - 22, LO + 250), color=FG, fontsize=24,
                    fontweight="bold", alpha=arrow_a, arrowprops=dict(arrowstyle="->", color=FG, lw=3, alpha=arrow_a), zorder=7)
    return ax

def bottom(lines):
    y = 0.225
    for t, col, sz, a in lines:
        if a > 0: fig.text(0.07, y, t, color=col, fontsize=sz, fontweight="bold", alpha=a)
        y -= 0.05

# --- scenes: each a function frame -> draw ---
def s1(f):  # hook 0-2.5s
    t = f / FPS
    base()
    a1, a2 = ease(t / 0.4), ease((t - 0.5) / 0.4)
    fig.text(0.5, 0.60, "BTC just", color=FG, fontsize=96, fontweight="heavy", ha="center", alpha=a1)
    fig.text(0.5, 0.53, "HUNTED", color=GOLD, fontsize=130, fontweight="heavy", ha="center", alpha=a2)
    fig.text(0.5, 0.455, "the lows", color=FG, fontsize=96, fontweight="heavy", ha="center", alpha=ease((t - 0.9) / 0.4))
    fig.text(0.5, 0.36, "Watch what happened ↓", color=MUTED, fontsize=34, ha="center", alpha=ease((t - 1.5) / 0.4))

def s2(f):  # build chart 0-7s, candles 0..N
    t = f / FPS
    base(); header("BTCUSDT · 4H", "BTC swept the lows")
    n_vis = min(N, t / 6.2 * N)
    ssl_a = ease((n_vis - 33) / 3)
    flash = max(0, 1 - abs(n_vis - 50.5) / 2.5)
    chart(n_vis, ssl_a=ssl_a, flash=flash, arrow_a=ease((n_vis - LO_I - 1) / 2.5))
    bottom([("Equal lows near 79.4K = stop losses", FG, 34, ssl_a),
            ("Price ran them and tagged 76.3K", MUTED, 30, ease((n_vis - LO_I - 1) / 2.5))])

def s3(f):  # next target 0-4s
    t = f / FPS
    base(); header("BTCUSDT · 4H", "Next pool: 82K")
    chart(N, ssl_a=0.35, arrow_a=0.35, bsl_a=1, bsl_draw=t / 1.2)
    bottom([("Stops below are gone.", FG, 34, 1),
            ("Buy-side liquidity sits above 82K.", MUTED, 30, ease((t - 1.0) / 0.5)),
            ("Who's watching?", GOLD, 34, ease((t - 2.0) / 0.5))])

def s4(f):  # outro 0-2.5s
    t = f / FPS
    base()
    fig.text(0.5, 0.56, "Stop hunting the price.", color=FG, fontsize=60, fontweight="heavy", ha="center", alpha=ease(t / 0.4))
    fig.text(0.5, 0.49, "Hunt the liquidity.", color=GOLD, fontsize=60, fontweight="heavy", ha="center", alpha=ease((t - 0.5) / 0.4))
    fig.text(0.5, 0.40, "Follow for daily sweeps", color=MUTED, fontsize=36, ha="center", alpha=ease((t - 1.0) / 0.4))

SCENES = [("s1", s1, 2.5), ("s2", s2, 7.0), ("s3", s3, 4.0), ("s4", s4, 2.5)]

def grab():
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[:, :, :3].tobytes()

if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    if mode == "preview":
        for name, fn, dur in SCENES:
            for frac in (0.3, 0.98):
                fn(int(dur * FPS * frac)); fig.savefig(f"{out}/prev_{name}_{int(frac*100)}.png", facecolor=BG)
    else:
        files = []
        for name, fn, dur in SCENES:
            n = int(round(dur * FPS)); tmp = f"{out}/{name}.tmp.mp4"
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                  "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                                  "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
            for i in range(n):
                fn(i); p.stdin.write(grab())
            p.stdin.close()
            assert p.wait() == 0
            os.replace(tmp, f"{out}/{name}.mp4"); files.append(f"{name}.mp4")
        with open(f"{out}/list.txt", "w") as fh:
            fh.writelines(f"file '{x}'\n" for x in files)
        print("ok")
