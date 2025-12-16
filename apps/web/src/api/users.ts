import { apiClient } from "./client";
import type { User, UserListResponse } from "../types/user";

export async function fetchUsers(): Promise<UserListResponse> {
  return apiClient<UserListResponse>("/api/v1/users");
}

export async function searchUsers(query: string): Promise<User[]> {
  const response = await apiClient<UserListResponse>(
    `/api/v1/users/search?q=${encodeURIComponent(query)}`
  );
  return response.users;
}
