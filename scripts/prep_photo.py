#!/usr/bin/env python3
"""
Prep a source photo so it converts to readable ASCII art.

A flatly-lit face converts to a dark, unreadable blob, so this does three
things first:
  1. Remove the background (rembg) so only the subject remains.
  2. Boost local contrast with CLAHE — gives a flat face real highlights
     and shadows.
  3. Composite onto pure white so the background maps to the blank end of
     the ASCII ramp (white -> spaces).

Run this once per photo:
    python scripts/prep_photo.py source-photo.jpg
Output: source-prepped.png (grayscale), next to the input file.
"""
import sys
import os

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep(input_path: str) -> str:
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    # 1. Remove background -> RGBA with subject isolated
    cutout_bytes = remove(input_bytes)
    cutout = Image.open(__import__("io").BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Composite onto pure white
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("L")

    # 3. CLAHE contrast boost (needs a numpy array / OpenCV)
    arr = np.array(composited)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    boosted = clahe.apply(arr)

    out_img = Image.fromarray(boosted)
    out_path = os.path.splitext(input_path)[0] + "-prepped.png"
    out_img.save(out_path)
    return out_path


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/prep_photo.py <photo.jpg>", file=sys.stderr)
        sys.exit(1)
    out_path = prep(sys.argv[1])
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
