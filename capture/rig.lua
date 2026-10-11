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

function poll()
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
