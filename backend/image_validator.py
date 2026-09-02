from collections import Counter

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1
EXPECTED_IMAGE_COUNT = 116


# ============================================================
# HELPER
# ============================================================

def is_empty(value):
    return value is None or str(value).strip() == ""


def print_separator():
    print("-" * 60)


# ============================================================
# FETCH PRODUCTS
# ============================================================

def fetch_products():
    print(f"Reading products for document {DOCUMENT_ID}...")

    response = (
        supabase
        .table("products")
        .select("id, document_id, page_number, product_code")
        .eq("document_id", DOCUMENT_ID)
        .execute()
    )

    products = response.data or []

    print(f"Found {len(products)} products.")

    return products


# ============================================================
# FETCH PRODUCT IMAGES
# ============================================================

def fetch_images(product_ids):
    if not product_ids:
        print("No product IDs available.")
        return []

    print()
    print("Reading product images...")

    response = (
        supabase
        .table("product_images")
        .select(
            "id, product_id, image_type, storage_path, "
            "file_name, mime_type, width, height, created_at"
        )
        .in_("product_id", product_ids)
        .execute()
    )

    images = response.data or []

    print(f"Found {len(images)} product images.")

    return images


# ============================================================
# REQUIRED FIELD VALIDATION
# ============================================================

def validate_required_fields(images):
    print()
    print("=" * 60)
    print("CHECKING REQUIRED FIELDS")
    print("=" * 60)

    required_fields = [
        "id",
        "product_id",
        "image_type",
        "storage_path",
        "file_name",
        "mime_type",
    ]

    total_issues = 0

    for image in images:
        issues = []

        for field in required_fields:
            if field not in image or is_empty(image.get(field)):
                issues.append(f"{field} is missing")

        if issues:
            total_issues += len(issues)

            print()
            print(f"Image ID: {image.get('id')}")

            for issue in issues:
                print(f"  - {issue}")

    if total_issues == 0:
        print("All required fields are present.")
    else:
        print()
        print(f"Total required-field issues: {total_issues}")

    return total_issues


# ============================================================
# PRODUCT RELATION VALIDATION
# ============================================================

def validate_product_relationship(images, products):
    print()
    print("=" * 60)
    print("CHECKING PRODUCT RELATIONSHIPS")
    print("=" * 60)

    product_ids = {
        product["id"]
        for product in products
        if product.get("id") is not None
    }

    orphan_images = []

    for image in images:
        product_id = image.get("product_id")

        if product_id not in product_ids:
            orphan_images.append(image)

    if not orphan_images:
        print(
            "All images are correctly linked "
            "to products belonging to document "
            f"{DOCUMENT_ID}."
        )
    else:
        print(
            f"Orphan/wrong-product images: "
            f"{len(orphan_images)}"
        )

        for image in orphan_images:
            print(
                f"  Image ID: {image.get('id')} | "
                f"Product ID: {image.get('product_id')}"
            )

    return len(orphan_images)


# ============================================================
# DUPLICATE IMAGE CHECK
# ============================================================

def validate_duplicates(images):
    print()
    print("=" * 60)
    print("CHECKING DUPLICATES")
    print("=" * 60)

    # storage_path should normally uniquely identify
    # the stored image.
    storage_paths = []

    for image in images:
        storage_path = image.get("storage_path")

        if not is_empty(storage_path):
            storage_paths.append(
                str(storage_path).strip()
            )

    counts = Counter(storage_paths)

    duplicates = {
        path: count
        for path, count in counts.items()
        if count > 1
    }

    if not duplicates:
        print("No duplicate storage paths found.")
    else:
        print(
            f"Duplicate storage paths found: "
            f"{len(duplicates)}"
        )

        for path, count in duplicates.items():
            print(
                f"  {path} -> {count} records"
            )

    return len(duplicates)


# ============================================================
# FILE NAME CHECK
# ============================================================

def validate_file_names(images):
    print()
    print("=" * 60)
    print("CHECKING FILE NAMES")
    print("=" * 60)

    missing_names = []

    for image in images:
        file_name = image.get("file_name")

        if is_empty(file_name):
            missing_names.append(image)

    if not missing_names:
        print("All images have file names.")
    else:
        print(
            f"Images with missing file names: "
            f"{len(missing_names)}"
        )

        for image in missing_names:
            print(
                f"  Image ID: {image.get('id')}"
            )

    return len(missing_names)


# ============================================================
# MIME TYPE CHECK
# ============================================================

def validate_mime_types(images):
    print()
    print("=" * 60)
    print("CHECKING MIME TYPES")
    print("=" * 60)

    valid_mime_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/bmp",
        "image/tiff",
        "image/svg+xml",
    }

    invalid_images = []

    for image in images:
        mime_type = image.get("mime_type")

        if is_empty(mime_type):
            continue

        if str(mime_type).lower().strip() not in valid_mime_types:
            invalid_images.append(image)

    if not invalid_images:
        print("All MIME types are valid.")
    else:
        print(
            f"Images with unusual MIME types: "
            f"{len(invalid_images)}"
        )

        for image in invalid_images:
            print(
                f"  Image ID: {image.get('id')} | "
                f"MIME: {image.get('mime_type')}"
            )

    return len(invalid_images)


# ============================================================
# DIMENSION CHECK
# ============================================================

def validate_dimensions(images):
    print()
    print("=" * 60)
    print("CHECKING IMAGE DIMENSIONS")
    print("=" * 60)

    invalid_dimensions = []

    for image in images:
        width = image.get("width")
        height = image.get("height")

        # If dimensions are NULL, report them.
        if width is None or height is None:
            invalid_dimensions.append(image)
            continue

        try:
            width = int(width)
            height = int(height)

            if width <= 0 or height <= 0:
                invalid_dimensions.append(image)

        except (TypeError, ValueError):
            invalid_dimensions.append(image)

    if not invalid_dimensions:
        print("All image dimensions are valid.")
    else:
        print(
            f"Images with invalid dimensions: "
            f"{len(invalid_dimensions)}"
        )

        for image in invalid_dimensions:
            print(
                f"  Image ID: {image.get('id')} | "
                f"Width: {image.get('width')} | "
                f"Height: {image.get('height')}"
            )

    return len(invalid_dimensions)


# ============================================================
# IMAGE TYPE DISTRIBUTION
# ============================================================

def show_image_type_distribution(images):
    print()
    print("=" * 60)
    print("IMAGE TYPE DISTRIBUTION")
    print("=" * 60)

    counts = Counter()

    for image in images:
        image_type = image.get("image_type")

        if is_empty(image_type):
            image_type = "UNKNOWN"

        counts[str(image_type)] += 1

    if not counts:
        print("No image types available.")
        return

    for image_type, count in sorted(counts.items()):
        print(
            f"{image_type}: {count}"
        )


# ============================================================
# PRODUCT IMAGE DISTRIBUTION
# ============================================================

def show_product_distribution(images, products):
    print()
    print("=" * 60)
    print("IMAGES PER PRODUCT")
    print("=" * 60)

    product_lookup = {
        product["id"]: product
        for product in products
        if product.get("id") is not None
    }

    counts = Counter()

    for image in images:
        product_id = image.get("product_id")

        counts[product_id] += 1

    for product_id in sorted(counts):
        product = product_lookup.get(product_id)

        if product:
            product_code = product.get(
                "product_code",
                "UNKNOWN"
            )

            page_number = product.get(
                "page_number",
                "UNKNOWN"
            )

            print(
                f"{product_code} | "
                f"Page {page_number} | "
                f"{counts[product_id]} image(s)"
            )
        else:
            print(
                f"Product ID {product_id} | "
                f"{counts[product_id]} image(s)"
            )


# ============================================================
# IMAGE COUNT CHECK
# ============================================================

def check_image_count(images):
    print()
    print("=" * 60)
    print("IMAGE COUNT CHECK")
    print("=" * 60)

    actual_count = len(images)

    print(
        f"Expected extracted images : "
        f"{EXPECTED_IMAGE_COUNT}"
    )

    print(
        f"Images in database        : "
        f"{actual_count}"
    )

    if actual_count == EXPECTED_IMAGE_COUNT:
        print(
            "Image count matches the "
            "extraction result."
        )
        return 0

    difference = actual_count - EXPECTED_IMAGE_COUNT

    if difference > 0:
        print(
            f"WARNING: {difference} extra image "
            f"record(s) found."
        )
    else:
        print(
            f"WARNING: {abs(difference)} image "
            f"record(s) missing."
        )

    return 1


# ============================================================
# MAIN
# ============================================================

def main():
    print("Reading image records for validation...")
    print()

    # --------------------------------------------------------
    # Get products
    # --------------------------------------------------------

    products = fetch_products()

    if not products:
        print()
        print(
            "No products found for document "
            f"{DOCUMENT_ID}."
        )
        return

    product_ids = [
        product["id"]
        for product in products
        if product.get("id") is not None
    ]

    # --------------------------------------------------------
    # Get images
    # --------------------------------------------------------

    images = fetch_images(product_ids)

    if not images:
        print()
        print(
            "No images found in product_images "
            "for the selected products."
        )
        return

    # --------------------------------------------------------
    # Run validations
    # --------------------------------------------------------

    required_field_issues = (
        validate_required_fields(images)
    )

    relationship_issues = (
        validate_product_relationship(
            images,
            products
        )
    )

    duplicate_issues = (
        validate_duplicates(images)
    )

    file_name_issues = (
        validate_file_names(images)
    )

    mime_type_issues = (
        validate_mime_types(images)
    )

    dimension_issues = (
        validate_dimensions(images)
    )

    count_issues = (
        check_image_count(images)
    )

    # --------------------------------------------------------
    # Additional information
    # --------------------------------------------------------

    show_image_type_distribution(images)

    show_product_distribution(
        images,
        products
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    total_issues = (
        required_field_issues
        + relationship_issues
        + duplicate_issues
        + file_name_issues
        + mime_type_issues
        + dimension_issues
        + count_issues
    )

    print()
    print("=" * 60)
    print("IMAGE VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Products checked       : "
        f"{len(products)}"
    )

    print(
        f"Images checked         : "
        f"{len(images)}"
    )

    print(
        f"Required field issues  : "
        f"{required_field_issues}"
    )

    print(
        f"Relationship issues    : "
        f"{relationship_issues}"
    )

    print(
        f"Duplicate issues       : "
        f"{duplicate_issues}"
    )

    print(
        f"File name issues       : "
        f"{file_name_issues}"
    )

    print(
        f"MIME type issues       : "
        f"{mime_type_issues}"
    )

    print(
        f"Dimension issues       : "
        f"{dimension_issues}"
    )

    print(
        f"Count mismatch issues  : "
        f"{count_issues}"
    )

    print()

    if total_issues == 0:
        print("STATUS: VALID")
        print()
        print(
            "All image records passed validation."
        )
    else:
        print("STATUS: REVIEW REQUIRED")
        print()
        print(
            f"Total validation issues: "
            f"{total_issues}"
        )

    print("=" * 60)
    print()
    print(
        "Image validation completed."
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()