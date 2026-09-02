import re
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse

from supabase_client import supabase
from hybrid_search import hybrid_search
from ai_answer import answer_product_query


# ============================================================
# API CONFIGURATION
# ============================================================

API_VERSION = "5.0.0"

app = FastAPI(
    title="OCR Product Retrieval API",
    description=(
        "OCR-based product retrieval API with hybrid search "
        "and Groq-powered AI product answers."
    ),
    version=API_VERSION,
)


# ============================================================
# SUPABASE TABLES
# ============================================================

PRODUCTS_TABLE = "products"
PRODUCT_SPECS_TABLE = "product_specs"
PRODUCT_IMAGE_MAP_TABLE = "product_image_map"
PRODUCT_IMAGES_TABLE = "product_images"
OCR_RESULTS_TABLE = "ocr_results"


# ============================================================
# SEARCH CONFIGURATION
# ============================================================

FIELD_WEIGHTS = {
    "wattage": 35,
    "feature": 25,
    "colour_temperature": 20,
    "colour": 10,
    "beam_angle": 5,
    "ip_rating": 3,
    "material": 2,
}


STOP_WORDS: Set[str] = {
    "a",
    "an",
    "the",
    "for",
    "with",
    "and",
    "or",
    "of",
    "in",
    "on",
    "to",
    "from",
    "light",
    "lights",
    "lamp",
    "lamps",
    "spotlight",
    "spotlights",
    "led",
    "product",
    "products",
}


# ============================================================
# FEATURE ALIASES
# ============================================================

FEATURE_ALIASES = {
    "tiltable": [
        "tiltable",
        "tilt",
        "tilting",
        "adjustable",
        "adjustable spotlight",
    ],
    "adjustable": [
        "adjustable",
        "adjust",
        "tiltable",
        "tilt",
        "tilting",
    ],
    "trimless": [
        "trimless",
        "trim less",
        "trim-less",
    ],
    "surface": [
        "surface",
        "surface mounted",
        "surface mount",
    ],
    "recessed": [
        "recessed",
        "recess",
    ],
    "fixed": [
        "fixed",
        "non adjustable",
        "non-adjustable",
    ],
}


# ============================================================
# COLOUR ALIASES
# ============================================================

COLOUR_ALIASES = {
    "black": [
        "black",
    ],
    "white": [
        "white",
    ],
    "gold": [
        "gold",
        "golden",
    ],
    "silver": [
        "silver",
    ],
    "grey": [
        "grey",
        "gray",
    ],
}


# ============================================================
# COLOUR TEMPERATURE ALIASES
# ============================================================

TEMPERATURE_ALIASES = {
    "2700": [
        "2700k",
        "2700 k",
        "2700",
    ],
    "3000": [
        "3000k",
        "3000 k",
        "3000",
        "warm white",
        "warm lighting",
        "warm light",
    ],
    "4000": [
        "4000k",
        "4000 k",
        "4000",
        "cool white",
        "cool lighting",
        "cool light",
        "neutral white",
        "neutral lighting",
        "neutral light",
    ],
    "6000": [
        "6000k",
        "6000 k",
        "6000",
        "daylight white",
        "daylight",
        "day light",
    ],
}


# ============================================================
# MATERIALS
# ============================================================

MATERIALS = [
    "aluminium",
    "aluminum",
    "steel",
    "plastic",
    "brass",
    "iron",
    "copper",
]


# ============================================================
# PUBLIC RESPONSE HELPERS
# ============================================================

def remove_embedding(
    product: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Remove the internal embedding vector from public API
    responses.

    The embedding remains stored in Supabase and is still
    available internally for semantic/hybrid search.
    """

    if product is None:
        return None

    cleaned = dict(product)

    cleaned.pop("embedding", None)

    return cleaned


def remove_embeddings_from_list(
    products: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Remove embedding from a list of product records.
    """

    return [
        remove_embedding(product)
        for product in products
    ]


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_lower(value: Any) -> str:

    if value is None:
        return ""

    return str(value).strip().lower()


def normalize_text(value: Any) -> str:

    text = safe_lower(value)

    text = text.replace("°", " degree ")
    text = text.replace("-", " ")
    text = text.replace("/", " ")

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def contains_text(
    value: Any,
    term: str,
) -> bool:

    return term.lower() in safe_lower(value)


def extract_numbers(
    text: str,
) -> List[float]:

    if not text:
        return []

    values = re.findall(
        r"\d+(?:\.\d+)?",
        text,
    )

    result = []

    for value in values:

        try:
            result.append(float(value))

        except ValueError:
            pass

    return result


def clean_code(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(value).strip().upper()


# ============================================================
# SEARCH QUERY PARSER
# ============================================================

def parse_search_query(
    query: str,
) -> Dict[str, List[str]]:

    text = normalize_text(query)

    result = {
        "wattage": [],
        "colour_temperature": [],
        "colour": [],
        "beam_angle": [],
        "ip_rating": [],
        "feature": [],
        "material": [],
    }

    if not text:
        return result

    # --------------------------------------------------------
    # WATTAGE
    # --------------------------------------------------------

    wattage_matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:w|watt|watts)\b",
        text,
    )

    for value in wattage_matches:

        if value not in result["wattage"]:
            result["wattage"].append(value)

    # --------------------------------------------------------
    # BEAM ANGLE
    # --------------------------------------------------------

    beam_matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:degree|degrees|deg)\b",
        text,
    )

    for value in beam_matches:

        if value not in result["beam_angle"]:
            result["beam_angle"].append(value)

    # Also support "15°"

    degree_symbol_matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*°",
        query.lower(),
    )

    for value in degree_symbol_matches:

        if value not in result["beam_angle"]:
            result["beam_angle"].append(value)

    # --------------------------------------------------------
    # IP RATING
    # --------------------------------------------------------

    ip_matches = re.findall(
        r"\b(ip\d{2})\b",
        text,
    )

    for value in ip_matches:

        value = value.upper()

        if value not in result["ip_rating"]:
            result["ip_rating"].append(value)

    # --------------------------------------------------------
    # COLOUR TEMPERATURE
    # --------------------------------------------------------

    temperature_found_spans = []

    for temperature, aliases in TEMPERATURE_ALIASES.items():

        for alias in sorted(
            aliases,
            key=len,
            reverse=True,
        ):

            pattern = re.escape(alias)

            match = re.search(
                rf"\b{pattern}\b",
                text,
            )

            if match:

                if temperature not in result[
                    "colour_temperature"
                ]:
                    result[
                        "colour_temperature"
                    ].append(temperature)

                temperature_found_spans.append(
                    match.span()
                )

                break

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    for feature, aliases in FEATURE_ALIASES.items():

        for alias in sorted(
            aliases,
            key=len,
            reverse=True,
        ):

            if re.search(
                rf"\b{re.escape(alias)}\b",
                text,
            ):

                if feature not in result["feature"]:
                    result["feature"].append(feature)

                break

    # --------------------------------------------------------
    # COLOURS
    # --------------------------------------------------------

    for colour, aliases in COLOUR_ALIASES.items():

        found = False

        for alias in sorted(
            aliases,
            key=len,
            reverse=True,
        ):

            if colour == "white":

                if re.search(
                    rf"\b{re.escape(alias)}\b",
                    text,
                ):

                    phrase_found = any(
                        start <= text.find(alias) <= end
                        for start, end
                        in temperature_found_spans
                    )

                    if phrase_found:
                        continue

            if re.search(
                rf"\b{re.escape(alias)}\b",
                text,
            ):

                found = True
                break

        if found:
            result["colour"].append(colour)

    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    for material in MATERIALS:

        if re.search(
            rf"\b{re.escape(material)}\b",
            text,
        ):

            result["material"].append(
                material
            )

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    for field in result:

        result[field] = list(
            dict.fromkeys(
                result[field]
            )
        )

    return result


# ============================================================
# SUPABASE FETCH HELPERS
# ============================================================

def fetch_all_products() -> List[Dict[str, Any]]:

    response = (
        supabase
        .table(PRODUCTS_TABLE)
        .select("*")
        .order("id")
        .execute()
    )

    return response.data or []


def fetch_product_by_id(
    product_id: int,
) -> Optional[Dict[str, Any]]:

    response = (
        supabase
        .table(PRODUCTS_TABLE)
        .select("*")
        .eq("id", product_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def fetch_product_by_code(
    product_code: str,
) -> Optional[Dict[str, Any]]:

    code = product_code.strip()

    response = (
        supabase
        .table(PRODUCTS_TABLE)
        .select("*")
        .eq("product_code", code)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def fetch_all_specs() -> List[Dict[str, Any]]:

    response = (
        supabase
        .table(PRODUCT_SPECS_TABLE)
        .select("*")
        .execute()
    )

    return response.data or []


def fetch_specification(
    product_id: int,
) -> Optional[Dict[str, Any]]:

    response = (
        supabase
        .table(PRODUCT_SPECS_TABLE)
        .select("*")
        .eq("product_id", product_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def fetch_image_mappings(
    product_id: int,
) -> List[Dict[str, Any]]:

    response = (
        supabase
        .table(PRODUCT_IMAGE_MAP_TABLE)
        .select("*")
        .eq("product_id", product_id)
        .execute()
    )

    return response.data or []


def fetch_images_for_product(
    product_id: int,
) -> List[Dict[str, Any]]:

    mappings = fetch_image_mappings(
        product_id
    )

    if not mappings:
        return []

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

    response = (
        supabase
        .table(PRODUCT_IMAGES_TABLE)
        .select("*")
        .in_("id", image_ids)
        .execute()
    )

    images = response.data or []

    image_map = {
        image["id"]: image
        for image in images
        if image.get("id") is not None
    }

    result = []

    for mapping in mappings:

        image_id = mapping.get(
            "image_id"
        )

        image = image_map.get(
            image_id
        )

        if image:
            result.append(
                image
            )

    return result


def fetch_ocr_page(
    product_id: int,
    page_number: Optional[int] = None,
) -> Optional[Dict[str, Any]]:

    product = fetch_product_by_id(
        product_id
    )

    if not product:
        return None

    document_id = product.get(
        "document_id"
    )

    if document_id is None:
        return None

    query = (
        supabase
        .table(OCR_RESULTS_TABLE)
        .select("*")
        .eq(
            "document_id",
            document_id,
        )
    )

    if page_number is not None:

        query = query.eq(
            "page_number",
            page_number,
        )

    else:

        product_page = product.get(
            "page_number"
        )

        if product_page is not None:

            query = query.eq(
                "page_number",
                product_page,
            )

    response = (
        query
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def fetch_image_by_id(
    image_id: int,
) -> Optional[Dict[str, Any]]:

    response = (
        supabase
        .table(PRODUCT_IMAGES_TABLE)
        .select("*")
        .eq("id", image_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


# ============================================================
# SPECIFICATION MAP
# ============================================================

def build_specification_map(
    specifications: List[Dict[str, Any]],
) -> Dict[int, Dict[str, Any]]:

    result = {}

    for specification in specifications:

        product_id = specification.get(
            "product_id"
        )

        if product_id is not None:

            result[
                product_id
            ] = specification

    return result


# ============================================================
# VALUE MATCHING
# ============================================================

def value_contains(
    actual_value: Any,
    requested_value: str,
) -> bool:

    actual = normalize_text(
        actual_value
    )

    requested = normalize_text(
        requested_value
    )

    if not actual or not requested:
        return False

    return requested in actual


def match_wattage(
    specification: Dict[str, Any],
    requested_values: List[str],
) -> bool:

    if not requested_values:
        return False

    actual = specification.get(
        "wattage"
    )

    actual_numbers = extract_numbers(
        str(actual)
    )

    for requested in requested_values:

        try:
            requested_number = float(
                requested
            )

        except ValueError:
            continue

        if requested_number in actual_numbers:
            return True

    return False


def match_temperature(
    specification: Dict[str, Any],
    requested_values: List[str],
) -> bool:

    if not requested_values:
        return False

    actual = safe_lower(
        specification.get(
            "color_temperature"
        )
        or specification.get(
            "colour_temperature"
        )
    )

    actual_numbers = extract_numbers(
        actual
    )

    for requested in requested_values:

        try:
            requested_number = float(
                requested
            )

        except ValueError:
            continue

        if requested_number in actual_numbers:
            return True

    return False


def match_beam_angle(
    specification: Dict[str, Any],
    requested_values: List[str],
) -> bool:

    if not requested_values:
        return False

    actual = safe_lower(
        specification.get(
            "beam_angle"
        )
    )

    actual_numbers = extract_numbers(
        actual
    )

    for requested in requested_values:

        try:
            requested_number = float(
                requested
            )

        except ValueError:
            continue

        if requested_number in actual_numbers:
            return True

    return False


def match_ip_rating(
    specification: Dict[str, Any],
    requested_values: List[str],
) -> bool:

    if not requested_values:
        return False

    actual = safe_lower(
        specification.get(
            "ip_rating"
        )
    )

    for requested in requested_values:

        if requested.lower() in actual:
            return True

    return False


def match_colour(
    specification: Dict[str, Any],
    requested_values: List[str],
) -> bool:

    if not requested_values:
        return False

    actual = safe_lower(
        specification.get(
            "outer_frame"
        )
    )

    for requested in requested_values:

        if requested.lower() in actual:
            return True

    return False


def match_material(
    specification: Dict[str, Any],
    requested_values: List[str],
) -> bool:

    if not requested_values:
        return False

    actual = safe_lower(
        specification.get(
            "housing"
        )
        or specification.get(
            "material"
        )
    )

    for requested in requested_values:

        if requested.lower() in actual:
            return True

    return False


def match_feature(
    product: Dict[str, Any],
    specification: Dict[str, Any],
    requested_features: List[str],
) -> List[str]:

    if not requested_features:
        return []

    product_code = safe_lower(
        product.get(
            "product_code"
        )
    )

    product_name = safe_lower(
        product.get(
            "product_name"
        )
    )

    combined = (
        f"{product_code} "
        f"{product_name}"
    )

    for key, value in specification.items():

        if key in {
            "id",
            "product_id",
            "created_at",
        }:
            continue

        combined += (
            f" {safe_lower(value)}"
        )

    matched = []

    for feature in requested_features:

        aliases = FEATURE_ALIASES.get(
            feature,
            [feature],
        )

        for alias in aliases:

            if alias.lower() in combined:

                matched.append(
                    feature
                )

                break

    return list(
        dict.fromkeys(
            matched
        )
    )


# ============================================================
# STRICT MATCH FILTER
# ============================================================

def passes_hard_filters(
    product: Dict[str, Any],
    specification: Dict[str, Any],
    parsed_query: Dict[str, List[str]],
) -> bool:

    if parsed_query["wattage"]:

        if not match_wattage(
            specification,
            parsed_query["wattage"],
        ):
            return False

    if parsed_query["colour_temperature"]:

        if not match_temperature(
            specification,
            parsed_query[
                "colour_temperature"
            ],
        ):
            return False

    if parsed_query["colour"]:

        if not match_colour(
            specification,
            parsed_query["colour"],
        ):
            return False

    if parsed_query["beam_angle"]:

        if not match_beam_angle(
            specification,
            parsed_query[
                "beam_angle"
            ],
        ):
            return False

    if parsed_query["ip_rating"]:

        if not match_ip_rating(
            specification,
            parsed_query[
                "ip_rating"
            ],
        ):
            return False

    if parsed_query["material"]:

        if not match_material(
            specification,
            parsed_query[
                "material"
            ],
        ):
            return False

    if parsed_query["feature"]:

        matched_features = match_feature(
            product,
            specification,
            parsed_query[
                "feature"
            ],
        )

        if not matched_features:
            return False

    return True


# ============================================================
# STRUCTURED SCORE
# ============================================================

def calculate_structured_rank(
    product: Dict[str, Any],
    specification: Dict[str, Any],
    parsed_query: Dict[str, List[str]],
) -> Dict[str, Any]:

    matched_fields = []
    matched_terms = []

    total_weight = 0
    matched_weight = 0

    # --------------------------------------------------------
    # WATTAGE
    # --------------------------------------------------------

    if parsed_query["wattage"]:

        weight = FIELD_WEIGHTS[
            "wattage"
        ]

        total_weight += weight

        if match_wattage(
            specification,
            parsed_query["wattage"],
        ):

            matched_weight += weight

            matched_fields.append(
                "wattage"
            )

            matched_terms.extend(
                parsed_query[
                    "wattage"
                ]
            )

    # --------------------------------------------------------
    # FEATURE
    # --------------------------------------------------------

    if parsed_query["feature"]:

        weight = FIELD_WEIGHTS[
            "feature"
        ]

        total_weight += weight

        features = match_feature(
            product,
            specification,
            parsed_query[
                "feature"
            ],
        )

        if features:

            matched_weight += weight

            matched_fields.append(
                "feature"
            )

            matched_terms.extend(
                features
            )

    # --------------------------------------------------------
    # COLOUR TEMPERATURE
    # --------------------------------------------------------

    if parsed_query[
        "colour_temperature"
    ]:

        weight = FIELD_WEIGHTS[
            "colour_temperature"
        ]

        total_weight += weight

        if match_temperature(
            specification,
            parsed_query[
                "colour_temperature"
            ],
        ):

            matched_weight += weight

            matched_fields.append(
                "colour_temperature"
            )

            matched_terms.extend(
                parsed_query[
                    "colour_temperature"
                ]
            )

    # --------------------------------------------------------
    # COLOUR
    # --------------------------------------------------------

    if parsed_query["colour"]:

        weight = FIELD_WEIGHTS[
            "colour"
        ]

        total_weight += weight

        if match_colour(
            specification,
            parsed_query["colour"],
        ):

            matched_weight += weight

            matched_fields.append(
                "colour"
            )

            matched_terms.extend(
                parsed_query[
                    "colour"
                ]
            )

    # --------------------------------------------------------
    # BEAM ANGLE
    # --------------------------------------------------------

    if parsed_query["beam_angle"]:

        weight = FIELD_WEIGHTS[
            "beam_angle"
        ]

        total_weight += weight

        if match_beam_angle(
            specification,
            parsed_query[
                "beam_angle"
            ],
        ):

            matched_weight += weight

            matched_fields.append(
                "beam_angle"
            )

            matched_terms.extend(
                parsed_query[
                    "beam_angle"
                ]
            )

    # --------------------------------------------------------
    # IP RATING
    # --------------------------------------------------------

    if parsed_query["ip_rating"]:

        weight = FIELD_WEIGHTS[
            "ip_rating"
        ]

        total_weight += weight

        if match_ip_rating(
            specification,
            parsed_query[
                "ip_rating"
            ],
        ):

            matched_weight += weight

            matched_fields.append(
                "ip_rating"
            )

            matched_terms.extend(
                parsed_query[
                    "ip_rating"
                ]
            )

    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    if parsed_query["material"]:

        weight = FIELD_WEIGHTS[
            "material"
        ]

        total_weight += weight

        if match_material(
            specification,
            parsed_query[
                "material"
            ],
        ):

            matched_weight += weight

            matched_fields.append(
                "material"
            )

            matched_terms.extend(
                parsed_query[
                    "material"
                ]
            )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    if total_weight == 0:

        percentage = 0.0

    else:

        percentage = (
            matched_weight
            / total_weight
        ) * 100

    return {
        "score": round(
            percentage,
            2,
        ),
        "matched_fields": matched_fields,
        "matched_terms": matched_terms,
    }


# ============================================================
# PRODUCT RESULT BUILDER
# ============================================================

def build_product_result(
    product: Dict[str, Any],
    specification: Optional[
        Dict[str, Any]
    ] = None,
    include_images: bool = False,
) -> Dict[str, Any]:

    product_id = product.get(
        "id"
    )

    result = {
        "product": remove_embedding(product),
        "specifications": specification,
    }

    if include_images:

        result["images"] = (
            fetch_images_for_product(
                product_id
            )
        )

    return result


# ============================================================
# HYBRID SEARCH RESULT NORMALIZER
# ============================================================

def get_hybrid_value(
    result: Dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:

    for key in keys:

        if key in result:
            return result[key]

    return default


def enrich_hybrid_result(
    hybrid_result: Dict[str, Any],
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Get product ID
    # --------------------------------------------------------

    product_id = get_hybrid_value(
        hybrid_result,
        "id",
        "product_id",
    )

    if product_id is None:

        product = hybrid_result.get(
            "product"
        )

        if isinstance(
            product,
            dict,
        ):

            product_id = product.get(
                "id"
            )

    if product_id is None:

        return {
            "product": remove_embedding(
                hybrid_result.get("product")
            ),
            "specifications": hybrid_result.get(
                "specifications"
            ),
            "matched_fields": hybrid_result.get(
                "matched_fields",
                [],
            ),
            "matched_terms": hybrid_result.get(
                "matched_terms",
                [],
            ),
            "match_percentage": hybrid_result.get(
                "structured_score",
                0,
            ),
            "score": hybrid_result.get(
                "hybrid_score",
                hybrid_result.get(
                    "score",
                    0,
                ),
            ),
            "semantic_score": hybrid_result.get(
                "semantic_score",
                0,
            ),
            "structured_score": hybrid_result.get(
                "structured_score",
                0,
            ),
            "hard_mismatches": hybrid_result.get(
                "hard_mismatches",
                [],
            ),
        }

    # --------------------------------------------------------
    # Product
    # --------------------------------------------------------

    product = hybrid_result.get(
        "product"
    )

    if not isinstance(
        product,
        dict,
    ):

        product = fetch_product_by_id(
            int(product_id)
        )

    # --------------------------------------------------------
    # Specification
    # --------------------------------------------------------

    specification = (
        hybrid_result.get(
            "specifications"
        )
    )

    if not isinstance(
        specification,
        dict,
    ):

        specification = fetch_specification(
            int(product_id)
        )

    # --------------------------------------------------------
    # Scores
    # --------------------------------------------------------

    semantic_score = get_hybrid_value(
        hybrid_result,
        "semantic_score",
        "semantic_similarity",
        default=0.0,
    )

    structured_score = get_hybrid_value(
        hybrid_result,
        "structured_score",
        "structured",
        default=0.0,
    )

    hybrid_score = get_hybrid_value(
        hybrid_result,
        "hybrid_score",
        "score",
        default=0.0,
    )

    matched_fields = hybrid_result.get(
        "matched_fields",
        [],
    )

    matched_terms = hybrid_result.get(
        "matched_terms",
        [],
    )

    hard_mismatches = hybrid_result.get(
        "hard_mismatches",
        [],
    )

    return {
        "product": remove_embedding(product),
        "specifications": specification,
        "matched_fields": matched_fields,
        "matched_terms": matched_terms,
        "match_percentage": structured_score,
        "score": hybrid_score,
        "semantic_score": semantic_score,
        "structured_score": structured_score,
        "hard_mismatches": hard_mismatches,
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "api_version": API_VERSION,
        "search_engine": "Hybrid Search V3",
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_dimensions": 384,
        "ai_answer_engine": "Groq",
        "ai_model": "openai/gpt-oss-120b",
    }


# ============================================================
# GET ALL PRODUCTS
# ============================================================

@app.get("/products")
def get_products(
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
):

    products = (
        supabase
        .table(PRODUCTS_TABLE)
        .select("*")
        .order("id")
        .limit(limit)
        .execute()
    )

    cleaned_products = (
        remove_embeddings_from_list(
            products.data or []
        )
    )

    return {
        "count": len(
            cleaned_products
        ),
        "products": cleaned_products,
    }


# ============================================================
# HYBRID PRODUCT SEARCH
# ============================================================

@app.get("/products/search")
def search_products(
    q: str = Query(
        ...,
        min_length=1,
        description="Product search query",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
):

    try:

        results = hybrid_search(
            q,
            limit=limit,
        )

        cleaned_results = []

        for result in results:

            result = dict(result)

            result.pop(
                "embedding",
                None,
            )

            cleaned_results.append(
                result
            )

        return {
            "query": q,
            "search_type": "hybrid",
            "search_version": "V3",
            "count": len(
                cleaned_results
            ),
            "results": cleaned_results,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Product search failed: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# AI PRODUCT QUESTION ANSWER
# ============================================================

@app.get("/products/ask")
def ask_product(
    q: str = Query(
        ...,
        min_length=1,
        description=(
            "Natural-language product "
            "question"
        ),
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=10,
    ),
):

    try:

        result = answer_product_query(
            query=q,
            limit=limit,
        )

        return {
            "query": result[
                "query"
            ],
            "answer": result[
                "answer"
            ],
            "results": result[
                "results"
            ],
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"AI product query failed: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# STRICT STRUCTURED SEARCH
# ============================================================

@app.get("/products/search/strict")
def strict_search_products(
    q: str = Query(
        ...,
        min_length=1,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
):

    parsed_query = parse_search_query(
        q
    )

    products = fetch_all_products()

    specifications = fetch_all_specs()

    specification_map = (
        build_specification_map(
            specifications
        )
    )

    results = []

    for product in products:

        product_id = product.get(
            "id"
        )

        specification = (
            specification_map.get(
                product_id,
                {},
            )
        )

        if not passes_hard_filters(
            product,
            specification,
            parsed_query,
        ):

            continue

        ranking = (
            calculate_structured_rank(
                product,
                specification,
                parsed_query,
            )
        )

        result = {
            "product": remove_embedding(
                product
            ),
            "specifications": specification,
            "matched_fields": ranking[
                "matched_fields"
            ],
            "matched_terms": ranking[
                "matched_terms"
            ],
            "match_percentage": ranking[
                "score"
            ],
            "score": ranking[
                "score"
            ],
        }

        results.append(
            result
        )

    results.sort(
        key=lambda item: item[
            "score"
        ],
        reverse=True,
    )

    limited_results = results[:limit]

    return {
        "query": q,
        "search_type": "strict_structured",
        "count": len(
            limited_results
        ),
        "results": limited_results,
    }


# ============================================================
# PRODUCT LOOKUP BY EXACT CODE
# ============================================================

@app.get(
    "/products/code/{product_code}"
)
def get_product_by_code(
    product_code: str,
):

    product = fetch_product_by_code(
        product_code
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Product code "
                f"'{product_code}' not found"
            ),
        )

    return remove_embedding(
        product
    )


# ============================================================
# PRODUCT COMPLETE DETAILS
# ============================================================

@app.get(
    "/products/code/{product_code}/complete"
)
def get_complete_product_by_code(
    product_code: str,
):

    product = fetch_product_by_code(
        product_code
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Product code "
                f"'{product_code}' not found"
            ),
        )

    product_id = product.get(
        "id"
    )

    specification = (
        fetch_specification(
            product_id
        )
    )

    images = (
        fetch_images_for_product(
            product_id
        )
    )

    return {
        "product": remove_embedding(
            product
        ),
        "specifications": specification,
        "images": images,
    }


# ============================================================
# PRODUCT SPECIFICATIONS
# ============================================================

@app.get(
    "/products/{product_id}/specifications"
)
def get_product_specifications(
    product_id: int,
):

    product = fetch_product_by_id(
        product_id
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Product {product_id} "
                f"not found"
            ),
        )

    specification = (
        fetch_specification(
            product_id
        )
    )

    return {
        "product_id": product_id,
        "product_code": product.get(
            "product_code"
        ),
        "product_name": product.get(
            "product_name"
        ),
        "specifications": specification,
    }


# ============================================================
# PRODUCT IMAGES
# ============================================================

@app.get(
    "/products/{product_id}/images"
)
def get_product_images(
    product_id: int,
):

    product = fetch_product_by_id(
        product_id
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Product {product_id} "
                f"not found"
            ),
        )

    images = (
        fetch_images_for_product(
            product_id
        )
    )

    return {
        "product_id": product_id,
        "product_code": product.get(
            "product_code"
        ),
        "count": len(images),
        "images": images,
    }


# ============================================================
# PRODUCT OCR PAGE
# ============================================================

@app.get(
    "/products/{product_id}/ocr/page"
)
def get_product_ocr_page(
    product_id: int,
):

    product = fetch_product_by_id(
        product_id
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Product {product_id} "
                f"not found"
            ),
        )

    ocr_page = fetch_ocr_page(
        product_id
    )

    if not ocr_page:

        raise HTTPException(
            status_code=404,
            detail=(
                f"OCR page not found "
                f"for product {product_id}"
            ),
        )

    return {
        "product": remove_embedding(
            product
        ),
        "ocr": ocr_page,
    }


# ============================================================
# IMAGE BY ID
# ============================================================

@app.get(
    "/images/{image_id}"
)
def get_image(
    image_id: int,
):

    image = fetch_image_by_id(
        image_id
    )

    if not image:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Image {image_id} "
                f"not found"
            ),
        )

    return image


# ============================================================
# IMAGE VIEW
# ============================================================

@app.get(
    "/images/{image_id}/view"
)
def view_image(
    image_id: int,
):

    image = fetch_image_by_id(
        image_id
    )

    if not image:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Image {image_id} "
                f"not found"
            ),
        )

    storage_path = image.get(
        "storage_path"
    )

    if not storage_path:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No storage path found "
                f"for image {image_id}"
            ),
        )

    try:

        public_url = (
            supabase
            .storage
            .from_("product-image")
            .get_public_url(
                storage_path
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not generate "
                f"image URL: {str(exc)}"
            ),
        )

    return RedirectResponse(
        url=public_url
    )


# ============================================================
# PRODUCT BY ID
# ============================================================

@app.get(
    "/products/{product_id}"
)
def get_product(
    product_id: int,
):

    product = fetch_product_by_id(
        product_id
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Product {product_id} "
                f"not found"
            ),
        )

    return remove_embedding(
        product
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": (
            "OCR Product Retrieval API"
        ),
        "version": API_VERSION,
        "search": "Hybrid Search V3",
        "ai_answer": "Groq",
        "ai_model": "openai/gpt-oss-120b",
        "docs": "/docs",
        "health": "/health",
    }