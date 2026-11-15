"""A contact sheet of stills, to look over many moments at once: python sheet.py out.jpg t1 t2 ..."""
import sys
from PIL import Image
out, names = sys.argv[1], sys.argv[2:]
cols = 2
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 960, rows * 540), "black")
for i, n in enumerate(names):
    sheet.paste(Image.open(f"stills/t{float(n):05.1f}.jpg").resize((960, 540), Image.LANCZOS), ((i % cols) * 960, (i // cols) * 540))
sheet.save(out, quality=82)
