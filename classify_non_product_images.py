import sys
from pathlib import Path


# ============================================================
# ADD BACKEND TO PYTHON PATH
# ============================================================

PROJECT_DIR = Path(r"E:\OCR_Project")
BACKEND_DIR = PROJECT_DIR / "backend"

sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# IMPORT SUPABASE CONNECTION
# ============================================================

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1

PRODUCTS_TABLE = "products"
IMAGES_TABLE = "product_images"

DOCUMENT_IMAGE_TYPE = "document"


# ============================================================
# FETCH PRODUCTS
# ============================================================

def fetch_products():

    print("Fetching products...")

    response = (
        supabase
        .table(PRODUCTS_TABLE)
        .select("id, product_code, page_number")
        .eq("document_id", DOCUMENT_ID)
        .execute()
    )

    products = response.data or []

    print(f"Products found: {len(products)}")

    return products


# ============================================================
# FETCH ALL IMAGES
# ============================================================

def fetch_images():

    print("Fetching images...")

    response = (
        supabase
        .table(IMAGES_TABLE)
        .select(
            "id, product_id, image_type, storage_path, file_name"
        )
        .eq("document_id", DOCUMENT_ID)
        .order("id")
        .execute()
    )

    images = response.data or []

    print(f"Images found: {len(images)}")

    return images


# ============================================================
# EXTRACT PAGE NUMBER FROM FILE NAME
# ============================================================

def get_page_number(file_name):

    if not file_name:
        return None

    try:

        # Example:
        # page_09_image_01.jpeg
        # page_13_image_05.jpeg

        parts = file_name.split("_")

        if len(parts) >= 2 and parts[0].lower() == "page":

            return int(parts[1])

    except (ValueError, IndexError):

        pass

    return None


# ============================================================
# FIND PRODUCT PAGES
# ============================================================

def get_product_pages(products):

    product_pages = set()

    for product in products:

        page_number = product.get("page_number")

        if page_number is not None:

            product_pages.add(int(page_number))

    return product_pages


# ============================================================
# CLASSIFY NON-PRODUCT IMAGES
# ============================================================

def classify_images(images, product_pages):

    non_product_images = []

    product_page_images = []

    for image in images:

        file_name = image.get("file_name")

        page_number = get_page_number(file_name)

        if page_number is None:

            print(
                f"WARNING: Could not determine page number "
                f"for image ID={image.get('id')} "
                f"file={file_name}"
            )

            continue

        if page_number in product_pages:

            product_page_images.append(image)

        else:

            non_product_images.append(image)

    return product_page_images, non_product_images


# ============================================================
# UPDATE DOCUMENT IMAGES
# ============================================================

def update_document_images(non_product_images):

    updated = 0
    failed = 0

    print()
    print("=" * 80)
    print("CLASSIFYING NON-PRODUCT IMAGES")
    print("=" * 80)

    for image in non_product_images:

        image_id = image.get("id")
        file_name = image.get("file_name")

        try:

            response = (
                supabase
                .table(IMAGES_TABLE)
                .update({
                    "image_type": DOCUMENT_IMAGE_TYPE
                })
                .eq("id", image_id)
                .execute()
            )

            if response.data is not None:

                updated += 1

                page_number = get_page_number(file_name)

                print(
                    f"UPDATED | ID={image_id} | "
                    f"Page={page_number} | "
                    f"{file_name} | "
                    f"type=document"
                )

        except Exception as error:

            failed += 1

            print()
            print(
                f"ERROR | ID={image_id} | "
                f"File={file_name}"
            )

            print(error)

    return updated, failed


# ============================================================
# VERIFY RESULTS
# ============================================================

def verify_results():

    print()
    print("=" * 80)
    print("VERIFYING IMAGE CLASSIFICATION")
    print("=" * 80)

    response = (
        supabase
        .table(IMAGES_TABLE)
        .select("id, image_type, file_name")
        .eq("document_id", DOCUMENT_ID)
        .execute()
    )

    images = response.data or []

    product_count = 0
    document_count = 0
    other_count = 0

    for image in images:

        image_type = image.get("image_type")

        if image_type == "document":

            document_count += 1

        elif image_type == "product":

            product_count += 1

        else:

            other_count += 1

    print()
    print("IMAGE TYPE COUNTS")
    print("-" * 80)

    print(f"Total images:       {len(images)}")
    print(f"Product images:     {product_count}")
    print(f"Document images:    {document_count}")
    print(f"Other/NULL images:  {other_count}")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("CLASSIFY NON-PRODUCT IMAGES")
    print("=" * 80)
    print()

    # --------------------------------------------------------
    # FETCH PRODUCTS
    # --------------------------------------------------------

    products = fetch_products()

    # --------------------------------------------------------
    # FETCH IMAGES
    # --------------------------------------------------------

    images = fetch_images()

    # --------------------------------------------------------
    # DETERMINE PRODUCT PAGES
    # --------------------------------------------------------

    product_pages = get_product_pages(products)

    print()
    print("PRODUCT PAGES")
    print("-" * 80)

    for page in sorted(product_pages):

        print(f"Page {page}")

    print()
    print(f"Total product pages: {len(product_pages)}")

    # --------------------------------------------------------
    # CLASSIFY
    # --------------------------------------------------------

    product_page_images, non_product_images = (
        classify_images(
            images,
            product_pages
        )
    )

    print()
    print("=" * 80)
    print("CLASSIFICATION SUMMARY")
    print("=" * 80)

    print(
        f"Images on product pages:       "
        f"{len(product_page_images)}"
    )

    print(
        f"Images on non-product pages:   "
        f"{len(non_product_images)}"
    )

    # --------------------------------------------------------
    # SHOW NON-PRODUCT IMAGES
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("NON-PRODUCT IMAGES")
    print("=" * 80)

    for image in non_product_images:

        page_number = get_page_number(
            image.get("file_name")
        )

        print(
            f"ID={image.get('id')} | "
            f"Page={page_number} | "
            f"{image.get('file_name')}"
        )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    updated, failed = update_document_images(
        non_product_images
    )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print(
        f"Total images:                 {len(images)}"
    )

    print(
        f"Images on product pages:      "
        f"{len(product_page_images)}"
    )

    print(
        f"Non-product images:            "
        f"{len(non_product_images)}"
    )

    print(
        f"Document images updated:      {updated}"
    )

    print(
        f"Failed updates:               {failed}"
    )

    print("=" * 80)

    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    verify_results()

    print()
    print("=" * 80)
    print("CLASSIFICATION COMPLETED")
    print("=" * 80)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()