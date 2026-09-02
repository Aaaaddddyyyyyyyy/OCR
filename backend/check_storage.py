from supabase_client import supabase


BUCKET_NAME = "product-image"


print()
print("=" * 80)
print("SUPABASE STORAGE PATH DIAGNOSTIC")
print("=" * 80)


# ============================================================
# 1. CHECK BUCKET ROOT
# ============================================================

print()
print("1. CHECKING BUCKET ROOT")
print("-" * 80)

try:

    files = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .list()
    )

    print("Bucket:", BUCKET_NAME)
    print("Items found:", len(files))

    if files:

        for item in files:

            print(item)

    else:

        print("ROOT IS EMPTY")


except Exception as e:

    print("ERROR:")
    print(e)


# ============================================================
# 2. CHECK products FOLDER
# ============================================================

print()
print("=" * 80)
print("2. CHECKING products/ FOLDER")
print("=" * 80)

try:

    files = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .list(
            "products"
        )
    )

    print("Items found:", len(files))

    if files:

        for item in files:

            print(item)

    else:

        print("products/ FOLDER IS EMPTY OR DOES NOT EXIST")


except Exception as e:

    print("ERROR:")
    print(e)


# ============================================================
# 3. CHECK products/1 FOLDER
# ============================================================

print()
print("=" * 80)
print("3. CHECKING products/1/ FOLDER")
print("=" * 80)

try:

    files = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .list(
            "products/1"
        )
    )

    print("Items found:", len(files))

    if files:

        for item in files:

            print(item)

    else:

        print("products/1/ FOLDER IS EMPTY OR DOES NOT EXIST")


except Exception as e:

    print("ERROR:")
    print(e)


# ============================================================
# 4. TEST THE EXACT IMAGE
# ============================================================

IMAGE_PATH = "products/1/page_09_image_01.jpeg"

print()
print("=" * 80)
print("4. TESTING EXACT IMAGE")
print("=" * 80)

print("Bucket:", BUCKET_NAME)
print("Path:", IMAGE_PATH)


try:

    image_data = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .download(IMAGE_PATH)
    )

    print()
    print("SUCCESS!")
    print("Image exists in Supabase Storage.")
    print("Downloaded bytes:", len(image_data))


except Exception as e:

    print()
    print("IMAGE DOES NOT EXIST AT THIS PATH")
    print(e)


# ============================================================
# 5. GENERATE PUBLIC URL
# ============================================================

print()
print("=" * 80)
print("5. PUBLIC URL")
print("=" * 80)

try:

    public_url = (
        supabase
        .storage
        .from_(BUCKET_NAME)
        .get_public_url(IMAGE_PATH)
    )

    print(public_url)

except Exception as e:

    print("ERROR:")
    print(e)


print()
print("=" * 80)
print("STORAGE DIAGNOSTIC COMPLETED")
print("=" * 80)