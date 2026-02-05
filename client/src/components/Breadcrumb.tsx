import { ChevronRight, Home } from "lucide-react";
import { parseBreadcrumbPath } from "../lib/folders";

interface BreadcrumbProps {
  path: string | null;
  onNavigate: (path: string | null) => void;
}

export function Breadcrumb({ path, onNavigate }: BreadcrumbProps) {
  const segments = parseBreadcrumbPath(path);

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm">
      {/* Home / All Reports */}
      <button
        onClick={() => onNavigate(null)}
        className={`flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100 transition-colors ${
          !path ? "text-gray-900 font-medium" : "text-blue-500 hover:text-blue-600"
        }`}
      >
        <Home className="w-4 h-4" />
        <span>All Reports</span>
      </button>

      {/* Path segments */}
      {segments.map((segment, index) => {
        const isLast = index === segments.length - 1;

        return (
          <span key={segment.path} className="flex items-center gap-1">
            <ChevronRight className="w-4 h-4 text-gray-400" />
            {isLast ? (
              <span className="px-2 py-1 text-gray-900 font-medium">
                {segment.label}
              </span>
            ) : (
              <button
                onClick={() => onNavigate(segment.path)}
                className="px-2 py-1 text-blue-500 hover:text-blue-600 hover:bg-gray-100 rounded transition-colors"
              >
                {segment.label}
              </button>
            )}
          </span>
        );
      })}
    </nav>
  );
}
