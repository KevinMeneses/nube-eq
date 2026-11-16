-- Abre una pestaña de demo: pista con audio (fader en -inf, no suena), Nube EQ con bandas tipo "Nube baja",
-- ventana del FX flotante y reproducción en loop para ver el analizador. Cerrar con tests/ui_close.lua.
local ROOT = os.getenv("HOME") .. "/Music/NubeEQ/tests"
local AUDIO = os.getenv("NUBE_AUDIO") or (os.getenv("HOME") .. "/Music/ClaudeBeats/Master/Nube baja (master X20).wav")
local FR, Q, AT, RE = 2, 4, 9, 10
local LOGP = {[FR] = {20, 20000, 1000}, [Q] = {0.1, 18, 1}, [AT] = {0.1, 100, 5}, [RE] = {5, 1000, 100}}
local function setp(tr, fx, idx, v)
  local spec = idx >= 6 and LOGP[(idx - 6) % 12]
  if spec then
    local mn, mx, mid = spec[1], spec[2], spec[3]; local sr = (mx - mn) / (mid - mn) - 1; local r = sr * sr
    reaper.TrackFX_SetParamNormalized(tr, fx, idx, math.log((v - mn) / (mx - mn) * (r - 1) + 1) / math.log(r))
  else reaper.TrackFX_SetParam(tr, fx, idx, v) end
end
local function band(tr, fx, b, ty, f, g, q, sl, ch, dyn)
  local o = 6 + (b - 1) * 12
  local vals = {1, ty, f, g, q, sl or 3, ch or 0, dyn and dyn[1] or 0, dyn and dyn[2] or -30, dyn and dyn[3] or 5, dyn and dyn[4] or 120, dyn and dyn[5] or 0}
  for p = 0, 11 do setp(tr, fx, o + p, vals[p + 1]) end
end
reaper.Main_OnCommand(40859, 0)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "Nube EQ demo", true)
reaper.SetMediaTrackInfo_Value(tr, "D_VOL", 0)
local item = reaper.AddMediaItemToTrack(tr); local take = reaper.AddTakeToMediaItem(item)
local src = reaper.PCM_Source_CreateFromFile(AUDIO); reaper.SetMediaItemTake_Source(take, src)
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", 60)
reaper.UpdateArrange()
local fx = reaper.TrackFX_AddByName(tr, "JS:Nube EQ/nube_eq.jsfx", false, -1)
local mode = os.getenv("NUBE_DEMO") or "voz"
if mode == "voz" then
  band(tr, fx, 5, 3, 80, 0, 0.707, 3)
  band(tr, fx, 2, 1, 110, -6, 0.7)
  band(tr, fx, 3, 0, 315, -5.5, 1.2)
  band(tr, fx, 4, 0, 2500, -3.5, 2.5)
  band(tr, fx, 1, 0, 4500, 0, 1.5, 3, 0, {-6, -40, 1, 80, 0})
  band(tr, fx, 6, 0, 7500, 5.5, 1.2)
  band(tr, fx, 7, 2, 11000, -4.5, 0.7)
  band(tr, fx, 8, 0, 1500, -3, 0.6, 3, 2)
end
reaper.TrackFX_Show(tr, fx, 3)
reaper.GetSet_LoopTimeRange(true, true, 0, 60, false)
reaper.GetSetRepeat(1)
reaper.OnPlayButton()
local f = io.open(ROOT .. "/out/ui.txt", "w"); f:write("done\n"); f:close()
