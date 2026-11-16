"""Señales de prueba (48 kHz, estéreo, float32)."""
import numpy as np, soundfile as sf, pathlib
D = pathlib.Path(__file__).parent / "signals"; D.mkdir(exist_ok=True)
SR = 48000
def save(name, L, R): sf.write(D / name, np.stack([L, R], 1).astype(np.float32), SR, subtype="FLOAT")
n = SR * 2; z = np.zeros(n)
imp = z.copy(); imp[SR // 10] = 0.5
save("impulse.wav", imp, imp)
save("impulse_L.wav", imp, z)
t = np.arange(n) / SR
s5 = 10 ** (-10 / 20) * np.sin(2 * np.pi * 5000 * t)
save("sine5k.wav", s5, s5)
s1 = 10 ** (-10 / 20) * np.sin(2 * np.pi * 1000 * t)
save("sine1k.wav", s1, s1)
# sidechain: tono 1.5 kHz en 1/2 todo el tiempo; ruido de 300 Hz-4 kHz en 3/4 solo de 0.2 a 1.0 s
from scipy import signal as sg
t1 = 10 ** (-10 / 20) * np.sin(2 * np.pi * 1500 * t)
nz = np.random.default_rng(1).standard_normal(n); nz = sg.sosfilt(sg.butter(4, [300, 4000], "band", fs=SR, output="sos"), nz)
nz = 0.3 * nz / np.abs(nz).max(); nz[: int(0.2 * SR)] = 0; nz[int(1.0 * SR):] = 0
sf.write(D / "sidechain4.wav", np.stack([t1, t1, nz, nz], 1).astype(np.float32), SR, subtype="FLOAT")
print("ok", sorted(p.name for p in D.iterdir()))
