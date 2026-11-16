"""Ayudante para probar la interfaz con cliclick (ventana del FX en su posición/tamaño por defecto)."""
import math, subprocess, sys, time, pathlib
WX, WY, WW, WH = 26, 66, 980, 633      # ventana del FX (puntos)
GY0 = 53                               # alto de la cabecera de REAPER sobre el área gráfica
ROOT = pathlib.Path(__file__).resolve().parent.parent
def layout():
    W, H = WW, WH - GY0
    gx, gy = 46, 50; gw = W - gx - 16; gh = H - 44 - 176 - 26 - 20 - 14
    return gx, gy, gw, gh
def fx(f): gx, gy, gw, gh = layout(); return WX + gx + gw * math.log10(f / 20) / 3
def dy(d, rng=12): gx, gy, gw, gh = layout(); return WY + GY0 + gy + gh / 2 - d / rng * (gh / 2 - 8)
def pt(x, y): return f"{round(x)},{round(y)}"
def cc(*args): subprocess.run(["cliclick", "-w", "60", *args], check=True); time.sleep(0.4)
def shot(name, region=None):
    r = region or (WX, WY, WW, WH)
    out = f"/private/tmp/claude-501/-Users-kevinmeneses/67769d65-5737-44ef-8d28-6108103eafbe/scratchpad/{name}.png"
    subprocess.run(["screencapture", "-x", "-R" + ",".join(map(str, r)), out], check=True); return out
def dump():
    p = ROOT / "tests/out/dump.txt"; p.unlink(missing_ok=True)
    subprocess.Popen(["/Applications/REAPER.app/Contents/MacOS/REAPER", "-nonewinst", str(ROOT / "tests/ui_dump.lua")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if p.exists() and "done" in p.read_text(): return p.read_text().replace("done\n", "")
        time.sleep(0.25)
    return "(sin respuesta)"
