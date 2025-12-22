import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import type { SortDirection } from "../types/common";
import { PAGINATION } from "../constants";

const { MIN_LIMIT, MAX_LIMIT, MIN_PAGE } = PAGINATION;

/**
 * Safely parse integer from string with fallback and clamping.
 */
function parseIntSafe(
  value: string | null,
  fallback: number,
  min?: number,
  max?: number
): number {
  if (!value) return fallback;

  const parsed = parseInt(value, 10);
  if (Number.isNaN(parsed)) return fallback;

  let result = parsed;
  if (min !== undefined) result = Math.max(result, min);
  if (max !== undefined) result = Math.min(result, max);

  return result;
}

interface UseTableParamsOptions<TSortField extends string> {
  /** Valid sort fields for validation */
  validSortFields?: readonly TSortField[];
  /** Default rows per page (default: 10, clamped to 1-200) */
  defaultRowsPerPage?: number;
}

interface UseTableParamsReturn<TSortField extends string> {
  // Pagination
  page: number;
  rowsPerPage: number;
  setPage: (page: number) => void;
  setRowsPerPage: (rowsPerPage: number) => void;

  // Search
  searchInput: string;
  setSearchInput: (search: string) => void;

  // Sort
  sortBy: TSortField | undefined;
  sortDir: SortDirection;
  handleSort: (column: TSortField) => void;

  // Computed params for API
  params: {
    limit: number;
    offset: number;
    search: string | undefined;
    sortBy: TSortField | undefined;
    sortDir: SortDirection | undefined;
  };
}

/**
 * Custom hook for managing table state (pagination, search, sort) synced with URL.
 * Supports 3-state sorting: asc → desc → clear
 *
 * - Handles invalid URL params gracefully (e.g., ?page=abc → falls back to 0)
 * - Clamps limit to backend constraints (1-200)
 */
export function useTableParams<TSortField extends string>(
  options: UseTableParamsOptions<TSortField> = {}
): UseTableParamsReturn<TSortField> {
  const { validSortFields, defaultRowsPerPage = 10 } = options;
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse and validate URL params with safe fallbacks
  const page = parseIntSafe(searchParams.get("page"), 0, MIN_PAGE);
  const rowsPerPage = parseIntSafe(
    searchParams.get("limit"),
    defaultRowsPerPage,
    MIN_LIMIT,
    MAX_LIMIT
  );
  const searchInput = searchParams.get("search") || "";
  const sortByParam = searchParams.get("sort_by") as TSortField | null;
  const sortDirParam = searchParams.get("sort_dir") as SortDirection | null;

  // Validate sort field
  const sortBy = useMemo(() => {
    if (!sortByParam) return undefined;
    if (validSortFields && !validSortFields.includes(sortByParam)) {
      return undefined;
    }
    return sortByParam;
  }, [sortByParam, validSortFields]);

  const sortDir: SortDirection =
    sortDirParam === "asc" || sortDirParam === "desc" ? sortDirParam : "asc";

  // Update URL helper
  const updateParams = useCallback(
    (updates: Record<string, string | undefined>) => {
      setSearchParams(
        (prev) => {
          const newParams = new URLSearchParams(prev);
          Object.entries(updates).forEach(([key, value]) => {
            if (value === undefined || value === "") {
              newParams.delete(key);
            } else {
              newParams.set(key, value);
            }
          });
          return newParams;
        },
        { replace: true }
      );
    },
    [setSearchParams]
  );

  // Setters
  const setPage = useCallback(
    (newPage: number) => {
      const safePage = Math.max(newPage, MIN_PAGE);
      updateParams({ page: safePage === 0 ? undefined : String(safePage) });
    },
    [updateParams]
  );

  const setRowsPerPage = useCallback(
    (newRowsPerPage: number) => {
      // Clamp to backend constraints
      const safeLimit = Math.min(Math.max(newRowsPerPage, MIN_LIMIT), MAX_LIMIT);
      updateParams({
        limit:
          safeLimit === defaultRowsPerPage ? undefined : String(safeLimit),
        page: undefined, // Reset page when changing rows per page
      });
    },
    [updateParams, defaultRowsPerPage]
  );

  const setSearchInput = useCallback(
    (search: string) => {
      updateParams({
        search: search || undefined,
        page: undefined, // Reset page when searching
      });
    },
    [updateParams]
  );

  // 3-state sort handler: asc → desc → clear
  const handleSort = useCallback(
    (column: TSortField) => {
      if (sortBy === column) {
        if (sortDir === "asc") {
          updateParams({ sort_dir: "desc", page: undefined });
        } else {
          // Clear sort
          updateParams({
            sort_by: undefined,
            sort_dir: undefined,
            page: undefined,
          });
        }
      } else {
        updateParams({
          sort_by: column,
          sort_dir: "asc",
          page: undefined,
        });
      }
    },
    [sortBy, sortDir, updateParams]
  );

  // Computed params for API calls
  const params = useMemo(
    () => ({
      limit: rowsPerPage,
      offset: page * rowsPerPage,
      search: searchInput || undefined,
      sortBy,
      sortDir: sortBy ? sortDir : undefined,
    }),
    [page, rowsPerPage, searchInput, sortBy, sortDir]
  );

  return {
    page,
    rowsPerPage,
    setPage,
    setRowsPerPage,
    searchInput,
    setSearchInput,
    sortBy,
    sortDir,
    handleSort,
    params,
  };
}
