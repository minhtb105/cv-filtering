"""
Text Validation & Cleaning Module

Handles:
- Bad text detection (poor OCR quality, encoding artifacts)
- Text normalization (whitespace, encoding issues)
- Unicode normalization and accent removal
- Artifact removal (cid patterns, null bytes)
"""

import re
import unicodedata
from typing import Tuple


class TextCleaner:
    """Validates and cleans extracted text with production-grade heuristics."""

    # Artifact patterns that indicate poor extraction quality
    ARTIFACT_PATTERNS = [
        r'\(cid:\d+\)',  # PDF CID artifacts
        r'[\x00]',  # NULL bytes
        r'[\x01-\x08\x0b\x0c\x0e-\x1f]',  # Control characters
    ]

    # Excessive whitespace/newline thresholds
    MAX_CONSECUTIVE_NEWLINES = 3
    NEWLINE_RATIO_THRESHOLD = 0.3  # More than 30% newlines = bad

    @staticmethod
    def is_bad_text(text: str) -> Tuple[bool, str]:
        """
        Heuristic detection of poor extraction quality.

        Returns:
            (is_bad: bool, reason: str)
            - is_bad: True if text quality is poor
            - reason: Explanation of why text is bad
        """
        if not text:
            return True, "Empty text"

        if len(text.strip()) < 10:
            return True, f"Text too short: {len(text.strip())} chars"

        # Check newline ratio
        newline_count = text.count('\n')
        if newline_count > 0:
            newline_ratio = newline_count / len(text)
            if newline_ratio > TextCleaner.NEWLINE_RATIO_THRESHOLD:
                return True, f"Excessive newlines: {newline_ratio:.1%}"

        # Check for excessive consecutive newlines
        if '\n\n\n' in text or '\r\n\r\n\r\n' in text:
            return True, "Excessive consecutive newlines"

        # Check for CID artifacts (OCR garbage)
        cid_matches = len(re.findall(r'\(cid:\d+\)', text))
        if cid_matches > 5:  # Tolerate a few, flag many
            return True, f"High artifact count: {cid_matches} CID patterns"

        # Check for control characters
        if any(ord(c) < 32 and c not in '\t\n\r' for c in text):
            return True, "Contains control characters"

        # Check for excessive spaces (common in table extraction)
        if re.search(r' {4,}', text):
            space_lines = len([l for l in text.split('\n') if re.search(r' {4,}', l)])
            if space_lines / max(len(text.split('\n')), 1) > 0.5:
                return True, f"Excessive spacing in {space_lines} lines"

        return False, "Text OK"

    @staticmethod
    def remove_null_bytes(text: str) -> str:
        """Remove NULL bytes and other problematic control characters."""
        # Remove NULL bytes
        text = text.replace('\x00', '')
        # Remove other control characters (except tab, newline, carriage return)
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\t\n\r')
        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace:
        - Standardize line endings
        - Remove excess consecutive newlines
        - Fix common spacing issues
        """
        # Standardize line endings to \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove excess consecutive newlines (max 2 for paragraphs)
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')

        # Remove trailing/leading whitespace per line
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)

        # Remove multiple consecutive spaces (common in table extraction)
        text = re.sub(r' {2,}', ' ', text)

        return text

    @staticmethod
    def remove_artifacts(text: str) -> str:
        """Remove known PDF extraction artifacts."""
        for pattern in TextCleaner.ARTIFACT_PATTERNS:
            text = re.sub(pattern, '', text)
        return text

    @staticmethod
    def remove_accents(text: str) -> str:
        """
        Remove accents from text (for matching purposes).
        Converts 'Café' → 'Cafe', 'Ételéstéria' → 'Eteleteria'
        """
        # Decompose accented characters
        nfkd = unicodedata.normalize('NFKD', text)
        # Filter out combining marks (accents)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize unicode to NFC form for consistent comparison."""
        return unicodedata.normalize('NFC', text)

    @staticmethod
    def clean_text(
        text: str,
        remove_accents: bool = False,
        lowercase: bool = True,
    ) -> str:
        """
        Complete text cleaning pipeline.

        Args:
            text: Raw extracted text
            remove_accents: If True, remove accents for matching
            lowercase: If True, convert to lowercase

        Returns:
            Cleaned text
        """
        # Step 1: Remove null bytes and control characters
        text = TextCleaner.remove_null_bytes(text)

        # Step 2: Remove extraction artifacts
        text = TextCleaner.remove_artifacts(text)

        # Step 3: Normalize whitespace
        text = TextCleaner.normalize_whitespace(text)

        # Step 4: Normalize unicode
        text = TextCleaner.normalize_unicode(text)

        # Step 5: Remove accents if requested (for matching)
        if remove_accents:
            text = TextCleaner.remove_accents(text)

        # Step 6: Lowercase if requested
        if lowercase:
            text = text.lower()

        return text

    @staticmethod
    def extract_lines(text: str, min_length: int = 1) -> list:
        """
        Extract non-empty lines from text.

        Args:
            text: Input text
            min_length: Minimum line length to include

        Returns:
            List of non-empty lines
        """
        return [
            line.strip()
            for line in text.split('\n')
            if len(line.strip()) >= min_length
        ]

    @staticmethod
    def map_symbols_to_text(text: str) -> str:
        """Map common symbols to readable labels."""
        replacements = {
            '📞': 'Phone:',
            '☎': 'Phone:',
            '✉': 'Email:',
            '✉️': 'Email:',
            '📧': 'Email:',
            '📍': 'Location:',
            '🔗': 'Website:',
            '🌐': 'Website:',
            'linkedin.com': 'LinkedIn:',
            'github.com': 'GitHub:',
        }

        for symbol, label in replacements.items():
            text = text.replace(symbol, label)

        return text

    @staticmethod
    def validate_and_clean(text: str) -> Tuple[bool, str, str]:
        """
        Complete validation and cleaning pipeline.

        Returns:
            (is_valid: bool, reason: str, cleaned_text: str)
        """
        # Check if text is bad
        is_bad, reason = TextCleaner.is_bad_text(text)
        if is_bad:
            return False, f"Bad text: {reason}", ""

        # Clean the text
        cleaned = TextCleaner.clean_text(text)

        # Re-validate after cleaning
        is_bad_after_clean, reason_after = TextCleaner.is_bad_text(cleaned)
        if is_bad_after_clean:
            return False, f"Bad after cleaning: {reason_after}", cleaned

        return True, "Valid text", cleaned
