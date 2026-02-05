/**
 * Report types matching backend API.
 *
 * IMPORTANT: The Flask API returns camelCase field names (e.g., projectPath, ownerName).
 * This is due to Flask's default JSON serialization. Always verify field names match
 * the actual API response before adding new fields.
 *
 * To check API response format: curl http://localhost:5000/api/reports | head -c 500
 */
export interface Report {
  id: string;
  name: string;
  description: string | null;
  projectName: string;
  projectPath: string;
  ownerName: string | null;
  ownerEmail: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  webUrl: string | null;
  viewCount: number;
}

export interface ReportsResponse {
  success: boolean;
  data: Report[];
  total: number;
}

export interface ReportDetailResponse {
  success: boolean;
  data: Report & {
    views: ReportView[];
  };
}

export interface ReportView {
  id: string;
  name: string;
  contentUrl: string;
}

export interface ProjectsResponse {
  success: boolean;
  data: string[];
  total: number;
}

// Health check
export interface HealthResponse {
  status: string;
  tableauConfigured: boolean;
}

// Request status based on Trello list
export type RequestStatus =
  | "Change Request Queue"
  | "Reviewing and Planning"
  | "In Progress"
  | "Pending Review"
  | "Completed"
  | "On Hold"
  | "Unknown";

export type RequestType = "issue" | "enhancement" | "other";
export type Priority = "low" | "medium" | "high";

// Request summary (from GET /api/requests)
export interface RequestSummary {
  id: string;
  title: string;
  status: RequestStatus;
  trelloUrl: string;
  updatedAt: string;
  checklistProgress: number;
}

// Request details (from GET /api/requests/:id)
export interface RequestDetails {
  id: string;
  title: string;
  description: string;
  status: RequestStatus;
  trelloUrl: string;
  updatedAt: string;
  reportName: string;
  reportId: string;
  requestType: RequestType;
  priority: Priority;
  requesterEmail: string;
  checklistProgress: number;
  checklistItems: ChecklistItem[];
}

export interface ChecklistItem {
  id: string;
  name: string;
  completed: boolean;
}

export interface CreateRequestPayload {
  report_id: string;
  report_name: string;
  title: string;
  description: string;
  request_type: RequestType;
  priority: Priority;
  requester_email: string;
}

// API Responses
export interface RequestsResponse {
  success: boolean;
  data: RequestSummary[];
  total: number;
}

export interface RequestDetailsResponse {
  success: boolean;
  data: RequestDetails;
}

export interface CreateRequestResponse {
  success: boolean;
  data: {
    id: string;
    title: string;
    trelloUrl: string;
  };
  message: string;
}

// API Error
export interface APIError {
  success: false;
  error: string;
}
