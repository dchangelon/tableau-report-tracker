import { ExternalLink, Plus, Star } from "lucide-react";
import { cn } from "../lib/utils";
import type { Report } from "../types";

interface ReportCardProps {
  report: Report;
  onRequestChange?: (reportId: string) => void;
  isFavorite?: boolean;
  onToggleFavorite?: (reportId: string) => void;
}

export function ReportCard({ report, onRequestChange, isFavorite = false, onToggleFavorite }: ReportCardProps) {
  return (
    <a
      href={report.webUrl ?? "#"}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "block bg-white rounded-lg border border-gray-200 shadow-sm p-4",
        // P1.3 - Consistent hover states with duration-200
        "hover:shadow-lg hover:border-blue-300 transition-all duration-200",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 line-clamp-2">{report.name}</h3>
        {/* P2.2 - aria-hidden for decorative icon with proper label via link text */}
        <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0" aria-hidden="true" />
      </div>

      {report.description && (
        <p className="text-sm text-gray-500 line-clamp-2 mt-1">{report.description}</p>
      )}

      {/* Owner and favorite button */}
      <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
        <span>Owner: {report.ownerName ?? "Unknown"}</span>
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onToggleFavorite?.(report.id);
          }}
          className={cn(
            "flex items-center gap-1 px-2 py-1 rounded transition-colors duration-200",
            isFavorite
              ? "text-yellow-600 hover:text-yellow-700 bg-yellow-50"
              : "text-gray-400 hover:text-yellow-600 hover:bg-yellow-50"
          )}
          aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
        >
          <Star className={cn("w-4 h-4", isFavorite && "fill-current")} aria-hidden="true" />
        </button>
      </div>

      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onRequestChange?.(report.id);
        }}
        className="mt-3 w-full py-2 text-sm font-medium text-white bg-blue-500 rounded-lg
                   hover:bg-blue-600 transition-colors duration-200
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                   inline-flex items-center justify-center gap-1"
      >
        <Plus className="w-4 h-4" aria-hidden="true" />
        Request Change
      </button>
    </a>
  );
}
