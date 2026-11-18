"""Compara los renders de tests/out con la respuesta teórica. Sale con código 1 si algo falla."""
import numpy as np, soundfile as sf, pathlib, sys
from scipy import signal
D = pathlib.Path(__file__).parent / "out"; SR = 48000
FREQS = np.array([30, 60, 100, 200, 315, 500, 1000, 2000, 3000, 5000, 8000, 12000, 16000])

def rbj(kind, f0, g=0, q=0.7071):
    A = 10 ** (g / 40); w = 2 * np.pi * f0 / SR; c, s = np.cos(w), np.sin(w); al = s / (2 * q)
    if kind == "bell": b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    elif kind == "notch": b = [1, -2 * c, 1]; a = [1 + al, -2 * c, 1 - al]
    elif kind == "bp": b = [al, 0, -al]; a = [1 + al, -2 * c, 1 - al]
    elif kind in ("ls", "hs"):
        sA = 2 * np.sqrt(A) * al
        if kind == "ls":
            b = [A * ((A + 1) - (A - 1) * c + sA), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sA)]
            a = [(A + 1) + (A - 1) * c + sA, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sA]
        else:
            b = [A * ((A + 1) + (A - 1) * c + sA), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sA)]
            a = [(A + 1) - (A - 1) * c + sA, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sA]
    return b, a

def resp(ba_list, f=FREQS):
    h = np.ones(len(f), complex)
    for item in ba_list:
        if isinstance(item, np.ndarray): h *= signal.sosfreqz(item, worN=f, fs=SR)[1]
        else: h *= signal.freqz(item[0], item[1], worN=f, fs=SR)[1]
    return h

def db(x): return 20 * np.log10(np.abs(x) + 1e-15)
def bw(n, f0, kind): return [signal.butter(n, f0, kind, fs=SR, output="sos")]

def measured(name, ch=0, ref=None):
    x, sr = sf.read(D / f"{name}.wav"); assert sr == SR
    n = 65536; X = np.fft.rfft(x[:n, ch]); fr = np.fft.rfftfreq(n, 1 / SR)
    H = X / (0.5 * np.exp(-2j * np.pi * fr * (SR // 10) / SR))
    return np.interp(FREQS, fr, H.real) + 1j * np.interp(FREQS, fr, H.imag)

def rms_db(name, t0=1.0, t1=1.9):
    x, _ = sf.read(D / f"{name}.wav"); seg = x[int(t0 * SR):int(t1 * SR), 0]
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) * np.sqrt(2))

fails = 0
def check(name, expect_db, tol=0.15, ch=0, mask=None):
    global fails
    m = db(measured(name, ch)); e = np.asarray(expect_db)
    ok = np.ones(len(FREQS), bool) if mask is None else mask
    ok &= e > -60   # no comparar en el fondo de un corte profundo
    err = np.abs(m - e)[ok].max()
    st = "OK " if err <= tol else "MAL"
    if err > tol: fails += 1
    print(f"{st} {name:18s} err máx {err:5.2f} dB | " + " ".join(f"{f}:{v:+.1f}" for f, v in zip(FREQS, m)))

def scalar(name, got, want, tol):
    global fails
    st = "OK " if abs(got - want) <= tol else "MAL"
    if abs(got - want) > tol: fails += 1
    print(f"{st} {name:18s} {got:+.2f} dB (esperado {want:+.2f})")

Z = np.zeros(len(FREQS))
check("flat", Z, 0.01)
check("bell1k_+6", db(resp([rbj("bell", 1000, 6, 1)])))
check("bell1k_-12_q4", db(resp([rbj("bell", 1000, -12, 4)])))
check("hpf100_24", db(resp(bw(4, 100, "high"))))
check("hpf100_6", db(resp(bw(1, 100, "high"))))
check("hpf100_48", db(resp(bw(8, 100, "high"))), 0.3)
check("lpf5k_12", db(resp(bw(2, 5000, "low"))))
check("lpf5k_18", db(resp(bw(3, 5000, "low"))))
check("ls200_-6", db(resp([rbj("ls", 200, -6, 0.707)])))
check("hs8k_+4", db(resp([rbj("hs", 8000, 4, 0.707)])))
check("notch60", db(resp([rbj("notch", 60, 0, 4)])), 0.3)
check("bp1k", db(resp([rbj("bp", 1000, 0, 2)])))
# M/S con impulso solo en L: L = m' + s ; R = m' - s
hm = resp([rbj("bell", 1000, -12, 1)])
check("mid_bell1k_-12", db(0.5 * hm + 0.5), ch=0)
check("mid_bell1k_-12", db(0.5 * hm - 0.5), ch=1, mask=np.abs(db(0.5 * hm - 0.5)) < 40)
check("side_bell1k_-12", db(0.5 + 0.5 * hm), ch=0)
check("side_bell1k_-12", db(0.5 - 0.5 * hm), ch=1, mask=np.abs(db(0.5 - 0.5 * hm)) < 40)
check("left_only_+6", db(resp([rbj("bell", 1000, 6, 1)])), ch=0)
check("left_only_+6", Z, 0.01, ch=1)
check("three_bands", db(resp(bw(4, 80, "high") + [rbj("bell", 315, -5.5, 1.2), rbj("hs", 10000, 3, 0.707)])))
check("bypassed", Z, 0.01)
check("out_-6", Z - 6, 0.01)
# auto gain: compensación = -10 log10(media pesada de |H|^2) en 48 puntos log 40 Hz - 16 kHz
fa = 40 * 400 ** (np.arange(48) / 47)
wa = 1 / (1 + (fa / 2000) ** 1.2) / (1 + (60 / fa) ** 2)
comp = -10 * np.log10(np.sum(wa * np.abs(resp([rbj("hs", 5000, 6, 0.707)], fa)) ** 2) / wa.sum())
check("autogain_hs", db(resp([rbj("hs", 5000, 6, 0.707)])) + comp)
check("delta_bell", db(resp([rbj("bell", 1000, 6, 1)]) - 1), 0.2, mask=db(resp([rbj("bell", 1000, 6, 1)]) - 1) > -40)
# dinámica: seno 5k a -10 dBFS; detector ~ -10 dB, umbral -30 -> exceso 20 dB -> min(6, 15) = 6 dB
scalar("dyn5k", rms_db("dyn5k"), -16.0, 0.4)
scalar("dyn5k_up", rms_db("dyn5k_up"), -10 + 4, 0.4)
scalar("dyn_off_1k", rms_db("dyn_off_1k"), -10 + db(resp([rbj("bell", 5000, 0, 1.5)], np.array([1000])))[0] - 0.0, 0.6)
e16 = np.zeros(len(FREQS))
for b in range(1, 17):
    e16 += db(resp([rbj("bell", 40 * 1.5 ** b, 1 if b % 2 == 0 else -1, 2)]))
check("16_bands", e16, 0.2)
# presets (impulso: la banda dinámica no actúa)
check("preset1", db(resp(bw(4, 80, "high") + [rbj("ls", 110, -6, 0.7), rbj("ls", 200, -4, 0.7), rbj("bell", 250, -1, 0.9),
      rbj("bell", 300, -3, 1.5), rbj("bell", 315, -5.5, 1.2), rbj("bell", 2500, -3.5, 2.5), rbj("bell", 3500, -4.5, 0.8),
      rbj("bell", 7500, 5.5, 1.2), rbj("hs", 11000, -4.5, 0.7)])), 0.2)
check("preset3", db(resp(bw(4, 400, "high") + bw(4, 3500, "low") + [rbj("bell", 1500, 4, 1.0)])), 0.2)
check("preset6", db(resp(bw(4, 25, "high") + [rbj("ls", 60, 2, 0.7), rbj("bell", 95, -5, 1.4)])), 0.2)
check("preset8", db(resp(bw(4, 25, "high") + [rbj("bell", 250, -0.8, 1.0), rbj("bell", 3000, 0.9, 1.0), rbj("hs", 10000, 1.4, 0.7)])), 0.2)
# presets agregados (las bandas dinámicas no actúan con el impulso; con L = R las bandas de lados no hacen nada)
H, L2, B = lambda f: bw(4, f, "high"), lambda f: bw(2, f, "low"), lambda f, g, q: rbj("bell", f, g, q)
for p, ex in ((9, H(90) + [B(250, -2.5, 1), B(3500, 2, 0.9), rbj("hs", 12000, 3, 0.7)]),
              (10, H(110) + [B(400, -3, 1.2), B(2000, 2.5, 1), B(5000, 2, 1.5)]),
              (11, H(70) + [rbj("ls", 180, 1.5, 0.7), rbj("hs", 10000, 2, 0.7)]),
              (12, H(200) + [B(3000, -2, 0.8)] + L2(9000)),
              (13, H(28) + [B(100, 2.5, 1.2), B(300, -2, 1)]),
              (14, H(30) + [B(60, 2, 1.2), B(300, -4, 1.5), B(3500, 3, 1.5)]),
              (15, H(120) + [B(200, 2, 1.2), B(800, -2, 2), rbj("hs", 8000, 2.5, 0.7)]),
              (16, H(400) + [B(6000, -2, 1)] + L2(9000)),
              (17, H(120) + [B(2500, -3, 0.8)]),
              (18, H(90) + [B(200, -3, 1.2), B(5000, 2, 1), rbj("hs", 12000, 1.5, 0.7)]),
              (19, H(35) + [B(80, 1.5, 1), B(250, -2.5, 1.2), B(900, 2, 1.5)]),
              (20, bw(2, 250, "high") + L2(5000) + [B(1000, 3, 0.8)]),
              (21, H(25) + [rbj("ls", 80, 1, 0.7), B(400, -0.8, 0.8), rbj("hs", 12000, 1.5, 0.7)]),
              (22, H(25)),
              (23, [])):
    check(f"preset{p}", db(resp(ex)), 0.2)
# de-esser: seno 5k a -10 dBFS, campana 6k Q1.6 rango -8 umbral -32; detector ve ~-10.6 -> exceso ~21 -> -8 dB en 6k; en 5k menos
x5 = db(resp([rbj("bell", 6000, -8, 1.6)], np.array([5000])))[0]
scalar("preset4_s", rms_db("preset4_s"), -10 + x5, 0.5)
# sidechain: con "voz" en 3/4 (0.2-1.0 s) la campana Mid de 1.5 kHz baja hasta -5 dB; sin voz, 0 dB
scalar("sc_duck con voz", rms_db("sc_duck", 0.5, 0.95), -15.0, 0.6)
scalar("sc_duck sin voz", rms_db("sc_duck", 1.6, 1.95), -10.0, 0.3)
print("\nFALLAS:", fails)
sys.exit(1 if fails else 0)
