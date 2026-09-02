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

    "product_code": [
        r"Product\s*Code\s*[:\-]?\s*([A-Za-z0-9._/\-]+)",
        r"Product\s*No\.?\s*[:\-]?\s*([A-Za-z0-9._/\-]+)",
        r"Code\s*[:\-]?\s*([A-Za-z0-9._/\-]+)"
    ],

    "product_name": [
        r"Product\s*Name\s*[:\-]?\s*(.+)",
        r"Product\s*[:\-]\s*(.+)"
    ],

    "housing": [
        r"Housing\s*[:\-]?\s*(.+)",
        r"Housing\s*Material\s*[:\-]?\s*(.+)"
    ],

    "wattage": [
        r"Wattage\s*[:\-]?\s*(.+)",
        r"Watt\s*[:\-]?\s*(.+)"
    ],

    "led_source": [
        r"LED\s*Source\s*[:\-]?\s*(.+)",
        r"LED\s*[:\-]?\s*(.+)"
    ],

    "color_temperature": [
        r"Col\.?\s*Temp\.?\s*[:\-]?\s*(.+)",
        r"Color\s*Temperature\s*[:\-]?\s*(.+)",
        r"Colour\s*Temperature\s*[:\-]?\s*(.+)"
    ],

    "beam_angle": [
        r"Beam\s*Angle\s*[:\-]?\s*(.+)",
        r"Beam\s*[:\-]?\s*(.+)"
    ],

    "system_lumens": [
        r"System\s*Lumens\s*[:\-]?\s*(.+)",
        r"Lumens\s*[:\-]?\s*(.+)"
    ],

    "product_size": [
        r"Product\s*Size\s*[:\-]?\s*(.+)",
        r"Size\s*[:\-]?\s*(.+)"
    ],

    "cutout": [
        r"Cutout\s*[:\-]?\s*(.+)",
        r"Cut\s*Out\s*[:\-]?\s*(.+)"
    ],

    "ip_rating": [
        r"IP\s*Rating\s*[:\-]?\s*(.+)",
        r"IP\s*[:\-]?\s*(.+)"
    ],

    "outer_frame": [
        r"Outer\s*Frame\s*[:\-]?\s*(.+)",
        r"Frame\s*[:\-]?\s*(.+)"
    ]
}


# ============================================================
# CLEAN OCR VALUE
# ============================================================

def clean_value(value):

    if not value:
        return None

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    value = value.strip(
        " :;-"
    )

    if not value:
        return None

    return value


# ============================================================
# EXTRACT FIELD
# ============================================================

def extract_field(text, patterns):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
            | re.MULTILINE
        )

        if match:

            value = clean_value(
                match.group(1)
            )

            if value:

                return value

    return None


# ============================================================
# EXTRACT ALL PRODUCT DATA
# ============================================================

def extract_product_data(raw_text):

    data = {}

    for field, patterns in FIELD_PATTERNS.items():

        data[field] = extract_field(
            raw_text,
            patterns
        )

    return data


# ============================================================
# GET OCR RESULTS
# ============================================================

def get_ocr_results():

    try:

        response = (
            supabase
            .table("ocr_results")
            .select(
                "id, document_id, page_number, raw_text"
            )
            .eq(
                "document_id",
                DOCUMENT_ID
            )
            .order(
                "page_number"
            )
            .execute()
        )

        return response.data

    except Exception as e:

        print()
        print("FAILED TO FETCH OCR RESULTS")
        print(e)

        return []


# ============================================================
# CHECK PRODUCT
# ============================================================

def product_exists(
    product_code,
    page_number
):

    if not product_code:

        return False

    try:

        response = (
            supabase
            .table("products")
            .select("id")
            .eq(
                "document_id",
                DOCUMENT_ID
            )
            .eq(
                "product_code",
                product_code
            )
            .eq(
                "page_number",
                page_number
            )
            .limit(1)
            .execute()
        )

        return len(response.data) > 0

    except Exception as e:

        print(
            "PRODUCT CHECK FAILED:",
            e
        )

        return False


# ============================================================
# INSERT PRODUCT
# ============================================================

def insert_product(
    product_data,
    page_number
):

    record = {

        "document_id": DOCUMENT_ID,

        "product_code":
            product_data.get(
                "product_code"
            ),

        "product_name":
            product_data.get(
                "product_name"
            ),

        "page_number":
            page_number
    }

    try:

        response = (
            supabase
            .table("products")
            .insert(record)
            .execute()
        )

        if response.data:

            return response.data[0]["id"]

        return None

    except Exception as e:

        print()
        print("PRODUCT INSERT FAILED")
        print(e)

        return None


# ============================================================
# CHECK PRODUCT SPEC
# ============================================================

def product_spec_exists(product_id):

    try:

        response = (
            supabase
            .table("product_spec")
            .select("id")
            .eq(
                "product_id",
                product_id
            )
            .limit(1)
            .execute()
        )

        return len(response.data) > 0

    except Exception as e:

        print(
            "PRODUCT SPEC CHECK FAILED:",
            e
        )

        return False


# ============================================================
# INSERT PRODUCT SPEC
# ============================================================

def insert_product_spec(
    product_id,
    product_data
):

    record = {

        "product_id":
            product_id,

        "housing":
            product_data.get(
                "housing"
            ),

        "wattage":
            product_data.get(
                "wattage"
            ),

        "led_source":
            product_data.get(
                "led_source"
            ),

        "color_temperature":
            product_data.get(
                "color_temperature"
            ),

        "beam_angle":
            product_data.get(
                "beam_angle"
            ),

        "system_lumens":
            product_data.get(
                "system_lumens"
            ),

        "product_size":
            product_data.get(
                "product_size"
            ),

        "cutout":
            product_data.get(
                "cutout"
            ),

        "ip_rating":
            product_data.get(
                "ip_rating"
            ),

        "outer_frame":
            product_data.get(
                "outer_frame"
            )
    }

    try:

        response = (
            supabase
            .table("product_spec")
            .insert(record)
            .execute()
        )

        return True

    except Exception as e:

        print()
        print("PRODUCT SPEC INSERT FAILED")
        print(e)

        return False


# ============================================================
# PROCESS ONE OCR RECORD
# ============================================================

def process_ocr_record(ocr_record):

    page_number = ocr_record[
        "page_number"
    ]

    raw_text = ocr_record[
        "raw_text"
    ]

    print()
    print(
        "-" * 60
    )

    print(
        f"Page: {page_number}"
    )

    # --------------------------------------------------------
    # Extract fields
    # --------------------------------------------------------

    product_data = extract_product_data(
        raw_text
    )

    product_code = product_data.get(
        "product_code"
    )

    print(
        f"Product Code: {product_code}"
    )

    print(
        f"Product Name: "
        f"{product_data.get('product_name')}"
    )

    # --------------------------------------------------------
    # Require product code
    # --------------------------------------------------------

    if not product_code:

        print(
            "WARNING: Product code not found."
        )

        return "skipped"


    # --------------------------------------------------------
    # Check existing product
    # --------------------------------------------------------

    if product_exists(
        product_code,
        page_number
    ):

        print(
            "PRODUCT: ALREADY EXISTS"
        )

        return "skipped"


    # --------------------------------------------------------
    # Insert product
    # --------------------------------------------------------

    product_id = insert_product(
        product_data,
        page_number
    )

    if product_id is None:

        return "failed"


    print(
        f"PRODUCT INSERTED: ID {product_id}"
    )


    # --------------------------------------------------------
    # Insert product specification
    # --------------------------------------------------------

    if product_spec_exists(
        product_id
    ):

        print(
            "PRODUCT SPEC: ALREADY EXISTS"
        )

    else:

        success = insert_product_spec(
            product_id,
            product_data
        )

        if not success:

            return "failed"

        print(
            "PRODUCT SPEC: INSERTED"
        )


    return "success"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print(
        "OCR → PRODUCT DATA EXTRACTION"
    )
    print("=" * 60)

    print(
        f"Document ID: {DOCUMENT_ID}"
    )

    # --------------------------------------------------------
    # Get OCR records
    # --------------------------------------------------------

    ocr_results = get_ocr_results()

    total_records = len(
        ocr_results
    )

    print(
        f"OCR records found: {total_records}"
    )

    if total_records == 0:

        print()
        print(
            "No OCR records found."
        )

        return


    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    successful = 0

    skipped = 0

    failed = 0


    # --------------------------------------------------------
    # Process OCR records
    # --------------------------------------------------------

    for index, ocr_record in enumerate(
        ocr_results,
        start=1
    ):

        print()
        print(
            f"[{index}/{total_records}]"
        )

        result = process_ocr_record(
            ocr_record
        )

        if result == "success":

            successful += 1

        elif result == "skipped":

            skipped += 1

        elif result == "failed":

            failed += 1


    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print(
        f"OCR records found:       {total_records}"
    )

    print(
        f"Products created:        {successful}"
    )

    print(
        f"Existing/skipped:        {skipped}"
    )

    print(
        f"Failed operations:       {failed}"
    )

    print("=" * 60)

    if failed == 0:

        print(
            "PRODUCT DATA EXTRACTION "
            "COMPLETED SUCCESSFULLY"
        )

    else:

        print(
            "PRODUCT DATA EXTRACTION "
            "COMPLETED WITH ERRORS"
        )


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()