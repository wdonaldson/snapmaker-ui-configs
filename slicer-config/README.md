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

## Naming convention — use `AI `, never `AI:`

All custom presets are prefixed `AI` + **space**. An earlier `AI:` scheme is
banned: **OrcaSlicer silently rejects `:` in preset names**. Saving or loading
a colon-named preset can revert to a stale in-memory copy with no error. That
caused a real Strength-profile regression (PETG interface settings dropped).

Filenames and internal `name` / `filament_settings_id` / `print_settings_id`
must match the space-based form. If a preset silently reverts after restart,
check its name for a colon first.

## Current profile set (0.20mm only)

0.16mm process tiers were removed to keep one layer height while PETG-interface
tuning was in progress. Re-derive from 0.20mm later if needed.

| Role | Preset | Path |
|---|---|---|
| ASA filament | `AI PolyLite ASA @ NoCooling` | `orcaslicer/filament/` |
| PETG interface filament | `AI PETG Support Inf for ASA` | `orcaslicer/filament/` |
| Visual Quality process | `AI 0.20 Visual Quality ASA @ .4` | `orcaslicer/process/` |
| Compromise process | `AI 0.20 Compromise ASA @ .4` | `orcaslicer/process/` |
| Strength process | `AI 0.20 Strength ASA @ .4` | `orcaslicer/process/` |
| PETG interface test | `AI 0.20 PETG Interface Test @ .4` | `orcaslicer/process/` |
| Printer | `Snapmaker U1 (0.4 nozzle), HeatSoak` | `orcaslicer/machine/` |

### Process tiers (quick reference)

- **Visual Quality** — 2 walls, 10% lightning, slow outer wall, extra shells. Cosmetic.
- **Compromise** — 4 walls, 20% gyroid. Daily driver.
- **Strength** — 6 walls, 40% gyroid, slow walls/infill, no ironing, random seam.

All three production tiers share PETG-interface support tuning (solid interface,
denser tree tips, dual-extruder `print_extruder_id`).

## How to plate a dual-material ASA print

1. Printer: `Snapmaker U1 (0.4 nozzle), HeatSoak`
2. Process: one of `AI 0.20 Visual Quality / Compromise / Strength ASA @ .4`
3. **Tool 1 (PETG slot):** `AI PETG Support Inf for ASA` — not stock `Snapmaker PETG @U1`
4. **ASA body tool:** `AI PolyLite ASA @ NoCooling`
5. Process settings already route interface only: `support_interface_filament: 1`,
   `support_filament: 0`, `support_interface_not_for_body: 1`

## Filament notes

### `AI PolyLite ASA @ NoCooling`

PolyLite ASA tuned for the U1 chamber: nozzle ~260°C, bed 95/100°C, fan off
except light overhang/bridge assist, chamber 60°C (U1 max).

### `AI PETG Support Inf for ASA`

Inherits Snapmaker `PETG @U1`, overridden for **support-interface-only** use in
a 60°C ASA chamber (Orca takes the max chamber temp across filaments). Fan
pushed high, nozzle cooled vs stock U1 PETG, retraction lengthened + z-hop —
all to cope with heat-soaked PETG, not to make a normal PETG profile.

**Toolchanger gear-jam (2026-07-29):** frequent toolchanges + 10mm
`retract_length_toolchange` + soft heat-soaked filament chewed a knot at the
drive gear. Fix: `filament_retraction_speed` **60 → 30 mm/s**. If knotting
returns: inspect that toolhead's gear, reconsider densified tree tips (more
interface islands → more toolchanges), or shorten retraction length.

Do **not** leave accidental `… - Copy` duplicates around after Orca prompts
about unsaved changes; keep this preset as the single canonical PETG interface.

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

After any rename/resave, diff Strength against `AI 0.20 PETG Interface Test @ .4`
(or another known-good tier) before trusting a print.

### Watchlist for next prints

- PETG interface adhesion on Strength (post-regression fix)
- Whether 30 mm/s retraction stops gear knotting

## Syncing

```sh
LIVE="$HOME/Library/Application Support/OrcaSlicer/user/default"
REPO="$(git rev-parse --show-toplevel)/slicer-config/orcaslicer"

# Pull live → repo (after intentional Orca edits)
cp "$LIVE/filament/AI PolyLite ASA @ NoCooling."* "$REPO/filament/"
cp "$LIVE/filament/AI PETG Support Inf for ASA.json" "$REPO/filament/"
cp "$LIVE/process/AI 0.20 "* "$REPO/process/"
cp "$LIVE/machine/Snapmaker U1 (0.4 nozzle), HeatSoak."* "$REPO/machine/"

# Restore repo → live (then restart Orca / Reload from disk)
# cp "$REPO/filament/"* "$LIVE/filament/"
# cp "$REPO/process/"* "$LIVE/process/"
# cp "$REPO/machine/"* "$LIVE/machine/"
```
