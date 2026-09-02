import sys
from pathlib import Path

# ============================================================
# ADD BACKEND DIRECTORY TO PYTHON PATH
# ============================================================

BACKEND_DIR = Path(__file__).parent / "backend"

sys.path.insert(
    0,
    str(BACKEND_DIR)
)

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1


# ============================================================
# FETCH PRODUCTS
# ============================================================

def fetch_products():

    response = (
        supabase
        .table("products")
        .select(
            "id, product_code, page_number, document_id"
        )
        .eq(
            "document_id",
            DOCUMENT_ID
        )
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
        .select(
            "id, product_id, image_type, "
            "storage_path, file_name, mime_type, "
            "width, height, created_at, document_id"
        )
        .eq(
            "document_id",
            DOCUMENT_ID
        )
        .execute()
    )

    return response.data or []


# ============================================================
# FETCH MAPPINGS
# ============================================================

def fetch_mappings():

    response = (
        supabase
        .table("product_image_map")
        .select(
            "id, product_id, image_id"
        )
        .execute()
    )

    return response.data or []


# ============================================================
# BASIC COUNTS
# ============================================================

def check_basic_counts(
    products,
    images,
    mappings
):

    print()
    print("=" * 70)
    print("BASIC COUNTS")
    print("=" * 70)

    mapped_product_ids = set()
    mapped_image_ids = set()

    for mapping in mappings:

        product_id = mapping.get(
            "product_id"
        )

        image_id = mapping.get(
            "image_id"
        )

        if product_id is not None:

            mapped_product_ids.add(
                product_id
            )

        if image_id is not None:

            mapped_image_ids.add(
                image_id
            )

    print(
        f"Products:              {len(products)}"
    )

    print(
        f"Images:                {len(images)}"
    )

    print(
        f"Mappings:              {len(mappings)}"
    )

    print(
        f"Products mapped:       {len(mapped_product_ids)}"
    )

    print(
        f"Unique images mapped:  {len(mapped_image_ids)}"
    )


# ============================================================
# CHECK UNMAPPED IMAGES
# ============================================================

def check_unmapped_images(
    images,
    mappings
):

    print()
    print("=" * 70)
    print("CHECKING UNMAPPED IMAGES")
    print("=" * 70)

    mapped_image_ids = set()

    for mapping in mappings:

        image_id = mapping.get(
            "image_id"
        )

        if image_id is not None:

            mapped_image_ids.add(
                image_id
            )

    unmapped_images = []

    for image in images:

        if image["id"] not in mapped_image_ids:

            unmapped_images.append(
                image
            )

    print(
        f"Total images:       {len(images)}"
    )

    print(
        f"Mapped images:      {len(mapped_image_ids)}"
    )

    print(
        f"Unmapped images:    {len(unmapped_images)}"
    )

    if not unmapped_images:

        print()
        print(
            "All images are mapped."
        )

    else:

        print()
        print(
            "UNMAPPED IMAGES"
        )

        print(
            "-" * 70
        )

        for image in unmapped_images:

            print(
                f"ID={image['id']} | "
                f"File={image['file_name']} | "
                f"Path={image['storage_path']}"
            )

    return unmapped_images


# ============================================================
# CHECK PRODUCTS WITHOUT MAPPINGS
# ============================================================

def check_unmapped_products(
    products,
    mappings
):

    print()
    print("=" * 70)
    print("CHECKING PRODUCTS WITHOUT IMAGE MAPPINGS")
    print("=" * 70)

    mapped_product_ids = set()

    for mapping in mappings:

        product_id = mapping.get(
            "product_id"
        )

        if product_id is not None:

            mapped_product_ids.add(
                product_id
            )

    unmapped_products = []

    for product in products:

        if product["id"] not in mapped_product_ids:

            unmapped_products.append(
                product
            )

    print(
        f"Products without mappings: "
        f"{len(unmapped_products)}"
    )

    if not unmapped_products:

        print()
        print(
            "All products have image mappings."
        )

    else:

        print()
        print(
            "PRODUCTS WITHOUT MAPPINGS"
        )

        print(
            "-" * 70
        )

        for product in unmapped_products:

            print(
                f"ID={product['id']} | "
                f"Product={product['product_code']} | "
                f"Page={product['page_number']}"
            )

    return unmapped_products


# ============================================================
# CHECK INVALID PRODUCT REFERENCES
# ============================================================

def check_invalid_product_references(
    products,
    mappings
):

    print()
    print("=" * 70)
    print("CHECKING INVALID PRODUCT REFERENCES")
    print("=" * 70)

    valid_product_ids = set()

    for product in products:

        valid_product_ids.add(
            product["id"]
        )

    invalid_mappings = []

    for mapping in mappings:

        product_id = mapping.get(
            "product_id"
        )

        if product_id not in valid_product_ids:

            invalid_mappings.append(
                mapping
            )

    print(
        f"Invalid product references: "
        f"{len(invalid_mappings)}"
    )

    if invalid_mappings:

        print()
        print(
            "INVALID PRODUCT REFERENCES"
        )

        print(
            "-" * 70
        )

        for mapping in invalid_mappings:

            print(
                f"Mapping ID={mapping['id']} | "
                f"Product ID={mapping['product_id']} | "
                f"Image ID={mapping['image_id']}"
            )

    else:

        print(
            "All mappings reference valid products."
        )


# ============================================================
# CHECK INVALID IMAGE REFERENCES
# ============================================================

def check_invalid_image_references(
    images,
    mappings
):

    print()
    print("=" * 70)
    print("CHECKING INVALID IMAGE REFERENCES")
    print("=" * 70)

    valid_image_ids = set()

    for image in images:

        valid_image_ids.add(
            image["id"]
        )

    invalid_mappings = []

    for mapping in mappings:

        image_id = mapping.get(
            "image_id"
        )

        if image_id not in valid_image_ids:

            invalid_mappings.append(
                mapping
            )

    print(
        f"Invalid image references: "
        f"{len(invalid_mappings)}"
    )

    if invalid_mappings:

        print()
        print(
            "INVALID IMAGE REFERENCES"
        )

        print(
            "-" * 70
        )

        for mapping in invalid_mappings:

            print(
                f"Mapping ID={mapping['id']} | "
                f"Product ID={mapping['product_id']} | "
                f"Image ID={mapping['image_id']}"
            )

    else:

        print(
            "All mappings reference valid images."
        )


# ============================================================
# CHECK DUPLICATE MAPPINGS
# ============================================================

def check_duplicate_mappings(
    mappings
):

    print()
    print("=" * 70)
    print("CHECKING DUPLICATE MAPPINGS")
    print("=" * 70)

    seen = set()
    duplicates = []

    for mapping in mappings:

        key = (
            mapping.get("product_id"),
            mapping.get("image_id")
        )

        if key in seen:

            duplicates.append(
                mapping
            )

        else:

            seen.add(
                key
            )

    print(
        f"Duplicate mappings: "
        f"{len(duplicates)}"
    )

    if duplicates:

        print()
        print(
            "DUPLICATE MAPPINGS"
        )

        print(
            "-" * 70
        )

        for mapping in duplicates:

            print(
                f"Mapping ID={mapping['id']} | "
                f"Product ID={mapping['product_id']} | "
                f"Image ID={mapping['image_id']}"
            )

    else:

        print(
            "No duplicate product-image mappings found."
        )


# ============================================================
# CHECK PAGE CONSISTENCY
# ============================================================

def check_page_consistency(
    products,
    images,
    mappings
):

    print()
    print("=" * 70)
    print("CHECKING PAGE CONSISTENCY")
    print("=" * 70)

    product_lookup = {}

    for product in products:

        product_lookup[
            product["id"]
        ] = product

    image_lookup = {}

    for image in images:

        image_lookup[
            image["id"]
        ] = image

    inconsistencies = []

    for mapping in mappings:

        product_id = mapping.get(
            "product_id"
        )

        image_id = mapping.get(
            "image_id"
        )

        product = product_lookup.get(
            product_id
        )

        image = image_lookup.get(
            image_id
        )

        if product is None:

            continue

        if image is None:

            continue

        product_page = product.get(
            "page_number"
        )

        image_file = image.get(
            "file_name",
            ""
        )

        if product_page is None:

            continue

        expected_page = (
            f"page_{int(product_page):02d}_"
        )

        if expected_page not in image_file:

            inconsistencies.append(
                {
                    "mapping_id": mapping["id"],
                    "product_id": product_id,
                    "product_code": product[
                        "product_code"
                    ],
                    "product_page": product_page,
                    "image_id": image_id,
                    "image_file": image_file
                }
            )

    print(
        f"Page inconsistencies: "
        f"{len(inconsistencies)}"
    )

    if inconsistencies:

        print()
        print(
            "PAGE INCONSISTENCIES"
        )

        print(
            "-" * 70
        )

        for item in inconsistencies:

            print(
                f"Mapping={item['mapping_id']} | "
                f"Product={item['product_code']} | "
                f"Product Page={item['product_page']} | "
                f"Image={item['image_file']}"
            )

    else:

        print(
            "All mappings have consistent page numbers."
        )


# ============================================================
# PRODUCT-WISE SUMMARY
# ============================================================

def product_wise_summary(
    products,
    mappings
):

    print()
    print("=" * 70)
    print("PRODUCT-WISE MAPPING SUMMARY")
    print("=" * 70)

    product_mapping_count = {}

    for mapping in mappings:

        product_id = mapping.get(
            "product_id"
        )

        if product_id not in product_mapping_count:

            product_mapping_count[
                product_id
            ] = 0

        product_mapping_count[
            product_id
        ] += 1

    print(
        f"{'ID':<5}"
        f"{'PRODUCT CODE':<35}"
        f"{'PAGE':<8}"
        f"{'MAPPINGS':<10}"
    )

    print(
        "-" * 70
    )

    for product in products:

        product_id = product["id"]

        count = product_mapping_count.get(
            product_id,
            0
        )

        print(
            f"{product_id:<5}"
            f"{product['product_code']:<35}"
            f"{str(product['page_number']):<8}"
            f"{count:<10}"
        )


# ============================================================
# PAGE-WISE SUMMARY
# ============================================================

def page_wise_summary(
    products,
    images,
    mappings
):

    print()
    print("=" * 70)
    print("PAGE-WISE MAPPING SUMMARY")
    print("=" * 70)

    product_lookup = {}

    for product in products:

        product_lookup[
            product["id"]
        ] = product

    image_lookup = {}

    for image in images:

        image_lookup[
            image["id"]
        ] = image

    page_data = {}

    for mapping in mappings:

        product = product_lookup.get(
            mapping.get("product_id")
        )

        image = image_lookup.get(
            mapping.get("image_id")
        )

        if product is None:

            continue

        if image is None:

            continue

        page = product.get(
            "page_number"
        )

        if page is None:

            continue

        if page not in page_data:

            page_data[page] = {
                "products": set(),
                "images": set(),
                "mappings": 0
            }

        page_data[
            page
        ]["products"].add(
            product["id"]
        )

        page_data[
            page
        ]["images"].add(
            image["id"]
        )

        page_data[
            page
        ]["mappings"] += 1

    print(
        f"{'PAGE':<10}"
        f"{'PRODUCTS':<12}"
        f"{'IMAGES':<12}"
        f"{'MAPPINGS':<12}"
    )

    print(
        "-" * 50
    )

    for page in sorted(page_data):

        data = page_data[page]

        print(
            f"{page:<10}"
            f"{len(data['products']):<12}"
            f"{len(data['images']):<12}"
            f"{data['mappings']:<12}"
        )


# ============================================================
# CHECK EXPECTED MAPPING COUNT
# ============================================================

def check_expected_mapping_count(
    products,
    mappings
):

    print()
    print("=" * 70)
    print("CHECKING MAPPING COUNTS")
    print("=" * 70)

    product_mapping_count = {}

    for mapping in mappings:

        product_id = mapping.get(
            "product_id"
        )

        if product_id is None:

            continue

        product_mapping_count[
            product_id
        ] = (
            product_mapping_count.get(
                product_id,
                0
            ) + 1
        )

    products_without_mapping = 0

    for product in products:

        count = product_mapping_count.get(
            product["id"],
            0
        )

        if count == 0:

            products_without_mapping += 1

        print(
            f"{product['product_code']}: "
            f"{count} image mappings"
        )

    print()

    print(
        f"Products without mappings: "
        f"{products_without_mapping}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

def final_summary(
    products,
    images,
    mappings,
    unmapped_images,
    unmapped_products
):

    mapped_product_ids = set()
    mapped_image_ids = set()

    for mapping in mappings:

        product_id = mapping.get(
            "product_id"
        )

        image_id = mapping.get(
            "image_id"
        )

        if product_id is not None:

            mapped_product_ids.add(
                product_id
            )

        if image_id is not None:

            mapped_image_ids.add(
                image_id
            )

    print()
    print("=" * 70)
    print("FINAL VERIFICATION SUMMARY")
    print("=" * 70)

    print(
        f"Products:              {len(products)}"
    )

    print(
        f"Images:                {len(images)}"
    )

    print(
        f"Total mappings:        {len(mappings)}"
    )

    print(
        f"Products mapped:       {len(mapped_product_ids)}"
    )

    print(
        f"Unique images mapped:  {len(mapped_image_ids)}"
    )

    print(
        f"Unmapped images:       {len(unmapped_images)}"
    )

    print(
        f"Unmapped products:     {len(unmapped_products)}"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("PRODUCT IMAGE MAPPING VERIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # FETCH PRODUCTS
    # --------------------------------------------------------

    print()
    print("Fetching products...")

    products = fetch_products()

    print(
        f"Products found: {len(products)}"
    )

    # --------------------------------------------------------
    # FETCH IMAGES
    # --------------------------------------------------------

    print()
    print("Fetching images...")

    images = fetch_images()

    print(
        f"Images found: {len(images)}"
    )

    # --------------------------------------------------------
    # FETCH MAPPINGS
    # --------------------------------------------------------

    print()
    print("Fetching mappings...")

    mappings = fetch_mappings()

    print(
        f"Mappings found: {len(mappings)}"
    )

    # --------------------------------------------------------
    # VALIDATIONS
    # --------------------------------------------------------

    check_basic_counts(
        products,
        images,
        mappings
    )

    unmapped_images = check_unmapped_images(
        images,
        mappings
    )

    unmapped_products = check_unmapped_products(
        products,
        mappings
    )

    check_invalid_product_references(
        products,
        mappings
    )

    check_invalid_image_references(
        images,
        mappings
    )

    check_duplicate_mappings(
        mappings
    )

    check_page_consistency(
        products,
        images,
        mappings
    )

    check_expected_mapping_count(
        products,
        mappings
    )

    product_wise_summary(
        products,
        mappings
    )

    page_wise_summary(
        products,
        images,
        mappings
    )

    final_summary(
        products,
        images,
        mappings,
        unmapped_images,
        unmapped_products
    )

    print()
    print("=" * 70)
    print("VERIFICATION COMPLETED")
    print("=" * 70)


# ============================================================
# RUN SCRIPT
# ============================================================

if __name__ == "__main__":

    main()