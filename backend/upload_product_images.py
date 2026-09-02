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
# FIND ALL IMAGES
# ============================================================

def find_images():

    if not IMAGE_DIR.exists():
        print("ERROR: Image directory does not exist:")
        print(IMAGE_DIR)
        return []

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

    images.sort()

    return images


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
# CHECK DATABASE RECORD
# ============================================================

def database_record_exists(storage_path):

    try:

        response = (
            supabase
            .table("product_images")
            .select("id")
            .eq("product_id", PRODUCT_ID)
            .eq("storage_path", storage_path)
            .limit(1)
            .execute()
        )

        return len(response.data) > 0

    except Exception as e:

        print("DATABASE CHECK FAILED")
        print(e)

        return False


# ============================================================
# UPLOAD IMAGE TO STORAGE
# ============================================================

def upload_to_storage(image_path, storage_path, mime_type):

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

        return "uploaded"

    except Exception as e:

        error_text = str(e)

        if (
            "Duplicate" in error_text
            or "already exists" in error_text
            or "resource already exists" in error_text
            or "409" in error_text
        ):

            return "exists"

        print("STORAGE UPLOAD FAILED")
        print(e)

        return "failed"


# ============================================================
# INSERT DATABASE RECORD
# ============================================================

def insert_database_record(
    image_path,
    storage_path,
    mime_type,
    width,
    height
):

    record = {
        "product_id": PRODUCT_ID,
        "image_type": "product",
        "storage_path": storage_path,
        "file_name": image_path.name,
        "mime_type": mime_type,
        "width": width,
        "height": height
    }

    try:

        response = (
            supabase
            .table("product_images")
            .insert(record)
            .execute()
        )

        return True

    except Exception as e:

        print("DATABASE INSERT FAILED")
        print(e)

        return False


# ============================================================
# PROCESS ONE IMAGE
# ============================================================

def process_image(image_path):

    print()
    print("-" * 60)
    print(f"Processing: {image_path.name}")

    # --------------------------------------------------------
    # GET IMAGE INFORMATION
    # --------------------------------------------------------

    try:

        mime_type, width, height = get_image_information(
            image_path
        )

    except Exception as e:

        print("IMAGE INFORMATION FAILED")
        print(e)

        return "failed"


    # --------------------------------------------------------
    # CREATE STORAGE PATH
    # --------------------------------------------------------

    storage_path = (
        f"products/{PRODUCT_ID}/{image_path.name}"
    )


    # --------------------------------------------------------
    # CHECK DATABASE
    # --------------------------------------------------------

    if database_record_exists(storage_path):

        print("DATABASE: RECORD ALREADY EXISTS")
        print("SKIPPED")

        return "skipped"


    # --------------------------------------------------------
    # UPLOAD TO STORAGE
    # --------------------------------------------------------

    storage_result = upload_to_storage(
        image_path,
        storage_path,
        mime_type
    )

    if storage_result == "failed":

        print("STORAGE: FAILED")

        return "failed"


    if storage_result == "uploaded":

        print("STORAGE: UPLOADED")

    elif storage_result == "exists":

        print("STORAGE: ALREADY EXISTS")


    # --------------------------------------------------------
    # INSERT DATABASE RECORD
    # --------------------------------------------------------

    database_success = insert_database_record(
        image_path,
        storage_path,
        mime_type,
        width,
        height
    )

    if not database_success:

        return "failed"


    print("DATABASE: INSERTED")
    print("SUCCESS")

    return "success"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("PRODUCT IMAGE BULK UPLOAD")
    print("=" * 60)

    # --------------------------------------------------------
    # FIND IMAGES
    # --------------------------------------------------------

    images = find_images()

    total_images = len(images)

    print(f"Image directory: {IMAGE_DIR}")
    print(f"Total images found: {total_images}")

    if total_images == 0:

        print()
        print("No images found.")

        return


    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    successful = 0
    skipped = 0
    failed = 0


    # --------------------------------------------------------
    # PROCESS ALL IMAGES
    # --------------------------------------------------------

    for index, image_path in enumerate(images, start=1):

        print()
        print(
            f"[{index}/{total_images}] "
            f"{image_path.name}"
        )

        result = process_image(image_path)

        if result == "success":

            successful += 1

        elif result == "skipped":

            skipped += 1

        elif result == "failed":

            failed += 1


    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print(f"Total images found:       {total_images}")
    print(f"Images processed:         {successful}")
    print(f"Existing records skipped: {skipped}")
    print(f"Failed operations:        {failed}")

    print("=" * 60)

    if failed == 0:

        print("BULK IMAGE UPLOAD COMPLETED SUCCESSFULLY")

    else:

        print("BULK IMAGE UPLOAD COMPLETED WITH ERRORS")


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()