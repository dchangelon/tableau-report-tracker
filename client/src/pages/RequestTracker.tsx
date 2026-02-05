import { useState, useMemo } from "react";
import { ListTodo, Search, X, ArrowLeft, Loader2 } from "lucide-react";
import { useRequests, useRequest } from "../api/hooks";
import { RequestCard, RequestCardSkeleton } from "../components/RequestCard";
import { StatusBadge } from "../components/StatusBadge";
import { ProgressTracker } from "../components/ProgressTracker";
import { cn } from "../lib/utils";
import type { RequestStatus } from "../types";

// Status filter options
const STATUS_FILTERS: { value: RequestStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "Change Request Queue", label: "Queued" },
  { value: "Reviewing and Planning", label: "In Review" },
  { value: "In Progress", label: "In Progress" },
  { value: "Pending Review", label: "Pending Review" },
  { value: "Completed", label: "Completed" },
  { value: "On Hold", label: "On Hold" },
];

export function RequestTracker() {
  // Email state for fetching user's requests
  const [email, setEmail] = useState("");
  const [submittedEmail, setSubmittedEmail] = useState("");
  const [statusFilter, setStatusFilter] = useState<RequestStatus | "all">("all");
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);

  // Fetch requests for the submitted email
  const { data, isLoading, error, refetch } = useRequests(submittedEmail);
  const requests = data?.data ?? [];

  // Fetch selected request details
  const { data: detailData, isLoading: isLoadingDetail } = useRequest(selectedRequestId || "");
  const selectedRequest = detailData?.data;

  // Filter requests by status
  const filteredRequests = useMemo(() => {
    if (statusFilter === "all") return requests;
    return requests.filter((r) => r.status === statusFilter);
  }, [requests, statusFilter]);

  // Count requests by status for filter badges
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { all: requests.length };
    for (const req of requests) {
      counts[req.status] = (counts[req.status] || 0) + 1;
    }
    return counts;
  }, [requests]);

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setSubmittedEmail(email.trim());
      setSelectedRequestId(null);
    }
  };

  const handleClearEmail = () => {
    setEmail("");
    setSubmittedEmail("");
    setSelectedRequestId(null);
  };

  // If a request is selected, show the detail view
  if (selectedRequestId && selectedRequest) {
    return (
      <div className="space-y-6">
        {/* Back button */}
        <button
          onClick={() => setSelectedRequestId(null)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors duration-200"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          <span>Back to requests</span>
        </button>

        {/* Request Detail Header */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {selectedRequest.title}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Report: {selectedRequest.reportName}
              </p>
            </div>
            <StatusBadge status={selectedRequest.status} />
          </div>

          {/* Request metadata */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4 border-t border-b border-gray-100">
            <div>
              <span className="text-xs text-gray-500">Type</span>
              <p className="text-sm font-medium text-gray-900 capitalize">
                {selectedRequest.requestType.replace("_", " ")}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Priority</span>
              <p className="text-sm font-medium text-gray-900 capitalize">
                {selectedRequest.priority}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Submitted by</span>
              <p className="text-sm font-medium text-gray-900">
                {selectedRequest.requesterEmail}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-500">Last updated</span>
              <p className="text-sm font-medium text-gray-900">
                {new Date(selectedRequest.updatedAt).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Description */}
          {selectedRequest.description && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Description</h3>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">
                {selectedRequest.description}
              </p>
            </div>
          )}
        </div>

        {/* Progress Tracker */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Progress Tracking
          </h3>
          <ProgressTracker
            items={selectedRequest.checklistItems}
            progress={selectedRequest.checklistProgress}
          />
        </div>
      </div>
    );
  }

  // Loading detail view
  if (selectedRequestId && isLoadingDetail) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setSelectedRequestId(null)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors duration-200"
        >
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          <span>Back to requests</span>
        </button>
        <div className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4" />
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-6" />
          <div className="grid grid-cols-4 gap-4 py-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i}>
                <div className="h-3 bg-gray-200 rounded w-12 mb-1" />
                <div className="h-4 bg-gray-200 rounded w-20" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Request Tracker</h2>
        <p className="text-gray-600 mt-1">
          Track the status of your change requests.
        </p>
      </div>

      {/* Email Input */}
      <form onSubmit={handleEmailSubmit} className="flex gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email to view requests..."
            className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {email && (
            <button
              type="button"
              onClick={handleClearEmail}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              aria-label="Clear email"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={!email.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Search
        </button>
      </form>

      {/* Show content only if email is submitted */}
      {submittedEmail && (
        <>
          {/* Status Filters */}
          <div className="flex flex-wrap gap-2">
            {STATUS_FILTERS.map((filter) => {
              const count = statusCounts[filter.value] || 0;
              // Don't show filters with 0 count (except "all")
              if (filter.value !== "all" && count === 0) return null;

              return (
                <button
                  key={filter.value}
                  onClick={() => setStatusFilter(filter.value)}
                  className={cn(
                    // P4.3 - Filter buttons with consistent transitions
                    "px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200",
                    statusFilter === filter.value
                      ? "bg-blue-50 text-blue-700 border border-blue-200"
                      : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
                  )}
                >
                  {filter.label} ({count})
                </button>
              );
            })}
          </div>

          {/* Error State */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
              <p className="font-medium">Failed to load requests</p>
              <p className="text-sm mt-1">{error.message}</p>
              <button
                onClick={() => refetch()}
                className="text-sm text-red-600 hover:text-red-800 mt-2 underline"
              >
                Try again
              </button>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="space-y-4">
              {/* Loading indicator with text */}
              <div className="flex items-center justify-center gap-3 py-4">
                <Loader2 className="w-5 h-5 animate-spin text-blue-600" aria-hidden="true" />
                <span className="text-gray-600 font-medium">Loading your requests...</span>
              </div>

              {/* Skeleton cards */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <RequestCardSkeleton key={i} />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && filteredRequests.length === 0 && (
            <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
              <ListTodo className="w-12 h-12 text-gray-300 mx-auto mb-4" aria-hidden="true" />
              <p className="text-gray-500 font-medium">
                {statusFilter === "all"
                  ? "No requests found"
                  : `No ${STATUS_FILTERS.find((f) => f.value === statusFilter)?.label.toLowerCase()} requests`}
              </p>
              <p className="text-gray-400 text-sm mt-1">
                {statusFilter === "all"
                  ? `No change requests found for ${submittedEmail}`
                  : "Try selecting a different filter"}
              </p>
            </div>
          )}

          {/* Request List */}
          {!isLoading && !error && filteredRequests.length > 0 && (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredRequests.map((request) => (
                <RequestCard
                  key={request.id}
                  request={request}
                  onClick={() => setSelectedRequestId(request.id)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Initial State - No email submitted */}
      {!submittedEmail && (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" aria-hidden="true" />
          <p className="text-gray-500 font-medium">Enter your email to get started</p>
          <p className="text-gray-400 text-sm mt-1">
            View and track all change requests associated with your email
          </p>
        </div>
      )}
    </div>
  );
}
