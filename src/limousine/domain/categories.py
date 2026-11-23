"""Canonical attachment types and explicit aliases, independent of filenames."""

import re
import unicodedata
from difflib import SequenceMatcher

from limousine.domain.vehicles import DomainError

SEED_CATEGORIES = (
    (
        "vehicle_license",
        "رخصة السيارة",
        ("رخصة المركبة", "الرخصة", "Vehicle license", "Car license", "Vehicle licence"),
    ),
    ("direction_card", "كرت الاتجاه", ("كرت الإتجاه", "Direction card")),
    ("customs_declaration", "البيان الجمركي", ("بيان جمركي", "Customs declaration")),
    ("other", "أخرى", ("Other",)),
)


class SimilarCategory(DomainError):
    """The caller must review suggestions before declaring a distinct type."""


class CategoryConflict(DomainError):
    pass


class CategoryInUse(DomainError):
    """A named category already has an active gallery attachment on this vehicle."""


def require_free_category(is_other, occupied):
    if not is_other and occupied:
        raise CategoryInUse(
            "This vehicle already has an attachment in this category, in Photos or Files."
        )


def category_name(value):
    if not isinstance(value, str):
        raise DomainError("Enter a category name.")
    value = " ".join(unicodedata.normalize("NFKC", value).split())
    if (
        not value
        or len(value) > 100
        or any(unicodedata.category(c).startswith("C") for c in value)
    ):
        raise DomainError("Use a category name of 1 to 100 characters.")
    return value


def category_key(value):
    value = category_name(value).casefold()
    value = value.translate(
        str.maketrans(
            {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ی": "ي", "ک": "ك", "ـ": ""}
        )
    )
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    value = " ".join(value.split())
    if not value or len(value) > 160:
        raise DomainError(
            "Enter a category name containing letters or digits, within 160 normalized characters."
        )
    return value


def similar_categories(categories, name):
    key = category_key(name)
    matches = []
    for category in categories:
        if category["is_other"]:
            continue
        aliases = [category["name"], *category["aliases"]]
        score = max(SequenceMatcher(None, key, category_key(alias)).ratio() for alias in aliases)
        if score >= 0.72 or any(
            key in category_key(alias) or category_key(alias) in key for alias in aliases
        ):
            matches.append((score, category))
    return [
        category for _, category in sorted(matches, key=lambda item: (-item[0], item[1]["id"]))[:5]
    ]
