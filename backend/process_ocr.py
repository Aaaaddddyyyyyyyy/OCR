import re
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
from pytesseract import Output

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

PDF_PATH = Path(r"E:\OCR_Project\test.pdf")

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DOCUMENT_ID = 1

OCR_ENGINE = "tesseract"

DPI = 300

OCR_TABLE = "ocr_results"


# ============================================================
# CONFIGURE TESSERACT
# ============================================================

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


# ============================================================
# CHECK TESSERACT
# ============================================================

def check_tesseract():

    if not Path(TESSERACT_PATH).exists():

        print()
        print("ERROR: Tesseract not found:")
        print(TESSERACT_PATH)
        print()

        return False

    print(
        f"Tesseract: {TESSERACT_PATH}"
    )

    return True


# ============================================================
# CHECK PDF
# ============================================================

def check_pdf():

    if not PDF_PATH.exists():

        print()
        print("ERROR: PDF file not found:")
        print(PDF_PATH)
        print()

        return False

    print(
        f"PDF: {PDF_PATH}"
    )

    return True


# ============================================================
# GET PDF PAGE COUNT
# ============================================================

def get_page_count():

    try:

        document = pymupdf.open(
            PDF_PATH
        )

        page_count = len(
            document
        )

        document.close()

        return page_count

    except Exception as error:

        print()
        print("FAILED TO OPEN PDF")
        print(
            f"Error type: {type(error).__name__}"
        )
        print(
            f"Error: {error}"
        )
        print()

        return 0


# ============================================================
# CHECK EXISTING OCR RECORD
# ============================================================

def ocr_record_exists(page_number):

    try:

        response = (
            supabase
            .table(OCR_TABLE)
            .select("id")
            .eq(
                "document_id",
                DOCUMENT_ID
            )
            .eq(
                "page_number",
                page_number
            )
            .limit(1)
            .execute()
        )

        return len(
            response.data
        ) > 0

    except Exception as error:

        print()
        print("OCR DATABASE CHECK FAILED")
        print(
            f"Error type: {type(error).__name__}"
        )
        print(
            f"Error: {error}"
        )
        print()

        raise


# ============================================================
# RENDER PDF PAGE
# ============================================================

def render_page(page):

    try:

        scale = DPI / 72

        matrix = pymupdf.Matrix(
            scale,
            scale
        )

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image = Image.frombytes(
            "RGB",
            [
                pixmap.width,
                pixmap.height
            ],
            pixmap.samples
        )

        return image

    except Exception as error:

        print()
        print("PAGE RENDERING FAILED")
        print(
            f"Error type: {type(error).__name__}"
        )
        print(
            f"Error: {error}"
        )
        print()

        return None


# ============================================================
# RUN OCR ON COMPLETE PAGE
# ============================================================

def run_ocr(image):

    try:

        print(
            f"Rendered image size: {image.size}"
        )

        # ----------------------------------------------------
        # OCR TEXT
        # ----------------------------------------------------

        raw_text = pytesseract.image_to_string(
            image,
            config="--oem 3 --psm 6"
        )

        # ----------------------------------------------------
        # OCR DETAILED DATA
        # ----------------------------------------------------

        data = pytesseract.image_to_data(
            image,
            output_type=Output.DICT,
            config="--oem 3 --psm 6"
        )

        confidences = []

        bounding_boxes = []

        total_items = len(
            data["text"]
        )

        for i in range(total_items):

            word = data["text"][i].strip()

            confidence = data["conf"][i]

            try:

                confidence = float(
                    confidence
                )

            except (
                ValueError,
                TypeError
            ):

                continue

            if confidence < 0:

                continue

            if word:

                confidences.append(
                    confidence
                )

                bounding_boxes.append(
                    {
                        "text": word,
                        "confidence": confidence,
                        "left": int(
                            data["left"][i]
                        ),
                        "top": int(
                            data["top"][i]
                        ),
                        "width": int(
                            data["width"][i]
                        ),
                        "height": int(
                            data["height"][i]
                        )
                    }
                )

        # ----------------------------------------------------
        # AVERAGE CONFIDENCE
        # ----------------------------------------------------

        if confidences:

            average_confidence = (
                sum(confidences)
                / len(confidences)
            )

        else:

            average_confidence = 0.0

        return (
            raw_text.strip(),
            average_confidence,
            bounding_boxes
        )

    except Exception as error:

        print()
        print("OCR FAILED")
        print(
            f"Error type: {type(error).__name__}"
        )
        print(
            f"Error: {error}"
        )
        print()

        return None, None, None


# ============================================================
# INSERT OCR RESULT
# ============================================================

def insert_ocr_result(
    page_number,
    raw_text,
    average_confidence,
    bounding_boxes
):

    record = {

        "document_id":
            DOCUMENT_ID,

        "image_id":
            None,

        "page_number":
            page_number,

        "raw_text":
            raw_text,

        "ocr_engine":
            OCR_ENGINE,

        "average_confidence":
            average_confidence,

        "bounding_boxes":
            bounding_boxes
    }

    print()
    print("Database data:")
    print(
        f"Document ID: {DOCUMENT_ID}"
    )
    print(
        f"Page number: {page_number}"
    )
    print(
        f"Characters: {len(raw_text)}"
    )
    print(
        f"Average confidence: "
        f"{average_confidence:.2f}%"
    )
    print(
        f"Bounding boxes: "
        f"{len(bounding_boxes)}"
    )

    try:

        response = (
            supabase
            .table(OCR_TABLE)
            .insert(record)
            .execute()
        )

        return True

    except Exception as error:

        print()
        print("DATABASE INSERT FAILED")
        print(
            f"Error type: {type(error).__name__}"
        )
        print(
            f"Error: {error}"
        )
        print(
            f"Data sent: {record}"
        )
        print()

        return False


# ============================================================
# PROCESS ONE PAGE
# ============================================================

def process_page(
    document,
    page_index,
    total_pages
):

    page_number = page_index + 1

    print()
    print("=" * 60)

    print(
        f"PROCESSING PAGE "
        f"{page_number}/{total_pages}"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # CHECK EXISTING OCR
    # --------------------------------------------------------

    if ocr_record_exists(
        page_number
    ):

        print(
            "OCR RECORD: ALREADY EXISTS"
        )

        print(
            "SKIPPED"
        )

        return "skipped"

    # --------------------------------------------------------
    # GET PAGE
    # --------------------------------------------------------

    try:

        page = document[
            page_index
        ]

    except Exception as error:

        print()
        print("FAILED TO READ PAGE")
        print(error)

        return "failed"

    # --------------------------------------------------------
    # PAGE INFORMATION
    # --------------------------------------------------------

    page_rect = page.rect

    print(
        f"Original page size: "
        f"{page_rect.width:.2f} x "
        f"{page_rect.height:.2f}"
    )

    # --------------------------------------------------------
    # RENDER COMPLETE PAGE
    # --------------------------------------------------------

    image = render_page(
        page
    )

    if image is None:

        return "failed"

    # --------------------------------------------------------
    # RUN OCR
    # --------------------------------------------------------

    (
        raw_text,
        average_confidence,
        bounding_boxes
    ) = run_ocr(
        image
    )

    if raw_text is None:

        return "failed"

    # --------------------------------------------------------
    # DISPLAY OCR RESULT
    # --------------------------------------------------------

    print()
    print("-" * 60)
    print("OCR RESULT")
    print("-" * 60)

    print(raw_text)

    print("-" * 60)

    print(
        f"Characters: {len(raw_text)}"
    )

    print(
        f"Average confidence: "
        f"{average_confidence:.2f}%"
    )

    print(
        f"Bounding boxes: "
        f"{len(bounding_boxes)}"
    )

    # --------------------------------------------------------
    # INSERT DATABASE RECORD
    # --------------------------------------------------------

    success = insert_ocr_result(
        page_number,
        raw_text,
        average_confidence,
        bounding_boxes
    )

    if not success:

        return "failed"

    print()
    print(
        "DATABASE: OCR RECORD INSERTED"
    )

    return "success"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print(
        "PAGE-LEVEL PDF OCR -> SUPABASE"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # CHECK TESSERACT
    # --------------------------------------------------------

    if not check_tesseract():

        return

    # --------------------------------------------------------
    # CHECK PDF
    # --------------------------------------------------------

    if not check_pdf():

        return

    # --------------------------------------------------------
    # GET PAGE COUNT
    # --------------------------------------------------------

    total_pages = get_page_count()

    print(
        f"Total PDF pages: {total_pages}"
    )

    if total_pages == 0:

        print()
        print(
            "ERROR: PDF contains no pages."
        )

        return

    print(
        f"Rendering DPI: {DPI}"
    )

    print(
        f"Document ID: {DOCUMENT_ID}"
    )

    print(
        f"OCR table: {OCR_TABLE}"
    )

    # --------------------------------------------------------
    # OPEN PDF
    # --------------------------------------------------------

    try:

        document = pymupdf.open(
            PDF_PATH
        )

    except Exception as error:

        print()
        print("FAILED TO OPEN PDF")
        print(
            f"Error type: {type(error).__name__}"
        )
        print(
            f"Error: {error}"
        )
        print()

        return

    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    successful = 0

    skipped = 0

    failed = 0

    # --------------------------------------------------------
    # PROCESS EVERY PAGE
    # --------------------------------------------------------

    for page_index in range(
        total_pages
    ):

        result = process_page(
            document,
            page_index,
            total_pages
        )

        if result == "success":

            successful += 1

        elif result == "skipped":

            skipped += 1

        elif result == "failed":

            failed += 1

    # --------------------------------------------------------
    # CLOSE PDF
    # --------------------------------------------------------

    document.close()

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print("=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print(
        f"Total PDF pages:        {total_pages}"
    )

    print(
        f"OCR records inserted:   {successful}"
    )

    print(
        f"Existing pages skipped: {skipped}"
    )

    print(
        f"Failed pages:            {failed}"
    )

    print("=" * 60)

    if failed == 0:

        print(
            "PAGE-LEVEL OCR PIPELINE "
            "COMPLETED SUCCESSFULLY"
        )

    else:

        print(
            "PAGE-LEVEL OCR PIPELINE "
            "COMPLETED WITH ERRORS"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()