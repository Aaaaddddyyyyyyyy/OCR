import fitz
from pathlib import Path


PDF_PATH = Path(r"E:\OCR_Project\test.pdf")

doc = fitz.open(PDF_PATH)

# Page 9 = index 8
page = doc[8]

print("=" * 80)
print("PAGE 9 PDF IMAGE INFORMATION")
print("=" * 80)

images = page.get_images(full=True)

print(f"\nTotal PDF image objects: {len(images)}\n")

for index, img in enumerate(images, start=1):

    xref = img[0]

    print("-" * 80)
    print(f"PDF IMAGE #{index}")
    print(f"XREF: {xref}")

    try:
        rects = page.get_image_rects(xref)

        print(f"Rectangles: {len(rects)}")

        for rect_no, rect in enumerate(rects, start=1):
            print(
                f"  Rect {rect_no}: "
                f"x0={rect.x0:.2f}, "
                f"y0={rect.y0:.2f}, "
                f"x1={rect.x1:.2f}, "
                f"y1={rect.y1:.2f}"
            )

            print(
                f"  Center: "
                f"x={(rect.x0 + rect.x1) / 2:.2f}, "
                f"y={(rect.y0 + rect.y1) / 2:.2f}"
            )

    except Exception as e:
        print(f"ERROR getting rectangle: {e}")


print("\n" + "=" * 80)
print("PAGE SIZE")
print("=" * 80)

print(f"Width : {page.rect.width:.2f}")
print(f"Height: {page.rect.height:.2f}")

doc.close()