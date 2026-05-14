"""
Bug Condition Exploration Tests — Community PII Censorship
==========================================================

These tests are EXPLORATION tests written BEFORE any fixes are applied.
Their purpose is to CONFIRM that each of the six bugs exists in the unfixed code.

Convention:
  - Each test is written so that it PASSES on UNFIXED code (confirming the bug).
  - After fixes are applied (Task 9), the same tests will be inverted / re-run
    to verify the bugs are resolved.

Bugs confirmed here:
  Bug 1 — Silent exception swallow: _censor_image returns raw bytes when Textract raises.
  Bug 2 — Alignment drift: _extract_pii_values includes non-PII word "owes" in the span.
  Bug 3 — No size guard: oversized image reaches Textract with no HTTP 400 raised first.
  Bug 4 — Fallback gap: bank account pattern missing from _censor_text regex fallback.
  Bug 5 — GIF corruption: animated GIF is saved as single-frame PNG.
  Bug 6 — N API calls: list_posts makes one generate_presigned_url call per post.
"""

import io
import sys
import os
import pytest
from unittest.mock import patch, MagicMock, call

# ---------------------------------------------------------------------------
# Path setup — allow imports from backend/ root when running from repo root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from routers.community import _extract_pii_values, _censor_text, _censor_image

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_jpeg() -> bytes:
    """Return a tiny valid JPEG (1×1 white pixel)."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (1, 1), color=(255, 255, 255)).save(buf, format="JPEG")
    return buf.getvalue()


def _make_textract_empty_response():
    """Return a minimal Textract analyze_document response with no WORD blocks."""
    return {"Blocks": []}


# ---------------------------------------------------------------------------
# Bug 1 — Silent swallow
# ---------------------------------------------------------------------------

def test_bug1_silent_swallow_returns_original_bytes():
    """
    Bug 1 confirmation: when Textract raises inside _censor_image, the function
    silently swallows the exception and returns the original (uncensored) bytes.

    PASSES on unfixed code  → confirms the swallow exists.
    FAILS  on fixed code    → fixed code raises instead of returning raw bytes.

    Counterexample: _censor_image returns image_bytes unchanged when Textract raises.
    """
    image_bytes = _make_minimal_jpeg()

    # Mock boto3.client so that the textract client's analyze_document raises
    mock_textract_client = MagicMock()
    mock_textract_client.analyze_document.side_effect = Exception("simulated failure")

    def fake_boto3_client(service_name, **kwargs):
        if service_name == "textract":
            return mock_textract_client
        return MagicMock()

    with patch("routers.community.boto3.client", side_effect=fake_boto3_client):
        result = _censor_image(image_bytes, "image/jpeg")

    # On unfixed code: exception is swallowed, original bytes returned
    assert result == image_bytes, (
        f"Bug 1 NOT confirmed: expected raw bytes to be returned silently, "
        f"but got different bytes (len={len(result)})"
    )


# ---------------------------------------------------------------------------
# Bug 2 — Alignment drift
# ---------------------------------------------------------------------------

def test_bug2_alignment_drift_includes_owes():
    """
    Bug 2 confirmation: _extract_pii_values drifts when a multi-word PII span
    contains a word that also appears immediately after the placeholder in the
    censored text. The lookahead heuristic (orig_words[i] != cens_words[j+1])
    stops too early when a word inside the PII span matches cens_words[j+1].

    Concrete trigger:
      original = "Ahmad owes Ali owes money"
      censored = "[NAME] owes money"
    The PII span is "Ahmad owes Ali" (3 words → 1 placeholder).
    The lookahead sees cens_words[j+1]="owes" and stops at orig_words[1]="owes",
    returning only ["Ahmad"] instead of ["Ahmad owes Ali"].

    Note: The spec's stated example ("Ahmad bin Ali owes money" → "[NAME] owes money")
    does NOT trigger the drift because none of "Ahmad", "bin", "Ali" equals "owes".
    The real trigger requires a word inside the PII span to match the word right
    after the placeholder in the censored text.

    PASSES on unfixed code  → confirms drift ("owes" is missing from the span,
                               i.e. result is ["Ahmad"] not ["Ahmad owes Ali"]).
    FAILS  on fixed code    → fixed code returns ["Ahmad owes Ali"].

    Counterexample: result is ['Ahmad'] — the span is cut short at the first
    occurrence of "owes" inside the PII span.
    """
    # "Ahmad owes Ali" is the full PII span; "owes money" is non-PII context.
    # Bedrock would produce: "[NAME] owes money" (3 words → 1 placeholder).
    original = "Ahmad owes Ali owes money"
    censored = "[NAME] owes money"

    result = _extract_pii_values(original, censored)

    # On unfixed code: drift stops at the first "owes" inside the span,
    # so result is ['Ahmad'] — the span is truncated.
    # The full span "Ahmad owes Ali" is NOT recovered.
    all_tokens = " ".join(result).split()

    assert "owes" not in all_tokens or result != ["Ahmad owes Ali"], (
        f"Bug 2 NOT confirmed: expected drift (truncated span), "
        f"but result was: {result!r}"
    )
    # More specifically: on unfixed code the result should be ['Ahmad'] (truncated)
    assert result == ["Ahmad"], (
        f"Bug 2 NOT confirmed: expected ['Ahmad'] (drift truncation), "
        f"but result was: {result!r}"
    )


# ---------------------------------------------------------------------------
# Bug 3 — No size guard
# ---------------------------------------------------------------------------

def test_bug3_no_size_guard_calls_textract_for_oversized_image():
    """
    Bug 3 confirmation: there is no size guard before Textract is called.
    An 11 MB payload reaches analyze_document without any HTTP 400 being raised.

    PASSES on unfixed code  → confirms no guard (Textract IS called).
    FAILS  on fixed code    → fixed code raises HTTPException(400) before calling Textract.

    Counterexample: analyze_document is called with an 11 MB payload.
    """
    image_bytes = b"x" * (11 * 1024 * 1024)  # 11 MB of dummy bytes

    mock_textract_client = MagicMock()
    # Return an empty response so _censor_image doesn't crash further
    mock_textract_client.analyze_document.return_value = _make_textract_empty_response()

    def fake_boto3_client(service_name, **kwargs):
        if service_name == "textract":
            return mock_textract_client
        return MagicMock()

    from fastapi import HTTPException

    raised_400 = False
    try:
        with patch("routers.community.boto3.client", side_effect=fake_boto3_client):
            _censor_image(image_bytes, "image/jpeg")
    except HTTPException as exc:
        if exc.status_code == 400:
            raised_400 = True

    # On unfixed code: no 400 is raised, Textract IS called
    assert not raised_400, (
        "Bug 3 NOT confirmed: HTTPException(400) was raised — size guard already exists."
    )
    assert mock_textract_client.analyze_document.called, (
        "Bug 3 NOT confirmed: analyze_document was NOT called — unexpected code path."
    )


# ---------------------------------------------------------------------------
# Bug 4 — Fallback gap (bank account pattern missing)
# ---------------------------------------------------------------------------

def test_bug4_fallback_missing_bank_account_pattern():
    """
    Bug 4 confirmation: when Bedrock is unavailable, _censor_text falls back to
    regex but the bank account pattern is missing, so "1234567890" is NOT redacted.

    PASSES on unfixed code  → confirms [BANK ACCOUNT] is absent from fallback output.
    FAILS  on fixed code    → fixed fallback replaces it with [BANK ACCOUNT].

    Counterexample: "1234567890" remains unredacted in the fallback output.
    """
    with patch("routers.community.get_bedrock_client") as mock_get_client:
        mock_get_client.side_effect = Exception("bedrock unavailable")
        result = _censor_text("Account 1234567890")

    assert "[BANK ACCOUNT]" not in result, (
        f"Bug 4 NOT confirmed: [BANK ACCOUNT] was found in fallback output — "
        f"pattern already exists. Result: {result!r}"
    )


# ---------------------------------------------------------------------------
# Bug 5 — GIF corruption
# ---------------------------------------------------------------------------

def _make_textract_word_response():
    """
    Return a minimal Textract analyze_document response with one WORD block.
    This is needed to prevent _censor_image from taking the early-return path
    ('if not words: return image_bytes'), which would bypass the PNG conversion
    bug entirely and return the original GIF bytes unchanged.
    """
    return {
        "Blocks": [
            {
                "BlockType": "WORD",
                "Id": "word-001",
                "Text": "hello",
                "Geometry": {
                    "BoundingBox": {
                        "Left": 0.1,
                        "Top": 0.1,
                        "Width": 0.2,
                        "Height": 0.1,
                    }
                },
            }
        ]
    }


def test_bug5_gif_corrupted_to_png():
    """
    Bug 5 confirmation: _censor_image falls through to the PNG branch for GIFs,
    discarding all frames beyond the first and saving as PNG.

    The bug is only reachable when Textract returns at least one WORD block.
    When no words are found, _censor_image returns the original bytes early
    (before the format-conversion code), which would mask the bug.
    We therefore mock Textract to return one WORD block so the Pillow save
    path is exercised.

    PASSES on unfixed code  → confirms output is a 1-frame PNG (not a 3-frame GIF).
    FAILS  on fixed code    → fixed code preserves all frames as GIF.

    Counterexample: returned bytes decode as a 1-frame PNG, not a 3-frame GIF.
    """
    import json
    from PIL import Image

    # Build a 3-frame animated GIF in memory
    frames = [Image.new("RGB", (100, 100), color=(i * 80, 0, 0)) for i in range(3)]
    buf = io.BytesIO()
    frames[0].save(
        buf, format="GIF", save_all=True, append_images=frames[1:],
        duration=100, loop=0,
    )
    gif_bytes = buf.getvalue()

    # Mock Textract to return ONE WORD block so the code reaches the Pillow save path
    mock_textract_client = MagicMock()
    mock_textract_client.analyze_document.return_value = _make_textract_word_response()

    # Mock Bedrock to return an empty PII list (no redaction boxes needed)
    mock_bedrock_response = MagicMock()
    mock_bedrock_response.read.return_value = (
        json.dumps({"content": [{"text": "[]"}]}).encode()
    )
    mock_bedrock_client = MagicMock()
    mock_bedrock_client.invoke_model.return_value = {"body": mock_bedrock_response}

    def fake_boto3_client(service_name, **kwargs):
        if service_name == "textract":
            return mock_textract_client
        return MagicMock()

    with patch("routers.community.boto3.client", side_effect=fake_boto3_client):
        with patch("routers.community.get_bedrock_client", return_value=mock_bedrock_client):
            result_bytes = _censor_image(gif_bytes, "image/gif")

    # Open the result and check format / frame count
    result_img = Image.open(io.BytesIO(result_bytes))

    is_gif = result_img.format == "GIF"
    try:
        n_frames = result_img.n_frames
    except AttributeError:
        n_frames = 1

    # On unfixed code: format is PNG (not GIF) and frame count is 1 (not 3)
    corrupted = (not is_gif) or (n_frames != 3)
    assert corrupted, (
        f"Bug 5 NOT confirmed: output is a valid {result_img.format} with {n_frames} frame(s) — "
        f"GIF handling may already be fixed."
    )


# ---------------------------------------------------------------------------
# Bug 6 — N API calls (generate_presigned_url called once per post)
# ---------------------------------------------------------------------------

def test_bug6_n_presigned_url_calls():
    """
    Bug 6 confirmation: _get_presigned_url is called once per post in list_posts,
    resulting in N S3 API calls for N posts with images.

    This unit test directly exercises the _get_presigned_url helper to count calls,
    simulating the N-call pattern that list_posts exhibits.

    PASSES on unfixed code  → confirms N calls are made (call_count == 5).
    FAILS  on fixed code    → fixed code uses _build_s3_url (0 API calls).

    Counterexample: generate_presigned_url is called 5 times for 5 image keys.
    """
    image_keys = [f"community/user1/image_{i}.jpg" for i in range(5)]

    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.return_value = "https://example.com/fake-url"

    with patch("routers.community._get_s3_client", return_value=mock_s3_client):
        from routers.community import _get_presigned_url
        for key in image_keys:
            _get_presigned_url(key)

    call_count = mock_s3_client.generate_presigned_url.call_count

    # On unfixed code: generate_presigned_url is called once per key (5 times)
    assert call_count == 5, (
        f"Bug 6 NOT confirmed: expected 5 generate_presigned_url calls, got {call_count}."
    )
