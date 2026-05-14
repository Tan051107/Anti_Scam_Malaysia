# Bugfix Requirements Document

## Introduction

The PII censorship pipeline in `backend/routers/community.py` contains six defects that collectively
create privacy risks, data corruption, and performance problems. The most critical issues are silent
exception swallowing (which can cause raw, uncensored images to be stored in S3) and word-alignment
drift in the PII extraction diff (which causes false-positive redactions). Additional issues include
missing image-size validation before AWS service calls, an incomplete fallback regex in `_censor_text`,
broken GIF handling, and per-post presigned URL generation on every `list_posts` call.

---

## Bug Analysis

### Current Behavior (Defect)

**Bug 1 — Silent exception swallowing (privacy risk)**

1.1 WHEN Textract or Bedrock raises any exception inside `_censor_image` THEN the system silently
    returns the original uncensored `image_bytes` with no log entry and no error propagated to the
    caller, causing the raw image to be uploaded to S3.

1.2 WHEN `_extract_message_from_image` raises any exception THEN the system silently returns an
    empty string with no log entry, causing the image text extraction step to fail invisibly.

1.3 WHEN the Bedrock call inside the Layer 3 block of `_censor_image` raises any exception THEN
    the system silently skips the entire Bedrock classification step with no log entry, potentially
    leaving PII words unredacted.

**Bug 2 — `_extract_pii_values` word-alignment drift**

1.4 WHEN a PII value spans multiple words (e.g. "Ahmad bin Ali" is replaced by the single token
    `[NAME]`) THEN the word-by-word diff in `_extract_pii_values` drifts, causing subsequent
    non-PII words to be consumed into the PII span and misidentified as PII.

1.5 WHEN the censored text contains consecutive multi-word PII replacements THEN the alignment
    drift compounds across each replacement, causing an increasing number of non-PII words to be
    incorrectly added to `pii_values`.

**Bug 3 — No image size validation before Textract/Bedrock**

1.6 WHEN an uploaded image exceeds Textract's 10 MB document limit THEN the system sends the
    oversized payload to Textract, which raises an exception that is silently swallowed, causing
    the raw uncensored image to be stored in S3.

1.7 WHEN an uploaded image is very large (e.g. 20 MB) THEN the system sends the full payload to
    Bedrock as a base64-encoded body with no size check, risking request rejection or timeout.

**Bug 4 — `_censor_text` fallback regex is incomplete**

1.8 WHEN Bedrock is unavailable and `_censor_text` falls back to regex THEN the system only
    redacts IC numbers, phone numbers, and email addresses, leaving names, addresses, bank account
    numbers, and passport numbers unredacted in the stored `original_message` field.

**Bug 5 — GIF handling is broken**

1.9 WHEN an uploaded image has content type `image/gif` THEN the save logic in `_censor_image`
    falls through to the PNG branch, discarding all animation frames except the first and saving
    the file as PNG regardless of the original format.

1.10 WHEN an animated GIF is uploaded THEN the system stores a static single-frame PNG under the
     original `.gif` extension key in S3, corrupting the file.

**Bug 6 — Presigned URL generation is inefficient**

1.11 WHEN `list_posts` is called with a page of N posts that have images THEN the system makes N
     individual S3 `generate_presigned_url` API calls in the hot path of the request, one per post.

1.12 WHEN `list_my_posts` is called THEN the system similarly makes one S3 API call per post image,
     adding latency proportional to the number of posts returned.

---

### Expected Behavior (Correct)

**Bug 1 — Silent exception swallowing**

2.1 WHEN Textract or Bedrock raises any exception inside `_censor_image` THEN the system SHALL log
    the exception at ERROR level with full traceback and SHALL raise an error that prevents the
    uncensored image from being uploaded to S3.

2.2 WHEN `_extract_message_from_image` raises any exception THEN the system SHALL log the exception
    at WARNING level and SHALL return an empty string so the caller can handle the degraded state
    explicitly.

2.3 WHEN the Bedrock call inside the Layer 3 block of `_censor_image` raises any exception THEN
    the system SHALL log the exception at WARNING level and SHALL continue with only the words
    already flagged by Layers 1 and 2, never silently dropping the entire classification step.

**Bug 2 — `_extract_pii_values` word-alignment drift**

2.4 WHEN a PII value spans multiple words and Bedrock replaces them with a single placeholder token
    THEN `_extract_pii_values` SHALL correctly consume all original words that map to that
    placeholder without drifting into adjacent non-PII words.

2.5 WHEN the censored text contains consecutive multi-word PII replacements THEN
    `_extract_pii_values` SHALL return exactly the original word spans for each replacement with
    no false-positive non-PII words included.

**Bug 3 — No image size validation**

2.6 WHEN an uploaded image exceeds 10 MB THEN the system SHALL reject the upload before calling
    Textract and SHALL return an HTTP 400 response with a clear message indicating the size limit.

2.7 WHEN an uploaded image exceeds the configured size limit THEN the system SHALL NOT call
    Textract or Bedrock and SHALL NOT store any image bytes in S3.

**Bug 4 — `_censor_text` fallback regex**

2.8 WHEN Bedrock is unavailable and `_censor_text` falls back to regex THEN the system SHALL also
    redact bank account numbers (sequences of 10–16 digits) and passport numbers (letter followed
    by 7–9 digits) in addition to IC numbers, phone numbers, and email addresses.

**Bug 5 — GIF handling**

2.9 WHEN an uploaded image has content type `image/gif` THEN the system SHALL process it as a GIF,
    preserve all animation frames where possible, and save the output file in GIF format.

2.10 WHEN a GIF image is uploaded THEN the system SHALL store the processed file under the correct
     `.gif` extension key in S3 with content type `image/gif`.

**Bug 6 — Presigned URL generation**

2.11 WHEN `list_posts` or `list_my_posts` is called THEN the system SHALL generate presigned URLs
     without making one S3 API call per post, using local URL construction instead of
     `generate_presigned_url` for each individual post image.

2.12 WHEN presigned URLs are generated for a page of posts THEN the total number of S3 API calls
     SHALL NOT scale linearly with the number of posts on the page.

---

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a JPEG or PNG image is uploaded and Textract and Bedrock both succeed THEN the system
    SHALL CONTINUE TO run all four censorship layers and store the redacted image in S3.

3.2 WHEN a WEBP image is uploaded THEN the system SHALL CONTINUE TO process it through the
    censorship pipeline and store the result in S3.

3.3 WHEN `_censor_text` is called and Bedrock succeeds THEN the system SHALL CONTINUE TO return
    the Bedrock-censored text with all seven PII categories replaced.

3.4 WHEN Textract detects form key-value pairs whose keys match `PII_FIELD_KEYS` THEN the system
    SHALL CONTINUE TO automatically flag the corresponding value word IDs for redaction in Layer 1.

3.5 WHEN `_extract_pii_values` is called with a censored text where all PII values are single
    words THEN the system SHALL CONTINUE TO return the correct single-word PII spans with no
    regressions.

3.6 WHEN an image contains no text detectable by Textract THEN the system SHALL CONTINUE TO return
    the image bytes (after censorship attempt) without error.

3.7 WHEN a post is created without an image THEN the system SHALL CONTINUE TO store the post with
    no image key and return `image_url: null`.

3.8 WHEN `list_posts` is called THEN the system SHALL CONTINUE TO return posts ordered by upvote
    count descending then by creation date descending, with correct upvote counts and `has_upvoted`
    flags.

3.9 WHEN a post is deleted THEN the system SHALL CONTINUE TO attempt to remove the associated S3
    object and delete the database record.

3.10 WHEN an image type not in `ALLOWED_IMAGE_TYPES` is uploaded THEN the system SHALL CONTINUE TO
     reject the upload with HTTP 400.
