from backend.supabase_client import supabase


DOCUMENT_ID = 1


# ============================================================
# FETCH PRODUCTS
# ============================================================

def fetch_products():

    response = (
        supabase
        .table("products")
        .select("id, product_code, page_number")
        .eq("document_id", DOCUMENT_ID)
        .order("page_number")
        .order("id")
        .execute()
    )

    return response.data or []


# ============================================================
# FETCH IMAGES
# ============================================================

def fetch_images():

    response = (
        supabase
        .table("product_images")
        .select("id, file_name, storage_path, document_id")
        .eq("document_id", DOCUMENT_ID)
        .order("id")
        .execute()
    )

    return response.data or []


# ============================================================
# EXTRACT PAGE NUMBER FROM FILE NAME
# ============================================================

def get_page_number(file_name):

    import re

    match = re.search(
        r"page_(\d+)_image_\d+",
        file_name,
        re.IGNORECASE
    )

    if not match:
        return None

    return int(match.group(1))


# ============================================================
# GROUP PRODUCTS BY PAGE
# ============================================================

def group_products_by_page(products):

    grouped = {}

    for product in products:

        page = product["page_number"]

        if page not in grouped:
            grouped[page] = []

        grouped[page].append(product)

    return grouped


# ============================================================
# GROUP IMAGES BY PAGE
# ============================================================

def group_images_by_page(images):

    grouped = {}

    for image in images:

        page = get_page_number(image["file_name"])

        if page is None:
            continue

        if page not in grouped:
            grouped[page] = []

        grouped[page].append(image)

    return grouped


# ============================================================
# CREATE PAGE-LEVEL MAPPINGS
# ============================================================

def create_mappings(products_by_page, images_by_page):

    mappings_created = 0
    mappings_existing = 0
    mappings_failed = 0

    print()
    print("=" * 70)
    print("CREATING PRODUCT-IMAGE PAGE MAPPINGS")
    print("=" * 70)

    for page_number in sorted(products_by_page.keys()):

        products = products_by_page.get(page_number, [])
        images = images_by_page.get(page_number, [])

        if not images:
            print()
            print(f"Page {page_number}: No images found")
            continue

        print()
        print(
            f"Page {page_number}: "
            f"{len(products)} products / "
            f"{len(images)} images"
        )

        for product in products:

            product_id = product["id"]
            product_code = product["product_code"]

            for image in images:

                image_id = image["id"]

                try:

                    existing = (
                        supabase
                        .table("product_image_map")
                        .select("id")
                        .eq("product_id", product_id)
                        .eq("image_id", image_id)
                        .execute()
                    )

                    if existing.data:

                        mappings_existing += 1

                        continue

                    (
                        supabase
                        .table("product_image_map")
                        .insert({
                            "product_id": product_id,
                            "image_id": image_id
                        })
                        .execute()
                    )

                    mappings_created += 1

                except Exception as e:

                    mappings_failed += 1

                    print(
                        f"ERROR: "
                        f"product={product_code}, "
                        f"image={image['file_name']}"
                    )

                    print(str(e))

    return (
        mappings_created,
        mappings_existing,
        mappings_failed
    )


# ============================================================
# VALIDATE RESULT
# ============================================================

def validate():

    print()
    print("=" * 70)
    print("VALIDATING PRODUCT-IMAGE MAPPINGS")
    print("=" * 70)

    response = (
        supabase
        .table("product_image_map")
        .select("id, product_id, image_id")
        .execute()
    )

    mappings = response.data or []

    print()
    print(f"Total mappings: {len(mappings)}")

    product_ids = set()
    image_ids = set()

    for mapping in mappings:

        product_ids.add(mapping["product_id"])
        image_ids.add(mapping["image_id"])

    print(f"Products with mappings: {len(product_ids)}")
    print(f"Images with mappings: {len(image_ids)}")

    return mappings


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("PRODUCT-IMAGE RELATIONSHIP PIPELINE")
    print("=" * 70)

    print()
    print("Fetching products...")

    products = fetch_products()

    print(f"Products found: {len(products)}")

    print()
    print("Fetching images...")

    images = fetch_images()

    print(f"Images found: {len(images)}")

    if not products:
        print()
        print("ERROR: No products found.")
        return

    if not images:
        print()
        print("ERROR: No images found.")
        return

    products_by_page = group_products_by_page(products)
    images_by_page = group_images_by_page(images)

    print()
    print("=" * 70)
    print("PAGE SUMMARY")
    print("=" * 70)

    for page in sorted(
        set(products_by_page.keys()) |
        set(images_by_page.keys())
    ):

        product_count = len(
            products_by_page.get(page, [])
        )

        image_count = len(
            images_by_page.get(page, [])
        )

        print(
            f"Page {page}: "
            f"{product_count} products | "
            f"{image_count} images"
        )

    (
        created,
        existing,
        failed
    ) = create_mappings(
        products_by_page,
        images_by_page
    )

    validate()

    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(f"Products:              {len(products)}")
    print(f"Images:                {len(images)}")
    print(f"Mappings created:      {created}")
    print(f"Mappings already exist: {existing}")
    print(f"Failed mappings:       {failed}")

    print()
    print("=" * 70)
    print("PIPELINE COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()