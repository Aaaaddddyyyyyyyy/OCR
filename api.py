import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_DIR / "backend"

if not BACKEND_DIR.exists():
    raise RuntimeError(
        f"Backend folder not found: {BACKEND_DIR}"
    )

sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# SUPABASE
# ============================================================

from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

PRODUCTS_TABLE = "products"
SPECS_TABLE = "product_specs"
MAPPING_TABLE = "product_image_map"
IMAGES_TABLE = "product_images"

STORAGE_BUCKET = "product-image"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="OCR Product Retrieval API",
    description="API for retrieving products, specifications and images",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# CREATE STORAGE URL
# ============================================================

def create_image_url(storage_path):

    if not storage_path:
        return None

    try:

        response = (
            supabase
            .storage
            .from_(STORAGE_BUCKET)
            .get_public_url(storage_path)
        )

        return response

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
        "version": "1.0.0",

        "endpoints": {
            "health": "/health",
            "all_products": "/products",
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
# PRODUCT BY CODE
# ============================================================

@app.get("/products/{product_code}")
def get_product(product_code: str):

    try:

        # ----------------------------------------------------
        # FETCH PRODUCT
        # ----------------------------------------------------

        product_response = (
            supabase
            .table(PRODUCTS_TABLE)
            .select(
                "id, product_code, product_name, "
                "page_number, document_id, created_at"
            )
            .eq(
                "product_code",
                product_code
            )
            .limit(1)
            .execute()
        )

        products = product_response.data or []

        if not products:

            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {product_code}"
            )

        product = products[0]

        product_id = product["id"]


        # ----------------------------------------------------
        # FETCH SPECIFICATIONS
        # ----------------------------------------------------

        specs_response = (
            supabase
            .table(SPECS_TABLE)
            .select("*")
            .eq(
                "product_id",
                product_id
            )
            .order("id")
            .execute()
        )

        specifications = specs_response.data or []


        # ----------------------------------------------------
        # FETCH IMAGE MAPPINGS
        # ----------------------------------------------------

        mapping_response = (
            supabase
            .table(MAPPING_TABLE)
            .select("*")
            .eq(
                "product_id",
                product_id
            )
            .order("id")
            .execute()
        )

        mappings = mapping_response.data or []


        # ----------------------------------------------------
        # EXTRACT IMAGE IDS
        # ----------------------------------------------------

        image_ids = []

        for mapping in mappings:

            image_id = mapping.get("image_id")

            if image_id is not None:

                image_ids.append(image_id)


        # ----------------------------------------------------
        # FETCH IMAGES
        # ----------------------------------------------------

        images = []

        if image_ids:

            images_response = (
                supabase
                .table(IMAGES_TABLE)
                .select("*")
                .in_(
                    "id",
                    image_ids
                )
                .order("id")
                .execute()
            )

            images = images_response.data or []


        # ----------------------------------------------------
        # CREATE IMAGE RESPONSE
        # ----------------------------------------------------

        image_results = []

        for image in images:

            storage_path = image.get(
                "storage_path"
            )

            image_results.append(
                {
                    "id": image.get("id"),

                    "file_name": image.get(
                        "file_name"
                    ),

                    "image_type": image.get(
                        "image_type"
                    ),

                    "storage_path": storage_path,

                    "image_url": create_image_url(
                        storage_path
                    ),

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
                    )
                }
            )


        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        return {

            "success": True,

            "product": {

                "id": product.get(
                    "id"
                ),

                "product_code": product.get(
                    "product_code"
                ),

                "product_name": product.get(
                    "product_name"
                ),

                "page_number": product.get(
                    "page_number"
                ),

                "document_id": product.get(
                    "document_id"
                ),

                "created_at": product.get(
                    "created_at"
                )
            },

            "specifications":
                specifications,

            "images":
                image_results,

            "summary": {

                "specifications_count":
                    len(specifications),

                "image_mappings_count":
                    len(mappings),

                "images_count":
                    len(image_results)
            }
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

        # ----------------------------------------------------
        # FETCH PRODUCT
        # ----------------------------------------------------

        product_response = (
            supabase
            .table(PRODUCTS_TABLE)
            .select("*")
            .eq(
                "id",
                product_id
            )
            .limit(1)
            .execute()
        )

        products = product_response.data or []

        if not products:

            raise HTTPException(
                status_code=404,
                detail=f"Product ID not found: {product_id}"
            )

        product = products[0]


        # ----------------------------------------------------
        # FETCH SPECIFICATIONS
        # ----------------------------------------------------

        specs_response = (
            supabase
            .table(SPECS_TABLE)
            .select("*")
            .eq(
                "product_id",
                product_id
            )
            .order("id")
            .execute()
        )

        specifications = specs_response.data or []


        # ----------------------------------------------------
        # FETCH MAPPINGS
        # ----------------------------------------------------

        mapping_response = (
            supabase
            .table(MAPPING_TABLE)
            .select("*")
            .eq(
                "product_id",
                product_id
            )
            .order("id")
            .execute()
        )

        mappings = mapping_response.data or []


        # ----------------------------------------------------
        # IMAGE IDS
        # ----------------------------------------------------

        image_ids = []

        for mapping in mappings:

            image_id = mapping.get(
                "image_id"
            )

            if image_id is not None:

                image_ids.append(
                    image_id
                )


        # ----------------------------------------------------
        # FETCH IMAGES
        # ----------------------------------------------------

        images = []

        if image_ids:

            images_response = (
                supabase
                .table(IMAGES_TABLE)
                .select("*")
                .in_(
                    "id",
                    image_ids
                )
                .order("id")
                .execute()
            )

            images = (
                images_response.data
                or []
            )


        # ----------------------------------------------------
        # ADD IMAGE URL
        # ----------------------------------------------------

        image_results = []

        for image in images:

            storage_path = image.get(
                "storage_path"
            )

            image_copy = dict(image)

            image_copy["image_url"] = (
                create_image_url(
                    storage_path
                )
            )

            image_results.append(
                image_copy
            )


        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        return {

            "success": True,

            "product":
                product,

            "specifications":
                specifications,

            "images":
                image_results,

            "summary": {

                "specifications_count":
                    len(specifications),

                "image_mappings_count":
                    len(mappings),

                "images_count":
                    len(image_results)
            }
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

    print("=" * 80)
    print("OCR PRODUCT RETRIEVAL API")
    print("=" * 80)

    print()
    print("API:")
    print("http://127.0.0.1:8000")

    print()
    print("Swagger:")
    print("http://127.0.0.1:8000/docs")

    print()
    print("All products:")
    print("http://127.0.0.1:8000/products")

    print()
    print("Product:")
    print(
        "http://127.0.0.1:8000/products/{product_code}"
    )

    print("=" * 80)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )