"""
Text cleaning service.

Normalizes and cleans extracted text for high-quality RAG retrieval.
Provides file-type-aware cleaning with specialized handling for:
- PDF: artifact removal, hyphenation fixing, line break normalization
- Markdown: syntax handling, code block preservation
- CSV: tabular structure preservation
- TXT: general text normalization
"""

import re
import time
import unicodedata
import logging
from typing import Optional, List, Tuple, Set

from app.services.ingestion.types import (
    FileType,
    CleaningResult,
    CleaningMetrics,
)

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Advanced text cleaning service for RAG applications.

    Provides file-type-aware cleaning with metrics tracking.
    """

    # Common page number patterns
    PAGE_NUMBER_PATTERNS = [
        r"^\s*(?:page|p\.?)\s*\d+\s*(?:of\s*\d+)?\s*$",  # "Page 1 of 10"
        r"^\s*-?\s*\d+\s*-?\s*$",  # "- 1 -" or just "1"
        r"^\s*\d+\s*/\s*\d+\s*$",  # "1/10"
    ]

    # Common header/footer patterns (configurable)
    BOILERPLATE_PATTERNS = [
        r"(?:confidential|proprietary|internal use only)",
        r"©\s*\d{4}.*?(?:all rights reserved)?",
        r"^\s*(?:draft|version\s*[\d.]+)\s*$",
    ]

    # Hyphenation pattern - word split across lines
    HYPHENATION_PATTERN = r"(\w+)-\n\s*(\w+)"

    # URL pattern
    URL_PATTERN = r"https?://[^\s<>\"{}|\\^`\[\]]+"

    # Email pattern
    EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    def __init__(
        self,
        remove_page_numbers: bool = True,
        fix_hyphenation: bool = True,
        remove_boilerplate: bool = True,
        normalize_urls: bool = False,
        preserve_tables: bool = True,
        preserve_lists: bool = True,
        custom_header_pattern: Optional[str] = None,
        custom_footer_pattern: Optional[str] = None,
    ):
        """
        Initialize the text cleaner with configuration.

        Args:
            remove_page_numbers: Remove common page number patterns
            fix_hyphenation: Fix words split across lines with hyphens
            remove_boilerplate: Remove common boilerplate text
            normalize_urls: Normalize or remove URLs
            preserve_tables: Attempt to preserve table structure
            preserve_lists: Attempt to preserve list structure
            custom_header_pattern: Regex pattern for document-specific headers
            custom_footer_pattern: Regex pattern for document-specific footers
        """
        self.remove_page_numbers = remove_page_numbers
        self.fix_hyphenation = fix_hyphenation
        self.remove_boilerplate = remove_boilerplate
        self.normalize_urls = normalize_urls
        self.preserve_tables = preserve_tables
        self.preserve_lists = preserve_lists
        self.custom_header_pattern = custom_header_pattern
        self.custom_footer_pattern = custom_footer_pattern

    def clean(
        self,
        text: str,
        file_type: Optional[FileType] = None,
    ) -> CleaningResult:
        """
        Apply all cleaning operations to text based on file type.

        Args:
            text: Raw text content
            file_type: Type of source file for specialized cleaning

        Returns:
            CleaningResult with cleaned text and metrics
        """
        start_time = time.time()

        if not text:
            return CleaningResult(
                text="",
                file_type=file_type or FileType.UNKNOWN,
                metrics=CleaningMetrics(),
            )

        original_length = len(text)
        original_lines = text.count("\n")
        metrics = CleaningMetrics(original_length=original_length)
        warnings: List[str] = []

        # Determine file type if not provided
        if file_type is None:
            file_type = FileType.UNKNOWN

        # Apply file-type-specific cleaning first
        if file_type == FileType.PDF:
            text, pdf_metrics = self._clean_pdf(text)
            metrics.hyphenations_fixed = pdf_metrics.get("hyphenations_fixed", 0)
            metrics.page_artifacts_removed = pdf_metrics.get(
                "page_artifacts_removed", 0
            )
        elif file_type == FileType.MD:
            text = self._clean_markdown(text)
        elif file_type == FileType.CSV:
            text = self._clean_csv(text)
        else:
            text = self._clean_plaintext(text)

        # Apply universal cleaning
        text = self.normalize_unicode(text)
        text = self.remove_control_chars(text)

        # Whitespace normalization
        original_ws_len = len(text)
        text = self.normalize_whitespace(text)
        metrics.whitespace_normalized = original_ws_len - len(text)

        text = self.normalize_newlines(text)

        # Custom header/footer removal
        if self.custom_header_pattern:
            text, count = self._remove_pattern(text, self.custom_header_pattern)
            metrics.headers_removed += count
        if self.custom_footer_pattern:
            text, count = self._remove_pattern(text, self.custom_footer_pattern)
            metrics.footers_removed += count

        # URL normalization
        if self.normalize_urls:
            text, url_count = self._normalize_urls(text)
            metrics.urls_normalized = url_count

        text = text.strip()

        # Calculate final metrics
        metrics.cleaned_length = len(text)
        metrics.chars_removed = original_length - metrics.cleaned_length
        metrics.lines_removed = original_lines - text.count("\n")
        metrics.processing_time_ms = (time.time() - start_time) * 1000

        # Add warnings for potential issues
        if metrics.reduction_percentage > 50:
            warnings.append(
                f"High text reduction ({metrics.reduction_percentage:.1f}%). "
                "Content may have been over-cleaned."
            )

        if metrics.cleaned_length < 100:
            warnings.append("Very short cleaned text. Document may be mostly noise.")

        logger.debug(
            f"Cleaned {file_type.value} document: "
            f"{metrics.original_length} -> {metrics.cleaned_length} chars "
            f"({metrics.reduction_percentage:.1f}% reduction) in "
            f"{metrics.processing_time_ms:.2f}ms"
        )

        return CleaningResult(
            text=text,
            file_type=file_type,
            metrics=metrics,
            warnings=warnings,
        )

    def _clean_pdf(self, text: str) -> Tuple[str, dict]:
        """
        PDF-specific cleaning operations.

        PDFs often have:
        - Hyphenated words split across lines
        - Page numbers, headers, footers
        - Inconsistent spacing from column layouts
        - Ligatures and special characters
        """
        metrics = {"hyphenations_fixed": 0, "page_artifacts_removed": 0}

        # Fix hyphenation (words split across lines)
        if self.fix_hyphenation:
            text, count = self._fix_hyphenation(text)
            metrics["hyphenations_fixed"] = count

        # Remove page numbers
        if self.remove_page_numbers:
            text, count = self._remove_page_numbers(text)
            metrics["page_artifacts_removed"] = count

        # Remove common boilerplate
        if self.remove_boilerplate:
            text = self._remove_boilerplate(text)

        # Fix common PDF extraction issues
        text = self._fix_pdf_ligatures(text)

        # Handle column layout artifacts (double spaces often indicate columns)
        text = re.sub(r"  {2,}", " ", text)

        return text, metrics

    def _clean_markdown(self, text: str) -> str:
        """
        Markdown-specific cleaning.

        Preserve markdown structure while:
        - Normalizing whitespace within paragraphs
        - Keeping code blocks intact
        - Maintaining list formatting
        """
        # Extract and protect code blocks
        code_blocks: List[Tuple[str, str]] = []

        def protect_code_block(match):
            placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
            code_blocks.append((placeholder, match.group(0)))
            return placeholder

        # Protect fenced code blocks
        text = re.sub(r"```[\s\S]*?```", protect_code_block, text)
        text = re.sub(r"~~~[\s\S]*?~~~", protect_code_block, text)

        # Normalize paragraph spacing but keep structure
        # Don't collapse intentional blank lines in markdown
        text = re.sub(r"\n{4,}", "\n\n\n", text)

        # Restore code blocks
        for placeholder, original in code_blocks:
            text = text.replace(placeholder, original)

        return text

    def _clean_csv(self, text: str) -> str:
        """
        CSV-specific cleaning.

        For CSV data:
        - Preserve row/column structure
        - Handle quoted fields
        - Normalize delimiters
        """
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            # Keep the structure but normalize whitespace within cells
            cleaned_lines.append(line.strip())

        return "\n".join(cleaned_lines)

    def _clean_plaintext(self, text: str) -> str:
        """
        General plaintext cleaning.
        """
        # Remove excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _fix_hyphenation(self, text: str) -> Tuple[str, int]:
        """
        Fix words that were hyphenated across line breaks.

        Example: "recog-\nnize" → "recognize"

        Returns:
            Tuple of (fixed text, number of fixes)
        """
        count = 0

        def replacer(match):
            nonlocal count
            count += 1
            return match.group(1) + match.group(2)

        # Don't fix if the hyphenated word is a known compound
        # or if the parts are very short (likely intentional)
        def smart_replacer(match):
            nonlocal count
            word1, word2 = match.group(1), match.group(2)
            # Skip if either part is too short (likely intentional hyphenation)
            if len(word1) < 2 or len(word2) < 2:
                return match.group(0)
            count += 1
            return word1 + word2

        text = re.sub(self.HYPHENATION_PATTERN, smart_replacer, text)
        return text, count

    def _remove_page_numbers(self, text: str) -> Tuple[str, int]:
        """
        Remove common page number patterns.

        Returns:
            Tuple of (cleaned text, number of removals)
        """
        total_removed = 0

        for pattern in self.PAGE_NUMBER_PATTERNS:
            text, count = re.subn(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
            total_removed += count

        return text, total_removed

    def _remove_boilerplate(self, text: str) -> str:
        """
        Remove common boilerplate text.
        """
        for pattern in self.BOILERPLATE_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    def _fix_pdf_ligatures(self, text: str) -> str:
        """
        Replace common PDF ligatures with standard characters.
        """
        ligature_map = {
            "ﬁ": "fi",
            "ﬂ": "fl",
            "ﬀ": "ff",
            "ﬃ": "ffi",
            "ﬄ": "ffl",
            "ﬅ": "st",
            "ﬆ": "st",
        }
        for ligature, replacement in ligature_map.items():
            text = text.replace(ligature, replacement)
        return text

    def _normalize_urls(self, text: str) -> Tuple[str, int]:
        """
        Normalize URLs - either clean or replace with placeholder.
        """
        count = len(re.findall(self.URL_PATTERN, text))
        # Keep URLs but normalize whitespace around them
        text = re.sub(f"\\s*({self.URL_PATTERN})\\s*", r" \1 ", text)
        return text, count

    def _remove_pattern(self, text: str, pattern: str) -> Tuple[str, int]:
        """
        Remove text matching a pattern.
        """
        text, count = re.subn(pattern, "", text, flags=re.MULTILINE)
        return text, count

    def normalize_unicode(self, text: str) -> str:
        """
        Normalize unicode characters to NFC form.
        """
        return unicodedata.normalize("NFC", text)

    def remove_control_chars(self, text: str) -> str:
        """
        Remove control characters except newlines and tabs.
        """
        return "".join(
            char
            for char in text
            if not unicodedata.category(char).startswith("C") or char in "\n\r\t"
        )

    def normalize_whitespace(self, text: str) -> str:
        """
        Replace multiple spaces/tabs with single space.
        """
        # Replace tabs with spaces
        text = text.replace("\t", " ")
        # Replace multiple spaces with single space (but not newlines)
        text = re.sub(r"[^\S\n]+", " ", text)
        # Remove trailing whitespace from lines
        text = re.sub(r" +$", "", text, flags=re.MULTILINE)
        # Remove leading whitespace from lines
        text = re.sub(r"^ +", "", text, flags=re.MULTILINE)
        return text

    def normalize_newlines(self, text: str) -> str:
        """
        Replace multiple newlines with max two newlines.
        """
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Replace 3+ newlines with 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def remove_headers_footers(
        self,
        text: str,
        header_pattern: Optional[str] = None,
        footer_pattern: Optional[str] = None,
    ) -> str:
        """
        Remove repeated headers/footers from text.
        Optional - use patterns if document has consistent headers/footers.
        """
        if header_pattern:
            text = re.sub(header_pattern, "", text, flags=re.MULTILINE)
        if footer_pattern:
            text = re.sub(footer_pattern, "", text, flags=re.MULTILINE)
        return text

    # Legacy method for backward compatibility
    def clean_legacy(self, text: str) -> str:
        """
        Legacy clean method for backward compatibility.
        Returns just the cleaned text string.
        """
        result = self.clean(text)
        return result.text
