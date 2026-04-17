# Software Engineering Plan for LearnPilot

## 1. Project Title

**LearnPilot: A Conversation-Centric Personal Assistant-as-a-Service for Academic Workflows**

---

## 2. Assignment Alignment

LearnPilot is designed for **Topic 2: Personal Assistant-as-a-Service** in `Project 2026.pdf`.

The assignment asks for a software platform where personal assistant capabilities are decomposed into independent services that communicate through well-defined RESTful APIs, and where novel API usage is demonstrated through AI-agent-style workflows.

This revised plan keeps the existing educational focus, but reframes the product from a one-shot document analyzer into a **session-based personal assistant platform**. In the target system, the assistant will:

1. converse with a user in a dedicated chat workspace,
2. accept uploaded documents during conversation,
3. trigger asynchronous document analysis tasks,
4. create and manage calendar events,
5. manage notes as session artifacts,
6. export notes through document-conversion tools,
7. manage selected cloud files through Google Drive,
8. expose all major capabilities through modular backend services and REST endpoints.

This makes the project more clearly aligned with the assignment than a document-only dashboard workflow.

---

## 3. Current Baseline and Observed Gaps

### 3.1 Existing Capabilities Already Implemented

The repository already contains a functional MVP foundation:

* FastAPI backend with authentication and per-user credentials.
* PDF upload and text extraction with PyMuPDF.
* LLM-based intent classification and structured note generation.
* Candidate calendar-event extraction and Google Calendar write-back.
* Google OAuth and Google Drive upload of original PDFs.
* Next.js frontend with:
  * dashboard,
  * settings page,
  * document detail page,
  * note editing form,
  * candidate event review UI.
* SQLite persistence and Alembic migrations.

### 3.2 Concrete Existing Locations

The following code is already useful and should be reused rather than replaced:

* `backend/app/services/document_service.py`
  * PDF validation, storage, and text extraction.
* `backend/app/services/orchestrator_service.py`
  * current one-shot analysis orchestration.
* `backend/app/services/note_service.py`
  * structured note generation and persistence.
* `backend/app/services/calendar_service.py`
  * event extraction and Google Calendar creation.
* `backend/app/services/drive_service.py`
  * Google Drive archive upload.
* `backend/app/services/credential_service.py`
  * LLM key storage and Google OAuth token handling.
* `frontend/src/app/app/page.tsx`
  * dashboard page.
* `frontend/src/app/app/settings/page.tsx`
  * settings page.
* `frontend/src/app/app/documents/[documentId]/page.tsx`
  * current document-centric workflow.

### 3.3 What Is Missing for the Requested Direction

The current implementation is **not yet a multi-turn assistant platform**. Important gaps are:

* no chat page parallel to Dashboard and Settings,
* no conversation/session data model,
* no message persistence,
* no markdown conversation rendering,
* no tool-calling UI or approval modal,
* no asynchronous job system,
* no streaming or event-based progress updates,
* notes are currently tied to a document, not to a session,
* notes are editable directly by the user, which conflicts with the revised requirement,
* no note diff/patch workflow controlled by the assistant,
* no Pandoc integration,
* no general Google Drive management workflow beyond archive upload,
* no generic tool runtime for assistant actions,
* no date-normalization policy for missing years,
* no dedicated assistant orchestration around uploads, tools, approvals, and resumable runs.

### 3.4 Key Architectural Reframing

The current MVP is **document-centric**.

The requested target system should be **conversation-centric**:

* users interact with a session first,
* documents are attachments to a session,
* notes belong to a session rather than a document,
* tool calls and analysis tasks are part of the conversation history,
* calendar and Drive actions become assistant tools rather than isolated buttons only.

---

## 4. Refined Product Vision

LearnPilot will become a student-focused assistant workspace where a user can open a conversation, upload study documents, ask questions, request summaries or exports, approve external actions, and review assistant-generated notes beside the conversation.

The assistant should behave like a controlled SaaS agent:

* conversational like mainstream LLM applications,
* tool-augmented,
* auditable,
* user-approved for external side effects,
* persistent at the user/session level,
* modular at the service level.

This preserves the educational domain while satisfying the Personal Assistant-as-a-Service principle.

---

## 5. Scope Definition

### 5.1 In-Scope for the Revised System

The revised system will support:

* user registration, login, and profile management,
* per-user LLM credential storage,
* Google OAuth connection and token storage,
* chat sessions parallel to Dashboard and Settings,
* markdown-rendered assistant and system messages,
* file upload from the conversation page into the user workspace,
* association of uploaded documents with the current session,
* asynchronous document-analysis jobs,
* assistant-triggered note creation in markdown,
* notes associated with sessions rather than documents,
* non-editable note viewing in the UI,
* assistant-driven note modifications through a diff/patch tool,
* candidate date-event extraction from chat or document-analysis context,
* user-approved Google Calendar event creation,
* assistant-triggered Pandoc export of notes to `docx` or `pptx`,
* assistant-triggered Google Drive file operations within the approved app scope,
* persistent storage of messages, tool calls, approvals, and generated artifacts,
* auditability of assistant decisions and side effects.

### 5.2 Out-of-Scope for This Revision

The following will remain out of scope unless later expanded:

* OCR for scanned PDFs,
* arbitrary multi-user shared conversations,
* voice input/output,
* background autonomous agents acting without user initiation,
* unrestricted Google Drive browsing across the entire user account by default,
* arbitrary third-party tool ecosystems beyond the selected set,
* complex retrieval-augmented generation across large document corpora,
* long-term personal habit modeling across months of behavioral data.

---

## 6. Engineering Interpretation of the Requested Features

This section translates the request into precise, buildable requirements.

### 6.1 Chat Page

Add a new protected route parallel to Dashboard and Settings:

* `/app/chat`
* optional session routes such as `/app/chat/[conversationId]`

The page should provide:

* conversation list or session switcher,
* message timeline,
* composer input,
* file upload control,
* tool approval modal,
* side panel for session notes.

### 6.2 Markdown Rendering

Assistant messages and note content should be rendered as markdown.

Recommended frontend tooling:

* `react-markdown`
* `remark-gfm`
* `rehype-sanitize`

Optional enhancement:

* `rehype-highlight` for fenced code blocks.

This should be applied to:

* assistant chat messages,
* system messages where suitable,
* note display panel,
* exported note previews if added later.

### 6.3 User-Level Persistence

The system must persist, per user:

* conversations,
* messages,
* message attachments,
* tool call events,
* approval decisions,
* assistant runs,
* session notes,
* exports,
* Drive operations,
* calendar records.

This persistence must be idempotent where repeated retries are possible.

### 6.4 Tool Approval

Any tool with side effects or external visibility should require approval before execution.

At minimum, approval should be required for:

* Google Calendar event creation,
* Google Drive file upload/move/download operations,
* Pandoc export that materializes output files,
* note patch operations if they overwrite existing note content.

Safe read-only operations may be auto-approved later, but the first implementation should favor explicit user approval for clarity.

### 6.5 Chat Upload

A user can upload a document directly within a conversation.

The upload should:

1. store the file in the user workspace,
2. create or reuse a document record,
3. associate the document with the current session,
4. surface an attachment chip or system message in the conversation.

### 6.6 Asynchronous Document Analysis

Document analysis should become an asynchronous job rather than a synchronous request/response action.

The default assistant job for a document should produce:

* a summary,
* key points,
* optionally action items,
* optionally a session note in markdown.

Users may also issue custom analysis instructions in chat, for example:

* “turn this into revision notes,”
* “extract exam dates only,”
* “compare this brief with my notes.”

The output note must be associated with the session, not the document.

### 6.7 Date Event Handling

When the assistant detects a date event in chat or analysis:

* it should produce a structured candidate event,
* if the year is missing, the current year should be used by default,
* the user should approve before Google Calendar creation,
* the created event should be stored with source provenance.

### 6.8 Note Display and Editing Policy

Notes should be shown in a side panel adjacent to the conversation.

Important policy decision:

* the user does **not** directly edit the note text in the UI,
* the assistant updates notes through an explicit note-diff tool,
* note revisions must be tracked.

This is a deliberate change from the current document-level note editor.

### 6.9 Pandoc Export

The assistant should be able to export session notes from markdown to:

* `docx`
* `pptx`

This requires:

* a Pandoc binary available on the deployment host,
* a controlled export directory,
* an export artifact record in the database,
* optional reference templates for brand-consistent output.

### 6.10 Google Drive File Management

The assistant should be able to manage files through Google Drive within an explicitly defined scope.

For the first implementation, the recommended scope is:

* app-created or app-managed files inside a LearnPilot-owned Drive folder.

Supported operations should include:

* upload exported artifacts,
* upload original documents,
* move files between assistant-managed folders,
* retrieve file metadata,
* generate downloadable references where allowed.

This is more feasible and safer than unrestricted full-account Drive management.

---

## 7. Proposed High-Level Architecture

LearnPilot should evolve into a four-part architecture:

1. **Frontend Application**
2. **Backend API**
3. **Assistant Worker / Job Runtime**
4. **Persistence and External Integrations**

### 7.1 Frontend Layer

Responsibilities:

* authentication UX,
* dashboard and settings,
* chat workspace,
* markdown rendering,
* upload controls,
* note side panel,
* tool approval modal,
* run-status and progress display.

Recommended stack:

* Next.js
* React
* Tailwind CSS
* SSE or polling for run updates

### 7.2 Backend API Layer

Responsibilities:

* auth and credential management,
* document upload,
* conversation CRUD,
* message creation and retrieval,
* tool approval endpoints,
* note retrieval,
* export endpoints,
* status endpoints for runs and jobs.

Recommended stack:

* FastAPI
* SQLAlchemy Async
* Pydantic

### 7.3 Assistant Worker Layer

Responsibilities:

* consume queued assistant jobs,
* call the LLM,
* request tools,
* pause for approval,
* resume execution,
* persist run traces,
* create artifacts and notes.

This should be separated conceptually from the request-serving API process.

### 7.4 Data Layer

Responsibilities:

* user and credential data,
* conversation and message history,
* workspace documents,
* note content and note revisions,
* assistant runs and tool calls,
* approval state,
* export artifacts,
* calendar and Drive records.

SQLite can remain acceptable for coursework demos, but the schema should be designed so it can later move to PostgreSQL without conceptual change.

### 7.5 Concrete Runtime Interaction Pattern

To make the architecture implementable, the runtime should follow the sequence below:

1. the frontend submits a user message or file-upload request,
2. the backend API persists the request and creates an `AssistantRun`,
3. the Job Service enqueues the run for the worker,
4. the worker loads the conversation context and tool registry,
5. the worker calls the LLM and receives either:
   * a normal assistant response, or
   * a tool request,
6. if the result is a normal assistant response, the backend stores it as an assistant message and marks the run completed,
7. if the result is a tool request and approval is required, the backend stores a `ToolCall`, marks the run `waiting_for_approval`, and exposes the approval request to the frontend,
8. once the user approves or rejects, the backend stores the decision and re-enqueues the run,
9. the worker resumes execution, performs the tool action or returns a rejection-aware assistant response, and then persists the final state.

This interaction pattern is the operational core of the assistant platform and should remain stable even if individual tools evolve.

---

## 8. Service Decomposition

The platform should be decomposed into the following logical services.

### 8.1 Auth Service

Handles:

* registration,
* login,
* JWT/session issuance,
* profile access.

### 8.2 Credential Service

Handles:

* LLM API key storage,
* provider metadata,
* Google OAuth tokens,
* user assistant preferences such as timezone and default export settings.

### 8.3 Workspace Document Service

Handles:

* upload,
* storage-path management,
* MIME validation,
* extracted text,
* workspace document metadata,
* session-document associations.

### 8.4 Conversation Service

Handles:

* conversation creation,
* conversation listing,
* message history,
* attachment associations,
* pinned note retrieval.

### 8.5 Assistant Runtime Service

Handles:

* multi-turn LLM interaction,
* tool selection,
* run state,
* resumable execution,
* message generation,
* trace logging.

### 8.6 Tool Gateway Service

Handles a controlled registry of assistant tools, such as:

* `analyze_document`
* `create_calendar_event`
* `patch_note`
* `export_note_with_pandoc`
* `drive_upload_file`
* `drive_move_file`
* `drive_get_metadata`

It should enforce:

* parameter validation,
* approval requirements,
* execution logging,
* permission checks.

### 8.7 Note Service

Handles:

* session note creation,
* markdown storage,
* diff-based updates,
* immutable revision history,
* current note materialization.

### 8.8 Calendar Service

Handles:

* event extraction from document/chat context,
* candidate-event storage,
* year defaulting,
* Google Calendar API execution,
* sync records.

### 8.9 Drive Service

Handles:

* app-folder management,
* file upload,
* move/copy/download metadata,
* artifact synchronization.

### 8.10 Export Service

Handles:

* markdown-to-docx conversion,
* markdown-to-pptx conversion,
* export file tracking,
* upload of exports to Drive when requested.

### 8.11 Job Service

Handles:

* asynchronous job scheduling,
* retries,
* job states,
* resumable waiting states such as “pending approval”.

### 8.12 Recommended Code Organization

The existing repository can be extended without a full rewrite.

Recommended backend organization:

* `backend/app/api/routes/`
  * add `conversations.py`
  * add `messages.py`
  * add `runs.py`
  * add `tool_calls.py`
  * add `exports.py`
* `backend/app/models/`
  * add `conversation.py`
  * add `conversation_document.py`
  * add `message.py`
  * add `message_attachment.py`
  * add `assistant_run.py`
  * add `tool_call.py`
  * add `tool_approval_decision.py`
  * add `session_note.py`
  * add `session_note_revision.py`
  * add `export_artifact.py`
* `backend/app/schemas/`
  * add request and response schemas for each new route group
* `backend/app/services/`
  * add `conversation_service.py`
  * add `message_service.py`
  * add `assistant_runtime_service.py`
  * add `tool_gateway_service.py`
  * add `job_service.py`
  * add `export_service.py`
* `backend/app/integrations/`
  * extend OpenAI wrapper to support conversation and tool-call mode
  * add a small Pandoc wrapper
* `backend/app/workers/`
  * add worker entrypoints and resume logic

Recommended frontend organization:

* `frontend/src/app/app/chat/page.tsx`
  * chat landing page
* `frontend/src/app/app/chat/[conversationId]/page.tsx`
  * primary conversation workspace
* `frontend/src/components/chat/`
  * `conversation-list.tsx`
  * `message-timeline.tsx`
  * `message-bubble.tsx`
  * `chat-composer.tsx`
  * `attachment-chip.tsx`
  * `tool-approval-modal.tsx`
  * `session-note-panel.tsx`
  * `artifact-list.tsx`
* `frontend/src/lib/`
  * add `chat-api.ts`
  * add `chat-types.ts`
  * add markdown renderer helpers

This layout preserves current project conventions while cleanly separating the new assistant workflow from the existing document-detail MVP.

### 8.13 Work Package Decomposition

For implementation planning, the work should be decomposed into the following packages:

* **WP1: Conversation foundation**
  * conversation model,
  * message model,
  * chat routes,
  * chat navigation and base UI.
* **WP2: Assistant runtime**
  * assistant-run model,
  * worker execution loop,
  * conversation context loading,
  * assistant response persistence.
* **WP3: Tooling and approval**
  * tool registry,
  * tool-call persistence,
  * approval modal,
  * approval endpoints and resume logic.
* **WP4: Session note system**
  * session note model,
  * note revision model,
  * note side panel,
  * note diff/patch application.
* **WP5: External actions**
  * calendar event normalization and creation,
  * Drive management,
  * Pandoc export.
* **WP6: Hardening**
  * tests,
  * audit logs,
  * error handling,
  * migration cleanup.

### 8.14 Suggested Team Division

If one person implements the project, the recommended order is simply WP1 → WP2 → WP3 → WP4 → WP5 → WP6.

If two people implement the project, a practical split is:

* **Member A: Frontend and interaction layer**
  * chat routes and layout,
  * markdown rendering,
  * approval modal,
  * conversation state management,
  * note side panel,
  * artifact presentation.
* **Member B: Backend and integrations**
  * database migrations,
  * conversation/message APIs,
  * assistant runtime,
  * worker and queue,
  * tool execution,
  * Calendar / Drive / Pandoc integration.

Shared work:

* API contract definition,
* end-to-end integration,
* error-state UX,
* testing and report preparation.

---

## 9. Recommended Data Model

The current schema should be extended from document-centric entities to session-centric entities.

### 9.1 User

Existing concept to keep.

### 9.2 UserCredential

Existing concept to keep and extend with:

* timezone,
* preferred model,
* export defaults if needed.

### 9.3 WorkspaceDocument

Refined form of the current `Document` entity.

Fields:

* `id`
* `user_id`
* `filename`
* `storage_path`
* `mime_type`
* `file_size`
* `extracted_text`
* `processing_status`
* `drive_file_id`
* `drive_folder_id`
* `sha256_hash`
* `created_at`
* `updated_at`

Add a stable hash to avoid duplicate semantic uploads when appropriate.

### 9.4 Conversation

Fields:

* `id`
* `user_id`
* `title`
* `status`
* `created_at`
* `updated_at`
* `last_message_at`

### 9.5 ConversationDocument

Join table to decouple notes from documents while allowing a conversation to reference multiple uploaded files.

Fields:

* `id`
* `conversation_id`
* `document_id`
* `attached_by_message_id`
* `created_at`

### 9.6 Message

Fields:

* `id`
* `conversation_id`
* `user_id`
* `role` (`user`, `assistant`, `system`, `tool`)
* `content_markdown`
* `status`
* `created_at`
* `updated_at`

### 9.7 MessageAttachment

Fields:

* `id`
* `message_id`
* `document_id`
* `attachment_type`
* `created_at`

### 9.8 AssistantRun

A generalized evolution of the current analysis-run concept.

Fields:

* `id`
* `conversation_id`
* `message_id`
* `user_id`
* `status`
* `requested_capabilities`
* `completed_capabilities`
* `trace`
* `raw_llm_output`
* `error_message`
* `created_at`
* `updated_at`

### 9.9 ToolCall

Fields:

* `id`
* `assistant_run_id`
* `conversation_id`
* `tool_name`
* `arguments_json`
* `status` (`pending_approval`, `approved`, `rejected`, `running`, `completed`, `failed`)
* `approval_required`
* `approval_reason`
* `result_json`
* `error_message`
* `created_at`
* `updated_at`

### 9.10 ToolApprovalDecision

Optional separate entity if a richer audit trail is desired.

Fields:

* `id`
* `tool_call_id`
* `decided_by_user_id`
* `decision`
* `comment`
* `created_at`

### 9.11 SessionNote

This replaces the current document-bound note model.

Fields:

* `id`
* `conversation_id`
* `user_id`
* `title`
* `current_markdown`
* `created_at`
* `updated_at`

### 9.12 SessionNoteRevision

Fields:

* `id`
* `note_id`
* `assistant_run_id`
* `patch_format`
* `patch_text`
* `result_markdown`
* `created_at`

### 9.13 CandidateEvent

May be reused and extended with:

* `conversation_id`
* `source_message_id`
* `source_document_id`
* `normalized_year_defaulted`

### 9.14 CalendarRecord

Existing concept to keep.

### 9.15 ExportArtifact

Fields:

* `id`
* `conversation_id`
* `note_id`
* `source_format`
* `target_format`
* `storage_path`
* `drive_file_id`
* `status`
* `created_at`
* `updated_at`

### 9.16 Relational Rules and Constraints

The following relational rules should be enforced at the database level where feasible:

* one `Conversation` belongs to one `User`,
* one `SessionNote` belongs to one `Conversation`,
* one `Message` belongs to one `Conversation`,
* one `AssistantRun` is triggered by one user message,
* one `ToolCall` belongs to one `AssistantRun`,
* one `ToolApprovalDecision` belongs to one `ToolCall`,
* one `Conversation` can reference many uploaded documents through `ConversationDocument`,
* one `WorkspaceDocument` can be attached to many conversations if reuse is allowed in later phases.

Recommended uniqueness constraints:

* `conversation_documents (conversation_id, document_id)` unique
* `message_attachments (message_id, document_id)` unique
* `session_notes (conversation_id)` unique
* `calendar_records (candidate_event_id)` unique
* `export_artifacts (note_id, target_format, source_revision_id)` unique when revision-aware export is added

Recommended indexes:

* `messages (conversation_id, created_at)`
* `assistant_runs (conversation_id, created_at)`
* `tool_calls (assistant_run_id, status)`
* `candidate_events (conversation_id, status)`
* `workspace_documents (user_id, created_at)`

### 9.17 Status Enums

To reduce ambiguity, the following enum sets should be defined explicitly.

Recommended `conversation.status` values:

* `active`
* `archived`
* `deleted`

Recommended `message.status` values:

* `complete`
* `streaming`
* `error`

Recommended `assistant_run.status` values:

* `queued`
* `running`
* `waiting_for_approval`
* `completed`
* `failed`
* `cancelled`

Recommended `export_artifact.status` values:

* `queued`
* `generating`
* `completed`
* `failed`

### 9.18 Migration Strategy

The database should be evolved through additive migrations rather than destructive replacement.

Recommended sequence:

1. add conversation and message tables,
2. add assistant run and tool call tables,
3. add session note and note revision tables,
4. add export artifact table,
5. add any compatibility migration needed to phase out document-bound notes later.

This keeps the current MVP usable while the new chat architecture is introduced incrementally.

---

## 10. LLM and Tool-Calling Architecture

### 10.1 Current State

The existing backend uses an OpenAI-compatible client for one-shot JSON generation. That is suitable for:

* intent classification,
* note generation,
* event extraction.

It is not yet sufficient for:

* multi-turn conversations,
* tool calls with approval pauses,
* rich assistant event traces.

### 10.2 Recommended Target

Adopt a conversation-oriented assistant runtime that supports:

* multi-turn message history,
* structured tool definitions,
* server-executed tool functions,
* resumable runs after user approval,
* markdown assistant output.

Recommended provider strategy:

* keep OpenAI as the default provider,
* use a tool-capable API mode for assistant responses,
* retain provider abstraction so the rest of the backend is not tightly coupled to one SDK surface.

### 10.3 Tool Categories

#### Read-Only Tools

Examples:

* inspect uploaded documents,
* retrieve current note,
* list session attachments,
* inspect event proposals.

#### Side-Effect Tools

Examples:

* create Google Calendar events,
* upload or move files in Drive,
* export notes with Pandoc,
* apply note patches.

These should go through approval.

### 10.4 Approval Semantics

Suggested rule:

* the model may **request** a tool,
* the backend persists the request,
* the frontend shows an approval modal,
* the user approves or rejects,
* the assistant run resumes accordingly.

This gives the project a clear “agent with human-in-the-loop” design, which is strong for the assignment.

---

## 11. External Tools and Required Configuration

### 11.1 Already Present

The project already uses:

* OpenAI API
* Google OAuth
* Google Calendar API
* Google Drive API
* PyMuPDF

### 11.2 New Frontend Libraries to Add

Recommended:

* `react-markdown`
* `remark-gfm`
* `rehype-sanitize`

Optional:

* `rehype-highlight`
* a minimal diff viewer if note revisions are shown visually

### 11.3 New Backend Libraries to Add

Recommended:

* `dateparser`
  * normalize partial or ambiguous date expressions,
  * enforce “current year if missing”.
* a background job runtime:
  * recommended: `arq` with Redis,
  * acceptable fallback for a smaller demo: a DB-backed worker loop.

### 11.4 New System-Level Tool to Install

Required:

* `pandoc`

Reason:

* markdown-to-docx
* markdown-to-pptx

Environment addition:

* `PANDOC_BINARY` or a documented system dependency in setup instructions

### 11.5 Google Scope Strategy

Keep the existing Google integrations, but rationalize scope carefully.

Recommended v1 scopes:

* `https://www.googleapis.com/auth/calendar.events`
* `https://www.googleapis.com/auth/drive.file`
* `openid`
* `https://www.googleapis.com/auth/userinfo.email`

If unrestricted Drive browsing is later required, a broader Drive scope may be necessary, but that should be an explicit security decision rather than a default.

### 11.6 Runtime and Deployment Considerations

If the worker route is adopted, local development should run:

1. frontend,
2. backend API,
3. Redis,
4. assistant worker.

---

## 12. API Design Direction

The API should remain RESTful even if the frontend later uses SSE for live updates.

### 12.1 Conversations

* `POST /api/conversations`
* `GET /api/conversations`
* `GET /api/conversations/{id}`
* `PATCH /api/conversations/{id}`

### 12.2 Messages

* `GET /api/conversations/{id}/messages`
* `POST /api/conversations/{id}/messages`

### 12.3 Conversation Uploads

* `POST /api/conversations/{id}/documents`
* `GET /api/conversations/{id}/documents`

### 12.4 Assistant Runs

* `POST /api/conversations/{id}/runs`
* `GET /api/runs/{id}`
* `GET /api/runs/{id}/events`

### 12.5 Tool Approvals

* `GET /api/tool-calls/{id}`
* `POST /api/tool-calls/{id}/approve`
* `POST /api/tool-calls/{id}/reject`

### 12.6 Notes

* `GET /api/conversations/{id}/note`
* `GET /api/notes/{id}/revisions`

Note editing should not be exposed as a direct user-write endpoint in the revised design unless an admin/debug mode is intentionally kept.

### 12.7 Calendar

* `GET /api/conversations/{id}/events`
* `POST /api/events/{id}/approve-and-create`

### 12.8 Exports

* `POST /api/conversations/{id}/exports`
* `GET /api/exports/{id}`

### 12.9 Drive

* `POST /api/drive/upload-artifact`
* `POST /api/drive/move-file`
* `GET /api/drive/files/{id}`

### 12.10 Concrete Request and Response Formats

The following contracts are recommended so implementation can proceed consistently across frontend and backend.

#### Create Conversation

`POST /api/conversations`

```json
{
  "title": "SC4052 Week 8 planning"
}
```

```json
{
  "id": "conv_123",
  "title": "SC4052 Week 8 planning",
  "status": "active",
  "created_at": "2026-04-17T10:00:00Z",
  "updated_at": "2026-04-17T10:00:00Z",
  "last_message_at": null
}
```

#### Send User Message

`POST /api/conversations/{id}/messages`

```json
{
  "content": "Please summarize the uploaded syllabus and extract all deadlines.",
  "attachment_document_ids": ["doc_001"]
}
```

```json
{
  "message": {
    "id": "msg_001",
    "role": "user",
    "content_markdown": "Please summarize the uploaded syllabus and extract all deadlines.",
    "status": "complete",
    "created_at": "2026-04-17T10:02:00Z"
  },
  "assistant_run": {
    "id": "run_001",
    "status": "queued"
  }
}
```

#### Upload Document into Conversation

`POST /api/conversations/{id}/documents`

Request:

* `multipart/form-data`
* field name: `file`

```json
{
  "document": {
    "id": "doc_001",
    "filename": "course_outline.pdf",
    "mime_type": "application/pdf",
    "file_size": 245812,
    "processing_status": "uploaded"
  },
  "conversation_document": {
    "conversation_id": "conv_123",
    "document_id": "doc_001"
  }
}
```

#### Get Conversation Detail

`GET /api/conversations/{id}`

```json
{
  "conversation": {
    "id": "conv_123",
    "title": "SC4052 Week 8 planning",
    "status": "active"
  },
  "latest_note": {
    "id": "note_001",
    "title": "Study Note",
    "updated_at": "2026-04-17T10:10:00Z"
  },
  "documents": [
    {
      "id": "doc_001",
      "filename": "course_outline.pdf",
      "processing_status": "analyzed"
    }
  ]
}
```

#### Tool Approval

`POST /api/tool-calls/{id}/approve`

```json
{
  "decision_comment": "Create this event in my primary calendar."
}
```

```json
{
  "tool_call_id": "tool_001",
  "status": "approved",
  "assistant_run": {
    "id": "run_001",
    "status": "queued"
  }
}
```

`POST /api/tool-calls/{id}/reject`

```json
{
  "decision_comment": "Do not create external events for this item."
}
```

#### Retrieve Session Note

`GET /api/conversations/{id}/note`

```json
{
  "id": "note_001",
  "conversation_id": "conv_123",
  "title": "Syllabus Summary",
  "current_markdown": "# Summary\n\n- Deadline one\n- Deadline two",
  "updated_at": "2026-04-17T10:10:00Z"
}
```

#### Create Export

`POST /api/conversations/{id}/exports`

```json
{
  "note_id": "note_001",
  "target_format": "docx",
  "upload_to_drive": true
}
```

```json
{
  "id": "export_001",
  "status": "queued",
  "target_format": "docx"
}
```

### 12.11 Event Stream Format

If SSE is added, the event stream for `GET /api/runs/{id}/events` should use simple event types so the frontend can remain straightforward.

Recommended event types:

* `run.status`
* `message.created`
* `tool_call.created`
* `tool_call.updated`
* `note.updated`
* `artifact.created`

Recommended event payload shape:

```json
{
  "type": "tool_call.created",
  "run_id": "run_001",
  "timestamp": "2026-04-17T10:05:00Z",
  "data": {
    "tool_call_id": "tool_001",
    "tool_name": "create_calendar_event",
    "status": "pending_approval"
  }
}
```

---

## 13. Main Interaction Flows

### 13.1 New Conversation Flow

1. User opens Chat.
2. User creates or selects a conversation.
3. User sends a message, optionally with uploaded PDF attachments.
4. Backend stores the message and enqueues an assistant run.
5. Worker processes the run.
6. Assistant responds in markdown.
7. If a tool is needed, the run pauses for approval.
8. After approval, the run resumes and stores the result.

### 13.2 Document Analysis Flow

1. User uploads a PDF in chat.
2. Workspace Document Service stores the file and extracts text.
3. Assistant recognizes the user’s intent to analyze.
4. Worker runs document analysis asynchronously.
5. Assistant posts progress or completion messages.
6. Session note is created or updated in markdown.

### 13.3 Calendar Flow

1. Assistant detects date-bearing tasks.
2. Backend normalizes dates.
3. Candidate events are stored.
4. User approves event creation.
5. Calendar Service writes to Google Calendar.
6. Result is persisted and shown in the conversation.

### 13.4 Note Patch Flow

1. A note already exists for the session.
2. User asks the assistant to revise it.
3. Assistant requests `patch_note`.
4. User approves if required.
5. Backend applies patch logic and stores a revision.
6. Updated note appears in the side panel.

### 13.5 Export Flow

1. User requests `docx` or `pptx` export.
2. Assistant requests the Pandoc tool.
3. User approves.
4. Export Service generates the artifact.
5. Artifact metadata is stored.
6. Assistant shares the result and may optionally upload it to Drive.

---

## 14. Frontend Design Plan

### 14.1 Navigation

The protected navigation should become:

* Dashboard
* Chat
* Settings

### 14.2 Chat Workspace Layout

Recommended layout:

* left: conversation list or thread selector,
* center: message timeline and composer,
* right: note panel and run artifacts.

On smaller screens:

* stack the note panel below the chat timeline,
* keep the approval modal full-width.

### 14.3 Components to Introduce

* `ConversationList`
* `MessageTimeline`
* `MessageBubble`
* `ChatComposer`
* `AttachmentChip`
* `ToolApprovalModal`
* `RunStatusBanner`
* `SessionNotePanel`
* `ArtifactList`

### 14.4 UX Principles

The assistant UI should feel familiar to mainstream LLM apps while still supporting auditability:

* markdown messages,
* readable system status messages,
* clear tool approval boundaries,
* visible attachment context,
* visible session note state,
* visible export/download artifacts.

### 14.5 Concrete Page Additions

The frontend should introduce the following user-facing pages or route states.

#### Dashboard

Role:

* remains the high-level overview page,
* shows recent documents,
* shows recent conversations,
* provides shortcuts to Chat and Settings.

New additions:

* “Continue conversation” panel,
* recent export artifacts,
* recent pending approvals summary.

#### Chat Landing Page

Route:

* `/app/chat`

Role:

* show conversation list,
* create a new conversation,
* show an empty-state introduction when no thread exists.

#### Chat Workspace Page

Route:

* `/app/chat/[conversationId]`

Role:

* primary working page for conversation,
* center the message timeline,
* keep uploads and assistant actions in one place,
* show current note and artifacts in the side panel.

#### Settings Page

Role:

* keep profile and credential management,
* add assistant preferences such as timezone and default export preference if needed.

#### Legacy Document Detail Page

Role:

* remain temporarily for backward compatibility during migration,
* link users toward the new conversation workflow,
* gradually reduce its editing responsibilities once session notes are stable.

### 14.6 Chat Workspace Regions

For implementation, the chat workspace should be divided into fixed visual regions:

* **Region A: Conversation Sidebar**
  * create thread button,
  * searchable conversation list,
  * unread or pending-approval indicators.
* **Region B: Main Timeline**
  * user messages,
  * assistant markdown messages,
  * system status messages,
  * tool request cards.
* **Region C: Composer Dock**
  * text input,
  * upload action,
  * submit button,
  * disabled/loading states.
* **Region D: Right Utility Panel**
  * current note,
  * attached documents,
  * candidate events,
  * generated artifacts.

### 14.7 UI State Handling

The frontend should explicitly design for the following states:

* empty conversation,
* assistant running,
* waiting for approval,
* export in progress,
* upload failed,
* note unavailable,
* Google integration unavailable,
* document analysis failed.

Each state should have visible, user-readable feedback rather than silently failing or hiding controls.

### 14.8 Frontend State Management Strategy

To avoid over-engineering, the recommended frontend state strategy is:

* route-driven page state with Next.js,
* local component state for composer and modal interactions,
* shared auth state through the existing provider,
* conversation polling hook or SSE hook for run updates,
* API response normalization in `src/lib/chat-api.ts`.

This keeps complexity moderate while supporting the assistant workflow.

---

## 15. Persistence Strategy and Data Integrity

The system should preserve consistency under retries and partial failures.

### 15.1 Idempotency Requirements

The implementation should avoid semantically duplicated data for:

* repeated tool retries,
* repeated event creation attempts,
* repeated upload submissions,
* repeated assistant-run resumptions,
* repeated note patch applications.

Recommended approaches:

* stable hashes for uploaded documents,
* unique tool-call IDs per run step,
* unique calendar signatures,
* revision-based note storage,
* export artifact deduplication by note revision and target format.

### 15.2 Auditability

The database should preserve:

* which message triggered a run,
* which tool was requested,
* whether approval was granted,
* what side effect occurred,
* what note revision resulted.

This is important both for debugging and for demonstrating disciplined PA-as-a-Service design.

---

## 16. Security and Safety Design

The system should adopt the following controls:

* encrypted LLM API keys,
* encrypted Google tokens,
* strict per-user access control,
* approval gates before external side effects,
* server-side validation of uploaded files,
* sanitized markdown rendering,
* controlled filesystem locations for uploads and exports,
* no frontend exposure of third-party secrets,
* bounded assistant tool registry rather than arbitrary code execution.

Special care should be taken so that:

* assistant tools do not expose unrestricted host access,
* Drive operations stay within approved scope,
* note patching cannot overwrite unrelated user data,
* approval states cannot be forged across users.

---

## 17. Background Execution Strategy

### 17.1 Why Asynchronous Execution Is Required

The requested assistant behavior includes:

* document parsing,
* LLM calls,
* waiting for user approval,
* Pandoc conversion,
* external API calls.

This is too complex and too long-running for a single synchronous HTTP request.

### 17.2 Recommended Approach

Preferred option:

* Redis + ARQ worker

Reasons:

* simple Python integration,
* good fit for async FastAPI code,
* supports retry and background processing cleanly.

Fallback option for coursework simplicity:

* database-backed run records plus a lightweight worker loop

This fallback reduces infrastructure needs but is less robust.

### 17.3 Status Reporting

Recommended order of implementation:

1. polling-based run status for correctness first,
2. SSE-based incremental updates second.

This is a pragmatic engineering sequence.

### 17.4 Assistant Run State Machine

The assistant runtime should implement a simple explicit state machine:

* `queued`
  * run is persisted and waiting for worker pickup
* `running`
  * worker is actively calling the model or executing a tool
* `waiting_for_approval`
  * worker is paused because a side-effect tool was requested
* `completed`
  * run finished successfully
* `failed`
  * run ended due to an unrecoverable error
* `cancelled`
  * run was abandoned by explicit user or system action

Allowed transitions:

* `queued -> running`
* `running -> waiting_for_approval`
* `waiting_for_approval -> queued`
* `running -> completed`
* `running -> failed`
* `queued -> cancelled`
* `waiting_for_approval -> cancelled`

Persisting these transitions is important for debugging, retry logic, and UI correctness.

---

## 18. Migration Plan from the Current MVP

### Phase 0: Preserve and Reuse

Reuse without major redesign:

* auth flow,
* credential storage,
* PDF upload storage,
* Google OAuth handling,
* low-level Calendar and Drive integration helpers.

### Phase 1: Data Model Expansion

Implement:

* conversations,
* messages,
* conversation-document links,
* generalized assistant runs,
* tool calls,
* session notes,
* note revisions,
* export artifacts.

### Phase 2: Chat UI and Persistence

Implement:

* Chat navigation item,
* chat page,
* session list,
* message timeline,
* markdown renderer,
* upload within conversation,
* note side panel.

### Phase 3: Assistant Runtime

Implement:

* multi-turn run orchestration,
* tool registry,
* pause/resume state,
* document-analysis jobs,
* candidate event creation from chat context.

### Phase 4: Approval and Side-Effect Tools

Implement:

* tool approval modal,
* approval endpoints,
* Google Calendar side-effect flow,
* Drive management flow,
* note patch tool.

### Phase 5: Export

Implement:

* Pandoc integration,
* docx export,
* pptx export,
* Drive upload for exports.

### Phase 6: Hardening

Implement:

* audit improvements,
* retries,
* better status updates,
* richer tests,
* UX refinements.

### Phase 7: Cleanup and Consolidation

Implement:

* retire or simplify direct note editing on the old document page,
* migrate dashboards to show session notes and recent conversations,
* de-duplicate overlapping old and new APIs where appropriate,
* finalize documentation and demo scripts.

---

## 19. Testing Strategy

### 19.1 Backend Tests

Add tests for:

* conversation creation and retrieval,
* message persistence,
* session-document association,
* assistant-run state transitions,
* approval-required tool flows,
* note revision application,
* date normalization with missing year,
* export artifact creation,
* Drive operation authorization checks.

### 19.2 Frontend Tests

Add tests for:

* chat route rendering,
* markdown rendering safety,
* approval modal behavior,
* upload UX,
* note side-panel rendering,
* conversation switching,
* run-status display.

### 19.3 End-to-End Checks

Demonstrate:

1. upload a course PDF in chat,
2. generate a markdown note,
3. detect a deadline,
4. approve calendar creation,
5. export note to `docx`,
6. upload artifact to Drive.

This end-to-end scenario strongly showcases the assignment requirements.

---

## 20. Risks and Mitigation

### Risk 1: Scope Explosion

The revised system is substantially broader than the current MVP.

**Mitigation:**

* prioritize conversation core first,
* defer streaming polish until after correctness,
* constrain Drive scope,
* keep OCR and broad retrieval out of scope.

### Risk 2: Approval Workflow Complexity

Pause/resume agent execution is more complex than one-shot analysis.

**Mitigation:**

* persist every run state transition,
* keep tool interfaces small and explicit,
* start with polling before SSE.

### Risk 3: Data Model Refactor Cost

The current note model is document-bound.

**Mitigation:**

* introduce session-note entities rather than overloading the old note schema,
* migrate incrementally,
* keep old document detail pages operational during transition if needed.

### Risk 4: External Tooling Availability

Pandoc is not a Python library dependency; it is a host binary.

**Mitigation:**

* document installation explicitly,
* validate availability at startup or before export,
* surface a clear configuration error to the user.

### Risk 5: Calendar and Drive Permission Boundaries

Google scopes can easily become too broad.

**Mitigation:**

* keep v1 to app-managed scope,
* require explicit approval,
* log all side-effect operations.

---

## 21. Success Criteria

The revised LearnPilot implementation will be considered successful if it can demonstrate the following:

1. A user can open a chat session, upload a study PDF, and talk to the assistant.
2. The assistant responds with markdown-rendered messages.
3. Conversation history, attachments, tool calls, and artifacts persist per user.
4. The assistant can trigger asynchronous document analysis.
5. The assistant can maintain a session note in markdown.
6. The assistant can propose Google Calendar events and wait for approval.
7. The assistant can export a note to `docx` or `pptx` through Pandoc.
8. The assistant can manage app-scoped files through Google Drive.
9. The backend remains modular and clearly decomposed into independent services with RESTful interfaces.

---

## 22. Final Engineering Position

The right engineering move is **not** to bolt a chat UI onto the current document-detail flow.

Instead, LearnPilot should be evolved into a **conversation-first assistant platform** that reuses the existing MVP foundations while introducing:

* session-centric persistence,
* asynchronous assistant runs,
* tool approval gates,
* note revision control,
* export and cloud-file tooling.

This architecture is more coherent, more extensible, and more faithful to the assignment’s idea of Personal Assistant-as-a-Service.
