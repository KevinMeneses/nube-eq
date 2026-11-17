#!/bin/zsh
# Renderiza los casos en REAPER (pestaña temporal) y verifica la respuesta.
cd "$(dirname "$0")/.."
python3 tools/build.py >/dev/null || exit 1
PY=${NUBE_PY:-python3}   # necesita numpy, scipy y soundfile
[ -f tests/signals/impulse.wav ] || $PY tests/make_signals.py
rm -f tests/out/log.txt
/Applications/REAPER.app/Contents/MacOS/REAPER -nonewinst "$PWD/tests/render_cases.lua" >/dev/null 2>&1 &
for i in $(seq 1 120); do grep -q done tests/out/log.txt 2>/dev/null && break; sleep 1; done
grep -q done tests/out/log.txt || { echo "REAPER no terminó (¿diálogo abierto?)"; exit 1; }
grep -i error tests/out/log.txt
$PY tests/check.py
