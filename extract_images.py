import mimetypes
from pathlib import Path

import fitz

from supabase_client import supabase


DOCUMENT_ID = 1
PDF_PATH = Path(r"E:\OCR_Project\test.pdf")
OUTPUT_DIR = Path(r"E:\OCR_Project\extracted_images")
STORAGE_BUCKET = "product-image"


def create_output_directory():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


def fetch_products():
    print(f"\nReading products for document {DOCUMENT_ID}...")
    response = (
        supabase.table("products")
        .select("id, product_code, product_name, page_number")
        .eq("document_id", DOCUMENT_ID)
        .order("page_number")
        .order("id")
        .execute()
    )
    products = response.data or []
    print(f"Found {len(products)} products.")
    return products


def find_product_for_page(products, page_number):
    page_products = [
        product for product in products if product.get("page_number") == page_number
    ]
    return page_products[0] if len(page_products) == 1 else None


def upload_image_to_storage(local_path, storage_path, mime_type):
    try:
        with open(local_path, "rb") as file:
            supabase.storage.from_(STORAGE_BUCKET).upload(
                storage_path,
                file.read(),
                {"content-type": mime_type, "upsert": True},
            )
        return True
    except Exception as error:
        print(f"Storage upload failed for {local_path.name}: {error}")
        return False


def image_record_exists(storage_path):
    try:
        response = (
            supabase.table("product_images")
            .select("id")
            .eq("storage_path", storage_path)
            .limit(1)
            .execute()
        )
        return bool(response.data)
    except Exception as error:
        print(f"Could not check existing image record: {error}")
        return False


def insert_image_record(product_id, storage_path, file_name, mime_type, width, height):
    return (
        supabase.table("product_images")
        .insert(
            {
                "product_id": product_id,
                "image_type": "product",
                "storage_path": storage_path,
                "file_name": file_name,
                "mime_type": mime_type,
                "width": width,
                "height": height,
            }
        )
        .execute()
        .data
    )


def extract_images():
    if not PDF_PATH.exists():
        print(f"ERROR: PDF not found: {PDF_PATH}")
        return

    create_output_directory()
    print(f"\nOpening PDF: {PDF_PATH}")
    products = fetch_products()

    total_images = total_uploaded = total_records = total_skipped = total_failed = 0

    try:
        pdf = fitz.open(PDF_PATH)
    except Exception as error:
        print(f"ERROR: Could not open PDF: {error}")
        return

    try:
        print(f"Total pages: {len(pdf)}")

        for page_number, page in enumerate(pdf, start=1):
            images = page.get_images(full=True)
            product = find_product_for_page(products, page_number)

            print("\n" + "-" * 60)
            print(f"Page {page_number}: {len(images)} embedded image(s)")
            print(
                f"Product: {product.get('product_code')}"
                if product
                else "Product: No unique product association found"
            )

            for image_index, image in enumerate(images, start=1):
                try:
                    image_data = pdf.extract_image(image[0])
                    image_bytes = image_data["image"]
                    extension = image_data["ext"]
                    width, height = image_data["width"], image_data["height"]
                    file_name = f"page_{page_number:02d}_image_{image_index:02d}.{extension}"
                    output_path = OUTPUT_DIR / file_name
                    output_path.write_bytes(image_bytes)
                    total_images += 1

                    mime_type = mimetypes.guess_type(file_name)[0] or f"image/{extension}"
                    storage_path = f"document_{DOCUMENT_ID}/page_{page_number:02d}/{file_name}"

                    print(f"Saved: {file_name} ({width}x{height})")

                    if image_record_exists(storage_path):
                        print("Database record already exists. Skipping upload.")
                        total_skipped += 1
                        continue

                    if not upload_image_to_storage(output_path, storage_path, mime_type):
                        total_failed += 1
                        continue

                    total_uploaded += 1
                    insert_image_record(
                        product_id=product.get("id") if product else None,
                        storage_path=storage_path,
                        file_name=file_name,
                        mime_type=mime_type,
                        width=width,
                        height=height,
                    )
                    total_records += 1
                    print(f"Uploaded and recorded: {storage_path}")

                except Exception as error:
                    print(f"Failed to process image {image_index} on page {page_number}: {error}")
                    total_failed += 1
    finally:
        pdf.close()

    print("\n" + "=" * 60)
    print(f"Total images extracted: {total_images}")
    print(f"Images uploaded: {total_uploaded}")
    print(f"Database records created: {total_records}")
    print(f"Existing records skipped: {total_skipped}")
    print(f"Failed operations: {total_failed}")
    print("=" * 60)


if __name__ == "__main__":
    extract_images()
