const API_BASE_URL = import.meta.env.DEV
  ? ""
  : (import.meta.env.VITE_API_BASE_URL || "https://beautyaiservice.polandcentral.cloudapp.azure.com");

const AUTH_TOKENS_KEY = "beautyai_auth_tokens";

export type AuthTokens = { access: string; refresh: string };

export type ApiUserProfile = {
  id?: number;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  photo?: string | null;
  is_staff?: boolean;
  is_master?: boolean;
};

export type ApiSalon = {
  id: number;
  name: string;
  city: string;
  district?: string | null;
  address: string;
  logo?: string;
  average_rating?: number;
  total_reviews?: number;
  masters_count?: number;
  service_count?: number;
  working_hours?: Array<{ opening_time?: string; closing_time?: string; is_closed?: boolean }>;
  available_status?: string;
};

export type ApiService = {
  id: number;
  name: string;
  description?: string;
  category?: string;
  price?: string | number;
  duration_minutes?: number;
  salons?: Array<{ id: number; name: string }>;
  masters?: string;
  image?: string | null;
};

export type ApiMaster = {
  id: number;
  first_name: string;
  last_name: string;
  photo?: string;
  average_rating?: number;
  total_reviews?: number;
  years_of_experience?: number;
  salons?: Array<{ id: number; name: string }>;
  services?: Array<{ id: number; name: string }>;
};

export type ApiPromotion = {
  id: number;
  name: string;
  description?: string;
  discount_percent: number;
  start_date: string;
  end_date: string;
  salon: number;
};

export type ApiReview = {
  id: number;
  appointment: number;
  client: number;
  master: number;
  rating: number;
  comment?: string | null;
  created_at: string;
};

export type ApiAppointment = {
  id: number;
  client?: number;
  master: number;
  salon: number;
  service: number;
  promo_id?: number | null;
  start: string;
  end: string;
  status: string;
  created_at: string;
};

export type ApiMasterAppointment = {
  id: number;
  start: string;
  end: string;
  client_name: string;
  service_name: string;
  status: string;
  duration_minutes: number;
  total_price: string;
  salon_name: string;
  created_at: string;
};

export type ApiFavoriteMaster = {
  id: number;
  name: string;
  profile_photo?: string | null;
  average_rating?: string | number | null;
  salons?: Array<{ id: number; name: string }>;
  active_services?: Array<{ id: number; name: string }>;
};

function readTokens(): AuthTokens | null {
  try {
    const raw = localStorage.getItem(AUTH_TOKENS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (typeof parsed?.access !== "string" || typeof parsed?.refresh !== "string") return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeTokens(tokens: AuthTokens) {
  try {
    localStorage.setItem(AUTH_TOKENS_KEY, JSON.stringify(tokens));
  } catch {
    // Authentication still works for the current request when storage is unavailable.
  }
}

export function getAccessToken() {
  return readTokens()?.access ?? null;
}

async function refreshAccessToken(refresh: string) {
  const response = await fetch(`${API_BASE_URL}/api/users/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) return null;
  const payload = await response.json();
  if (!payload?.access) return null;
  const tokens = { access: payload.access, refresh };
  writeTokens(tokens);
  return tokens.access;
}

export async function apiRequest<T = unknown>(
  path: string,
  init: RequestInit = {},
  canRetry = true,
  includeAuth = true,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) headers.set("Content-Type", "application/json");
  const access = includeAuth ? getAccessToken() : null;
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (response.status === 401 && canRetry && includeAuth) {
    const tokens = readTokens();
    if (tokens?.refresh) {
      const nextAccess = await refreshAccessToken(tokens.refresh);
      if (nextAccess) return apiRequest<T>(path, init, false, includeAuth);
    }
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.detail || payload?.message || `API request failed (${response.status})`;
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function apiResults<T>(payload: T[] | { results?: T[] }): T[] {
  return Array.isArray(payload) ? payload : payload?.results ?? [];
}

export async function login(email: string, password: string) {
  const tokens = await apiRequest<AuthTokens>("/api/users/token/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }, true, false);
  writeTokens(tokens);
  return tokens;
}

export async function register(payload: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone: string;
}) {
  return apiRequest<ApiUserProfile>("/api/users/register/", {
    method: "POST",
    body: JSON.stringify(payload),
  }, true, false);
}

export async function getMe() {
  return apiRequest<ApiUserProfile>("/api/users/me/");
}

export function clearTokens() {
  try {
    localStorage.removeItem(AUTH_TOKENS_KEY);
  } catch {
    // ignore
  }
}