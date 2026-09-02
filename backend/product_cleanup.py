import re

from supabase_client import supabase

# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1

# ============================================================
# CLEAN PRODUCT SIZE
# ============================================================

def clean_product_size(value):
    if not value:
        return value

    value = str(value).strip()

    # OCR commonly reads the diameter symbol incorrectly.
    value = value.replace("@", "Ø")
    value = value.replace("©", "Ø")

    # Known OCR spacing and O/0 errors.
    value = value.replace("H1 20mm", "H120mm")
    value = value.replace("H7Omm", "H70mm")
    value = value.replace("H5Omm", "H50mm")

    return value.rstrip(".")


# ============================================================
# CLEAN CUTOUT
# ============================================================

def clean_cutout(value):
    if not value:
        return value

    value = str(value).strip()
    value = value.replace("@", "Ø")
    value = value.replace("©", "Ø")

    # Retain a valid leading diameter measurement, e.g. Ø75mm or Ø75-80mm.
    match = re.match(
        r"^(Ø\s*\d+(?:\s*-\s*\d+)?\s*mm)",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return re.sub(r"\s+", "", match.group(1))

    return value


# ============================================================
# CLEAN IP RATING
# ============================================================

def clean_ip_rating(value):
    if not value:
        return value

    value = str(value).strip()

    match = re.search(
        r"I\s*P\s*(\d{2})",
        value,
        flags=re.IGNORECASE,
    )
    if match:
        return f"IP{match.group(1)}"

    # OCR can lose the leading "I": P20 -> IP20.
    match = re.search(
        r"\bP\s*(\d{2})\b",
        value,
        flags=re.IGNORECASE,
    )
    if match:
        return f"IP{match.group(1)}"

    return value


# ============================================================
# CLEAN COLOUR TEMPERATURE
# ============================================================

def clean_color_temperature(value):
    if not value:
        return value

    value = str(value).strip()

    # Correct exactly 300K, but do not alter values such as 1300K.
    return re.sub(
        r"\b300\s*K\b",
        "3000K",
        value,
        flags=re.IGNORECASE,
    )


# ============================================================
# GET PRODUCTS
# ============================================================

def get_products():
    response = (
        supabase.table("products")
        .select(
            """
            id,
            product_code,
            page_number,
            product_specs(*)
            """
        )
        .eq("document_id", DOCUMENT_ID)
        .order("page_number")
        .execute()
    )

    return response.data or []


# ============================================================
# UPDATE SPECIFICATION
# ============================================================

def update_specification(spec_id, field, old_value, new_value):
    if old_value == new_value:
        return False

    response = (
        supabase.table("product_specs")
        .update({field: new_value})
        .eq("id", spec_id)
        .execute()
    )

    if not response.data:
        raise RuntimeError(
            f"Failed to update {field} for specification ID {spec_id}"
        )

    print(f"Updated {field}: {old_value} -> {new_value}")
    return True


# ============================================================
# CLEAN PRODUCT
# ============================================================

def clean_product(product):
    product_code = product.get("product_code")
    page_number = product.get("page_number")
    specs = product.get("product_specs")

    if not specs:
        print(f"\nWARNING: No specifications found for {product_code}")
        return 0

    # Supabase may return a joined relationship as a dictionary or list.
    if isinstance(specs, dict):
        spec = specs
    elif isinstance(specs, list):
        spec = specs[0] if specs else None
    else:
        spec = None

    if not spec:
        print(f"\nWARNING: Invalid specifications for {product_code}")
        return 0

    spec_id = spec.get("id")

    if not spec_id:
        print(f"\nWARNING: No specification ID for {product_code}")
        return 0

    print("\n" + "-" * 60)
    print(f"Product: {product_code}")
    print(f"Page: {page_number}")

    changes = 0

    fields_to_clean = {
        "product_size": clean_product_size,
        "cutout": clean_cutout,
        "ip_rating": clean_ip_rating,
        "colour_temperature": clean_color_temperature,
    }

    for field, cleaner in fields_to_clean.items():
        old_value = spec.get(field)
        new_value = cleaner(old_value)

        if update_specification(spec_id, field, old_value, new_value):
            changes += 1

    return changes


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"Reading products for document {DOCUMENT_ID}...")

    products = get_products()
    print(f"Found {len(products)} products.")

    total_changes = 0

    for product in products:
        total_changes += clean_product(product)

    print("\n" + "=" * 60)
    print(f"Products processed: {len(products)}")
    print(f"Total fields cleaned: {total_changes}")
    print("=" * 60)
    print("\nDatabase cleanup completed successfully.")


if __name__ == "__main__":
    main()