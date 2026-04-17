

# Software Engineering Plan for LearnPilot

## 1. Project Title

**LearnPilot: A Learning Assistant-as-a-Service for Academic Document Understanding, Scheduling, and Cloud Archiving**

---

## 2. Project Overview

LearnPilot is a cloud-based learning assistant platform designed for students to process academic PDF documents and automatically perform useful follow-up actions. The system allows users to upload text-based PDF files such as course syllabi, assignment briefs, lecture notes, and announcements. It then uses a large language model (LLM) to identify user intent, extract important information, summarize content, generate notes, detect schedule-related events, and optionally archive files to cloud storage.

The platform follows the principle of **Personal Assistant-as-a-Service**, where assistant capabilities are decomposed into modular services that communicate via RESTful APIs. This design directly matches the Topic 2 requirement of building a personal assistant platform composed of independent service components. 

The proposed system focuses on the educational domain rather than being a general-purpose personal assistant. This scope reduction improves thematic consistency and makes the project more feasible to implement within the course timeline.

---

## 3. Project Objectives

The main objectives of LearnPilot are:

1. To build a web-based learning assistant platform for students.
2. To support secure user login and user-level API credential management.
3. To allow users to upload text-based PDF documents for automated analysis.
4. To use an LLM to perform intent recognition and structured information extraction.
5. To provide modular RESTful services for:

   * document summarization,
   * key-point extraction,
   * note storage,
   * event extraction and calendar creation,
   * optional cloud archiving.
6. To integrate with external APIs, especially Google Calendar and Google Drive.
7. To demonstrate an agent-style orchestration workflow that chooses suitable services based on document content and user intent.

---

## 4. Problem Statement

Students often receive many academic documents such as syllabi, assignment specifications, announcements, and lecture notes. Important information such as deadlines, class schedules, exam dates, and key learning points is scattered across multiple files. Manually reviewing these documents, extracting relevant actions, and organizing notes can be time-consuming and error-prone.

Existing tools usually solve only one part of the problem. For example:

* cloud storage systems store files but do not analyze them,
* calendar applications create events but do not extract them from course documents,
* LLM chat tools summarize text but do not maintain structured personal study records.

LearnPilot aims to provide an integrated solution by combining document understanding, scheduling, note organization, and cloud storage under one unified service-oriented platform.

---

## 5. Scope of the System

### 5.1 In-Scope Features

The first version of the system will support:

* user registration and login,
* user profile management,
* user-specific LLM API key configuration,
* upload of text-based PDF documents,
* extraction of text from PDFs,
* document summarization,
* key-point analysis,
* extraction of schedule-related information,
* user confirmation of suggested calendar events,
* creation of Google Calendar events,
* optional archiving of original PDFs to Google Drive,
* saving generated notes into a database,
* viewing processed documents and saved notes in a dashboard.

### 5.2 Out-of-Scope Features

The following features are intentionally excluded from the first version:

* OCR for image-based PDFs,
* GitHub-related functions,
* email integration,
* advanced long-term memory or habit modeling,
* multi-cloud storage support beyond Google ecosystem,
* automatic event creation without user confirmation,
* complex collaboration or multi-user shared workspaces.

This scope control is important to keep the project feasible while still demonstrating meaningful API integration and agent-based service orchestration.

---

## 6. Functional Requirements

### 6.1 User Management

The system shall allow users to:

* register an account,
* log in securely,
* manage their profile,
* store and update their LLM API key,
* connect their Google account through OAuth 2.0.

### 6.2 Document Upload and Processing

The system shall allow users to:

* upload text-based PDF documents,
* view uploaded documents,
* trigger document analysis,
* retrieve extracted text and processing results.

### 6.3 Intent Recognition

The system shall use an LLM to classify document-related intent into a limited set of supported actions, such as:

* summarize the document,
* extract key points,
* identify actionable schedule events,
* archive the file,
* save notes.

### 6.4 Note Generation and Storage

The system shall:

* generate structured notes from uploaded documents,
* save notes to the database,
* allow users to review generated notes later.

### 6.5 Calendar Integration

The system shall:

* identify date/time-related items from documents,
* generate candidate calendar events,
* present candidate events for user review,
* create approved events in Google Calendar.

Google Calendar API officially supports event creation and management through REST endpoints and client libraries, making it suitable for this project.

### 6.6 Drive Integration

The system shall optionally:

* create folders in Google Drive,
* upload original PDF documents into user-specific folders,
* maintain the file reference in the platform database.

Google Drive API officially supports file upload, metadata management, and folder organization, which aligns well with the archiving requirement.

---

## 7. Non-Functional Requirements

### 7.1 Usability

The web interface should be simple and suitable for student use. Main workflows such as upload, analyze, review event, and save note should be easy to complete.

### 7.2 Security

The system must protect:

* user passwords,
* user API keys,
* Google OAuth tokens.

Sensitive credentials should be stored securely on the backend and never exposed directly in frontend code.

### 7.3 Maintainability

The system should adopt a modular service-oriented backend structure. Even if deployed as a single backend application, internal components should be logically separated to simplify future extension.

### 7.4 Reliability

The system should handle invalid PDFs, API errors, authentication failures, and malformed extraction results gracefully.

### 7.5 Extensibility

The architecture should allow future addition of:

* OCR,
* Google Docs export,
* more external tools,
* MCP-compatible tool exposure.

---

## 8. Proposed System Architecture

LearnPilot will use a **three-layer architecture**:

### 8.1 Frontend Layer

Responsible for:

* user interaction,
* file upload,
* display of summaries and notes,
* review of extracted events,
* account and credential settings.

Recommended technology:

* **Next.js / React**
* Tailwind CSS for UI styling

### 8.2 Backend Layer

Responsible for:

* authentication,
* business logic,
* LLM request handling,
* intent recognition,
* tool orchestration,
* PDF parsing,
* calendar and drive integration,
* note persistence.

Recommended technology:

* **FastAPI**
* Python 3.11
* Pydantic for schema validation

### 8.3 Data Layer

Responsible for:

* user data,
* API key metadata,
* document records,
* extracted notes,
* event records,
* Drive file references.

Recommended technology:

* **PostgreSQL** or **SQLite** for prototype development

---

## 9. Internal Service Decomposition

Although the system may be physically deployed as one backend application, it will be logically decomposed into the following independent services:

### 9.1 Auth Service

Handles:

* user registration,
* login,
* session/JWT issuance,
* password hashing.

### 9.2 API Credential Service

Handles:

* user-level LLM API key storage,
* Google OAuth token storage,
* credential update and retrieval.

### 9.3 Document Service

Handles:

* PDF upload,
* text extraction,
* document metadata storage.

### 9.4 Intent Service

Handles:

* LLM-based intent classification,
* structured extraction of task types from document text.

### 9.5 Notes Service

Handles:

* summary generation,
* key-point generation,
* note persistence.

### 9.6 Calendar Service

Handles:

* candidate event creation,
* event review state,
* Google Calendar API invocation.

### 9.7 Drive Service

Handles:

* folder creation,
* PDF upload to Google Drive,
* file reference storage.

### 9.8 Orchestrator Service

Handles:

* selecting which internal services to call,
* controlling workflow order,
* managing execution trace and result aggregation.

This decomposition satisfies the assignment’s idea of PA capabilities being implemented as independent services communicating through APIs. 

---

## 10. Suggested RESTful API Design

A simplified initial API design is as follows:

### Authentication

* `POST /api/auth/register`
* `POST /api/auth/login`
* `GET /api/auth/me`

### Credential Management

* `POST /api/credentials/llm`
* `POST /api/credentials/google/connect`
* `GET /api/credentials/status`

### Document Handling

* `POST /api/documents/upload`
* `GET /api/documents`
* `GET /api/documents/{id}`

### Analysis and Orchestration

* `POST /api/documents/{id}/analyze`
* `POST /api/assistant/execute`

### Notes

* `GET /api/notes`
* `POST /api/notes/save`

### Calendar

* `POST /api/calendar/extract-events`
* `POST /api/calendar/create-events`

### Drive

* `POST /api/drive/archive`
* `GET /api/drive/files/{document_id}`

---

## 11. Main Workflow

The main user workflow of LearnPilot is as follows:

1. The user logs into the platform.
2. The user configures an LLM API key.
3. The user connects a Google account via OAuth.
4. The user uploads a text-based PDF.
5. The backend extracts text from the document.
6. The LLM performs intent recognition and structured analysis.
7. The orchestrator selects appropriate services:

   * summary generation,
   * note saving,
   * event extraction,
   * optional Drive archiving.
8. Candidate calendar events are shown to the user.
9. After user confirmation, selected events are written to Google Calendar.
10. Notes and document metadata are saved and displayed in the dashboard.

---

## 12. Required Tools and Technologies

### 12.1 Core Development Tools

* **Python 3.11**
* **FastAPI**
* **Next.js / React**
* **PostgreSQL or SQLite**
* **Docker** for local deployment and packaging
* **Git** for version control

### 12.2 PDF Processing

* **PyMuPDF** or **pdfplumber**

  * used only for text-based PDF extraction

### 12.3 LLM Access

* OpenAI-compatible API protocol
* user-provided API key
* JSON-structured output for intent and event extraction

### 12.4 Google Integrations

* **Google Calendar API**
* **Google Drive API**
* **OAuth 2.0**
* official Google client libraries or direct REST invocation

Google provides official quickstarts and SDK guidance for both Drive and Calendar, which lowers integration difficulty for this project.

### 12.5 Optional Development Utilities

* Swagger / OpenAPI docs generated by FastAPI
* Postman for API testing
* Alembic for database migration
* Celery or background task queue if long-running jobs are added later

---

## 13. Data Model Overview

The main database entities are:

### User

* user_id
* email
* password_hash
* created_at

### UserCredential

* credential_id
* user_id
* llm_provider
* encrypted_api_key
* google_token_reference

### Document

* document_id
* user_id
* filename
* extracted_text
* upload_time
* drive_file_id

### Note

* note_id
* document_id
* summary
* key_points
* action_items
* created_at

### CandidateEvent

* event_id
* document_id
* title
* start_time
* end_time
* description
* status

### CalendarRecord

* calendar_record_id
* user_id
* candidate_event_id
* google_event_id

---

## 14. Security Design

The system will adopt the following security practices:

* passwords stored with secure hashing,
* API keys encrypted before persistence,
* Google authentication handled through OAuth 2.0,
* backend-only access to external service tokens,
* HTTPS assumed in deployment,
* server-side validation for uploaded files,
* strict access control so users only see their own documents and notes.

---

## 15. Why Google Ecosystem Is a Good Fit

The project intentionally favors a single ecosystem for cloud integration. Google services are suitable because:

1. **Calendar integration is directly relevant** to extracting deadlines and schedules from academic documents.
2. **Drive integration naturally supports file archiving** and folder organization.
3. Google provides mature official APIs, documentation, and quickstarts.
4. A single ecosystem reduces development overhead compared with integrating multiple vendors.

This is a practical engineering trade-off rather than a limitation.

---

## 16. MCP Consideration

Model Context Protocol (MCP) is an open protocol for exposing tools and resources to AI systems, and there are existing community efforts around Google-related MCP servers. However, for this project, MCP is better treated as a **future extension** rather than the primary implementation model.

The reason is that LearnPilot is primarily a user-facing SaaS application with its own frontend, authentication, and controlled workflow. A direct REST-based backend is simpler and more suitable for the first implementation. In future work, services such as CalendarService and DriveService could be wrapped as MCP tools so that external agent clients can reuse them. This design choice keeps the current system feasible while still acknowledging modern agent-tooling standards.

---

## 17. Risks and Mitigation

### Risk 1: Scope becomes too large

**Mitigation:** restrict the first version to text PDF, note generation, Calendar integration, and optional Drive archiving.

### Risk 2: External API integration complexity

**Mitigation:** use only Google Calendar and Google Drive in the first version, and rely on official SDKs and guides.

### Risk 3: LLM output instability

**Mitigation:** use constrained prompts and JSON schema validation.

### Risk 4: Incorrect calendar event extraction

**Mitigation:** require user confirmation before event creation.

---

## 18. Development Plan

### Phase 1: Core Platform

* implement login and user management
* implement PDF upload and text extraction
* build database schema

### Phase 2: LLM Analysis

* implement summary generation
* implement intent recognition
* implement structured event extraction

### Phase 3: External Tool Integration

* integrate Google Calendar API
* integrate Google Drive API

### Phase 4: Frontend and Demonstration

* build dashboard
* add event review interface
* add note display
* prepare demo scenarios

### Phase 5: Evaluation

* test correctness of event extraction
* test note usefulness
* test API integration reliability
* evaluate end-to-end workflow success

---

## 19. Expected Deliverables

The project will deliver:

1. A working web-based prototype of LearnPilot
2. Source code repository
3. Final report
4. Presentation slides
5. Demonstration cases showing:

   * PDF upload,
   * summary generation,
   * note storage,
   * event extraction,
   * Google Calendar creation,
   * optional Drive archiving

---

## 20. Conclusion

LearnPilot is a feasible and well-scoped Topic 2 project that applies the Personal Assistant-as-a-Service concept to the educational domain. The proposed system uses modular RESTful services, LLM-based intent recognition, and external API integration to transform uploaded academic documents into actionable outputs such as notes, schedules, and archived resources. By focusing on Google Calendar and Google Drive, the system remains practical to implement while still demonstrating meaningful cloud integration and agent-style orchestration.

