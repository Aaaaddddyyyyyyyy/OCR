import mimetypes
from pathlib import Path

from PIL import Image

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

IMAGE_DIR = Path(r"E:\OCR_Project\extracted_images")

STORAGE_BUCKET = "product-image"

PRODUCT_ID = 1


# ============================================================
# FIND FIRST IMAGE
# ============================================================

def find_first_image():

    if not IMAGE_DIR.exists():
        print("ERROR: Image directory does not exist:")
        print(IMAGE_DIR)
        return None

    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff"
    }

    images = [
        file
        for file in IMAGE_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in image_extensions
    ]

    if not images:
        print("ERROR: No images found.")
        return None

    images.sort()

    return images[0]


# ============================================================
# GET IMAGE INFORMATION
# ============================================================

def get_image_information(image_path):

    mime_type, _ = mimetypes.guess_type(image_path.name)

    if mime_type is None:
        mime_type = "application/octet-stream"

    with Image.open(image_path) as image:
        width, height = image.size

    return mime_type, width, height


# ============================================================
# UPLOAD IMAGE TO STORAGE
# ============================================================

def upload_image(image_path, storage_path, mime_type):

    print()
    print("============================================================")
    print("STORAGE UPLOAD")
    print("============================================================")

    try:

        with open(image_path, "rb") as file:
            image_bytes = file.read()

        supabase.storage \
            .from_(STORAGE_BUCKET) \
            .upload(
                storage_path,
                image_bytes,
                {
                    "content-type": mime_type,
                    "upsert": False
                }
            )

        print("STORAGE UPLOAD: SUCCESS")
        print(f"Storage path: {storage_path}")

        return True

    except Exception as e:

        error_text = str(e)

        if (
            "Duplicate" in error_text
            or "already exists" in error_text
            or "resource already exists" in error_text
            or "409" in error_text
        ):

            print("STORAGE UPLOAD: ALREADY EXISTS")
            print("The image is already present in Supabase Storage.")
            print("Continuing with database insert...")

            return True

        print("STORAGE UPLOAD: FAILED")
        print(e)

        return False


# ============================================================
# INSERT DATABASE RECORD
# ============================================================

def insert_database_record(
    product_id,
    image_path,
    storage_path,
    mime_type,
    width,
    height
):

    print()
    print("============================================================")
    print("DATABASE INSERT")
    print("============================================================")

    database_record = {
        "product_id": product_id,
        "image_type": "product",
        "storage_path": storage_path,
        "file_name": image_path.name,
        "mime_type": mime_type,
        "width": width,
        "height": height
    }

    print("Table: product_images")
    print("Record:")
    print(database_record)

    try:

        response = (
            supabase
            .table("product_images")
            .insert(database_record)
            .execute()
        )

        print()
        print("DATABASE INSERT: SUCCESS")
        print("Inserted record:")
        print(response.data)

        return True

    except Exception as e:

        print()
        print("DATABASE INSERT: FAILED")
        print(e)

        return False


# ============================================================
# MAIN TEST
# ============================================================

def main():

    print()
    print("============================================================")
    print("PRODUCT IMAGE STORAGE + DATABASE TEST")
    print("============================================================")

    # --------------------------------------------------------
    # STEP 1: FIND IMAGE
    # --------------------------------------------------------

    image_path = find_first_image()

    if image_path is None:
        print()
        print("TEST FAILED AT IMAGE SEARCH")
        return

    print()
    print(f"Image found: {image_path}")
    print(f"File name: {image_path.name}")

    # --------------------------------------------------------
    # STEP 2: GET IMAGE INFORMATION
    # --------------------------------------------------------

    try:

        mime_type, width, height = get_image_information(image_path)

        print(f"MIME type: {mime_type}")
        print(f"Width: {width}")
        print(f"Height: {height}")

    except Exception as e:

        print()
        print("IMAGE INFORMATION: FAILED")
        print(e)
        return

    # --------------------------------------------------------
    # STEP 3: CREATE STORAGE PATH
    # --------------------------------------------------------

    storage_path = (
        f"products/{PRODUCT_ID}/{image_path.name}"
    )

    print()
    print(f"Storage bucket: {STORAGE_BUCKET}")
    print(f"Storage path: {storage_path}")

    # --------------------------------------------------------
    # STEP 4: UPLOAD TO STORAGE
    # --------------------------------------------------------

    storage_success = upload_image(
        image_path,
        storage_path,
        mime_type
    )

    if not storage_success:

        print()
        print("============================================================")
        print("TEST FAILED AT STORAGE UPLOAD")
        print("============================================================")

        return

    # --------------------------------------------------------
    # STEP 5: INSERT DATABASE RECORD
    # --------------------------------------------------------

    database_success = insert_database_record(
        PRODUCT_ID,
        image_path,
        storage_path,
        mime_type,
        width,
        height
    )

    if not database_success:

        print()
        print("============================================================")
        print("STORAGE WORKED, BUT DATABASE INSERT FAILED")
        print("============================================================")

        return

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print()
    print("============================================================")
    print("FINAL RESULT")
    print("============================================================")

    print("Storage upload: SUCCESS")
    print("Database insert: SUCCESS")
    print("Product image test: PASSED")

    print("============================================================")


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()