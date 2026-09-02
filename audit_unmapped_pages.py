from pathlib import Path
import sys


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# SUPABASE CONNECTION
# ============================================================

try:
    from supabase_client import supabase
except ModuleNotFoundError:
    print("ERROR: supabase_client.py not found.")
    print(f"Expected location: {BACKEND_DIR / 'supabase_client.py'}")
    sys.exit(1)


# ============================================================
# TABLE NAMES
# ============================================================

PRODUCTS_TABLE = "products"
OCR_TABLE = "ocr_results"
IMAGES_TABLE = "product_images"
MAPPING_TABLE = "product_image_map"


# ============================================================
# DOCUMENT
# ============================================================

DOCUMENT_ID = 1


# ============================================================
# FETCH PRODUCTS
# ============================================================

def fetch_products():

    print("Fetching products...")

    response = (
        supabase
        .table(PRODUCTS_TABLE)
        .select("id, product_code, product_name, page_number")
        .eq("document_id", DOCUMENT_ID)
        .order("page_number")
        .execute()
    )

    products = response.data or []

    print(f"Products found: {len(products)}")

    return products


# ============================================================
# FETCH OCR RESULTS
# ============================================================

def fetch_ocr_results():

    print("Fetching OCR results...")

    response = (
        supabase
        .table(OCR_TABLE)
        .select("id, page_number, raw_text")
        .eq("document_id", DOCUMENT_ID)
        .order("page_number")
        .execute()
    )

    ocr_results = response.data or []

    print(f"OCR records found: {len(ocr_results)}")

    return ocr_results


# ============================================================
# FETCH IMAGES
# ============================================================

def fetch_images():

    print("Fetching images...")

    response = (
        supabase
        .table(IMAGES_TABLE)
        .select("id, file_name, storage_path, document_id")
        .eq("document_id", DOCUMENT_ID)
        .order("id")
        .execute()
    )

    images = response.data or []

    print(f"Images found: {len(images)}")

    return images


# ============================================================
# FETCH MAPPINGS
# ============================================================

def fetch_mappings():

    print("Fetching mappings...")

    response = (
        supabase
        .table(MAPPING_TABLE)
        .select("product_id, image_id")
        .execute()
    )

    mappings = response.data or []

    print(f"Mappings found: {len(mappings)}")

    return mappings


# ============================================================
# EXTRACT PAGE NUMBER FROM IMAGE NAME
# ============================================================

def get_page_number(file_name):

    try:

        parts = file_name.split("_")

        for part in parts:

            if part.isdigit():
                return int(part)

    except Exception:
        pass

    return None


# ============================================================
# BUILD PRODUCT PAGE MAP
# ============================================================

def build_product_page_map(products):

    product_pages = {}

    for product in products:

        page = product.get("page_number")

        if page is None:
            continue

        product_pages.setdefault(page, []).append(product)

    return product_pages


# ============================================================
# BUILD OCR PAGE MAP
# ============================================================

def build_ocr_page_map(ocr_results):

    ocr_pages = {}

    for record in ocr_results:

        page = record.get("page_number")

        if page is None:
            continue

        raw_text = record.get("raw_text") or ""

        ocr_pages[page] = raw_text

    return ocr_pages


# ============================================================
# BUILD IMAGE PAGE MAP
# ============================================================

def build_image_page_map(images):

    image_pages = {}

    for image in images:

        file_name = image.get("file_name") or ""

        page = get_page_number(file_name)

        if page is None:
            continue

        image_pages.setdefault(page, []).append(image)

    return image_pages


# ============================================================
# BUILD MAPPED IMAGE SET
# ============================================================

def build_mapped_image_set(mappings):

    mapped_image_ids = set()

    for mapping in mappings:

        image_id = mapping.get("image_id")

        if image_id is not None:
            mapped_image_ids.add(image_id)

    return mapped_image_ids


# ============================================================
# AUDIT PAGES
# ============================================================

def audit_pages(
    product_pages,
    ocr_pages,
    image_pages,
    mapped_image_ids
):

    all_pages = set()

    all_pages.update(product_pages.keys())
    all_pages.update(ocr_pages.keys())
    all_pages.update(image_pages.keys())

    all_pages = sorted(all_pages)

    print()
    print("=" * 90)
    print("PAGE-BY-PAGE AUDIT")
    print("=" * 90)

    for page in all_pages:

        products = product_pages.get(page, [])
        images = image_pages.get(page, [])
        ocr_text = ocr_pages.get(page, "")

        mapped_images = [
            image
            for image in images
            if image.get("id") in mapped_image_ids
        ]

        unmapped_images = [
            image
            for image in images
            if image.get("id") not in mapped_image_ids
        ]

        print()
        print("-" * 90)
        print(f"PAGE {page}")
        print("-" * 90)

        print(f"Products: {len(products)}")
        print(f"Images: {len(images)}")
        print(f"Mapped images: {len(mapped_images)}")
        print(f"Unmapped images: {len(unmapped_images)}")

        # ----------------------------------------------------
        # PRODUCTS
        # ----------------------------------------------------

        if products:

            print()
            print("PRODUCTS:")

            for product in products:

                product_id = product.get("id")
                product_code = product.get("product_code")
                product_name = product.get("product_name")

                print(
                    f"  ID={product_id} | "
                    f"Code={product_code} | "
                    f"Name={product_name}"
                )

        else:

            print()
            print("PRODUCTS:")
            print("  NONE")

        # ----------------------------------------------------
        # IMAGES
        # ----------------------------------------------------

        if images:

            print()
            print("IMAGES:")

            for image in images:

                image_id = image.get("id")
                file_name = image.get("file_name")

                status = (
                    "MAPPED"
                    if image_id in mapped_image_ids
                    else "UNMAPPED"
                )

                print(
                    f"  ID={image_id} | "
                    f"{file_name} | "
                    f"{status}"
                )

        else:

            print()
            print("IMAGES:")
            print("  NONE")

        # ----------------------------------------------------
        # OCR PREVIEW
        # ----------------------------------------------------

        print()
        print("OCR TEXT PREVIEW:")

        cleaned_text = " ".join(ocr_text.split())

        if cleaned_text:

            if len(cleaned_text) > 500:
                cleaned_text = cleaned_text[:500] + "..."

            print(f"  {cleaned_text}")

        else:

            print("  NO OCR TEXT")

    print()
    print("=" * 90)
    print("PAGE-BY-PAGE AUDIT COMPLETED")
    print("=" * 90)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 90)
    print("AUDIT UNMAPPED IMAGE PAGES")
    print("=" * 90)
    print()

    products = fetch_products()

    ocr_results = fetch_ocr_results()

    images = fetch_images()

    mappings = fetch_mappings()

    product_pages = build_product_page_map(products)

    ocr_pages = build_ocr_page_map(ocr_results)

    image_pages = build_image_page_map(images)

    mapped_image_ids = build_mapped_image_set(mappings)

    audit_pages(
        product_pages,
        ocr_pages,
        image_pages,
        mapped_image_ids
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()