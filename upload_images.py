import mimetypes
from pathlib import Path

from PIL import Image

from supabase_client import supabase


DOCUMENT_ID = 1
IMAGE_DIR = Path(r"E:\OCR_Project\extracted_images")
STORAGE_BUCKET = "product-image"
IMAGE_TABLE = "product_images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def get_image_dimensions(image_file):
    try:
        with Image.open(image_file) as image:
            return image.size
    except Exception as error:
        print(f"WARNING: Could not read image dimensions: {error}")
        return None, None


def record_exists(storage_path):
    response = (
        supabase.table(IMAGE_TABLE)
        .select("id")
        .eq("storage_path", storage_path)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def upload_image(image_file, storage_path, mime_type):
    supabase.storage.from_(STORAGE_BUCKET).upload(
        storage_path,
        image_file.read_bytes(),
        {"content-type": mime_type, "upsert": True},
    )


def create_image_record(image_file, storage_path, mime_type, width, height):
    return (
        supabase.table(IMAGE_TABLE)
        .insert(
            {
                "product_id": None,
                "image_type": "product",
                "storage_path": storage_path,
                "file_name": image_file.name,
                "mime_type": mime_type,
                "width": width,
                "height": height,
            }
        )
        .execute()
    )


def remove_storage_file(storage_path):
    supabase.storage.from_(STORAGE_BUCKET).remove([storage_path])


def main():
    if not IMAGE_DIR.exists():
        print(f"ERROR: Image directory does not exist: {IMAGE_DIR}")
        raise SystemExit(1)

    image_files = sorted(
        file
        for file in IMAGE_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
    )

    images_uploaded = 0
    database_records_created = 0
    existing_records_skipped = 0
    failed_operations = 0
    total_images = len(image_files)

    print("=" * 60)
    print("IMAGE UPLOAD AND DATABASE INSERTION")
    print("=" * 60)
    print(f"Image directory: {IMAGE_DIR}")
    print(f"Storage bucket: {STORAGE_BUCKET}")
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Total images: {total_images}")

    for index, image_file in enumerate(image_files, start=1):
        print("\n" + "-" * 60)
        print(f"Processing image {index}/{total_images}: {image_file.name}")

        try:
            mime_type = (
                mimetypes.guess_type(image_file.name)[0] or "application/octet-stream"
            )
            width, height = get_image_dimensions(image_file)
            storage_path = f"document_{DOCUMENT_ID}/{image_file.name}"
            print(f"MIME type: {mime_type}")
            print(f"Dimensions: {width} x {height}")
            print(f"Storage path: {storage_path}")

            existing_record = record_exists(storage_path)
            if existing_record:
                print(f"Database record already exists (ID: {existing_record['id']}).")
                existing_records_skipped += 1
                continue

            upload_image(image_file, storage_path, mime_type)
            images_uploaded += 1
            print("Storage upload successful.")

            try:
                response = create_image_record(
                    image_file, storage_path, mime_type, width, height
                )
                database_records_created += 1
                print(f"Database insert successful: {response.data}")
            except Exception as error:
                failed_operations += 1
                print(f"DATABASE INSERT FAILED: {error}")
                try:
                    remove_storage_file(storage_path)
                    print("Removed orphaned storage file.")
                except Exception as cleanup_error:
                    print(f"WARNING: Could not remove storage file: {cleanup_error}")

        except Exception as error:
            failed_operations += 1
            print(f"FAILED: {error}")

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Total images found: {total_images}")
    print(f"Images uploaded: {images_uploaded}")
    print(f"Database records created: {database_records_created}")
    print(f"Existing records skipped: {existing_records_skipped}")
    print(f"Failed operations: {failed_operations}")
    print("SUCCESS: Image processing completed successfully." if failed_operations == 0 else "WARNING: Some operations failed.")


if __name__ == "__main__":
    main()
