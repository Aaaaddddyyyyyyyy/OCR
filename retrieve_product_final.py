import sys
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

PRODUCTS_TABLE = "products"
SPECS_TABLE = "product_specs"
MAPPING_TABLE = "product_image_map"
IMAGES_TABLE = "product_images"


# ============================================================
# HELPER
# ============================================================

def print_separator(char="-", length=80):
    print(char * length)


# ============================================================
# FETCH PRODUCT
# ============================================================

def fetch_product(product_code):
    print()
    print("Fetching product...")

    try:
        response = (
            supabase
            .table(PRODUCTS_TABLE)
            .select("*")
            .eq("product_code", product_code)
            .execute()
        )

        products = response.data or []

        print(f"Products found: {len(products)}")

        if not products:
            print()
            print("ERROR: Product not found.")
            return None

        if len(products) > 1:
            print()
            print("WARNING: Multiple products found.")
            print("Using the first matching product.")

        return products[0]

    except Exception as e:
        print()
        print("ERROR retrieving product:")
        print(e)
        return None


# ============================================================
# FETCH PRODUCT SPECIFICATIONS
# ============================================================

def fetch_specifications(product_id):
    print()
    print(f"Fetching specifications for product ID={product_id}...")

    try:
        response = (
            supabase
            .table(SPECS_TABLE)
            .select("*")
            .eq("product_id", product_id)
            .execute()
        )

        specifications = response.data or []

        print(f"Specifications found: {len(specifications)}")

        return specifications

    except Exception as e:
        print()
        print("ERROR retrieving specifications:")
        print(e)
        return []


# ============================================================
# FETCH IMAGE MAPPINGS
# ============================================================

def fetch_image_mappings(product_id):
    print()
    print(f"Fetching image mappings for product ID={product_id}...")

    try:
        response = (
            supabase
            .table(MAPPING_TABLE)
            .select("*")
            .eq("product_id", product_id)
            .execute()
        )

        mappings = response.data or []

        print(f"Mappings found: {len(mappings)}")

        return mappings

    except Exception as e:
        print()
        print("ERROR retrieving image mappings:")
        print(e)
        return []


# ============================================================
# FETCH IMAGES
# ============================================================

def fetch_images(image_ids):

    if not image_ids:
        return []

    print()
    print(f"Fetching {len(image_ids)} images...")

    try:
        response = (
            supabase
            .table(IMAGES_TABLE)
            .select("*")
            .in_("id", image_ids)
            .execute()
        )

        images = response.data or []

        print(f"Images found: {len(images)}")

        return images

    except Exception as e:
        print()
        print("ERROR retrieving images:")
        print(e)
        return []


# ============================================================
# DISPLAY PRODUCT
# ============================================================

def display_product(product):

    print()
    print_separator("=")

    print("PRODUCT")

    print_separator("=")

    print(f"Product ID:    {product.get('id')}")
    print(f"Product Code:  {product.get('product_code')}")
    print(f"Product Name:  {product.get('product_name')}")
    print(f"Page Number:   {product.get('page_number')}")
    print(f"Document ID:   {product.get('document_id')}")


# ============================================================
# DISPLAY SPECIFICATIONS
# ============================================================

def display_specifications(specifications):

    print()
    print_separator("=")

    print("PRODUCT SPECIFICATIONS")

    print_separator("=")

    if not specifications:
        print()
        print("No specifications found.")
        return

    for index, spec in enumerate(specifications, start=1):

        print()
        print(f"Specification #{index}")

        print_separator("-")

        fields = [
            "housing",
            "wattage",
            "led_source",
            "colour_temperature",
            "color_temperature",
            "beam_angle",
            "system_lumens",
            "product_size",
            "cutout",
            "ip_rating",
            "outer_frame",
            "created_at"
        ]

        displayed_fields = set()

        for field in fields:

            if field in displayed_fields:
                continue

            if field in spec:

                value = spec.get(field)

                print(f"{field}: {value}")

                displayed_fields.add(field)


# ============================================================
# DISPLAY IMAGES
# ============================================================

def display_images(images):

    print()
    print_separator("=")

    print("PRODUCT IMAGES")

    print_separator("=")

    print(f"Total images: {len(images)}")

    if not images:
        print()
        print("No images found.")
        return

    images = sorted(
        images,
        key=lambda x: x.get("id", 0)
    )

    for index, image in enumerate(images, start=1):

        print()
        print(f"Image #{index}")

        print_separator("-")

        print(f"ID:            {image.get('id')}")
        print(f"File name:     {image.get('file_name')}")
        print(f"Image type:    {image.get('image_type')}")
        print(f"Storage path:  {image.get('storage_path')}")
        print(f"Mime type:     {image.get('mime_type')}")
        print(f"Width:         {image.get('width')}")
        print(f"Height:        {image.get('height')}")

        if image.get("created_at"):
            print(f"Created at:    {image.get('created_at')}")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print_separator("=")

    print("PRODUCT RETRIEVAL")

    print_separator("=")

    product_code = input("Enter product code: ").strip()

    if not product_code:

        print()
        print("ERROR: Product code cannot be empty.")
        return

    # --------------------------------------------------------
    # FETCH PRODUCT
    # --------------------------------------------------------

    product = fetch_product(product_code)

    if product is None:
        return

    product_id = product.get("id")

    if product_id is None:

        print()
        print("ERROR: Product ID is missing.")
        return

    # --------------------------------------------------------
    # DISPLAY PRODUCT
    # --------------------------------------------------------

    display_product(product)

    # --------------------------------------------------------
    # FETCH SPECIFICATIONS
    # --------------------------------------------------------

    specifications = fetch_specifications(product_id)

    display_specifications(specifications)

    # --------------------------------------------------------
    # FETCH IMAGE MAPPINGS
    # --------------------------------------------------------

    mappings = fetch_image_mappings(product_id)

    # --------------------------------------------------------
    # EXTRACT IMAGE IDS
    # --------------------------------------------------------

    image_ids = []

    for mapping in mappings:

        image_id = mapping.get("image_id")

        if image_id is not None:
            image_ids.append(image_id)

    # Remove duplicate image IDs
    image_ids = list(dict.fromkeys(image_ids))

    # --------------------------------------------------------
    # FETCH IMAGES
    # --------------------------------------------------------

    images = fetch_images(image_ids)

    # --------------------------------------------------------
    # DISPLAY IMAGES
    # --------------------------------------------------------

    display_images(images)

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print_separator("=")

    print("RETRIEVAL SUMMARY")

    print_separator("=")

    print(f"Products found:       1")
    print(f"Specifications:       {len(specifications)}")
    print(f"Image mappings:       {len(mappings)}")
    print(f"Images retrieved:     {len(images)}")

    print_separator("=")

    print()
    print_separator("=")

    print("PRODUCT RETRIEVAL COMPLETED")

    print_separator("=")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()