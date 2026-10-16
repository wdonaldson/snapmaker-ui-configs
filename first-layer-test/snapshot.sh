#!/bin/sh
# Read-only: print the active head, its calibrated Z offset, and any live-Z
# trim applied on top of it (babystep from Fluidd or the touchscreen).
# Run while the test layer is printing, after you've finished adjusting.
#   ./snapshot.sh            (default printer 192.168.4.50)
#   PRINTER_IP=1.2.3.4 ./snapshot.sh
PRINTER_IP=${PRINTER_IP:-192.168.4.50}

curl -s -m 5 "http://$PRINTER_IP:7125/printer/objects/query?toolhead=extruder&gcode_move=homing_origin&extruder=extruder_offset&extruder1=extruder_offset&extruder2=extruder_offset&extruder3=extruder_offset&print_stats=filename,state" |
python3 -c '
import json, sys
s = json.load(sys.stdin)["result"]["status"]
active = s["toolhead"]["extruder"]
head = {"extruder": 1, "extruder1": 2, "extruder2": 3, "extruder3": 4}[active]
cal_z = s[active]["extruder_offset"][2]
applied_z = s["gcode_move"]["homing_origin"][2]
ps = s["print_stats"]
job, state = ps["filename"], ps["state"]
print(f"job:          {job} ({state})")
print(f"active head:  {head}  ({active})")
print(f"calibrated Z: {cal_z:+.3f} mm")
print(f"applied Z:    {applied_z:+.3f} mm")
print(f"live trim:    {applied_z - cal_z:+.3f} mm   <- record this")
'
