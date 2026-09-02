from supabase_client import supabase


def retrieve_product(product_code):
    """
    Retrieve complete product information using product_code.

    Returns:
        dict | None
    """

    # ---------------------------------------------------------
    # 1. GET PRODUCT
    # ---------------------------------------------------------

    product_response = (
        supabase
        .table("products")
        .select("*")
        .eq("product_code", product_code)
        .limit(1)
        .execute()
    )

    if not product_response.data:
        print(f"No product found for product code: {product_code}")
        return None

    product = product_response.data[0]

    product_id = product["id"]

    # ---------------------------------------------------------
    # 2. GET PRODUCT SPECIFICATIONS
    # ---------------------------------------------------------

    specs_response = (
        supabase
        .table("product_specs")
        .select("*")
        .eq("product_id", product_id)
        .limit(1)
        .execute()
    )

    specifications = None

    if specs_response.data:
        specifications = specs_response.data[0]

    # ---------------------------------------------------------
    # 3. GET PRODUCT IMAGES
    # ---------------------------------------------------------

    images_response = (
        supabase
        .table("product_images")
        .select("*")
        .eq("product_id", product_id)
        .order("id")
        .execute()
    )

    images = images_response.data or []

    # ---------------------------------------------------------
    # 4. GET OCR FOR EACH IMAGE
    # ---------------------------------------------------------

    for image in images:

        image_id = image["id"]

        ocr_response = (
            supabase
            .table("ocr_results")
            .select("*")
            .eq("image_id", image_id)
            .order("id")
            .execute()
        )

        image["ocr_results"] = ocr_response.data or []

    # ---------------------------------------------------------
    # 5. BUILD FINAL RESULT
    # ---------------------------------------------------------

    result = {
        "product": product,
        "specifications": specifications,
        "images": images
    }

    return result


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    PRODUCT_CODE = "EX-110 (Tiltable)"

    print("=" * 70)
    print("PRODUCT RETRIEVAL TEST")
    print("=" * 70)

    result = retrieve_product(PRODUCT_CODE)

    if result is None:
        print("Product retrieval failed.")
    else:

        product = result["product"]
        specifications = result["specifications"]
        images = result["images"]

        print("\nPRODUCT")
        print("-" * 70)
        print(f"ID:           {product.get('id')}")
        print(f"Product Code: {product.get('product_code')}")
        print(f"Product Name: {product.get('product_name')}")
        print(f"Page Number:  {product.get('page_number')}")

        print("\nSPECIFICATIONS")
        print("-" * 70)

        if specifications:
            for key, value in specifications.items():
                if key not in ["id", "product_id", "created_at"]:
                    print(f"{key}: {value}")
        else:
            print("No specifications found.")

        print("\nIMAGES")
        print("-" * 70)
        print(f"Total images: {len(images)}")

        for image in images:

            print(f"\nImage ID:   {image.get('id')}")
            print(f"File name:  {image.get('file_name')}")
            print(f"Image path: {image.get('storage_path')}")

            ocr_results = image.get("ocr_results", [])

            print(f"OCR records: {len(ocr_results)}")

            for ocr in ocr_results:

                raw_text = ocr.get("raw_text") or ""

                print("\nOCR TEXT:")
                print(raw_text[:500])

    print("\n" + "=" * 70)
    print("RETRIEVAL TEST COMPLETED")
    print("=" * 70)