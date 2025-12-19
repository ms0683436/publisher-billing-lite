/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import type { AuthUser, LoginRequest } from "../types";
import {
  login as apiLogin,
  logout as apiLogout,
  refresh as apiRefresh,
  getCurrentUser,
} from "../api/auth";
import {
  setAccessToken,
  clearAccessToken,
  onAuthFailure,
} from "../api/client";

export interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = user !== null;

  // Try to restore session on mount using refresh token cookie
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Try to get new access token using refresh token cookie
        const response = await apiRefresh();
        setAccessToken(response.access_token);

        // Get user info with the new token
        const currentUser = await getCurrentUser(response.access_token);
        setUser(currentUser);
      } catch {
        // No valid session, user needs to login
        clearAccessToken();
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  // Listen for auth failures (token refresh failed)
  useEffect(() => {
    const unsubscribe = onAuthFailure(() => {
      setUser(null);
    });
    return unsubscribe;
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    const response = await apiLogin(credentials);
    setAccessToken(response.access_token);

    // Get user info after login
    const currentUser = await getCurrentUser(response.access_token);
    setUser(currentUser);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      clearAccessToken();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
