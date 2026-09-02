from pathlib import Path

import pytesseract
from PIL import Image


# ============================================================
# CONFIGURATION
# ============================================================

IMAGE_DIR = Path(r"E:\OCR_Project\extracted_images")

# Change this only if your Tesseract is installed elsewhere.
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ============================================================
# FIND FIRST IMAGE
# ============================================================

def find_first_image():

    if not IMAGE_DIR.exists():
        print("ERROR: Image directory does not exist:")
        print(IMAGE_DIR)
        return None

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff"
    }

    images = [
        file
        for file in IMAGE_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in image_extensions
    ]

    images.sort()

    if not images:
        print("ERROR: No images found.")
        return None

    return images[0]


# ============================================================
# TEST TESSERACT
# ============================================================

def test_ocr(image_path):

    print()
    print("=" * 60)
    print("OCR TEST")
    print("=" * 60)

    print(f"Image: {image_path}")

    # --------------------------------------------------------
    # Configure Tesseract
    # --------------------------------------------------------

    if not Path(TESSERACT_PATH).exists():

        print()
        print("ERROR: Tesseract executable not found:")
        print(TESSERACT_PATH)

        return False

    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

    # --------------------------------------------------------
    # Open image
    # --------------------------------------------------------

    try:

        image = Image.open(image_path)

        print(f"Image size: {image.size}")
        print(f"Image format: {image.format}")

    except Exception as e:

        print()
        print("IMAGE OPEN FAILED")
        print(e)

        return False

    # --------------------------------------------------------
    # Run OCR
    # --------------------------------------------------------

    try:

        text = pytesseract.image_to_string(
            image,
            config="--psm 6"
        )

    except Exception as e:

        print()
        print("OCR FAILED")
        print(e)

        return False

    # --------------------------------------------------------
    # Display result
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("OCR RESULT")
    print("=" * 60)

    print(text)

    print("=" * 60)

    if text.strip():

        print("OCR TEST: SUCCESS")

        return True

    else:

        print("OCR TEST: COMPLETED BUT NO TEXT FOUND")

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("TESSERACT OCR SINGLE IMAGE TEST")
    print("=" * 60)

    image_path = find_first_image()

    if image_path is None:

        print()
        print("TEST FAILED AT IMAGE SEARCH")

        return

    success = test_ocr(image_path)

    print()
    print("=" * 60)

    if success:

        print("FINAL RESULT")
        print("OCR PIPELINE TEST PASSED")

    else:

        print("FINAL RESULT")
        print("OCR PIPELINE TEST FAILED")

    print("=" * 60)


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()