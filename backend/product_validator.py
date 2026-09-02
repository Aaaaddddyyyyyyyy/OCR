import re

from supabase_client import supabase

# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENT_ID = 1

# ============================================================
# NORMALIZATION FUNCTIONS
# ============================================================

def normalize_ip_rating(value):
    """Clean common OCR noise from IP ratings."""
    if not value:
        return value

    value = value.strip()

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

    return value


def normalize_temperature(value):
    """Normalize known OCR temperature errors."""
    if not value:
        return value

    return re.sub(
        r"\b300\s*K\b",
        "3000K",
        value.strip(),
        flags=re.IGNORECASE,
    )


# ============================================================
# VALIDATION FUNCTIONS
# ============================================================

def validate_wattage(value):
    if not value:
        return True, None

    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*W",
        value.strip(),
        flags=re.IGNORECASE,
    )

    if not match:
        return False, "Invalid wattage format"

    number = float(match.group(1))

    if number <= 0 or number > 200:
        return False, "Suspicious wattage value"

    return True, None


def validate_ip_rating(value):
    if not value:
        return True, None

    normalized = normalize_ip_rating(value)

    if not re.fullmatch(r"IP\d{2}", normalized, flags=re.IGNORECASE):
        return False, f"Suspicious IP rating: {value}"

    return True, None


def validate_temperature(value):
    if not value:
        return True, None

    normalized = normalize_temperature(value)

    temperatures = re.findall(
        r"\d{3,4}\s*K",
        normalized,
        flags=re.IGNORECASE,
    )

    if not temperatures:
        return False, f"No valid temperature found: {value}"

    for temperature in temperatures:
        number = int(re.search(r"\d+", temperature).group())

        if number < 1500 or number > 10000:
            return False, f"Suspicious temperature: {temperature}"

    return True, None


def validate_beam_angle(value):
    if not value:
        return True, None

    angles = re.findall(r"\d+(?:\.\d+)?\s*°", value)

    if not angles:
        return False, f"No valid beam angle found: {value}"

    for angle in angles:
        number = float(re.search(r"\d+(?:\.\d+)?", angle).group())

        if number <= 0 or number > 180:
            return False, f"Suspicious beam angle: {angle}"

    return True, None


def validate_system_lumens(value):
    if not value:
        return True, None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*Lm\s*/\s*W",
        value,
        flags=re.IGNORECASE,
    )

    if not match:
        return False, f"Invalid system lumens: {value}"

    number = float(match.group(1))

    if number <= 0 or number > 300:
        return False, f"Suspicious system lumens: {value}"

    return True, None


def validate_product_size(value):
    if not value:
        return True, None

    if not re.findall(r"\d+(?:\.\d+)?", value):
        return False, f"No dimensions found: {value}"

    return True, None


def validate_cutout(value):
    if not value:
        return True, None

    if not re.findall(r"\d+(?:\.\d+)?", value):
        return False, f"No cutout dimension found: {value}"

    return True, None


# ============================================================
# FETCH PRODUCTS
# ============================================================

def get_products():
    response = (
        supabase.table("products")
        .select(
            """
            id,
            document_id,
            product_code,
            product_name,
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
# VALIDATE PRODUCT
# ============================================================

def validate_product(product):
    issues = []

    product_code = product.get("product_code")
    page_number = product.get("page_number")
    specs = product.get("product_specs")

    print("\n" + "-" * 60)
    print(f"Product: {product_code}")
    print(f"Page: {page_number}")

    if not specs:
        issues.append("No specification record found")
        return issues

    # Supabase can return the relation as either a dictionary or list.
    if isinstance(specs, dict):
        spec = specs
    elif isinstance(specs, list):
        spec = specs[0] if specs else None
    else:
        spec = None

    if not spec:
        issues.append("No specification record found")
        return issues

    validators = {
        "wattage": validate_wattage,
        "colour_temperature": validate_temperature,
        "beam_angle": validate_beam_angle,
        "system_lumens": validate_system_lumens,
        "product_size": validate_product_size,
        "cutout": validate_cutout,
        "ip_rating": validate_ip_rating,
    }

    for field, validator in validators.items():
        value = spec.get(field)
        valid, message = validator(value)

        if not valid:
            issues.append(f"{field}: {message}")

    return issues


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"Reading products for document {DOCUMENT_ID}...")

    products = get_products()
    print(f"Found {len(products)} products.")

    total_valid = 0
    total_suspicious = 0

    for product in products:
        issues = validate_product(product)

        if issues:
            total_suspicious += 1
            print("\nOCR SUSPICIOUS:")

            for issue in issues:
                print(f"  - {issue}")
        else:
            total_valid += 1
            print("Status: VALID")

    print("\n" + "=" * 60)
    print(f"Total products: {len(products)}")
    print(f"Valid products: {total_valid}")
    print(f"Products requiring review: {total_suspicious}")
    print("=" * 60)
    print("\nValidation completed.")


if __name__ == "__main__":
    main()