# Community PII Censorship Fixes — Bugfix Design

## Overview

This document formalises the fix strategy for six defects in `backend/routers/community.py`.
The bugs collectively create privacy risks (raw images stored in S3), data corruption (GIF frames
lost, false-positive redactions), missing input validation (no size guard before AWS calls),
incomplete fallback coverage (regex misses bank accounts and passports), and unnecessary latency
(N S3 API calls per listing page).

The fix approach is surgical: each change targets exactly the defective code path, and the
correctness properties below define both what must change and what must stay the same.

---

## Glossary

- **Bug_Condition (C)**: The set of inputs or execution states that trigger one of the six defects.
- **Property (P)**: The desired observable behaviour when the bug condition holds after the fix is applied.
- **Preservation**: All existing correct behaviours that must remain unchanged after the fix.
- **`_censor_image`**: The function in `backend/routers/community.py` that runs the four-layer PII
  redaction pipeline on raw image bytes and returns censored image bytes.
- **`_extract_message_from_image`**: The function that calls Bedrock to extract suspicious text from
  an image; used to populate `original_message` when the caller does not supply one.
- **`_censor_text`**: The function that calls Bedrock to replace PII tokens in a text string with
  labelled placeholders; falls back to regex when Bedrock is unavailable.
- **`_extract_pii_values`**: The function that diffs the original and censored text strings to
  recover the original word spans that were replaced by placeholders.
- **`_get_presigned_url`**: The current helper that makes one S3 `generate_presigned_url` API call
  per invocation; called once per post in listing endpoints.
- **`_build_s3_url`**: The new local helper that constructs an S3 URL from a key without any API
  call.
- **`MAX_IMAGE_SIZE_BYTES`**: New module-level constant set to `10 * 1024 * 1024` (10 MB).
- **Placeholder token**: A string such as `[NAME]`, `[IC NUMBER]`, `[PHONE NUMBER]`, `[EMAIL]`,
  `[BANK ACCOUNT]`, `[ADDRESS]`, or `[PASSPORT]` inserted by Bedrock in place of a PII span.
- **Word-alignment drift**: The progressive desynchronisation between the `orig_words` and
  `cens_words` index pointers in `_extract_pii_values` when a multi-word PII span is replaced by a
  single placeholder token.

---

## Bug Details

### Bug Condition

The six bugs share a common structure: each is triggered by a specific input or execution state
that the current code handles incorrectly.

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input — one of:
           ExceptionEvent(site)          -- an exception raised at a specific call site
           TextDiff(original, censored)  -- a pair of strings fed to _extract_pii_values
           ImageUpload(bytes, mime)      -- raw image bytes with MIME type
           FallbackTextCensor(text)      -- text censored via regex fallback
           ListRequest(posts)            -- a listing request returning N posts with images
  OUTPUT: boolean

  RETURN (
    -- Bug 1: exception swallowed silently
    (site IN {_censor_image_outer, _extract_message_from_image, _censor_image_layer3}
     AND ExceptionRaised(site))

    OR

    -- Bug 2: multi-word PII causes alignment drift
    (input IS TextDiff
     AND EXISTS placeholder IN censored_words
         WHERE placeholder maps to multiple words in original)

    OR

    -- Bug 3: oversized image bypasses size guard
    (input IS ImageUpload
     AND len(bytes) > MAX_IMAGE_SIZE_BYTES)

    OR

    -- Bug 4: fallback regex misses bank account / passport
    (input IS FallbackTextCensor
     AND (ContainsBankAccount(text) OR ContainsPassport(text))
     AND BedrockUnavailable())

    OR

    -- Bug 5: GIF falls through to PNG branch
    (input IS ImageUpload AND mime == "image/gif")

    OR

    -- Bug 6: listing makes N presigned-URL API calls
    (input IS ListRequest AND len(posts_with_images) > 0)
  )
END FUNCTION
```

### Examples

**Bug 1 — Silent swallow:**
- Textract raises `InvalidParameterException` inside `_censor_image` → current code returns raw
  `image_bytes`; fixed code logs ERROR and raises `HTTPException(500)`.
- Bedrock times out inside `_extract_message_from_image` → current code returns `""`; fixed code
  logs WARNING and returns `""` (same return value, but now logged).

**Bug 2 — Alignment drift:**
- `original = "Ahmad bin Ali owes money"`, `censored = "[NAME] owes money"`.
  Current: `pii_values = ["Ahmad", "bin", "Ali", "owes"]` (drift consumes "owes").
  Fixed: `pii_values = ["Ahmad bin Ali"]`.

**Bug 3 — No size guard:**
- 15 MB JPEG uploaded → current code calls Textract, which raises `InvalidS3ObjectException`;
  exception is swallowed and raw image stored. Fixed code returns HTTP 400 before any AWS call.

**Bug 4 — Incomplete fallback:**
- Bedrock down, text contains `"Account: 1234567890"` → current fallback leaves it unredacted.
  Fixed fallback replaces it with `[BANK ACCOUNT]`.

**Bug 5 — GIF corruption:**
- 10-frame animated GIF uploaded → current code saves frame 0 as PNG under a `.gif` key.
  Fixed code iterates all frames, applies redaction per frame, saves as GIF preserving animation.

**Bug 6 — N API calls:**
- `list_posts` returns 20 posts each with an image → current code makes 20 S3 API calls.
  Fixed code makes 0 S3 API calls, constructing URLs locally.

---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- JPEG and PNG images continue to be processed through all four censorship layers and stored in S3.
- WEBP images continue to be processed and stored.
- When Bedrock succeeds in `_censor_text`, all seven PII categories are replaced.
- Textract KV-pair auto-flagging (Layer 1) continues to work for known `PII_FIELD_KEYS`.
- `_extract_pii_values` continues to return correct single-word PII spans when no multi-word drift
  can occur.
- Images with no Textract-detectable text continue to return (censored) image bytes without error.
- Posts created without images continue to store `image_key = None` and return `image_url: null`.
- `list_posts` continues to return posts ordered by upvote count desc, then creation date desc,
  with correct upvote counts and `has_upvoted` flags.
- Post deletion continues to attempt S3 object removal and database record deletion.
- Uploads of disallowed MIME types continue to be rejected with HTTP 400.

**Scope:**
All inputs that do NOT satisfy `isBugCondition` must be completely unaffected by the fix. This
includes successful Textract/Bedrock calls, single-word PII replacements, sub-10 MB images,
JPEG/PNG/WEBP uploads, Bedrock-available text censorship, and post operations that do not involve
image listing.

---

## Hypothesized Root Cause

1. **Overly broad bare `except Exception: pass/return` clauses (Bug 1)**
   The outer `try/except` in `_censor_image` and `_extract_message_from_image` was written to
   guarantee a return value under all conditions, but it silently discards the exception and — in
   the case of `_censor_image` — returns the uncensored bytes, defeating the privacy guarantee.
   The Layer 3 inner `except Exception: pass` similarly discards Bedrock failures.

2. **Naive word-by-word index walk without sequence alignment (Bug 2)**
   `_extract_pii_values` increments `i` (original index) and `j` (censored index) in lockstep,
   assuming a 1-to-1 word correspondence. When Bedrock collapses N original words into 1
   placeholder, the lookahead heuristic (`orig_words[i] != cens_words[j + 1]`) is fragile and
   fails when the word immediately after the placeholder happens to match an original word inside
   the PII span.

3. **No pre-flight size check before AWS calls (Bug 3)**
   The `create_post` endpoint reads the full image bytes and immediately passes them to
   `_censor_image`, which forwards them to Textract. Textract's 10 MB limit is not enforced
   locally, so oversized payloads reach the AWS API, raise an exception, and trigger the silent
   swallow in Bug 1.

4. **Fallback regex list was written for the MVP and never extended (Bug 4)**
   The three patterns in the `except` branch of `_censor_text` cover only IC, phone, and email —
   the patterns that were present in the original `PII_PATTERNS` list. Bank account and passport
   patterns were added to `PII_PATTERNS` later but were never mirrored in the fallback.

5. **Image format branch only checks JPEG vs. everything-else (Bug 5)**
   The `fmt` assignment `"JPEG" if content_type in ("image/jpeg", "image/jpg") else "PNG"` was
   written before GIF support was added to `ALLOWED_IMAGE_TYPES`. GIFs fall into the `else` branch,
   and `Image.open(...).convert("RGB")` discards the palette and all frames beyond the first.

6. **`_get_presigned_url` wraps a synchronous S3 API call (Bug 6)**
   Presigned URLs are generated by signing a request locally using the AWS SDK — no network round
   trip is strictly required — but the current implementation calls `generate_presigned_url` which
   does perform SDK work proportional to the number of calls. For public-read or path-style buckets
   the URL can be constructed deterministically from the bucket name, region, and key.

---

## Correctness Properties

Property 1: Bug Condition — Exception Sites Must Not Silently Swallow Errors

_For any_ execution where an exception is raised at one of the three identified sites
(`_censor_image` outer handler, `_extract_message_from_image` handler, `_censor_image` Layer 3
handler), the fixed code SHALL log the exception and either propagate it as an `HTTPException` (for
the outer `_censor_image` handler) or return a safe degraded value with a log entry (for the other
two sites), and SHALL NOT return uncensored image bytes to the caller.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Bug Condition — `_extract_pii_values` Alignment Correctness

_For any_ pair `(original_text, censored_text)` where `censored_text` was produced by replacing
one or more contiguous word spans in `original_text` with placeholder tokens, the fixed
`_extract_pii_values` SHALL return exactly the original word spans that correspond to each
placeholder, with no non-PII words included and no PII words omitted.

**Validates: Requirements 2.4, 2.5**

Property 3: Bug Condition — Image Size Rejection

_For any_ image upload where `len(image_bytes) > MAX_IMAGE_SIZE_BYTES`, the fixed `create_post`
endpoint SHALL return HTTP 400 before calling Textract or Bedrock, and SHALL NOT write any bytes
to S3.

**Validates: Requirements 2.6, 2.7**

Property 4: Bug Condition — Fallback Regex Completeness

_For any_ text that contains a bank account number (10–16 consecutive digits) or a passport number
(one letter followed by 7–9 digits) when Bedrock is unavailable, the fixed `_censor_text` fallback
SHALL replace those patterns with `[BANK ACCOUNT]` and `[PASSPORT]` respectively.

**Validates: Requirement 2.8**

Property 5: Bug Condition — GIF Frame Preservation

_For any_ GIF image upload (MIME type `image/gif`), the fixed `_censor_image` SHALL process every
frame, apply redaction boxes to each frame, and save the output as a valid GIF file preserving
animation metadata (frame durations, loop count, palette).

**Validates: Requirements 2.9, 2.10**

Property 6: Bug Condition — O(1) S3 Calls on Listing

_For any_ call to `list_posts` or `list_my_posts` that returns a page of N posts with images, the
fixed code SHALL construct image URLs without making any S3 API calls, so the number of S3 API
calls is O(1) (zero) regardless of N.

**Validates: Requirements 2.11, 2.12**

Property 7: Preservation — Existing Censorship Pipeline Unchanged

_For any_ input where `isBugCondition` returns false (successful Textract/Bedrock calls on a
sub-10 MB JPEG, PNG, or WEBP image), the fixed `_censor_image` SHALL produce the same redacted
output as the original function, preserving all four censorship layers.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

Property 8: Preservation — Post Lifecycle Operations Unchanged

_For any_ post creation without an image, post deletion, or upvote operation, the fixed code SHALL
produce exactly the same behaviour as the original code.

**Validates: Requirements 3.7, 3.8, 3.9, 3.10**

---

## Fix Implementation

### Changes Required

**File**: `backend/routers/community.py`

#### Change 1 — Add `MAX_IMAGE_SIZE_BYTES` constant and `logging` import (Bug 3 + Bug 1)

Add at the top of the module alongside existing imports and constants:

```python
import logging
logger = logging.getLogger(__name__)

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB — Textract hard limit
```

#### Change 2 — Replace silent swallows with logged handlers (Bug 1)

**`_extract_message_from_image`** — change the bare `except`:
```python
except Exception as exc:
    logger.warning("_extract_message_from_image failed: %s", exc, exc_info=True)
    return ""
```

**`_censor_image` outer handler** — change the bare `except` that returns raw bytes:
```python
except Exception as exc:
    logger.error(
        "_censor_image pipeline failed — refusing to return uncensored bytes: %s",
        exc, exc_info=True,
    )
    raise
```
The caller (`create_post`) must catch this and return HTTP 500 rather than storing the raw image.

**`_censor_image` Layer 3 inner handler** — change the bare `except Exception: pass`:
```python
except Exception as exc:
    logger.warning(
        "_censor_image Layer 3 Bedrock call failed — continuing with Layers 1+2 only: %s",
        exc, exc_info=True,
    )
```

#### Change 3 — Add size guard in `create_post` before `_censor_image` (Bug 3)

After `image_bytes = await image.read()`, add:
```python
if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
    raise HTTPException(
        status_code=400,
        detail=f"Image exceeds the {MAX_IMAGE_SIZE_BYTES // (1024*1024)} MB size limit.",
    )
```

#### Change 4 — Replace word-walk with `difflib.SequenceMatcher` in `_extract_pii_values` (Bug 2)

Replace the entire `i, j` loop with a sequence-matcher approach:

```python
import difflib

def _extract_pii_values(original_text: str, censored_text: str) -> list:
    if not original_text or not censored_text:
        return []
    placeholder_re = re.compile(
        r'\[(?:NAME|IC NUMBER|PHONE NUMBER|EMAIL|BANK ACCOUNT|ADDRESS|PASSPORT)\]'
    )
    orig_words = original_text.split()
    cens_words = censored_text.split()
    pii_values = []

    matcher = difflib.SequenceMatcher(None, orig_words, cens_words, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            # The censored slice may be one or more placeholder tokens
            cens_slice = cens_words[j1:j2]
            if all(placeholder_re.fullmatch(t) for t in cens_slice):
                span = " ".join(orig_words[i1:i2])
                if span:
                    pii_values.append(span)
    return pii_values
```

#### Change 5 — Extend fallback regex in `_censor_text` (Bug 4)

In the `except` branch of `_censor_text`, add after the existing three substitutions:
```python
text = re.sub(r'\b\d{10,16}\b', '[BANK ACCOUNT]', text)
text = re.sub(r'\b[A-Za-z]\d{7,9}\b', '[PASSPORT]', text)
```

#### Change 6 — Add explicit GIF branch in `_censor_image` (Bug 5)

Replace the current format-selection and save block:
```python
# BEFORE
img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
draw = ImageDraw.Draw(img)
...
out = io.BytesIO()
fmt = "JPEG" if content_type in ("image/jpeg", "image/jpg") else "PNG"
img.save(out, format=fmt, quality=90)
return out.getvalue()
```

With a format-aware save that handles GIF frame iteration:
```python
if content_type == "image/gif":
    src = Image.open(io.BytesIO(image_bytes))
    frames = []
    durations = []
    try:
        while True:
            frame = src.copy().convert("RGBA")
            draw = ImageDraw.Draw(frame)
            iw, ih = frame.size
            for word in words:
                token = word["text"].lower().strip(".,!?;:\"'()[]")
                if token in pii_set or word["id"] in kv_value_ids or word["id"] in regex_flagged_ids:
                    x1 = max(0,  int(word["left"] * iw) - pad)
                    y1 = max(0,  int(word["top"]  * ih) - pad)
                    x2 = min(iw, int((word["left"] + word["width"])  * iw) + pad)
                    y2 = min(ih, int((word["top"]  + word["height"]) * ih) + pad)
                    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, 255))
            frames.append(frame.convert("P", palette=Image.ADAPTIVE))
            durations.append(src.info.get("duration", 100))
            src.seek(src.tell() + 1)
    except EOFError:
        pass
    out = io.BytesIO()
    frames[0].save(
        out, format="GIF", save_all=True, append_images=frames[1:],
        loop=src.info.get("loop", 0), duration=durations, disposal=2,
    )
    return out.getvalue()
else:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    iw, ih = img.size
    for word in words:
        token = word["text"].lower().strip(".,!?;:\"'()[]")
        if token in pii_set or word["id"] in kv_value_ids or word["id"] in regex_flagged_ids:
            x1 = max(0,  int(word["left"] * iw) - pad)
            y1 = max(0,  int(word["top"]  * ih) - pad)
            x2 = min(iw, int((word["left"] + word["width"])  * iw) + pad)
            y2 = min(ih, int((word["top"]  + word["height"]) * ih) + pad)
            draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0))
    out = io.BytesIO()
    fmt = "JPEG" if content_type in ("image/jpeg", "image/jpg") else "PNG"
    img.save(out, format=fmt, quality=90)
    return out.getvalue()
```

#### Change 7 — Replace `_get_presigned_url` calls with `_build_s3_url` in listing endpoints (Bug 6)

Add a new helper:
```python
def _build_s3_url(key: str) -> str:
    """Construct a direct S3 URL without an API call."""
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
```

In `list_posts` and `list_my_posts`, replace every occurrence of:
```python
image_url = _get_presigned_url(post.image_key) if post.image_key else None
```
with:
```python
image_url = _build_s3_url(post.image_key) if post.image_key else None
```

The `_get_presigned_url` helper is retained for `create_post` (single call, acceptable) and can
be removed in a follow-up if desired.

---

## Testing Strategy

### Validation Approach

Testing follows a two-phase approach for each bug:

1. **Exploratory / Bug Condition Checking** — run tests against the *unfixed* code to confirm the
   bug manifests as described and to surface concrete counterexamples.
2. **Fix + Preservation Checking** — run the same tests (and additional preservation tests) against
   the *fixed* code to verify the bug is resolved and no regressions are introduced.

---

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate each bug on unfixed code. Confirm or refute the
root cause analysis.

**Test Cases (run on UNFIXED code):**

1. **Bug 1 — Swallow check**: Mock Textract to raise `Exception("simulated failure")` inside
   `_censor_image`. Assert that the return value equals the original `image_bytes` (demonstrating
   the uncensored bytes are returned). This will pass on unfixed code, confirming the swallow.

2. **Bug 2 — Drift check**: Call `_extract_pii_values("Ahmad bin Ali owes money", "[NAME] owes money")`.
   Assert that `"owes"` is NOT in the result. This will fail on unfixed code, confirming drift.

3. **Bug 3 — Size bypass check**: Call `_censor_image` with `len(image_bytes) > 10 MB`. Assert
   that an `HTTPException(400)` is raised. This will fail on unfixed code (no guard exists).

4. **Bug 4 — Fallback gap check**: Mock Bedrock to raise an exception, then call `_censor_text`
   with `"Account 1234567890"`. Assert `"[BANK ACCOUNT]"` is in the result. Fails on unfixed code.

5. **Bug 5 — GIF corruption check**: Call `_censor_image` with a 3-frame animated GIF. Assert
   that the returned bytes can be opened as a GIF with 3 frames. Fails on unfixed code (returns PNG
   with 1 frame).

6. **Bug 6 — API call count check**: Patch `boto3.client` to count `generate_presigned_url` calls.
   Call `list_posts` returning 5 posts with images. Assert call count == 5. Passes on unfixed code,
   confirming the N-call behaviour.

**Expected Counterexamples:**
- Bug 1: `_censor_image` returns raw bytes when Textract raises.
- Bug 2: `_extract_pii_values` includes `"owes"` in the PII span.
- Bug 3: No `HTTPException` raised for oversized image.
- Bug 4: `"1234567890"` remains unredacted in fallback output.
- Bug 5: Output bytes decode as a 1-frame PNG, not a 3-frame GIF.
- Bug 6: `generate_presigned_url` called 5 times for 5 posts.

---

### Fix Checking

**Goal**: Verify that for all inputs where `isBugCondition` holds, the fixed functions produce the
expected behaviour.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := fixedFunction(input)
  ASSERT expectedBehavior(result)
END FOR
```

**Test Cases (run on FIXED code):**

1. **Bug 1**: Mock Textract to raise → assert `HTTPException` is raised (not raw bytes returned).
   Mock Layer 3 Bedrock to raise → assert function continues and returns censored bytes from
   Layers 1+2. Mock `_extract_message_from_image` Bedrock to raise → assert `""` returned and
   warning logged.

2. **Bug 2**: `_extract_pii_values("Ahmad bin Ali owes money", "[NAME] owes money")` →
   assert result == `["Ahmad bin Ali"]`.

3. **Bug 3**: Upload 11 MB image → assert HTTP 400 returned, no S3 `put_object` called.

4. **Bug 4**: Bedrock mocked to raise, text `"Passport A12345678 and account 9876543210"` →
   assert result contains `[PASSPORT]` and `[BANK ACCOUNT]`.

5. **Bug 5**: 3-frame GIF → assert output is valid GIF with 3 frames.

6. **Bug 6**: `list_posts` with 5 image posts → assert `generate_presigned_url` call count == 0,
   and each `image_url` matches the expected `https://{bucket}.s3.{region}.amazonaws.com/{key}`
   pattern.

---

### Preservation Checking

**Goal**: Verify that for all inputs where `isBugCondition` does NOT hold, the fixed functions
produce the same result as the original functions.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalFunction(input) = fixedFunction(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because it
generates many input combinations automatically and catches edge cases that manual tests miss.

**Test Cases (run on FIXED code, comparing against known-good baseline):**

1. **JPEG/PNG pipeline preservation**: Generate random small JPEG/PNG images with no text.
   Assert `_censor_image` returns bytes that can be opened as the same format.

2. **Single-word PII preservation**: Generate `(original, censored)` pairs where all PII spans
   are single words. Assert `_extract_pii_values` returns the same result as before the fix.

3. **`_censor_text` Bedrock-success preservation**: Mock Bedrock to return a known censored string.
   Assert `_censor_text` returns that string unchanged.

4. **Post listing order preservation**: Assert `list_posts` still returns posts ordered by upvote
   count desc, creation date desc, with correct `has_upvoted` flags.

5. **Post lifecycle preservation**: Assert create/delete/upvote endpoints behave identically for
   posts without images.

---

### Unit Tests

- Test `_extract_pii_values` with single-word PII, multi-word PII, consecutive multi-word PII,
  empty strings, and strings with no PII.
- Test `_censor_text` fallback branch with IC, phone, email, bank account, and passport patterns.
- Test `_build_s3_url` returns the correct URL format for a given key.
- Test size guard in `create_post` rejects images > 10 MB and accepts images <= 10 MB.
- Test `_censor_image` outer exception handler raises rather than returning raw bytes.
- Test `_censor_image` Layer 3 exception handler logs and continues (returns bytes from Layers 1+2).

### Property-Based Tests

- **Property 2 (alignment)**: Generate arbitrary sequences of words and PII spans; construct
  `(original, censored)` pairs programmatically; assert `_extract_pii_values` recovers exactly the
  PII spans with no false positives or false negatives.
- **Property 7 (pipeline preservation)**: Generate random sub-10 MB JPEG/PNG images; assert the
  fixed `_censor_image` produces output of the same MIME type and that the output is a valid image.
- **Property 4 (fallback completeness)**: Generate random strings containing bank account and
  passport patterns mixed with non-PII text; assert all patterns are redacted in the fallback path.

### Integration Tests

- Upload a real JPEG with embedded IC number text → assert stored S3 bytes are redacted.
- Upload a 3-frame animated GIF → assert stored S3 bytes are a valid GIF with 3 frames.
- Upload an 11 MB image → assert HTTP 400 and no S3 write.
- Call `list_posts` with 10 image posts → assert response time does not include S3 API latency
  and all `image_url` values are well-formed S3 URLs.
- Simulate Textract failure during post creation → assert HTTP 500 returned and no S3 write.
