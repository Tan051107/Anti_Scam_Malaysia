# Requirements Document

## Introduction

This feature replaces the mock scam-detection logic in the Anti-Scam Malaysia FastAPI backend with real AWS Bedrock API calls using the Claude 3 Sonnet model. Two existing endpoints are affected:

- `POST /api/analysis/chat` — analyses text messages and/or inline image attachments for scam indicators, with full conversation history passed to Claude per session
- `POST /api/analysis/upload` — analyses uploaded images for scam indicators

AWS credentials and the target model ID are already present in `backend/.env`. The `boto3` library is already installed. The goal is to wire up a real Bedrock client, replace the keyword-matching mock in the chat endpoint, and replace the random mock in the upload endpoint, while preserving the existing response schemas so the frontend requires no changes. The chat endpoint additionally gains multimodal input support (text and/or images) and per-session conversation history so that Claude has context from prior turns when analysing each new message.

---

## Glossary

- **Bedrock_Client**: The `boto3` `bedrock-runtime` client used to invoke Claude 3 Sonnet via AWS Bedrock.
- **Chat_Endpoint**: The `POST /api/analysis/chat` FastAPI route that accepts a text message and/or one or more inline base64-encoded images, maintains per-session conversation history, and returns a scam-risk analysis.
- **Chat_History**: The ordered list of prior `user` and `assistant` message turns associated with a given `session_id`, stored server-side and passed to Claude on every request within that session.
- **History_Store**: The server-side in-memory store (keyed by `session_id`) that holds each session's Chat_History.
- **Multimodal_Message**: A Bedrock message whose `content` array contains one or more `image` blocks (base64-encoded) alongside a `text` block, enabling Claude to reason over both text and images in a single turn.
- **Upload_Endpoint**: The `POST /api/analysis/upload` FastAPI route that accepts an image file and returns a scam-risk analysis.
- **Analysis_Response**: The structured JSON payload returned by both endpoints, containing `reply`, `risk_score`, `risk_level`, `indicators`, and `confidence`.
- **System_Prompt**: The instruction text passed to Claude in the `system` field of the Bedrock request body.
- **Vision_Payload**: The multipart Bedrock request body that includes a base64-encoded image alongside a text prompt.
- **BEDROCK_MODEL_ID**: The environment variable holding the Claude model identifier (`anthropic.claude-3-sonnet-20240229-v1:0`).
- **AWS_REGION**: The environment variable holding the AWS region (`ap-southeast-1`).
- **Simulator_Chat_Endpoint**: The `POST /api/simulator/chat` FastAPI route that drives an educational scam simulation, maintaining per-session conversation history and delegating all scammer dialogue and outcome detection to Claude via the Bedrock_Client.
- **Simulator_Reset_Endpoint**: The `POST /api/simulator/reset` FastAPI route that clears an existing simulator session and returns a fresh `session_id` so the user can start a new simulation.
- **SIMULATOR_MODEL_ID**: The model identifier used for the scam simulator (`us.anthropic.claude-haiku-4-5-20251001-v1:0`), optimised for fast, conversational responses.

---

## Requirements

### Requirement 1: Bedrock Client Initialisation

**User Story:** As a backend developer, I want a single, lazily-initialised Bedrock client shared across requests, so that the application does not create a new AWS connection on every API call.

#### Acceptance Criteria

1. THE Bedrock_Client SHALL be initialised using `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` from environment variables.
2. THE Bedrock_Client SHALL be created at most once per application lifetime (singleton / lazy init).
3. IF any required AWS credential environment variable is missing at initialisation time, THEN THE Bedrock_Client SHALL raise a `RuntimeError` with a descriptive message identifying the missing variable.
4. THE Bedrock_Client SHALL be accessible to both the Chat_Endpoint and the Upload_Endpoint via FastAPI dependency injection.

---

### Requirement 2: Text and Multimodal Analysis via Bedrock (Chat Endpoint)

**User Story:** As a user, I want to submit a text message and/or inline images to the chat endpoint and have them analysed by Claude 3 Sonnet, so that I receive an accurate, AI-powered scam-risk assessment that considers all content I provide.

#### Acceptance Criteria

1. WHEN a `POST /api/analysis/chat` request is received with a non-empty `message`, THE Chat_Endpoint SHALL invoke the Bedrock_Client with the `BEDROCK_MODEL_ID` model.
2. WHEN a `POST /api/analysis/chat` request includes one or more base64-encoded images in the `images` field, THE Chat_Endpoint SHALL construct a Multimodal_Message whose `content` array contains each image as an `image` block followed by the text message as a `text` block.
3. WHEN a `POST /api/analysis/chat` request contains no images, THE Chat_Endpoint SHALL construct a text-only message whose `content` is the plain `message` string.
4. THE Chat_Endpoint SHALL include a System_Prompt that instructs Claude to act as a Malaysian anti-scam analyst, to consider Malaysia-specific scam types (bank impersonation, PDRM/LHDN authority scams, Shopee/Lazada parcel scams, Macau scam, love scam, investment scams), and to respond in both English and Malay.
5. THE Chat_Endpoint SHALL instruct Claude to return a JSON object containing exactly the fields: `reply` (string), `risk_score` (integer 0–100), `risk_level` (one of `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `indicators` (list of strings), and `confidence` (integer 0–100).
6. THE Chat_Endpoint SHALL parse the JSON returned by Claude and map it to the existing `AnalysisChatResponse` schema without modification to that schema.
7. IF the `message` field is empty or whitespace-only AND no images are provided, THEN THE Chat_Endpoint SHALL return HTTP 400 with a descriptive error detail.
8. IF an image block's `media_type` is not one of `image/jpeg`, `image/png`, `image/gif`, or `image/webp`, THEN THE Chat_Endpoint SHALL return HTTP 400 with a descriptive error detail identifying the unsupported type.
9. IF the Bedrock_Client raises an exception during invocation, THEN THE Chat_Endpoint SHALL return HTTP 502 with an error detail that does not expose raw AWS error internals.
10. IF Claude returns a response body that cannot be parsed as valid JSON, THEN THE Chat_Endpoint SHALL return HTTP 502 with a descriptive error detail.

---

### Requirement 3: Chat History Management

**User Story:** As a user, I want Claude to remember what I said earlier in the same conversation, so that follow-up messages are analysed in context and I do not have to repeat myself.

#### Acceptance Criteria

1. THE History_Store SHALL maintain a Chat_History entry for each unique `session_id`, where each entry is an ordered list of message objects with `role` (`user` or `assistant`) and `content`.
2. WHEN a `POST /api/analysis/chat` request is received with a `session_id` that already exists in the History_Store, THE Chat_Endpoint SHALL prepend the stored Chat_History to the Bedrock messages array before invoking the Bedrock_Client.
3. WHEN a `POST /api/analysis/chat` request is received with a `session_id` that does not exist in the History_Store, THE Chat_Endpoint SHALL create a new Chat_History entry for that `session_id` before invoking the Bedrock_Client.
4. WHEN a `POST /api/analysis/chat` request is received with no `session_id`, THE Chat_Endpoint SHALL generate a new UUID as the `session_id` and create a new Chat_History entry for it.
5. AFTER a successful Bedrock invocation, THE Chat_Endpoint SHALL append the user's message (including any image blocks) and Claude's assistant reply to the Chat_History for the corresponding `session_id`.
6. AFTER a failed Bedrock invocation, THE Chat_Endpoint SHALL NOT append any new entries to the Chat_History for that `session_id`, preserving the history in its pre-request state.
7. THE History_Store SHALL limit each session's Chat_History to the 20 most recent message turns (10 user + 10 assistant); WHEN the limit is exceeded, THE History_Store SHALL discard the oldest turn pair before appending the new one.
8. WHEN a `DELETE /api/analysis/chat/history/{session_id}` request is received, THE Chat_Endpoint SHALL remove the Chat_History entry for that `session_id` from the History_Store and return HTTP 204.
9. IF a `DELETE /api/analysis/chat/history/{session_id}` request references a `session_id` that does not exist in the History_Store, THEN THE Chat_Endpoint SHALL return HTTP 404 with a descriptive error detail.
10. WHILE the application is running, THE History_Store SHALL reside in process memory; THE History_Store SHALL NOT persist Chat_History to disk or any external store.

---

### Requirement 4: Image Analysis via Bedrock (Upload Endpoint)

**User Story:** As a user, I want an uploaded screenshot or image to be analysed by Claude 3 Sonnet's vision capability, so that I receive an AI-powered assessment of whether the image contains scam content.

#### Acceptance Criteria

1. WHEN a `POST /api/analysis/upload` request is received with a supported image file, THE Upload_Endpoint SHALL read the image bytes and encode them as base64.
2. THE Upload_Endpoint SHALL construct a Vision_Payload containing the base64-encoded image with its `media_type` derived from `file.content_type`, and a text prompt instructing Claude to analyse the image for scam indicators in the Malaysian context.
3. THE Upload_Endpoint SHALL invoke the Bedrock_Client with the Vision_Payload using the `BEDROCK_MODEL_ID` model.
4. THE Upload_Endpoint SHALL instruct Claude to return a JSON object containing exactly the fields: `reply` (string), `risk_score` (integer 0–100), `risk_level` (one of `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), `indicators` (list of strings), and `confidence` (integer 0–100).
5. THE Upload_Endpoint SHALL parse the JSON returned by Claude and map it to the existing `AnalysisUploadResponse` schema without modification to that schema.
6. IF the uploaded file's `content_type` is not one of `image/jpeg`, `image/png`, `image/gif`, or `image/webp`, THEN THE Upload_Endpoint SHALL return HTTP 400 with a descriptive error detail.
7. IF the Bedrock_Client raises an exception during invocation, THEN THE Upload_Endpoint SHALL return HTTP 502 with an error detail that does not expose raw AWS error internals.
8. IF Claude returns a response body that cannot be parsed as valid JSON, THEN THE Upload_Endpoint SHALL return HTTP 502 with a descriptive error detail.

---

### Requirement 5: Response Schema Compatibility

**User Story:** As a frontend developer, I want the API response structure to remain unchanged after the Bedrock integration, so that no frontend code needs to be modified.

#### Acceptance Criteria

1. THE Chat_Endpoint SHALL return responses that conform to the existing `AnalysisChatResponse` Pydantic schema (`reply`, `risk_score`, `risk_level`, `indicators`, `confidence`, `session_id`).
2. THE Upload_Endpoint SHALL return responses that conform to the existing `AnalysisUploadResponse` Pydantic schema (`reply`, `risk_score`, `risk_level`, `indicators`, `confidence`, `filename`).
3. THE Chat_Endpoint SHALL preserve the `session_id` field: WHEN a `session_id` is provided in the request, THE Chat_Endpoint SHALL echo it in the response; WHEN no `session_id` is provided, THE Chat_Endpoint SHALL generate and return a new UUID.

---

### Requirement 6: Configuration and Environment

**User Story:** As a developer, I want all AWS configuration to be read from environment variables, so that credentials are never hard-coded and the deployment target can be changed without code changes.

#### Acceptance Criteria

1. THE Bedrock_Client SHALL read `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, and `BEDROCK_MODEL_ID` exclusively from environment variables loaded via `python-dotenv`.
2. THE Chat_Endpoint and THE Upload_Endpoint SHALL read `BEDROCK_MODEL_ID` from the environment at call time, not at import time, so that the value can be overridden between test runs without restarting the process.
3. WHERE `AWS_REGION` is not set, THE Bedrock_Client SHALL default to `ap-southeast-1`.

---

### Requirement 7: Scam Simulator via Bedrock

**User Story:** As a user, I want to engage in a realistic scam simulation powered by Claude, so that I can learn to recognise and resist common Malaysian scam tactics in a safe, educational environment.

#### Acceptance Criteria

1. WHEN a `POST /api/simulator/chat` request is received with a `session_id` that does not exist in the simulator History_Store, THE Simulator_Chat_Endpoint SHALL select one of the four hardcoded scam scenarios (Shopee Parcel Delivery Scam, LHDN Tax Authority Impersonation, Bank Officer Impersonation, Love Scam) and begin the simulation by invoking the Bedrock_Client with the `SIMULATOR_MODEL_ID` (`us.anthropic.claude-haiku-4-5-20251001-v1:0`).

2. WHEN a `POST /api/simulator/chat` request is received with a `session_id` that does not exist in the simulator History_Store, THE Simulator_Chat_Endpoint SHALL generate a new UUID as the `session_id` and create a new simulator Chat_History entry for it.

3. WHEN a `POST /api/simulator/chat` request is received with a `session_id` that already exists in the simulator History_Store, THE Simulator_Chat_Endpoint SHALL prepend the stored simulator Chat_History to the Bedrock messages array before invoking the Bedrock_Client.

4. THE Simulator_Chat_Endpoint SHALL invoke the Bedrock_Client with a System_Prompt that instructs Claude to act as a realistic scammer conducting an educational simulation, to build trust gradually, to introduce urgency and emotional triggers progressively, to guide the user toward becoming a victim, to NOT reveal the simulation until the ending condition is met, and to maintain realism and consistency throughout.

5. THE Simulator_Chat_Endpoint SHALL instruct Claude to return a JSON object containing exactly the fields: `reply` (string), `scam_ended` (boolean), `user_caught_scam` (boolean), and `report` (object or null — present only when `scam_ended` is true).

6. WHEN Claude returns a response with `scam_ended` set to true, THE Simulator_Chat_Endpoint SHALL include a `ScamReport` object in the response containing: `scam_type` (string), `red_flags` (list of strings), `summary` (string), `outcome` (string — either `"SUCCESS — You identified the scam!"` or `"FAILED — You fell for the scam"`), and `advice` (string).

7. WHEN Claude returns a response with `scam_ended` set to false, THE Simulator_Chat_Endpoint SHALL return `report` as null.

8. THE Simulator_Chat_Endpoint SHALL parse the JSON returned by Claude and map it to the existing `SimulatorChatResponse` Pydantic schema without modification to that schema.

9. AFTER a successful Bedrock invocation, THE Simulator_Chat_Endpoint SHALL append the user's message and Claude's assistant reply to the simulator Chat_History for the corresponding `session_id`.

10. AFTER a failed Bedrock invocation, THE Simulator_Chat_Endpoint SHALL NOT append any new entries to the simulator Chat_History for that `session_id`, preserving the history in its pre-request state.

11. THE simulator History_Store SHALL limit each session's Chat_History to the 20 most recent message turns (10 user + 10 assistant); WHEN the limit is exceeded, THE simulator History_Store SHALL discard the oldest turn pair before appending the new one.

12. WHEN a `POST /api/simulator/reset` request is received, THE Simulator_Reset_Endpoint SHALL clear the simulator Chat_History for the provided `session_id` (if it exists) and return a new UUID as the `session_id` along with a confirmation message conforming to the `SimulatorResetResponse` schema.

13. WHEN a `POST /api/simulator/reset` request is received with no `session_id`, THE Simulator_Reset_Endpoint SHALL generate and return a new UUID as the `session_id` without modifying any existing sessions.

14. IF the Bedrock_Client raises an exception during a simulator invocation, THEN THE Simulator_Chat_Endpoint SHALL return HTTP 502 with an error detail that does not expose raw AWS error internals.

15. IF Claude returns a response body that cannot be parsed as valid JSON during a simulator invocation, THEN THE Simulator_Chat_Endpoint SHALL return HTTP 502 with a descriptive error detail.

16. WHILE a simulation session has `scam_ended` set to true in the simulator History_Store, THE Simulator_Chat_Endpoint SHALL return a message indicating the simulation has ended and prompt the user to reset, without invoking the Bedrock_Client.
