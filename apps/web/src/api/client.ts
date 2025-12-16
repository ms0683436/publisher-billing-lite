const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const ACCESS_TOKEN_KEY = "access_token";

// Token storage functions
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Flag to prevent multiple refresh attempts
let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "include", // Include cookies for refresh token
  });

  if (!response.ok) {
    clearAccessToken();
    throw new ApiError(response.status, "Token refresh failed");
  }

  const data = await response.json();
  setAccessToken(data.access_token);
  return data.access_token;
}

async function getValidAccessToken(): Promise<string | null> {
  const token = getAccessToken();
  if (!token) return null;
  return token;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = await getValidAccessToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  let response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Include cookies
  });

  // If unauthorized, try to refresh token and retry
  if (response.status === 401 && token) {
    // Prevent multiple simultaneous refresh attempts
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = refreshAccessToken().finally(() => {
        isRefreshing = false;
        refreshPromise = null;
      });
    }

    try {
      const newToken = await refreshPromise;
      if (newToken) {
        // Retry the original request with new token
        const retryHeaders: HeadersInit = {
          "Content-Type": "application/json",
          ...options.headers,
          Authorization: `Bearer ${newToken}`,
        };

        response = await fetch(url, {
          ...options,
          headers: retryHeaders,
          credentials: "include",
        });
      }
    } catch {
      // Refresh failed, throw the original 401 error
      throw new ApiError(401, "Authentication required");
    }
  }

  if (!response.ok) {
    const errorBody = await response.text();
    throw new ApiError(response.status, errorBody || response.statusText);
  }

  // Handle 204 No Content responses
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}
