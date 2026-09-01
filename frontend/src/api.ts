const API_BASE_URL = import.meta.env.DEV
  ? ""
  : import.meta.env.VITE_API_BASE_URL ||
    "https://beautyaiservice.polandcentral.cloudapp.azure.com";

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
  city?: string;
  district?: string | null;
  address?: string;
  description?: string | null;
  phone?: string | null;
  logo?: string;
  location?: {
    id?: number;
    country?: string;
    city_name?: string;
    address?: string;
    region?: string;
    coordinates?: string;
    timezone?: string;
    city_tier?: string;
  } | null;
  opened_date?: string | null;
  owner?: number | null;
  latitude?: string | number;
  longitude?: string | number;
  masters?: number[];
  average_rating?: number;
  total_reviews?: number;
  masters_count?: number;
  service_count?: number;
  working_hours?: Array<{
    weekday?: number;
    opening_time?: string | null;
    closing_time?: string | null;
    is_closed?: boolean;
  }>;
  available_status?: string;
};

export type SalonLocationPayload = {
  country?: string;
  city_name?: string;
  address?: string;
  region?: string;
  coordinates?: string;
  timezone?: string;
  city_tier?: string;
};

export type SalonPatchPayload = {
  name?: string;
  location?: SalonLocationPayload;
  phone?: string | null;
  opened_date?: string | null;
  owner?: number | null;
  description?: string | null;
  logo?: string;
};

export type ApiService = {
  id: number;
  name: string;
  description?: string;
  category?: string;
  price?: string | number;
  duration_minutes?: number;
  salons?: Array<{ id: number; name: string }>;
  masters?:
    | string
    | Array<{ id: number; first_name: string; last_name: string }>;
  image?: string | null;
};

export type ApiMaster = {
  id: number;
  first_name: string;
  last_name: string;
  photo?: string | null;
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

export type AppointmentPayload = {
  master: number;
  salon: number;
  service: number;
  start: string;
  end: string;
  promo_id?: number | null;
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

export type PaymentMethod = "cash" | "card" | "apple_pay" | "google_pay";
export type PaymentStatus =
  | "pending"
  | "completed"
  | "failed"
  | "cancelled"
  | "refunded";

export type ApiPayment = {
  id: number;
  appointment: number;
  amount: string | number;
  currency?: string;
  payment_method: PaymentMethod;
  payment_method_display?: string;
  payment_status?: PaymentStatus;
  payment_status_display?: string;
  payment_date?: string;
};

export type ApiReferralEvent = {
  id: number;
  client?: number | null;
  session_id: string;
  salon: number;
  service?: number | null;
  source: string;
  destination_url: string;
  created_at?: string;
  event_type: string;
};

type ApiCollection<T> = T[] | { results?: T[] };

function readTokens(): AuthTokens | null {
  try {
    const raw = localStorage.getItem(AUTH_TOKENS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (
      typeof parsed?.access !== "string" ||
      typeof parsed?.refresh !== "string"
    )
      return null;
    return parsed;
  } catch {
    return null;
  }
}

function formatApiError(payload: unknown) {
  if (typeof payload === "string" && payload.trim()) return payload;
  if (!payload || typeof payload !== "object") return "";

  const record = payload as Record<string, unknown>;
  const directMessage = [record.detail, record.message, record.error].find(
    (value): value is string =>
      typeof value === "string" && value.trim().length > 0,
  );
  if (directMessage) return directMessage;

  return Object.entries(record)
    .flatMap(([field, value]) => {
      const messages = Array.isArray(value) ? value : [value];
      return messages
        .filter(
          (message): message is string =>
            typeof message === "string" && message.trim().length > 0,
        )
        .map((message) => `${field}: ${message}`);
    })
    .join("; ");
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
  if (!headers.has("Content-Type") && init.body)
    headers.set("Content-Type", "application/json");
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
    const message =
      formatApiError(payload) || `API request failed (${response.status})`;
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function apiResults<T>(payload: T[] | { results?: T[] }): T[] {
  return Array.isArray(payload) ? payload : (payload?.results ?? []);
}

export async function login(email: string, password: string) {
  const tokens = await apiRequest<AuthTokens>(
    "/api/users/token/",
    {
      method: "POST",
      body: JSON.stringify({ email, password }),
    },
    true,
    false,
  );
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
  return apiRequest<ApiUserProfile>(
    "/api/users/register/",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    true,
    false,
  );
}

export async function verifyEmail(id: string, token: string) {
  return apiRequest<void>(
    "/api/users/verify-email/",
    {
      method: "POST",
      body: JSON.stringify({ id, token }),
    },
    true,
    false,
  );
}

export async function getMe() {
  return apiRequest<ApiUserProfile>("/api/users/me/");
}

export async function getSalon(id: number) {
  return apiRequest<ApiSalon>(`/api/salons/${id}/`);
}

export async function patchSalon(id: number, payload: SalonPatchPayload) {
  return apiRequest<ApiSalon>(`/api/salons/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function createAppointment(payload: AppointmentPayload) {
  return apiRequest<ApiAppointment>("/api/appointments/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listPayments(page = 1) {
  const payload = await apiRequest<ApiCollection<ApiPayment>>(
    `/api/payments/?page=${page}`,
  );
  return apiResults(payload);
}

export type PaymentPayload = {
  appointment: number;
  amount: string;
  currency: string;
  payment_method: PaymentMethod;
  payment_status?: PaymentStatus;
};

export async function createPayment(payload: PaymentPayload) {
  return apiRequest<ApiPayment>("/api/payments/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPayment(id: number) {
  return apiRequest<ApiPayment>(`/api/payments/${id}/`);
}

export async function updatePayment(id: number, payload: PaymentPayload) {
  return apiRequest<ApiPayment>(`/api/payments/${id}/`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function patchPayment(
  id: number,
  payload: Partial<PaymentPayload>,
) {
  return apiRequest<ApiPayment>(`/api/payments/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deletePayment(id: number) {
  return apiRequest<void>(`/api/payments/${id}/`, { method: "DELETE" });
}

export type PromotionPayload = {
  name: string;
  description: string;
  discount_percent: number;
  start_date: string;
  end_date: string;
  salon: number;
};

export async function listPromotions(
  filters: {
    page?: number;
    active?: boolean;
    discount_percent?: number;
    salon_id?: number;
  } = {},
) {
  const params = new URLSearchParams({ page: String(filters.page ?? 1) });
  if (filters.active !== undefined)
    params.set("active", String(filters.active));
  if (filters.discount_percent !== undefined)
    params.set("discount_percent", String(filters.discount_percent));
  if (filters.salon_id !== undefined)
    params.set("salon_id", String(filters.salon_id));
  const payload = await apiRequest<ApiCollection<ApiPromotion>>(
    `/api/promotions/?${params.toString()}`,
  );
  return apiResults(payload);
}

export async function createPromotion(payload: PromotionPayload) {
  return apiRequest<ApiPromotion>("/api/promotions/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getPromotion(id: number) {
  return apiRequest<ApiPromotion>(`/api/promotions/${id}/`);
}

export async function updatePromotion(id: number, payload: PromotionPayload) {
  return apiRequest<ApiPromotion>(`/api/promotions/${id}/`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function patchPromotion(
  id: number,
  payload: Partial<PromotionPayload>,
) {
  return apiRequest<ApiPromotion>(`/api/promotions/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deletePromotion(id: number) {
  return apiRequest<void>(`/api/promotions/${id}/`, { method: "DELETE" });
}

export type ReferralEventPayload = {
  session_id: string;
  salon: number;
  service?: number | null;
  source: string;
  destination_url: string;
  event_type: string;
};

export async function listReferralEvents(page = 1) {
  const payload = await apiRequest<ApiCollection<ApiReferralEvent>>(
    `/api/referral-events/?page=${page}`,
  );
  return apiResults(payload);
}

export async function createReferralEvent(payload: ReferralEventPayload) {
  return apiRequest<ApiReferralEvent>("/api/referral-events/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getReferralEvent(id: number) {
  return apiRequest<ApiReferralEvent>(`/api/referral-events/${id}/`);
}

export async function updateReferralEvent(
  id: number,
  payload: ReferralEventPayload,
) {
  return apiRequest<ApiReferralEvent>(`/api/referral-events/${id}/`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function patchReferralEvent(
  id: number,
  payload: Partial<ReferralEventPayload>,
) {
  return apiRequest<ApiReferralEvent>(`/api/referral-events/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteReferralEvent(id: number) {
  return apiRequest<void>(`/api/referral-events/${id}/`, { method: "DELETE" });
}

export async function listMasters(
  filters: { page?: number; ordering?: string } = {},
) {
  const params = new URLSearchParams({ page: String(filters.page ?? 1) });
  if (filters.ordering) params.set("ordering", filters.ordering);
  const payload = await apiRequest<ApiCollection<ApiMaster>>(
    `/api/users/masters/?${params.toString()}`,
    {},
    true,
    true,
  );
  return apiResults(payload);
}

export async function listFavoriteMasters(page = 1) {
  const payload = await apiRequest<ApiCollection<ApiFavoriteMaster>>(
    `/api/users/favorite-masters/?page=${page}`,
  );
  return apiResults(payload);
}

export async function checkIsFavoriteMaster(masterId: number) {
  const result = await apiRequest<{ is_favorite: boolean }>(
    `/api/users/favorite-masters/${masterId}/`,
  );
  return result.is_favorite;
}

export async function addFavoriteMaster(masterId: number) {
  return apiRequest<ApiFavoriteMaster>(
    `/api/users/favorite-masters/${masterId}/`,
    { method: "POST" },
  );
}

export async function removeFavoriteMaster(masterId: number) {
  return apiRequest<void>(`/api/users/favorite-masters/${masterId}/`, {
    method: "DELETE",
  });
}

export function clearTokens() {
  try {
    localStorage.removeItem(AUTH_TOKENS_KEY);
  } catch {
    // ignore
  }
}
