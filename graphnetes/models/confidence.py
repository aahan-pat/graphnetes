from enum import Enum


class Confidence(str, Enum):
    # Directly derived from resource spec
    EXTRACTED = "EXTRACTED"
    # Derived by resolving selectors or owner chains
    INFERRED = "INFERRED"
    # Uncertain; multiple possible interpretations
    AMBIGUOUS = "AMBIGUOUS"
