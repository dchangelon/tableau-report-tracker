import { cn } from "../lib/utils";

interface ProgressBarProps {
  progress: number; // 0-100
  className?: string;
  showLabel?: boolean;
}

export function ProgressBar({ progress, className, showLabel = true }: ProgressBarProps) {
  // Clamp progress between 0 and 100
  const clampedProgress = Math.max(0, Math.min(100, progress));

  // Determine color based on progress
  const getProgressColor = (value: number) => {
    if (value >= 100) return "bg-green-500";
    if (value >= 60) return "bg-blue-500";
    if (value >= 30) return "bg-yellow-500";
    return "bg-gray-400";
  };

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between mb-1">
        {showLabel && (
          <span className="text-xs text-gray-500">Progress</span>
        )}
        <span className="text-xs font-medium text-gray-700">{clampedProgress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300",
            getProgressColor(clampedProgress)
          )}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
}
