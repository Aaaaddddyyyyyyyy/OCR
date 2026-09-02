import pymupdf
from pathlib import Path

PDF_PATH = r"E:\OCR_Project\test.pdf"
OUTPUT_DIR = Path(r"E:\OCR_Project\page9_product_images")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

XREFS = {
    140: "image_01_xref140.png",
    141: "image_02_xref141.png",
    142: "image_03_xref142.png",
    143: "image_04_xref143.png",
    147: "image_05_xref147.png",
    148: "image_06_xref148.png",
    149: "image_07_xref149.png",
}

doc = pymupdf.open(PDF_PATH)

print("=" * 80)
print("PAGE 9 PRODUCT IMAGE EXTRACTION")
print("=" * 80)

for xref, filename in XREFS.items():

    try:
        # Extract embedded image
        image_data = doc.extract_image(xref)

        if not image_data:
            print(f"ERROR: No image data for XREF {xref}")
            continue

        image_bytes = image_data["image"]
        extension = image_data["ext"]

        print(f"\nXREF {xref}")
        print(f"  Original format : {extension}")
        print(f"  Original size   : {image_data['width']} x {image_data['height']}")

        # --------------------------------------------------------
        # Open extracted image through PyMuPDF
        # --------------------------------------------------------
        pix = pymupdf.Pixmap(image_bytes)

        # --------------------------------------------------------
        # Convert unusual colorspace → RGB
        # --------------------------------------------------------
        if pix.colorspace is None:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

        elif pix.colorspace.n != 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

        # --------------------------------------------------------
        # Remove alpha if present
        # --------------------------------------------------------
        if pix.alpha:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

        output_path = OUTPUT_DIR / filename

        pix.save(str(output_path))

        print(f"  Saved           : {output_path}")
        print(f"  Final size      : {pix.width} x {pix.height}")

        pix = None

    except Exception as e:
        print(f"ERROR extracting XREF {xref}: {e}")

doc.close()

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)