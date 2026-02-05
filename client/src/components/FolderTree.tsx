import { useState } from "react";
import { Folder, FolderOpen, ChevronRight, ChevronDown } from "lucide-react";
import { cn } from "../lib/utils";
import { getTotalReportCount, type FolderNode } from "../lib/folders";

interface FolderItemProps {
  folder: FolderNode;
  selectedFolder: string | null;
  onSelect: (path: string) => void;
  depth: number;
}

export function FolderItem({ folder, selectedFolder, onSelect, depth }: FolderItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasChildren = folder.children.length > 0;
  const isSelected = selectedFolder === folder.path;
  const isParentOfSelected = selectedFolder?.startsWith(folder.path + "/") ?? false;
  const totalCount = getTotalReportCount(folder);

  // Auto-expand if a child is selected
  const shouldExpand = isExpanded || isParentOfSelected;

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-1 py-1.5 rounded text-sm cursor-pointer",
          isSelected
            ? "bg-blue-50 text-blue-700 font-medium"
            : "text-gray-700 hover:bg-gray-50"
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {/* Expand/collapse toggle */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!shouldExpand);
            }}
            className="p-0.5 hover:bg-gray-200 rounded"
            aria-label={shouldExpand ? `Collapse ${folder.name}` : `Expand ${folder.name}`}
            aria-expanded={shouldExpand}
          >
            {shouldExpand ? (
              <ChevronDown className="w-3 h-3" aria-hidden="true" />
            ) : (
              <ChevronRight className="w-3 h-3" aria-hidden="true" />
            )}
          </button>
        ) : (
          <span className="w-4" aria-hidden="true" />
        )}

        {/* Folder icon and name */}
        <button
          onClick={() => onSelect(folder.path)}
          className="flex items-center gap-2 flex-1 min-w-0 text-left"
        >
          {isSelected || shouldExpand ? (
            <FolderOpen className="w-4 h-4 flex-shrink-0 text-blue-500" aria-hidden="true" />
          ) : (
            <Folder className="w-4 h-4 flex-shrink-0 text-gray-500" aria-hidden="true" />
          )}
          <span className="truncate">{folder.name}</span>
          {/* P2.4 - Fixed color contrast: text-gray-400 -> text-gray-500 */}
          <span className="text-xs text-gray-500 flex-shrink-0">{totalCount}</span>
        </button>
      </div>

      {/* Children */}
      {shouldExpand && hasChildren && (
        <div role="group" aria-label={`Subfolders of ${folder.name}`}>
          {folder.children.map((child) => (
            <FolderItem
              key={child.path}
              folder={child}
              selectedFolder={selectedFolder}
              onSelect={onSelect}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}
