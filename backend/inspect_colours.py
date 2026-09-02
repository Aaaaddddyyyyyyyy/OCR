from supabase_client import supabase


response = (
    supabase
    .table("products")
    .select("id, product_code, product_name")
    .execute()
)

products = response.data or []

product_ids = [
    product["id"]
    for product in products
]

spec_response = (
    supabase
    .table("product_specs")
    .select("product_id, outer_frame, housing")
    .in_("product_id", product_ids)
    .execute()
)

specs = spec_response.data or []

spec_map = {
    row["product_id"]: row
    for row in specs
}


print()
print("=" * 90)
print("PRODUCT COLOUR / HOUSING INSPECTION")
print("=" * 90)

for product in products:

    product_id = product["id"]

    spec = spec_map.get(
        product_id,
        {}
    )

    print(
        f"{product_id:>3} | "
        f"{product.get('product_code')} | "
        f"outer_frame={spec.get('outer_frame')} | "
        f"housing={spec.get('housing')}"
    )