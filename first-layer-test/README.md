# Per-head first-layer test

Goal: decide whether the rippled first layers on heads 2 and 4 follow the
**head** (Z offset / nozzle hardware → fix on the printer) or the **filament**
(flow / temp / speed → fix with Orca calibrations).

Model: [Perfect First Layer Test](https://www.printables.com/model/252059)
(`perfect-first-layer-test.stl`): five 0.2 mm tiles, one per corner plus
center, 176 × 176 mm as downloaded.

`first-layer-test-labeled.stl` is the same layout, with 40 mm tiles and each
tile's position (C, BL, BR, FR, FL) cut through it, so pulled tiles can't be
mixed up. Regenerate with
`/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd make_labeled_tiles.py`.
Import it as-is (no scaling), centered.

Head numbering below is the touchscreen's (1–4). Klipper/Orca use 0–3:
head 1 = `extruder`/T0, head 2 = `extruder1`/T1, head 3 = `extruder2`/T2,
head 4 = `extruder3`/T3.

## Slicer setup (same for every run)

1. Printer: `Snapmaker U1 (0.4 nozzle), HeatSoak`
2. Process: `AI 0.20 First Layer Test @ .4`. It's based on 0.20 Quality with
   these changes: first layer 0.2 mm, first-layer speed 25 mm/s, 2 walls, no
   brim or skirt, no elephant-foot compensation.
3. Import the STL, center it, and scale **X and Y only** to 142% (≈ 250 mm)
   with Z left at 0.2 mm. This puts the tiles near the bed edges.
4. Assign the object to the head under test. It must be the only head used,
   so that head also does the Z home and bed mesh. Slice it and check the
   preview shows exactly one layer.
5. Keep the plate, bed temperature and chamber the same across runs. For PLA,
   leave chamber heating off.

## Runs

**Pass A: as loaded.** Print once on each head with the filament already in
it. Don't touch Z, so you see the problem as it really is.

**Pass B: swap test.** Load the head-1 PLA into head 2, and then into head 4,
using the same filament preset. Print again.
- If the ripples **stay with the head**, the cause is the head.
- If they **move with the filament**, the cause is the filament.

**Pass C: find the trim** (only for heads that fail on the head side).
Reprint, and during the center tile adjust Z live (Fluidd or the touchscreen)
until the surface is smooth. Then run `./snapshot.sh` before the print ends
and record its `live trim` value.

**Z ladder (replaces live-adjusting).** `make_zladder.py` takes a sliced
single-layer test and gives each tile its own relative Z offset (default:
center 0, back left -0.02, back right -0.04, front right -0.06, front left
-0.08 mm; negative = closer to the bed). The best tile is that head's
correction. Upload with Orca's **Upload** button (not Upload and Print), then
start from the touchscreen with **Auto leveling** on, because Orca's upload
path skips the bed mesh.

    ./make_zladder.py sliced.gcode -o FLT-zladder-headN.gcode
    ./make_zladder.py sliced.gcode --offsets C=-0.04 BL=-0.05 BR=-0.06 FR=-0.07 FL=-0.08

## What to look for

- **Fish-scale ridges, plowed or transparent lines** → nozzle too close.
  Expect a positive trim (raise Z).
- **Separate round lines with gaps; tiles tear apart easily** → nozzle too
  far. Expect a negative trim.
- **Only some tiles bad** → a bed mesh or tilt problem, not a head problem.
  Note which tiles.
- A good tile is smooth, nearly gap-free, and hard to tear.

## Results

| Pass | Head | Filament / preset | Nozzle / bed °C | Tiles bad (FL FR C RL RR) | Look | Live trim (mm) |
|---|---|---|---|---|---|---|
| A | 1 | Generic PLA @System (sliced with 0.20 Quality, NOT the test preset: 0.25 mm / 50–105 mm/s) | 220 / 55, textured PEI | none worse, all 5 alike | rounded beaded lines, visible gaps, not fused | — (invalid run, redo) |
| A | 1 | Generic PLA @System, test preset (0.2 mm / 25 mm/s), 176 mm unscaled, stale mesh (auto-leveling off) | 220 / 55, textured PEI | all 5 alike | same as run 1: rounded beaded lines, translucent web between, curly/looped perimeter on left edges | 0 (none applied) → looks too high |
| Ladder | 1 | Generic PLA, test preset, FRESH 5×5 mesh (Auto leveling on), flow cal on (PA 0.0174) | 220 / 55 | C 0 good · BL −0.02 good but bed shows through between lines · **BR −0.04 best** · FR −0.06 ridges starting · FL −0.08 ridged/plowed | fresh mesh alone fixed most of it | **head 1 = −0.04** |
| A | 2 | | | | | |
| A | 3 | | | | | |
| A | 4 | | | | | |
| B | 2 | (head-1 PLA) | | | | |
| B | 4 | (head-1 PLA) | | | | |
| C | | | | | | |

Calibrated Z offsets for reference (2026-10-02, relative to head 1):
head 2 +0.146, head 3 +0.198, head 4 +0.076 mm.
