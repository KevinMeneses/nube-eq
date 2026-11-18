#!/usr/bin/env python3
"""Genera nube_eq.jsfx desde src/nube_eq.template.jsfx.

JSFX no tiene arreglos de sliders, asi que este script escribe:
  - las declaraciones de los 197 sliders (5 globales + 16 bandas x 12 parametros)
  - slider_set(i, v) y slider_aut(i): acceso por indice con un arbol de comparaciones,
    porque slider_automate() necesita la referencia literal sliderN.
"""
import re
from pathlib import Path

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent.parent
NB, NP, P0 = 16, 12, 11

# mismos nombres y orden que preset_name() en la plantilla (sin comas: separan la lista)
PRESETS = [
    "Voz Tonor - Nube baja (cadena exacta)",
    "Voz rap - punto de partida",
    "Voz hablada tipo radio / telefono",
    "De-esser (banda dinamica en las s)",
    "Hueco para la voz (Rhodes o coros; sidechain 3/4)",
    "808 / bajo limpio",
    "Hi-hats y clap sin siseo",
    "Master sutil (Nube baja)",
    "Voz trap - brillo y aire",
    "Voz drill - presencia agresiva",
    "Voz R&B - calida y suave",
    "Coros / dobles - atras",
    "808 - que se escuche en celulares",
    "Kick - golpe y click",
    "Snare / clap - cuerpo y brillo",
    "Hi-hats - suaves (lo-fi)",
    "Pads / keys - hueco para la voz (M/S)",
    "Guitarra acustica - limpia",
    "Bajo / synth bass - definicion",
    "Lo-fi - telefono viejo / cassette",
    "Master - sonrisa (graves y aire)",
    "Master - M/S (centro firme y lados abiertos)",
    "Sidechain: el kick baja el 808 (3/4)",
    "Vacio (sin bandas)",
]

GLOBALS = [
    (1, "0<-24,24,0.1>-Salida (dB)"),
    (2, "0<0,1,1{Apagado,Encendido}>-Auto gain"),
    (3, "1<0,2,1{Apagado,Salida,Entrada y salida}>-Analizador"),
    (4, "1<0,3,1{6 dB,12 dB,24 dB,30 dB}>-Escala de la grafica"),
    (5, "0<0,1,1{Normal,Solo los cambios}>-Escuchar cambios"),
    (6, "0<0,%d,1{-,%s}>-Cargar preset" % (len(PRESETS), ",".join(PRESETS))),
]

TYPES = "Campana,Shelf grave,Shelf agudo,Corte grave (HPF),Corte agudo (LPF),Notch,Pasa banda"
BAND = [
    ("0<0,2,1{Sin usar,Encendida,Apagada}>", "Estado"),
    ("0<0,6,1{%s}>" % TYPES, "Tipo"),
    ("1000<20,20000,0.1:log=1000>", "Frecuencia (Hz)"),
    ("0<-30,30,0.1>", "Ganancia (dB)"),
    ("1<0.1,18,0.01:log=1>", "Q"),
    ("3<0,5,1{6 dB/oct,12 dB/oct,18 dB/oct,24 dB/oct,36 dB/oct,48 dB/oct}>", "Pendiente"),
    ("0<0,4,1{Estereo,Centro (Mid),Lados (Side),Izquierda,Derecha}>", "Canal"),
    ("0<-24,24,0.1>", "Dinamica rango (dB)"),
    ("-30<-60,0,0.1>", "Dinamica umbral (dB)"),
    ("5<0.1,100,0.1:log=5>", "Dinamica ataque (ms)"),
    ("120<5,1000,1:log=100>", "Dinamica release (ms)"),
    ("0<0,1,1{Interna,Sidechain 3/4}>", "Dinamica fuente"),
]


def slider_lines():
    lines = [f"slider{i}:{d}" for i, d in GLOBALS]
    for b in range(NB):
        for p, (spec, name) in enumerate(BAND):
            idx = P0 + b * NP + p
            lines.append(f"slider{idx}:{spec}-B{b + 1} {name}")
    return lines


def indices():
    return [i for i, _ in GLOBALS] + [P0 + k for k in range(NB * NP)]


def tree(idx, leaf):
    if len(idx) == 1:
        return leaf(idx[0])
    mid = len(idx) // 2
    return f"(i < {idx[mid]} ? ({tree(idx[:mid], leaf)}) : ({tree(idx[mid:], leaf)}))"


def setters():
    idx = indices()
    s = "function slider_set(i, v) (\n  " + tree(idx, lambda n: f"slider{n} = v") + ";\n);\n"
    s += "function slider_aut(i) (\n  " + tree(idx, lambda n: f"slider_automate(slider{n})") + ";\n);\n"
    return s


def dup_coeffs(src):
    """Copia las funciones de coeficientes con sufijo _ui: la interfaz corre en otro hilo
    y las variables locales de EEL son estáticas por función (no deben compartirse con el audio)."""
    a = src.index("//@@COEFFS_BEGIN"); b = src.index("//@@COEFFS_END")
    block = src[a:b]
    ui = block
    for fn in ("set_stage", "cut1", "cut2", "calc_coeffs"):
        ui = re.sub(r"\b%s\(" % fn, fn + "_ui(", ui)
    return src[:b] + ui + src[b:]


def check_presets(src):
    for i, name in enumerate(PRESETS, 1):
        assert f'n == {i} ? "{name}"' in src, f"preset {i} no coincide con la plantilla: {name}"


def main():
    check_presets((ROOT / "src" / "nube_eq.template.jsfx").read_text())
    src = dup_coeffs((ROOT / "src" / "nube_eq.template.jsfx").read_text())
    out = (src.replace("@@SLIDERS@@", "\n".join(slider_lines()))
              .replace("@@SETTERS@@", setters())
              .replace("@@VERSION@@", VERSION))
    dst = ROOT / "nube_eq.jsfx"
    dst.write_text(out)
    print(f"{dst} ({len(out.splitlines())} lineas, {len(indices())} sliders)")


if __name__ == "__main__":
    main()
