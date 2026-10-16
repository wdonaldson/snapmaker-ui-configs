#!/usr/bin/env python3
"""Rebase OrcaSlicer user presets onto Snapmaker Orca system profiles without
changing their effective settings.

For each user preset: resolve it fully against the OrcaSlicer system profiles
it was written for, resolve the new Snapmaker Orca parent, and emit a preset
that inherits the new parent and pins every key whose value differs.

    rebase_presets.py OUT_DIR          # write rebased presets + print a report
    rebase_presets.py --diff-machine   # compare effective G-code fields only

Nothing is written into either slicer's settings folder; copy OUT_DIR's
contents into ~/Library/Application Support/Snapmaker_Orca/user/default/
yourself, with Snapmaker Orca closed.
"""
import json
import os
import sys

HOME = os.path.expanduser("~")
OLD_SYS = f"{HOME}/Library/Application Support/OrcaSlicer/system"
NEW_SYS = f"{HOME}/Library/Application Support/Snapmaker_Orca/system"
SRC = f"{HOME}/Library/Application Support/OrcaSlicer/user/default"
NEW_USER = f"{HOME}/Library/Application Support/Snapmaker_Orca/user/default"

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


def rebase(old_idx, new_idx, out_dir):
    for kind in KINDS:
        os.makedirs(os.path.join(out_dir, kind), exist_ok=True)
        for f in sorted(os.listdir(os.path.join(SRC, kind))):
            if not f.endswith(".json"):
                continue
            user = json.load(open(os.path.join(SRC, kind, f)))
            old_parent = user["inherits"]
            new_parent = PARENT_MAP.get(old_parent, old_parent)
            eff = {**resolve(old_idx, kind, old_parent), **user}
            new_base = resolve(new_idx, kind, new_parent)
            out = dict(user, inherits=new_parent)
            pinned, dropped = [], []
            for k, v in eff.items():
                if k in META or k in user:
                    continue
                if k not in new_base:
                    dropped.append(k)
                elif new_base[k] != v:
                    out[k] = v
                    pinned.append(k)
            if kind == "machine":
                out.pop("print_host", None)  # let Print use Snapmaker Orca's LAN send
            json.dump(out, open(os.path.join(out_dir, kind, f), "w"), indent=4)
            print(f"[{kind}] {f[:-5]}")
            print(f"    parent: {old_parent}" + ("" if old_parent == new_parent else f"  ->  {new_parent}"))
            print(f"    pinned {len(pinned)}: {', '.join(sorted(pinned))}")
            if dropped:
                print(f"    not in Snapmaker Orca (left out): {', '.join(sorted(dropped))}")


if __name__ == "__main__":
    old_idx, new_idx = index(OLD_SYS), index(NEW_SYS)
    if sys.argv[1:] == ["--diff-machine"]:
        diff_machine(old_idx, new_idx)
    elif len(sys.argv) == 2:
        rebase(old_idx, new_idx, sys.argv[1])
    else:
        sys.exit(__doc__)
