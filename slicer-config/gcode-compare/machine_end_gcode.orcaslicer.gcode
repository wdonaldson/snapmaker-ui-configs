;===== date: 20260605 =====================
; layer [layer_num]
; max_layer_z [max_layer_z]
; print_sequence [print_sequence]

{if print_sequence == "by object"}
{
local move_z = max_print_height;

if max_layer_z < ((max_print_height - z_offset) - 2) then
    move_z = z_offset + min(((max_layer_z - z_offset) + 2), max_print_height);
endif
}

G91
G1 X2 Y2 Z1 F24000
G90
G1 Z{move_z} F600
{endif}

PRINT_END
TIMELAPSE_STOP
