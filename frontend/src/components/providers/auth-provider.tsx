"use client";

import {
  createContext,
  useCallback,
  useMemo,
  startTransition,
  useContext,
  useEffect,
  useState,
} from "react";

import { authApi } from "@/lib/api";
import type { ApiError, TokenResponse, User } from "@/lib/types";

const STORAGE_KEY = "learnpilot-access-token";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  status: AuthStatus;
  error: ApiError | null;
  login: (payload: { email: string; password: string }) => Promise<TokenResponse>;
  register: (payload: {
    email: string;
    password: string;
    full_name?: string | null;
  }) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<User | null>;
  updateProfile: (payload: { full_name?: string | null }) => Promise<User>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function storeToken(token: string | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (token) {
    window.localStorage.setItem(STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const storedToken = window.localStorage.getItem(STORAGE_KEY);
    if (!storedToken) {
      setStatus("unauthenticated");
      return;
    }

    setToken(storedToken);
    authApi
      .me(storedToken)
      .then((currentUser) => {
        startTransition(() => {
          setUser(currentUser);
          setStatus("authenticated");
          setError(null);
        });
      })
      .catch((authError: ApiError) => {
        storeToken(null);
        startTransition(() => {
          setToken(null);
          setUser(null);
          setStatus("unauthenticated");
          setError(authError);
        });
      });
  }, []);

  const login = useCallback(async (payload: { email: string; password: string }) => {
    const response = await authApi.login(payload);
    storeToken(response.access_token);
    startTransition(() => {
      setToken(response.access_token);
      setUser(response.user);
      setStatus("authenticated");
      setError(null);
    });
    return response;
  }, []);

  const register = useCallback(
    async (payload: {
      email: string;
      password: string;
      full_name?: string | null;
    }) => {
      const createdUser = await authApi.register(payload);
      startTransition(() => {
        setError(null);
      });
      return createdUser;
    },
    [],
  );

  const logout = useCallback(() => {
    storeToken(null);
    startTransition(() => {
      setToken(null);
      setUser(null);
      setStatus("unauthenticated");
      setError(null);
    });
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) {
      return null;
    }

    try {
      const currentUser = await authApi.me(token);
      startTransition(() => {
        setUser(currentUser);
        setStatus("authenticated");
        setError(null);
      });
      return currentUser;
    } catch (authError) {
      storeToken(null);
      startTransition(() => {
        setToken(null);
        setUser(null);
        setStatus("unauthenticated");
        setError(authError as ApiError);
      });
      return null;
    }
  }, [token]);

  const updateProfile = useCallback(
    async (payload: { full_name?: string | null }) => {
      if (!token) {
        throw { code: "unauthorized", message: "You need to log in first." } satisfies ApiError;
      }

      const updatedUser = await authApi.updateMe(token, payload);
      startTransition(() => {
        setUser(updatedUser);
      });
      return updatedUser;
    },
    [token],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      status,
      error,
      login,
      register,
      logout,
      refreshUser,
      updateProfile,
    }),
    [error, login, logout, refreshUser, register, status, token, updateProfile, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}
