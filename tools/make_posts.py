import json, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib import font_manager as fm

for f in fm.findSystemFonts():
    if "Inter" in f:
        try: fm.fontManager.addfont(f)
        except Exception: pass
plt.rcParams["font.family"] = "Inter"

BG = "#0B0F14"; PANEL = "#121821"; FG = "#E8EDF2"; MUTED = "#8A97A6"
UP = "#26C281"; DN = "#EF4E5B"; GOLD = "#F5B83D"; ACC = "#3AA0FF"
OUT = sys.argv[1]
data = json.load(open(sys.argv[2]))

def frame(title, kicker):
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor=BG)
    fig.text(0.06, 0.945, kicker, color=GOLD, fontsize=20, fontweight="bold")
    fig.text(0.06, 0.885, title, color=FG, fontsize=40, fontweight="heavy", va="center")
    fig.text(0.06, 0.03, "LIQUIDITY HUNTERS", color=FG, fontsize=18, fontweight="heavy")
    fig.text(0.94, 0.03, "Not financial advice", color=MUTED, fontsize=14, ha="right")
    return fig

def candles(ax, d, n):
    o, h, l, c = (d[k][-n:] for k in "ohlc")
    for i in range(n):
        col = UP if c[i] >= o[i] else DN
        ax.plot([i, i], [l[i], h[i]], color=col, lw=1.4, zorder=2)
        ax.add_patch(Rectangle((i - 0.35, min(o[i], c[i])), 0.7, max(abs(c[i] - o[i]), 1e-9), color=col, zorder=3))
    ax.set_xlim(-1, n + 6)
    ax.set_facecolor(PANEL)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=13, length=0)
    ax.set_xticks([])
    ax.yaxis.tick_right()
    ax.grid(axis="y", color="#1E2733", lw=1)
    return o, h, l, c

def level(ax, y, n, color, label, ls="--"):
    ax.axhline(y, color=color, lw=2, ls=ls, zorder=1)
    ax.text(n + 5.5, y, label, color=BG, fontsize=13, fontweight="bold", ha="right", va="center",
            bbox=dict(boxstyle="round,pad=0.35", fc=color, ec="none"), zorder=5)

def footer_text(fig, lines):
    y = 0.215
    for t, col, sz, w in lines:
        fig.text(0.06, y, t, color=col, fontsize=sz, fontweight=w)
        y -= 0.048

# 1 BTC
d = data["btc"]; n = 60
fig = frame("BTC swept the lows", "BTCUSDT · 4H")
ax = fig.add_axes([0.06, 0.27, 0.86, 0.56])
o, h, l, c = candles(ax, d, n)
lo = min(l); lo_i = l.index(lo)
level(ax, 79370, n, DN, "Sell-side liquidity 79.4K")
level(ax, 82000, n, UP, "Buy-side liquidity 82K")
ax.annotate("Stops taken\n%sK" % f"{lo/1000:.1f}", xy=(lo_i, lo), xytext=(lo_i - 14, lo + 300),
            color=FG, fontsize=15, fontweight="bold", arrowprops=dict(arrowstyle="->", color=FG, lw=2))
footer_text(fig, [
    ("Equal lows near 79.4K were a magnet.", FG, 24, "bold"),
    ("Price ran them, tagged %sK and stalled." % f"{lo/1000:.1f}", MUTED, 21, "normal"),
    ("Next pool above: 82K. Who's watching?", GOLD, 21, "bold"),
])
fig.savefig(f"{OUT}/2026-10-31-01-btc-sweep.png", facecolor=BG); plt.close(fig)

# 2 Gold
d = data["gold"]; n = 60
fig = frame("Gold's floor was a trap", "XAUUSD · 4H")
ax = fig.add_axes([0.06, 0.27, 0.86, 0.56])
o, h, l, c = candles(ax, d, n)
lo = min(l); lo_i = l.index(lo)
level(ax, 3980, n, DN, "Equal lows 3,980")
level(ax, 4065, n, UP, "Range high 4,065")
ax.annotate("Break + sweep\n%s" % f"{lo:,.0f}", xy=(lo_i, lo), xytext=(lo_i - 18, lo + 10),
            color=FG, fontsize=15, fontweight="bold", arrowprops=dict(arrowstyle="->", color=FG, lw=2))
footer_text(fig, [
    ("Everyone saw support at 3,980.", FG, 24, "bold"),
    ("That's exactly where the stops sat.", MUTED, 21, "normal"),
    ("Watch for reclaim of 3,980 or continuation.", GOLD, 21, "bold"),
])
fig.savefig(f"{OUT}/2026-10-31-02-gold-trap.png", facecolor=BG); plt.close(fig)

# 3 Education: liquidity sweep
fig = frame("What is a liquidity sweep?", "SMART MONEY 101")
ax = fig.add_axes([0.06, 0.27, 0.88, 0.56]); ax.set_facecolor(PANEL)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks([]); ax.set_yticks([])
path = [5, 7, 5.2, 7.5, 5.1, 6.6, 5.05, 3.4, 6.2, 8.4, 10.5]
ax.plot(range(len(path)), path, color=FG, lw=4, solid_joinstyle="round")
ax.axhline(5.05, color=DN, ls="--", lw=2.5)
ax.text(0.2, 4.6, "Equal lows = stop losses below", color=DN, fontsize=17, fontweight="bold")
ax.annotate("Sweep", xy=(7, 3.4), xytext=(8.2, 2.6), color=GOLD, fontsize=20, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=GOLD, lw=2.5))
ax.annotate("Real move", xy=(9.6, 9.5), xytext=(6.4, 10.3), color=UP, fontsize=20, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=UP, lw=2.5))
ax.set_ylim(1.8, 11.5); ax.set_xlim(-0.3, 10.5)
footer_text(fig, [
    ("1. Price builds obvious lows.", FG, 23, "bold"),
    ("2. It dips below to grab the stops.", FG, 23, "bold"),
    ("3. Then the real move starts.", GOLD, 23, "bold"),
])
fig.savefig(f"{OUT}/2026-10-31-03-what-is-a-sweep.png", facecolor=BG); plt.close(fig)

# 4 Education: why your stop gets hit
fig = frame("Why your stop gets hit", "TRADER PSYCHOLOGY")
items = [
    ("Your SL sits where everyone's SL sits", "Just under the obvious low or above the obvious high."),
    ("Big players need liquidity", "Your stop is someone else's fill."),
    ("Fix: wait for the sweep", "Enter after the stops are taken, not before."),
]
y = 0.74
for i, (head, sub) in enumerate(items, 1):
    fig.patches.append(FancyBboxPatch((0.06, y - 0.075), 0.88, 0.13, boxstyle="round,pad=0.008,rounding_size=0.02",
                                      transform=fig.transFigure, fc=PANEL, ec="#1E2733"))
    fig.text(0.1, y + 0.01, str(i), color=GOLD, fontsize=46, fontweight="heavy", va="center")
    fig.text(0.19, y + 0.02, head, color=FG, fontsize=23, fontweight="bold", va="center")
    fig.text(0.19, y - 0.03, sub, color=MUTED, fontsize=18, va="center")
    y -= 0.17
footer_text(fig, [
    ("Stop hunting the price.", FG, 26, "bold"),
    ("Start hunting the liquidity.", GOLD, 26, "bold"),
])
fig.savefig(f"{OUT}/2026-10-31-04-why-stop-hit.png", facecolor=BG); plt.close(fig)
print("ok")
