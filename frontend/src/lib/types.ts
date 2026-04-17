export type ApiError = {
  code: string;
  message: string;
  details?: unknown;
};

export type User = {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
  updated_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export type CredentialStatus = {
  llm_configured: boolean;
  llm_provider: string | null;
  google_connected: boolean;
  google_account_email: string | null;
  google_token_expiry: string | null;
};

export type DocumentListItem = {
  id: string;
  user_id: string;
  filename: string;
  mime_type: string;
  file_size: number;
  processing_status: string;
  drive_file_id: string | null;
  drive_folder_id: string | null;
  created_at: string;
  updated_at: string;
};

export type AnalysisRun = {
  id: string;
  user_id: string;
  document_id: string;
  status: string;
  requested_actions: string[];
  completed_actions: string[];
  raw_llm_output: string | null;
  trace: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type AssistantRun = {
  id: string;
  conversation_id: string;
  message_id: string;
  user_id: string;
  status: "queued" | "running" | "completed" | "failed";
  trace: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type Conversation = {
  id: string;
  user_id: string;
  title: string;
  status: "active" | "archived";
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ConversationDetail = Conversation & {
  latest_run: AssistantRun | null;
};

export type MessageAttachmentReference = {
  id: string;
  filename: string;
  processing_status: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  user_id: string;
  role: "user" | "assistant" | "system" | "tool";
  content_markdown: string;
  status: "complete" | "error";
  attachments: MessageAttachmentReference[];
  created_at: string;
  updated_at: string;
};

export type ConversationDocument = {
  id: string;
  conversation_id: string;
  document_id: string;
  attached_by_message_id: string | null;
  document: DocumentListItem;
  created_at: string;
  updated_at: string;
};

export type Note = {
  id: string;
  user_id: string;
  document_id: string;
  summary: string;
  key_points: string[];
  action_items: string[];
  created_at: string;
  updated_at: string;
};

export type CandidateEvent = {
  id: string;
  user_id: string;
  document_id: string;
  title: string;
  start_time: string;
  end_time: string | null;
  description: string | null;
  location: string | null;
  source_excerpt: string | null;
  status: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentDetail = DocumentListItem & {
  extracted_text: string | null;
  note: Note | null;
  candidate_events: CandidateEvent[];
  analysis_runs: AnalysisRun[];
};

export type AnalysisSummary = {
  document_id: string;
  analysis_run: AnalysisRun;
  note: Note | null;
  candidate_events: CandidateEvent[];
};

export type CalendarRecord = {
  id: string;
  user_id: string;
  candidate_event_id: string;
  google_event_id: string;
  created_at: string;
  updated_at: string;
};

export type DriveArchiveStatus = {
  document_id: string;
  drive_file_id: string | null;
  drive_folder_id: string | null;
  archived: boolean;
};

export type AssistantAction =
  | "summarize"
  | "extract_key_points"
  | "extract_schedule_events"
  | "archive_file"
  | "save_notes";
