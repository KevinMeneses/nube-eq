-- Escribe el estado de las bandas del Nube EQ de la pista 1 (pestaña actual) en tests/out/dump.txt
local OUT = os.getenv("HOME") .. "/Music/NubeEQ/tests/out"
local f = io.open(OUT .. "/dump.txt", "w")
local tr = reaper.GetTrack(0, 0); local fx = 0
for b = 1, 16 do
  local o = 6 + (b - 1) * 12
  local st = reaper.TrackFX_GetParam(tr, fx, o)
  if st > 0 then
    local t = {}
    for p = 0, 11 do local _, v = reaper.TrackFX_GetFormattedParamValue(tr, fx, o + p); t[#t + 1] = v end
    f:write("B" .. b .. ": " .. table.concat(t, " | "), "\n")
  end
end
local _, g = reaper.TrackFX_GetFormattedParamValue(tr, fx, 0); f:write("salida ", g, "\n")
f:write("done\n"); f:close()
