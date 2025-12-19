/**
 * Build URL query string from params object.
 * Filters out undefined/null values and converts numbers to strings.
 */
function buildQueryString(
  params: Record<string, string | number | undefined | null>
): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  }

  return searchParams.toString();
}

/**
 * Build full URL with query string.
 */
export function buildUrl(
  path: string,
  params: Record<string, string | number | undefined | null>
): string {
  const query = buildQueryString(params);
  return query ? `${path}?${query}` : path;
}
