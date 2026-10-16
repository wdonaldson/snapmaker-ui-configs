# Build a labeled version of the Perfect First Layer Test: five single-layer
# tiles, each with its bed position (C, BL, BR, FR, FL) cut through it in block
# letters, so the tiles can be told apart after they're pulled off the bed.
# Letters read correctly from the front of the printer.
#
#   /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd make_labeled_tiles.py
#
# Writes first-layer-test-labeled.stl next to this script.
import os

import Mesh
import MeshPart
import Part
from FreeCAD import Vector

OUT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

SPAN = 176.0    # overall footprint, same as the original model
TILE = 40.0     # tile edge (original tiles are ~31.5 mm)
HEIGHT = 0.2    # one layer
CELL = 1.6      # letter pixel = 4 lines at 0.4 mm
MARGIN = 3.0    # label distance from the tile's front edge

FONT = {
    "B": ["1111.", "1...1", "1...1", "1111.", "1...1", "1...1", "1111."],
    "C": [".1111", "1....", "1....", "1....", "1....", "1....", ".1111"],
    "F": ["11111", "1....", "1....", "1111.", "1....", "1....", "1...."],
    "L": ["1....", "1....", "1....", "1....", "1....", "1....", "11111"],
    "R": ["1111.", "1...1", "1...1", "1111.", "1.1..", "1..1.", "1...1"],
}

# label -> tile origin (front-left corner); back = high Y
TILES = {
    "BL": (0.0, SPAN - TILE),
    "BR": (SPAN - TILE, SPAN - TILE),
    "C": ((SPAN - TILE) / 2, (SPAN - TILE) / 2),
    "FL": (0.0, 0.0),
    "FR": (SPAN - TILE, 0.0),
}


def label_cut(text, x0, y0):
    """Union of pixel boxes for `text`, front edge at y0, centered on x0."""
    width = len(text) * 5 * CELL + (len(text) - 1) * CELL
    left = x0 - width / 2
    boxes = []
    for n, ch in enumerate(text):
        for row, bits in enumerate(FONT[ch]):
            for col, bit in enumerate(bits):
                if bit == "1":
                    x = left + (n * 6 + col) * CELL
                    y = y0 + (6 - row) * CELL
                    # slight overlap so neighbouring pixels fuse into one stroke
                    boxes.append(Part.makeBox(CELL + 0.01, CELL + 0.01, HEIGHT + 2,
                                              Vector(x, y, -1)))
    cut = boxes[0]
    for b in boxes[1:]:
        cut = cut.fuse(b)
    return cut.removeSplitter()


shapes = []
for text, (tx, ty) in TILES.items():
    tile = Part.makeBox(TILE, TILE, HEIGHT, Vector(tx, ty, 0))
    shapes.append(tile.cut(label_cut(text, tx + TILE / 2, ty + MARGIN)).removeSplitter())

model = Part.makeCompound(shapes)
mesh = MeshPart.meshFromShape(Shape=model, LinearDeflection=0.01, AngularDeflection=0.1)
out = os.path.join(OUT_DIR, "first-layer-test-labeled.stl")
mesh.write(out)
print("wrote", out, "facets", mesh.CountFacets, "bbox", model.BoundBox)
for s in shapes:
    print("  tile volume", round(s.Volume, 2), "solid", s.isValid())
