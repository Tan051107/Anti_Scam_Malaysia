"""
Preservation Tests — Community PII Censorship
=============================================

These tests are PRESERVATION tests written BEFORE any fixes are applied.
Their purpose is to confirm the EXISTING CORRECT BEHAVIORS on unfixed code,
establishing a baseline that must remain unchanged after all bug fixes are applied.

Convention:
  - All tests in this file MUST PASS on UNFIXED code.
  - They will be re-run after fixes (Task 9.2) to confirm no regressions.

Behaviors confirmed here:
  P2a — JPEG/PNG/WEBP pipeline: _censor_image returns valid image bytes of the same type.
  P2b — Single-word PII extraction: _extract_pii_values returns correct single-word spans.
  P2c — _censor_text Bedrock-success: Bedrock output is returned verbatim.
  P2d — Disallowed MIME type rejection: ALLOWED_IMAGE_TYPES excludes image/bmp and image/tiff.
  P2e — _extract_pii_values with empty/no-PII inputs: returns empty list.
"""

import io
import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Path setup — allow imports from backend/ root when running from repo root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from routers.community import (
    _extract_pii_values,
    _censor_text,
    _censor_image,
    ALLOWED_IMAGE_TYPES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_jpeg() -> bytes:
    """Return a tiny valid JPEG (4×4 white pixel image)."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color=(255, 255, 255)).save(buf, format="JPEG")
    return buf.getvalue()


def _make_minimal_png() -> bytes:
    """Return a tiny valid PNG (4×4 white pixel image)."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _make_minimal_webp() -> bytes:
    """Return a tiny valid WEBP (4×4 white pixel image)."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), color=(180, 180, 180)).save(buf, format="WEBP")
    return buf.getvalue()


def _make_textract_empty_response():
    """Return a minimal Textract analyze_document response with no WORD blocks."""
    return {"Blocks": []}


def _make_bedrock_empty_pii_response():
    """Return a mock Bedrock response body that yields an empty PII list."""
    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps(
        {"content": [{"text": "[]"}]}
    ).encode()
    return mock_body


# ---------------------------------------------------------------------------
# P2a — JPEG/PNG/WEBP pipeline preservation
# ---------------------------------------------------------------------------

class TestP2aImagePipelinePreservation:
    """
    P2a: For a small valid JPEG/PNG/WEBP (< 10 MB), when Textract returns an empty
    blocks response and Bedrock returns [], _censor_image returns bytes that can be
    opened by Pillow as a valid image of the same (or compatible) format.
    """

    def _run_censor_image(self, image_bytes: bytes, content_type: str) -> bytes:
        """Helper: run _censor_image with mocked Textract (empty) and Bedrock (empty PII)."""
        mock_textract_client = MagicMock()
        mock_textract_client.analyze_document.return_value = _make_textract_empty_response()

        mock_bedrock_client = MagicMock()
        mock_bedrock_client.invoke_model.return_value = {
            "body": _make_bedrock_empty_pii_response()
        }

        def fake_boto3_client(service_name, **kwargs):
            if service_name == "textract":
                return mock_textract_client
            return MagicMock()

        with patch("routers.community.boto3.client", side_effect=fake_boto3_client):
            with patch("routers.community.get_bedrock_client", return_value=mock_bedrock_client):
                return _censor_image(image_bytes, content_type)

    def test_jpeg_pipeline_returns_valid_image(self):
        """
        P2a-JPEG: _censor_image with a small JPEG and empty Textract/Bedrock responses
        returns bytes that Pillow can open as a valid image.
        """
        jpeg_bytes = _make_minimal_jpeg()
        result = self._run_censor_image(jpeg_bytes, "image/jpeg")

        # The result must be openable by Pillow
        from PIL import Image
        img = Image.open(io.BytesIO(result))
        assert img is not None, "Result bytes could not be opened by Pillow"
        # JPEG pipeline: when no words found, original bytes are returned (valid JPEG)
        # When words found, output is JPEG. Either way, it must be a valid image.
        assert img.format in ("JPEG", "PNG", "WEBP"), (
            f"Expected a valid image format, got: {img.format}"
        )

    def test_png_pipeline_returns_valid_image(self):
        """
        P2a-PNG: _censor_image with a small PNG and empty Textract/Bedrock responses
        returns bytes that Pillow can open as a valid image.
        """
        png_bytes = _make_minimal_png()
        result = self._run_censor_image(png_bytes, "image/png")

        from PIL import Image
        img = Image.open(io.BytesIO(result))
        assert img is not None, "Result bytes could not be opened by Pillow"
        assert img.format in ("JPEG", "PNG", "WEBP"), (
            f"Expected a valid image format, got: {img.format}"
        )

    def test_webp_pipeline_returns_valid_image(self):
        """
        P2a-WEBP: _censor_image with a small WEBP and empty Textract/Bedrock responses
        returns bytes that Pillow can open as a valid image.
        """
        webp_bytes = _make_minimal_webp()
        result = self._run_censor_image(webp_bytes, "image/webp")

        from PIL import Image
        img = Image.open(io.BytesIO(result))
        assert img is not None, "Result bytes could not be opened by Pillow"
        assert img.format in ("JPEG", "PNG", "WEBP"), (
            f"Expected a valid image format, got: {img.format}"
        )

    def test_jpeg_result_is_non_empty(self):
        """P2a: _censor_image with JPEG returns non-empty bytes."""
        jpeg_bytes = _make_minimal_jpeg()
        result = self._run_censor_image(jpeg_bytes, "image/jpeg")
        assert len(result) > 0, "Expected non-empty result bytes"

    def test_png_result_is_non_empty(self):
        """P2a: _censor_image with PNG returns non-empty bytes."""
        png_bytes = _make_minimal_png()
        result = self._run_censor_image(png_bytes, "image/png")
        assert len(result) > 0, "Expected non-empty result bytes"

    def test_webp_result_is_non_empty(self):
        """P2a: _censor_image with WEBP returns non-empty bytes."""
        webp_bytes = _make_minimal_webp()
        result = self._run_censor_image(webp_bytes, "image/webp")
        assert len(result) > 0, "Expected non-empty result bytes"


# ---------------------------------------------------------------------------
# P2b — Single-word PII extraction preservation
# ---------------------------------------------------------------------------

class TestP2bSingleWordPiiExtraction:
    """
    P2b: _extract_pii_values correctly extracts single-word PII spans.
    These are the non-bug-condition inputs (single-word replacements, no drift).
    """

    def test_single_word_name_extraction(self):
        """
        P2b: 'Hello John owes money' → 'Hello [NAME] owes money'
        Single-word PII span 'John' is correctly extracted.
        """
        result = _extract_pii_values("Hello John owes money", "Hello [NAME] owes money")
        assert result == ["John"], (
            f"Expected ['John'] for single-word name PII, got: {result!r}"
        )

    def test_single_word_email_extraction(self):
        """
        P2b: 'Email test@example.com here' → 'Email [EMAIL] here'
        Single-word PII span 'test@example.com' is correctly extracted.

        Note: Multi-word placeholders like '[PHONE NUMBER]', '[IC NUMBER]', and
        '[BANK ACCOUNT]' split into two tokens when the censored text is split
        by whitespace, so the unfixed word-walk algorithm cannot match them as
        placeholders. We use '[EMAIL]' (a single-token placeholder) to test
        single-word PII extraction for a non-name PII type.
        """
        result = _extract_pii_values(
            "Email test@example.com here",
            "Email [EMAIL] here"
        )
        assert result == ["test@example.com"], (
            f"Expected ['test@example.com'] for single-word email PII, got: {result!r}"
        )

    def test_no_pii_returns_empty_list(self):
        """
        P2b: 'No PII here' → 'No PII here' (no change)
        No PII spans → empty list returned.
        """
        result = _extract_pii_values("No PII here", "No PII here")
        assert result == [], (
            f"Expected [] when original and censored are identical, got: {result!r}"
        )


# ---------------------------------------------------------------------------
# P2c — _censor_text Bedrock-success preservation
# ---------------------------------------------------------------------------

class TestP2cCensorTextBedrockSuccess:
    """
    P2c: When Bedrock succeeds, _censor_text returns the Bedrock-censored string verbatim.
    """

    def test_bedrock_output_returned_verbatim(self):
        """
        P2c: Mock get_bedrock_client to return a client whose invoke_model returns
        a known censored string. Assert _censor_text returns that string unchanged.
        """
        censored_output = "Hello [NAME] please call [PHONE NUMBER]"

        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(
            {"content": [{"text": censored_output}]}
        ).encode()

        mock_bedrock_client = MagicMock()
        mock_bedrock_client.invoke_model.return_value = {"body": mock_body}

        with patch("routers.community.get_bedrock_client", return_value=mock_bedrock_client):
            result = _censor_text("Hello Ahmad please call 0123456789")

        assert result == censored_output, (
            f"Expected Bedrock output returned verbatim.\n"
            f"Expected: {censored_output!r}\n"
            f"Got:      {result!r}"
        )

    def test_bedrock_output_with_multiple_pii_types(self):
        """
        P2c: Bedrock output with multiple PII placeholders is returned verbatim.
        """
        censored_output = "[NAME] IC [IC NUMBER] email [EMAIL]"

        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(
            {"content": [{"text": censored_output}]}
        ).encode()

        mock_bedrock_client = MagicMock()
        mock_bedrock_client.invoke_model.return_value = {"body": mock_body}

        with patch("routers.community.get_bedrock_client", return_value=mock_bedrock_client):
            result = _censor_text("Ahmad IC 901231-14-5678 email test@example.com")

        assert result == censored_output, (
            f"Expected multi-PII Bedrock output returned verbatim.\n"
            f"Expected: {censored_output!r}\n"
            f"Got:      {result!r}"
        )


# ---------------------------------------------------------------------------
# P2d — Disallowed MIME type rejection preservation (static check)
# ---------------------------------------------------------------------------

class TestP2dDisallowedMimeTypes:
    """
    P2d: ALLOWED_IMAGE_TYPES does NOT include image/bmp or image/tiff.
    This is a static check confirming the set membership.
    """

    def test_bmp_not_in_allowed_types(self):
        """P2d: 'image/bmp' must NOT be in ALLOWED_IMAGE_TYPES."""
        assert "image/bmp" not in ALLOWED_IMAGE_TYPES, (
            "image/bmp should not be in ALLOWED_IMAGE_TYPES but it is."
        )

    def test_tiff_not_in_allowed_types(self):
        """P2d: 'image/tiff' must NOT be in ALLOWED_IMAGE_TYPES."""
        assert "image/tiff" not in ALLOWED_IMAGE_TYPES, (
            "image/tiff should not be in ALLOWED_IMAGE_TYPES but it is."
        )

    def test_jpeg_is_in_allowed_types(self):
        """P2d (sanity): 'image/jpeg' IS in ALLOWED_IMAGE_TYPES."""
        assert "image/jpeg" in ALLOWED_IMAGE_TYPES

    def test_png_is_in_allowed_types(self):
        """P2d (sanity): 'image/png' IS in ALLOWED_IMAGE_TYPES."""
        assert "image/png" in ALLOWED_IMAGE_TYPES

    def test_webp_is_in_allowed_types(self):
        """P2d (sanity): 'image/webp' IS in ALLOWED_IMAGE_TYPES."""
        assert "image/webp" in ALLOWED_IMAGE_TYPES


# ---------------------------------------------------------------------------
# P2e — _extract_pii_values with empty inputs
# ---------------------------------------------------------------------------

class TestP2eExtractPiiValuesEdgeCases:
    """
    P2e: _extract_pii_values handles empty and no-PII inputs correctly.
    """

    def test_empty_strings_return_empty_list(self):
        """
        P2e: _extract_pii_values('', '') returns [].
        """
        result = _extract_pii_values("", "")
        assert result == [], (
            f"Expected [] for empty string inputs, got: {result!r}"
        )

    def test_identical_text_no_pii_returns_empty_list(self):
        """
        P2e: _extract_pii_values('some text', 'some text') returns []
        when original and censored are identical (no PII detected).
        """
        result = _extract_pii_values("some text", "some text")
        assert result == [], (
            f"Expected [] when original equals censored (no PII), got: {result!r}"
        )

    def test_longer_identical_text_returns_empty_list(self):
        """
        P2e: Longer identical text with no PII returns [].
        """
        text = "This is a normal sentence with no personal information at all."
        result = _extract_pii_values(text, text)
        assert result == [], (
            f"Expected [] for longer identical text, got: {result!r}"
        )
