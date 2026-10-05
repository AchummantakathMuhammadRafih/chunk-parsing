"""Mask personal information in exported text."""

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

street_recognizer = PatternRecognizer(
    supported_entity="STREET_ADDRESS",
    patterns=[
        Pattern(
            name="street",
            regex=(
                r"\b\d{1,5}\s+(?:\w+\s){1,4}"
                r"(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct)\b\.?"
            ),
            score=0.6,
        )
    ],
)
analyzer.registry.add_recognizer(street_recognizer)

ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "STREET_ADDRESS"]
MASK_OPERATOR = OperatorConfig(
    "mask", {"masking_char": "*", "chars_to_mask": 1000, "from_end": False}
)
OPERATORS = {entity: MASK_OPERATOR for entity in ENTITIES}
OPERATORS["DEFAULT"] = MASK_OPERATOR


def mask_personal_info(text: str) -> str:
    """Mask supported personal information in an English text string."""
    results = analyzer.analyze(
        text=text,
        language="en",
        entities=ENTITIES,
        score_threshold=0.4,
    )
    return anonymizer.anonymize(text=text, analyzer_results=results, operators=OPERATORS).text