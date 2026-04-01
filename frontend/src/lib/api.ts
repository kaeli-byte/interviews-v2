"use client";

import { supabase } from "@/lib/supabase";

export function getBackendBaseUrl(): string {
  return process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ?? "";
}

export function toBackendUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const base = getBackendBaseUrl();
  return base ? `${base}${normalizedPath}` : normalizedPath;
}

export async function getAuthToken(): Promise<string | null> {
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error) {
    console.error('[Auth] getSession error:', error.message);
  }

  if (!session?.access_token) {
    console.warn('[Auth] No active session - user not logged in');
    localStorage.removeItem("auth_token");
    return null;
  }

  console.log('[Auth] Token retrieved:', session.access_token.slice(0, 20) + '...');
  return session.access_token;
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await getAuthToken();

  if (!token) {
    console.error('[API] No auth token - need to sign in');
    throw new Error('Not authenticated - please sign in');
  }

  const headers = new Headers(init.headers || {});
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Content-Type", "application/json");

  const url = toBackendUrl(path);
  console.log(`[API] ${init.method || 'GET'} ${url}`);

  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (response.status === 401) {
    console.error('[API] 401 Unauthorized - token may be expired or invalid');
    // Clear the session and redirect to sign in
    await supabase.auth.signOut();
  }

  return response;
}

export type ServerTimingMetric = {
  name: string;
  duration: number | null;
};

export function parseServerTimingHeader(header: string | null): ServerTimingMetric[] {
  if (!header) {
    return [];
  }

  return header
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => {
      const [name, ...params] = part.split(";").map((value) => value.trim());
      const durParam = params.find((value) => value.startsWith("dur="));
      const duration = durParam ? Number.parseFloat(durParam.slice(4)) : null;
      return {
        name,
        duration: Number.isFinite(duration) ? duration : null,
      };
    });
}

export function getServerTimingMetrics(response: Response): ServerTimingMetric[] {
  return parseServerTimingHeader(response.headers.get("Server-Timing"));
}
