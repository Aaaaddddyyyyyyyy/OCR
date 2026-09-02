import re
from typing import Dict, List, Any

from sentence_transformers import SentenceTransformer
from supabase_client import supabase


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "all-MiniLM-L6-v2"

SEMANTIC_THRESHOLD = 0.30
SEMANTIC_COUNT = 20

FIELD_WEIGHTS = {
    "wattage": 35,
    "feature": 25,
    "colour_temperature": 20,
    "colour": 10,
    "beam_angle": 5,
    "ip_rating": 3,
    "material": 2,
}

# Explicit specification queries should rely mostly on
# structured matching.
ATTRIBUTE_STRUCTURED_WEIGHT = 0.85
ATTRIBUTE_SEMANTIC_WEIGHT = 0.15

# Natural-language queries benefit more from semantic search.
NATURAL_STRUCTURED_WEIGHT = 0.35
NATURAL_SEMANTIC_WEIGHT = 0.65

# Penalty applied to the final score for every hard mismatch.
MISMATCH_PENALTY = 0.20


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded.")


# ============================================================
# DATABASE
# ============================================================

def get_products() -> List[Dict[str, Any]]:
    """
    Fetch all products.
    """

    response = (
        supabase
        .table("products")
        .select("id, product_code, product_name, page_number")
        .execute()
    )

    return response.data or []


def get_product_specs(product_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    Fetch specifications for ALL products in one query.

    Returns:
        {
            product_id: spec_dict
        }
    """

    if not product_ids:
        return {}

    response = (
        supabase
        .table("product_specs")
        .select("*")
        .in_("product_id", product_ids)
        .execute()
    )

    specs = {}

    for row in response.data or []:
        product_id = row.get("product_id")

        if product_id is not None:
            specs[product_id] = row

    return specs


# ============================================================
# SEMANTIC SEARCH
# ============================================================

def semantic_search(query: str) -> Dict[int, float]:
    """
    Perform vector similarity search.

    Returns:
        {
            product_id: similarity
        }
    """

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    ).tolist()

    response = supabase.rpc(
        "match_products",
        {
            "query_embedding": query_embedding,
            "match_threshold": SEMANTIC_THRESHOLD,
            "match_count": SEMANTIC_COUNT,
        }
    ).execute()

    results = response.data or []

    semantic_scores = {}

    for row in results:
        product_id = row.get("id")
        similarity = float(row.get("similarity", 0))

        if product_id is not None:
            semantic_scores[int(product_id)] = similarity

    return semantic_scores


# ============================================================
# QUERY PARSER
# ============================================================

def parse_query(query: str) -> Dict[str, List[str]]:
    """
    Extract structured attributes from the user's query.
    """

    normalized = query.lower().strip()

    parsed = {
        "wattage": [],
        "colour_temperature": [],
        "colour": [],
        "beam_angle": [],
        "ip_rating": [],
        "feature": [],
        "material": [],
    }

    # --------------------------------------------------------
    # WATTAGE
    # --------------------------------------------------------

    watt_values = re.findall(
        r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:w|watt|watts)\b",
        normalized
    )

    for watt in watt_values:
        if watt not in parsed["wattage"]:
            parsed["wattage"].append(watt)

    # --------------------------------------------------------
    # COLOUR TEMPERATURE
    # --------------------------------------------------------

    temperature_values = re.findall(
        r"(?<!\d)(\d{4})\s*k\b",
        normalized
    )

    for temp in temperature_values:

        if temp not in parsed["colour_temperature"]:
            parsed["colour_temperature"].append(temp)

    # Natural language temperature aliases

    temperature_aliases = {
        "warm white": ["3000"],
        "warm lighting": ["3000"],
        "warm light": ["3000"],

        "cool white": ["4000"],
        "cool lighting": ["4000"],
        "cool light": ["4000"],

        "neutral white": ["4000"],
        "neutral lighting": ["4000"],
        "neutral light": ["4000"],

        "daylight white": ["6000"],
        "daylight": ["6000"],
    }

    for phrase, values in temperature_aliases.items():

        if phrase in normalized:

            for value in values:

                if value not in parsed["colour_temperature"]:
                    parsed["colour_temperature"].append(value)

    # --------------------------------------------------------
    # COLOUR
    # --------------------------------------------------------

    colour_aliases = {
        "black": ["black"],
        "white": ["white"],
        "gold": ["gold"],
        "silver": ["silver"],
        "grey": ["grey"],
        "gray": ["grey"],
    }

    # IMPORTANT:
    # "warm white", "cool white", etc. are temperature
    # descriptions, NOT outer-frame colour requests.

    temperature_colour_phrases = [
        "warm white",
        "cool white",
        "neutral white",
        "daylight white",
    ]

    for colour_word, values in colour_aliases.items():

        # Skip "white" when it is part of a temperature phrase.
        if colour_word == "white":

            is_temperature_phrase = any(
                phrase in normalized
                for phrase in temperature_colour_phrases
            )

            if is_temperature_phrase:
                continue

        if re.search(
            rf"\b{re.escape(colour_word)}\b",
            normalized
        ):

            for value in values:

                if value not in parsed["colour"]:
                    parsed["colour"].append(value)

    # --------------------------------------------------------
    # BEAM ANGLE
    # --------------------------------------------------------

    beam_values = re.findall(
        r"(?<!\d)(\d+(?:\.\d+)?)\s*"
        r"(?:degree|degrees|deg|°)",
        normalized
    )

    for beam in beam_values:

        if beam not in parsed["beam_angle"]:
            parsed["beam_angle"].append(beam)

    # --------------------------------------------------------
    # IP RATING
    # --------------------------------------------------------

    ip_values = re.findall(
        r"\bip\s*(\d{2})\b",
        normalized
    )

    for ip in ip_values:

        if ip not in parsed["ip_rating"]:
            parsed["ip_rating"].append(ip)

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    feature_aliases = {

        "tiltable": [
            "tiltable",
            "tilting",
            "tilt"
        ],

        "adjustable": [
            "adjustable"
        ],

        "trimless": [
            "trimless"
        ],

        "surface": [
            "surface",
            "surface mounted",
            "surface-mounted"
        ],

        "recessed": [
            "recessed"
        ],

        "fixed": [
            "fixed"
        ],
    }

    for feature, aliases in feature_aliases.items():

        for alias in aliases:

            if re.search(
                rf"\b{re.escape(alias)}\b",
                normalized
            ):

                if feature not in parsed["feature"]:
                    parsed["feature"].append(feature)

                break

    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    material_aliases = [
        "aluminium",
        "aluminum",
        "steel",
        "plastic",
        "pc",
        "polycarbonate",
        "metal",
        "brass",
    ]

    for material in material_aliases:

        if re.search(
            rf"\b{re.escape(material)}\b",
            normalized
        ):

            normalized_material = material

            if material == "aluminum":
                normalized_material = "aluminium"

            if normalized_material not in parsed["material"]:
                parsed["material"].append(normalized_material)

    return parsed


# ============================================================
# FEATURE MATCHING
# ============================================================

def product_has_feature(
    product: Dict[str, Any],
    spec: Dict[str, Any],
    requested_feature: str
) -> bool:

    product_code = str(
        product.get("product_code") or ""
    ).lower()

    product_name = str(
        product.get("product_name") or ""
    ).lower()

    combined_text = (
        product_code
        + " "
        + product_name
    )

    housing = str(
        spec.get("housing") or ""
    ).lower()

    outer_frame = str(
        spec.get("outer_frame") or ""
    ).lower()

    combined_spec = (
        housing
        + " "
        + outer_frame
    )

    text = combined_text + " " + combined_spec

    # --------------------------------------------------------
    # TILTABLE
    # --------------------------------------------------------

    if requested_feature == "tiltable":

        return any(
            word in text
            for word in [
                "tiltable",
                "tilting",
                "tilt"
            ]
        )

    # --------------------------------------------------------
    # ADJUSTABLE
    # --------------------------------------------------------

    if requested_feature == "adjustable":

        return any(
            word in text
            for word in [
                "adjustable",
                "tiltable",
                "tilting",
                "tilt"
            ]
        )

    # --------------------------------------------------------
    # TRIMLESS
    # --------------------------------------------------------

    if requested_feature == "trimless":

        return "trimless" in text

    # --------------------------------------------------------
    # SURFACE
    # --------------------------------------------------------

    if requested_feature == "surface":

        return any(
            word in text
            for word in [
                "surface",
                "surface mounted",
                "surface-mounted"
            ]
        )

    # --------------------------------------------------------
    # RECESSED
    # --------------------------------------------------------

    if requested_feature == "recessed":

        return "recessed" in text

    # --------------------------------------------------------
    # FIXED
    # --------------------------------------------------------

    if requested_feature == "fixed":

        return "fixed" in text

    return False


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize_text(value: Any) -> str:

    if value is None:
        return ""

    return str(value).lower().strip()


def contains_value(
    field_value: Any,
    requested_values: List[str]
) -> bool:

    text = normalize_text(field_value)

    if not text:
        return False

    for requested in requested_values:

        requested = normalize_text(requested)

        if requested in text:
            return True

    return False


# ============================================================
# STRUCTURED MATCHING
# ============================================================

def calculate_structured_match(
    product: Dict[str, Any],
    spec: Dict[str, Any],
    parsed_query: Dict[str, List[str]]
):

    structured_score = 0.0
    max_score = 0.0

    matched_fields = []
    hard_mismatches = []

    # --------------------------------------------------------
    # WATTAGE
    # --------------------------------------------------------

    if parsed_query["wattage"]:

        weight = FIELD_WEIGHTS["wattage"]

        max_score += weight

        wattage = spec.get("wattage")

        if contains_value(
            wattage,
            parsed_query["wattage"]
        ):

            structured_score += weight
            matched_fields.append("wattage")

        else:

            hard_mismatches.append("wattage")

    # --------------------------------------------------------
    # COLOUR TEMPERATURE
    # --------------------------------------------------------

    if parsed_query["colour_temperature"]:

        weight = FIELD_WEIGHTS["colour_temperature"]

        max_score += weight

        temperature = spec.get(
            "color_temperature"
        )

        if contains_value(
            temperature,
            parsed_query["colour_temperature"]
        ):

            structured_score += weight
            matched_fields.append(
                "colour_temperature"
            )

        else:

            hard_mismatches.append(
                "colour_temperature"
            )

    # --------------------------------------------------------
    # COLOUR
    # --------------------------------------------------------

    if parsed_query["colour"]:

        weight = FIELD_WEIGHTS["colour"]

        max_score += weight

        outer_frame = spec.get(
            "outer_frame"
        )

        if contains_value(
            outer_frame,
            parsed_query["colour"]
        ):

            structured_score += weight
            matched_fields.append("colour")

        else:

            hard_mismatches.append("colour")

    # --------------------------------------------------------
    # BEAM ANGLE
    # --------------------------------------------------------

    if parsed_query["beam_angle"]:

        weight = FIELD_WEIGHTS["beam_angle"]

        max_score += weight

        beam_angle = spec.get(
            "beam_angle"
        )

        if contains_value(
            beam_angle,
            parsed_query["beam_angle"]
        ):

            structured_score += weight
            matched_fields.append(
                "beam_angle"
            )

        else:

            hard_mismatches.append(
                "beam_angle"
            )

    # --------------------------------------------------------
    # IP RATING
    # --------------------------------------------------------

    if parsed_query["ip_rating"]:

        weight = FIELD_WEIGHTS["ip_rating"]

        max_score += weight

        ip_rating = spec.get(
            "ip_rating"
        )

        if contains_value(
            ip_rating,
            parsed_query["ip_rating"]
        ):

            structured_score += weight
            matched_fields.append(
                "ip_rating"
            )

        else:

            hard_mismatches.append(
                "ip_rating"
            )

    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    if parsed_query["material"]:

        weight = FIELD_WEIGHTS["material"]

        max_score += weight

        material_fields = [
            spec.get("housing"),
            spec.get("outer_frame"),
        ]

        material_match = any(
            contains_value(
                field,
                parsed_query["material"]
            )
            for field in material_fields
        )

        if material_match:

            structured_score += weight
            matched_fields.append("material")

        else:

            hard_mismatches.append(
                "material"
            )

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    requested_features = parsed_query["feature"]

    for feature in requested_features:

        weight = FIELD_WEIGHTS["feature"]

        max_score += weight

        if product_has_feature(
            product,
            spec,
            feature
        ):

            structured_score += weight

            matched_fields.append(
                f"feature:{feature}"
            )

        else:

            hard_mismatches.append(
                f"feature:{feature}"
            )

    # --------------------------------------------------------
    # NORMALIZED SCORE
    # --------------------------------------------------------

    if max_score > 0:

        normalized_score = (
            structured_score / max_score
        )

    else:

        normalized_score = 0.0

    return (
        structured_score,
        max_score,
        normalized_score,
        matched_fields,
        hard_mismatches,
    )


# ============================================================
# QUERY TYPE
# ============================================================

def is_attribute_query(
    parsed_query: Dict[str, List[str]]
) -> bool:

    total_attributes = sum(
        len(values)
        for values in parsed_query.values()
    )

    return total_attributes > 0


# ============================================================
# BUILD HYBRID RESULTS
# ============================================================

def hybrid_search(
    query: str,
    limit: int = 10
):

    print()
    print("=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    # --------------------------------------------------------
    # PARSE QUERY
    # --------------------------------------------------------

    parsed_query = parse_query(query)

    print("Parsed query:")
    print(parsed_query)

    # --------------------------------------------------------
    # GET PRODUCTS
    # --------------------------------------------------------

    products = get_products()

    if not products:
        return []

    product_ids = [
        int(product["id"])
        for product in products
        if product.get("id") is not None
    ]

    # --------------------------------------------------------
    # GET ALL SPECS IN ONE REQUEST
    # --------------------------------------------------------

    specs_by_product = get_product_specs(
        product_ids
    )

    # --------------------------------------------------------
    # SEMANTIC SEARCH
    # --------------------------------------------------------

    semantic_scores = semantic_search(query)

    # --------------------------------------------------------
    # QUERY TYPE
    # --------------------------------------------------------

    attribute_query = is_attribute_query(
        parsed_query
    )

    if attribute_query:

        structured_weight = (
            ATTRIBUTE_STRUCTURED_WEIGHT
        )

        semantic_weight = (
            ATTRIBUTE_SEMANTIC_WEIGHT
        )

    else:

        structured_weight = (
            NATURAL_STRUCTURED_WEIGHT
        )

        semantic_weight = (
            NATURAL_SEMANTIC_WEIGHT
        )

    results = []

    # ========================================================
    # SCORE PRODUCTS
    # ========================================================

    for product in products:

        product_id = product.get("id")

        if product_id is None:
            continue

        product_id = int(product_id)

        spec = specs_by_product.get(
            product_id,
            {}
        )

        semantic_score = semantic_scores.get(
            product_id,
            0.0
        )

        (
            structured_score,
            max_score,
            structured_normalized,
            matched_fields,
            hard_mismatches,
        ) = calculate_structured_match(
            product,
            spec,
            parsed_query
        )

        # ----------------------------------------------------
        # BASE HYBRID SCORE
        # ----------------------------------------------------

        hybrid_score = (
            structured_normalized
            * structured_weight
            * 100
        ) + (
            semantic_score
            * semantic_weight
            * 100
        )

        # ----------------------------------------------------
        # HARD MISMATCH PENALTY
        # ----------------------------------------------------

        mismatch_count = len(
            hard_mismatches
        )

        if attribute_query and mismatch_count > 0:

            hybrid_score *= max(
                0,
                1 - (
                    MISMATCH_PENALTY
                    * mismatch_count
                )
            )

        # ----------------------------------------------------
        # KEEP SCORE IN RANGE
        # ----------------------------------------------------

        hybrid_score = max(
            0,
            min(100, hybrid_score)
        )

        results.append({

            "id": product_id,

            "product_code":
                product.get("product_code"),

            "product_name":
                product.get("product_name"),

            "page_number":
                product.get("page_number"),

            "hybrid_score":
                hybrid_score,

            "structured_score":
                structured_normalized * 100,

            "semantic_score":
                semantic_score,

            "matched_fields":
                matched_fields,

            "hard_mismatches":
                hard_mismatches,

            "mismatch_count":
                mismatch_count,
        })

    # ========================================================
    # RANKING
    # ========================================================

    if attribute_query:

        # For explicit specifications:
        #
        # 1. Products with fewer hard mismatches first
        # 2. Then higher structured score
        # 3. Then higher semantic similarity
        #
        # This prevents semantic similarity from pushing an
        # incorrect product above an exact specification match.

        results.sort(
            key=lambda x: (
                x["mismatch_count"],
                -x["structured_score"],
                -x["semantic_score"],
            )
        )

    else:

        # Natural-language search relies primarily on
        # hybrid similarity.

        results.sort(
            key=lambda x: (
                -x["hybrid_score"],
                -x["semantic_score"],
            )
        )

    return results[:limit]


# ============================================================
# DISPLAY RESULTS
# ============================================================

def print_results(
    results: List[Dict[str, Any]]
):

    print()
    print("-" * 80)
    print("RESULTS")
    print("-" * 80)

    if not results:

        print("No results found.")
        return

    for index, result in enumerate(
        results,
        start=1
    ):

        print(
            f"{index}. "
            f"{result['product_code']} "
            f"| hybrid "
            f"{result['hybrid_score']:.2f} "
            f"| structured "
            f"{result['structured_score']:.2f} "
            f"| semantic "
            f"{result['semantic_score']:.4f}"
        )

        matched = (
            ", ".join(result["matched_fields"])
            if result["matched_fields"]
            else "none"
        )

        mismatches = (
            ", ".join(result["hard_mismatches"])
            if result["hard_mismatches"]
            else "none"
        )

        print(f"   matched: {matched}")
        print(f"   mismatch: {mismatches}")