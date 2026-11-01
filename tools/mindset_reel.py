"""Mindset reel (trading psychology / discipline / consistency / motivation): 1080x1920, 30fps.
usage: python3 mindset_reel.py preview|render <cfg.json> <out_dir>
cfg: {"kicker":"TRADER PSYCHOLOGY",
      "hook":"Your strategy isn't\\nthe problem.",          # visible on frame 0
      "lines":["You moved your stop.","You doubled after a loss.","You traded out of boredom."],
      "punch":"Discipline is\\nthe edge.",                 # big closing line
      "gold":["Discipline","edge"],                        # words drawn in gold
      "seed":3}
All text must be ORIGINAL (no quotes copied from books, films or famous traders).
Timeline: hook 0-2.2s, lines appear every 1.6s, punch, CTA. Returns hit times for beat2 in <out_dir>/hits.txt.
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

BG = "#0B0F14"; FG = "#E8EDF2"; MUTED = "#8A97A6"; GOLD = "#F5B83D"; UP = "#26C281"; DN = "#EF4E5B"
W, H, FPS = 1080, 1920, 30
mode, cfgp, out = sys.argv[1], sys.argv[2], sys.argv[3]
C = json.load(open(cfgp))
GOLDW = [g.strip(".,!?:").lower() for g in C.get("gold", [])]
rng = np.random.default_rng(C.get("seed", 1))

T_HOOK = 2.2; STEP = 1.6
T_LINES = [T_HOOK + i * STEP for i in range(len(C["lines"]))]
T_PUNCH = T_HOOK + len(C["lines"]) * STEP + 0.3
T_CTA = T_PUNCH + 2.4
DUR = T_CTA + 2.3
os.makedirs(out, exist_ok=True)
open(f"{out}/hits.txt", "w").write(",".join(f"{t:.2f}" for t in [T_PUNCH]))

# background: faint random-walk candles drifting left
n_bg = 70
walk = np.cumsum(rng.normal(0, 1, n_bg + 40))
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)

def bg(t):
    ax = fig.add_axes([0, 0.30, 1, 0.45]); ax.axis("off")
    off = t * 2.2
    i0 = int(off); fr = off - i0
    ys = walk[i0:i0 + n_bg + 1]
    ax.set_xlim(0, n_bg); ax.set_ylim(walk.min() - 2, walk.max() + 2)
    for k in range(n_bg):
        o, c = ys[k], ys[k + 1]
        col = UP if c >= o else DN
        x = k - fr
        ax.plot([x, x], [min(o, c) - 0.6, max(o, c) + 0.6], color=col, lw=1.2, alpha=0.10)
        ax.add_patch(Rectangle((x - 0.3, min(o, c)), 0.6, max(abs(c - o), 0.05), color=col, alpha=0.10))

def words(x, y, text, size, a, ha="left", base=FG, weight="heavy", dy=0.0):
    """draw text line, gold-highlighting words in GOLDW. Multi-line via \\n."""
    lines = text.split("\n")
    for li, line in enumerate(lines):
        yy = y - li * size * 0.00062 * 1.25 - dy
        r = fig.canvas.get_renderer()
        parts = line.split(" ")
        # measure total width
        tmp = []
        for p in parts:
            tt = fig.text(0, 0, p + " ", fontsize=size, fontweight=weight)
            bb = tt.get_window_extent(renderer=r); tmp.append(bb.width / W); tt.remove()
        total = sum(tmp)
        cx = x - total / 2 if ha == "center" else x
        for p, w_ in zip(parts, tmp):
            col = GOLD if p.strip(".,!?:").lower() in GOLDW else base
            fig.text(cx, yy, p, color=col, fontsize=size, fontweight=weight, alpha=a, va="center")
            cx += w_

def chrome(t):
    fig.text(0.07, 0.03, "LIQUIDITY HUNTERS", color=FG, fontsize=26, fontweight="heavy")
    fig.text(0.93, 0.03, "Mindset", color=MUTED, fontsize=19, ha="right")
    ax = fig.add_axes([0, 0.992, 1, 0.008]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((0, 0), t / DUR, 1, color=GOLD))

def frame(i):
    t = i / FPS
    fig.clf(); fig.set_facecolor(BG)
    bg(t)
    fig.text(0.07, 0.92, C["kicker"], color=GOLD, fontsize=30, fontweight="bold")
    if t < T_PUNCH:
        hook_y = 0.82 if t >= T_HOOK else 0.60
        size = 54 if t >= T_HOOK else 70
        if t >= T_HOOK:
            k = ease((t - T_HOOK) / 0.35)
            hook_y = 0.60 + (0.82 - 0.60) * k; size = 70 + (54 - 70) * k
        words(0.07, hook_y, C["hook"], size, 1)
        y = 0.62
        for j, (ln, tl) in enumerate(zip(C["lines"], T_LINES)):
            if t < tl + 0.15: break
            a = ease((t - tl - 0.15) / 0.3)
            slide = (1 - a) * 0.03
            fig.text(0.07 - slide, y, "×" if C.get("bullets", "x") == "x" else "→", color=DN if C.get("bullets", "x") == "x" else UP,
                     fontsize=40, fontweight="bold", alpha=a, va="center")
            words(0.15 - slide, y, ln, 42, a, weight="bold")
            y -= 0.075 * (1 + ln.count("\n"))
    elif t < T_CTA:
        a = ease((t - T_PUNCH) / 0.3)
        scale = 1 + 0.25 * max(0, 1 - (t - T_PUNCH) / 0.25)
        words(0.5, 0.58, C["punch"], 84 * scale, a, ha="center")
        if t - T_PUNCH < 0.2:
            fig.patches.append(Rectangle((0, 0), 1, 1, transform=fig.transFigure, color=GOLD, alpha=0.15 * (1 - (t - T_PUNCH) / 0.2)))
    else:
        words(0.5, 0.62, C["punch"], 64, 1, ha="center")
        a = ease((t - T_CTA) / 0.3)
        fig.text(0.5, 0.40, "Save this for your next red day", color=MUTED, fontsize=34, ha="center", alpha=a)
        fig.text(0.5, 0.33, "Follow for daily signals + mindset", color=GOLD, fontsize=40, fontweight="heavy", ha="center", alpha=ease((t - T_CTA - 0.4) / 0.3))
    chrome(t)

if mode == "preview":
    for t in (0.0, T_LINES[-1] + 0.9, T_PUNCH + 0.6, DUR - 0.1):
        frame(int(t * FPS)); fig.savefig(f"{out}/prev_{t:04.1f}.png", facecolor=BG)
    print(f"dur {DUR:.1f}")
else:
    tmp = f"{out}/video.tmp.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        frame(i); fig.canvas.draw()
        p.stdin.write(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].tobytes())
    p.stdin.close(); assert p.wait() == 0
    os.replace(tmp, f"{out}/video.mp4"); print(f"ok dur {DUR:.1f}")
