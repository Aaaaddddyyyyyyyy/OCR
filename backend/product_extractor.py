import re

from supabase_client import supabase

# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1

# ============================================================
# FIELD PATTERNS
# ============================================================

FIELD_PATTERNS = {
    "product_code": r"Product Code\s*:\s*(.+?)(?:\n|$)",
    "housing": r"Housing\s*:\s*(.+?)(?:\n|$)",
    "wattage": r"Wattage\s*:\s*(.+?)(?:\n|$)",
    "led_source": r"Led Source\s*:\s*(.+?)(?:\n|$)",
    "color_temperature": (
        r"(?:Col\.?\s*Temp\.?|Color Temperature)\s*:\s*"
        r"(.+?)(?:\n|$)"
    ),
    "beam_angle": r"Beam Angle\s*:\s*(.+?)(?:\n|$)",
    "system_lumens": r"System Lumens\s*:\s*(.+?)(?:\n|$)",
    "product_size": r"Product Size\s*:\s*(.+?)(?:\n|$)",
    "cutout": r"Cutout\s*:\s*(.+?)(?:\n|$)",
    "ip_rating": r"IP Rating\s*:\s*(.+?)(?:\n|$)",
    "outer_frame": r"Outer Frame\s*:\s*(.+?)(?:\n|$)",
}


def clean_value(value):
    """Clean unnecessary whitespace from an OCR value."""
    if value is None:
        return None

    value = value.strip()
    return re.sub(r"\s+", " ", value)


def extract_field(text, pattern):
    """Extract one field from OCR text."""
    match = re.search(pattern, text, flags=re.IGNORECASE)

    if not match:
        return None

    return clean_value(match.group(1))


def extract_products_from_page(text):
    """Extract all product blocks from one OCR page."""
    matches = list(
        re.finditer(
            r"Product Code\s*:",
            text,
            flags=re.IGNORECASE,
        )
    )

    products = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)

        product_text = text[start:end]
        product_code = extract_field(
            product_text,
            FIELD_PATTERNS["product_code"],
        )

        if not product_code:
            continue

        products.append(
            {
                "product_code": product_code,
                "housing": extract_field(product_text, FIELD_PATTERNS["housing"]),
                "wattage": extract_field(product_text, FIELD_PATTERNS["wattage"]),
                "led_source": extract_field(product_text, FIELD_PATTERNS["led_source"]),
                "colour_temperature": extract_field(
                    product_text,
                    FIELD_PATTERNS["color_temperature"],
                ),
                "beam_angle": extract_field(product_text, FIELD_PATTERNS["beam_angle"]),
                "system_lumens": extract_field(
                    product_text,
                    FIELD_PATTERNS["system_lumens"],
                ),
                "product_size": extract_field(
                    product_text,
                    FIELD_PATTERNS["product_size"],
                ),
                "cutout": extract_field(product_text, FIELD_PATTERNS["cutout"]),
                "ip_rating": extract_field(
                    product_text,
                    FIELD_PATTERNS["ip_rating"],
                ),
                "outer_frame": extract_field(
                    product_text,
                    FIELD_PATTERNS["outer_frame"],
                ),
            }
        )

    return products


def get_ocr_results(document_id):
    """Retrieve OCR pages belonging to a document."""
    response = (
        supabase.table("ocr_results")
        .select("id,document_id,page_number,raw_text")
        .eq("document_id", document_id)
        .order("page_number")
        .execute()
    )

    return response.data or []


def get_existing_product(document_id, product_code, page_number):
    """Return an existing product ID, if present."""
    response = (
        supabase.table("products")
        .select("id")
        .eq("document_id", document_id)
        .eq("product_code", product_code)
        .eq("page_number", page_number)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["id"]

    return None


def get_or_create_product(document_id, page_number, product):
    """Get an existing product or create it."""
    product_code = product["product_code"]

    existing_product_id = get_existing_product(
        document_id,
        product_code,
        page_number,
    )

    if existing_product_id is not None:
        print(f"Product already exists: {product_code} (ID: {existing_product_id})")
        return existing_product_id

    product_record = {
        "document_id": document_id,
        "product_code": product_code,
        "product_name": product_code,
        "page_number": page_number,
    }

    response = supabase.table("products").insert(product_record).execute()

    if not response.data:
        raise RuntimeError(f"Failed to insert product: {product_code}")

    product_id = response.data[0]["id"]
    print(f"Product inserted: {product_code} (ID: {product_id})")
    return product_id


def product_specs_exist(product_id):
    """Check whether specifications already exist for a product."""
    response = (
        supabase.table("product_specs")
        .select("id")
        .eq("product_id", product_id)
        .limit(1)
        .execute()
    )

    return bool(response.data)


def insert_product_specs(product_id, product):
    """Insert a product's specifications if they do not exist."""
    if product_specs_exist(product_id):
        print(f"Specifications already exist for {product['product_code']}")
        return False

    spec_record = {
        "product_id": product_id,
        "housing": product["housing"],
        "wattage": product["wattage"],
        "led_source": product["led_source"],
        "colour_temperature": product["colour_temperature"],
        "beam_angle": product["beam_angle"],
        "system_lumens": product["system_lumens"],
        "product_size": product["product_size"],
        "cutout": product["cutout"],
        "ip_rating": product["ip_rating"],
        "outer_frame": product["outer_frame"],
    }

    response = supabase.table("product_specs").insert(spec_record).execute()

    if not response.data:
        raise RuntimeError(
            f"Failed to insert specifications for {product['product_code']}"
        )

    print(f"Specifications inserted for {product['product_code']}")
    return True


def process_product(document_id, page_number, product):
    """Create/get one product and insert its specifications."""
    product_id = get_or_create_product(document_id, page_number, product)
    specs_inserted = insert_product_specs(product_id, product)

    return product_id, specs_inserted


def main():
    print(f"Reading OCR results for document {DOCUMENT_ID}...")

    pages = get_ocr_results(DOCUMENT_ID)
    print(f"Found {len(pages)} OCR pages.")

    total_detected = 0
    total_products_inserted = 0
    total_specs_inserted = 0
    total_existing = 0

    for page in pages:
        page_number = page["page_number"]
        raw_text = page["raw_text"] or ""

        products = extract_products_from_page(raw_text)

        if not products:
            continue

        print(f"\nPage {page_number}: {len(products)} product(s) detected")

        for product in products:
            total_detected += 1
            product_code = product["product_code"]

            existing_product_id = get_existing_product(
                DOCUMENT_ID,
                product_code,
                page_number,
            )

            if existing_product_id is not None:
                total_existing += 1

            _, specs_inserted = process_product(
                DOCUMENT_ID,
                page_number,
                product,
            )

            if existing_product_id is None:
                total_products_inserted += 1

            if specs_inserted:
                total_specs_inserted += 1

    print("\n" + "=" * 60)
    print(f"Total products detected: {total_detected}")
    print(f"New products inserted: {total_products_inserted}")
    print(f"Existing products encountered: {total_existing}")
    print(f"New specifications inserted: {total_specs_inserted}")
    print("=" * 60)
    print("\nProduct extraction and database insertion completed successfully.")


if __name__ == "__main__":
    main()