from pathlib import Path
import mimetypes

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

IMAGE_DIR = Path(r"E:\OCR_Project\extracted_images")
BUCKET_NAME = "product-image"
PRODUCT_FOLDER = "products/1"


# ============================================================
# CHECK LOCAL DIRECTORY
# ============================================================

if not IMAGE_DIR.exists():
    print("=" * 80)
    print("ERROR")
    print("=" * 80)
    print(f"Image directory does not exist:")
    print(IMAGE_DIR)
    raise SystemExit(1)


# ============================================================
# GET LOCAL IMAGES
# ============================================================

image_files = sorted(
    [
        file
        for file in IMAGE_DIR.iterdir()
        if file.is_file()
        and file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]
    ]
)


print("=" * 80)
print("SUPABASE IMAGE STORAGE UPLOAD")
print("=" * 80)

print(f"Bucket:          {BUCKET_NAME}")
print(f"Local directory: {IMAGE_DIR}")
print(f"Images found:    {len(image_files)}")
print("=" * 80)


# ============================================================
# TEST BUCKET
# ============================================================

print()
print("CHECKING BUCKET")
print("-" * 80)

try:

    bucket_test = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .list("")
    )

    print("Bucket access successful.")
    print(f"Objects currently visible: {len(bucket_test)}")

except Exception as e:

    print("BUCKET ACCESS FAILED")
    print(e)
    raise SystemExit(1)


# ============================================================
# UPLOAD IMAGES
# ============================================================

uploaded = 0
already_exists = 0
failed = 0


for index, image_file in enumerate(image_files, start=1):

    print()
    print("-" * 80)
    print(f"[{index}/{len(image_files)}] {image_file.name}")
    print("-" * 80)

    # --------------------------------------------------------
    # Storage path
    # --------------------------------------------------------

    storage_path = f"{PRODUCT_FOLDER}/{image_file.name}"

    print(f"Local file:    {image_file}")
    print(f"Storage path:  {storage_path}")

    # --------------------------------------------------------
    # MIME type
    # --------------------------------------------------------

    mime_type, _ = mimetypes.guess_type(str(image_file))

    if mime_type is None:
        mime_type = "application/octet-stream"

    print(f"MIME type:     {mime_type}")

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    try:

        with open(image_file, "rb") as file:

            file_data = file.read()

        print(f"File size:     {len(file_data)} bytes")

    except Exception as e:

        print("LOCAL FILE READ FAILED")
        print(e)

        failed += 1
        continue

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    try:

        response = (
            supabase
            .storage
            .from_(BUCKET_NAME)
            .upload(
                path=storage_path,
                file=file_data,
                file_options={
                    "content-type": mime_type,
                    "upsert": "true"
                }
            )
        )

        print("UPLOAD SUCCESSFUL")
        print(response)

        uploaded += 1

    except Exception as e:

        error_text = str(e)

        print("UPLOAD ERROR")
        print(error_text)

        # ----------------------------------------------------
        # If object already exists, treat it as success
        # ----------------------------------------------------

        if (
            "Duplicate" in error_text
            or "already exists" in error_text
            or "409" in error_text
        ):

            print("OBJECT ALREADY EXISTS")

            already_exists += 1

        else:

            failed += 1


# ============================================================
# SUMMARY
# ============================================================

print()
print()
print("=" * 80)
print("UPLOAD SUMMARY")
print("=" * 80)

print(f"Local images found:    {len(image_files)}")
print(f"Images uploaded:       {uploaded}")
print(f"Already existed:       {already_exists}")
print(f"Failed uploads:        {failed}")

print("=" * 80)


# ============================================================
# VERIFY STORAGE
# ============================================================

print()
print("=" * 80)
print("VERIFYING SUPABASE STORAGE")
print("=" * 80)

try:

    root_items = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .list("")
    )

    print(f"Bucket root objects/folders: {len(root_items)}")

    for item in root_items[:20]:

        print(item)

except Exception as e:

    print("ROOT LIST FAILED")
    print(e)


# ============================================================
# VERIFY products/1/
# ============================================================

print()
print("-" * 80)
print("CHECKING products/1/")
print("-" * 80)

try:

    product_items = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .list(PRODUCT_FOLDER)
    )

    print(f"Objects inside {PRODUCT_FOLDER}: {len(product_items)}")

    for item in product_items[:20]:

        print(item)

except Exception as e:

    print("PRODUCT FOLDER CHECK FAILED")
    print(e)


# ============================================================
# VERIFY FIRST IMAGE
# ============================================================

if image_files:

    first_image = image_files[0]

    first_path = f"{PRODUCT_FOLDER}/{first_image.name}"

    print()
    print("=" * 80)
    print("VERIFYING FIRST IMAGE")
    print("=" * 80)

    print(f"Path: {first_path}")

    try:

        check = (
            supabase
            .storage
            .from_(BUCKET_NAME)
            .list(PRODUCT_FOLDER)
        )

        found = False

        for item in check:

            if item.get("name") == first_image.name:

                found = True
                break

        if found:

            print("IMAGE EXISTS IN SUPABASE STORAGE")

            public_url = (
                supabase
                .storage
                .from_(BUCKET_NAME)
                .get_public_url(first_path)
            )

            print()
            print("PUBLIC IMAGE URL")
            print("-" * 80)
            print(public_url)

        else:

            print("IMAGE NOT FOUND IN SUPABASE STORAGE")
            print()
            print("Expected path:")
            print(first_path)

    except Exception as e:

        print("IMAGE VERIFICATION FAILED")
        print(e)


print()
print("=" * 80)
print("STORAGE UPLOAD PROCESS FINISHED")
print("=" * 80)