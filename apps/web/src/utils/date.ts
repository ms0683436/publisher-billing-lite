/**
 * Date formatting utilities for displaying timestamps in user's local timezone
 */

/**
 * Parse a date string from the API
 * API may return with or without timezone; treat missing as UTC
 */
function parseAsUTC(dateString: string): Date {
  // If already has timezone info (Z or +/-), parse directly
  if (dateString.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(dateString)) {
    return new Date(dateString);
  }
  // Otherwise, append Z to treat as UTC (backward compatibility)
  return new Date(dateString + "Z");
}

const MINUTE = 60;
const HOUR = MINUTE * 60;
const DAY = HOUR * 24;
const WEEK = DAY * 7;
const MONTH = DAY * 30;
const YEAR = DAY * 365;

/**
 * Format a date string as relative time (e.g., "2 hours ago")
 * Automatically uses the user's browser timezone
 */
export function formatRelativeTime(dateString: string): string {
  const date = parseAsUTC(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  // Handle future dates
  if (diffInSeconds < 0) {
    return formatFullDate(dateString);
  }

  // Just now (less than 1 minute)
  if (diffInSeconds < MINUTE) {
    return "just now";
  }

  // Minutes ago
  if (diffInSeconds < HOUR) {
    const minutes = Math.floor(diffInSeconds / MINUTE);
    return `${minutes} ${minutes === 1 ? "minute" : "minutes"} ago`;
  }

  // Hours ago
  if (diffInSeconds < DAY) {
    const hours = Math.floor(diffInSeconds / HOUR);
    return `${hours} ${hours === 1 ? "hour" : "hours"} ago`;
  }

  // Days ago
  if (diffInSeconds < WEEK) {
    const days = Math.floor(diffInSeconds / DAY);
    return `${days} ${days === 1 ? "day" : "days"} ago`;
  }

  // Weeks ago
  if (diffInSeconds < MONTH) {
    const weeks = Math.floor(diffInSeconds / WEEK);
    return `${weeks} ${weeks === 1 ? "week" : "weeks"} ago`;
  }

  // Months ago
  if (diffInSeconds < YEAR) {
    const months = Math.floor(diffInSeconds / MONTH);
    return `${months} ${months === 1 ? "month" : "months"} ago`;
  }

  // Years ago
  const years = Math.floor(diffInSeconds / YEAR);
  return `${years} ${years === 1 ? "year" : "years"} ago`;
}

/**
 * Format a date string as full localized date/time with timezone
 * Uses Intl.DateTimeFormat for proper localization
 */
export function formatFullDate(dateString: string): string {
  const date = parseAsUTC(dateString);

  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(date);
}
