import type { Report } from "../types";

export interface FolderNode {
  name: string;
  path: string;
  reportCount: number;
  children: FolderNode[];
}

// Internal type used during tree building
interface BuildNode {
  name: string;
  path: string;
  reportCount: number;
  childrenMap: Map<string, BuildNode>;
}

/**
 * Build a folder tree from report project paths.
 * Example paths: "3. Academic Reports/Surveys", "9. Compliance Reports/ABHES Visitation"
 */
export function buildFolderTree(reports: Report[]): FolderNode[] {
  const rootMap = new Map<string, BuildNode>();

  for (const report of reports) {
    // Skip reports without a valid project path
    if (!report.projectPath) continue;
    
    const parts = report.projectPath.split("/").filter(Boolean);
    let currentMap = rootMap;
    let currentPath = "";

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      currentPath = currentPath ? `${currentPath}/${part}` : part;

      // Get or create node at this level
      if (!currentMap.has(part)) {
        currentMap.set(part, {
          name: part,
          path: currentPath,
          reportCount: 0,
          childrenMap: new Map(),
        });
      }

      const node = currentMap.get(part)!;

      // Count reports at their actual folder level (leaf of path)
      if (i === parts.length - 1) {
        node.reportCount++;
      }

      // Move down to children for next iteration
      currentMap = node.childrenMap;
    }
  }

  // Convert internal build nodes to clean FolderNode objects
  return convertToFolderNodes(rootMap);
}

function convertToFolderNodes(map: Map<string, BuildNode>): FolderNode[] {
  return Array.from(map.values())
    .map((node): FolderNode => ({
      name: node.name,
      path: node.path,
      reportCount: node.reportCount,
      children: convertToFolderNodes(node.childrenMap),
    }))
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
}

/**
 * Get total report count for a folder (including all subfolders)
 */
export function getTotalReportCount(folder: FolderNode): number {
  return (
    folder.reportCount +
    folder.children.reduce((sum, child) => sum + getTotalReportCount(child), 0)
  );
}

/**
 * Filter reports by folder path (only reports directly in this folder, not subfolders)
 */
export function filterReportsByFolder(
  reports: Report[],
  folderPath: string | null
): Report[] {
  if (!folderPath) return reports;
  return reports.filter((r) => r.projectPath === folderPath);
}

/**
 * Find a folder node by its path in the tree
 */
export function findFolderByPath(
  tree: FolderNode[],
  path: string
): FolderNode | null {
  for (const folder of tree) {
    if (folder.path === path) return folder;
    if (path.startsWith(folder.path + "/")) {
      const found = findFolderByPath(folder.children, path);
      if (found) return found;
    }
  }
  return null;
}

/**
 * Get immediate child folders for a given path
 * If parentPath is null, returns top-level folders
 */
export function getImmediateChildren(
  tree: FolderNode[],
  parentPath: string | null
): FolderNode[] {
  if (!parentPath) return tree;
  const parent = findFolderByPath(tree, parentPath);
  return parent?.children ?? [];
}

/**
 * Parse a folder path into breadcrumb segments
 * "3. Academic Reports/Surveys" -> [
 *   { label: "3. Academic Reports", path: "3. Academic Reports" },
 *   { label: "Surveys", path: "3. Academic Reports/Surveys" }
 * ]
 */
export interface BreadcrumbSegment {
  label: string;
  path: string;
}

export function parseBreadcrumbPath(path: string | null): BreadcrumbSegment[] {
  if (!path) return [];

  const parts = path.split("/").filter(Boolean);
  const segments: BreadcrumbSegment[] = [];
  let currentPath = "";

  for (const part of parts) {
    currentPath = currentPath ? `${currentPath}/${part}` : part;
    segments.push({ label: part, path: currentPath });
  }

  return segments;
}
