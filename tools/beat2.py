import numpy as np, wave, sys, argparse
ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('--seed', type=int, default=23); ap.add_argument('--bpm', type=float, default=128)
ap.add_argument('--hook', type=float, default=1.5); ap.add_argument('--hits', default='6.4,10.4')
ap.add_argument('--key', default='dm')
ARGS = ap.parse_args()
SR = 44100; DUR = 16.0; BPM = ARGS.bpm
beat = 60 / BPM; n = int(SR * DUR)
mix = np.zeros((n, 2))
rng = np.random.default_rng(ARGS.seed)
t_all = np.arange(n) / SR

def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= n: return
    sig = sig[: n - i] * gain
    mix[i:i + len(sig), 0] += sig * (1 - max(pan, 0))
    mix[i:i + len(sig), 1] += sig * (1 + min(pan, 0))

def env(L, a=0.002, r=0.2):
    t = np.arange(int(L * SR)) / SR
    return np.minimum(1, t / a) * np.exp(-t / r)

def kick(L=0.5):
    t = np.arange(int(L * SR)) / SR
    f = 45 + 110 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(L, 0.001, 0.18)

def eight08(freq, L):
    t = np.arange(int(L * SR)) / SR
    f = freq * (1 + 0.6 * np.exp(-t * 40))
    s = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR))
    return s * env(L, 0.003, L * 0.6)

def clap(L=0.25):
    s = rng.normal(0, 1, int(L * SR))
    e = np.zeros_like(s)
    for d in (0, 0.01, 0.02):
        i = int(d * SR); e[i:] += env(L - d, 0.001, 0.05)[: len(e) - i]
    s = s * e
    return np.convolve(s, [1, -0.9], "same") * 0.5

def hat(L=0.05, open_=False):
    s = rng.normal(0, 1, int(L * SR))
    s = np.diff(np.concatenate([[0], s]))
    return s * env(L, 0.0005, 0.05 if open_ else 0.012)

def pad(freqs, L):
    t = np.arange(int(L * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 0.5) for f in freqs) / len(freqs)
    a = np.minimum(1, t / 0.3) * np.minimum(1, (L - t) / 0.4)
    return s * a

def impact(L=2.5):
    t = np.arange(int(L * SR)) / SR
    boom = np.sin(2 * np.pi * np.cumsum(30 + 80 * np.exp(-t * 6)) / SR) * np.exp(-t * 1.6)
    noise = rng.normal(0, 1, len(t)) * np.exp(-t * 3) * 0.25
    return np.tanh(1.5 * (boom + noise))

def riser(L=1.5):
    t = np.arange(int(L * SR)) / SR
    s = rng.normal(0, 1, len(t)) * (t / L) ** 2
    return np.convolve(s, np.ones(8) / 8, "same")

A, F, C, G = 55.0, 43.65, 65.41, 49.0
KEYS = {'dm': ([(293.66, 349.23, 440), (233.08, 293.66, 349.23), (174.61, 220, 261.63), (196, 261.63, 329.63)], [73.42, 58.27, 43.65, 65.41]),
        'am': ([(220, 261.63, 329.63), (174.61, 220, 261.63), (261.63, 329.63, 392), (196, 246.94, 293.66)], [55.0, 43.65, 65.41, 49.0]),
        'em': ([(164.81, 196, 246.94), (261.63, 329.63, 392), (196, 246.94, 293.66), (146.83, 185, 220)], [41.2, 65.41, 49.0, 73.42])}
chords, roots = KEYS[ARGS.key]
bar = 4 * beat
nbars = int(np.ceil(DUR / bar))
HITS = [float(x) for x in ARGS.hits.split(',')]
SWEEP = HITS[-1]; BSLHIT = HITS[0] if len(HITS) > 1 else None
HOOK = ARGS.hook

for b in range(nbars):
    t0 = b * bar
    add(pad(chords[b % 4], bar), t0, 0.11)
    for k, at in enumerate((0, 1.5, 2.75)):
        tt = t0 + at * beat
        if tt < HOOK: continue  # intro: no drums under hook
        if abs(tt - SWEEP) < 0.6: continue
        add(kick(), tt, 0.9)
        add(eight08(roots[b % 4], 1.4 * beat), tt, 0.55)
    for at in (1, 3):
        tt = t0 + at * beat
        if tt >= HOOK and abs(tt - SWEEP) > 0.4: add(clap(), tt, 0.5, pan=0.1)
    for s16 in range(16):
        tt = t0 + s16 * beat / 4
        if tt < HOOK: continue
        roll = (b % 2 == 1 and s16 >= 13)
        if s16 % 2 == 0 or roll:
            add(hat(), tt, 0.18 if s16 % 4 else 0.25, pan=-0.3)
            if roll: add(hat(), tt + beat / 8, 0.14, pan=-0.3)

add(impact(1.0), 0.0, 0.55)              # frame-0 hit for the hook
add(riser(HOOK), 0.0, 0.14)
add(impact(), HOOK, 0.5)
add(riser(1.6), SWEEP - 1.6, 0.22)       # build into sweep
add(impact(), SWEEP, 0.9)
if BSLHIT is not None:
    add(riser(0.9), BSLHIT - 0.9, 0.14)
    add(impact(1.4), BSLHIT, 0.6)

fade = np.minimum(1, (DUR - t_all) / 1.5)[:, None]
mix *= fade
mix /= np.max(np.abs(mix)) / 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(ARGS.out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok")
