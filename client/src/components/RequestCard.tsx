import { Clock } from "lucide-react";
import { cn } from "../lib/utils";
import { StatusBadge } from "./StatusBadge";
import { ProgressBar } from "./ProgressBar";
import type { RequestSummary } from "../types";

interface RequestCardProps {
  request: RequestSummary;
  onClick?: () => void;
  className?: string;
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}

export function RequestCard({ request, onClick, className }: RequestCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow",
        onClick && "cursor-pointer",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <h3 className="text-sm font-medium text-gray-900 line-clamp-2 flex-1">
          {request.title}
        </h3>
        <StatusBadge status={request.status} />
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <ProgressBar progress={request.checklistProgress} />
      </div>

      {/* Footer */}
      <div className="flex items-center text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{formatRelativeTime(request.updatedAt)}</span>
        </div>
      </div>
    </div>
  );
}

// Skeleton loader for RequestCard
export function RequestCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="h-4 bg-gray-200 rounded w-3/4" />
        <div className="h-5 bg-gray-200 rounded w-16" />
      </div>
      <div className="mb-3">
        <div className="h-2 bg-gray-200 rounded w-full mb-1" />
        <div className="h-2 bg-gray-200 rounded w-1/2" />
      </div>
      <div className="flex items-center justify-between">
        <div className="h-3 bg-gray-200 rounded w-16" />
        <div className="h-3 bg-gray-200 rounded w-20" />
      </div>
    </div>
  );
}
