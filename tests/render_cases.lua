-- Carga Nube EQ en una pestaña nueva, renderiza cada caso y cierra la pestaña.
-- Uso: REAPER -nonewinst tests/render_cases.lua   (escribe tests/out/*.wav y tests/out/log.txt)
local ROOT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
local OUT = ROOT .. "/out"
os.execute('mkdir -p "' .. OUT .. '"')
local logf = io.open(OUT .. "/log.txt", "w")
local function log(...) local t = {} for i, v in ipairs({...}) do t[#t+1] = tostring(v) end logf:write(table.concat(t, " "), "\n") logf:flush() end

-- índice de parámetro: global g (1..6) -> g-1 ; banda b (1..16) parámetro p (0..11) -> 6 + (b-1)*12 + p
local function G(g) return g - 1 end
local function B(b, p) return 6 + (b - 1) * 12 + p end
local ST, TY, FR, GA, Q, SL, CH, DR, TH, AT, RE, SRC = 0,1,2,3,4,5,6,7,8,9,10,11

local function band(b, ty, f, g, q, sl, ch)
  return {{B(b,ST),1},{B(b,TY),ty},{B(b,FR),f},{B(b,GA),g or 0},{B(b,Q),q or 1},{B(b,SL),sl or 3},{B(b,CH),ch or 0}}
end
-- sliders con forma :log=mid -> REAPER los expone normalizados 0..1
local LOGP = {[FR] = {20, 20000, 1000}, [Q] = {0.1, 18, 1}, [AT] = {0.1, 100, 5}, [RE] = {5, 1000, 100}}
local function to_param(idx, v)
  if idx < 6 then return v end
  local spec = LOGP[(idx - 6) % 12]
  if not spec then return v end
  local mn, mx, mid = spec[1], spec[2], spec[3]
  local sr = (mx - mn) / (mid - mn) - 1; local r = sr * sr
  return math.log((v - mn) / (mx - mn) * (r - 1) + 1) / math.log(r)
end
local function cat(...) local r = {} for _, t in ipairs({...}) do for _, v in ipairs(t) do r[#r+1] = v end end return r end

local CASES = {
  {"flat",        "impulse.wav",   {}},
  {"bell1k_+6",   "impulse.wav",   band(1, 0, 1000, 6, 1)},
  {"bell1k_-12_q4","impulse.wav",  band(1, 0, 1000, -12, 4)},
  {"hpf100_24",   "impulse.wav",   band(1, 3, 100, 0, 0.707, 3)},
  {"hpf100_6",    "impulse.wav",   band(1, 3, 100, 0, 0.707, 0)},
  {"hpf100_48",   "impulse.wav",   band(1, 3, 100, 0, 0.707, 5)},
  {"lpf5k_12",    "impulse.wav",   band(1, 4, 5000, 0, 0.707, 1)},
  {"lpf5k_18",    "impulse.wav",   band(1, 4, 5000, 0, 0.707, 2)},
  {"ls200_-6",    "impulse.wav",   band(1, 1, 200, -6, 0.707)},
  {"hs8k_+4",     "impulse.wav",   band(1, 2, 8000, 4, 0.707)},
  {"notch60",     "impulse.wav",   band(1, 5, 60, 0, 4)},
  {"bp1k",        "impulse.wav",   band(1, 6, 1000, 0, 2)},
  {"mid_bell1k_-12","impulse_L.wav", band(1, 0, 1000, -12, 1, 3, 1)},
  {"side_bell1k_-12","impulse_L.wav",band(1, 0, 1000, -12, 1, 3, 2)},
  {"left_only_+6","impulse.wav",   band(1, 0, 1000, 6, 1, 3, 3)},
  {"three_bands", "impulse.wav",   cat(band(1, 3, 80, 0, 0.707, 3), band(2, 0, 315, -5.5, 1.2), band(3, 2, 10000, 3, 0.707))},
  {"bypassed",    "impulse.wav",   cat(band(1, 0, 1000, 6, 1), {{B(1,ST),2}})},
  {"out_-6",      "impulse.wav",   {{G(1), -6}}},
  {"autogain_hs", "impulse.wav",   cat(band(1, 2, 5000, 6, 0.707), {{G(2), 1}})},
  {"delta_bell",  "impulse.wav",   cat(band(1, 0, 1000, 6, 1), {{G(5), 1}})},
  {"dyn5k",       "sine5k.wav",    cat(band(1, 0, 5000, 0, 1.5), {{B(1,DR),-6},{B(1,TH),-30},{B(1,AT),1},{B(1,RE),80}})},
  {"dyn5k_up",    "sine5k.wav",    cat(band(1, 0, 5000, 0, 1.5), {{B(1,DR),4},{B(1,TH),-20},{B(1,AT),1},{B(1,RE),80}})},
  {"dyn_off_1k",  "sine1k.wav",    cat(band(1, 0, 5000, 0, 1.5), {{B(1,DR),-6},{B(1,TH),-30}})},
  {"preset1",     "impulse.wav",   {{G(6), 1}}},
  {"preset3",     "impulse.wav",   {{G(6), 3}}},
  {"preset6",     "impulse.wav",   {{G(6), 6}}},
  {"preset8",     "impulse.wav",   {{G(6), 8}}},
  {"preset4_s",   "sine5k.wav",    {{G(6), 4}}},
  {"sc_duck",     "sidechain4.wav", {{G(6), 5}}, 4},
  {"16_bands",    "impulse.wav",   (function() local r = {} for b = 1, 16 do for _, v in ipairs(band(b, 0, 40 * 1.5 ^ b, (b % 2 == 0) and 1 or -1, 2)) do r[#r+1] = v end end return r end)()},
}

local only = os.getenv("NUBE_CASE")

reaper.Main_OnCommand(40859, 0) -- nueva pestaña
reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 1, true)
local tr
reaper.InsertTrackAtIndex(0, false); tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr)
local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0)
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", 2)

for _, c in ipairs(CASES) do
  local name, src, params = c[1], c[2], c[3]
  reaper.SetMediaTrackInfo_Value(tr, "I_NCHAN", c[4] or 2)
  local s = reaper.PCM_Source_CreateFromFile(ROOT .. "/signals/" .. src)
  reaper.SetMediaItemTake_Source(take, s)
  reaper.UpdateItemInProject(item)
  while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
  local fx = reaper.TrackFX_AddByName(tr, "JS:Nube EQ/nube_eq.jsfx", false, -1)
  if fx < 0 then log("ERROR no cargó el FX") break end
  for _, pv in ipairs(params) do
    local idx, v = pv[1], pv[2]
    if idx >= 6 and LOGP[(idx - 6) % 12] then reaper.TrackFX_SetParamNormalized(tr, fx, idx, to_param(idx, v))
    else reaper.TrackFX_SetParam(tr, fx, idx, v) end
  end
  local np = reaper.TrackFX_GetNumParams(tr, fx)
  local file = OUT .. "/" .. name .. ".wav"
  os.remove(file)
  reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
  reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
  reaper.GetSetProjectInfo(0, "RENDER_SRATE", 48000, true)
  reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
  reaper.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, true)
  reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true)
  reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
  reaper.Main_OnCommand(42230, 0)
  log("caso", name, "params", np)
end
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_test.rpp", 0)
reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_test.rpp") -- queda con ruta y sin cambios: se cierra sin preguntar
reaper.Main_OnCommand(40860, 0) -- cerrar pestaña
log("done")
logf:close()
