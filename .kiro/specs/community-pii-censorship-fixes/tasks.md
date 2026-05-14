# Implementation Plan

- [x] 1. Write bug condition exploration tests (BEFORE implementing any fix)
  - **Property 1: Bug Condition** - Six PII Censorship Defects
  - **CRITICAL**: These tests MUST FAIL on unfixed code — failure confirms each bug exists
  - **DO NOT attempt to fix the tests or the code when they fail**
  - **NOTE**: These tests encode the expected behavior — they will validate the fixes when they pass after implementation
  - **GOAL**: Surface counterexamples that demonstrate each of the six bugs on unfixed code
  - **Scoped PBT Approach**: For deterministic bugs, scope each property to the concrete failing case(s) to ensure reproducibility
  - Create `backend/tests/test_community_bugs.py` with the following six exploration tests:
    - **Bug 1 — Silent swallow**: Mock Textract to raise `Exception("simulated failure")` inside `_censor_image`; assert the return value equals the original `image_bytes` (demonstrates uncensored bytes are returned). Run on unfixed code — **EXPECTED: PASSES** (confirms the swallow exists, i.e. raw bytes are returned instead of raising).
    - **Bug 2 — Alignment drift**: Call `_extract_pii_values("Ahmad bin Ali owes money", "[NAME] owes money")`; assert `"owes"` IS in the result (demonstrates drift). Run on unfixed code — **EXPECTED: PASSES** (confirms drift, i.e. "owes" is incorrectly included).
    - **Bug 3 — No size guard**: Call `create_post` with `len(image_bytes) > 10 MB`; assert NO `HTTPException(400)` is raised before Textract is called. Run on unfixed code — **EXPECTED: PASSES** (confirms no guard exists).
    - **Bug 4 — Fallback gap**: Mock Bedrock to raise, call `_censor_text("Account 1234567890")`; assert `"[BANK ACCOUNT]"` is NOT in the result. Run on unfixed code — **EXPECTED: PASSES** (confirms pattern is missing from fallback).
    - **Bug 5 — GIF corruption**: Call `_censor_image` with a 3-frame animated GIF; assert the returned bytes decode as a 1-frame PNG (not a 3-frame GIF). Run on unfixed code — **EXPECTED: PASSES** (confirms GIF is corrupted to PNG).
    - **Bug 6 — N API calls**: Patch `boto3.client` to count `generate_presigned_url` calls; call `list_posts` returning 5 posts with images; assert call count == 5. Run on unfixed code — **EXPECTED: PASSES** (confirms N-call behaviour).
  - Document all counterexamples found to understand root causes before implementing fixes
  - Mark task complete when all six tests are written, run, and their (expected) outcomes are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12_

- [x] 2. Write preservation property tests (BEFORE implementing any fix)
  - **Property 2: Preservation** - Existing Censorship Pipeline and Post Lifecycle Unchanged
  - **IMPORTANT**: Follow observation-first methodology — run UNFIXED code with non-buggy inputs, observe outputs, then write tests that assert those observed outputs
  - Observe on UNFIXED code (non-bug-condition inputs):
    - `_censor_image` with a small valid JPEG/PNG/WEBP returns bytes of the same MIME type
    - `_extract_pii_values` with single-word PII spans returns the correct single-word values
    - `_censor_text` when Bedrock succeeds returns the Bedrock-censored string unchanged
    - `list_posts` returns posts ordered by upvote count desc, then creation date desc, with correct `has_upvoted` flags
    - Post creation without an image stores `image_key = None` and returns `image_url: null`
    - Post deletion removes the S3 object and database record
    - Uploads of disallowed MIME types are rejected with HTTP 400
  - Write property-based tests in `backend/tests/test_community_preservation.py` capturing these observed behaviors:
    - **Preservation P2a**: For all sub-10 MB JPEG/PNG/WEBP images (mocked Textract/Bedrock success), `_censor_image` returns bytes that open as the same MIME type
    - **Preservation P2b**: For all `(original, censored)` pairs where every PII span is a single word, `_extract_pii_values` returns exactly those single words with no extras
    - **Preservation P2c**: `_censor_text` with mocked Bedrock success returns the mocked censored string verbatim
    - **Preservation P2d**: `list_posts` ordering and flag correctness for posts without images
    - **Preservation P2e**: Post lifecycle (create without image, delete, upvote) produces identical behavior
  - Verify ALL preservation tests PASS on UNFIXED code before proceeding
  - **EXPECTED OUTCOME**: All preservation tests PASS (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and confirmed passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

- [x] 3. Fix Bug 1 — Replace silent exception swallows with logged handlers

  - [x] 3.1 Add `logging` import and `logger` at module level in `backend/routers/community.py`
    - Add `import logging` alongside existing imports
    - Add `logger = logging.getLogger(__name__)` after imports
    - _Bug_Condition: isBugCondition(ExceptionEvent(site)) where site IN {_censor_image_outer, _extract_message_from_image, _censor_image_layer3}_
    - _Expected_Behavior: Exception is logged and either propagated (outer handler) or a safe degraded value is returned (other two sites); uncensored bytes are never returned_
    - _Preservation: All non-exception code paths in _censor_image and _extract_message_from_image are unaffected_
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.2 Fix `_extract_message_from_image` bare except
    - Replace `except Exception: return ""` with `except Exception as exc: logger.warning("_extract_message_from_image failed: %s", exc, exc_info=True); return ""`
    - _Requirements: 2.2_

  - [x] 3.3 Fix `_censor_image` outer bare except
    - Replace `except Exception: return image_bytes` with `except Exception as exc: logger.error("_censor_image pipeline failed — refusing to return uncensored bytes: %s", exc, exc_info=True); raise`
    - Update `create_post` to catch the re-raised exception and return `HTTPException(status_code=500)` rather than storing raw bytes
    - _Requirements: 2.1_

  - [x] 3.4 Fix `_censor_image` Layer 3 inner bare except
    - Replace `except Exception: pass` with `except Exception as exc: logger.warning("_censor_image Layer 3 Bedrock call failed — continuing with Layers 1+2 only: %s", exc, exc_info=True)`
    - _Requirements: 2.3_

- [x] 4. Fix Bug 2 — Replace word-walk with `difflib.SequenceMatcher` in `_extract_pii_values`

  - [x] 4.1 Add `import difflib` to module imports
    - _Bug_Condition: isBugCondition(TextDiff(original, censored)) where a placeholder maps to multiple original words_
    - _Expected_Behavior: _extract_pii_values returns exactly the original word spans for each placeholder with no false-positive non-PII words_
    - _Preservation: Single-word PII spans continue to be returned correctly (Requirement 3.5)_
    - _Requirements: 2.4, 2.5_

  - [x] 4.2 Replace the `i, j` word-walk loop in `_extract_pii_values` with `SequenceMatcher` opcodes
    - Compile `placeholder_re` matching all seven placeholder tokens
    - Use `difflib.SequenceMatcher(None, orig_words, cens_words, autojunk=False).get_opcodes()`
    - For each `replace` opcode where the entire censored slice consists of placeholder tokens, append `" ".join(orig_words[i1:i2])` to `pii_values`
    - Return `pii_values`
    - _Requirements: 2.4, 2.5_

- [x] 5. Fix Bug 3 — Add image size guard in `create_post` before any AWS call

  - [x] 5.1 Add `MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024` constant at module level
    - Place alongside existing module-level constants (`S3_BUCKET`, `AWS_REGION`, etc.)
    - _Bug_Condition: isBugCondition(ImageUpload(bytes, mime)) where len(bytes) > MAX_IMAGE_SIZE_BYTES_
    - _Expected_Behavior: HTTP 400 returned before any Textract or Bedrock call; no bytes written to S3_
    - _Preservation: Images <= 10 MB continue through the full pipeline unchanged_
    - _Requirements: 2.6, 2.7_

  - [x] 5.2 Add size check in `create_post` immediately after `image_bytes = await image.read()`
    - Add: `if len(image_bytes) > MAX_IMAGE_SIZE_BYTES: raise HTTPException(status_code=400, detail=f"Image exceeds the {MAX_IMAGE_SIZE_BYTES // (1024*1024)} MB size limit.")`
    - Ensure this check runs before `_extract_message_from_image`, `_censor_image`, and `_upload_to_s3`
    - _Requirements: 2.6, 2.7_

- [x] 6. Fix Bug 4 — Extend fallback regex in `_censor_text` to cover bank accounts and passports

  - [x] 6.1 Add bank account and passport patterns to the `except` branch of `_censor_text`
    - After the existing three `re.sub` calls, add:
      - `text = re.sub(r'\b\d{10,16}\b', '[BANK ACCOUNT]', text)`
      - `text = re.sub(r'\b[A-Za-z]\d{7,9}\b', '[PASSPORT]', text)`
    - _Bug_Condition: isBugCondition(FallbackTextCensor(text)) where (ContainsBankAccount(text) OR ContainsPassport(text)) AND BedrockUnavailable()_
    - _Expected_Behavior: [BANK ACCOUNT] and [PASSPORT] placeholders appear in the fallback output for matching patterns_
    - _Preservation: IC, phone, and email patterns continue to be redacted; Bedrock-success path is unaffected (Requirement 3.3)_
    - _Requirements: 2.8_

- [x] 7. Fix Bug 5 — Add explicit GIF frame-iteration branch in `_censor_image`

  - [x] 7.1 Add GIF branch before the existing Pillow save block in `_censor_image`
    - Add `if content_type == "image/gif":` branch that:
      - Opens the GIF with `Image.open(io.BytesIO(image_bytes))`
      - Iterates all frames via `src.seek(src.tell() + 1)` until `EOFError`
      - For each frame: converts to RGBA, draws redaction boxes using the same `words`/`pii_set`/`kv_value_ids`/`regex_flagged_ids` logic, converts to palette mode `"P"` with `Image.ADAPTIVE`
      - Collects per-frame durations from `src.info.get("duration", 100)`
      - Saves with `frames[0].save(out, format="GIF", save_all=True, append_images=frames[1:], loop=src.info.get("loop", 0), duration=durations, disposal=2)`
    - Wrap existing non-GIF Pillow block in `else:` branch (JPEG/PNG/WEBP unchanged)
    - _Bug_Condition: isBugCondition(ImageUpload(bytes, mime)) where mime == "image/gif"_
    - _Expected_Behavior: Output bytes are a valid GIF preserving all frames and animation metadata_
    - _Preservation: JPEG, PNG, and WEBP images continue through the existing Pillow branch unchanged (Requirements 3.1, 3.2)_
    - _Requirements: 2.9, 2.10_

- [x] 8. Fix Bug 6 — Replace per-post `_get_presigned_url` calls with local `_build_s3_url` in listing endpoints

  - [x] 8.1 Add `_build_s3_url` helper function in the S3 helpers section
    - Add: `def _build_s3_url(key: str) -> str: return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"`
    - Place alongside `_get_presigned_url` in the S3 helpers section
    - _Bug_Condition: isBugCondition(ListRequest(posts)) where len(posts_with_images) > 0_
    - _Expected_Behavior: Number of S3 API calls is O(1) (zero) regardless of N posts; each image_url matches the expected https://{bucket}.s3.{region}.amazonaws.com/{key} pattern_
    - _Preservation: `list_posts` continues to return correct post data, ordering, upvote counts, and has_upvoted flags (Requirement 3.8); `create_post` presigned URL call is unaffected_
    - _Requirements: 2.11, 2.12_

  - [x] 8.2 Replace `_get_presigned_url` with `_build_s3_url` in `list_posts`
    - Change `image_url = _get_presigned_url(post.image_key) if post.image_key else None` to `image_url = _build_s3_url(post.image_key) if post.image_key else None`
    - _Requirements: 2.11, 2.12_

  - [x] 8.3 Replace `_get_presigned_url` with `_build_s3_url` in `list_my_posts`
    - Change `image_url = _get_presigned_url(post.image_key) if post.image_key else None` to `image_url = _build_s3_url(post.image_key) if post.image_key else None`
    - _Requirements: 2.11, 2.12_

- [x] 9. Verify bug condition exploration tests now pass (after all fixes)

  - [x] 9.1 Re-run the exploration tests from Task 1 on the FIXED code
    - **Property 1: Expected Behavior** - Six PII Censorship Defects Resolved
    - **IMPORTANT**: Re-run the SAME tests from Task 1 — do NOT write new tests
    - The tests from Task 1 encode the expected behavior; when they pass, the bugs are fixed
    - Bug 1: `_censor_image` raises (not returns raw bytes) when Textract raises
    - Bug 2: `_extract_pii_values("Ahmad bin Ali owes money", "[NAME] owes money")` returns `["Ahmad bin Ali"]` and does NOT include `"owes"`
    - Bug 3: `create_post` with >10 MB image raises `HTTPException(400)` before any AWS call
    - Bug 4: Fallback `_censor_text("Account 1234567890")` returns text containing `[BANK ACCOUNT]`
    - Bug 5: `_censor_image` with 3-frame GIF returns valid GIF bytes with 3 frames
    - Bug 6: `list_posts` with 5 image posts makes 0 `generate_presigned_url` calls
    - **EXPECTED OUTCOME**: All six exploration tests PASS (confirms all bugs are fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12_

  - [x] 9.2 Verify preservation tests still pass on the FIXED code
    - **Property 2: Preservation** - Existing Censorship Pipeline and Post Lifecycle Unchanged
    - **IMPORTANT**: Re-run the SAME tests from Task 2 — do NOT write new tests
    - **EXPECTED OUTCOME**: All preservation tests PASS (confirms no regressions)
    - Confirm JPEG/PNG/WEBP pipeline, single-word PII extraction, Bedrock-success text censorship, post ordering, and post lifecycle all behave identically to the unfixed baseline
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

- [x] 10. Checkpoint — Ensure all tests pass
  - Run the full test suite: `pytest backend/tests/test_community_bugs.py backend/tests/test_community_preservation.py -v`
  - Ensure all exploration tests (Task 1) now PASS on fixed code
  - Ensure all preservation tests (Task 2) still PASS on fixed code
  - Confirm no other existing tests were broken by the changes
  - Ask the user if any questions arise before closing the spec
