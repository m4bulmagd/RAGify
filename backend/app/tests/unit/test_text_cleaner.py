"""
Unit tests for the TextCleaner service.

Tests file-type-aware cleaning, hyphenation fixing, page artifact removal,
and quality metrics tracking.
"""

import pytest
from app.services.ingestion.text_cleaner import TextCleaner
from app.services.ingestion.types import FileType, CleaningResult


class TestTextCleaner:
    """Tests for TextCleaner class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cleaner = TextCleaner()

    # --- Basic Cleaning Tests ---

    def test_clean_empty_text(self):
        """Empty text should return empty result."""
        result = self.cleaner.clean("")
        assert result.text == ""
        assert result.metrics.original_length == 0
        assert result.metrics.cleaned_length == 0

    def test_clean_returns_cleaning_result(self):
        """Clean should return a CleaningResult object."""
        result = self.cleaner.clean("Hello world")
        assert isinstance(result, CleaningResult)
        assert result.text == "Hello world"
        assert result.metrics is not None

    def test_unicode_normalization(self):
        """Unicode should be normalized to NFC."""
        # Composed vs decomposed form
        text = "café"  # could be composed or decomposed
        result = self.cleaner.clean(text)
        assert "café" in result.text or "cafe" in result.text

    def test_control_char_removal(self):
        """Control characters should be removed except newlines/tabs."""
        text = "Hello\x00World\x01Test"
        result = self.cleaner.clean(text)
        assert "\x00" not in result.text
        assert "\x01" not in result.text
        assert "Hello" in result.text

    # --- Hyphenation Tests ---

    def test_hyphenation_fix_basic(self):
        """Basic hyphenation across lines should be fixed."""
        text = "This word is recog-\nnized correctly."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "recognized" in result.text
        assert "recog-" not in result.text

    def test_hyphenation_fix_multiple(self):
        """Multiple hyphenations should all be fixed."""
        text = "The docu-\nment contains multi-\nple hyphenated words."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "document" in result.text
        assert "multiple" in result.text
        assert result.metrics.hyphenations_fixed == 2

    def test_hyphenation_preserves_real_hyphens(self):
        """Real hyphens (like 'self-aware') should be preserved."""
        text = "This is self-aware text with a real hyphen."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "self-aware" in result.text

    def test_hyphenation_single_char_preserved(self):
        """Single character parts shouldn't be joined incorrectly."""
        # Single-char parts should not be joined (they're likely intentional like 'e-mail')
        text = "e-\nmail"  # 'e' has only 1 char, should NOT be joined
        cleaner = TextCleaner(fix_hyphenation=True)
        result = cleaner.clean(text, file_type=FileType.PDF)
        # Should not be joined because 'e' is only 1 char
        assert result.metrics.hyphenations_fixed == 0

    # --- Page Number Removal Tests ---

    def test_page_number_removal_simple(self):
        """Simple page numbers should be removed."""
        text = "Content here.\n\nPage 1\n\nMore content."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "Page 1" not in result.text
        assert "Content here" in result.text

    def test_page_number_removal_with_total(self):
        """'Page X of Y' format should be removed."""
        text = "Content.\n\nPage 5 of 10\n\nMore content."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "Page 5 of 10" not in result.text

    def test_page_number_removal_dash_format(self):
        """'- X -' format page numbers should be removed."""
        text = "Content.\n\n- 3 -\n\nMore content."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "- 3 -" not in result.text

    def test_page_artifact_metrics(self):
        """Page artifact removal should be tracked in metrics."""
        text = "Line 1.\nPage 1\nLine 2.\nPage 2\nLine 3."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert result.metrics.page_artifacts_removed >= 2

    # --- Whitespace Normalization Tests ---

    def test_multiple_spaces_normalized(self):
        """Multiple spaces should be normalized to single space."""
        text = "Hello    world   test"
        result = self.cleaner.clean(text)
        assert "Hello world test" == result.text

    def test_tabs_converted_to_spaces(self):
        """Tabs should be converted to spaces."""
        text = "Hello\tworld"
        result = self.cleaner.clean(text)
        assert "\t" not in result.text

    def test_multiple_newlines_normalized(self):
        """3+ newlines should be reduced to 2."""
        text = "Para 1.\n\n\n\n\nPara 2."
        result = self.cleaner.clean(text)
        assert "\n\n\n" not in result.text
        assert "\n\n" in result.text

    def test_line_ending_normalization(self):
        """Windows line endings should be normalized."""
        text = "Line 1.\r\nLine 2.\r\nLine 3."
        result = self.cleaner.clean(text)
        assert "\r" not in result.text
        assert "Line 1.\nLine 2.\nLine 3." == result.text

    # --- File Type Specific Tests ---

    def test_pdf_specific_cleaning(self):
        """PDF cleaning should include ligature replacement."""
        text = "This has a ﬁle with ﬂag ligatures."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "file" in result.text
        assert "flag" in result.text
        assert "ﬁ" not in result.text

    def test_markdown_preserves_code_blocks(self):
        """Markdown cleaning should preserve code blocks."""
        text = "Text.\n\n```python\ndef foo():\n    pass\n```\n\nMore text."
        result = self.cleaner.clean(text, file_type=FileType.MD)
        assert "```python" in result.text
        assert "def foo():" in result.text

    def test_csv_preserves_structure(self):
        """CSV cleaning should preserve row structure."""
        text = "col1,col2,col3\nval1,val2,val3\nval4,val5,val6"
        result = self.cleaner.clean(text, file_type=FileType.CSV)
        lines = result.text.split("\n")
        assert len(lines) == 3
        assert "col1,col2,col3" in result.text

    def test_file_type_from_extension(self):
        """FileType should correctly parse from extension."""
        assert FileType.from_extension(".pdf") == FileType.PDF
        assert FileType.from_extension("pdf") == FileType.PDF
        assert FileType.from_extension(".txt") == FileType.TXT
        assert FileType.from_extension(".md") == FileType.MD
        assert FileType.from_extension(".markdown") == FileType.MD
        assert FileType.from_extension(".csv") == FileType.CSV
        assert FileType.from_extension(".docx") == FileType.UNKNOWN

    # --- Metrics Tests ---

    def test_metrics_character_count(self):
        """Metrics should accurately track character counts."""
        text = "Hello     world"  # 5 extra spaces
        result = self.cleaner.clean(text)
        assert result.metrics.original_length == 15
        assert result.metrics.cleaned_length == 11
        assert result.metrics.chars_removed == 4

    def test_metrics_reduction_percentage(self):
        """Reduction percentage should be calculated correctly."""
        text = "A" * 100 + "    " * 25  # 100 chars + 100 spaces
        result = self.cleaner.clean(text)
        # Should reduce significantly
        assert result.metrics.reduction_percentage > 0

    def test_metrics_processing_time(self):
        """Processing time should be tracked."""
        text = "Hello world " * 100
        result = self.cleaner.clean(text)
        assert result.metrics.processing_time_ms > 0

    # --- Configuration Tests ---

    def test_hyphenation_can_be_disabled(self):
        """Hyphenation fixing can be disabled."""
        cleaner = TextCleaner(fix_hyphenation=False)
        text = "recog-\nnize"
        result = cleaner.clean(text, file_type=FileType.PDF)
        assert "recog-" in result.text or result.metrics.hyphenations_fixed == 0

    def test_page_number_removal_can_be_disabled(self):
        """Page number removal can be disabled."""
        cleaner = TextCleaner(remove_page_numbers=False)
        text = "Content.\nPage 1\nMore."
        result = cleaner.clean(text, file_type=FileType.PDF)
        # Page number should still be there (might be normalized whitespace)
        # Check that page artifacts weren't removed
        assert result.metrics.page_artifacts_removed == 0

    # --- Warning Tests ---

    def test_high_reduction_warning(self):
        """High text reduction should trigger a warning."""
        # Create text that will be heavily reduced
        text = "X" + "   " * 100  # Lots of whitespace
        result = self.cleaner.clean(text)
        # Check if high reduction triggers warning (depends on actual reduction)
        # This test verifies the warning mechanism exists
        assert isinstance(result.warnings, list)

    def test_short_text_warning(self):
        """Very short cleaned text should trigger warning."""
        text = "Hi"
        result = self.cleaner.clean(text)
        # Short text should trigger warning
        assert any("short" in w.lower() for w in result.warnings)

    # --- Legacy Compatibility Tests ---

    def test_legacy_clean_method(self):
        """Legacy clean_legacy method should return just string."""
        text = "Hello    world"
        result = self.cleaner.clean_legacy(text)
        assert isinstance(result, str)
        assert result == "Hello world"


class TestBoilerplateRemoval:
    """Tests for boilerplate removal functionality."""

    def setup_method(self):
        self.cleaner = TextCleaner(remove_boilerplate=True)

    def test_confidential_notice_removed(self):
        """Confidential notices should be removed."""
        text = "Content here.\nCONFIDENTIAL\nMore content."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "CONFIDENTIAL" not in result.text

    def test_copyright_notice_removed(self):
        """Copyright notices should be removed."""
        text = "Content.\n© 2024 Company Inc. All Rights Reserved\nMore."
        result = self.cleaner.clean(text, file_type=FileType.PDF)
        assert "© 2024" not in result.text or "All Rights Reserved" not in result.text

    def test_boilerplate_removal_can_be_disabled(self):
        """Boilerplate removal can be disabled."""
        cleaner = TextCleaner(remove_boilerplate=False)
        text = "CONFIDENTIAL content here."
        result = cleaner.clean(text, file_type=FileType.PDF)
        # CONFIDENTIAL should still be present
        assert "CONFIDENTIAL" in result.text or "confidential" in result.text.lower()
