# U1 firmware update 1.4.0 → 2.0.0: plan and checklist

Status: **updated to 2.0.0; steps 2–3 done** (2026-10-13).
Decisions and findings from this update are logged in [`DECISION-LOG.md`](DECISION-LOG.md). Step 1 was skipped: the
update itself wiped `/oem/.debug`, the plugin and the SSH host key.

Nothing here changes the printer until you work through it yourself. Steps
marked *(root)* need SSH as `root`; the rest use the touchscreen, Fluidd
(<http://192.168.4.50>) or this repo.

## 0. Already done (read-only)

- [x] Full backup of the printer's config folder (59 files) in
      [`printer-backups/2026-10-13_fw-1.4.0/`](printer-backups/2026-10-13_fw-1.4.0/).
      This includes the per-head calibration files: Z/XY offsets
      (`snapmaker/extruder_base_position.json`), flow-calibration factors
      (`snapmaker/flow_calibrator.json`), bed mesh and PID values. Not committed;
      `snapmaker/product_info.json` contains the printer serial number.
- [x] Repo `printer.cfg`, `panda_breath.cfg` and `print_macros.cfg` match the
      printer exactly.
- [x] `pandabreath-klipper` checkout is current (upstream has one unrelated
      commit since).

Values to re-check after the update (from the backup):

| Setting | Value on 1.4.0 |
|---|---|
| Head 1 probe `[inductance_coil extruder] z_offset` | **-0.07** (factory -0.05) |
| Head Z offsets vs head 1 (`extruder_offset` Z) | head 2 +0.146, head 3 +0.198, head 4 +0.076 |
| Pressure advance (flow cal) | 0.02 / 0.025 / **0.25** / 0.02 |
| `printer.cfg` includes at the end | `[include panda_breath.cfg]`, `[include heat_soak/print_macros.cfg]` |

## Release-note review (1.4.0 → 2.0.0)

The latest Snapmaker firmware is **V2.0.0 (2026-09-14)**. Its source isn't on
GitHub yet; `Snapmaker/u1-klipper` stops at 1.6.0. Reviewed: release notes for
1.5.0, 1.5.1, 1.5.2 and 2.0.0 (none published for 1.6.0), plus the 1.4.0 → 1.6.0
source diff.

**Panda Breath: no conflict found.**
- Stock firmware never defines `M141`/`M191`, so the plugin's macros don't clash.
  Stock chamber logic is separate: the top-cover **purifier** module
  (`SET_PURIFIER_MODE`, `WAIT_CHAMBER_TEMP`), added with Top Cover support in
  1.5.0 and reworked in 1.6.0. The 2.0 fix "device still waited for the chamber
  to heat up when the top cover was in exhaust mode" is in that logic.
- Only Snapmaker's **stock** printer start G-code calls the purifier logic.
  Depending on a cooling mode Snapmaker Orca computes, it sets mode 3 "keep warm"
  (inner fan, 45 °C), mode 1 "strong cooling" (exhaust fan, desired 42 °C,
  **alarm 45 °C, which pauses the print**) or mode 3 with no target. It then runs
  `WAIT_CHAMBER_TEMP TIMEOUT=180`. The **HeatSoak** start G-code calls none of
  this, so **always use the HeatSoak printer preset for Panda Breath prints**. A
  60 °C chamber under the stock preset could hit that 45 °C alarm or have the
  exhaust fan fight the heater.
- 1.6.0's `heaters.py` change (PWM scheduling via `get_mcu().estimated_print_time`)
  is compatible: the plugin's `PandaBreathVirtualPin.get_mcu()` returns the main
  MCU. 2.0's Klipper changes can't be checked until its source is published, so
  the verification in step 4 still matters.

**Relevant to the first-layer work:**
- 1.5.0 introduced, and 1.5.1/1.5.2 fixed, "the first layer was overly squished
  when Heated Bed Leveling was not enabled before printing" (not present in 1.4.0).
- 1.5.2 lists **required post-install steps**: multi-toolhead offset calibration
  **without filament loaded**, and Heated Bed Leveling enabled before printing.
  Both are now in step 4.
- Stock start G-code applies `Z_OFFSET -0.07` at homing and meshing for the High
  Temp, Graphic Effect and Smooth PEI plates, but not Textured PEI. The HeatSoak
  start G-code never does, which is fine for the textured plate in use.

## 1. Before updating

- [ ] No print running; printer idle.
- [ ] *(root, recommended)* Start from a clean system overlay, so files from
      1.4.0 can't shadow the new firmware's. The Panda Breath plugin
      (`~/klipper/klippy/extras/panda_breath.py`) only survives because
      `/oem/.debug` is set. See README "Read This First".
      ```sh
      ssh root@192.168.4.50
      rm /oem/.debug && reboot      # overlay is wiped on this boot
      ```
      Klipper will then fail to load `[panda_breath]`. That's expected until
      step 3.

## 2. Update

- [x] Update firmware from the touchscreen (Settings → firmware update) to 2.0.0.
- [x] After reboot, check the touchscreen and Fluidd show 2.0.0 (`2.0.0.205_20260914173503`).

## 3. Restore our configuration

- [x] Compare the new `printer.cfg` with the backup **before** editing it. The
      update may replace it (README: "Stock firmware will overwrite printer.cfg
      on OTA updates"), and 2.0.0 may add new sections that must be kept:
      ```sh
      curl -s http://192.168.4.50:7125/server/files/config/printer.cfg -o /tmp/printer-2.0.0.cfg
      diff printer-backups/2026-10-13_fw-1.4.0/printer.cfg /tmp/printer-2.0.0.cfg
      ```
- [x] Re-apply only our deltas onto the 2.0.0 file (stock 2.0.0 file saved in
      `printer-backups/2026-10-13_fw-2.0.0-stock/`):
  - `[include panda_breath.cfg]` and `[include heat_soak/print_macros.cfg]` at the end
  - ~~`[inductance_coil extruder] z_offset`~~ **Decided 2026-10-13: keep 2.0.0's
    factory -0.05.** The 1.4.0 offset problems came from printing without
    per-print bed leveling, not from the probe offset.
- [x] *(root)* Re-enable persistence: `touch /oem/.debug && reboot`. 2.0.0 has
      no `sudo`, so log in as `root`. Clear the old SSH host key first
      (`ssh-keygen -R 192.168.4.50`); the update regenerates it.
- [x] Reinstall the Panda Breath plugin from source. **Done without `install.sh`:**
      only `panda_breath.py` was copied (`ssh lava@… 'cat > ~/klipper/klippy/extras/panda_breath.py' < panda_breath.py`),
      because our `panda_breath.cfg` survived and the binding lives on the Panda Breath.
      Original install notes:
      [justinh-rahb/pandabreath-klipper](https://github.com/justinh-rahb/pandabreath-klipper).
      It provides two things:
  - `panda_breath.py`, the Klipper module copied into `~/klipper/klippy/extras/`
    (outside `/oem/`, which is why `/oem/.debug` must be on);
  - `panda_breath.cfg`, **generated** by `install.sh` from the templates in its
    `config/` folder (`panda_breath.stock.cfg` + `panda_breath.heater.cfg` +
    `panda_breath.macros.cfg`, with your Panda Breath IP filled in).

  The printer has no git or update manager, so the source is pulled on the Mac
  and copied over. The local checkout at `~/3D-Printing/Snapmaker-U1/pandabreath-klipper`
  is one commit behind upstream; that commit (2026-07-18) only retires the
  `klipper-firmware/` folder and doesn't touch the plugin or installer.
  ```sh
  cd ~/3D-Printing/Snapmaker-U1/pandabreath-klipper && git pull --ff-only
  cd .. && scp -r pandabreath-klipper lava@192.168.4.50:~/
  ssh lava@192.168.4.50 'cd ~/pandabreath-klipper && ./install.sh --host 192.168.4.30 --printer-ip 192.168.4.50 --no-include'
  ```
  `--no-include` because we add the include to `printer.cfg` ourselves above.
  Leave binding on (no `--no-bind`): it points the Panda Breath back at this
  Klipper host, which is what we want after a reinstall.
- [x] **Restore this repo's `panda_breath.cfg`** (not needed: it survived the update) over the one the installer
      generates. The installer writes its own template (keeping a `.bak`) and
      **drops our M191 bed-assist** (`M140 S100` during chamber pre-heat).
- [x] Restart Klipper; confirm no config errors in Fluidd. Plugin connected, 29 °C.

## 4. Verify

- [x] `SET_HEATER_TEMPERATURE HEATER=panda_breath TARGET=35` works (29 → 35 °C in ~2¼ min), then set 0 (heater off).
- [x] `heater_generic panda_breath` and `temperature_sensor cavity` report sane temperatures (29 °C / 28 °C).
- [x] **Re-run the multi-toolhead (nozzle offset) calibration with no filament
      loaded** and clean nozzles (done 2026-10-13 16:16; the touchscreen routine also
      redid input shaping, 47.8 → 51.8 Hz, and a 13×13 bed mesh). Full backup after
      calibration: `printer-backups/2026-10-13_fw-2.0.0-calibrated/`.
      Offsets relative to head 1 (mm), 1.4.0 → 2.0.0:

      | Head | X | Y | Z |
      |---|---|---|---|
      | 2 | +0.067 → −0.142 (**−0.21**) | +0.578 → +1.071 (**+0.49**) | +0.146 → +0.100 (−0.05) |
      | 3 | +0.039 → +0.028 | +1.233 → +1.202 | +0.198 → +0.165 (−0.03) |
      | 4 | −0.132 → −0.151 | +0.492 → +0.458 | +0.076 → +0.045 (−0.03) |

      Head 1's own base Z also moved −0.03. **Head 2's XY moved ~0.5 mm**; check it
      with a multi-head alignment print before trusting either value.
- [x] Compare `flow_calibrator.json` with the backup: head 1 0.025 → 0.02, others unchanged.
- [ ] Check the head-3 pressure advance outlier (**still 0.25**, ~10× the others) after
      the first print with Extrusion Flow Calibration on. If it stays, recalibrate head 3.

## 5. First-layer work resumes on 2.0.0

`z_offset` is back at the factory -0.05 (decided 2026-10-13). The 1.4.0 ladder
result (−0.04 mm from -0.07) doesn't carry over: it was measured on a different
offset and firmware. **Print the first-layer test on each head with Auto
Leveling on before considering any offset change**; only run the ladder for a
head that still looks wrong.

- Send tests from **Snapmaker Orca**, printer **HeatSoak**, with Auto Leveling
  on (Print → Upload and Print → Print Preprocessing).
- Watch the fresh mesh's centre value. On 1.4.0 a fresh mesh read +0.19 mm at
  the homing point while a re-zeroed saved mesh read 0.00. That offset decides
  how far a ladder result transfers between prints.

## To-do later (not part of the update)

- [ ] **PA chamber/bed handling.** Steps 1–3 applied 2026-10-14; step 4 (check real prints) open.
      Measured from klippy.log (bed boost to 100 °C + Panda Breath at full power):
      | | Time |
      |---|---|
      | Chamber 28 → 60 °C, cold start | 18 min (~1.1 °C/min over the last 10 °C) |
      | Chamber 37 → 60 °C, warm start | 15 min |
      | Bed 95 → 70 / 60 / 50 °C, heater off, chamber cooling from 60 to 41 °C | 9 / 17 / 29 min |

      Findings:
      1. Snapmaker Orca emits `M191 S60` as the **first line**, before the start
         G-code, with no bed temperature. The start G-code's `M140`/`M190` come later.
      2. **PA's bed target (50/45 °C) is below its chamber target (60 °C).** A bed
         with its heater off can't cool below the chamber air temperature, so
         `M190 S50` (which waits within ±1 °C, in both directions) only finishes once
         the chamber itself cools. That's the long wait, not the boost alone.
      3. After reaching temperature, our `M191` hands the hold to Panda native auto
         mode with `HOTBEDTEMP=80`. Auto mode only heats while the bed is ≥ 80 °C,
         so with a 45–50 °C PA bed the **chamber isn't held during the print**
         (fine for ASA at 95–100 °C). To confirm by watching a PA print.

      **Decided rule (2026-10-13), for every filament with chamber control:** keep
      the filament's chamber target (Orca's "Chamber temperature", e.g. 60 °C). While
      `M191` waits for the chamber, the bed is set to that same temperature (it was
      100 °C). Afterwards the start G-code raises the bed if the filament needs it
      hotter (ASA 100 °C) and never waits for it to cool (PA's 50 °C bed just
      settles near the chamber temperature). Apply after the current print, in this
      order:
      1. ✅ Start G-code (slicer): `M190 S{bed_temperature_initial_layer_single}` →
         `M140 S{…}` + `TEMPERATURE_WAIT SENSOR=heater_bed MINIMUM={… - 1}`. Must go
         first, or PA would hang at `M190 S50` with a 60 °C bed.
      2. ✅ `panda_breath.cfg` `M191`: `M140 S100` → `M140 S{s}` (bed = chamber target).
      3. ✅ `panda_breath.cfg` `M191` and `M141`: auto-mode hold with `HOTBEDTEMP=30` instead of 80,
         so the chamber is held with low PA beds too. `M141 S0` at print end still
         turns it off.
      4. Check the next ASA and PA prints in klippy.log: chamber heat-up time without
         the 100 °C boost, the bed during the first layer, and the chamber held through
         the print. If ASA heat-up is too slow, add a "boost to 100 until near target"
         stage for filaments whose bed is hotter than their chamber.
      5. 2026-10-14 PA test (bed at chamber target throughout): chamber 28 → 60 °C in
         ~30 min (vs 18 with the boost); chamber held at 58–60 °C through the print
         at `HOTBEDTEMP=30`; bed settled at ~63 °C (≈ chamber + 4–5 °C). The bed
         closes about two-thirds of its gap to that every ~5.5 min.
      6. ✅ Hybrid applied 2026-10-14: `M191` boosts the bed to 100 °C until the chamber
         reaches `S − MARGIN` (default 5), then sets the bed to `S` for the final
         stretch. Expected: chamber ~18–20 min; PA bed ~65 °C at the first layer.
         To verify on the next ASA/PA print.
      7. 2026-10-15 ASA cold start with the hybrid: 28 min (14.5 boost + 13.5 final
         stretch); the last degrees need bed radiation. **`MARGIN` default set to 0**
         (boost to the end, start routine cools a PA bed); uploaded 15:40 after the
         print. To verify on the next cold-start ASA/PA print.
- [x] **Done 2026-10-13:** `print_macros.cfg` include removed from `printer.cfg`
      (stock `PRINT_START` active again; `PRINT_WARMUP` retired). HeatSoak start
      G-code in `snapmaker-orca-rebased/` now calls `PRINT_START`. Original note:
      **Stock `PRINT_START` never runs.** The HeatSoak start G-code calls
      `PRINT_WARMUP` instead, and `print_macros.cfg` redefines `PRINT_START` (a
      macro nothing calls). Stock `PRINT_START` (in `fluidd.cfg`) re-applies each
      head's calibrated pressure advance (`FLOW_APPLY_CALIBRATE_K`), and resets the
      speed factor (`M220 S100`) and some auto-feed state. Effect today: a print
      whose filament sets its own PA (e.g. the PETG preset's 0.03) leaves that
      head at that value until the next reboot or flow calibration. Possible fix:
      delete our `PRINT_START` from `print_macros.cfg`, then call stock
      `PRINT_START` as the first line of the HeatSoak start G-code. Its `M84` is
      harmless there, because `PRINT_WARMUP` homes right after.

## 6. Slicer housekeeping (local, independent of the firmware)

- [ ] With Snapmaker Orca **closed**, install the rebased presets from
      [`slicer-config/snapmaker-orca-rebased/`](slicer-config/snapmaker-orca-rebased/)
      into `~/Library/Application Support/Snapmaker_Orca/user/default/`
      (back up the current folder first). This fixes the HeatSoak printer preset
      in Snapmaker Orca, which was saved on Oct 2 22:11 with:
  - **Before layer change** = the whole 107-line start G-code (would run at every layer)
  - **Layer change** = the end G-code including `PRINT_END` (would run at every layer)
  - end and tool-change G-code falling back to Snapmaker Orca's older versions

  No print has used that preset yet; recent Snapmaker Orca prints used the
  stock `Snapmaker U1 (0.4 nozzle)` preset, so they also skipped `PRINT_WARMUP`.
  Side-by-side copies of every differing G-code field are in
  [`slicer-config/gcode-compare/`](slicer-config/gcode-compare/), and per-preset
  details are in `snapmaker-orca-rebased/REPORT.txt`.
