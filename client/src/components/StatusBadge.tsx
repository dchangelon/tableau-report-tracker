import { Clock, Eye, Loader2, MessageSquare, CheckCircle, Pause } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../lib/utils";
import type { RequestStatus } from "../types";

interface StatusBadgeProps {
  status: RequestStatus;
  className?: string;
}

const statusConfig: Record<RequestStatus, { label: string; color: string; icon: LucideIcon }> = {
  "Change Request Queue": {
    label: "Queued",
    color: "bg-gray-100 text-gray-700",
    icon: Clock,
  },
  "Reviewing and Planning": {
    label: "In Review",
    color: "bg-purple-100 text-purple-700",
    icon: Eye,
  },
  "In Progress": {
    label: "In Progress",
    color: "bg-blue-100 text-blue-700",
    icon: Loader2,
  },
  "Pending Review": {
    label: "Pending Review",
    color: "bg-yellow-100 text-yellow-700",
    icon: MessageSquare,
  },
  "Completed": {
    label: "Completed",
    color: "bg-green-100 text-green-700",
    icon: CheckCircle,
  },
  "On Hold": {
    label: "On Hold",
    color: "bg-orange-100 text-orange-700",
    icon: Pause,
  },
  "Unknown": {
    label: "Unknown",
    color: "bg-gray-100 text-gray-500",
    icon: Clock,
  },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig["Unknown"];
  const Icon = config.icon;
  const isAnimated = status === "In Progress";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium",
        config.color,
        className
      )}
    >
      <Icon className={cn("w-3 h-3", isAnimated && "animate-spin")} aria-hidden="true" />
      {config.label}
    </span>
  );
}
