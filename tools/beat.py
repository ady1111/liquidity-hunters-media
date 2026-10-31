import numpy as np, wave, sys
SR = 44100; DUR = 16.0; BPM = 140
beat = 60 / BPM; n = int(SR * DUR)
mix = np.zeros((n, 2))
rng = np.random.default_rng(7)
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
chords = [(220, 261.63, 329.63), (174.61, 220, 261.63), (261.63, 329.63, 392), (196, 246.94, 293.66)]
roots = [A, F, C, G]
bar = 4 * beat
nbars = int(np.ceil(DUR / bar))
SWEEP = 7.7  # sweep moment in video

for b in range(nbars):
    t0 = b * bar
    add(pad(chords[b % 4], bar), t0, 0.11)
    for k, at in enumerate((0, 1.5, 2.75)):
        tt = t0 + at * beat
        if tt < 2.5: continue  # intro: no drums under hook
        if abs(tt - SWEEP) < 0.6: continue
        add(kick(), tt, 0.9)
        add(eight08(roots[b % 4], 1.4 * beat), tt, 0.55)
    for at in (1, 3):
        tt = t0 + at * beat
        if tt >= 2.5 and abs(tt - SWEEP) > 0.4: add(clap(), tt, 0.5, pan=0.1)
    for s16 in range(16):
        tt = t0 + s16 * beat / 4
        if tt < 2.5: continue
        roll = (b % 2 == 1 and s16 >= 13)
        if s16 % 2 == 0 or roll:
            add(hat(), tt, 0.18 if s16 % 4 else 0.25, pan=-0.3)
            if roll: add(hat(), tt + beat / 8, 0.14, pan=-0.3)

add(riser(1.4), 2.5 - 1.4, 0.18)        # into the drop after hook
add(impact(), 2.5, 0.5)
add(riser(1.6), SWEEP - 1.6, 0.22)       # build into sweep
add(impact(), SWEEP, 0.9)

fade = np.minimum(1, (DUR - t_all) / 1.5)[:, None]
mix *= fade
mix /= np.max(np.abs(mix)) / 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok")
