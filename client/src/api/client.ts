import type {
  ReportsResponse,
  ReportDetailResponse,
  ProjectsResponse,
  HealthResponse,
  CreateRequestPayload,
  CreateRequestResponse,
  RequestsResponse,
  RequestDetailsResponse,
} from "../types";

const API_BASE = "/api";

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Request failed" }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

// Health check
export async function getHealth(): Promise<HealthResponse> {
  return fetchAPI<HealthResponse>("/health");
}

// Reports
export async function getReports(): Promise<ReportsResponse> {
  return fetchAPI<ReportsResponse>("/reports");
}

export async function getReportById(id: string): Promise<ReportDetailResponse> {
  return fetchAPI<ReportDetailResponse>(`/reports/${id}`);
}

export async function getProjects(): Promise<ProjectsResponse> {
  return fetchAPI<ProjectsResponse>("/reports/projects");
}

// Requests
export async function getRequests(email: string): Promise<RequestsResponse> {
  return fetchAPI<RequestsResponse>(`/requests?email=${encodeURIComponent(email)}`);
}

export async function getRequestById(cardId: string): Promise<RequestDetailsResponse> {
  return fetchAPI<RequestDetailsResponse>(`/requests/${cardId}`);
}

export async function createRequest(payload: CreateRequestPayload): Promise<CreateRequestResponse> {
  return fetchAPI<CreateRequestResponse>("/requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
