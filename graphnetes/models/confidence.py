from enum import Enum


class Confidence(str, Enum):
    EXTRACTED = "EXTRACTED"   # directly derived from resource spec
    INFERRED = "INFERRED"     # derived by resolving selectors or owner chains
    AMBIGUOUS = "AMBIGUOUS"   # uncertain; multiple possible interpretations
