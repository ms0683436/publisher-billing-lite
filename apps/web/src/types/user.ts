export interface User {
  id: number;
  username: string;
}

export interface UserDetail extends User {
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  users: User[];
  total: number;
  limit: number;
  offset: number;
}
