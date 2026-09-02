from sentence_transformers import SentenceTransformer

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "all-MiniLM-L6-v2"

MATCH_THRESHOLD = 0.30
MATCH_COUNT = 10


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
# SEMANTIC SEARCH
# ============================================================

def semantic_search(query: str):

    print("=" * 70)
    print(f"QUERY: {query}")
    print("=" * 70)

    # --------------------------------------------------------
    # Generate query embedding
    # --------------------------------------------------------

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    query_embedding = query_embedding.tolist()

    print(f"Query vector dimensions: {len(query_embedding)}")

    # --------------------------------------------------------
    # Call Supabase RPC
    # --------------------------------------------------------

    response = supabase.rpc(
        "match_products",
        {
            "query_embedding": query_embedding,
            "match_threshold": MATCH_THRESHOLD,
            "match_count": MATCH_COUNT,
        }
    ).execute()

    results = response.data or []

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print()
    print(f"Results found: {len(results)}")
    print()

    for index, product in enumerate(results, start=1):

        similarity = product.get("similarity", 0)

        print(
            f"{index}. "
            f"{product.get('product_code')} "
            f"| similarity: {similarity:.4f}"
        )

    print()

    return results


# ============================================================
# TEST QUERIES
# ============================================================

if __name__ == "__main__":

    semantic_search(
        "10 watt tiltable aluminium spotlight"
    )

    semantic_search(
        "warm white adjustable ceiling light"
    )

    semantic_search(
        "black trimless spotlight"
    )