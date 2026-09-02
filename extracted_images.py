from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import math


# ============================================================
# CONFIGURATION
# ============================================================

IMAGE_DIR = Path(r"E:\OCR_Project\extracted_images")
OUTPUT_FILE = Path(r"E:\OCR_Project\page_09_contact_sheet.jpg")

images = sorted(
    [
        p for p in IMAGE_DIR.iterdir()
        if p.name.startswith("page_09_image_")
    ],
    key=lambda p: int(
        p.stem.split("_")[-1]
    )
)

print(f"Found {len(images)} images")


# ============================================================
# CONTACT SHEET SETTINGS
# ============================================================

THUMB_WIDTH = 220
THUMB_HEIGHT = 220

LABEL_HEIGHT = 40

COLUMNS = 4
ROWS = math.ceil(len(images) / COLUMNS)

CELL_WIDTH = THUMB_WIDTH
CELL_HEIGHT = THUMB_HEIGHT + LABEL_HEIGHT

SHEET_WIDTH = COLUMNS * CELL_WIDTH
SHEET_HEIGHT = ROWS * CELL_HEIGHT


# ============================================================
# CREATE SHEET
# ============================================================

sheet = Image.new(
    "RGB",
    (SHEET_WIDTH, SHEET_HEIGHT),
    "white"
)

draw = ImageDraw.Draw(sheet)


# ============================================================
# ADD IMAGES
# ============================================================

for index, image_path in enumerate(images):

    try:
        img = Image.open(image_path).convert("RGB")

        # Keep aspect ratio
        img.thumbnail(
            (THUMB_WIDTH - 20, THUMB_HEIGHT - 20)
        )

        x = (index % COLUMNS) * CELL_WIDTH
        y = (index // COLUMNS) * CELL_HEIGHT

        # Center image
        image_x = x + (CELL_WIDTH - img.width) // 2
        image_y = y + 10 + (THUMB_HEIGHT - img.height) // 2

        sheet.paste(img, (image_x, image_y))

        # Label
        label = f"{index + 1}: {image_path.name}"

        draw.text(
            (x + 5, y + THUMB_HEIGHT + 5),
            label,
            fill="black"
        )

    except Exception as e:
        print(f"ERROR: {image_path.name} -> {e}")


# ============================================================
# SAVE
# ============================================================

sheet.save(
    OUTPUT_FILE,
    quality=95
)

print()
print("Contact sheet created:")
print(OUTPUT_FILE)