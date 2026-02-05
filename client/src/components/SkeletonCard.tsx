export function SkeletonCard() {
  return (
    <div className="animate-pulse bg-white rounded-lg border border-gray-200 p-4">
      <div className="h-5 bg-gray-200 rounded w-3/4 mb-3" />
      <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
      <div className="flex justify-between">
        <div className="h-3 bg-gray-200 rounded w-1/4" />
        <div className="h-3 bg-gray-200 rounded w-1/4" />
      </div>
      <div className="h-8 bg-gray-200 rounded w-full mt-3" />
    </div>
  );
}
