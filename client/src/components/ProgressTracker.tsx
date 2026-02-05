import { Check } from "lucide-react";
import { cn } from "../lib/utils";
import { ProgressBar } from "./ProgressBar";
import type { ChecklistItem } from "../types";

interface ProgressTrackerProps {
  items: ChecklistItem[];
  progress: number;
  className?: string;
}

export function ProgressTracker({ items, progress, className }: ProgressTrackerProps) {
  const completedCount = items.filter((item) => item.completed).length;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Progress Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            Overall Progress
          </span>
          <span className="text-sm text-gray-500">
            {completedCount} of {items.length} completed
          </span>
        </div>
        <ProgressBar progress={progress} showLabel={false} />
      </div>

      {/* Checklist Items */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700">Workflow Steps</h4>
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li
              key={item.id}
              className={cn(
                "flex items-center gap-3 p-3 rounded-lg border",
                item.completed
                  ? "bg-green-50 border-green-200"
                  : "bg-white border-gray-200"
              )}
            >
              {/* Step Number / Check Icon */}
              <div
                className={cn(
                  "flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium",
                  item.completed
                    ? "bg-green-500 text-white"
                    : "bg-gray-100 text-gray-500"
                )}
              >
                {item.completed ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <span>{index + 1}</span>
                )}
              </div>

              {/* Item Name */}
              <span
                className={cn(
                  "text-sm",
                  item.completed ? "text-green-700" : "text-gray-700"
                )}
              >
                {item.name}
              </span>

              {/* Status Indicator */}
              {item.completed && (
                <span className="ml-auto text-xs text-green-600 font-medium">
                  Done
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
