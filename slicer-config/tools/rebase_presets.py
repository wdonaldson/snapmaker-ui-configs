#!/usr/bin/env python3
"""Rebase OrcaSlicer user presets onto Snapmaker Orca system profiles without
changing their effective settings.

For each user preset: resolve it fully against the OrcaSlicer system profiles
it was written for, resolve the new Snapmaker Orca parent, and emit a preset
that inherits the new parent and pins every key whose value differs.

    rebase_presets.py OUT_DIR          # write rebased presets + print a report
    rebase_presets.py --diff-machine   # compare effective G-code fields only
    rebase_presets.py --to-orcaslicer ORCA_SRC OUT_DIR
                                       # the reverse: Snapmaker Orca presets onto
                                       # OrcaSlicer parents, print_host set

Nothing is written into either slicer's settings folder; copy OUT_DIR's
contents into ~/Library/Application Support/Snapmaker_Orca/user/default/
(or OrcaSlicer/user/default/) yourself, with the app closed.

OrcaSlicer 2.4.2 keeps its system profiles packed in .opc files, so the reverse
direction reads them as JSON from a checkout of the matching release tag
(ORCA_SRC, e.g. OrcaSlicer at v2.4.2; resources/profiles and
src/libslic3r/PrintConfig.cpp are all it needs).
"""
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
OLD_SYS = f"{HOME}/Library/Application Support/OrcaSlicer/system"
NEW_SYS = f"{HOME}/Library/Application Support/Snapmaker_Orca/system"
SRC = f"{HOME}/Library/Application Support/OrcaSlicer/user/default"
NEW_USER = f"{HOME}/Library/Application Support/Snapmaker_Orca/user/default"
PRINTER_HOST = "192.168.4.50"  # the U1 (Moonraker on :7125, Fluidd on :80)

# Old parent -> Snapmaker Orca 2.4.0 parent (same name when absent).
PARENT_MAP = {
    "0.12 High Quality @Snapmaker U1 (0.4 nozzle)": "0.12mm Standard @Snapmaker U1 (0.4 nozzle)",
    "0.16 High Quality @Snapmaker U1 (0.4 nozzle)": "0.16mm Standard @Snapmaker U1 (0.4 nozzle)",
    "0.20 Standard @Snapmaker U1 (0.4 nozzle)": "0.20mm Standard @Snapmaker U1 (0.4 nozzle)",
    "0.20 Strength @Snapmaker U1 (0.4 nozzle)": "0.20mm Standard @Snapmaker U1 (0.4 nozzle)",
    "0.20 Quality @Snapmaker U1 (0.4 nozzle)": "0.20mm Standard @Snapmaker U1 (0.4 nozzle)",
    "0.28 Extra Draft @Snapmaker U1 (0.4 nozzle)": "0.28mm Standard @Snapmaker U1 (0.4 nozzle)",
    "Snapmaker PETG @U1": "Generic PETG",
}
# Snapmaker Orca parent -> OrcaSlicer 2.4.2 parent, for --to-orcaslicer. Each is
# the OrcaSlicer profile with the fewest differing keys (or the original parent).
REVERSE_PARENT_MAP = {
    "0.12mm Standard @Snapmaker U1 (0.4 nozzle)": "0.12 High Quality @Snapmaker U1 (0.4 nozzle)",
    "0.16mm Standard @Snapmaker U1 (0.4 nozzle)": "0.16 High Quality @Snapmaker U1 (0.4 nozzle)",
    "0.20mm Standard @Snapmaker U1 (0.4 nozzle)": "0.20 Standard @Snapmaker U1 (0.4 nozzle)",
    "0.28mm Standard @Snapmaker U1 (0.4 nozzle)": "0.28 Extra Draft @Snapmaker U1 (0.4 nozzle)",
    "Generic PETG": "Snapmaker PETG @U1",
    "Snapmaker TPU 95A HF @U1 0.4 nozzle": "Snapmaker TPU 95A @U1",
}
# Identity / bookkeeping keys never copied from a base.
META = {"name", "inherits", "from", "instantiation", "setting_id", "filament_id",
        "renamed_from", "type", "version", "is_custom_defined", "base_id",
        "print_settings_id", "filament_settings_id", "printer_settings_id",
        "compatible_printers", "compatible_printers_condition",
        "compatible_prints", "compatible_prints_condition", "inherits_group",
        "description"}
KINDS = ("machine", "process", "filament")


def index(root):
    """(vendor, kind, name) -> data for every system profile under root."""
    idx = {}
    for vendor in os.listdir(root):
        vdir = os.path.join(root, vendor)
        if not os.path.isdir(vdir):
            continue
        for dirpath, _, files in os.walk(vdir):
            kind = next((k for k in KINDS if f"/{k}/" in dirpath + "/"), None)
            for f in files:
                if not f.endswith(".json"):
                    continue
                try:
                    d = json.load(open(os.path.join(dirpath, f)))
                except Exception:
                    continue
                if "name" in d:
                    idx.setdefault((vendor, kind, d["name"]), d)
    return idx


def resolve(idx, kind, name, vendor="Snapmaker"):
    for v in (vendor, "Snapmaker", "OrcaFilamentLibrary", "Custom"):
        if (v, kind, name) in idx:
            d = idx[(v, kind, name)]
            base = resolve(idx, kind, d["inherits"], v) if d.get("inherits") else {}
            return {**base, **d}
    raise KeyError(f"{kind} '{name}' not found")


def load_user(folder, kind, fname):
    return json.load(open(os.path.join(folder, kind, fname)))


def diff_machine(old_idx, new_idx):
    name = "Snapmaker U1 (0.4 nozzle), HeatSoak.json"
    uo, un = load_user(SRC, "machine", name), load_user(NEW_USER, "machine", name)
    eo = {**resolve(old_idx, "machine", uo["inherits"]), **uo}
    en = {**resolve(new_idx, "machine", un["inherits"]), **un}
    for k in sorted(k for k in set(eo) | set(en) if "gcode" in k):
        a, b = eo.get(k), en.get(k)
        state = ("same" if a == b else "only in OrcaSlicer" if b is None
                 else "only in Snapmaker Orca" if a is None else "DIFFERENT")
        first = lambda s: (s.split("\n")[0][:60] if isinstance(s, str) else "")
        print(f"{k:<32} {state:<22} OrcaSlicer: {first(a)!r:<64} Snapmaker Orca: {first(b)!r}")


def orca_schema(print_config_cpp):
    """key -> allowed enum values (None for non-enum) from OrcaSlicer's PrintConfig.cpp."""
    src = open(print_config_cpp).read()
    maps = {m.group(1): set(re.findall(r'\{\s*"([^"]+)"', m.group(2)))
            for m in re.finditer(r"s_keys_map_(\w+)\s*\{(.*?)\n\};", src, re.S)}
    schema = {}
    for m in re.finditer(r'this->add(?:_nullable)?\("([^"]+)",\s*(\w+)\)(.*?)(?=this->add|\Z)', src, re.S):
        enum = re.search(r"ConfigOptionEnum<(\w+)>::get_enum_values", m.group(3))
        schema[m.group(1)] = maps.get(enum.group(1)) if enum else None
    # filament_retraction_length etc. are added in a loop, copying the printer option.
    overrides = re.search(r"filament_extruder_override_keys = \{(.*?)\};", src, re.S).group(1)
    for key in re.findall(r'"(filament_\w+)"', overrides):
        schema[key] = schema.get(key[len("filament_"):])
    # machine_max_speed_x etc. are added in a loop over the axes.
    for limit in ("speed", "acceleration", "jerk"):
        for axis in "xyze":
            schema[f"machine_max_{limit}_{axis}"] = None
    return schema


def orca_nullable(print_config_cpp):
    """Options declared with add_nullable: only these may hold "nil" entries."""
    src = open(print_config_cpp).read()
    keys = set(re.findall(r'this->add_nullable\("([^"]+)"', src))
    overrides = re.search(r"filament_extruder_override_keys = \{(.*?)\};", src, re.S).group(1)
    return keys | set(re.findall(r'"(filament_\w+)"', overrides))


def bad_enums(preset, schema):
    """Keys whose value the target app would not accept."""
    bad = []
    for k, v in preset.items():
        allowed = schema.get(k)
        if allowed and any(x not in allowed for x in (v if isinstance(v, list) else [v])):
            bad.append(f"{k}={v}")
    return bad


def rebase(old_idx, new_idx, out_dir, src=SRC, kinds=KINDS, parent_map=PARENT_MAP,
           target="Snapmaker Orca", schema=None, nullable=None):
    """With schema (the target's options), a key missing from the new parent is pinned
    when the target knows it, so the target's built-in default can't replace it."""
    for kind in kinds:
        os.makedirs(os.path.join(out_dir, kind), exist_ok=True)
        for f in sorted(os.listdir(os.path.join(src, kind))):
            if not f.endswith(".json"):
                continue
            user = json.load(open(os.path.join(src, kind, f)))
            old_parent = user["inherits"]
            new_parent = parent_map.get(old_parent, old_parent)
            eff = {**resolve(old_idx, kind, old_parent), **user}
            new_base = resolve(new_idx, kind, new_parent)
            out = dict(user, inherits=new_parent)
            pinned, dropped = [], []
            for k, v in eff.items():
                if k in META or k in user:
                    continue
                if k not in new_base and (schema is None or k not in schema):
                    dropped.append(k)
                elif new_base.get(k) != v:
                    out[k] = v
                    pinned.append(k)
            unknown = sorted(k for k in user if schema and k not in META and k not in schema)
            for k in unknown:
                out.pop(k)
            # Both apps store every value as a string and silently drop a preset key
            # written as a JSON number ("invalid json type"), e.g. support_filament: 0.
            numbers = sorted(k for k, v in out.items() if isinstance(v, (int, float)))
            for k in numbers:
                out[k] = str(int(out[k]) if isinstance(out[k], bool) else out[k])
            # Snapmaker Orca writes "nil" for unused toolheads even in lists OrcaSlicer
            # can't null (nozzle_type); repeat the first real value instead.
            nils = sorted(k for k, v in out.items() if nullable is not None and k not in nullable
                          and isinstance(v, list) and "nil" in v and any(x != "nil" for x in v))
            for k in nils:
                first = next(x for x in out[k] if x != "nil")
                out[k] = [first if x == "nil" else x for x in out[k]]
            if kind == "machine" and target == "OrcaSlicer":
                out["print_host"] = PRINTER_HOST  # Set & Send needs it; Print is greyed out without
                # OrcaSlicer's U1 parent slows outer walls at 40-90 mm/s to 40; Snapmaker Orca
                # has no such setting, and the processes were tuned without it.
                out["resonance_avoidance"] = "0"
            elif kind == "machine":
                out.pop("print_host", None)  # let Print use Snapmaker Orca's LAN send
            json.dump(out, open(os.path.join(out_dir, kind, f), "w"), indent=4)
            print(f"[{kind}] {f[:-5]}")
            print(f"    parent: {old_parent}" + ("" if old_parent == new_parent else f"  ->  {new_parent}"))
            print(f"    pinned {len(pinned)}: {', '.join(sorted(pinned))}")
            if dropped:
                print(f"    not in {target} (left out): {', '.join(sorted(dropped))}")
            if unknown:
                print(f"    set in the preset but unknown to {target} (removed): {', '.join(unknown)}")
            if numbers:
                print(f"    written as numbers, now strings: {', '.join(numbers)}")
            for k in nils:
                print(f"    {k}: \"nil\" entries filled with the first value: {out[k]}")
            if schema and bad_enums(out, schema):
                print(f"    VALUE {target} WON'T ACCEPT: {', '.join(bad_enums(out, schema))}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--to-orcaslicer"] and len(sys.argv) == 4:
        orca = sys.argv[2]
        rebase(index(NEW_SYS), index(f"{orca}/resources/profiles"), sys.argv[3], src=NEW_USER,
               parent_map=REVERSE_PARENT_MAP, target="OrcaSlicer",
               schema=orca_schema(f"{orca}/src/libslic3r/PrintConfig.cpp"),
               nullable=orca_nullable(f"{orca}/src/libslic3r/PrintConfig.cpp"))
        sys.exit()
    old_idx, new_idx = index(OLD_SYS), index(NEW_SYS)
    if sys.argv[1:] == ["--diff-machine"]:
        diff_machine(old_idx, new_idx)
    elif len(sys.argv) == 2:
        rebase(old_idx, new_idx, sys.argv[1])
    else:
        sys.exit(__doc__)
