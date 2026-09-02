import re

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    """
    Clean common OCR artifacts while preserving useful data.
    """
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # Remove obvious HTML fragments
    value = re.sub(r"<[^>]+>", "", value)

    # Normalize multiple spaces
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def clean_dimension(value):
    """
    Fix common OCR mistakes in dimension/cutout values.
    """

    if value is None:
        return None

    value = clean_text(value)

    if value is None:
        return None

    # Common OCR mistake:
    # B65xH48mm -> Ø65xH48mm
    value = re.sub(
        r"^[Bb](\d+xH\d+mm)$",
        r"Ø\1",
        value
    )

    # Remove accidental leading OCR characters
    value = re.sub(
        r"^[A-Za-z]\s*(\d+)",
        r"\1",
        value
    )

    # Normalize spaces around x
    value = re.sub(r"\s*x\s*", "x", value)

    return value


def clean_cutout(value):
    """
    Clean cutout values.
    """

    if value is None:
        return None

    value = clean_text(value)

    if value is None:
        return None

    # Common OCR error:
    # 255mm -> 55mm
    #
    # Only apply this when the value is exactly 255mm.
    # This prevents blindly modifying legitimate values.
    if value.lower() == "255mm":
        value = "55mm"

    # G48mm / G 48mm -> 48mm
    value = re.sub(
        r"^[Gg]\s*(\d+mm)$",
        r"\1",
        value
    )

    return value


def clean_wattage(value):
    """
    Normalize wattage.
    """

    if value is None:
        return None

    value = clean_text(value)

    if value is None:
        return None

    # Normalize spaces
    value = re.sub(r"\s+", "", value)

    # 12 W -> 12W
    value = re.sub(r"^(\d+)[Ww]$", r"\1W", value)

    return value


def clean_ip_rating(value):
    """
    Normalize IP rating.
    """

    if value is None:
        return None

    value = clean_text(value)

    if value is None:
        return None

    value = value.upper()

    # Common OCR variants
    value = value.replace("IP 20", "IP20")

    return value


def clean_system_lumens(value):
    """
    Normalize system lumens.
    """

    if value is None:
        return None

    value = clean_text(value)

    if value is None:
        return None

    value = value.replace(" ", "")

    return value


# ============================================================
# FETCH DATA
# ============================================================

def fetch_products():
    print("Fetching products...")

    response = (
        supabase
        .table("products")
        .select("*")
        .eq("document_id", DOCUMENT_ID)
        .order("id")
        .execute()
    )

    products = response.data or []

    print(f"Products found: {len(products)}")

    return products


def fetch_specs():
    print("Fetching product specifications...")

    response = (
        supabase
        .table("product_specs")
        .select("*")
        .order("product_id")
        .execute()
    )

    specs = response.data or []

    print(f"Specification records found: {len(specs)}")

    return specs


# ============================================================
# UPDATE SPECIFICATION
# ============================================================

def update_spec(spec_id, data):
    """
    Update only the fields that actually changed.
    """

    if not data:
        return False

    try:
        (
            supabase
            .table("product_specs")
            .update(data)
            .eq("id", spec_id)
            .execute()
        )

        return True

    except Exception as error:
        print(f"ERROR updating spec {spec_id}: {error}")
        return False


# ============================================================
# VALIDATE PRODUCT
# ============================================================

def validate_product(product):
    """
    Validate product-level information.
    """

    product_id = product["id"]

    product_code = clean_text(product.get("product_code"))
    product_name = clean_text(product.get("product_name"))

    updates = {}

    if product_code != product.get("product_code"):
        updates["product_code"] = product_code

    if product_name != product.get("product_name"):
        updates["product_name"] = product_name

    if updates:

        try:
            (
                supabase
                .table("products")
                .update(updates)
                .eq("id", product_id)
                .execute()
            )

            print(
                f"Updated product {product_id}: "
                f"{product_code}"
            )

        except Exception as error:
            print(
                f"ERROR updating product "
                f"{product_id}: {error}"
            )


# ============================================================
# VALIDATE SPECIFICATION
# ============================================================

def validate_spec(spec):
    """
    Validate and normalize specification values.
    """

    spec_id = spec["id"]

    updates = {}

    fields = {
        "housing": clean_text(spec.get("housing")),
        "wattage": clean_wattage(spec.get("wattage")),
        "led_source": clean_text(spec.get("led_source")),
        "colour_temperature": clean_text(
            spec.get("colour_temperature")
        ),
        "beam_angle": clean_text(
            spec.get("beam_angle")
        ),
        "system_lumens": clean_system_lumens(
            spec.get("system_lumens")
        ),
        "product_size": clean_dimension(
            spec.get("product_size")
        ),
        "cutout": clean_cutout(
            spec.get("cutout")
        ),
        "ip_rating": clean_ip_rating(
            spec.get("ip_rating")
        ),
        "outer_frame": clean_text(
            spec.get("outer_frame")
        ),
    }

    for field, new_value in fields.items():

        old_value = spec.get(field)

        if new_value != old_value:
            updates[field] = new_value

    if updates:

        if update_spec(spec_id, updates):

            print(
                f"Updated spec {spec_id} "
                f"(product_id={spec.get('product_id')})"
            )

            for field, value in updates.items():
                print(
                    f"    {field}: "
                    f"{spec.get(field)} -> {value}"
                )

            return True

    return False


# ============================================================
# CHECK PRODUCT-SPEC RELATIONSHIPS
# ============================================================

def validate_relationships(products, specs):

    print()
    print("=" * 60)
    print("CHECKING PRODUCT-SPEC RELATIONSHIPS")
    print("=" * 60)

    product_ids = {
        product["id"]
        for product in products
    }

    orphan_specs = []

    for spec in specs:

        product_id = spec.get("product_id")

        if product_id not in product_ids:
            orphan_specs.append(spec)

    if orphan_specs:

        print(
            f"WARNING: {len(orphan_specs)} "
            f"orphan specification records found."
        )

        for spec in orphan_specs:
            print(
                f"  Spec ID: {spec['id']} "
                f"Product ID: {spec.get('product_id')}"
            )

    else:

        print(
            "All specification records are linked "
            "to valid products."
        )


# ============================================================
# CHECK DUPLICATE PRODUCT CODES
# ============================================================

def check_duplicate_products(products):

    print()
    print("=" * 60)
    print("CHECKING DUPLICATE PRODUCT CODES")
    print("=" * 60)

    product_codes = {}

    for product in products:

        code = product.get("product_code")

        if not code:
            continue

        code = code.strip()

        if code not in product_codes:
            product_codes[code] = []

        product_codes[code].append(product["id"])

    duplicates = {
        code: ids
        for code, ids in product_codes.items()
        if len(ids) > 1
    }

    if duplicates:

        print("Duplicate product codes found:")

        for code, ids in duplicates.items():
            print(
                f"  {code}: IDs {ids}"
            )

    else:

        print("No duplicate product codes found.")


# ============================================================
# PRINT FINAL DATA
# ============================================================

def print_summary(products, specs):

    print()
    print("=" * 60)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Products:             {len(products)}"
    )

    print(
        f"Specification records: {len(specs)}"
    )

    product_ids = {
        product["id"]
        for product in products
    }

    valid_specs = [
        spec
        for spec in specs
        if spec.get("product_id") in product_ids
    ]

    print(
        f"Valid relationships:  {len(valid_specs)}"
    )

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRODUCT DATA VALIDATION PIPELINE")
    print("=" * 60)

    products = fetch_products()

    specs = fetch_specs()

    if not products:

        print()
        print("No products found.")

        return

    if not specs:

        print()
        print("No specification records found.")

        return

    # --------------------------------------------------------
    # Validate products
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("VALIDATING PRODUCTS")
    print("=" * 60)

    for product in products:

        validate_product(product)

    # --------------------------------------------------------
    # Validate specifications
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("VALIDATING SPECIFICATIONS")
    print("=" * 60)

    updated_count = 0

    for spec in specs:

        changed = validate_spec(spec)

        if changed:
            updated_count += 1

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    validate_relationships(
        products,
        specs
    )

    # --------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------

    check_duplicate_products(products)

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print_summary(
        products,
        specs
    )

    print()
    print(
        f"Specification records updated: "
        f"{updated_count}"
    )

    print()
    print("=" * 60)
    print("VALIDATION PIPELINE COMPLETED")
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()