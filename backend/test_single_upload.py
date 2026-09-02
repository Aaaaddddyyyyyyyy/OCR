from pathlib import Path
import mimetypes

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

BUCKET_NAME = "product-image"

LOCAL_FILE = Path(
    r"E:\OCR_Project\extracted_images\page_03_image_01.jpeg"
)

STORAGE_PATH = "products/1/page_03_image_01.jpeg"


# ============================================================
# START
# ============================================================

print("=" * 80)
print("SUPABASE SINGLE IMAGE UPLOAD TEST")
print("=" * 80)

print("Bucket:")
print(BUCKET_NAME)

print("Local file:")
print(LOCAL_FILE)

print("Storage path:")
print(STORAGE_PATH)

print("=" * 80)


# ============================================================
# CHECK LOCAL FILE
# ============================================================

if not LOCAL_FILE.exists():

    print("ERROR: LOCAL FILE DOES NOT EXIST")

    raise SystemExit(1)


print("Local file exists.")

file_size = LOCAL_FILE.stat().st_size

print("File size:", file_size, "bytes")


# ============================================================
# READ IMAGE
# ============================================================

try:

    with open(LOCAL_FILE, "rb") as file:

        file_data = file.read()

    print("Image loaded successfully.")

except Exception as e:

    print("FAILED TO READ IMAGE")
    print(repr(e))

    raise SystemExit(1)


# ============================================================
# MIME TYPE
# ============================================================

mime_type, _ = mimetypes.guess_type(
    str(LOCAL_FILE)
)

if mime_type is None:

    mime_type = "image/jpeg"


print("MIME type:", mime_type)


# ============================================================
# UPLOAD
# ============================================================

print()
print("=" * 80)
print("UPLOADING IMAGE")
print("=" * 80)

try:

    result = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .upload(
            STORAGE_PATH,
            file_data,
            {
                "content-type": mime_type,
                "upsert": "true"
            }
        )
    )

    print()
    print("UPLOAD SUCCESSFUL")
    print("=" * 80)

    print(result)

except Exception as e:

    print()
    print("UPLOAD FAILED")
    print("=" * 80)

    print("Exception type:")
    print(type(e))

    print()

    print("Exception:")
    print(repr(e))

    print()

    print("Message:")
    print(str(e))

    raise SystemExit(1)


# ============================================================
# CHECK STORAGE
# ============================================================

print()
print("=" * 80)
print("VERIFYING STORAGE")
print("=" * 80)

try:

    items = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .list("products/1")
    )

    print("Items found:", len(items))

    for item in items:

        print(item)

except Exception as e:

    print("STORAGE CHECK FAILED")

    print(repr(e))

    raise SystemExit(1)


# ============================================================
# CHECK IMAGE
# ============================================================

print()
print("=" * 80)
print("CHECKING UPLOADED IMAGE")
print("=" * 80)

image_found = False

for item in items:

    if item.get("name") == LOCAL_FILE.name:

        image_found = True

        break


if image_found:

    print("IMAGE FOUND IN STORAGE")

else:

    print("IMAGE NOT FOUND IN STORAGE")


# ============================================================
# PUBLIC URL
# ============================================================

print()
print("=" * 80)
print("PUBLIC IMAGE URL")
print("=" * 80)

try:

    public_url = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .get_public_url(
            STORAGE_PATH
        )
    )

    print(public_url)

except Exception as e:

    print("FAILED TO GENERATE PUBLIC URL")

    print(repr(e))


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 80)
print("FINAL RESULT")
print("=" * 80)

if image_found:

    print("SUCCESS")
    print()
    print("The image is now stored in Supabase Storage.")
    print()
    print("You can open the PUBLIC IMAGE URL in your browser.")

else:

    print("FAILED")
    print()
    print("The upload did not result in a visible Storage object.")

print("=" * 80)