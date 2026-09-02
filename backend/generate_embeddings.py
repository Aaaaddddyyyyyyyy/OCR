from sentence_transformers import SentenceTransformer
from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

PRODUCTS_TABLE = "products"
PRODUCT_SPECS_TABLE = "product_specs"

MODEL_NAME = "all-MiniLM-L6-v2"


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 70)
print("LOADING EMBEDDING MODEL")
print("=" * 70)

model = SentenceTransformer(MODEL_NAME)

print(f"Model loaded: {MODEL_NAME}")
print()


# ============================================================
# FETCH PRODUCTS
# ============================================================

print("=" * 70)
print("FETCHING PRODUCTS")
print("=" * 70)

products_response = (
    supabase
    .table(PRODUCTS_TABLE)
    .select("*")
    .order("id")
    .execute()
)

products = products_response.data or []

print(f"Products found: {len(products)}")
print()


# ============================================================
# BUILD PRODUCT TEXT
# ============================================================

def build_product_text(product, spec):

    parts = []

    # ========================================================
    # PRODUCT INFORMATION
    # ========================================================

    product_code = product.get("product_code")
    product_name = product.get("product_name")

    if product_code:
        parts.append(
            f"Product Code: {product_code}"
        )

    if product_name:
        parts.append(
            f"Product Name: {product_name}"
        )

    # ========================================================
    # SPECIFICATIONS
    # ========================================================

    if spec:

        field_labels = {
            "housing": "Housing",
            "wattage": "Wattage",
            "led_source": "LED Source",
            "colour_temperature": "Colour Temperature",
            "beam_angle": "Beam Angle",
            "system_lumens": "System Lumens",
            "product_size": "Product Size",
            "cutout": "Cutout",
            "ip_rating": "IP Rating",
            "outer_frame": "Outer Frame",
        }

        for field, label in field_labels.items():

            value = spec.get(field)

            if value is not None and str(value).strip():

                parts.append(
                    f"{label}: {value}"
                )

        # ====================================================
        # NATURAL-LANGUAGE TEMPERATURE TERMS
        # ====================================================

        colour_temperature = str(
            spec.get("colour_temperature") or ""
        ).lower()

        if "3000k" in colour_temperature:

            parts.append(
                "Warm White"
            )

            parts.append(
                "Warm Lighting"
            )

        if "4000k" in colour_temperature:

            parts.append(
                "Cool White"
            )

            parts.append(
                "Neutral White"
            )

        if "2700k" in colour_temperature:

            parts.append(
                "Warm White"
            )

        if "6000k" in colour_temperature:

            parts.append(
                "Daylight White"
            )

        # ====================================================
        # FEATURE TERMS FROM PRODUCT NAME / CODE
        # ====================================================

        combined_text = " ".join([
            str(product_code or ""),
            str(product_name or "")
        ]).lower()

        if "tiltable" in combined_text:

            parts.append(
                "Tiltable"
            )

            parts.append(
                "Adjustable"
            )

            parts.append(
                "Adjustable Spotlight"
            )

        if "adjustable" in combined_text:

            parts.append(
                "Adjustable"
            )

            parts.append(
                "Adjustable Spotlight"
            )

        if "trimless" in combined_text:

            parts.append(
                "Trimless"
            )

            parts.append(
                "Trimless Spotlight"
            )

        if "surface" in combined_text:

            parts.append(
                "Surface Mounted"
            )

        if "recessed" in combined_text:

            parts.append(
                "Recessed"
            )

        if "fixed" in combined_text:

            parts.append(
                "Fixed"
            )

    # ========================================================
    # RETURN SEARCH TEXT
    # ========================================================

    return "\n".join(parts)

    # --------------------------------------------------------
    # PRODUCT INFORMATION
    # --------------------------------------------------------

    if product.get("product_code"):
        parts.append(
            f"Product Code: {product['product_code']}"
        )

    if product.get("product_name"):
        parts.append(
            f"Product Name: {product['product_name']}"
        )

    # --------------------------------------------------------
    # SPECIFICATIONS
    # --------------------------------------------------------

    if spec:

        field_labels = {
            "housing": "Housing",
            "wattage": "Wattage",
            "led_source": "LED Source",
            "colour_temperature": "Colour Temperature",
            "beam_angle": "Beam Angle",
            "system_lumens": "System Lumens",
            "product_size": "Product Size",
            "cutout": "Cutout",
            "ip_rating": "IP Rating",
            "outer_frame": "Outer Frame",
        }

        for field, label in field_labels.items():

            value = spec.get(field)

            if value is not None and str(value).strip():

                parts.append(
                    f"{label}: {value}"
                )

    # --------------------------------------------------------
    # RETURN SEARCH TEXT
    # --------------------------------------------------------

    return "\n".join(parts)


# ============================================================
# PROCESS PRODUCTS
# ============================================================

print("=" * 70)
print("GENERATING PRODUCT EMBEDDINGS")
print("=" * 70)

updated = 0
failed = 0


for product in products:

    product_id = product["id"]

    try:

        # ----------------------------------------------------
        # FETCH SPECIFICATION
        # ----------------------------------------------------

        spec_response = (
            supabase
            .table(PRODUCT_SPECS_TABLE)
            .select("*")
            .eq("product_id", product_id)
            .limit(1)
            .execute()
        )

        specs = spec_response.data or []

        spec = specs[0] if specs else None

        # ----------------------------------------------------
        # BUILD TEXT
        # ----------------------------------------------------

        product_text = build_product_text(
            product,
            spec
        )

        print("-" * 70)
        print(f"Product ID: {product_id}")
        print(f"Code: {product.get('product_code')}")
        print()
        print("Search text:")
        print(product_text)
        print()

        # ----------------------------------------------------
        # GENERATE EMBEDDING
        # ----------------------------------------------------

        embedding = model.encode(
            product_text,
            normalize_embeddings=True
        )

        embedding = embedding.tolist()

        print(
            f"Embedding dimensions: {len(embedding)}"
        )

        # ----------------------------------------------------
        # UPDATE DATABASE
        # ----------------------------------------------------

        (
            supabase
            .table(PRODUCTS_TABLE)
            .update({
                "embedding": embedding
            })
            .eq("id", product_id)
            .execute()
        )

        updated += 1

        print("Status: UPDATED")

    except Exception as e:

        failed += 1

        print("Status: FAILED")
        print(f"Error: {e}")


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 70)
print("FINAL RESULT")
print("=" * 70)

print(f"Total products: {len(products)}")
print(f"Embeddings generated: {updated}")
print(f"Failed: {failed}")

print("=" * 70)