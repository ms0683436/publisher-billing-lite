import type { AuthUser, LoginRequest, TokenResponse } from "../types";

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
    credentials: "include", // Include cookies for refresh token
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(errorBody || "Login failed");
  }

  return response.json();
}

export async function refresh(): Promise<TokenResponse> {
  const response = await fetch("/api/v1/auth/refresh", {
    method: "POST",
    credentials: "include", // Include cookies for refresh token
  });

  if (!response.ok) {
    throw new Error("Token refresh failed");
  }

  return response.json();
}

export async function logout(): Promise<void> {
  await fetch("/api/v1/auth/logout", {
    method: "POST",
    credentials: "include",
  });
}

export async function getCurrentUser(accessToken: string): Promise<AuthUser> {
  const response = await fetch("/api/v1/auth/me", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get current user");
  }

  return response.json();
}
