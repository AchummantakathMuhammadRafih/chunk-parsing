"""Constants and defaults for Markdown PII Redactor."""

from typing import List

DEFAULT_OUTPUT_DIR = "output/redacted"

DEFAULT_ENTITIES: List[str] = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "LOCATION",
    "STREET_ADDRESS",
    "US_SSN",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "IBAN_CODE",
    "US_BANK_NUMBER",
    "US_DRIVER_LICENSE",
    "US_PASSPORT",
]

DEFAULT_SCORE_THRESHOLD: float = 0.4
DEFAULT_MASK_CHAR: str = "*"
DEFAULT_CHARS_TO_MASK: int = 1000  # Masks entire detected token
