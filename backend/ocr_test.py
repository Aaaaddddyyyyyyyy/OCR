import pytesseract
from pdf2image import convert_from_path


PDF_PATH = r"E:\OCR_Project\test.pdf"

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_text_from_pdf(pdf_path):

    print("Converting PDF pages to images...")

    pages = convert_from_path(pdf_path, dpi=200)

    print(f"Total pages found: {len(pages)}")

    for page_number, page in enumerate(pages, start=1):

        print(f"\nProcessing page {page_number}...")

        text = pytesseract.image_to_string(page)

        print("=" * 60)
        print(text)
        print("=" * 60)


if __name__ == "__main__":

    extract_text_from_pdf(PDF_PATH)