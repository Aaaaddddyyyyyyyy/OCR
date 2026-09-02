import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from hybrid_search import hybrid_search
from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv(r"E:\OCR_Project\.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found."
    )


LLM_MODEL = "openai/gpt-oss-120b"

PRODUCTS_TABLE = "products"
SPECS_TABLE = "product_specs"
IMAGE_MAP_TABLE = "product_image_map"
IMAGES_TABLE = "product_images"
STORAGE_BUCKET = "product-image"


# ============================================================
# GROQ LLM
# ============================================================

llm = ChatGroq(
    model=LLM_MODEL,
    temperature=0,
    api_key=GROQ_API_KEY,
)


# ============================================================
# FETCH PRODUCT SPECIFICATION
# ============================================================

def fetch_specification(
    product_id: int,
):
    """
    Fetch the specification record for a product.
    """

    response = (
        supabase
        .table(SPECS_TABLE)
        .select("*")
        .eq(
            "product_id",
            product_id,
        )
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return {}


# ============================================================
# FETCH PRODUCT IMAGES
# ============================================================

def fetch_product_images(
    product_id: int,
):
    """
    Fetch images mapped to a product and generate
    public Supabase Storage URLs.
    """

    # --------------------------------------------------------
    # FETCH IMAGE MAPPINGS
    # --------------------------------------------------------

    mapping_response = (
        supabase
        .table(IMAGE_MAP_TABLE)
        .select("image_id")
        .eq(
            "product_id",
            product_id,
        )
        .execute()
    )

    mappings = (
        mapping_response.data
        or []
    )

    image_ids = []

    for mapping in mappings:

        image_id = mapping.get(
            "image_id"
        )

        if image_id is not None:

            image_ids.append(
                image_id
            )

    if not image_ids:
        return []


    # --------------------------------------------------------
    # FETCH IMAGE RECORDS
    # --------------------------------------------------------

    image_response = (
        supabase
        .table(IMAGES_TABLE)
        .select("*")
        .in_(
            "id",
            image_ids,
        )
        .execute()
    )

    images = (
        image_response.data
        or []
    )


    # --------------------------------------------------------
    # PRESERVE MAPPING ORDER
    # --------------------------------------------------------

    image_map = {
        image.get("id"): image
        for image in images
    }


    # --------------------------------------------------------
    # BUILD PUBLIC IMAGE RESPONSE
    # --------------------------------------------------------

    result = []

    for image_id in image_ids:

        image = image_map.get(
            image_id
        )

        if not image:
            continue

        storage_path = image.get(
            "storage_path"
        )

        image_url = None

        if storage_path:

            try:

                image_url = (
                    supabase
                    .storage
                    .from_(
                        STORAGE_BUCKET
                    )
                    .get_public_url(
                        storage_path
                    )
                )

            except Exception as exc:

                print(
                    "WARNING: Could not "
                    f"create image URL for "
                    f"{storage_path}: {exc}"
                )


        result.append(
            {
                "id": image.get(
                    "id"
                ),

                "file_name": image.get(
                    "file_name"
                ),

                "image_type": image.get(
                    "image_type"
                ),

                "storage_path": storage_path,

                "image_url": image_url,

                "mime_type": image.get(
                    "mime_type"
                ),

                "width": image.get(
                    "width"
                ),

                "height": image.get(
                    "height"
                ),

                "created_at": image.get(
                    "created_at"
                ),
            }
        )


    return result


# ============================================================
# BUILD AI CONTEXT
# ============================================================

def build_context(
    results,
):
    """
    Build grounded product context for the Groq model.

    The LLM receives only retrieved catalog information.
    """

    if not results:

        return (
            "No products were found."
        )


    context_parts = []


    for i, result in enumerate(
        results,
        start=1,
    ):

        product_id = result.get(
            "id"
        )

        product_code = result.get(
            "product_code",
            "Unknown",
        )

        product_name = result.get(
            "product_name",
            "Unknown",
        )

        page_number = result.get(
            "page_number",
            "Unknown",
        )


        # ----------------------------------------------------
        # FETCH SPECIFICATION
        # ----------------------------------------------------

        specification = (
            fetch_specification(
                product_id
            )
        )


        # ----------------------------------------------------
        # BUILD CONTEXT
        # ----------------------------------------------------

        context_parts.append(
            f"""
PRODUCT {i}

Product ID: {product_id}
Product Code: {product_code}
Product Name: {product_name}
Page Number: {page_number}

Search Information:
Matched Fields: {result.get("matched_fields", [])}
Hard Mismatches: {result.get("hard_mismatches", [])}
Hybrid Score: {result.get("hybrid_score", 0)}

Specifications:

Housing: {
    specification.get(
        "housing",
        "Not available"
    )
}

Wattage: {
    specification.get(
        "wattage",
        "Not available"
    )
}

LED Source: {
    specification.get(
        "led_source",
        "Not available"
    )
}

Color Temperature: {
    specification.get(
        "color_temperature"
    )
    or specification.get(
        "colour_temperature",
        "Not available"
    )
}

Beam Angle: {
    specification.get(
        "beam_angle",
        "Not available"
    )
}

System Lumens: {
    specification.get(
        "system_lumens",
        "Not available"
    )
}

Product Size: {
    specification.get(
        "product_size",
        "Not available"
    )
}

Cutout: {
    specification.get(
        "cutout",
        "Not available"
    )
}

IP Rating: {
    specification.get(
        "ip_rating",
        "Not available"
    )
}

Outer Frame: {
    specification.get(
        "outer_frame",
        "Not available"
    )
}
"""
        )


    return "\n".join(
        context_parts
    )


# ============================================================
# ENRICH SEARCH RESULTS
# ============================================================

def enrich_results(
    results,
):
    """
    Add product information, specifications and images
    to the hybrid search results.

    Internal embedding vectors are never returned.
    """

    enriched_results = []


    for result in results:

        product_id = result.get(
            "id"
        )

        if product_id is None:
            continue


        # ----------------------------------------------------
        # PRODUCT
        # ----------------------------------------------------

        product = {
            "id": product_id,

            "product_code": result.get(
                "product_code"
            ),

            "product_name": result.get(
                "product_name"
            ),

            "page_number": result.get(
                "page_number"
            ),
        }


        # ----------------------------------------------------
        # SPECIFICATION
        # ----------------------------------------------------

        specification = (
            fetch_specification(
                product_id
            )
        )


        # ----------------------------------------------------
        # IMAGES
        # ----------------------------------------------------

        images = (
            fetch_product_images(
                product_id
            )
        )


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        enriched_results.append(
            {
                "product": product,

                "specifications":
                    specification,

                "images":
                    images,

                "matched_fields":
                    result.get(
                        "matched_fields",
                        [],
                    ),

                "matched_terms":
                    result.get(
                        "matched_terms",
                        [],
                    ),

                "hard_mismatches":
                    result.get(
                        "hard_mismatches",
                        [],
                    ),

                "hybrid_score":
                    result.get(
                        "hybrid_score",
                        0,
                    ),

                "semantic_score":
                    result.get(
                        "semantic_score",
                        0,
                    ),

                "structured_score":
                    result.get(
                        "structured_score",
                        0,
                    ),
            }
        )


    return enriched_results


# ============================================================
# MAIN AI PRODUCT QUERY
# ============================================================

def answer_product_query(
    query: str,
    limit: int = 5,
):
    """
    Complete product question pipeline:

        User Query
             ↓
        Hybrid Search
             ↓
        Product Specifications
             ↓
        Groq AI Answer
             ↓
        Product Images
             ↓
        Final Response
    """

    # --------------------------------------------------------
    # HYBRID SEARCH
    # --------------------------------------------------------

    results = hybrid_search(
        query,
        limit=limit,
    )


    # --------------------------------------------------------
    # BUILD AI CONTEXT
    # --------------------------------------------------------

    context = build_context(
        results
    )


    # --------------------------------------------------------
    # GROQ PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are an AI assistant for a product catalog.

Your job is to answer the user's product question using ONLY
the retrieved catalog information below.

USER QUESTION:
{query}

RETRIEVED CATALOG DATA:
{context}


IMPORTANT RULES:

1. Use ONLY information contained in the retrieved catalog data.

2. Never invent product specifications.

3. Product Code and Product Name are reliable identifiers.

4. If the requested specification exists in the catalog,
   use it directly.

5. If a specification says "Not available", do not guess it.

6. If a product has a hard mismatch for a requested attribute,
   do not claim that it satisfies that attribute.

7. Only list a product as a match if it satisfies ALL
   requested attributes.

8. If no product fully satisfies the user's request,
   clearly say that no exact match was found.

9. You may mention close alternatives separately if useful.

10. Do not treat semantic similarity alone as proof that a
    product satisfies an explicit specification.

11. Keep the answer concise and practical.

12. Do not mention embeddings, vector search, database queries,
    hybrid scores, or internal implementation details.

Answer the user's question now.
"""


    # --------------------------------------------------------
    # GROQ RESPONSE
    # --------------------------------------------------------

    response = llm.invoke(
        prompt
    )


    # --------------------------------------------------------
    # ENRICH RESULTS WITH SPECS + IMAGES
    # --------------------------------------------------------

    enriched_results = (
        enrich_results(
            results
        )
    )


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "query": query,

        "answer": response.content,

        "results":
            enriched_results,
    }


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    query = input(
        "Enter product query: "
    )


    result = answer_product_query(
        query
    )


    print(
        "\n"
        + "=" * 80
    )

    print(
        "AI ANSWER"
    )

    print(
        "=" * 80
    )

    print(
        result["answer"]
    )


    print(
        "\n"
        + "=" * 80
    )

    print(
        "RETRIEVED PRODUCTS"
    )

    print(
        "=" * 80
    )


    for item in result[
        "results"
    ]:

        product = item.get(
            "product",
            {}
        )

        print(
            f"{product.get('product_code')} - "
            f"{product.get('product_name')}"
        )

        print(
            f"Images: "
            f"{len(item.get('images', []))}"
        )