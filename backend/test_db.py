from supabase_client import supabase


print("=" * 60)
print("SUPABASE DATABASE TEST")
print("=" * 60)


try:
    response = (
        supabase
        .table("product_images")
        .select("id")
        .limit(1)
        .execute()
    )

    print("DATABASE SELECT: SUCCESS")
    print("Data:", response.data)

except Exception as error:
    print("DATABASE SELECT: FAILED")
    print("Error type:", type(error).__name__)
    print("Error:", error)


print("=" * 60)