import { useState, useMemo, useDeferredValue, useEffect, useRef } from "react";
import { FileText, Folder, X, Star } from "lucide-react";
import { toast } from "sonner";
import { useReports, useCreateRequest } from "../api/hooks";
import { cn } from "../lib/utils";
import { buildFolderTree, filterReportsByFolder, getImmediateChildren } from "../lib/folders";
import { useFavorites } from "../hooks/useFavorites";
import { Breadcrumb } from "../components/Breadcrumb";
import { FolderGrid } from "../components/FolderCard";
import { FolderItem } from "../components/FolderTree";
import { SearchBar } from "../components/SearchBar";
import { ReportCard } from "../components/ReportCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { RequestModal } from "../components/RequestModal";
import type { Report, CreateRequestPayload } from "../types";

export function ReportSearch() {
  const [searchQuery, setSearchQuery] = useState("");
  // P1.1 - Use deferred value for smooth filtering during typing
  const deferredQuery = useDeferredValue(searchQuery);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // P4.1 - Mobile sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // P1.4 - Ref for keyboard shortcut
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading, error } = useReports();
  const createRequest = useCreateRequest();
  const { favorites, toggleFavorite, isFavorite } = useFavorites();

  const reports = data?.data ?? [];

  // Special constant for favorites folder
  const FAVORITES_FOLDER = "__favorites__";

  // Check if we're viewing favorites
  const isViewingFavorites = selectedFolder === FAVORITES_FOLDER;

  // Determine if we're at root level (show folders) or inside a folder (show reports)
  const isRootLevel = selectedFolder === null;

  // Build folder tree from reports
  const folderTree = useMemo(() => buildFolderTree(reports), [reports]);

  // Filter folders by search query at root level (using deferred query for smooth UX)
  const filteredFolders = useMemo(() => {
    if (!deferredQuery || !isRootLevel) return folderTree;
    return folderTree.filter((folder) =>
      folder.name.toLowerCase().includes(deferredQuery.toLowerCase())
    );
  }, [folderTree, deferredQuery, isRootLevel]);

  // Get immediate subfolders for current location (not for favorites)
  const currentSubfolders = useMemo(() => {
    if (isViewingFavorites) return []; // No subfolders in favorites view
    return getImmediateChildren(folderTree, selectedFolder);
  }, [folderTree, selectedFolder, isViewingFavorites]);

  // Filter by folder first, then by search query (using deferred query)
  // Only get reports directly in this folder (not subfolders) when we have subfolders
  const folderFilteredReports = useMemo(() => {
    // At root level with search query: search ALL reports
    if (!selectedFolder && deferredQuery) {
      return reports;
    }
    // At root level without search: show folders (no reports)
    if (!selectedFolder) {
      return [];
    }
    if (isViewingFavorites) {
      // Show only favorite reports
      return reports.filter((report) => favorites.has(report.id));
    }
    return filterReportsByFolder(reports, selectedFolder);
  }, [reports, selectedFolder, isViewingFavorites, favorites, deferredQuery]);

  const filteredReports = folderFilteredReports
    .filter((report) => report.name.toLowerCase().includes(deferredQuery.toLowerCase()))
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));

  // Get current folder name for display
  const currentFolderName = isViewingFavorites
    ? "Favorites"
    : isRootLevel && deferredQuery
    ? "Search Results"
    : selectedFolder?.split("/").pop() ?? "All Reports";

  // P1.4 - Keyboard shortcut for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input/textarea
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.key === "/" && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // P4.1 - Close sidebar when navigating on mobile
  const handleFolderSelect = (path: string | null) => {
    setSelectedFolder(path);
    setSidebarOpen(false);
  };

  const handleRequestChange = (reportId: string) => {
    const report = reports.find((r) => r.id === reportId);
    if (report) {
      setSelectedReport(report);
      setIsModalOpen(true);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedReport(null);
  };

  const handleSubmitRequest = async (payload: CreateRequestPayload) => {
    try {
      await createRequest.mutateAsync(payload);
      // P3.3 - Explicit toast duration
      toast.success("Request submitted!", {
        description: "Your change request has been created.",
        duration: 4000,
      });
      handleCloseModal();
    } catch (error) {
      // P3.3 - Longer duration for errors
      toast.error("Failed to submit request", {
        description: error instanceof Error ? error.message : "Please try again.",
        duration: 6000,
      });
      throw error; // Re-throw to keep the form in submitting state
    }
  };

  return (
    <div className="flex gap-6">
      {/* P4.1 - Mobile sidebar toggle */}
      <button
        className="md:hidden fixed bottom-4 right-4 z-40 bg-blue-500 text-white p-3 rounded-full shadow-lg hover:bg-blue-600 transition-colors"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label={sidebarOpen ? "Close folders" : "Open folders"}
      >
        {sidebarOpen ? <X className="w-5 h-5" /> : <Folder className="w-5 h-5" />}
      </button>

      {/* P4.1 - Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 md:hidden animate-backdrop"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Folder Sidebar - P4.1 responsive */}
      <aside
        className={cn(
          "w-72 flex-shrink-0",
          "fixed md:relative inset-y-0 left-0 z-30 md:z-auto",
          "transform md:transform-none transition-transform duration-300 ease-in-out",
          sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          "bg-gray-50 md:bg-transparent p-4 md:p-0"
        )}
      >
        <div className="bg-white rounded-lg border border-gray-200 p-4 sticky top-4 max-h-[calc(100vh-2rem)] overflow-y-auto">
          <h3 className="font-semibold text-gray-900 mb-3">Folders</h3>

          {/* Favorites option */}
          <button
            onClick={() => handleFolderSelect(FAVORITES_FOLDER)}
            className={cn(
              "w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm text-left mb-2",
              isViewingFavorites
                ? "bg-yellow-50 text-yellow-700 font-medium"
                : "text-gray-700 hover:bg-gray-50"
            )}
          >
            <Star className={cn("w-4 h-4", isViewingFavorites && "fill-current")} aria-hidden="true" />
            <span className="flex-1">Favorites</span>
            <span className="text-xs text-gray-500">{favorites.size}</span>
          </button>

          {/* All Reports option */}
          <button
            onClick={() => handleFolderSelect(null)}
            className={cn(
              "w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm text-left mb-2",
              selectedFolder === null
                ? "bg-blue-50 text-blue-700 font-medium"
                : "text-gray-700 hover:bg-gray-50"
            )}
          >
            <Folder className="w-4 h-4" aria-hidden="true" />
            <span className="flex-1">All Reports</span>
            {/* P2.4 - Fixed color contrast */}
            <span className="text-xs text-gray-500">{reports.length}</span>
          </button>

          {/* Loading state */}
          {isLoading && (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="animate-pulse h-6 bg-gray-100 rounded" />
              ))}
            </div>
          )}

          {/* Folder tree */}
          {!isLoading && (
            <div className="space-y-0.5 max-h-[60vh] overflow-y-auto">
              {folderTree.map((folder) => (
                <FolderItem
                  key={folder.path}
                  folder={folder}
                  selectedFolder={selectedFolder}
                  onSelect={handleFolderSelect}
                  depth={0}
                />
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 min-w-0 space-y-4">
        {/* Breadcrumb Navigation */}
        <Breadcrumb path={selectedFolder} onNavigate={handleFolderSelect} />

        <div>
          <h2 className="text-2xl font-bold text-gray-900">{currentFolderName}</h2>
          <p className="text-gray-600 mt-1">
            {isRootLevel && deferredQuery
              ? "Search results from all reports."
              : isRootLevel
              ? "Browse folders to find Tableau reports."
              : isViewingFavorites
              ? "Your favorite reports for quick access."
              : `Browsing reports in this folder.`}
          </p>
        </div>

        {/* Search Bar - P1.4 with ref */}
        <SearchBar
          ref={searchInputRef}
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder={isRootLevel ? "Search all reports..." : `Search in ${currentFolderName}...`}
        />

        {/* Loading State */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            <p className="font-medium">Failed to load reports</p>
            <p className="text-sm mt-1">{error.message}</p>
          </div>
        )}

        {/* Root Level: Show folder cards or search results - P1.2 with fade-in animation */}
        {!isLoading && !error && isRootLevel && !deferredQuery && (
          <div className="animate-fade-in">
            {/* P2.3 - Live region for results count */}
            <p className="text-sm text-gray-500" aria-live="polite" aria-atomic="true">
              {filteredFolders.length} {filteredFolders.length === 1 ? "folder" : "folders"}
              {!searchQuery && ` · ${reports.length} total reports`}
            </p>
            <div className="mt-4">
              <FolderGrid folders={filteredFolders} onSelect={handleFolderSelect} />
            </div>
          </div>
        )}

        {/* Root Level with Search: Show report results - P1.2 with fade-in animation */}
        {!isLoading && !error && isRootLevel && deferredQuery && (
          <div className="animate-fade-in space-y-3">
            {/* P2.3 - Live region for results count */}
            <p className="text-sm text-gray-500" aria-live="polite" aria-atomic="true">
              {filteredReports.length} {filteredReports.length === 1 ? "report" : "reports"}
              {` matching "${searchQuery}"`}
            </p>

            {/* P3.1 - Improved Empty State */}
            {filteredReports.length === 0 && (
              <div className="text-center py-16 bg-gradient-to-b from-gray-50 to-white rounded-lg border border-gray-100">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                  <FileText className="w-8 h-8 text-gray-400" aria-hidden="true" />
                </div>
                <p className="text-gray-600 font-medium">No reports match your search</p>
                <p className="text-gray-500 text-sm mt-2 max-w-xs mx-auto">
                  Try different keywords or check the spelling
                </p>
              </div>
            )}

            {/* Report Grid */}
            {filteredReports.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredReports.map((report) => (
                  <ReportCard
                    key={report.id}
                    report={report}
                    onRequestChange={handleRequestChange}
                    isFavorite={isFavorite(report.id)}
                    onToggleFavorite={toggleFavorite}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Inside a folder: Show subfolders (if any) and reports - P1.2 with fade-in */}
        {!isLoading && !error && !isRootLevel && (
          <div className="animate-fade-in">
            {/* Subfolders section */}
            {currentSubfolders.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-700">
                  Subfolders ({currentSubfolders.length})
                </h3>
                <FolderGrid folders={currentSubfolders} onSelect={handleFolderSelect} />
              </div>
            )}

            {/* Reports section */}
            <div className="space-y-3 mt-4">
              {currentSubfolders.length > 0 && filteredReports.length > 0 && (
                <h3 className="text-sm font-medium text-gray-700">
                  Reports ({filteredReports.length})
                </h3>
              )}

              {/* P2.3 - Live region for results count (when no subfolders) */}
              {currentSubfolders.length === 0 && (
                <p className="text-sm text-gray-500" aria-live="polite" aria-atomic="true">
                  {filteredReports.length} {filteredReports.length === 1 ? "report" : "reports"}
                  {searchQuery && ` matching "${searchQuery}"`}
                </p>
              )}

              {/* P3.1 - Improved Empty State */}
              {filteredReports.length === 0 && currentSubfolders.length === 0 && (
                <div className="text-center py-16 bg-gradient-to-b from-gray-50 to-white rounded-lg border border-gray-100">
                  <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <FileText className="w-8 h-8 text-gray-400" aria-hidden="true" />
                  </div>
                  <p className="text-gray-600 font-medium">
                    {searchQuery ? "No reports match your search" : "This folder is empty"}
                  </p>
                  <p className="text-gray-500 text-sm mt-2 max-w-xs mx-auto">
                    {searchQuery
                      ? "Try different keywords or check the spelling"
                      : "Navigate to a subfolder or try searching"}
                  </p>
                </div>
              )}

              {/* Report Grid */}
              {filteredReports.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredReports.map((report) => (
                    <ReportCard
                      key={report.id}
                      report={report}
                      onRequestChange={handleRequestChange}
                      isFavorite={isFavorite(report.id)}
                      onToggleFavorite={toggleFavorite}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Request Modal */}
      <RequestModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        report={selectedReport}
        onSubmit={handleSubmitRequest}
        isSubmitting={createRequest.isPending}
      />
    </div>
  );
}
