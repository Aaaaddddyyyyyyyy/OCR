import os
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from pytesseract import Output

from supabase_client import supabase


TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def calculate_average_confidence(data):
    confidences = []

    for confidence in data["conf"]:
        try:
            confidence = float(confidence)

            if confidence >= 0:
                confidences.append(confidence)

        except (ValueError, TypeError):
            continue

    if not confidences:
        return None

    return round(sum(confidences) / len(confidences), 2)


def process_pdf(document_id, pdf_path):

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    print(f"Processing document ID: {document_id}")
    print(f"PDF: {pdf_path}")

    pages = convert_from_path(
        str(pdf_path),
        dpi=200
    )

    page_count = len(pages)

    print(f"Total pages: {page_count}")

    # Update document information
    supabase.table("documents").update(
        {
            "page_count": page_count,
            "processing_status": "processing"
        }
    ).eq(
        "id",
        document_id
    ).execute()

    for page_number, page in enumerate(
        pages,
        start=1
    ):

        print(
            f"Processing page "
            f"{page_number}/{page_count}..."
        )

        data = pytesseract.image_to_data(
            page,
            output_type=Output.DICT
        )

        raw_text = pytesseract.image_to_string(
            page
        ).strip()

        average_confidence = (
            calculate_average_confidence(data)
        )

        ocr_record = {
            "document_id": document_id,
            "page_number": page_number,
            "raw_text": raw_text,
            "ocr_engine": "tesseract",
            "average_confidence": average_confidence
        }

        response = (
            supabase
            .table("ocr_results")
            .insert(ocr_record)
            .execute()
        )

        print(
            f"Page {page_number} saved."
        )

        print(
            f"Average confidence: "
            f"{average_confidence}"
        )

    # Mark processing as completed
    supabase.table("documents").update(
        {
            "processing_status": "completed"
        }
    ).eq(
        "id",
        document_id
    ).execute()

    print("\nOCR processing completed successfully.")


if __name__ == "__main__":

    DOCUMENT_ID = 1

    PDF_PATH = r"E:\OCR_Project\test.pdf"

    try:

        process_pdf(
            DOCUMENT_ID,
            PDF_PATH
        )

    except Exception as error:

        print("\nOCR processing failed!")

        print(error)

        try:
            supabase.table("documents").update(
                {
                    "processing_status": "failed"
                }
            ).eq(
                "id",
                DOCUMENT_ID
            ).execute()

        except Exception as update_error:

            print(
                "Could not update document status:"
            )

            print(update_error)