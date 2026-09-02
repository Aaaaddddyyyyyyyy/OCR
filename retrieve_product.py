import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(r"E:\OCR_Project")
BACKEND_DIR = PROJECT_DIR / "backend"

sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# SUPABASE CONNECTION
# ============================================================

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1

PRODUCTS_TABLE = "products"
PRODUCT_SPECS_TABLE = "product_specs"
PRODUCT_IMAGES_TABLE = "product_images"
MAPPING_TABLE = "product_image_map"


# ============================================================
# GET PRODUCT CODE
# ============================================================

def get_product_code():

    print()
    print("=" * 80)
    print("PRODUCT RETRIEVAL")
    print("=" * 80)

    product_code = input(
        "Enter product code: "
    ).strip()

    if not product_code:

        print()
        print("ERROR: Product code cannot be empty.")

        return None

    return product_code


# ============================================================
# FETCH PRODUCT
# ============================================================

def fetch_products(product_code):

    print()
    print("Fetching product...")

    response = (
        supabase
        .table(PRODUCTS_TABLE)
        .select("*")
        .eq("document_id", DOCUMENT_ID)
        .eq("product_code", product_code)
        .execute()
    )

    products = response.data or []

    print(
        f"Products found: {len(products)}"
    )

    return products


# ============================================================
# FETCH PRODUCT SPECIFICATIONS
# ============================================================

def fetch_specifications(product_id):

    print(
        f"Fetching specifications for "
        f"product ID={product_id}..."
    )

    response = (
        supabase
        .table(PRODUCT_SPECS_TABLE)
        .select("*")
        .eq("product_id", product_id)
        .execute()
    )

    specifications = response.data or []

    print(
        f"Specifications found: "
        f"{len(specifications)}"
    )

    return specifications


# ============================================================
# FETCH IMAGE MAPPINGS
# ============================================================

def fetch_image_mappings(product_id):

    print(
        f"Fetching image mappings for "
        f"product ID={product_id}..."
    )

    response = (
        supabase
        .table(MAPPING_TABLE)
        .select("*")
        .eq("product_id", product_id)
        .execute()
    )

    mappings = response.data or []

    print(
        f"Mappings found: {len(mappings)}"
    )

    return mappings


# ============================================================
# FETCH IMAGES
# ============================================================

def fetch_images(image_ids):

    if not image_ids:

        return []

    print(
        f"Fetching {len(image_ids)} images..."
    )

    response = (
        supabase
        .table(PRODUCT_IMAGES_TABLE)
        .select("*")
        .in_("id", image_ids)
        .execute()
    )

    images = response.data or []

    print(
        f"Images found: {len(images)}"
    )

    return images


# ============================================================
# DISPLAY PRODUCT
# ============================================================

def display_product(product):

    print()
    print("=" * 80)
    print("PRODUCT")
    print("=" * 80)

    print(
        f"Product ID:    {product.get('id')}"
    )

    print(
        f"Product Code:  {product.get('product_code')}"
    )

    print(
        f"Product Name:  {product.get('product_name')}"
    )

    print(
        f"Page Number:   {product.get('page_number')}"
    )

    print(
        f"Document ID:   {product.get('document_id')}"
    )


# ============================================================
# DISPLAY SPECIFICATIONS
# ============================================================

def display_specifications(specifications):

    print()
    print("=" * 80)
    print("PRODUCT SPECIFICATIONS")
    print("=" * 80)

    if not specifications:

        print("No specifications found.")

        return

    for index, spec in enumerate(
        specifications,
        start=1
    ):

        print()
        print(
            f"Specification #{index}"
        )

        print("-" * 80)

        for key, value in spec.items():

            if key in [
                "id",
                "product_id"
            ]:

                continue

            print(
                f"{key}: {value}"
            )


# ============================================================
# DISPLAY IMAGES
# ============================================================

def display_images(images):

    print()
    print("=" * 80)
    print("PRODUCT IMAGES")
    print("=" * 80)

    if not images:

        print("No images found.")

        return

    print(
        f"Total images: {len(images)}"
    )

    print()

    for index, image in enumerate(
        images,
        start=1
    ):

        print(
            f"Image #{index}"
        )

        print("-" * 80)

        print(
            f"ID:            {image.get('id')}"
        )

        print(
            f"File name:     {image.get('file_name')}"
        )

        print(
            f"Image type:    {image.get('image_type')}"
        )

        print(
            f"Storage path:  {image.get('storage_path')}"
        )

        print(
            f"Mime type:     {image.get('mime_type')}"
        )

        print(
            f"Width:         {image.get('width')}"
        )

        print(
            f"Height:        {image.get('height')}"
        )

        print()


# ============================================================
# RETRIEVE PRODUCT
# ============================================================

def retrieve_product(product):

    product_id = product.get("id")

    # --------------------------------------------------------
    # DISPLAY PRODUCT
    # --------------------------------------------------------

    display_product(product)

    # --------------------------------------------------------
    # FETCH SPECIFICATIONS
    # --------------------------------------------------------

    specifications = fetch_specifications(
        product_id
    )

    # --------------------------------------------------------
    # DISPLAY SPECIFICATIONS
    # --------------------------------------------------------

    display_specifications(
        specifications
    )

    # --------------------------------------------------------
    # FETCH MAPPINGS
    # --------------------------------------------------------

    mappings = fetch_image_mappings(
        product_id
    )

    # --------------------------------------------------------
    # EXTRACT IMAGE IDS
    # --------------------------------------------------------

    image_ids = []

    for mapping in mappings:

        image_id = mapping.get("image_id")

        if image_id is not None:

            image_ids.append(image_id)

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    image_ids = list(
        dict.fromkeys(image_ids)
    )

    # --------------------------------------------------------
    # FETCH IMAGES
    # --------------------------------------------------------

    images = fetch_images(
        image_ids
    )

    # --------------------------------------------------------
    # DISPLAY IMAGES
    # --------------------------------------------------------

    display_images(
        images
    )

    return (
        specifications,
        mappings,
        images
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

def display_final_summary(
    products,
    total_specifications,
    total_mappings,
    total_images
):

    print()
    print("=" * 80)
    print("RETRIEVAL SUMMARY")
    print("=" * 80)

    print(
        f"Products found:       "
        f"{len(products)}"
    )

    print(
        f"Specifications:       "
        f"{total_specifications}"
    )

    print(
        f"Image mappings:       "
        f"{total_mappings}"
    )

    print(
        f"Images retrieved:     "
        f"{total_images}"
    )

    print("=" * 80)


# ============================================================
# MAIN
# ============================================================

def main():

    product_code = get_product_code()

    if product_code is None:

        return

    # --------------------------------------------------------
    # FETCH PRODUCTS
    # --------------------------------------------------------

    try:

        products = fetch_products(
            product_code
        )

    except Exception as error:

        print()
        print(
            "ERROR while fetching product:"
        )

        print(error)

        return

    # --------------------------------------------------------
    # PRODUCT NOT FOUND
    # --------------------------------------------------------

    if not products:

        print()
        print("=" * 80)
        print("PRODUCT NOT FOUND")
        print("=" * 80)

        print(
            f"No product found for: "
            f"{product_code}"
        )

        return

    # --------------------------------------------------------
    # RETRIEVE DATA
    # --------------------------------------------------------

    total_specifications = 0
    total_mappings = 0
    total_images = 0

    for product in products:

        product_id = product.get("id")

        try:

            (
                specifications,
                mappings,
                images
            ) = retrieve_product(
                product
            )

            total_specifications += (
                len(specifications)
            )

            total_mappings += (
                len(mappings)
            )

            total_images += (
                len(images)
            )

        except Exception as error:

            print()
            print(
                f"ERROR retrieving "
                f"product ID={product_id}"
            )

            print(error)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    display_final_summary(
        products,
        total_specifications,
        total_mappings,
        total_images
    )

    print()
    print("=" * 80)
    print("PRODUCT RETRIEVAL COMPLETED")
    print("=" * 80)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()