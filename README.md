# Snapmaker U1 — Conditional Heat-Soak Macros

## Read This First: `/oem/.debug` Controls Persistence

The U1 mounts `/home/lava/` (where Klipper lives) on an overlay filesystem whose
upper layer is **wiped on every boot** by `/etc/init.d/S01aoverlayfs` — *unless*
`/oem/.debug` exists. Without that flag file, anything you drop into
`~/klipper/klippy/extras/` (Python plugins) or modify under `/etc/`, `/usr/`,
etc. silently reverts on the next reboot.

### What persists *without* `/oem/.debug`

- Files in `/oem/printer_data/config/` — including the `.cfg` files in this
  repo. Klipper reads its configs from there via the `~/printer_data` symlink.
  The standard install steps below do not need debug mode.
- Anything else under `/oem/`.

### What does NOT persist without `/oem/.debug`

- Python plugins in `~/klipper/klippy/extras/` (e.g., the
  [pandabreath-klipper](https://github.com/justinh-rahb/pandabreath-klipper)
  bridge for the BIQU Panda Breath chamber heater).
- Modifications to `/etc/`, `/usr/`, or anywhere else outside `/oem/`.
- New scripts in `/etc/init.d/`.

### Enable / disable

```sh
sudo touch /oem/.debug     # enable persistence — surviving reboots
sudo rm    /oem/.debug     # disable — back to overlay-wipe-on-boot
```

A reboot is needed for the setting to take effect.

### Trade-offs

- With `/oem/.debug` on, *every* filesystem change outside `/oem/` persists —
  including mistakes. Recovery is `sudo rm /oem/.debug && reboot`, which
  returns the system to firmware-default state for everything except `/oem/`
  (configs and printer_data).
- Factory reset most likely leaves `/oem/.debug` intact (it lives in `/oem/`
  alongside other persistent settings; common factory-reset targets are
  `/oem/overlay/*` and `/oem/printer_data/`, not the partition root).
  Verify on your unit before relying on factory reset as an escape hatch:
  ```sh
  sudo touch /oem/.debug
  echo marker | sudo tee /oem/overlay/upper/.persist-test
  # ...trigger factory reset, then on next boot:
  ls /oem/.debug /oem/overlay/upper/.persist-test
  ```
  If both files survive, factory reset is debug-mode-friendly. If `/oem/.debug`
  is gone, factory reset wipes the partition further and you'll need to
  re-enable debug mode each time.

Source for this behaviour: `/etc/init.d/S01aoverlayfs` — the
`rm -rf /oem/overlay/*` line guarded by `[ ! -f /oem/.debug ]`.

---

## Status (June 2026)

**Active chamber heating is now integrated.** The BIQU Panda Breath chamber
heater is exposed to Klipper as a native `[heater_generic panda_breath]` via
the [pandabreath-klipper](https://github.com/justinh-rahb/pandabreath-klipper)
plugin (a single-file Python WebSocket bridge dropped into
`~/klipper/klippy/extras/`, persisted via `/oem/.debug`). Chamber temperature
is now controllable via:

- Standard Klipper gcode (`SET_HEATER_TEMPERATURE HEATER=panda_breath TARGET=60`)
- Slicer per-filament settings (Orca's *"Activate chamber temperature control"* +
  *"Chamber temperature: 60°C"* → emits `M141 S60` / `M191 S60` automatically)
- Klipper macros (used in `PRINT_END_COOLDOWN` below)

**Implication for this repo:**

- **`heatsoak.cfg` is no longer required for the standard workflow.** It existed
  to fake a chamber heater by maxing the bed and waiting for cavity-sensor
  stabilization via rate-of-change detection. With a real chamber heater, the
  slicer's `M191 S<chamber-temp>` (set-and-wait, per-filament) replaces the
  whole orchestration. The file is kept in the repo as legacy/reference and can
  be removed from `printer.cfg`'s `[include]` list at your discretion.
- **`PRINT_WARMUP` is now a thin wrapper** that pre-heats the nozzle + bed and
  homes the printer. Filament-conditional soak gating is gone — the slicer
  gates chamber heating per-filament in its own filament-start g-code.
- **`PRINT_END_COOLDOWN` was tested but did not work in practice.** A ~4-hour
  stepped bed-and-chamber ramp (50 min @ 100 °C bed / chamber 60 °C, walking
  down through ASA's Tg-crossing zone) showed no measurable reduction in
  post-print warping on ASA. The macro is preserved in `print_macros.cfg` and
  the slicer end-gcode line is left commented out in
  `slicer-config/orca-end-gcode.cfg` for reference, but the workflow no longer
  invokes it. Root cause of the warping is likely elsewhere (part geometry,
  bed adhesion / Z-offset, first-layer squish, ambient airflow), not the
  cooldown profile.

---

Macros for the Snapmaker U1 that pre-heat the printer for any print. A
conditional gradual post-print cooldown ramp was prototyped for high-temp
filaments (ASA / ABS / PA / PC / PET) but did not reduce warping in practice —
see "Status" above. The cooldown macro remains in `print_macros.cfg` but is
not invoked by the current workflow.

Built on top of garethky's `HEAT_SOAK` macro, which uses rate-of-change
detection (waits for the chamber temperature to stabilize, not a fixed time)
and supports cancellation mid-soak.

## Files

- **`heatsoak.cfg`** — `HEAT_SOAK`, `STOP_HEAT_SOAK`, `CANCEL_HEAT_SOAK`,
  `HEAT_SOAK_RESUME`, and an override of `RESUME`.
  Source: <https://github.com/garethky/klipper-voron2.4-config/blob/mainline/printer_data/config/heatsoak.cfg>

- **`print_macros.cfg`** — `PRINT_WARMUP` and `PRINT_START` for the U1.
  `PRINT_WARMUP` reads the filament list from the slicer, decides whether
  a soak is warranted, and either invokes `HEAT_SOAK` or proceeds normally.

## Installation

### 1. Enable Advanced Mode on the U1

On the printer's touchscreen: **Settings → Maintenance → Advanced Mode**.
Without this, the config directory is read-only and you can't save changes.

### 2. Back up your current `printer.cfg`

In Fluidd's Configuration Files panel, hover the `printer.cfg` row and click
**Download**. Save it somewhere safe on your laptop. Do this every time before
making changes.

### 3. Copy these two files to `/config/`

Upload `heatsoak.cfg` and `print_macros.cfg` into the same directory as
`printer.cfg` using Fluidd's file browser (drag-and-drop into the
Configuration Files panel works).

### 4. Add two include lines to `printer.cfg`

Find this line near the top of `printer.cfg`:

```ini
[include fluidd.cfg]
```

Add immediately after it:

```ini
[include heatsoak.cfg]
[include print_macros.cfg]
```

The order matters — `heatsoak.cfg` overrides the `RESUME` macro, so it must
load *after* `fluidd.cfg` (which provides the base `PAUSE`/`RESUME`/`CANCEL_PRINT`).

### 5. Save `printer.cfg`

Klipper will auto-restart (per your "Klipper Save & Restart action" setting).
Watch the console for any errors:

- **"Unknown config object"** → file path or include line is wrong
- **"redefined" warnings on `RESUME` or `PRINT_START`** → see Troubleshooting below
- **"Unable to parse"** → Jinja syntax issue, look at the indicated line number

### 6. Update the slicer

In SnOrca: edit your U1 printer profile → **Machine G-code** tab →
**Machine start G-code**. Add these two lines (or merge with existing
Snapmaker-specific start g-code):

```
PRINT_WARMUP EXTRUDER=[nozzle_temperature_initial_layer] BED=[bed_temperature_initial_layer_single] FILAMENTS="[filament_type]"
PRINT_START EXTRUDER=[nozzle_temperature_initial_layer] BED=[bed_temperature_initial_layer_single]
```

**Important**: copy the existing machine start g-code somewhere safe before
replacing it — SnOrca's default may include Snapmaker-specific setup
(NFC tag reads, filament loading, etc.) you don't want to lose.

## Verification

After Klipper restarts, run from Fluidd's console as a dry test:

```
PRINT_WARMUP FILAMENTS="ASA" EXTRUDER=270 BED=100
```

You should see:
1. `M117 Filaments: ASA` on the display
2. `M117 Heat-soaking for high-temp material`
3. Bed starts heating, homing happens
4. `HEAT_SOAK` engages, print state goes to "Paused"
5. Console prints `Heating -- 67.3C / 100.0C -- 0.5m elapsed` style messages
6. Once bed reaches target, console switches to `Soaking -- temp: 38.2C / 45C -- rate: 0.420C/m / 0.100C/m -- 44.5m remaining`
7. Cancel from Fluidd to verify the cancel path works → heaters off, paused state cleared

For the "no soak" path, run:

```
PRINT_WARMUP FILAMENTS="PLA" EXTRUDER=215 BED=60
```

Should heat bed to 60 and proceed without pausing.

## Tunable parameters in `print_macros.cfg`

In the `HEAT_SOAK` call inside `PRINT_WARMUP`:

- **`SOAK_TEMP=45`** — minimum chamber temperature before soak can complete.
  Realistic for U1's passive top cover. Increase if your room is warm and
  you regularly hit higher; decrease if you have a cold workshop and prefer
  shorter soaks.
- **`RATE=0.1`** — target rate of temperature change (°C/min). Soak completes
  when chamber rises slower than this. Tighter (e.g. 0.05) = longer, more
  thermally stable. Looser (e.g. 0.2) = shorter, less stable.
- **`RATE_SMOOTH=30`** — seconds of smoothing on the rate calculation.
  Reduces noise. Pair changes with `RATE`.
- **`TIMEOUT=45`** — maximum minutes to wait before aborting. Safety guardrail
  if equilibrium can't be reached (top cover off, room too cold, etc.).

To extend the high-temp filament list, add entries to the `high_temp` array
in `print_macros.cfg`. Names must match exactly what the slicer emits (use
`upper`-cased, semicolon-separated).

## Troubleshooting

**"Existing macro PRINT_START is being redefined"**
Something else (likely `fluidd.cfg` or a Snapmaker include) already defines
`PRINT_START`. Two options:
1. Rename our `PRINT_START` to `MY_PRINT_START` in `print_macros.cfg` and
   update the slicer's machine start g-code accordingly.
2. Find and remove/comment out the existing definition (less recommended,
   may break Snapmaker UI features).

**"Existing macro RESUME is being redefined"**
This is expected — `heatsoak.cfg` intentionally overrides `RESUME`. The warning
is informational. The override calls `HEAT_SOAK_RESUME` which falls through
to the original `RESUME` for non-soak cases.

**Soak runs forever, never proceeds**
Check that the cavity sensor is reading reasonable values in Fluidd's
Temperature panel. If the sensor reads 25 °C in a hot chamber, it's
disconnected or wrong. Cancel the soak, check physical connections, restart
Klipper, retry.

**Bed shuts off during soak**
Your `[idle_timeout]` block in `printer.cfg` should have
`timeout_on_pause: 9999999999` (the U1 stock config has this). If it doesn't,
add it. The pause-state timeout is what keeps the bed alive during the soak.

**`FILAMENTS=""` in injected g-code (placeholder not expanding)**
Some OrcaSlicer versions don't expand `[filament_type]` to a joined list in
machine start g-code. Workaround: use indexed placeholders manually:
```
PRINT_WARMUP ... FILAMENTS="[filament_type[0]];[filament_type[1]];[filament_type[2]];[filament_type[3]]"
```

## Notes on the U1 specifically

- Bed `max_temp` is 100 °C — the firmware will reject any attempt to set
  higher. Make sure your slicer ASA bed temp is ≤ 100.
- The cavity sensor is named `temperature_sensor cavity` (not `chamber`).
  This is what the `SOAKER=` parameter references.
- The top cover is *passive* — chamber temp is driven entirely by bed
  radiation. With a 100 °C bed, expect the cavity to settle around 45-55 °C
  in a normal room. Above that requires extraordinary conditions.
- Stock firmware will overwrite `printer.cfg` on OTA updates. Save these
  files locally and re-apply after each update. The Paxx12 community
  firmware has a `persistent/` includes path that survives updates if you
  want to escape this.

## Source / credits

- `HEAT_SOAK` macro: <https://github.com/garethky/klipper-voron2.4-config>
  (originally based on work by @blalor and @mwu in the Klipper forums).
- `PRINT_WARMUP` / `PRINT_START` and U1 integration: built for this setup.

If `heatsoak.cfg` in this package looks off, treat the GitHub source as
canonical and grab the raw file from there.
