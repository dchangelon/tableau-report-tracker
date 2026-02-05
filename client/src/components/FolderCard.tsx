import { Folder, ChevronRight } from "lucide-react";
import { cn } from "../lib/utils";
import type { FolderNode } from "../lib/folders";
import { getTotalReportCount } from "../lib/folders";

interface FolderCardProps {
  folder: FolderNode;
  onSelect: (path: string) => void;
}

export function FolderCard({ folder, onSelect }: FolderCardProps) {
  const totalReports = getTotalReportCount(folder);
  const hasSubfolders = folder.children.length > 0;

  return (
    <button
      onClick={() => onSelect(folder.path)}
      className={cn(
        "w-full text-left bg-white rounded-lg border border-gray-200 shadow-sm p-4",
        // P1.3 - Consistent hover states with duration-200
        "hover:shadow-lg hover:border-blue-300 transition-all duration-200",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
        "group"
      )}
    >
      <div className="flex items-start gap-3">
        {/* P1.3 - Consistent transition duration */}
        <div className="p-2 bg-blue-50 rounded-lg group-hover:bg-blue-100 transition-colors duration-200">
          {/* P2.2 - aria-hidden for decorative icon */}
          <Folder className="w-6 h-6 text-blue-500" aria-hidden="true" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900 truncate">
              {folder.name}
            </h3>
            {/* P2.2 - aria-hidden for decorative icon */}
            <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition-colors duration-200" aria-hidden="true" />
          </div>

          <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
            <span>
              {totalReports} {totalReports === 1 ? "report" : "reports"}
            </span>
            {hasSubfolders && (
              <>
                <span className="text-gray-300" aria-hidden="true">|</span>
                <span>
                  {folder.children.length}{" "}
                  {folder.children.length === 1 ? "subfolder" : "subfolders"}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}

interface FolderGridProps {
  folders: FolderNode[];
  onSelect: (path: string) => void;
}

export function FolderGrid({ folders, onSelect }: FolderGridProps) {
  if (folders.length === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {folders.map((folder) => (
        <FolderCard key={folder.path} folder={folder} onSelect={onSelect} />
      ))}
    </div>
  );
}
