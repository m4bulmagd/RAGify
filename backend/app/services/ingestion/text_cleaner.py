"""
Text cleaning service.

Normalizes and cleans extracted text for better processing.
"""

import re
import unicodedata
from typing import Optional


class TextCleaner:
    """
    Cleans and normalizes text content.
    """

    def clean(self, text: str) -> str:
        """
        Apply all cleaning operations to text.

        Args:
            text: Raw text content

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Normalize unicode
        text = self.normalize_unicode(text)

        # Remove control characters
        text = self.remove_control_chars(text)

        # Normalize whitespace
        text = self.normalize_whitespace(text)

        # Remove excessive newlines
        text = self.normalize_newlines(text)

        return text.strip()

    def normalize_unicode(self, text: str) -> str:
        """
        Normalize unicode characters to NFC form.
        """
        return unicodedata.normalize("NFC", text)

    def remove_control_chars(self, text: str) -> str:
        """
        Remove control characters except newlines and tabs.
        """
        # Keep newlines (\n, \r) and tabs (\t)
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
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
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
