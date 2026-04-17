import type {
  AnalysisSummary,
  ApiError,
  AssistantAction,
  CalendarRecord,
  CredentialStatus,
  DocumentDetail,
  DocumentListItem,
  DriveArchiveStatus,
  Note,
  TokenResponse,
  User,
} from "@/lib/types";

type RequestOptions = Omit<RequestInit, "body"> & {
  token?: string | null;
  body?: BodyInit | Record<string, unknown> | null;
};

async function readResponse(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");

  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (
    options.body &&
    typeof options.body === "object" &&
    !(options.body instanceof Blob) &&
    !(options.body instanceof ArrayBuffer)
  ) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  } else if (options.body) {
    body = options.body;
  }

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`/api/backend${path}`, {
    ...options,
    headers,
    body,
  });

  const payload = await readResponse(response);
  if (!response.ok) {
    const error = (typeof payload === "object" && payload
      ? payload
      : {
          code: "request_failed",
          message:
            typeof payload === "string" && payload.trim().length > 0
              ? payload
              : "The request could not be completed. Please try again.",
        }) as ApiError;
    throw error;
  }

  return payload as T;
}

export const authApi = {
  register(payload: { email: string; password: string; full_name?: string | null }) {
    return apiRequest<User>("/auth/register", {
      method: "POST",
      body: payload,
    });
  },
  login(payload: { email: string; password: string }) {
    return apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: payload,
    });
  },
  me(token: string) {
    return apiRequest<User>("/auth/me", { token });
  },
  updateMe(token: string, payload: { full_name?: string | null }) {
    return apiRequest<User>("/auth/me", {
      method: "PATCH",
      token,
      body: payload,
    });
  },
};

export const credentialsApi = {
  status(token: string) {
    return apiRequest<CredentialStatus>("/credentials/status", { token });
  },
  saveLlmKey(token: string, payload: { provider: string; api_key: string }) {
    return apiRequest<CredentialStatus>("/credentials/llm", {
      method: "POST",
      token,
      body: payload,
    });
  },
  googleConnect(token: string) {
    return apiRequest<{ authorization_url: string }>("/credentials/google/connect", {
      method: "POST",
      token,
    });
  },
};

export const documentsApi = {
  list(token: string) {
    return apiRequest<DocumentListItem[]>("/documents", { token });
  },
  detail(token: string, documentId: string) {
    return apiRequest<DocumentDetail>(`/documents/${documentId}`, { token });
  },
  upload(token: string, file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return apiRequest<DocumentListItem>("/documents/upload", {
      method: "POST",
      token,
      body: formData,
    });
  },
  analyze(
    token: string,
    documentId: string,
    payload: {
      requested_actions?: AssistantAction[];
      archive_to_drive?: boolean;
      save_notes?: boolean;
    },
  ) {
    return apiRequest<AnalysisSummary>(`/documents/${documentId}/analyze`, {
      method: "POST",
      token,
      body: payload,
    });
  },
};

export const assistantApi = {
  execute(
    token: string,
    payload: {
      document_id: string;
      requested_actions?: AssistantAction[];
      archive_to_drive?: boolean;
      save_notes?: boolean;
    },
  ) {
    return apiRequest<AnalysisSummary>("/assistant/execute", {
      method: "POST",
      token,
      body: payload,
    });
  },
};

export const notesApi = {
  list(token: string) {
    return apiRequest<Note[]>("/notes", { token });
  },
  save(
    token: string,
    payload: {
      document_id: string;
      summary: string;
      key_points: string[];
      action_items: string[];
    },
  ) {
    return apiRequest<Note>("/notes/save", {
      method: "POST",
      token,
      body: payload,
    });
  },
};

export const calendarApi = {
  extractEvents(token: string, documentId: string) {
    return apiRequest<DocumentDetail["candidate_events"]>("/calendar/extract-events", {
      method: "POST",
      token,
      body: { document_id: documentId },
    });
  },
  createEvents(token: string, candidateEventIds: string[]) {
    return apiRequest<CalendarRecord[]>("/calendar/create-events", {
      method: "POST",
      token,
      body: { candidate_event_ids: candidateEventIds },
    });
  },
};

export const driveApi = {
  archive(token: string, documentId: string) {
    return apiRequest<DriveArchiveStatus>("/drive/archive", {
      method: "POST",
      token,
      body: { document_id: documentId },
    });
  },
  status(token: string, documentId: string) {
    return apiRequest<DriveArchiveStatus>(`/drive/files/${documentId}`, { token });
  },
};
