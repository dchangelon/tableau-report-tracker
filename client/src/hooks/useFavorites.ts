import { useState, useEffect } from "react";

const FAVORITES_KEY = "tableau-report-favorites";

/**
 * Custom hook for managing favorite reports using localStorage.
 */
export function useFavorites() {
  const [favorites, setFavorites] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem(FAVORITES_KEY);
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  // Persist to localStorage whenever favorites change
  useEffect(() => {
    try {
      localStorage.setItem(FAVORITES_KEY, JSON.stringify(Array.from(favorites)));
    } catch (error) {
      console.error("Failed to save favorites:", error);
    }
  }, [favorites]);

  const toggleFavorite = (reportId: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(reportId)) {
        next.delete(reportId);
      } else {
        next.add(reportId);
      }
      return next;
    });
  };

  const isFavorite = (reportId: string) => favorites.has(reportId);

  return {
    favorites,
    toggleFavorite,
    isFavorite,
  };
}
