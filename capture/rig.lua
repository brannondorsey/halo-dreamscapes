-- Scripted camera rig: reads data/global/rig/shot.lua (a Lua table) and drives the
-- camera along Catmull-Rom keyframes {t, x,y,z, tx,ty,tz, fov_deg}. Empty file = off.
clua_version = 2.056
local shot, t0, last_src = nil, 0, ""

local function cr(p0, p1, p2, p3, u)
  local u2, u3 = u * u, u * u * u
  return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3)
end

local function sample(keys, t)
  local n = #keys
  if n == 1 or t <= keys[1][1] then return keys[1] end
  if t >= keys[n][1] then return keys[n] end
  local i = 1
  while keys[i + 1][1] < t do i = i + 1 end
  local a, b = keys[i], keys[i + 1]
  local p0, p3 = keys[math.max(1, i - 1)], keys[math.min(n, i + 2)]
  local u = (t - a[1]) / (b[1] - a[1])
  u = u * u * (3 - 2 * u) * (shot.ease and 1 or 0) + u * (shot.ease and 0 or 1)
  local out = { t }
  for k = 2, 8 do out[k] = cr(p0[k], a[k], b[k], p3[k], u) end
  return out
end

-- Strip mode (data/global/rig/strip exists): delete vehicles, weapons, equipment, garbage,
-- projectiles and every biped but the player's. Scenery, lights and the level itself stay.
-- If the file says "hide", vehicles are instead parked far below the map every poll: campaign
-- scripts (b30's Pelicans) still reference them, and deleting them segfaults the game.
-- Uses Chimera's get_object(index), which validates the slot; reading Halo's object table directly
-- only works on CE (on the trial its address is unmapped and the game segfaults).
local STRIP = { [0] = true, [1] = true, [2] = true, [3] = true, [4] = true, [5] = true }
-- "remove <fragment>" lines in the strip file also delete scenery (type 6) whose tag path contains it.
local tag_names = {}
local function tag_name(id)
  if tag_names[id] == nil then
    local t = get_tag(id)
    tag_names[id] = t and read_string(read_dword(t + 0x10)) or ""
  end
  return tag_names[id]
end

-- AI that campaign scripts spawn after setup.sh's one-off ai_erase_all (b30's Covenant waves) is
-- erased as soon as a poll sees a biped that isn't the player. "ai_seen" counts the polls that found
-- one, so cap.sh can refilm a shot an AI wandered into before it was erased.
local ai_seen = 0

local function strip(hide, remove)
  local me = get_dynamic_player()
  if not me then return end
  local ai = false
  for i = 0, 2047 do
    local o = get_object(i)
    if o and o ~= me then
      local t = read_word(o + 0xB4)
      if t == 0 then ai = true end
      local gone = false
      if t == 6 and #remove > 0 then
        local name = tag_name(read_dword(o))
        for _, frag in ipairs(remove) do
          if name:find(frag, 1, true) then gone = true end
        end
      end
      if gone then
        delete_object(i)
      elseif hide and t == 1 then
        write_float(o + 0x5C, 0); write_float(o + 0x60, 0); write_float(o + 0x64, -500)   -- position
        write_float(o + 0x68, 0); write_float(o + 0x6C, 0); write_float(o + 0x70, 0)      -- velocity
      elseif not hide and STRIP[t] then
        delete_object(i)
      end
    end
  end
  if ai then
    ai_seen = ai_seen + 1
    write_file("ai_seen", tostring(ai_seen))
    execute_script("ai_erase_all")
    execute_script("garbage_collect_now")
  end
end

function poll()
  local mode = read_file("strip")
  if mode then
    local remove = {}
    for frag in mode:gmatch("remove (%S+)") do remove[#remove + 1] = frag end
    strip(mode:match("^hide") ~= nil, remove)
  end
  local src = read_file("shot.lua") or ""
  if src ~= last_src then
    last_src = src
    if src:match("%S") then
      local f = load("return " .. src)
      shot = f and f() or nil
      t0 = ticks()
    else
      shot = nil
    end
  end
end

function on_tick()
  if math.floor(ticks()) % 10 == 0 then poll() end
end

function on_camera(x, y, z, fov, fx, fy, fz, ux, uy, uz)
  if not shot then return x, y, z, fov, fx, fy, fz, ux, uy, uz end
  local k = sample(shot.keys, (ticks() - t0) / 30)
  local dx, dy, dz = k[5] - k[2], k[6] - k[3], k[7] - k[4]
  local l = math.sqrt(dx * dx + dy * dy + dz * dz); dx, dy, dz = dx / l, dy / l, dz / l
  -- up = world z orthogonalised against forward
  local d = dz
  local vx, vy, vz = -d * dx, -d * dy, 1 - d * dz
  local m = math.sqrt(vx * vx + vy * vy + vz * vz)
  return k[2], k[3], k[4], math.rad(k[8]), dx, dy, dz, vx / m, vy / m, vz / m
end

set_callback("tick", "on_tick")
set_callback("precamera", "on_camera")
