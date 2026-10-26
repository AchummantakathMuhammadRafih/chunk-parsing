"""Markdown-aware PII Redactor engine using Microsoft Presidio."""

import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from markdown_redactor.config.settings import RedactionConfig
from markdown_redactor.core.custom_recognizers import get_street_address_recognizer
from markdown_redactor.models.schemas import RedactionFinding, RedactionResult


class MarkdownRedactor:
    """Orchestrates PII detection and star-masking in Markdown documents."""

    def __init__(self, config: Optional[RedactionConfig] = None):
        """Initialize Presidio Analyzer and Anonymizer engines."""
        self.config = config or RedactionConfig()
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        if self.config.custom_recognizers:
            self.analyzer.registry.add_recognizer(get_street_address_recognizer())

        self._operators = self._build_operators()

    def _build_operators(self) -> Dict[str, OperatorConfig]:
        """Construct anonymizer operator configurations with asterisk masking."""
        star_operator = OperatorConfig(
            "mask",
            {
                "masking_char": self.config.mask_char,
                "chars_to_mask": self.config.chars_to_mask,
                "from_end": False,
            },
        )
        operators = {entity: star_operator for entity in self.config.entities}
        operators["DEFAULT"] = star_operator
        return operators

    def redact_text(self, text: str) -> Tuple[str, List[RedactionFinding], Dict[str, int]]:
        """Redact sensitive PII from text, respecting Markdown elements if configured.

        Returns:
            Tuple of (redacted_text, findings_list, entity_counts_dict)
        """
        if not text:
            return "", [], {}

        placeholder_map: Dict[str, str] = {}
        processed_text = text

        # 1. Protect code blocks if enabled
        if self.config.ignore_code_blocks:
            def replace_code_block(match):
                idx = len(placeholder_map)
                key = f"__MD_CODE_BLOCK_{idx}__"
                placeholder_map[key] = match.group(0)
                return key

            processed_text = re.sub(r"```[\s\S]*?```", replace_code_block, processed_text)
            processed_text = re.sub(r"`[^`\n]+`", replace_code_block, processed_text)

        # 2. Protect markdown image targets and links if enabled
        if self.config.ignore_image_urls:
            def replace_image(match):
                idx = len(placeholder_map)
                key = f"__MD_IMG_{idx}__"
                placeholder_map[key] = match.group(0)
                return key

            # Match ![alt](url)
            processed_text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", replace_image, processed_text)

        # 3. Analyze text with Presidio
        analyzer_results = self.analyzer.analyze(
            text=processed_text,
            language=self.config.language,
            entities=self.config.entities,
            score_threshold=self.config.score_threshold,
        )

        findings: List[RedactionFinding] = []
        entity_counts: Dict[str, int] = {}
        for res in analyzer_results:
            findings.append(
                RedactionFinding(
                    entity_type=res.entity_type,
                    start=res.start,
                    end=res.end,
                    score=res.score,
                    original_text=processed_text[res.start:res.end],
                )
            )
            entity_counts[res.entity_type] = entity_counts.get(res.entity_type, 0) + 1

        # 4. Anonymize with asterisk masks
        anonymized = self.anonymizer.anonymize(
            text=processed_text,
            analyzer_results=analyzer_results,
            operators=self._operators,
        )
        redacted_text = anonymized.text

        # 5. Restore protected markdown elements
        for key, original in placeholder_map.items():
            redacted_text = redacted_text.replace(key, original)

        return redacted_text, findings, entity_counts

    def redact_file(self, input_file: Path, output_file: Optional[Path] = None) -> RedactionResult:
        """Redact PII from a Markdown file and write to output_file.

        Args:
            input_file: Path to source Markdown file.
            output_file: Optional path for destination. If None, overwrites or appends .redacted.md.
        """
        start_time = time.time()
        input_path = Path(input_file).resolve()

        if not input_path.exists():
            return RedactionResult(
                input_path=input_path,
                output_path=output_file or input_path,
                findings_count=0,
                success=False,
                error_message=f"File not found: {input_path}",
            )

        if output_file is None:
            output_path = input_path.parent / f"{input_path.stem}.redacted{input_path.suffix}"
        else:
            output_path = Path(output_file).resolve()

        try:
            content = input_path.read_text(encoding="utf-8")
            original_size = len(content.encode("utf-8"))

            redacted_text, findings, entity_counts = self.redact_text(content)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(redacted_text, encoding="utf-8")
            redacted_size = len(redacted_text.encode("utf-8"))

            elapsed = time.time() - start_time
            return RedactionResult(
                input_path=input_path,
                output_path=output_path,
                findings_count=len(findings),
                entity_counts=entity_counts,
                execution_time=elapsed,
                original_size_bytes=original_size,
                redacted_size_bytes=redacted_size,
                success=True,
            )
        except Exception as e:
            elapsed = time.time() - start_time
            return RedactionResult(
                input_path=input_path,
                output_path=output_path,
                findings_count=0,
                execution_time=elapsed,
                success=False,
                error_message=str(e),
            )
