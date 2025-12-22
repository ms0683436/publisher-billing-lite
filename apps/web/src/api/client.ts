// In-memory token storage (more secure than localStorage - not accessible to XSS)
let accessToken: string | null = null;

// Token storage functions
export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string): void {
  accessToken = token;
}

export function clearAccessToken(): void {
  accessToken = null;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Event system for auth state changes
type AuthEventListener = () => void;
const authEventListeners = new Set<AuthEventListener>();

export function onAuthFailure(listener: AuthEventListener): () => void {
  authEventListeners.add(listener);
  return () => authEventListeners.delete(listener);
}

function emitAuthFailure(): void {
  authEventListeners.forEach((listener) => listener());
}

// Token refresh with proper race condition handling
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const response = await fetch("/api/v1/auth/refresh", {
    method: "POST",
    credentials: "include", // Include cookies for refresh token
  });

  if (!response.ok) {
    clearAccessToken();
    emitAuthFailure();
    return null;
  }

  const data = await response.json();
  setAccessToken(data.access_token);
  return data.access_token;
}

async function getRefreshedToken(): Promise<string | null> {
  // If a refresh is already in progress, wait for it
  if (refreshPromise) {
    return refreshPromise;
  }

  // Start a new refresh and store the promise
  refreshPromise = refreshAccessToken().finally(() => {
    // Clear the promise after a short delay to allow all pending requests
    // to get the result before we allow new refresh attempts
    setTimeout(() => {
      refreshPromise = null;
    }, 100);
  });

  return refreshPromise;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint;
  const token = getAccessToken();

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

  // If unauthorized and we had a token, try to refresh
  if (response.status === 401 && token) {
    const newToken = await getRefreshedToken();

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
    } else {
      // Refresh failed
      throw new ApiError(401, "Authentication required");
    }
  }

  if (!response.ok) {
    const errorBody = await response.text();
    let errorMessage = errorBody || response.statusText;

    // Try to parse JSON and extract detail field
    if (errorBody) {
      try {
        const errorJson = JSON.parse(errorBody);
        if (errorJson.detail) {
          errorMessage = errorJson.detail;
        }
      } catch {
        // Not JSON, use raw text
      }
    }

    throw new ApiError(response.status, errorMessage);
  }

  // Handle 204 No Content responses
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}
