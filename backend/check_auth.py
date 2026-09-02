import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("=" * 70)
print("SUPABASE CONNECTION CHECK")
print("=" * 70)

print("SUPABASE_URL:")
print(url)

print()
print("KEY EXISTS:")
print(bool(key))

print()
print("KEY PREFIX:")
print(key[:20] + "..." if key else "NO KEY")

print()
print("KEY LENGTH:")
print(len(key) if key else 0)

print("=" * 70)

supabase = create_client(url, key)

print("Client created successfully")

print("=" * 70)
print("TESTING STORAGE ACCESS")
print("=" * 70)

try:
    result = supabase.storage.list_buckets()

    print("Storage request successful")
    print("Result:")
    print(result)

except Exception as e:
    print("Storage request FAILED")
    print(type(e))
    print(e)

print("=" * 70)