import mimetypes
from pathlib import Path

from PIL import Image

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1

IMAGE_DIR = Path(r"E:\OCR_Project\extracted_images")

STORAGE_BUCKET = "product-image"

IMAGE_TABLE = "product_images"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
}


# ============================================================
# GET IMAGE DIMENSIONS
# ============================================================

def get_image_dimensions(image_file):
    try:
        with Image.open(image_file) as image:
            return image.size

    except Exception as error:
        print(f"WARNING: Could not read image dimensions: {error}")
        return None, None


# ============================================================
# CHECK IF DATABASE RECORD ALREADY EXISTS
# ============================================================

def record_exists(storage_path):
    try:
        response = (
            supabase
            .table(IMAGE_TABLE)
            .select("id")
            .eq("storage_path", storage_path)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    except Exception as error:
        print()
        print("DATABASE SELECT FAILED")
        print(f"Error type: {type(error).__name__}")
        print(f"Error: {error}")
        print()

        raise


# ============================================================
# UPLOAD IMAGE TO SUPABASE STORAGE
# ============================================================

def upload_image(image_file, storage_path, mime_type):
    try:
        image_bytes = image_file.read_bytes()

        response = (
            supabase
            .storage
            .from_(STORAGE_BUCKET)
            .upload(
                storage_path,
                image_bytes,
                {
                    "content-type": mime_type,
                    "upsert": "true",
                },
            )
        )

        return response

    except Exception as error:
        print()
        print("STORAGE UPLOAD FAILED")
        print(f"Error type: {type(error).__name__}")
        print(f"Error: {error}")
        print()

        raise


# ============================================================
# CREATE DATABASE RECORD
# ============================================================

def create_image_record(
    image_file,
    storage_path,
    mime_type,
    width,
    height,
):
    image_record = {
        "product_id": None,
        "image_type": "product",
        "storage_path": storage_path,
        "file_name": image_file.name,
        "mime_type": mime_type,
        "width": width,
        "height": height,
    }

    print("Database data:")
    print(image_record)

    try:
        response = (
            supabase
            .table(IMAGE_TABLE)
            .insert(image_record)
            .execute()
        )

        return response

    except Exception as error:
        print()
        print("DATABASE INSERT FAILED")
        print(f"Error type: {type(error).__name__}")
        print(f"Error: {error}")
        print(f"Data sent: {image_record}")
        print()

        raise


# ============================================================
# REMOVE STORAGE FILE
# ============================================================

def remove_storage_file(storage_path):
    try:
        response = (
            supabase
            .storage
            .from_(STORAGE_BUCKET)
            .remove([storage_path])
        )

        return response

    except Exception as error:
        print(
            f"WARNING: Could not remove storage file: {error}"
        )


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    # --------------------------------------------------------
    # CHECK IMAGE DIRECTORY
    # --------------------------------------------------------

    if not IMAGE_DIR.exists():
        print(
            f"ERROR: Image directory does not exist: "
            f"{IMAGE_DIR}"
        )

        raise SystemExit(1)


    # --------------------------------------------------------
    # FIND ALL IMAGES
    # --------------------------------------------------------

    image_files = sorted(
        file
        for file in IMAGE_DIR.iterdir()
        if (
            file.is_file()
            and file.suffix.lower() in IMAGE_EXTENSIONS
        )
    )

    total_images = len(image_files)


    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    images_uploaded = 0
    database_records_created = 0
    existing_records_skipped = 0
    failed_operations = 0


    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    print("=" * 60)
    print("IMAGE UPLOAD AND DATABASE INSERTION")
    print("=" * 60)

    print(f"Image directory: {IMAGE_DIR}")
    print(f"Storage bucket: {STORAGE_BUCKET}")
    print(f"Database table: {IMAGE_TABLE}")
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Total images: {total_images}")

    print("=" * 60)


    # --------------------------------------------------------
    # PROCESS EACH IMAGE
    # --------------------------------------------------------

    for index, image_file in enumerate(
        image_files,
        start=1
    ):

        print()
        print("-" * 60)

        print(
            f"Processing image "
            f"{index}/{total_images}: "
            f"{image_file.name}"
        )


        try:

            # ------------------------------------------------
            # MIME TYPE
            # ------------------------------------------------

            mime_type = (
                mimetypes.guess_type(
                    image_file.name
                )[0]
                or "application/octet-stream"
            )


            # ------------------------------------------------
            # IMAGE DIMENSIONS
            # ------------------------------------------------

            width, height = get_image_dimensions(
                image_file
            )


            # ------------------------------------------------
            # STORAGE PATH
            # ------------------------------------------------

            storage_path = (
                f"document_{DOCUMENT_ID}/"
                f"{image_file.name}"
            )


            print(f"MIME type: {mime_type}")
            print(
                f"Dimensions: "
                f"{width} x {height}"
            )

            print(
                f"Storage path: "
                f"{storage_path}"
            )


            # ------------------------------------------------
            # CHECK EXISTING DATABASE RECORD
            # ------------------------------------------------

            existing_record = record_exists(
                storage_path
            )


            if existing_record:

                print(
                    "Database record already exists."
                )

                print(
                    f"Existing ID: "
                    f"{existing_record['id']}"
                )

                existing_records_skipped += 1

                continue


            # ------------------------------------------------
            # UPLOAD IMAGE TO STORAGE
            # ------------------------------------------------

            print(
                "Uploading image to Supabase Storage..."
            )

            upload_image(
                image_file,
                storage_path,
                mime_type,
            )

            images_uploaded += 1

            print(
                "Storage upload successful."
            )


            # ------------------------------------------------
            # INSERT DATABASE RECORD
            # ------------------------------------------------

            print(
                "Creating database record..."
            )


            try:

                response = create_image_record(
                    image_file,
                    storage_path,
                    mime_type,
                    width,
                    height,
                )


                database_records_created += 1


                print(
                    "Database insert successful."
                )

                print(
                    f"Response: {response.data}"
                )


            except Exception:

                failed_operations += 1

                print(
                    "Database insertion failed."
                )


                # --------------------------------------------
                # REMOVE ORPHANED STORAGE FILE
                # --------------------------------------------

                print(
                    "Removing orphaned storage file..."
                )

                remove_storage_file(
                    storage_path
                )

                continue


        except Exception as error:

            failed_operations += 1

            print()
            print("IMAGE PROCESSING FAILED")

            print(
                f"Error type: "
                f"{type(error).__name__}"
            )

            print(
                f"Error: {error}"
            )

            print()


    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print("=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print(
        f"Total images found: "
        f"{total_images}"
    )

    print(
        f"Images uploaded: "
        f"{images_uploaded}"
    )

    print(
        f"Database records created: "
        f"{database_records_created}"
    )

    print(
        f"Existing records skipped: "
        f"{existing_records_skipped}"
    )

    print(
        f"Failed operations: "
        f"{failed_operations}"
    )

    print("=" * 60)


    if failed_operations == 0:

        print(
            "SUCCESS: "
            "Image processing completed successfully."
        )

    else:

        print(
            "WARNING: "
            "Some operations failed."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()