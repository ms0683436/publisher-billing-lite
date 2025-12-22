// Pagination constraints - match backend constraints from deps.py
export const PAGINATION = {
  MIN_LIMIT: 1,
  MAX_LIMIT: 200,
  MIN_PAGE: 0,
  DEFAULT_ROWS_PER_PAGE: 10,
} as const;

// Currency display
export const CURRENCY = {
  DEFAULT_PREFIX: "$",
  LOCALE: "en-US",
} as const;

// Validation patterns
export const VALIDATION = {
  DECIMAL_PATTERN: /^-?\d*\.?\d{0,2}$/,
} as const;
