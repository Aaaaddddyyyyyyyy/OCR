import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# ============================================================
# PATH CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_DIR / "backend"

if not BACKEND_DIR.exists():
    raise RuntimeError(f"Backend folder not found: {BACKEND_DIR}")

sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# BACKEND IMPORTS
# ============================================================

from supabase_client import supabase
from hybrid_search import hybrid_search
from ai_answer import answer_product_query


# ============================================================
# CONFIGURATION
# ============================================================

PRODUCTS_TABLE = "products"
SPECS_TABLE = "product_specs"
MAPPING_TABLE = "product_image_map"
IMAGES_TABLE = "product_images"
STORAGE_BUCKET = "product-image"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="OCR Product Retrieval API",
    description="AI-powered OCR product retrieval with specifications and images",
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# IMAGE URL
# ============================================================

def create_image_url(storage_path):

    if not storage_path:
        return None

    try:
        return (
            supabase
            .storage
            .from_(STORAGE_BUCKET)
            .get_public_url(storage_path)
        )

    except Exception as e:
        print(
            f"WARNING: Could not create image URL "
            f"for {storage_path}: {e}"
        )
        return None


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "OCR Product Retrieval API is running",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "all_products": "/products",
            "ai_product_query": "/products/ask",
            "product_search": "/products/search",
            "product_by_code": "/products/{product_code}",
            "product_by_id": "/products/id/{product_id}"
        }
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():

    try:

        (
            supabase
            .table(PRODUCTS_TABLE)
            .select("id")
            .limit(1)
            .execute()
        )

        return {
            "status": "healthy",
            "supabase": "connected"
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "supabase": "connection failed",
            "error": str(e)
        }


# ============================================================
# ALL PRODUCTS
# ============================================================

@app.get("/products")
def get_all_products():

    try:

        response = (
            supabase
            .table(PRODUCTS_TABLE)
            .select(
                "id, product_code, product_name, "
                "page_number, document_id"
            )
            .order("id")
            .execute()
        )

        products = response.data or []

        return {
            "success": True,
            "count": len(products),
            "products": products
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve products: {str(e)}"
        )


# ============================================================
# PRODUCT SEARCH
# ============================================================

@app.get("/products/search")
def search_products(
    q: str = Query(
        ...,
        min_length=1,
        description="Product search query"
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=20
    ),
):

    try:

        results = hybrid_search(
            q,
            limit=limit
        )

        # Never expose embeddings
        for result in results:

            result.pop("embedding", None)

        return {
            "query": q,
            "count": len(results),
            "results": results
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Product search failed: {str(e)}"
        )


# ============================================================
# AI PRODUCT QUERY
# ============================================================

@app.get("/products/ask")
def ask_product(
    q: str = Query(
        ...,
        min_length=1,
        description="Natural-language product question"
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=10
    ),
):

    try:

        result = answer_product_query(
            query=q,
            limit=limit
        )

        return {
            "query": result["query"],
            "answer": result["answer"],
            "results": result["results"]
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"AI product query failed: {str(exc)}"
        )


# ============================================================
# PRODUCT BY CODE
# ============================================================

@app.get("/products/{product_code}")
def get_product(product_code: str):

    try:

        response = (
            supabase
            .table(PRODUCTS_TABLE)
            .select("*")
            .eq("product_code", product_code)
            .limit(1)
            .execute()
        )

        if not response.data:

            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {product_code}"
            )

        product = response.data[0]

        product_id = product["id"]

        # ----------------------------------------------------
        # Specifications
        # ----------------------------------------------------

        specs_response = (
            supabase
            .table(SPECS_TABLE)
            .select("*")
            .eq("product_id", product_id)
            .limit(1)
            .execute()
        )

        specifications = (
            specs_response.data[0]
            if specs_response.data
            else {}
        )

        # ----------------------------------------------------
        # Image mappings
        # ----------------------------------------------------

        mapping_response = (
            supabase
            .table(MAPPING_TABLE)
            .select("image_id")
            .eq("product_id", product_id)
            .order("image_id")
            .execute()
        )

        image_ids = [
            row["image_id"]
            for row in (mapping_response.data or [])
        ]

        images = []

        if image_ids:

            images_response = (
                supabase
                .table(IMAGES_TABLE)
                .select("*")
                .in_("id", image_ids)
                .execute()
            )

            image_lookup = {
                image["id"]: image
                for image in (images_response.data or [])
            }

            for image_id in image_ids:

                image = image_lookup.get(image_id)

                if not image:
                    continue

                image["image_url"] = create_image_url(
                    image.get("storage_path")
                )

                images.append(image)

        return {
            "product": product,
            "specifications": specifications,
            "images": images
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve product: {str(e)}"
        )


# ============================================================
# PRODUCT BY ID
# ============================================================

@app.get("/products/id/{product_id}")
def get_product_by_id(product_id: int):

    try:

        response = (
            supabase
            .table(PRODUCTS_TABLE)
            .select("*")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )

        if not response.data:

            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {product_id}"
            )

        product = response.data[0]

        # ----------------------------------------------------
        # Specifications
        # ----------------------------------------------------

        specs_response = (
            supabase
            .table(SPECS_TABLE)
            .select("*")
            .eq("product_id", product_id)
            .limit(1)
            .execute()
        )

        specifications = (
            specs_response.data[0]
            if specs_response.data
            else {}
        )

        # ----------------------------------------------------
        # Image mappings
        # ----------------------------------------------------

        mapping_response = (
            supabase
            .table(MAPPING_TABLE)
            .select("image_id")
            .eq("product_id", product_id)
            .order("image_id")
            .execute()
        )

        image_ids = [
            row["image_id"]
            for row in (mapping_response.data or [])
        ]

        images = []

        if image_ids:

            images_response = (
                supabase
                .table(IMAGES_TABLE)
                .select("*")
                .in_("id", image_ids)
                .execute()
            )

            image_lookup = {
                image["id"]: image
                for image in (images_response.data or [])
            }

            for image_id in image_ids:

                image = image_lookup.get(image_id)

                if not image:
                    continue

                image["image_url"] = create_image_url(
                    image.get("storage_path")
                )

                images.append(image)

        return {
            "product": product,
            "specifications": specifications,
            "images": images
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve product: {str(e)}"
        )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )