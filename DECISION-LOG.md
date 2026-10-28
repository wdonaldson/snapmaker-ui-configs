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
- **Preset values must be JSON strings.** A hand-written `"support_filament": 0`
  is dropped on load ("invalid json type" in the app's log) with no warning in
  the UI (2026-10-26). Check the log after any hand edit.
- **Signing in to Orca Cloud switches OrcaSlicer's preset folder** from
  `user/default` to `user/<account id>`; files installed into the other folder
  are invisible (2026-10-26).

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

## 2026-10-16 — `M191` bed boost only for chamber targets above 50 °C

- **Trigger (retrospective):** the 09:39 PA test print (chamber still 60) had
  the bed at ~70 °C when the first layer went down and 65 °C when cancelled,
  for a 50 °C setting. No G-code wait was involved; the start G-code's
  heat-only wait passed at once. The bed simply coasted from 100 °C through
  the whole start routine. The owner judged the 2026-10-15 "boost to the end"
  decision wrong *for a 45 °C chamber*.
- **Data:** at a 45 °C target the boost ran only 4 min (bed reached 93 °C,
  Benchy 10:51) and saved perhaps 2–3 min: the bed needs 5 min just to reach
  100 °C, and the Panda Breath alone does 27 → 45 °C in ~8–10 min. At 60 °C
  the boost is still essential (18 vs 30 min).
- **Applied 2026-10-16 12:01 (printer idle):** `M191` boosts the bed to 100 °C
  only when `S > BOOST_ABOVE` (default 50, overridable per call). Below that
  the bed sits at the chamber target while the Panda Breath heats, and the
  start G-code then raises it to the filament's bed temperature. ASA (60)
  unchanged; PA (45) now gets a 50 °C bed at the first layer, ~2–3 min slower
  chamber heat-up.
- **Verified 2026-10-16 12:13 (PA first-layer test, warm start, chamber 37 →
  45):** no boost; `M191` done in 2.5 min; bed went 45 → 50 and was **exactly
  50 °C at the first layer** (12:19, ~6 min after start incl. flow cal + mesh);
  chamber held 44–45 °C by the auto hold through the print. Cold-start timing
  still to be measured.

## 2026-10-16 — Sunlu Easy PA: chamber 60 → 45, cooler nozzle, fan on, slower

- **Context:** PA prints at a 60 °C chamber showed heavy stringing, and the
  60 °C target was costing ~12 min of heating for a filament that only needs a
  closed chamber. Reviewed the profile against the Sunlu datasheet (nozzle
  250–270 °C at 50–100 mm/s, bed 30–50 °C with glue, retraction 0.8–1.2 mm,
  no fan/chamber guidance), a reviewer's real-world tuning (curling without
  fan; fixed with 25 mm/s, overhangs 15 mm/s, jerk 2, fan 40–60 %, 80 % on
  overhangs, dried at 70 °C) and U1 top-cover user reports (cover settles
  ~50 °C passively; tester targets 45–60 °C; PA12/PA6-CF printed fine with glue
  on large parts; no Easy PA profile for the U1 exists publicly).
- **Owner decisions:** heating macros unchanged; this is filament + process
  only. Chamber **45 °C** (the live file had been set to 40 by hand; 45 is
  where the cover naturally sits and makes a 50 °C bed reachable, since the bed
  floor is chamber + 4). Nozzle lowered **270/265 → 260/255** (stringing;
  250 remains in reserve). Jerk kept conservative: **6 default / 5 outer wall**
  (printer limit 8; reviewer's 2 in reserve).
- **Applied (filament `AI Sunlu Easy PA @ NoCooling`):** bed 50/50 (was 50/45;
  45 is unreachable in a 45 °C chamber), retraction 1.0 → 1.2 mm @ 35, fan
  0/0 → **20/50 %**, overhang/bridge fan 30 → **80 %**, fan off for first 3
  layers (was 5). The "NoCooling" name is now historical.
- **Applied (all three PA process presets):** outer/inner wall 40/50, sparse
  infill 80, solid infill 120, top surface 80, overhangs 25/25/15/15, bridge 20,
  travel 300, accel 3000 default / 2000 outer / 3000 inner / 5000 travel,
  jerk 6/5/6. Strength also carries the owner's walls 2 → 4 from the same day.
  Snapmaker Orca 2.4.0 stores speed fields as two-value lists (per nozzle-flow
  variant); the Strength file keeps that form.
- **Not changed:** max volumetric 10 mm³/s, walls/infill/shells, drying advice
  (70 °C is the safe spool-dryer value; datasheet 80–110 °C is for an oven).
- **Watch on the next PA print:** stringing and overhang curl. Second step if
  needed: nozzle 250, jerk 2–3, speeds 25.
- **Reverted copy of the pre-edit live files:** scratchpad `pa-backup/` (this
  session only); the repo's previous versions are in git.
- **Same day, Benchy test print:** the bow flexed as each layer went down. The
  sliced file showed the part fan at **0 % everywhere except overhang segments**
  (80 % bursts from a standing start). Cause: Orca applies the minimum fan speed
  on long layers **only when "Keep fan always on" (`reduce_fan_stop_start_freq`)
  is enabled**; it was off (inherited), and `fan_cooling_layer_time` was 4 s, so
  the 20–50 % range never engaged on ~13 s layers. This also means the original
  "NoCooling" profile had been fan-less by accident as much as by design.
  **Applied:** always-on **on**, fan cooling layer time 4 → **20 s** (owner
  rejected 30 as too aggressive; note this setting changes fan speed, not print
  time: `slow_down_layer_time` 2 s is what slows layers). Expected ~32 % fan on
  Benchy-type layers, 20 % on long ones, 80 % on overhangs. **Renamed the
  preset to `AI Sunlu Easy PA`** (file, `name`, `filament_settings_id`);
  Snapmaker Orca's remembered filament for that slot resets once.
  Second step if the bow still flexes: PA chamber 45 → 40, overhang tiers 15.

## 2026-10-16 — PA Benchy (first print on the new profile) — observations

- **Print:** `PA Draft`, `PA Sunlu Easy (ai)` before the fan fix (fan 0 % except
  80 % overhang bursts), chamber 45, nozzle 260/255, bed 50 (57 °C at first
  layer), travel 300, retraction 1.2 @ 35, z-hop 0.4. Photos in
  `~/3D-Printing/tools-utilities/Sunlu PA Tuning/Photos-1-001/`.
- **Seen:** (1) fine hair-like **stringing** everywhere inside the hull, across
  the arch and portholes, plus surface fuzz; (2) the **bow overhang rippled and
  sagged** (the "flexing" seen live): matches zero baseline fan; (3) **first
  layer poor**: beaded, gappy lines with blobs on the underside, despite the
  fresh 4×4 mesh and glue; (4) walls, roof, chimney and cabin fine.
- **Reading:** (2) should be addressed by the always-on fan fix applied the
  same day; verify. (1) is classic moisture in nylon as much as temperature:
  hair-fine strings and fuzz point at a spool that needs drying (70 °C, 8–12 h)
  before further temperature tuning; also `travel_speed` 300 (lowered today)
  gives more ooze time than the previous 500 — revert. (3) needs the
  first-layer test on the PA head (head 3) before any offset or flow change
  (standing directive); candidates are first-layer squish (0.25 mm first layer,
  0.5 mm line at 50 mm/s) or the glue layer.
- **Decided same day:** travel back to **500** in all four PA processes (applied,
  live + repo). Spool drying started 2026-10-16 (Polymaker dryer, max setting,
  12 h; 60 °C is the low end for nylon, 24 h would be closer to 70 °C overnight).
  No Benchy before the spool is dry: wet nylon sags on overhangs by itself and
  would mask the fan fix. First-layer check will use a compact one-layer model
  instead of a Benchy: `~/3D-Printing/tools-utilities/Sunlu PA Tuning/PA-first-layer-test.stl`
  (40 mm centre tile + four 20 mm corner tiles + bars, 0.25 mm = one first
  layer; generator `make_pa_first_layer_test.py` next to it, run with
  `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd`). Print it with
  `All Test First Layer @0.4 (ai)` and `PA Sunlu Easy (ai)` on head 3 tomorrow.
- **First-layer test result (same day, 12:13, spool still undried):** all five
  tiles and the bars adhered; lines fused and uniform on the centre tile and
  three corners, one corner slightly less squished (individual ridges visible,
  no gaps). Photos in `…/Sunlu PA Tuning/First Layer/`. Conclusion: head 3's
  Z/flow is fine; the Benchy's bad underside came from the **Draft preset's
  first layer** (0.25 mm at 50 mm/s, 0.5 mm line) and/or wet filament, not the
  probe offset. No offset change.
- **Applied:** all four PA processes now print the first layer at **30 mm/s**
  (infill 50) and **0.2 mm** (Draft was 0.25 at 50/105 mm/s), matching what the
  test printed well with. Verify on the next PA part's underside.

## 2026-10-16 — Preset naming scheme: `Filament Characterization @nozzle (ai)`

- **Problem:** with names starting `AI 0.20 …` the dropdowns did not group by
  material; the owner starts from the filament ("I'm printing ASA: draft,
  strength or compromise?") and rarely thinks about nozzle size, but wants it
  kept for a future nozzle change. Six presets had no `AI` prefix at all, and
  two `@ NoCooling` suffixes were no longer true (PA now 20–50 % fan).
- **Decision:** `<Filament> <Characterization> @<nozzle> (ai)` for processes,
  `<Filament> <Brand/Variant> (ai)` for filaments, `All` for filament-agnostic
  processes, `(ai)` lower-case, **no layer height** ("0.20 could mean too many
  things"; High Quality / Extra Draft imply theirs). Printer preset unchanged
  (filaments/processes declare compatibility against the printer name).
- **Applied** with Snapmaker Orca closed: 4 filaments + 13 processes renamed
  (file, `name`, `filament_settings_id` / `print_settings_id`), mirrored in
  `snapmaker-orca-rebased/`; `All Strength Fast @0.4 (ai)` (created in the app
  2026-10-15, never mirrored) added to the repo. `orcaslicer/` keeps the July
  originals under the old names. Snapmaker Orca forgets its last-selected
  presets once after the rename.
- **Noted, not changed:** `ABS Strength Slow` inherits the 0.16 mm system
  profile while printing 0.2 mm; `All Strength Fast` and `All Strength Support`
  overlap (outer wall 200 vs 60 mm/s) and may be merged later.
- **Pre-rename copy of the live folder:** scratchpad `rename-backup/` (this
  session only); the repo's previous files are in git.

## 2026-10-16 — "Standard" tier for ASA and PA

- **Need:** a preset for parts that just have to exist: not Draft (lightning
  infill is too flimsy), not Strength (time). Owner's words: elephant-foot
  compensation, support ironing, adaptive infill, 0.2 mm, "a blah setting".
  The owner's own `All Strength Fast` (2026-10-15) was a first attempt.
- **Applied:** `ASA Standard @0.4 (ai)` (from ASA Compromise) and
  `PA Standard @0.4 (ai)` (from PA Strength): 3 walls, 4/3 shells, 15 %
  adaptive cubic, no top ironing, elephant-foot 0.25 × 2 layers, tree-slim
  supports **in the same material** (Compromise's PETG-interface keys dropped,
  so no tool changes) with support ironing, scarf seam. Filament-specific
  speeds, accelerations and jerk carried from the base preset.
- **Expected:** ~30–40 % less time than Strength. Verify on the first real part.

## 2026-10-16 — PETG support interface becomes an explicit special case

- **Problem:** three of four ASA presets (Visual Quality, Compromise, Strength)
  silently routed the support interface to the PETG filament; Compromise even
  pointed at slot 4 while the others pointed at slot 1. The owner regards the
  PETG interface as a one-off that must be visible in the name.
- **Applied:** the PETG keys (`print_extruder_id`, `print_extruder_variant`,
  `support_filament`, `support_interface_filament`,
  `support_interface_not_for_body`) removed from Visual Quality, Compromise and
  Strength, so every plain ASA preset prints same-material tree supports.
  Two explicit variants added, both with interface on slot 1 and body on its
  own filament: `ASA Strength PETG Support @0.4 (ai)` and
  `ASA Visual Quality PETG Support @0.4 (ai)`. `ASA Test PETG Interface` kept
  as the test preset. Nothing else in the stripped presets changed.

## 2026-10-16 — ASA first-layer test (head 4) and M191 boost path

- `All Test First Layer @0.4 (ai)` + `ASA PolyLite (ai)` on head 4: **first layer
  perfect** (owner's verdict; no photos). No offset or first-layer change for
  the ASA presets (they stay at 50/105 mm/s; the PA retune to 30/50 was driven
  by the PA Benchy underside, not by ASA).
- **M191 boost path confirmed** at chamber 60: bed to 100 °C, chamber 42 → 60 °C
  in **11 min** from a warm start (cold-start figure remains 18 min); bed
  already at 100 °C at the first layer.
- **ASA Benchy (same day, `ASA PolyLite (ai)`, chamber 60, fan 0–15 %):** clean
  reference print. Bow and hull overhangs smooth and fused with no sag, crisp
  roof/chimney/arch, readable stern text, only a few hair-thin strings inside
  the hull. Photos in `~/3D-Printing/tools-utilities/Generic ASA Tuning/Benchy/`.
  Used as the benchmark for the dry-spool PA Benchy (bow smoothness, stringing).
  No preset change.

## 2026-10-21 — TPU presets (new; untested)

- **Need:** no TPU profile of our own; the generics worked in the past but
  struggled with overhangs and support removal. Loaded TPU is a **95A** on
  slot 4 (an earlier snapshot showed 90A).
- **Base:** `Snapmaker TPU 95A HF @U1 0.4 nozzle` (the 90A preset is a slow
  3.2 mm³/s profile; Generic TPU is 240 °C at 3.2 mm³/s). Brand/HF status of
  the spool unknown, so every number below is a starting point.
- **`TPU 95A (ai)`:** nozzle 230/225, fan 20–60 % with 100 % on overhangs,
  always-on, max volumetric 5 mm³/s (conservative vs the HF 9), retraction
  1.5 @ 30. Pressure advance and flow ratio left to the flow calibration.
- **`TPU Standard @0.4 (ai)`:** walls 25/35 mm/s, infill 40, overhangs
  15/15/10/10, bridge 15, accel 2000/1000, jerk 5/4, 3 walls, 15 % adaptive
  cubic, no supports. **`TPU Easy Supports @0.4 (ai)`**: same plus tree-slim
  supports with a 0.28 mm top gap, 0.6 mm XY gap, no interface layers, no
  support ironing, 40° threshold, for easier removal.
- **Test model:** `~/3D-Printing/tools-utilities/TPU Tuning/TPU-overhang-test.stl`
  (134 × 40 × 14 mm: overhang wedges at 30–70°, a 25 mm bridge, a 20 mm
  cantilever shelf; generator next to it). Print with `TPU Easy Supports` on
  slot 4, then judge overhang droop per angle, bridge sag and how the shelf
  supports release. Nudge nozzle/fan/gap from there.
- **First TPU print (2026-10-21, the owner's grommet, not the test model;
  spool not fully dry):** part good except the overhangs, which rippled and
  looked unsupported; support stringing ignored. G-code analysis: supports
  ended **two empty layers (0.4 mm)** below each overhang layer (Z 7.05 →
  7.65 and 18.05 → 18.65). Cause: `support_top_z_distance` 0.28 is rounded up
  to whole layers (2 × 0.2); the flexible bridge sags into a 0.4 mm gap.
  **Fix:** 0.28 → **0.2**. Also corrected my earlier note: a *larger*
  `support_threshold_angle` means *more* supports, so 40° → **30°** (does not
  affect flat overhangs). TPU still being dried. Retest after drying; next
  options if the overhang still droops: 1–2 interface layers, or a PLA
  interface from another head (TPU bonds poorly to PLA).
- **Support stringing on the same print (owner: don't care about it on the
  supports, but is it a symptom?):** most likely moisture (spool being dried).
  Evidence worth re-checking after drying: the head-4 flow calibration returned
  **PA 0.073**, below the firmware's own TPU 95A search floor (k_min 0.15, max
  0.45), which suggests a noisy measurement from wet filament; the preset's
  flow ratio 1.067 is inherited from Snapmaker's own spool and may over-extrude
  another brand; printer-level z-hop 0.4 applies to TPU (1,385 retractions on
  a tree-support part). No setting changed. After drying: reprint, check PA is
  inside 0.15–0.45, and only if still stringy try flow 1.0, nozzle 220, TPU
  z-hop 0.2, one at a time.

## 2026-10-21 — OrcaSlicer 2.5.0-alpha reviewed: still no U1 print options

- **Question:** does vanilla OrcaSlicer's new alpha (published 2026-10-16) give
  access to the post-Print "Print Preprocessing" step that carries Auto
  Leveling / Flow Calibration / Time-lapse for the U1?
- **Finding: no.** PRs #15196 and #15145 (U1 filament mapping + calibration
  options) are still open with merge conflicts; #15711 (Moonraker/Qidi/
  Snapmaker printer agents: camera, lamp, filament sync) is open and mergeable
  but has no leveling/flow options. No code for `SDCARD_PRINT_FILE_WITH_PARAMETERS`
  in `main`. The notes list only U1 profile items (High Flow nozzles, bed type
  selector, 100 °C cap, filament names) and Moonraker fixes; the new
  Upload & Print passes `print=true` in the upload, which is still a plain
  start (the mesh would be skipped).
- **Decision:** stay on Snapmaker Orca. Re-check when 2.5.0 reaches beta or
  stable, or when #15196 / #15145 merge.
- **Reminder:** the Print Preprocessing dialog opens with Auto Leveling and
  Flow Calibration **unticked** every time; tick them before Send.

## 2026-10-21 — TPU supports, round 2: threshold reverted upward; PLA interface variant

- **Re-print (28 min, a shorter 9.9 mm layout of the grommet):** where supports
  exist the 0.2 mm gap works (last support layer 7.25, overhang 7.65, one empty
  layer). One side had **no support** and sagged like the first print.
- **Cause: my threshold change.** I lowered `support_threshold_angle` 40 → 30
  and said it would not matter for flat overhangs; the part's overhang there is
  a short **sloped** wall (9.6 mm of overhang wall at Z 7.65), and slopes
  between 30° and 40° lost their supports. A larger threshold means more
  support. TPU sags on anything flatter than ~45–50° from horizontal.
- **Applied:** `TPU Easy Supports` threshold → **50°**.
- **New special case `TPU PLA Support @0.4 (ai)`:** research (Prusa/Bambu
  forums, Snapmaker's U1 guide, Sanladerer via Hackaday) says PLA releases
  from TPU while PETG welds to it (avoid) and ASA needs a 100 °C bed / 60 °C
  chamber that conflicts with TPU (avoid). Settings: snug **normal** supports
  (trees left whole edges uncovered), PLA interface 3 layers, spacing 0, gap
  0.2, threshold 50°, bulk support stays in TPU to keep tool changes to the
  interface layers (an all-PLA support would swap on nearly every layer).
  Interface filament is slot 1, so load PLA as filament 1.
- **Watch:** PLA interface on TPU columns may bond loosely (fallback: all-PLA
  support); and the plate temperature when PLA and TPU share a print (TPU
  35 °C vs PLA 65 °C): check the sliced G-code's bed temperature.

## 2026-10-21 — Jerk warning in Orca: my PA/TPU jerk settings were incomplete

- **Warning:** "The jerk setting exceeds the printer's maximum jerk
  (machine_max_jerk_x/y) … jump to travel_jerk." Printer max is 9; Orca's
  built-in defaults are travel 12, infill/top surface/first layer 9.
- **Cause:** jerk control is off unless a preset sets it (`default_jerk` 0), and
  then no check or `SQUARE_CORNER_VELOCITY` is emitted (the ASA/ABS/All presets
  fall back to printer.cfg's `square_corner_velocity: 8`). The seven presets I
  wrote (4 × PA, 3 × TPU) set only default/outer/inner jerk, which switches
  jerk on and leaves the other keys at Orca's defaults; Orca capped travel
  12 → 9. So the "conservative" jerk reached only the walls; infill, top
  surface, first layer and travel ran at 9, looser than the ASA presets' 8.
  No filament presets involved (jerk is a process setting).
- **Applied:** all jerk keys explicit. PA: default 6, outer 5, inner 6,
  infill 6, top surface 5, first layer 5, **travel 8**. TPU: 5 / 4 / 5 /
  infill 5, top 4, first layer 4, **travel 8**. Travel 8 matches printer.cfg
  and is below the printer's 9 cap, so the warning goes away.
- **Also noted:** the PLA interface under TPU printed "very good" (owner,
  2026-10-21). **Correction:** the version that printed was the owner's own
  edit in the app (saved 15:26), not my repo version: **tree-strong** supports
  (not snug normal), PLA interface = **filament 2** (not 1), prime tower **off**,
  50° threshold, 0.2 mm gap, 3 interface layers. The repo now mirrors that copy
  (jerk keys from the entry above included). Lesson: before editing a preset,
  diff the live app copy against the repo; my jerk script wrote to both files
  separately and its "live == repo" message was unconditional, so it hid this
  divergence. README no longer says "filament 1".

## 2026-10-22 — PA bow overhang: ragged/sagging after a thorough dry; test presets

- **Context:** PA Benchy (`PA Standard`, `PA Sunlu Easy (ai)`, nozzle 255, chamber 45,
  0.2 mm layers, supports off) still showed a rippled, drooping bow underside and
  drool lines on the sloped hull (owner photos, 2026-10-22). Spool dried 14 h at
  85 °C, 9 % RH when removed, so moisture is no longer the leading suspect. The
  gcode footer on the printer confirmed the always-on fan fix is active (part fan
  ~43 % on small layers, 80 % on overhangs), so "no fan" is ruled out too.
- **Levers considered (ranked):** (1) overhang fan 80 → 100 %, max fan 50 → 70 %;
  (2) nozzle 255 → 250 (the preset's own low limit); (3) cooler cooling air:
  chamber 35-40 °C or cover off (the fan blows 45-50 °C air at a polymer that is
  still soft there); (4) `slow_down_layer_time` 2 → 5 s; (5) layer height 0.2 →
  0.12-0.16; (6) PLA support interface under a problem overhang. Less likely:
  `thick_bridges` 0 + bridge flow 0.9 (bridges only), overhang reverse (curl, not sag).
- **Test model:** the TPU wedge ladder was rejected as repetitive and wasteful
  (~14.8 cm3, ~17 g PA). New `~/3D-Printing/tools-utilities/Sunlu PA Tuning/PA-overhang-test.stl`
  (generator `make_pa_overhang_test.py`): one 1.2 mm wall curving 0 → 70° off
  vertical (failure height = failure angle; ridges mark 30/45/60°) plus one 20 mm
  bridge; 1.2 cm3, ~1.4 g.
- **Created (user presets, live + repo):**
  - `PA Sunlu Easy Overhang Test (ai)` = PA Sunlu Easy with nozzle **250**
    (first layer unchanged at 260), fan max **70 %**, overhang fan **100 %**.
  - `PA Test Overhang @0.4 (ai)` = PA Standard with supports **off** (for the model above).
  - `PA High Resolution @0.4 (ai)` = PA Standard with layer height **0.12** and
    supports off (for a Benchy re-run; roughly +65 % print time).
- **How to use:** overhang model: `PA Sunlu Easy Overhang Test (ai)` + `PA Test
  Overhang`, one variable per print. Benchy: same filament + `PA High Resolution`.
  The Benchy run changes fan, nozzle and layer height together, so it says whether
  the combination works, not which part did it; the overhang model is the
  single-variable test.
- **Also:** `TPU Easy Supports @0.4 (ai)` in the app had been re-saved at 16:17 on
  2026-10-21 in Orca's delta form, losing the 50° threshold and the jerk keys from
  the 16:14 commit (it would have silently used the parent's threshold). Restored
  the full repo version to the app.
- **Not done:** the new presets were not test-sliced (the Orca CLI cannot resolve
  inherited user machine presets; "process not compatible with printer"); verify by
  loading them in the app and checking the preview. Result of the test prints: pending.
- **Status:** open. Next: chamber 35-40 / cover off if still soft; layer height as a
  PA quality tier only.

## 2026-10-22 — PA split into a dry baseline and "Wet" variants

- **Context:** the bow still sagged after a 14 h / 85 °C dry (9 % RH). The owner
  is nearly certain the cause is moisture all the same: the same filament printed
  a good Benchy before (the July profile, fresh spool), and the spool then sat in
  a bag for about 2 months without much care. If so, the October tuning
  (2026-10-16 entries) was compensating for a damp spool, not fixing the profile.
- **Decision:** keep that work, but label it for what it is.
  - **`PA Sunlu Easy (ai)` reset to a dry-spool baseline:** the July values
    (nozzle 265/270, retraction 1.0 @ 35, part fan 0 % as the datasheet says,
    overhang/bridge fan 30 %, always-on off, fan off for the first 5 layers).
    Kept from October because they are not moisture fixes: chamber **45 °C**,
    bed **50/50**.
  - **`PA Sunlu Easy Wet (ai)`** = the October profile, values unchanged (nozzle
    255/260, retraction 1.2, fan 20-50 % always on with cooling layer time 20 s,
    overhang fan 80 %).
  - **`PA Sunlu Easy Overhang Test (ai)` renamed `PA Sunlu Easy Wet Overhang Test
    (ai)`** (nozzle 250, fan 70 %, overhang fan 100 %). Not run yet.
  - Every PA process preset is unchanged (Draft / Standard / Strength / Strength
    Thin Walls / Test Overhang / High Resolution): none of them were moisture
    fixes, and they pair with either filament.
- **Naming:** not called `PA Generic (ai)`, because bed 50 only suits Easy PA;
  most other nylons want a 90-100 °C bed, so a generic label would mislead.
- **Unverified:** that the July profile made the good Benchy (owner's
  recollection; no photo or log here), and that the fan-0 baseline still holds
  overhangs at chamber 45 (July ran at chamber 60, with more trapped heat).
- **Confirm moisture before relying on either profile:** weigh the spool before
  and after drying (a damp 1 kg nylon spool can lose 10-20 g), or extrude 50 mm
  into the air at 265 °C (popping or frothy strands = water). Nylon re-absorbs
  within hours; dry 24 h+ and print straight from the dryer.
- Snapmaker Orca forgets the filament chosen for each slot once after a rename;
  reselect it.

## 2026-10-26 — Back to base OrcaSlicer: Set & Send, presets ported

- **Context:** the only reason to use Snapmaker Orca was the Print
  Preprocessing dialog (Auto Leveling / Flow Calibration / Time-lapse /
  filament mapping). LayerLab's free **Set & Send** v1.0.3 adds that dialog to
  OrcaSlicer: a post-processing script for 2.4.2 stable, or an Orca Cloud
  plugin for 2.5 alpha. It sends `SET_PRINT_EXTRUDER_MAP`,
  `SET_PRINT_USED_EXTRUDERS` and `SET_PRINT_PREFERENCES` over Moonraker before
  Orca uploads, the same commands as Snapmaker Orca. Upstream bug
  OrcaSlicer#16836 describes the same gap.
- **Code review (all 1,508 lines):** standard library only; talks only to the
  printer (`/printer/objects/query`, `/printer/gcode/script` on :80/:7125);
  refuses while printing or paused; writes `~/.set_and_send.json`,
  `~/.set_and_send.log` and the G-code. Its G-code edits are a no-op here: no
  `M190` in our start G-code (so no `WAIT_CHAMBER_TEMP`) and no top cover
  detected (so no `SET_PURIFIER_MODE`). Use `--no-chamber-wait` anyway so it
  never competes with the Panda Breath `M191`. Without Tkinter it sends saved
  choices silently, all **off** at first: use python.org Python (Homebrew's
  has no Tkinter). Zip SHA-256 `1e2ec7c8…67ed1b3`. Not run yet.
- **Presets ported** to OrcaSlicer 2.4.2 with
  `tools/rebase_presets.py --to-orcaslicer` (output `slicer-config/orcaslicer-rebased/`).
  2.4.2 packs its system profiles into `.opc` files, so the tool reads the
  v2.4.2 tag's JSON profiles and `PrintConfig.cpp` (option list and enum
  values) from a GitHub checkout. Every key OrcaSlicer knows resolves to the
  same value as in Snapmaker Orca. Left out: Snapmaker-only keys
  (`process_flow_support`, `filament_flow_support`,
  `filament_is_high_temperature`, `filament_retract_length_toolchange` …).
  The old OrcaSlicer presets are in `OrcaSlicer/user/default.backup-2026-10-26`.
- **Bug found:** both PETG-interface ASA presets stored `support_filament`,
  `support_interface_filament` and `support_interface_not_for_body` as JSON
  numbers since 2026-10-16. Both apps drop such keys, so **the PETG interface
  routing never applied** in Snapmaker Orca. The converter now writes strings.
  The Snapmaker Orca copies are still wrong.
- **Orca Cloud:** the owner chose to sync the presets to their Orca Cloud
  account. While signed in, OrcaSlicer reads `user/a3e1878a-…` (5 old July
  presets, including a stale July `HeatSoak` printer), not `user/default`.
  Route: sign in, then File → Import → Import Configs with the
  `orcaslicer-rebased` JSON files.
- **Still to do:** the HeatSoak printer preset (start G-code, `print_host`),
  Set & Send install, and a first test print checking `print_task_config`.

## 2026-10-27 — OrcaSlicer 2.5.0-alpha: TPU toolchange retraction restored

- **Context:** the owner runs OrcaSlicer 2.5.0-alpha (not 2.4.2), with Set &
  Send 1.0.4 as an Orca Cloud plugin, turned on in all 24 process presets
  (chamber wait off). A review of every preset against 2.5's new settings
  found one regression from the 2026-10-26 port.
- **Regression:** Snapmaker Orca's TPU 95A profile set
  `filament_retract_length_toolchange` 3.6 mm. 2.4.2 had no such key, so the
  port left it out and TPU fell back to the printer's 10 mm. 2.5 has the key
  again; **TPU 95A (ai)** now sets 3.6 mm. PETG was 10 mm in both, so no change.
  Edited on disk with Orca closed; backup in
  `OrcaSlicer/user_backup-tpu-toolchange-2026-10-27`.
- **Exclude objects** on in the HeatSoak printer preset (`exclude_object`),
  the only custom printer preset; the firmware has `EXCLUDE_OBJECT`. Lets one
  part be cancelled from Fluidd. Backup in
  `OrcaSlicer/user_backup-exclude-object-2026-10-27`.
- **Dropped: Combine sparse layers** on the PETG-support/interface presets.
  It only merges whole tower layers that fit under the nozzle's maximum layer
  height (U1 0.4: 0.32 mm). At 0.20 mm, two layers are 0.40 mm, so nothing
  merges; it would only act on presets at 0.16 mm or less.
- **Small support perimeters** (support paths no longer than 2π × threshold
  print slower): threshold 2.5 mm (paths up to ~16 mm, thin tree branches) on
  TPU Easy Supports, TPU PLA Support and 0.16 Strong Fine Supports. The TPU
  presets also get an absolute 25 mm/s (their outer-wall speed): the default
  50 % of the 150 mm/s support speed is 75 mm/s, above what TPU's 5 mm³/s
  volumetric limit already allows, so it would change nothing. Backup in
  `OrcaSlicer/user_backup-small-support-2026-10-27`.
- **Set & Send settings moved to the global plugin config.** Removed
  `print_plugin_config_overrides` from all 24 process presets; each keeps
  `slicing_pipeline_plugin` = U1 print setup (turning the plugin on is
  per-preset only). Chamber wait off now comes from
  `orca_plugins/config.json`, which already had it off. The per-preset copies
  (stale, from plugin 1.0.3) also hid the pop-up's remembered choices, which the
  plugin saves to the global config; the global config currently has Auto
  leveling and Flow calibration **on**, so the pop-up now opens with those
  ticked instead of off. Backup in
  `OrcaSlicer/user_backup-plugin-overrides-2026-10-27`.
- **Print unsupported walls last** on in PA Test Overhang
  (`unsupported_wall_last`, 2026-10-28): wall loops in mid air wait until the
  walls, infill or bridges that anchor them are printed. Needs
  `detect_overhang_wall`, which the U1 system profile already turns on. Copy to
  the PA presets only if the overhang test print improves. Backup in
  `OrcaSlicer/user_backup-unsupported-walls-2026-10-28`.
- **Next candidates (one at a time):** Cubic infill with multiline 2 against
  Gyroid on a copy of ASA Strength; Top surface expansion on outdoor parts.
  Skip: Wait for temperature on wipe tower (the U1's
  toolchange G-code already waits with `M109`), Orca adaptive PA (overrides
  per-head PA), Skip G-code config block (Set & Send reads that block).
- **To check:** the HeatSoak start G-code forces
  `SET_PRINT_AUTO_BED_LEVELING ENABLE=1` and `SET_TIME_LAPSE_CAMERA ENABLE=1`;
  verify they don't override the Set & Send pop-up choices.

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
  `M190`, and the Orca Cloud copy is from July. Port the Snapmaker Orca
  printer preset next (2026-10-26).
- Snapmaker Orca's two PETG-interface ASA presets still hold numeric
  `support_*` values that it ignores; fix there too if Snapmaker Orca stays in use.
- Nothing from October 2026 is committed yet (this file included).
