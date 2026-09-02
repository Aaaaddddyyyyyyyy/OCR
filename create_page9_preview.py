from PIL import Image, ImageDraw
from pathlib import Path

INPUT_DIR = Path(r"E:\OCR_Project\page9_product_images")
OUTPUT = Path(r"E:\OCR_Project\page9_product_images\all_7_preview.png")

files = sorted(INPUT_DIR.glob("*.png"))

images = []

for file in files:
    if file.name == "all_7_preview.png":
        continue

    img = Image.open(file).convert("RGB")

    # Enlarge small images for easier visual inspection
    scale = 3
    img = img.resize(
        (img.width * scale, img.height * scale)
    )

    images.append((file.name, img))

padding = 30
label_height = 50
columns = 4
rows = (len(images) + columns - 1) // columns

cell_width = max(img.width for _, img in images) + padding * 2
cell_height = max(img.height for _, img in images) + label_height + padding * 2

canvas = Image.new(
    "RGB",
    (columns * cell_width, rows * cell_height),
    "white"
)

draw = ImageDraw.Draw(canvas)

for i, (name, img) in enumerate(images):

    row = i // columns
    col = i % columns

    x = col * cell_width + padding
    y = row * cell_height + padding

    draw.text(
        (x, y),
        name,
        fill="black"
    )

    canvas.paste(
        img,
        (x, y + label_height)
    )

canvas.save(OUTPUT)

print(f"Created: {OUTPUT}")