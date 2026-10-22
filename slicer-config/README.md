# OrcaSlicer — Filament & Process Configuration

Versioned copies of the custom OrcaSlicer presets used with this Snapmaker U1
setup (ASA body + PETG support interface, heated chamber at 60°C).

Live files live in:

```
~/Library/Application Support/OrcaSlicer/user/default/
```

OrcaSlicer is the source of truth while editing in the app. Sync *from* live
into `orcaslicer/` after intentional changes; copy *back* (then restart Orca
or "Reload from disk") to restore from this repo.

Related Klipper macros / machine start G-code live in this repo's root and in
`orca-machine-gcode.cfg` / `orca-end-gcode.cfg`.

## Layout

```
slicer-config/
├── README.md                          ← this file
├── orca-machine-gcode.cfg             ← HeatSoak machine start G-code excerpt
├── orca-end-gcode.cfg
└── orcaslicer/
    ├── filament/
    ├── process/
    └── machine/
```

## Naming convention — `Filament Characterization @nozzle (ai)`

All presets we created end in **`(ai)`** (lower-case). Names start with the
**filament type** so the dropdowns group by material, then what the preset is
for, then the nozzle for process presets: `ASA Strength @0.4 (ai)`,
`PA Draft @0.4 (ai)`, `All High Quality @0.4 (ai)` (`All` = filament-agnostic).
Filament presets carry no nozzle: `PA Sunlu Easy (ai)`. Layer height is not in
the name (adopted 2026-10-16; the earlier `AI 0.20 … @ .4` scheme and the
`@ NoCooling` suffixes are gone).

**Never use `:` in a preset name.** OrcaSlicer silently rejects it and can
revert to a stale in-memory copy with no error; that caused a real
Strength-profile regression in July 2026. Filenames and the internal `name` /
`filament_settings_id` / `print_settings_id` must match exactly. If a preset
silently reverts after a restart, check its name for a colon first.

## Current profile set (0.20mm only)

0.16mm process tiers were removed to keep one layer height while PETG-interface
tuning was in progress. Re-derive from 0.20mm later if needed.

| Role | Preset | Path |
|---|---|---|
| ASA filament | `ASA PolyLite (ai)` | `snapmaker-orca-rebased/filament/` |
| ABS-GF filament | `ABS-GF Generic (ai)` | `snapmaker-orca-rebased/filament/` |
| PETG interface filament | `PETG Support Interface (ai)` | `snapmaker-orca-rebased/filament/` |
| PA (nylon) filament | `PA Sunlu Easy (ai)` | `snapmaker-orca-rebased/filament/` |
| TPU filament | `TPU 95A (ai)` (based on Snapmaker's 95A HF; untested starting values) | `snapmaker-orca-rebased/filament/` |
| TPU processes | `TPU Standard / Easy Supports @0.4 (ai)` (tree supports in TPU; threshold 50°, gap 0.2) | `snapmaker-orca-rebased/process/` |
| TPU with PLA support interface (special case) | `TPU PLA Support @0.4 (ai)`: tree-strong supports, 3 PLA interface layers on **filament 2** (load PLA as filament 2), prime tower off; printed very well 2026-10-21 | `snapmaker-orca-rebased/process/` |
| ASA processes | `ASA Visual Quality / Standard / Compromise / Strength @0.4 (ai)` (same-material supports) | `snapmaker-orca-rebased/process/` |
| ASA with PETG interface (special case) | `ASA Strength PETG Support @0.4 (ai)`, `ASA Visual Quality PETG Support @0.4 (ai)` | `snapmaker-orca-rebased/process/` |
| ASA + PETG interface test | `ASA Test PETG Interface @0.4 (ai)` | `snapmaker-orca-rebased/process/` |
| ABS process | `ABS Strength Slow @0.4 (ai)` | `snapmaker-orca-rebased/process/` |
| PA processes | `PA Draft / Standard / Strength / Strength Thin Walls @0.4 (ai)` | `snapmaker-orca-rebased/process/` |
| PA overhang tests | filament `PA Sunlu Easy Overhang Test (ai)` (nozzle 250, fan 70/100) with `PA Test Overhang @0.4 (ai)` (supports off, for `PA-overhang-test.stl`) or `PA High Resolution @0.4 (ai)` (0.12 mm, for a Benchy); experimental, see `DECISION-LOG.md` 2026-10-22 | `snapmaker-orca-rebased/{filament,process}/` |
| Filament-agnostic processes | `All High Quality / Extra Draft / Strength Support / Strength Fast / Test First Layer @0.4 (ai)` | `snapmaker-orca-rebased/process/` |
| Printer | `Snapmaker U1 (0.4 nozzle), HeatSoak` | `snapmaker-orca-rebased/machine/` |

The `orcaslicer/` folder keeps the July 2026 OrcaSlicer originals under their
old names for reference; Snapmaker Orca is the live slicer for the U1.

## Process tiers (quick reference)

**Standard** (added 2026-10-16, ASA and PA): the "just print it" tier between
Draft and Strength. 3 walls, 4/3 top/bottom, **15 % adaptive cubic**, no top
ironing, elephant-foot 0.25 mm over 2 layers, same-material tree-slim supports
with support ironing, scarf seam. Speeds/accel/jerk come from the filament's
tuned preset (ASA: Compromise's; PA: the slow PA set). Use Draft only for fit
checks, Strength when the part is structural.

**ASA (dual-material, PETG interface):**
- **Visual Quality** — 2 walls, 10% lightning, slow outer wall, extra shells. Cosmetic.
- **Compromise** — 4 walls, 20% gyroid. Daily driver.
- **Strength** — 6 walls, 40% gyroid, slow walls/infill, no ironing, random seam.

All three production tiers share PETG-interface support tuning (solid interface,
denser tree tips, dual-extruder `print_extruder_id`).

**Sunlu Easy PA (single-material, functional-part workflow):**
- **Draft** — 2 walls, 10% lightning, fast (70/120/150 mm/s), no ironing. Print
  this first on any new geometry to check fit/dimensions and, specifically,
  how cleanly the supports break away and what the touched surfaces look like.
- **Strength** — 6 walls, 35% gyroid, slow walls/infill (50/60/90 mm/s) for
  maximum interlayer fusion, top ironing (also helps seal the top surface
  against moisture pickup). Print this once Draft confirms fit and support
  quality.
- **Strength Thin Walls** — same as Strength, but `outer_wall_line_width` /
  `inner_wall_line_width` dropped from the default 0.42/0.45mm to **0.32mm**
  (80% of the 0.4mm nozzle), with `wall_loops` raised 6→8 to keep the bulk
  wall footprint in open areas roughly the same as the standard Strength
  tier (8×0.32 ≈ 6×0.42). Use this whenever a feature is too thin for the
  regular tier to fit its target wall count — e.g. a boss around a dowel/pin
  hole — since Orca's Arachne wall generator will merge perimeters down to
  1-2 thick loops in tight spots rather than 3+ thinner ones unless the
  nominal line width is small enough to leave it room. 3 loops need ~0.96mm
  of wall thickness at 0.32mm/loop; if a specific boss is even tighter than
  that and still isn't getting 3 walls, the next lever is `min_bead_width`
  (Advanced tab, default 85%) — lowering it lets Arachne squeeze narrower
  still before giving up and merging loops.

Both PA tiers use the *same* support tuning (single-material support, no
second filament): `tree_slim` style, `tree(auto)` type, solid rectilinear
interface, slower `support_interface_speed` (25 mm/s, vs body speeds) for a
smoother witness surface, `support_top_z_distance` opened up slightly to
0.15mm (vs ASA/PETG's 0.12mm) since PA fuses to itself more aggressively than
ASA-onto-PETG — that gap is what actually makes single-material PA supports
removable at all. If Draft prints show supports still welded on, open the gap
further (0.18-0.2mm) at some cost to the touched-surface finish; if the
witness surface is rougher than you'd like and removal is already easy, close
it back down toward 0.12mm.

## How to plate an ASA print

Default ASA presets print supports in ASA itself (one head, no tool changes):

1. Printer: `Snapmaker U1 (0.4 nozzle), HeatSoak`
2. Process: `ASA Standard @0.4 (ai)` for "just print it", or
   `ASA Visual Quality / Compromise / Strength @0.4 (ai)`
3. Filament: `ASA PolyLite (ai)` on whichever head holds it

### Special case: PETG support interface (dual material)

Only when the underside finish matters and the PETG head is loaded:

1. Process: `ASA Strength PETG Support @0.4 (ai)` or
   `ASA Visual Quality PETG Support @0.4 (ai)`
2. **Tool 1 (PETG slot):** `PETG Support Interface (ai)` — not stock `Snapmaker PETG @U1`
3. **ASA body tool:** `ASA PolyLite (ai)`
4. These two presets route the interface only: `support_interface_filament: 1`,
   `support_filament: 0`, `support_interface_not_for_body: 1`. Since 2026-10-16
   the plain ASA presets no longer carry those keys.

## How to test/print a single-material Sunlu Easy PA part

1. Printer: `Snapmaker U1 (0.4 nozzle), HeatSoak`
2. Filament: `PA Sunlu Easy (ai)` on whichever tool slot you loaded it into
   (these process presets don't pin `print_extruder_id` — unlike the ASA workflow,
   there's no second filament to route)
3. First print: `PA Draft @0.4 (ai)` — check dimensions/fit, then
   remove supports and inspect the touched surfaces before trusting the tier
4. Once satisfied: `PA Strength @0.4 (ai)` for the real part —
   or `PA Strength Thin Walls @0.4 (ai)` instead if the part has
   any thin bosses/walls (e.g. around a dowel or pin) that need to hold 3+
   full perimeter loops

## Filament notes

### `ASA PolyLite (ai)`

PolyLite ASA tuned for the U1 chamber: nozzle ~260°C, bed 95/100°C, fan off
except light overhang/bridge assist, chamber 60°C (U1 max).

### `PETG Support Interface (ai)`

Inherits Snapmaker `PETG @U1`, overridden for **support-interface-only** use in
a 60°C ASA chamber (Orca takes the max chamber temp across filaments). Fan
pushed high, nozzle cooled vs stock U1 PETG, short retraction + z-hop —
all to cope with heat-soaked PETG, not to make a normal PETG profile.

**Heat-creep / gear-jam fix (2026-07-31):** parked PETG idle was softening
filament at the drive gear. With process Ooze prevention on: filament
`idle_temperature` 120°C, process `preheat_time` 60 s, retraction length
0.6 mm @ 30 mm/s. Chamber stays 60°C for ASA. If swaps stall reheating,
raise `preheat_time` further before raising idle temp.

Do **not** leave accidental `… - Copy` duplicates around after Orca prompts
about unsaved changes; keep this preset as the single canonical PETG interface.

### `PA Sunlu Easy (ai)`

> **Updated 2026-10-16** (see `DECISION-LOG.md`): renamed to **`PA Sunlu Easy (ai)`**
> (in Snapmaker Orca). Chamber **45 °C** (was 60: stringing, and PA only needs a
> closed chamber), bed 50/50, nozzle 260/255, retraction 1.2 mm, part fan
> **20–50 %** with 80 % on overhangs/bridges, **"Keep fan always on" enabled** and
> fan cooling layer time 20 s (without always-on, Orca's minimum fan speed is
> never applied on long layers, so the fan sat at 0 % except on overhangs), and
> the PA process presets slowed to 40/50 mm/s walls with 3000/2000 accel and
> jerk 6/5. The paragraph below describes the original 2026-07 reasoning and is
> kept for context.

Inherits Orca's `Generic PA @System`. Sunlu Easy PA is a nylon reformulated
for easier printing (less warp, less moisture sensitivity, still high
strength/toughness) — datasheet: nozzle 250-280°C, bed 30-50°C, fan off,
PEI textured plate + glue, dry 4-6h @ 80-110°C before every spool.

Tuned for the U1's chamber heater (Panda Breath, 60°C max) + passive cover:
chamber held at 60°C the whole print (the main warp-control lever, since
Easy PA's own bed-temp spec is deliberately low), fan fully off except a
mild overhang/bridge assist, nozzle biased hot (265/270°C) within spec for
stronger interlayer fusion given the strength priority, retraction 1.0mm @
35mm/s (mid-spec). `filament_vendor: Sunlu`. Full rationale is in the file's
own `filament_notes`.

**Cooling refinements (2026-08-12):** the general fan stays at 0%
everywhere, but two fans are independently nudged on: `support_material_interface_fan_speed`
15% (firms up the support-touching surface faster — ties into the
support-quality goal) and `ironing_fan_speed` 20% (keeps the Strength tier's
top-ironing pass from staying glossy/soft in the 60°C chamber). Both require
`enable_overhang_bridge_fan` to stay ON to matter at all — if Orca's Cooling
tab ever shows that toggle off with an unsaved-changes asterisk in the title
bar, that's a stray in-app edit, not this file; reload from disk before
saving over it.

Pair with `PA Draft @0.4 (ai)` (fit/support-quality testing) and
`PA Strength @0.4 (ai)` (functional parts) — see "Process tiers"
above.

**Not yet done:** no dedicated support-interface filament for PA (unlike the
ASA+PETG combo). Same-material PA-on-PA support currently relies on a slightly
larger `support_top_z_distance` (0.15mm) to stay removable — watch this on the
first Draft print of any new geometry; see the Process tiers note above for
how to tune it.

## Known gotchas

### Strength stale-save regression (fixed)

While renaming off `AI:`, a Save Preset from a stale in-memory Strength copy
dropped PETG-interface overrides (`print_extruder_id`, `support_filament`,
`support_interface_not_for_body`, `support_interface_speed`). Restored those,
plus `wall_loops: 6`, `top_shell_layers: 5`, `ironing_type: no ironing`. Kept
`sparse_infill_pattern: gyroid`.

When syncing this repo (2026-07-29), live Orca still had the broken Strength
file; the fixed copy from the backup was written back to both this repo and
`~/Library/Application Support/OrcaSlicer/user/default/process/`. Reload from
disk (or restart Orca) before the next Strength print.

After any rename/resave, diff Strength against `ASA Test PETG Interface @0.4 (ai)`
(or another known-good tier) before trusting a print.

### Watchlist for next prints

- PETG interface adhesion on Strength (post-regression fix)
- Idle 120°C + short retract: no mid-print gear blob on long parks
- Swaps stay prompt with `preheat_time` 60 s (raise if they stall)

## Syncing

Live presets (Snapmaker Orca is the source of truth while editing in the app):

```
~/Library/Application Support/Snapmaker_Orca/user/default/
```

```sh
LIVE="$HOME/Library/Application Support/Snapmaker_Orca/user/default"
REPO="$(git rev-parse --show-toplevel)/slicer-config/snapmaker-orca-rebased"

# Pull live → repo (after intentional edits in the app)
cp "$LIVE"/filament/*.json "$REPO/filament/"
cp "$LIVE"/process/*.json  "$REPO/process/"
cp "$LIVE"/machine/*.json  "$REPO/machine/"

# Restore repo → live: quit Snapmaker Orca first, or it overwrites the files
# from memory on exit. `.info` sidecars are not versioned; the app rewrites them.
```

### Snapmaker Orca

Vanilla OrcaSlicer (2.4.2) can only upload to the U1. Its plain start leaves
bed leveling and flow calibration off, because the firmware resets them after
every print. Snapmaker Orca sends prints with those options, so the same
presets are mirrored there:

```
~/Library/Application Support/Snapmaker_Orca/user/default/
```

**Sending a print with options (Snapmaker Orca 2.4.0):** click **Print**. The
"Send G-code to printer host" dialog appears; click **Upload and Print**
there. That opens **Print Preprocessing**, which has the printer dropdown,
filament→head mapping and **Extrusion Flow Calibration / Time-lapse / Auto
Leveling**. If the U1 isn't listed on first open, close and reopen the
dropdown (Snapmaker Orca issue #854).

Copied 2026-10-02 from the OrcaSlicer folder, with two differences:

- `Snapmaker U1 (0.4 nozzle), HeatSoak` has no `print_host`. With a host set,
  **Print** falls back to the plain upload dialog, without the options.
- `All Test First Layer @0.4 (ai)` inherits `0.20 Standard @Snapmaker U1 (0.4 nozzle)`
  because Snapmaker Orca has no `0.20 Quality` profile.

`.info` files aren't copied; Snapmaker Orca writes its own. Copy changes across
with Snapmaker Orca closed, or it overwrites them from memory.
