import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from hybrid_search import hybrid_search
from supabase_client import supabase


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(r"E:\OCR_Project\.env")


# ============================================================
# GROQ CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found.")


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=GROQ_API_KEY,
)


# ============================================================
# DATABASE TABLES
# ============================================================

PRODUCTS_TABLE = "products"
SPECS_TABLE = "product_specs"


# ============================================================
# FETCH SPECIFICATIONS
# ============================================================

def fetch_specification(product_id):

    response = (
        supabase
        .table(SPECS_TABLE)
        .select("*")
        .eq("product_id", product_id)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return {}


# ============================================================
# BUILD PRODUCT CONTEXT
# ============================================================

def build_context(results):

    if not results:
        return "No products were found."

    context_parts = []

    for i, result in enumerate(results, start=1):

        product_id = result.get("id")

        product_code = result.get(
            "product_code",
            "Unknown"
        )

        product_name = result.get(
            "product_name",
            "Unknown"
        )

        page_number = result.get(
            "page_number",
            "Unknown"
        )

        # Fetch specification from Supabase
        specification = fetch_specification(product_id)

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
Housing: {specification.get("housing", "Not available")}
Wattage: {specification.get("wattage", "Not available")}
LED Source: {specification.get("led_source", "Not available")}
Color Temperature: {specification.get("color_temperature", "Not available")}
Beam Angle: {specification.get("beam_angle", "Not available")}
System Lumens: {specification.get("system_lumens", "Not available")}
Product Size: {specification.get("product_size", "Not available")}
Cutout: {specification.get("cutout", "Not available")}
IP Rating: {specification.get("ip_rating", "Not available")}
Outer Frame: {specification.get("outer_frame", "Not available")}
"""
        )

    return "\n".join(context_parts)


# ============================================================
# AI ANSWER
# ============================================================

def answer_product_query(query: str, limit: int = 5):

    # --------------------------------------------------------
    # 1. Hybrid Search
    # --------------------------------------------------------

    results = hybrid_search(
        query,
        limit=limit
    )

    # --------------------------------------------------------
    # 2. Build Context
    # --------------------------------------------------------

    context = build_context(results)

    print("\n" + "=" * 80)
    print("CONTEXT SENT TO GROQ")
    print("=" * 80)
    print(context)

    # --------------------------------------------------------
    # 3. Groq Prompt
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
7. If no product fully satisfies the user's request, clearly
   say so.
8. You may mention the closest matching products if useful.
9. Keep the answer concise and practical.
10. Do not mention embeddings, vector search, database queries,
    hybrid scores, or internal implementation details.

Answer the user's question now.
"""

    # --------------------------------------------------------
    # 4. Call Groq
    # --------------------------------------------------------

    response = llm.invoke(prompt)

    # --------------------------------------------------------
    # 5. Return Result
    # --------------------------------------------------------

    return {
        "query": query,
        "answer": response.content,
        "results": results,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    query = input("Enter product query: ")

    result = answer_product_query(query)

    print("\n" + "=" * 80)
    print("AI ANSWER")
    print("=" * 80)

    print(result["answer"])

    print("\n" + "=" * 80)
    print("RETRIEVED PRODUCTS")
    print("=" * 80)

    for item in result["results"]:

        print(
            f"{item.get('product_code')} - "
            f"{item.get('product_name')}"
        )