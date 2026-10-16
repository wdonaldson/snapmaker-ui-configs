# Decision log

Institutional memory for this printer setup: what was tried, what was abandoned
and why, and the directives that still apply. **Read this before changing
`printer.cfg`, `panda_breath.cfg`, the HeatSoak start G-code or the slicer
presets, and before any firmware update.** The final state of a file never
explains why it looks that way; this file does. Add an entry whenever something
is tried, reversed or decided, even if it did not work — especially then.

Format per entry: *Context → Tried → Result → Decision → Why → Status*.
Entries are chronological. Entries up to 2026-07-29 are reconstructed from the
git commit bodies and README history (the de-facto log at the time); October
2026 entries come from the work sessions and are not yet committed.

## Standing directives (from the owner)

- **Never change the printer while a print is running or paused.** Check
  `print_stats.state` first. Prepare locally; upload only when idle.
- **Step by step: make one change, confirm it, then the next.**
- **No printer-offset changes on a hunch.** Offsets only change after a test
  print with Auto Leveling on shows a need (2026-10-13, z_offset).
- SSH to the printer is the owner's job. Everything else goes through Moonraker
  (`http://192.168.4.50:7125`) or Fluidd (`http://192.168.4.50`).
- `printer-backups/` contains the serial number (`snapmaker/product_info.json`);
  committing it is the owner's call.
- Panda Breath prints always use the **HeatSoak** printer preset, never the
  stock one (2026-10-13, stock preset).
- Log decisions here, not only in commit messages or plan files.

## Things that bit us more than once (check before planning)

- **The U1 has no `sudo`; `/oem/.debug` needs `root`.** Documented in the README
  since 2026-07-02, yet the 2026-10-13 update plan assumed `sudo` and that
  `.debug` would survive the update. Both were wrong. Read the README's "Read
  This First" and "Panda Breath Setup" before any firmware or plugin work.
- **Two `[gcode_macro M191]` sections kill Klipper startup** ("Existing command
  'M191' not found in gcode_macro rename"). Only one definition may exist
  (2026-06-03). Re-running the plugin's `install.sh` regenerates
  `panda_breath.cfg` and re-introduces the plugin's M191.
- **The start G-code's homing order matters with flow calibration on**
  (2026-06-01 vs 2026-10-13). A fix that works with one slicer path can break
  with another, because OrcaSlicer prints never ran flow calibration.
- **Orca preset names must not contain `:`** (2026-07-29). Silent stale-copy
  saves.
- **Edit slicer preset files only with the app closed.** Both OrcaSlicer and
  Snapmaker Orca overwrite them from memory on exit (2026-10-02).

## Measured reference data

| Measurement | Value | Source |
|---|---|---|
| Chamber 25 → 55 °C, Panda Breath alone (no bed) | ~20 min | README, June 2026 |
| Chamber 25 → 55 °C, Panda Breath + bed 100 °C | ~5–8 min | README, June 2026 |
| Chamber 27 → 60 °C, bed 100 °C throughout | **18 min** | 2026-10-13 ASA |
| Chamber 37 → 60 °C (warm start), bed 100 °C | 15 min | 2026-10-13 ASA |
| Chamber 28 → 60 °C, bed 60 °C throughout | ~30 min | 2026-10-14 PA |
| Chamber 27 → 60 °C, bed 100 °C to 55 °C then 60 °C | 28 min (14.5 + 13.5) | 2026-10-15 ASA |
| Bed cooling, heater off, chamber held ~58 °C | ~⅔ of the gap to (chamber + 4) every ~5.5 min; 100 → ~70 °C in 6.5 min, → ~65 °C in 11 min | 2026-10-14/15 |
| Bed cooling, heater off, chamber *not* held (60 → 42 °C) | 95 → 70 / 60 / 50 °C in 9 / 17 / 29 min | 2026-10-13 |
| Bed floor with a 60 °C chamber | ~63–64 °C (chamber + 4–5) | 2026-10-14 PA |
| Start routine after `M191` (home, flow cal, clean, mesh) | ~10 min | 2026-10-14 |
| Bed 60 → 100 °C reheat (ASA after `M191`) | ~2.5 min | 2026-10-15 |
| Fresh 13×13 mesh after 2.0.0 calibration | range 0.55 mm, high at back right (+0.41) | 2026-10-13 |
| Fresh 5×5 mesh on 1.4.0 vs stale saved mesh | +0.17–0.44 mm (centre +0.19) vs ~0.02 | 2026-10-02 |
| Panda Breath 29 → 35 °C, chamber only, no bed | 2¼ min | 2026-10-13 |
| Head-1 Z ladder, 1.4.0, fresh mesh, z_offset −0.07 | best at −0.04 (BR tile) | 2026-10-02, not applied |

---

## 2026-05-09 — Baseline: garethky `HEAT_SOAK` + first `PRINT_WARMUP`

- **Context:** no chamber heater, passive top cover, ASA warping. Goal: a
  conditional heat soak before high-temp prints.
- **Decision:** garethky's `HEAT_SOAK` macro suite (`heatsoak.cfg`, unmodified
  baseline commit, then small edits) driven by a `PRINT_WARMUP` macro that reads
  the filament list from the slicer and soaks only for high-temp materials.
  Rate-of-change detection on the cavity sensor instead of a fixed timer.
- **Also decided then (`printer.cfg.patch.md`):** includes go right after
  `[include fluidd.cfg]` because `heatsoak.cfg` renames `RESUME` and
  `print_macros.cfg` references `HEAT_SOAK`. **Do not touch** `[heater_bed]`
  (`max_temp: 100` is the firmware limit), `[idle_timeout]`
  (`timeout_on_pause: 9999999999` keeps the bed alive during a paused soak),
  `[temperature_sensor cavity]`, `[fan_generic cavity_fan]`, or anything below
  the `SAVE_CONFIG` marker.
- **Same day:** cavity fan at 0.25 during soak, applied after `PAUSE`
  (otherwise the pause sequence turned it off). Per-tick "Heating --/Soaking --"
  console spam silenced by passing `*_REPORT_INTERVAL=99999`; start/end
  summaries still fire.
- **Status:** superseded 2026-06-01. `heatsoak.cfg` kept as reference; it is
  not included in `printer.cfg`.

## 2026-05-14 — Bed pinned to 100 °C during the soak

- **Tried before:** soak target = the slicer's bed temperature (90 °C for ASA).
- **Decision:** pin the soak bed target to 100 °C (the firmware maximum).
- **Why:** radiation scales with T⁴, so 100 vs 90 °C gives ~11 % more and a
  higher steady-state cavity temperature; with a passive cover every degree
  counts. The slicer's own `M140` drops the bed back to print temperature
  afterwards, in parallel with the cleaning routine, so `M190` waits little or
  not at all. (This assumption fails for low-bed filaments; see 2026-10-14.)
- **Also:** the Orca start G-code (`slicer-config/orca-machine-gcode.cfg`)
  versioned for the first time, with Snapmaker's stock homing order `G28 X Y`.

## 2026-06-01 — `G28 X Y` → full `G28` in the start G-code (reversed 2026-10-13)

- **Context:** `HEAT_SOAK` used `PAUSE`, which lost the Z-homed flag; prints
  failed with Snapmaker error 0003-0522-0002-0012 ("Tap Home first, then move
  the Z axis").
- **Decision:** full `G28` near the top, plus a defensive `G28 Z` after the
  feed / flow-calibration loop, which "appeared to un-home Z even after the
  earlier full home".
- **Status:** reversed. The `PAUSE` no longer exists (no `HEAT_SOAK`), and the
  full `G28` itself causes the same error once flow calibration actually runs.
  See 2026-10-13 "G28 back to X Y".

## 2026-06-01 — Panda Breath chamber heater; `PRINT_END_COOLDOWN` added

- **Decision:** real chamber heating via the `pandabreath-klipper` plugin
  (`[heater_generic panda_breath]`, WebSocket bridge to the BIQU Panda Breath at
  192.168.4.30). Orca's per-filament "Activate chamber temperature control"
  emits `M141`/`M191`, so the slicer drives the chamber; `heatsoak.cfg` became
  obsolete. `PRINT_WARMUP` collapsed from 50+ lines of filament gating to
  nozzle pre-warm + bed on + home + bed wait.
- **Added:** `PRINT_END_COOLDOWN`: ~4 h stepped bed/chamber ramp for
  ASA/ABS/PC/PA/PET, called from the end G-code *before* `PRINT_END` (stock
  `PRINT_END` turns the bed off). `_HIGH_TEMP_FILAMENTS` list extracted for it.
- **Persistence finding:** the plugin lives in `~/klipper/klippy/extras/`,
  outside `/oem/`; the U1 wipes that overlay on every boot unless `/oem/.debug`
  exists. README "Read This First" written for this.

## 2026-06-03 — `PRINT_END_COOLDOWN` disabled; one `M191` only

- **Tried:** the cooldown ramp on real ASA prints (50 min at 100 °C bed /
  60 °C chamber, walking down through the Tg zone).
- **Result:** no measurable reduction in warping.
- **Decision:** end-G-code call commented out; macro kept in `print_macros.cfg`
  for reference. Warping assumed to come from elsewhere (geometry, adhesion,
  Z offset, first-layer squish, airflow). (Oct 2026: the first-layer squish
  turned out to be the stale-mesh problem, 2026-10-02.)
- **M191 ownership:** our bed-assist `M191` (plugin logic verbatim plus
  `M140 S100` at the top) was first written with `rename_existing`. Two
  `[gcode_macro M191]` sections (plugin's in `panda_breath.cfg` + ours) silently
  merge and Klipper halts at startup. Fix: remove the plugin's block; ours in
  `print_macros.cfg` is the sole definition. `panda_breath.cfg` and `printer.cfg`
  versioned as the on-printer baseline.

## 2026-07-02 — Panda Breath setup guide (README)

- **Findings recorded:** `/oem/.debug` needs `root`; the U1 root shell has **no
  `sudo`**. Klipper runs as `lava`; everything else as `lava`. Use the Panda
  Breath's **IP, not `PandaBreath.local`** (mDNS does not resolve on the U1; a
  hostname given to `install.sh` is written into `panda_breath.cfg` and must be
  replaced). `--no-bind` plus `panda_breath_cli.py bind-klipper` later works.

## 2026-07-03 — "Quick setup post firmware": `M191` moved into `panda_breath.cfg`

- **Context:** the owner wanted a repeatable procedure for after a firmware or
  plugin update, when `install.sh` regenerates `panda_breath.cfg`.
- **Decision:** the bed-assist `M191` moved from `print_macros.cfg` into
  `panda_breath.cfg`, so one file holds the whole Panda Breath config. README
  step "3. Patch the M191 macro with bed-assist": **don't blindly replace
  `panda_breath.cfg`** after a plugin update (a new release may add sections);
  fetch the live `M191` via Moonraker, check for `M140 S100`, add the two lines
  only if missing, restart via `POST /printer/restart`.
- **README "Notes on the U1":** stock firmware overwrites `printer.cfg` on OTA
  updates; keep these files locally and re-apply. The Paxx12 community firmware's
  `persistent/` include path was noted as an escape hatch, **considered, not
  adopted**.
- **Status (Oct 2026):** the README step still describes the 100 °C-throughout
  `M191`; the macro has since changed (2026-10-14/15). Rewrite pending.

## 2026-07-29 — OrcaSlicer presets versioned; naming rule

- **Decision:** custom presets prefixed `AI ` (space), **never `AI:`**.
  OrcaSlicer silently rejects `:` in preset names and can revert to a stale
  in-memory copy with no error; that caused a real Strength-profile regression
  (PETG-interface overrides dropped, fixed from a backup). 0.16 mm process
  tiers removed to keep one layer height while PETG-interface tuning was in
  progress. Sync direction: OrcaSlicer is the source of truth while editing;
  copy live → repo after intentional changes.

## 2026-10-02 — Root cause of poor first layers on heads 2 and 4

- **Context:** rippled/beaded first layers on heads 2 and 4 (T1/T3 in Klipper).
- **Tried:** Printables "Perfect First Layer Test" per head, labelled 40 mm
  tiles (FreeCAD script), a Z-ladder G-code post-processor that applies a
  different `SET_GCODE_OFFSET` per tile (`first-layer-test/`), a live-trim reader.
- **Misread, then corrected:** the beaded, translucent-webbed lines were first
  judged "nozzle too high". The ladder showed the opposite: **0.2–0.4 mm too
  close**. Cause: OrcaSlicer's "Upload and Print" sends a plain
  `SDCARD_PRINT_FILE`; the firmware's `print_task_config` gate then skips
  `BED_MESH_CALIBRATE` ("configuration does not do auto-leveling") and a
  **stale saved mesh** (re-zeroed at homing) is reused. Only the touchscreen /
  Snapmaker app path (`SDCARD_PRINT_FILE_WITH_PARAMETERS`) passes `BED_LEVEL`,
  `FLOW_CALIBRATE`, `TIME_LAPSE_CAMERA`; `reset_print_info` clears them after
  every print. `SET_PRINT_AUTO_BED_LEVELING` in the start G-code is unknown on
  1.4.0; `SET_PRINT_PREFERENCES` refuses to run during a print.
- **Abandoned:** vanilla OrcaSlicer for U1 prints. Upstream PRs #15196, #15145
  (merge conflicts) and #15711 for the U1 print-options panel are unmerged; no
  nightly or community build has it; clearing the print host makes the Print
  button do nothing; there is no "Print plate" option. Also abandoned: forcing
  the options from the start G-code (paxx12 Extended Firmware can force bed
  mesh/timelapse by wrapping the macros with `SET_PRINT_PREFERENCES … FORCE=1`,
  but not flow calibration; not installed).
- **Decision:** send from **Snapmaker Orca 2.4.0**: Print → "Send G-code to
  printer host" → **Upload and Print** → "Print Preprocessing" dialog (printer,
  filament→head mapping, Flow Calibration / Timelapse / Auto Leveling). If the
  U1 is missing from the dropdown, close and reopen it (Snapmaker Orca #854).
  Snapmaker Orca is an AGPL fork; it does not have to upstream, and its device
  UI is a compiled Flutter app, so this is not portable to OrcaSlicer.
- **Result:** a fresh mesh fixed most of the first-layer problem on head 1.
  The ladder then preferred −0.04 mm more (BR tile). Recorded in
  `first-layer-test/README.md`; **not applied** (see 2026-10-13, z_offset).

## 2026-10-02 — Preset migration OrcaSlicer → Snapmaker Orca

- **Problem:** Snapmaker Orca 2.4.0 renamed its system profiles ("0.20
  Strength/Standard/Quality" → "0.20mm Standard", "Snapmaker PETG @U1" →
  "Generic PETG", no "0.20 Quality"); straight copies of the user presets
  inherit different parents and so different effective settings. The HeatSoak
  printer preset saved in Snapmaker Orca on Oct 2 22:11 was broken: *before
  layer change* held the whole start G-code and *layer change* held `PRINT_END`
  (would have run both at every layer). It was never used for a print.
- **Decision:** `slicer-config/tools/rebase_presets.py` resolves each preset
  against the OrcaSlicer system profiles it was written for, maps it to the new
  parent, and pins every key whose value differs. Output in
  `slicer-config/snapmaker-orca-rebased/` with `REPORT.txt`. Eight keys cannot
  carry over (bed-mesh bounds, resonance-avoidance settings, `printer_agent`,
  `print_host`): they do not exist in Snapmaker Orca or are replaced by its
  Device tab. `print_host` is deliberately dropped: with a host set, Print falls
  back to the plain upload dialog without the options.
- **Installed 2026-10-13** with the app closed; the previous folder is
  `~/Library/Application Support/Snapmaker_Orca/user/default.backup-2026-10-13`.
- **Caveat:** re-running the script regenerates the start G-code from the
  **OrcaSlicer** preset, which still has `PRINT_WARMUP`, full `G28` and `M190`.
  Edit that preset first or hand-edit after regenerating.
- **Gotchas:** custom filaments vanish from the dropdowns when the **0.2
  nozzle** printer is selected (their `compatible_printers` is the 0.4-nozzle
  U1 only). G-code fields are stored with `\n` escapes in the JSON; that is
  normal, not corruption. "Support controlling chamber temperature" is hidden
  in the 2.4.0 UI but still works from the preset.

## 2026-10-13 — Firmware 1.4.0 → 2.0.0

- **Release-note review (1.5.0, 1.5.1, 1.5.2, 2.0.0; no notes for 1.6.0; 2.0
  source unpublished, `Snapmaker/u1-klipper` stops at 1.6.0):** stock firmware
  never defines `M141`/`M191`, so no clash with the plugin. 1.6.0's `heaters.py`
  change is compatible with the plugin's `get_mcu()`. 1.5.0 introduced, and
  1.5.1/1.5.2 fixed, an over-squished first layer without leveling. 1.5.2
  requires re-running multi-toolhead calibration **without filament loaded**.
- **What the update actually did:** wiped `/oem/.debug`, the plugin file and
  the SSH host key (all outside `/oem/`); replaced `printer.cfg` (our includes
  and `z_offset` gone; new accelerometer auto-detect, `cycle_time`,
  `power_loss_trigger_time` kept). `panda_breath.cfg`, `heat_soak/` and the
  calibration JSONs survived (inside `/oem/`). Clear the old host key with
  `ssh-keygen -R 192.168.4.50`. The plan had predicted none of the wipes.
- **Plugin reinstall:** only `panda_breath.py` copied (`ssh lava … 'cat >
  ~/klipper/klippy/extras/panda_breath.py' < panda_breath.py`), then `touch
  /oem/.debug` as `root` and reboot. `install.sh` was **not** run: it would
  regenerate `panda_breath.cfg` (dropping our `M191`) and the binding lives on
  the Panda Breath itself. Verified: heater 29 → 35 °C in 2¼ min, off on target 0.
- **z_offset:** the plan said restore −0.07 and later apply the ladder's
  −0.03. **Owner decision: keep the factory −0.05.** The 1.4.0 symptoms came
  from the skipped mesh, not the probe offset, and the ladder was measured on a
  different firmware and offset. Offsets change only if a per-head test with
  leveling on shows a need.
- **Calibration after the update (no filament, clean nozzles):** head 2 moved
  **X −0.21 / Y +0.49 mm** relative to head 1; heads 3 and 4 ≤ 0.05 mm, head 1's
  own Z −0.03 (probe-code shift). Which head-2 value is right is unverified.
  Input shaper 47.8 → 51.8 Hz; new 13×13 mesh. Head-3 pressure advance **0.25**
  (10× the others) persisted; head 1 0.025 → 0.02.
- **Backups:** `printer-backups/2026-10-13_fw-1.4.0/`, `…_fw-2.0.0-stock/`
  (the untouched 2.0.0 `printer.cfg`), `…_fw-2.0.0-calibrated/`.
- **Considered, not taken:** paxx12 Extended Firmware (web-UI Panda Breath
  setup, no SSH; warns the RK3562 throttles at 85 °C with a chamber heater).

## 2026-10-13 — Stock printer preset vs HeatSoak

- Stock start G-code runs the top-cover purifier logic (`SET_PURIFIER_MODE`:
  mode 3 keep-warm 45 °C, or mode 1 exhaust with a **45 °C alarm that pauses
  the print**), `WAIT_CHAMBER_TEMP TIMEOUT=180`, and `Z_OFFSET −0.07` for the
  High Temp / Graphic Effect / Smooth PEI plates (not Textured PEI). None of it
  belongs in a 60 °C Panda Breath print. **Always HeatSoak.** Two early
  Snapmaker Orca test prints accidentally used the stock preset.

## 2026-10-13 — `PRINT_WARMUP` retired; stock `PRINT_START` restored

- **Finding:** `print_macros.cfg` redefined `PRINT_START` (a macro nothing
  called) and so hid the stock one in `fluidd.cfg`, which re-applies each
  head's calibrated pressure advance (`FLOW_APPLY_CALIBRATE_K`), resets `M220`
  and some auto-feed state. A filament preset that sets its own PA (PETG 0.03)
  left that head on it until reboot. `PRINT_WARMUP` only duplicated what the
  start G-code does later (`M140`, `G28`, `M190`); `PRINT_END_COOLDOWN` was
  already dead; chamber heat comes from the filament's `M191`.
- **Decision:** start G-code line `PRINT_WARMUP …` → stock `PRINT_START`;
  `[include heat_soak/print_macros.cfg]` removed from `printer.cfg` (file kept
  on the printer and in the repo). Slicer first, printer second, so no job ever
  calls a macro that no longer exists (Klipper only warns "Unknown command",
  but warm-up would be skipped). The README "Installation" steps (`heatsoak.cfg`,
  `print_macros.cfg`, include order) are now historical.

## 2026-10-13 — `G28` back to `G28 X Y` (reversal of 2026-06-01)

- **Trigger:** the first Snapmaker Orca print with Flow Calibration on paused
  with 0003-0522-0002-0012 ("Must home Z axis first") during head 2's flow
  calibration, before the defensive `G28 Z` could run.
- **Why the June fix never showed this:** OrcaSlicer prints had the options
  skipped, so `SM_PRINT_FLOW_CALIBRATE` was a no-op for every print since June.
- **Mechanism (unconfirmed; 2.0 source unpublished):** homing Z activates the
  saved mesh; the flow-calibration routine un-homes Z; the next XY move then
  carries a mesh Z correction (0.0125 mm) and Klipper refuses it. Snapmaker's
  own order (XY only, Z after the loop) never has the mesh active there.
- **Decision:** stock homing order; keep the defensive `G28 Z` after the loop
  (and `G28 Z I140 J140`, final `G28 Z`). The reasoning is now in the start
  G-code comments. Verified: the same cube printed with flow calibration on.

## 2026-10-14 → 10-15 — Chamber heating vs bed for low-bed filaments (PA)

- **Problem:** Sunlu Easy PA: bed 50/45 °C, chamber 60 °C. `M191` pushed the
  bed to 100 °C; the start G-code's `M190 S50` then waited for the bed to
  *cool*, which it cannot do below chamber + 4 °C. Long dead wait before every
  PA print. The 2026-05-14 assumption ("M190 waits briefly or not at all")
  only holds when the print bed temperature is above the chamber temperature.
- **Also found:** after reaching temperature, `M191` hands the hold to the
  Panda Breath's native auto mode with `HOTBEDTEMP=80` (device heats only
  while the bed ≥ 80 °C), so the chamber was **not held** during PA prints.
  Orca emits `M191 S60` as the very first G-code line, before the start G-code,
  carrying only the chamber value. `print_task_config` has filament types but
  no temperatures.
- **Step 1 (slicer, kept):** `M190 S{bed}` → `M140 S{bed}` +
  `TEMPERATURE_WAIT SENSOR=heater_bed MINIMUM={bed − 1}`: wait to heat, never
  to cool. Had to go in before any `M191` change, or PA would hang at `M190`.
- **Step 2 (kept):** `HOTBEDTEMP` default 80 → **30** in `M141` and `M191`.
  Verified 2026-10-14: chamber held 58–60 °C through a 27-layer PA print;
  `M141 S0` at the end switched auto mode off.
- **v1 (tried 2026-10-14, abandoned):** bed = chamber target (60 °C) for the
  whole `M191` wait, no 100 °C boost. Result: 28 → 60 °C in **~30 min** vs
  18 min with the boost. Bed settled at ~63 °C. Too slow.
- **v2 "hybrid" (tried 2026-10-15, abandoned):** boost to 100 °C until the
  chamber reaches target − `MARGIN` (5), then bed = target. Result, ASA cold
  start: 27 → 55 °C in 14.5 min, then 55 → 60 took **13.5 min** (the last
  degrees depend on bed radiation; the Panda Breath alone crawls near its
  60 °C ceiling). 28 min total: no gain. The bed did fall 100 → 64 °C meanwhile.
- **Rejected without trying:** (a) "bed = higher of filament bed / chamber"
  rule: `M191` does not know the filament bed temperature; it would need the
  start G-code to call `M191 … BED=` itself and a check that Snapmaker Orca then
  drops its own `M191`; (b) switch at ~55 °C to the filament bed temperature:
  costs ~10 min of chamber time for a 2–5 °C cooler PA bed; (c) a fixed
  10-minute boost timer (the original idea): does not adapt to warm starts.
- **v3 (applied 2026-10-15 15:40, after the ASA print finished):** `MARGIN`
  default **0**: boost at 100 °C all the way to the chamber target, then set the
  bed to the chamber target. The start G-code immediately sets the filament's
  own bed temperature next (ASA → 100 °C again, ~2.5 min overlapping the start
  routine; PA → coasts down during the ~10 min start routine to ~65–68 °C,
  above its 50 °C setting anyway because of the chamber). Expected chamber time
  ~18 min. `MARGIN=` is still accepted per call.
- **Owner's framing of the rule:** heat with the bed at 100 °C; when the
  chamber is at target, set the bed to the filament's print temperature from
  the profile. ASA unaffected; PA gets the start routine to cool. Optional:
  set PA's profile bed temperature to 60 °C so the profile matches what
  physically happens (does not change timing).
- **Unexplained:** 2026-10-14 16:45:50 the bed target became 80 °C for 2.5 min
  during `M191`; nothing in our macros sets 80. Fluidd connected from
  192.168.4.23 nine seconds earlier. Suspects: a manual set, or the Panda
  Breath's stored `hotbedtemp` 80. Watch for a repeat.

## Open items

- Verify v3 timing on the next cold-start ASA/PA print (`klippy.log` Stats
  lines carry bed/cavity/panda_breath every 2 s; local = UTC − 4).
- Head-3 pressure advance 0.25 outlier: recalibrate if the next flow-cal print
  does not change it.
- Head-2 XY offset moved ~0.5 mm at the 2.0.0 calibration: alignment print.
- Per-head first-layer tests on 2.0.0 with Auto Leveling on (heads 2 and 4
  first); only then consider any Z change.
- The 80 °C bed event.
- README: "Installation" (heatsoak/print_macros) and "Panda Breath Setup → 3.
  Patch the M191 macro" are stale; rewrite against the current `M191`.
- OrcaSlicer's own HeatSoak preset still has `PRINT_WARMUP`, full `G28` and
  `M190`; only Snapmaker Orca is used for the U1 now. Update or retire.
- Nothing from October 2026 is committed yet (this file included).
