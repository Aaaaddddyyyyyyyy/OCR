import re

from supabase_client import supabase

# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1

# ============================================================
# GET OCR TEXT
# ============================================================

def get_ocr_pages():
    response = (
        supabase.table("ocr_results")
        .select("page_number, raw_text")
        .eq("document_id", DOCUMENT_ID)
        .order("page_number")
        .execute()
    )

    return response.data or []


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
# FIND PRODUCT SECTION
# ============================================================

def find_product_section(raw_text, product_code):
    """Find OCR text from this product code up to the next product code."""
    if not raw_text or not product_code:
        return ""

    escaped_code = re.escape(product_code)

    pattern = (
        rf"Product Code\s*:\s*{escaped_code}"
        rf".*?"
        rf"(?=Product Code\s*:|$)"
    )

    match = re.search(
        pattern,
        raw_text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return match.group(0) if match else ""


# ============================================================
# EXTRACT FIELD FROM OCR SECTION
# ============================================================

def extract_field(section, field_name):
    pattern = rf"{re.escape(field_name)}\s*:\s*(.+?)(?:\n|$)"

    match = re.search(
        pattern,
        section,
        flags=re.IGNORECASE,
    )

    return match.group(1).strip() if match else None


# ============================================================
# NORMALIZATION FUNCTIONS
# ============================================================

def normalize_ip(value):
    if not value:
        return None

    match = re.search(
        r"I\s*P\s*(\d{2})",
        value,
        flags=re.IGNORECASE,
    )
    if match:
        return f"IP{match.group(1)}"

    # Common OCR error: P20 -> IP20
    match = re.search(
        r"\bP\s*(\d{2})\b",
        value,
        flags=re.IGNORECASE,
    )
    if match:
        return f"IP{match.group(1)}"

    return value.strip()


def normalize_temperature(value):
    if not value:
        return None

    value = re.sub(
        r"\b300\s*K\b",
        "3000K",
        value,
        flags=re.IGNORECASE,
    )

    return value.strip()


def normalize_dimension(value):
    if not value:
        return None

    value = value.strip()
    value = value.replace("©", "Ø")
    value = value.replace("@", "Ø")
    value = re.sub(r"\s+", " ", value)

    return value


# ============================================================
# ANALYZE PRODUCT
# ============================================================

def analyze_product(product, ocr_pages):
    product_code = product.get("product_code")
    page_number = product.get("page_number")
    specs = product.get("product_specs")

    if not specs:
        print(f"\nProduct: {product_code}")
        print("WARNING: No specification record found.")
        return

    # Supabase may return a relation as either a dict or a list.
    if isinstance(specs, dict):
        spec = specs
    elif isinstance(specs, list):
        spec = specs[0] if specs else None
    else:
        spec = None

    if not spec:
        print(f"\nProduct: {product_code}")
        print("WARNING: Invalid specification record.")
        return

    raw_text = ""

    for page in ocr_pages:
        if page.get("page_number") == page_number:
            raw_text = page.get("raw_text") or ""
            break

    section = find_product_section(raw_text, product_code)

    print("\n" + "-" * 60)
    print(f"Product: {product_code}")
    print(f"Page: {page_number}")

    if not section:
        print("WARNING: Product section not found in OCR text.")
        return

    fields = {
        "wattage": "Wattage",
        "led_source": "Led Source",
        "colour_temperature": "Col. Temp.",
        "beam_angle": "Beam Angle",
        "system_lumens": "System Lumens",
        "product_size": "Product Size",
        "cutout": "Cutout",
        "ip_rating": "IP Rating",
        "outer_frame": "Outer Frame",
    }

    for database_field, ocr_field in fields.items():
        database_value = spec.get(database_field)
        ocr_value = extract_field(section, ocr_field)

        if ocr_value is None:
            continue

        normalized_value = ocr_value

        if database_field == "ip_rating":
            normalized_value = normalize_ip(ocr_value)

        elif database_field == "colour_temperature":
            normalized_value = normalize_temperature(ocr_value)

        elif database_field in ("product_size", "cutout"):
            normalized_value = normalize_dimension(ocr_value)

        if database_value != normalized_value:
            print(f"\nField: {database_field}")
            print(f"Database  : {database_value}")
            print(f"OCR       : {ocr_value}")
            print(f"Normalized: {normalized_value}")


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"Reading OCR and products for document {DOCUMENT_ID}...")

    ocr_pages = get_ocr_pages()
    products = get_products()

    print(f"Found {len(ocr_pages)} OCR pages.")
    print(f"Found {len(products)} products.")

    for product in products:
        analyze_product(product, ocr_pages)

    print("\n" + "=" * 60)
    print("Normalization analysis completed.")
    print("No database values were modified.")
    print("=" * 60)


if __name__ == "__main__":
    main()