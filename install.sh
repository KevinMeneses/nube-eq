#!/bin/zsh
# Instala Nube EQ en REAPER (macOS) como enlace: los cambios del repo se ven al volver a insertar el FX.
set -e
DST="$HOME/Library/Application Support/REAPER/Effects/Nube EQ"
cd "$(dirname "$0")"
python3 tools/build.py
mkdir -p "$DST"
ln -sf "$PWD/nube_eq.jsfx" "$DST/nube_eq.jsfx"
echo "Listo: en REAPER busca \"Nube EQ\" en el navegador de FX (JS: Nube EQ)."
