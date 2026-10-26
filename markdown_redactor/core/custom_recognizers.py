"""Custom pattern recognizers to enhance Presidio detection."""

from presidio_analyzer import PatternRecognizer, Pattern


def get_street_address_recognizer() -> PatternRecognizer:
    """Recognizer for standard US and international street addresses.
    
    Catches street addresses like:
    - 123 Main Street
    - 456 Elm Ave.
    - 7890 Park Boulevard
    """
    return PatternRecognizer(
        supported_entity="STREET_ADDRESS",
        patterns=[
            Pattern(
                name="street_address_pattern",
                regex=r"\b\d{1,5}\s+(?:[A-Za-z0-9\.\-]+\s){1,4}(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|way|circle|cir|terrace|ter)\b\.?",
                score=0.6,
            )
        ],
    )
