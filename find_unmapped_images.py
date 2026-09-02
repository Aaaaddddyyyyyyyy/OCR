from pathlib import Path
import sys


# ============================================================
# ADD BACKEND TO PYTHON PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# IMPORT SUPABASE
# ============================================================

try:
    from supabase_client import supabase
except ModuleNotFoundError:
    print("ERROR: Could not find supabase_client.py")
    print(f"Expected location: {BACKEND_DIR / 'supabase_client.py'}")
    sys.exit(1)


# ============================================================
# CONFIGURATION
# ============================================================

PRODUCTS_TABLE = "products"
IMAGES_TABLE = "product_images"
MAPPING_TABLE = "product_image_map"


# ============================================================
# FETCH IMAGES
# ============================================================

def fetch_images():

    print("Fetching all images...")

    response = (
        supabase
        .table(IMAGES_TABLE)
        .select("id, file_name, storage_path, document_id")
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

    print("Fetching product-image mappings...")

    response = (
        supabase
        .table(MAPPING_TABLE)
        .select("image_id")
        .execute()
    )

    mappings = response.data or []

    print(f"Mapping records found: {len(mappings)}")

    return mappings


# ============================================================
# FIND UNMAPPED IMAGES
# ============================================================

def find_unmapped_images(images, mappings):

    mapped_image_ids = set()

    for mapping in mappings:

        image_id = mapping.get("image_id")

        if image_id is not None:
            mapped_image_ids.add(image_id)

    unmapped = []

    for image in images:

        image_id = image.get("id")

        if image_id not in mapped_image_ids:
            unmapped.append(image)

    return unmapped


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(images, mappings, unmapped):

    print()
    print("=" * 70)
    print("UNMAPPED PRODUCT IMAGES")
    print("=" * 70)

    print(f"Total images:       {len(images)}")
    print(f"Mapped images:      {len(images) - len(unmapped)}")
    print(f"Unmapped images:    {len(unmapped)}")

    print()
    print("=" * 70)

    if not unmapped:

        print("ALL IMAGES ARE MAPPED")
        print("=" * 70)
        return

    print("UNMAPPED IMAGES")
    print("=" * 70)

    for image in unmapped:

        print(
            f"ID: {image.get('id')} | "
            f"File: {image.get('file_name')} | "
            f"Storage: {image.get('storage_path')} | "
            f"Document ID: {image.get('document_id')}"
        )

    print("=" * 70)
    print(f"Total unmapped images: {len(unmapped)}")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("FIND UNMAPPED PRODUCT IMAGES")
    print("=" * 70)
    print()

    images = fetch_images()

    mappings = fetch_mappings()

    unmapped = find_unmapped_images(
        images,
        mappings
    )

    display_results(
        images,
        mappings,
        unmapped
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()