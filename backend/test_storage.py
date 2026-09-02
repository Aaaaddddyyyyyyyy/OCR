from supabase_client import supabase


BUCKET_NAME = "product-image"


print("=" * 70)
print("SUPABASE STORAGE TEST")
print("=" * 70)

try:
    files = supabase.storage.from_(BUCKET_NAME).list()

    print("Bucket:", BUCKET_NAME)
    print("Connection successful!")
    print("Root files/folders:")

    for item in files:
        print(item)

except Exception as e:
    print("ERROR:")
    print(e)

print("=" * 70)