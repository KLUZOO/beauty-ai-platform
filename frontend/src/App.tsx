import React, { useEffect, useRef, useState } from "react";
import "./App.css";
import MapSection from "./MapSection";
import CategoryFilters from "./CategoryFilters";
import FilterBar from "./FilterBar";
import { DEFAULT_FILTERS, type FilterState } from "./filterTypes";
import beautyAISparkles from "./assets/beauty-ai-sparkles.svg";
import DashboardShell from "./dashboard/DashboardShell";
import {
  apiRequest,
  apiResults,
  clearTokens,
  getAccessToken,
  getMe,
  login,
  listMasters,
  register,
  createAppointment,
  getSalon,
  type ApiMaster,
  type ApiPromotion,
  type ApiReview,
  type ApiSalon,
  type ApiService,
  type ApiUserProfile,
  verifyEmail,
} from "./api";

type CardData = {
  id?: number;
  image?: string | null;
  badges: { text: string; kind: string }[];
  title: string;
  type: string;
  rating: number;
  reviews: number;
  district: string;
  distance: string;
  openNow?: boolean;
  tags: string[];
  priceFrom: string;
  mastersCount?: string;
  avgCheck?: string;
  why?: string;
  variant?: "solo";
  experience?: string;
  locationNote?: string;
  profileLinkLabel?: string;
  coordinates?: [number, number];
  booking?: {
    master: number;
    salon: number;
    service: number;
    masterName: string;
    salonName: string;
    serviceName: string;
  };
};

const CATEGORY_TERMS: Record<string, string[]> = {
  manicure: ["манікюр", "нейл", "nail", "нігт"],
  pedicure: ["педикюр", "pedicure"],
  haircut: ["стриж", "барбер", "haircut", "barber"],
  coloring: ["фарбув", "колор", "color", "блон"],
  botox: ["ботокс", "botox"],
  massage: ["масаж", "massage"],
  eyelashes: ["вії", "нарощув", "ламінуван вій", "eyelash", "lash"],
  brows: ["бров", "brow"],
  makeup: ["макіяж", "візаж", "makeup"],
  cosmetology: ["косметолог", "cosmetology"],
  depilation: ["депіляц", "depilation"],
  solarium: ["соляр", "solarium"],
  facial: ["чистк", "обличч", "facial"],
  spa: ["spa", "спа"],
  hair: ["волос", "стриж", "фарб", "уклад", "hair", "barber"],
  nails: ["манікюр", "педикюр", "нейл", "нігт", "nail"],
};

const DISTRICT_TERMS: Record<string, string[]> = {
  pecherskyi: ["печерськ", "печерський", "липки"],
  shevchenkivskyi: ["шевченківськ", "центр", "золоті ворота"],
  podilskyi: ["поділ", "подільськ"],
  holosiivskyi: ["голосіїв"],
};
const SEARCH_STOP_WORDS = new Set([
  "у",
  "в",
  "на",
  "та",
  "й",
  "і",
  "з",
  "зі",
  "до",
  "для",
  "сьогодні",
  "завтра",
  "today",
  "tomorrow",
  "this",
  "week",
  "київ",
  "києва",
  "kyiv",
]);

function normalize(value: string) {
  return value
    .toLocaleLowerCase("uk-UA")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function numberFrom(value: string) {
  const parsed = Number(value.replace(/[^\d.,]/g, "").replace(",", "."));
  return Number.isFinite(parsed) ? parsed : 0;
}

function matchesTerms(value: string, terms: string[]) {
  const normalized = normalize(value);
  return terms.some((term) => normalized.includes(normalize(term)));
}

function matchesSearch(value: string, query: string) {
  const normalizedValue = normalize(value);
  const tokens = normalize(query)
    .split(/[^\p{L}\p{N}]+/u)
    .filter((token) => token.length > 1 && !SEARCH_STOP_WORDS.has(token));

  return tokens.every(
    (token) =>
      normalizedValue.includes(token) ||
      (token.length > 3 && normalizedValue.includes(token.slice(0, -1))),
  );
}

function matchesCommonFilters(
  item: Pick<
    CardData,
    | "title"
    | "type"
    | "rating"
    | "district"
    | "distance"
    | "priceFrom"
    | "tags"
    | "openNow"
    | "variant"
  >,
  filters: FilterState,
  category: string,
  searchQuery: string,
) {
  const searchableText = [
    item.title,
    item.type,
    item.district,
    ...item.tags,
  ].join(" ");
  const price = numberFrom(item.priceFrom);
  const distance = numberFrom(item.distance);
  const serviceText = [item.title, item.type, ...item.tags].join(" ");
  const isSolo =
    item.variant === "solo" || matchesTerms(item.type, ["майстер", "master"]);
  const venueText = normalize(item.type);

  if (searchQuery.trim() && !matchesSearch(searchableText, searchQuery))
    return false;
  if (
    category !== "all" &&
    !matchesTerms(serviceText, CATEGORY_TERMS[category] ?? [])
  )
    return false;
  if (
    item.priceFrom !== "—" &&
    filters.priceMin &&
    price < Number(filters.priceMin)
  )
    return false;
  if (
    item.priceFrom !== "—" &&
    filters.priceMax &&
    price > Number(filters.priceMax)
  )
    return false;
  if (
    filters.rating !== "any" &&
    item.rating < Number(filters.rating.replace("from", "")) / 10
  )
    return false;
  if (
    filters.distance !== "any" &&
    distance > Number(filters.distance.replace("to", "").replace("km", ""))
  )
    return false;
  if (filters.city !== "any" && filters.city !== "kyiv") return false;
  if (
    filters.district !== "any" &&
    !matchesTerms(item.district, DISTRICT_TERMS[filters.district] ?? [])
  )
    return false;
  if (
    filters.service !== "any" &&
    !matchesTerms(serviceText, CATEGORY_TERMS[filters.service] ?? [])
  )
    return false;
  if (filters.venueType === "solo" && !isSolo) return false;
  if (
    filters.venueType === "studio" &&
    (isSolo || !venueText.includes("студи"))
  )
    return false;
  if (filters.venueType === "salon" && isSolo) return false;
  if (filters.availability === "today" && item.openNow === false && !isSolo)
    return false;

  return true;
}

function matchesPartnerFilters(
  offer: PartnerOffer,
  filters: FilterState,
  category: string,
  searchQuery: string,
) {
  const searchableText = [offer.title, offer.partner, offer.district].join(" ");
  const serviceText = searchableText;
  const price = numberFrom(offer.newPrice);
  const distance = numberFrom(offer.distance);

  if (searchQuery.trim() && !matchesSearch(searchableText, searchQuery))
    return false;
  if (
    category !== "all" &&
    !matchesTerms(serviceText, CATEGORY_TERMS[category] ?? [])
  )
    return false;
  if (
    !offer.isDiscountOnly &&
    filters.priceMin &&
    price < Number(filters.priceMin)
  )
    return false;
  if (
    !offer.isDiscountOnly &&
    filters.priceMax &&
    price > Number(filters.priceMax)
  )
    return false;
  if (
    filters.distance !== "any" &&
    distance > Number(filters.distance.replace("to", "").replace("km", ""))
  )
    return false;
  if (filters.city !== "any" && filters.city !== "kyiv") return false;
  if (
    filters.district !== "any" &&
    !matchesTerms(offer.district, DISTRICT_TERMS[filters.district] ?? [])
  )
    return false;
  if (
    filters.service !== "any" &&
    !matchesTerms(serviceText, CATEGORY_TERMS[filters.service] ?? [])
  )
    return false;
  if (filters.availability === "today" && !offer.openNow) return false;

  return true;
}

type PartnerOffer = {
  id?: number;
  image?: string | null;
  discount: string;
  validUntil: string;
  title: string;
  partner: string;
  district: string;
  distance: string;
  openNow?: boolean;
  oldPrice: string;
  newPrice: string;
  gift?: string;
  isDiscountOnly?: boolean;
  coordinates?: [number, number];
};

type SelectedMapLocation = {
  name: string;
  district: string;
  distance: string;
  lat: number;
  lng: number;
};

type Lang = "ua" | "en";

const dict = {
  ua: {
    nav: ["Салони", "Майстри", "Акції", "Про Beauty AI"],
    loginGoogle: "Увійти",
    heroTitle1: "ЗНАЙДИ СВІЙ", // було "Знайдіть свого майстра"
    heroTitle2: "BEAUTY MATCH", // новий рядок
    heroTitle3: "ЗА ДОПОМОГОЮ AI",
    heroEyebrow: "ТВІЙ РОЗУМНИЙ ПОШУК КРАСИ",
    heroSubtitle: "Опиши, що тобі потрібно — AI підбере майстра під твій запит",
    searchPlaceholder: "Наприклад: манікюр у центрі Києва сьогодні",
    searchBtn: "Знайти",
    filters: "Фільтри",
    partnersLink: "Про партнерів>",
    footer:
      "Beauty AI аналізує ваші запити та обирає найкращі варіанти саме для вас",
    noResults: "За цими параметрами нічого не знайдено",
    sections: {
      recommendations: {
        title: "Салони для вас",
        subtitle: "Найкращі збіги за рейтингом, ціною та доступністю",
      },
      soloMasters: {
        title: "Майстри для вас",
        subtitle: "Персональні рекомендації майстрів під ваш запит",
      },
      partners: {
        title: "Пропозиції від партнерів",
        subtitle: "Ексклюзивні знижки та акції",
      },
      nearby: {
        title: "Найкращі в Києві",
        subtitle: "Салони та майстри з найвищими показниками",
      },
      topRated: {
        title: "Варто спробувати",
        subtitle: "Щось нове, що може вас зацікавити",
      },
      fresh: {
        title: "Новинки на платформі",
        subtitle: "Нові майстри та салони для вас",
      },
    },
    cta: "Записатися",
    viewSalon: "Дивитися салон",
    inSalon: "у салоні",
    avgCheck: "Середній чек",
    about: {
      // ← тут вставляєш новий блок
      title: "Про Beauty AI",
      description:
        "Beauty AI — сервіс, який допомагає знайти майстра краси за лічені секунди. Опишіть, що вам потрібно, а наш AI підбере найкращі салони та майстрів поруч — з урахуванням рейтингу, цін і вільних вікон запису.",
      contactsTitle: "Зв'язок",
      partnersTitle: "Співпраця",
      partnersText:
        "Ви майстер або власник салону? Приєднуйтесь до Beauty AI та отримуйте нових клієнтів щодня.",
      partnersCta: "Стати партнером →",
    },
  },
  en: {
    nav: ["Salons", "Masters", "Promotions", "About Beauty AI"],
    loginGoogle: "Sign in",
    heroTitle1: "Find your",
    heroTitle2: "beauty match",
    heroTitle3: "with the help of AI",
    heroEyebrow: "YOUR SMART BEAUTY SEARCH",
    heroSubtitle: "Describe what you need — we'll find the best options nearby",
    searchPlaceholder: "E.g.: manicure in central Kyiv today",
    searchBtn: "Search",
    filters: "Filters",
    partnersLink: "About partners",
    footer:
      "Beauty AI analyzes your requests and picks the best options just for you",
    noResults: "Nothing found for these filters",
    sections: {
      recommendations: {
        title: "Salons For You",
        subtitle: "Best match for your request",
      },
      soloMasters: {
        title: "Masters For You",
        subtitle: "AI picked these masters for your request",
      },
      partners: {
        title: "Partner Offers",
        subtitle: "Exclusive discounts and promotions",
      },
      nearby: {
        title: "Best in Kyiv",
        subtitle: "Top salons and masters by overall performance",
      },
      topRated: {
        title: "Worth Trying",
        subtitle: "Something new that might catch your eye",
      },
      fresh: {
        title: "New on the Platform",
        subtitle: "New masters and salons for you",
      },
    },
    cta: "Book now",
    viewSalon: "View salon",
    inSalon: "at the salon",
    avgCheck: "Average check",
    about: {
      // ← і тут теж
      title: "About Beauty AI",
      description:
        "Beauty AI is a service that helps you find a beauty master in seconds. Describe what you need, and our AI will pick the best salons and masters nearby — based on ratings, prices, and open booking slots.",
      contactsTitle: "Get in touch",
      partnersTitle: "Partnership",
      partnersText:
        "Are you a master or salon owner? Join Beauty AI and get new clients every day.",
      partnersCta: "Become a partner →",
    },
  },
} as const;

type Translations = (typeof dict)[Lang];

type AuthRole = "client" | "master" | "admin";
type AppView = "home" | "dashboard";

type MockUser = {
  name: string;
  email: string;
  role: AuthRole;
  avatar?: string | null;
};

// Дев: йде через Vite proxy (vite.config.ts, ключ "/api") — той самий origin, без CORS/TLS болю.
// Прод-білд: proxy не існує (це чиста статика), тож б'ємо напряму в бекенд —
// бекенд для цього має дозволити прод-домен у CORS_ALLOWED_ORIGINS.
function clearAuthTokens() {
  clearTokens();
}

// GET /api/users/me/ -> визначаємо роль з is_staff/is_master (бекенд не віддає окреме поле role)
function resolveRoleFromProfile(profile: any): AuthRole {
  if (profile?.is_staff) return "admin";
  if (profile?.is_master) return "master";
  return "client";
}

function profileToMockUser(
  profile: ApiUserProfile,
  lang: Lang,
  fallbackEmail = "",
): MockUser {
  const role = resolveRoleFromProfile(profile);
  const name = `${profile.first_name ?? ""} ${profile.last_name ?? ""}`.trim();

  return {
    name: name || (lang === "ua" ? "Beauty AI користувач" : "Beauty AI user"),
    email: profile.email || fallbackEmail,
    role,
    avatar: profile.photo || null,
  };
}

function getAuthErrorMessage(error: unknown, lang: Lang, fallback: string) {
  const message = error instanceof Error ? error.message : "";
  const normalizedMessage = message.toLowerCase();
  if (
    normalizedMessage.includes("no active account") ||
    normalizedMessage.includes("not active")
  ) {
    return lang === "ua"
      ? "Акаунт ще не активний. Підтвердіть email у листі від Beauty AI, а потім спробуйте увійти ще раз."
      : "Your account is not active yet. Confirm your email using the Beauty AI message, then try signing in again.";
  }
  if (
    normalizedMessage.includes("email") &&
    (normalizedMessage.includes("already") ||
      normalizedMessage.includes("exists"))
  ) {
    return lang === "ua"
      ? "Цей email уже зареєстрований. Увійдіть у наявний акаунт або використайте іншу адресу."
      : "This email is already registered. Sign in to the existing account or use another address.";
  }
  if (/^api request failed \(\d+\)$/i.test(message)) return fallback;
  return message || fallback;
}

function AuthModal({
  lang,
  onClose,
  onAuthenticated,
  initialMode = "login",
  initialRole = "client",
  initialPartnerKind,
  initialError,
  initialSuccess,
}: {
  lang: Lang;
  onClose: () => void;
  onAuthenticated: (user: MockUser) => void;
  initialMode?: "login" | "register";
  initialRole?: Exclude<AuthRole, "admin">;
  initialPartnerKind?: "solo" | "salon";
  initialError?: string | null;
  initialSuccess?: string | null;
}) {
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [role, setRole] = useState<Exclude<AuthRole, "admin">>(initialRole);
  const [partnerKind] = useState<"solo" | "salon" | undefined>(
    initialPartnerKind,
  );
  const [businessName, setBusinessName] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState<string | null>(
    initialError ?? null,
  );
  const [authSuccess, setAuthSuccess] = useState<string | null>(
    initialSuccess ?? null,
  );
  const [authLoading, setAuthLoading] = useState(false);
  const [googlePickerOpen, setGooglePickerOpen] = useState(false);
  const [googlePickingRole, setGooglePickingRole] = useState<AuthRole | null>(
    null,
  );

  const ua = lang === "ua";

  const finishAuth = (authRole: AuthRole = role) => {
    const fallbackEmail =
      authRole === "master"
        ? "master@beautyai.demo"
        : authRole === "admin"
          ? "admin@beautyai.demo"
          : "client@beautyai.demo";

    onAuthenticated({
      name:
        authRole === "master"
          ? partnerKind === "salon" && businessName.trim()
            ? businessName.trim()
            : ua
              ? "Майстер Beauty AI"
              : "Beauty AI Master"
          : authRole === "admin"
            ? "Beauty AI Admin"
            : ua
              ? "Клієнт Beauty AI"
              : "Beauty AI Client",
      email: email || fallbackEmail,
      role: authRole,
      avatar: null,
    });
  };

  // Реальний логін: POST /api/users/token/ (email+password) → JWT access/refresh → GET /api/users/me/ для профілю й ролі
  const loginWithPassword = async () => {
    setAuthError(null);
    setAuthSuccess(null);
    setAuthLoading(true);
    try {
      const normalizedEmail = email.trim();
      await login(normalizedEmail, password);
      const profile = await getMe();
      onAuthenticated(profileToMockUser(profile, lang, normalizedEmail));
    } catch (err: any) {
      setAuthError(
        getAuthErrorMessage(
          err,
          lang,
          ua
            ? "Сталася помилка. Спробуйте ще раз."
            : "Something went wrong. Try again.",
        ),
      );
    } finally {
      setAuthLoading(false);
    }
  };

  const registerWithPassword = async () => {
    setAuthError(null);
    setAuthSuccess(null);
    setAuthLoading(true);
    try {
      const normalizedEmail = email.trim();
      await register({
        email: normalizedEmail,
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone.trim(),
      });
      setEmail(normalizedEmail);
      setPassword("");
      setMode("login");
      setAuthSuccess(
        ua
          ? "Акаунт створено. Якщо потрібно підтвердити email, перевірте пошту, а потім увійдіть."
          : "Your account was created. If email verification is required, check your inbox, then sign in.",
      );
    } catch (err: any) {
      setAuthError(
        getAuthErrorMessage(
          err,
          lang,
          ua ? "Не вдалося створити акаунт" : "Could not create account",
        ),
      );
    } finally {
      setAuthLoading(false);
    }
  };

  const fakeGoogleAccounts: {
    role: AuthRole;
    name: string;
    email: string;
    avatar: null;
  }[] = [
    {
      role: "client",
      name: ua ? "Ірина Клієнтка" : "Irene Client",
      email: "irene.client@gmail.com",
      avatar: null,
    },
    {
      role: "master",
      name: ua ? "Майстер Beauty" : "Beauty Master",
      email: "beauty.master@gmail.com",
      avatar: null,
    },
    {
      role: "admin",
      name: ua ? "Адмін Beauty AI" : "Beauty AI Admin",
      email: "admin.beautyai@gmail.com",
      avatar: null,
    },
  ];

  const pickGoogleAccount = (account: (typeof fakeGoogleAccounts)[number]) => {
    setGooglePickingRole(account.role);
    // Невелика штучна затримка — щоб виглядало як справжній вхід, а не миттєвий клік
    setTimeout(() => {
      setGooglePickerOpen(false);
      setGooglePickingRole(null);
      onAuthenticated({
        name: account.name,
        email: account.email,
        role: account.role,
        avatar: account.avatar,
      });
    }, 700);
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    if (mode === "login") {
      loginWithPassword();
      return;
    }
    registerWithPassword();
  };

  return (
    <div className="auth-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className="auth-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button
          className="auth-close"
          type="button"
          onClick={onClose}
          aria-label={ua ? "Закрити" : "Close"}
        >
          ×
        </button>

        <div className="auth-brand">
          <span className="auth-kicker">✦ BEAUTY AI</span>
          <h2 id="auth-title">
            {mode === "login"
              ? ua
                ? "Раді бачити вас знову"
                : "Welcome back"
              : ua
                ? "Створіть свій профіль"
                : "Create your profile"}
          </h2>
          <p>
            {mode === "login"
              ? ua
                ? "Увійдіть, щоб керувати записами, обраним і профілем."
                : "Sign in to manage bookings, favourites and your profile."
              : ua
                ? "Створіть акаунт, щоб керувати записами, обраним і профілем."
                : "Create an account to manage bookings, favourites and your profile."}
          </p>
        </div>

        <div className="auth-tabs" role="tablist">
          <button
            className={mode === "login" ? "active" : ""}
            type="button"
            onClick={() => {
              setAuthError(null);
              setAuthSuccess(null);
              setMode("login");
            }}
          >
            {ua ? "Увійти" : "Sign in"}
          </button>
          <button
            className={mode === "register" ? "active" : ""}
            type="button"
            onClick={() => {
              setAuthError(null);
              setAuthSuccess(null);
              setMode("register");
            }}
          >
            {ua ? "Реєстрація" : "Register"}
          </button>
        </div>

        {mode === "register" && (
          <div
            className="auth-role-switch"
            aria-label={ua ? "Тип профілю" : "Profile type"}
          >
            <button
              className={role === "client" ? "active" : ""}
              type="button"
              onClick={() => setRole("client")}
            >
              {ua ? "Я клієнт" : "I'm a client"}
            </button>
            <button
              className={role === "master" ? "active" : ""}
              type="button"
              onClick={() => setRole("master")}
            >
              {ua ? "Я майстер" : "I'm a master"}
            </button>
          </div>
        )}

        <form className="auth-form" onSubmit={submit}>
          {mode === "register" && (
            <>
              <div className="auth-form-row">
                <label>
                  <span>{ua ? "Ім'я" : "First name"}</span>
                  <input
                    type="text"
                    autoComplete="given-name"
                    value={firstName}
                    onChange={(event) => setFirstName(event.target.value)}
                    required
                  />
                </label>
                <label>
                  <span>{ua ? "Прізвище" : "Last name"}</span>
                  <input
                    type="text"
                    autoComplete="family-name"
                    value={lastName}
                    onChange={(event) => setLastName(event.target.value)}
                    required
                  />
                </label>
              </div>
              <label>
                <span>{ua ? "Телефон" : "Phone"}</span>
                <input
                  type="tel"
                  autoComplete="tel"
                  value={phone}
                  onChange={(event) => setPhone(event.target.value)}
                  required
                />
              </label>
            </>
          )}
          {mode === "register" && role === "master" && (
            <>
              {partnerKind === "salon" && (
                <label>
                  <span>{ua ? "Назва закладу" : "Business name"}</span>
                  <input
                    type="text"
                    value={businessName}
                    onChange={(event) => setBusinessName(event.target.value)}
                    placeholder={
                      ua
                        ? "Наприклад, Luna Beauty House"
                        : "e.g. Luna Beauty House"
                    }
                    required
                  />
                </label>
              )}
            </>
          )}

          <label>
            <span>Email</span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@example.com"
              required
            />
          </label>
          <label>
            <span>{ua ? "Пароль" : "Password"}</span>
            <input
              type="password"
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              minLength={mode === "register" ? 5 : undefined}
              required
            />
          </label>

          {mode === "login" && (
            <button className="auth-forgot" type="button">
              {ua ? "Забули пароль?" : "Forgot password?"}
            </button>
          )}

          {authError && <p className="auth-google-error">{authError}</p>}
          {authSuccess && <p className="auth-success">{authSuccess}</p>}

          <button className="auth-primary" type="submit" disabled={authLoading}>
            {mode === "login"
              ? authLoading
                ? ua
                  ? "Входимо…"
                  : "Signing in…"
                : ua
                  ? "Увійти"
                  : "Sign in"
              : authLoading
                ? ua
                  ? "Створюємо…"
                  : "Creating…"
                : ua
                  ? "Створити акаунт"
                  : "Create account"}
          </button>
        </form>

        <div className="auth-divider">
          <span>{ua ? "або" : "or"}</span>
        </div>

        <button
          className="auth-google"
          type="button"
          onClick={() => setGooglePickerOpen(true)}
        >
          <span className="google-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M21.6 12.23c0-.71-.06-1.4-.18-2.07H12v3.92h5.38a4.6 4.6 0 0 1-2 3.02v2.54h3.24c1.9-1.75 2.98-4.33 2.98-7.41Z"
              />
              <path
                fill="#34A853"
                d="M12 22c2.7 0 4.97-.9 6.62-2.36l-3.24-2.54c-.9.6-2.05.96-3.38.96-2.61 0-4.82-1.76-5.61-4.13H3.04v2.62A10 10 0 0 0 12 22Z"
              />
              <path
                fill="#FBBC05"
                d="M6.39 13.93A6.02 6.02 0 0 1 6.08 12c0-.67.11-1.32.31-1.93V7.45H3.04A10 10 0 0 0 2 12c0 1.61.38 3.14 1.04 4.55l3.35-2.62Z"
              />
              <path
                fill="#EA4335"
                d="M12 5.94c1.47 0 2.79.5 3.83 1.5l2.87-2.87A9.63 9.63 0 0 0 12 2a10 10 0 0 0-8.96 5.45l3.35 2.62C7.18 7.7 9.39 5.94 12 5.94Z"
              />
            </svg>
          </span>
          {ua ? "Продовжити з Google" : "Continue with Google"}
        </button>

        <p className="auth-demo-note">
          {ua
            ? "Email/пароль і реєстрація підключені до бекенду. Google потребує налаштованого OAuth ID token."
            : "Email/password sign-in and registration use the backend. Google needs a configured OAuth ID token."}
        </p>
      </div>

      {googlePickerOpen && (
        <div
          className="google-picker-backdrop"
          role="presentation"
          onMouseDown={() => !googlePickingRole && setGooglePickerOpen(false)}
        >
          <div
            className="google-picker-window"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="google-picker-titlebar">
              <span className="google-picker-url">accounts.google.com</span>
              <button
                type="button"
                className="google-picker-close"
                onClick={() => setGooglePickerOpen(false)}
                aria-label={ua ? "Закрити" : "Close"}
                disabled={!!googlePickingRole}
              >
                ×
              </button>
            </div>

            <div className="google-picker-body">
              <span className="google-mark google-mark-lg" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M21.6 12.23c0-.71-.06-1.4-.18-2.07H12v3.92h5.38a4.6 4.6 0 0 1-2 3.02v2.54h3.24c1.9-1.75 2.98-4.33 2.98-7.41Z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 22c2.7 0 4.97-.9 6.62-2.36l-3.24-2.54c-.9.6-2.05.96-3.38.96-2.61 0-4.82-1.76-5.61-4.13H3.04v2.62A10 10 0 0 0 12 22Z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M6.39 13.93A6.02 6.02 0 0 1 6.08 12c0-.67.11-1.32.31-1.93V7.45H3.04A10 10 0 0 0 2 12c0 1.61.38 3.14 1.04 4.55l3.35-2.62Z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.94c1.47 0 2.79.5 3.83 1.5l2.87-2.87A9.63 9.63 0 0 0 12 2a10 10 0 0 0-8.96 5.45l3.35 2.62C7.18 7.7 9.39 5.94 12 5.94Z"
                  />
                </svg>
              </span>
              <h3>{ua ? "Оберіть обліковий запис" : "Choose an account"}</h3>
              <p>
                {ua ? "щоб продовжити в Beauty AI" : "to continue to Beauty AI"}
              </p>

              <div className="google-picker-list">
                {fakeGoogleAccounts.map((account) => {
                  const isPicking = googlePickingRole === account.role;
                  return (
                    <button
                      key={account.email}
                      type="button"
                      className="google-picker-account"
                      onClick={() =>
                        !googlePickingRole && pickGoogleAccount(account)
                      }
                      disabled={!!googlePickingRole && !isPicking}
                    >
                      {account.avatar ? (
                        <img src={account.avatar} alt={account.name} />
                      ) : (
                        <span className="image-placeholder" aria-hidden="true">
                          ✦
                        </span>
                      )}
                      <span className="google-picker-account-info">
                        <b>{account.name}</b>
                        <span>{account.email}</span>
                      </span>
                      {isPicking && (
                        <span
                          className="google-picker-spinner"
                          aria-hidden="true"
                        />
                      )}
                    </button>
                  );
                })}
              </div>

              <p className="google-picker-footnote">
                {ua
                  ? "Демо-імітація вибору акаунта Google — реальна авторизація Google підключиться пізніше."
                  : "Demo simulation of Google's account picker — real Google auth will be wired later."}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FavButton() {
  const [active, setActive] = useState(false);
  return (
    <button
      className={`fav-btn ${active ? "active" : ""}`}
      aria-label="Додати в обране"
      onClick={(e) => {
        e.stopPropagation();
        e.preventDefault();
        setActive((prev) => !prev);
      }}
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill={active ? "currentColor" : "none"}
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
      </svg>
    </button>
  );
}

function Card({
  data,
  t,
  hideTags = false,
  hideReason = false,
  onLocationClick,
  onBookClick,
  onSalonDetailsClick,
}: {
  data: CardData;
  t: Translations;
  hideTags?: boolean;
  hideReason?: boolean;
  onLocationClick?: (
    name: string,
    district: string,
    distance: string,
    coordinates?: [number, number],
  ) => void;
  onBookClick?: (data: CardData) => void;
  onSalonDetailsClick?: (salonId: number) => void;
}) {
  const [showReason, setShowReason] = useState(false);
  const isSolo = data.variant === "solo";

  return (
    <div className={`card ${isSolo ? "card-solo" : ""}`}>
      <div
        className={`card-image ${isSolo ? "card-image-solo" : ""}`}
        style={
          data.image
            ? { ["--card-photo" as string]: `url(${data.image})` }
            : undefined
        }
      >
        <div className="card-badges">
          {data.badges.map((b) => (
            <span key={b.text} className={`badge ${b.kind}`}>
              {b.text}
            </span>
          ))}
        </div>
        <FavButton />
      </div>

      <div className="card-body">
        <div className="card-title-row">
          <div>
            <h3>{data.title}</h3>
            <p className="card-type">{data.type}</p>
          </div>
          <div className="card-rating">
            <span className="star">★</span> {data.rating.toFixed(1)}{" "}
            <span className="count">({data.reviews})</span>
          </div>
        </div>

        <div className="card-meta">
          <button
            type="button"
            className="card-location-link"
            onClick={() =>
              onLocationClick?.(
                data.title,
                data.district,
                data.distance,
                data.coordinates,
              )
            }
            title="Показати на карті"
          >
            <span className="district-pin">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#a855f7"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
              {data.district}
            </span>
            <span>· {data.distance}</span>
          </button>
          {data.openNow && !isSolo && (
            <span className="open-now">· Відкрито зараз</span>
          )}
          {isSolo && (
            <span className="solo-availability">· Є вікна сьогодні</span>
          )}
        </div>

        {!hideTags && (
          <div className="card-tags">
            {data.tags.map((tag) => (
              <span key={tag} className="tag">
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="card-footer">
          <div className="price-block">
            <div className="price">
              {data.priceFrom === "—" ? (
                t.avgCheck === "Середній чек" ? (
                  "Ціна за запитом"
                ) : (
                  "Price on request"
                )
              ) : (
                <>від {data.priceFrom} грн</>
              )}
            </div>
            <div className="avg">{data.avgCheck ?? t.avgCheck}</div>
          </div>
          <div className="masters-block">
            {(data.experience ?? data.mastersCount) && (
              <div>🕐 {data.experience ?? data.mastersCount}</div>
            )}
            <div>{data.locationNote ?? t.inSalon}</div>
          </div>
        </div>

        <div className="card-cta-row">
          <button
            className="cta-btn"
            type="button"
            onClick={() => onBookClick?.(data)}
          >
            {t.cta}
          </button>
          {!isSolo && data.id && onSalonDetailsClick ? (
            <button
              className="view-link view-link-button"
              type="button"
              onClick={() => onSalonDetailsClick(data.id as number)}
            >
              {data.profileLinkLabel ?? t.viewSalon} →
            </button>
          ) : (
            <a className="view-link" href="#">
              {data.profileLinkLabel ?? t.viewSalon} →
            </a>
          )}
        </div>

        {data.why && !hideReason && (
          <div className={`ai-reason ${showReason ? "is-open" : ""}`}>
            <button
              type="button"
              className="ai-reason-toggle"
              onClick={() => setShowReason((prev) => !prev)}
              aria-expanded={showReason}
            >
              <span className="ai-reason-label">✦ Чому рекомендуємо?</span>
              <span className="ai-reason-chevron" aria-hidden="true">
                ⌄
              </span>
            </button>

            <div className="ai-reason-content">
              <div className="ai-reason-inner">
                <p>{data.why}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const recommendations: CardData[] = [
  {
    badges: [{ text: "AI MATCH 98%", kind: "ai-match" }],
    title: "Luna Beauty House",
    type: "Салон краси",
    rating: 4.9,
    reviews: 124,
    district: "Печерський р-н",
    distance: "0.4 км",
    openNow: true,
    tags: ["Манікюр", "Педикюр", "Гель-лак", "Дизайн нігтів"],
    priceFrom: "600",
    mastersCount: "7 майстрів",
    why: "Високий рейтинг, спеціалізація на манікюрі, зручна локація та вільні вікна сьогодні",
  },
  {
    badges: [{ text: "AI MATCH 94%", kind: "ai-match" }],
    title: "Nails Studio",
    type: "Салон краси",
    rating: 4.8,
    reviews: 98,
    district: "Печерський р-н",
    distance: "0.6 км",
    openNow: true,
    tags: ["Манікюр", "Нарощування", "Дизайн", "SPA"],
    priceFrom: "550",
    mastersCount: "5 майстрів",
    why: "Чудові відгуки та оптимальне співвідношення ціна-якість для вашого запиту",
  },
  {
    badges: [
      { text: "AI MATCH 93%", kind: "ai-match" },
      { text: "НОВИНКА", kind: "new" },
    ],
    title: "Beauty Room",
    type: "Салон краси",
    rating: 4.7,
    reviews: 76,
    district: "Печерський р-н",
    distance: "0.8 км",
    openNow: true,
    tags: ["Манікюр", "Педикюр", "Нарощування вій", "Брови"],
    priceFrom: "650",
    mastersCount: "5 майстрів",
    why: "Підходить вашому бюджету та має багато позитивних відгуків",
  },
  {
    badges: [{ text: "AI MATCH 89%", kind: "ai-match" }],
    title: "Velvet Nails & Spa",
    type: "Салон краси",
    rating: 4.8,
    reviews: 61,
    district: "Печерський р-н",
    distance: "0.9 км",
    openNow: true,
    tags: ["Манікюр", "Педикюр", "SPA", "Масаж"],
    priceFrom: "580",
    mastersCount: "6 майстрів",
    why: "Стабільно високі оцінки за якість сервісу та зручний графік роботи",
  },

  {
    badges: [{ text: "AI MATCH 87%", kind: "ai-match" }],
    title: "Atelier Beauty",
    type: "Салон краси",
    rating: 4.8,
    reviews: 103,
    district: "Центр",
    distance: "1.2 км",
    openNow: true,
    tags: ["Стрижка", "Фарбування", "Догляд"],
    priceFrom: "650",
    mastersCount: "6 майстрів",
    why: "Сильні відгуки, зручна локація та послуги, що відповідають вашому запиту",
  },
  {
    badges: [
      { text: "AI MATCH 85%", kind: "ai-match" },
      { text: "НОВИНКА", kind: "new" },
    ],
    title: "Élan Studio",
    type: "Студія краси",
    rating: 4.9,
    reviews: 72,
    district: "Липки",
    distance: "1.4 км",
    tags: ["Брови", "Вії", "Макіяж"],
    priceFrom: "600",
    mastersCount: "4 майстри",
    why: "Високий рейтинг і сильна спеціалізація на beauty-послугах, які ви переглядали",
  },
];

const soloMastersRecommendations: CardData[] = [
  {
    badges: [{ text: "AI MATCH 96%", kind: "ai-match" }],
    title: "Оксана Мельник",
    type: "Соло майстер · Манікюр",
    rating: 4.9,
    reviews: 143,
    district: "Печерський р-н",
    distance: "0.5 км",
    tags: ["Манікюр", "Гель-лак", "Дизайн нігтів"],
    priceFrom: "500",
    experience: "6 років досвіду",
    locationNote: "Приймає у своїй студії",
    profileLinkLabel: "Профіль майстра",
    variant: "solo",
    why: "Високий рейтинг та вузька спеціалізація саме на манікюрі, який ви шукали",
  },
  {
    badges: [{ text: "AI MATCH 92%", kind: "ai-match" }],
    title: "Дмитро Кравець",
    type: "Соло майстер · Барбер",
    rating: 4.8,
    reviews: 201,
    district: "Печерський р-н",
    distance: "0.9 км",
    tags: ["Стрижка", "Борода", "Укладка"],
    priceFrom: "400",
    experience: "8 років досвіду",
    locationNote: "Приймає у своєму кабінеті",
    profileLinkLabel: "Профіль майстра",
    variant: "solo",
    why: "Один з найдосвідченіших барберів поруч із вами, з великою кількістю відгуків",
  },
  {
    badges: [{ text: "AI MATCH 90%", kind: "ai-match" }],
    title: "Ірина Бондар",
    type: "Соло майстер · Брови та вії",
    rating: 5.0,
    reviews: 87,
    district: "Липки",
    distance: "1.1 км",
    tags: ["Брови", "Вії", "Ламінування"],
    priceFrom: "600",
    experience: "5 років досвіду",
    locationNote: "Виїзд та прийом у кабінеті",
    profileLinkLabel: "Профіль майстра",
    variant: "solo",
    why: "Ідеальний рейтинг 5.0 та спеціалізація саме на бровах і віях",
  },
  {
    badges: [{ text: "AI MATCH 87%", kind: "ai-match" }],
    title: "Марина Кузьменко",
    type: "Соло майстер · Візаж",
    rating: 4.9,
    reviews: 112,
    district: "Липки",
    distance: "1.3 км",
    tags: ["Візаж", "Укладка", "Брови"],
    priceFrom: "700",
    experience: "7 років досвіду",
    locationNote: "Виїзний майстер",
    profileLinkLabel: "Профіль майстра",
    variant: "solo",
    why: "Багато відгуків саме за святковий та весільний візаж",
  },

  {
    badges: [{ text: "AI MATCH 85%", kind: "ai-match" }],
    title: "Софія Левченко",
    type: "Косметолог",
    rating: 4.8,
    reviews: 96,
    district: "Печерськ",
    distance: "1.5 км",
    tags: ["Косметологія", "Догляд", "Чистка"],
    priceFrom: "800",
    experience: "6 років досвіду",
    locationNote: "Приймає у власному кабінеті",
    profileLinkLabel: "Профіль майстра",
    variant: "solo",
    why: "Високі оцінки за доглядові процедури та зручний час запису",
  },
  {
    badges: [{ text: "AI MATCH 83%", kind: "ai-match" }],
    title: "Андрій Савчук",
    type: "Стиліст",
    rating: 4.9,
    reviews: 131,
    district: "Центр",
    distance: "1.7 км",
    tags: ["Стрижка", "Укладка", "Фарбування"],
    priceFrom: "700",
    experience: "9 років досвіду",
    locationNote: "Приймає у приватній студії",
    profileLinkLabel: "Профіль майстра",
    variant: "solo",
    why: "Високий рейтинг, великий досвід і сильний збіг із вашими фільтрами",
  },
];

const partners: PartnerOffer[] = [
  {
    discount: "-30%",
    validUntil: "до 30 червня",
    title: "Комплекс для волосся",
    partner: "Luna Beauty House",
    district: "Печерський р-н",
    distance: "0.4 км",
    openNow: true,
    oldPrice: "1 200",
    newPrice: "840",
    gift: "Укладка у подарунок",
  },
  {
    discount: "-20%",
    validUntil: "до 25 червня",
    title: "Масаж спини",
    partner: "Wellness Studio",
    district: "Липки",
    distance: "0.7 км",
    openNow: true,
    oldPrice: "900",
    newPrice: "720",
    gift: "Ароматерапія у подарунок",
  },
  {
    discount: "-25%",
    validUntil: "до 20 червня",
    title: "Манікюр + гель-лак",
    partner: "Nails Studio",
    district: "Золоті ворота",
    distance: "0.9 км",
    openNow: true,
    oldPrice: "800",
    newPrice: "600",
    gift: "Дизайн 2 нігтів у подарунок",
  },
  {
    discount: "-15%",
    validUntil: "до 15 червня",
    title: "Брови + ламінування",
    partner: "Brow Bar",
    district: "Центр",
    distance: "1.1 км",
    openNow: false,
    oldPrice: "1 000",
    newPrice: "850",
    gift: "Корекція у подарунок",
  },
  {
    discount: "-20%",
    validUntil: "до 12 липня",
    title: "Стрижка + укладка",
    partner: "Élan Studio",
    district: "Липки",
    distance: "1.3 км",
    openNow: true,
    oldPrice: "1 100",
    newPrice: "880",
    gift: "Догляд для волосся",
  },
  {
    discount: "-25%",
    validUntil: "до 18 липня",
    title: "Догляд для обличчя",
    partner: "Atelier Beauty",
    district: "Печерськ",
    distance: "1.5 км",
    openNow: true,
    oldPrice: "1 600",
    newPrice: "1 200",
    gift: "Маска у подарунок",
  },
];
const nearby: CardData[] = [
  {
    badges: [{ text: "ВИБІР BEAUTY AI", kind: "client-choice" }],
    title: "Beauty Point",
    type: "Салон краси",
    rating: 4.9,
    reviews: 324,
    district: "Печерський р-н",
    distance: "0.3 км",
    openNow: true,
    tags: [],
    priceFrom: "500",
    mastersCount: "8 майстрів",
  },

  {
    badges: [{ text: "ТОП МАЙСТЕР", kind: "top-rating" }],
    title: "Оксана Мельник",
    type: "Майстер манікюру",
    rating: 4.9,
    reviews: 143,
    district: "Печерський р-н",
    distance: "0.5 км",
    openNow: true,
    tags: [],
    priceFrom: "500",
    variant: "solo",
  },

  {
    badges: [{ text: "ТОП РЕЙТИНГ", kind: "top-rating" }],
    title: "Metro Beauty",
    type: "Салон краси",
    rating: 4.8,
    reviews: 268,
    district: "Кловська",
    distance: "0.5 км",
    openNow: true,
    tags: [],
    priceFrom: "600",
    mastersCount: "7 майстрів",
  },

  {
    badges: [{ text: "ВИБІР КЛІЄНТІВ", kind: "client-choice" }],
    title: "Дмитро Кравець",
    type: "Барбер",
    rating: 4.9,
    reviews: 201,
    district: "Печерський р-н",
    distance: "0.9 км",
    openNow: true,
    tags: [],
    priceFrom: "400",
    variant: "solo",
  },

  {
    badges: [{ text: "ЧАСТО БРОНЮЮТЬ", kind: "trend" }],
    title: "Élan Studio",
    type: "Студія краси",
    rating: 4.9,
    reviews: 172,
    district: "Липки",
    distance: "1.4 км",
    openNow: true,
    tags: [],
    priceFrom: "600",
    mastersCount: "5 майстрів",
  },
];
const topRated: CardData[] = [
  {
    badges: [{ text: "ТОП РЕЙТИНГ", kind: "top-rating" }],
    title: "Elegant Beauty",
    type: "Салон краси",
    rating: 4.9,
    reviews: 156,
    district: "Печерський",
    distance: "1.2 км",
    openNow: true,
    tags: ["Манікюр", "Педикюр", "Масаж", "Косметологія"],
    priceFrom: "800",
    mastersCount: "10 майстрів",
  },
  {
    badges: [{ text: "ВИБІР КЛІЄНТІВ", kind: "client-choice" }],
    title: "Perfect Look",
    type: "Нейл-бар",
    rating: 4.8,
    reviews: 97,
    district: "Печерський р-н",
    distance: "0.9 км",
    openNow: true,
    tags: ["Стрижка", "Фарбування", "Ботокс", "Догляд"],
    priceFrom: "450",
    mastersCount: "3 майстри",
  },
  {
    badges: [{ text: "НАЙКРАЩІ ВІДГУКИ", kind: "best-reviews" }],
    title: "VIP Beauty Club",
    type: "Салон краси",
    rating: 4.8,
    reviews: 89,
    district: "Арсенальна",
    distance: "1.5 км",
    openNow: true,
    tags: ["Манікюр", "Педикюр", "Масаж", "Косметологія"],
    priceFrom: "900",
    mastersCount: "7 майстрів",
  },
  {
    badges: [{ text: "НЕЗВИЧНИЙ ФОРМАТ", kind: "surprise" }],
    title: "Zen Beauty Loft",
    type: "Салон краси",
    rating: 4.7,
    reviews: 63,
    district: "Поділ",
    distance: "1.8 км",
    openNow: true,
    tags: ["Масаж", "SPA", "Медитативний догляд"],
    priceFrom: "650",
    mastersCount: "4 майстри",
  },
  {
    badges: [{ text: "РЕТЕЛЬНО ДІБРАНО", kind: "surprise" }],
    title: "Blush Beauty Bar",
    type: "Нейл-бар",
    rating: 4.9,
    reviews: 51,
    district: "Липки",
    distance: "1.0 км",
    openNow: true,
    tags: ["Манікюр", "Візаж", "Брови"],
    priceFrom: "550",
    mastersCount: "5 майстрів",
  },
];

const fresh: CardData[] = [
  {
    badges: [{ text: "НОВИЙ САЛОН", kind: "new-salon" }],
    title: "Fresh Beauty",
    type: "Салон краси",
    rating: 4.6,
    reviews: 22,
    district: "Печерський р-н",
    distance: "0.6 км",
    openNow: true,
    tags: ["Манікюр", "Педикюр", "Дизайн", "Нарощування"],
    priceFrom: "500",
    mastersCount: "4 майстри",
  },
  {
    badges: [{ text: "НОВИЙ МАЙСТЕР", kind: "new-master" }],
    title: "Kate Nails",
    type: "Майстер манікюру",
    rating: 4.7,
    reviews: 18,
    district: "Липки",
    distance: "1.0 км",
    openNow: true,
    tags: ["Манікюр", "Гель-лак", "Дизайн нігтів"],
    priceFrom: "400",
    mastersCount: "1 майстер",
  },
  {
    badges: [{ text: "НОВА ПОСЛУГА", kind: "new-service" }],
    title: "VIP Beauty Club",
    type: "Салон краси",
    rating: 4.8,
    reviews: 89,
    district: "Арсенальна",
    distance: "1.5 км",
    openNow: true,
    tags: ["Ботокс для волосся", "Ламінування"],
    priceFrom: "700",
    mastersCount: "3 майстри",
  },
  {
    badges: [{ text: "ПРИЄДНАЛИСЬ 3 ДНІ ТОМУ", kind: "new-salon" }],
    title: "Glow Studio",
    type: "Салон краси",
    rating: 4.5,
    reviews: 9,
    district: "Печерський р-н",
    distance: "1.1 км",
    openNow: true,
    tags: ["Манікюр", "Брови", "Вії"],
    priceFrom: "480",
    mastersCount: "3 майстри",
  },
  {
    badges: [{ text: "ПРИЄДНАВСЯ ВЧОРА", kind: "new-master" }],
    title: "Olena Style",
    type: "Майстриня стрижки",
    rating: 5.0,
    reviews: 3,
    district: "Липки",
    distance: "1.4 км",
    openNow: true,
    tags: ["Стрижка", "Укладка"],
    priceFrom: "420",
    mastersCount: "1 майстер",
  },
];

function RecommendationCarousel({
  cards,
  t,
  variant,
  onLocationClick,
  onBookClick,
  onSalonDetailsClick,
}: {
  cards: CardData[];
  t: Translations;
  variant: "salons" | "masters" | "nearby" | "worth-trying" | "fresh";
  onLocationClick?: (
    name: string,
    district: string,
    distance: string,
    coordinates?: [number, number],
  ) => void;
  onBookClick?: (data: CardData) => void;
  onSalonDetailsClick?: (salonId: number) => void;
}) {
  const trackRef = useRef<HTMLDivElement>(null);

  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(cards.length > 4);

  const updateArrows = () => {
    const track = trackRef.current;
    if (!track) return;

    const maxScrollLeft = Math.max(0, track.scrollWidth - track.clientWidth);

    setCanScrollLeft(track.scrollLeft > 5);
    setCanScrollRight(track.scrollLeft < maxScrollLeft - 5);
  };

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;

    // Кожен новий набір рекомендацій починаємо з першої картки
    track.scrollLeft = 0;

    setCanScrollLeft(false);

    const frame = requestAnimationFrame(() => {
      updateArrows();
    });

    const resizeObserver = new ResizeObserver(() => {
      updateArrows();
    });

    resizeObserver.observe(track);

    return () => {
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
    };
  }, [cards.length]);

  const scroll = (direction: 1 | -1) => {
    const track = trackRef.current;
    if (!track) return;

    const card = track.querySelector<HTMLElement>(".card");

    const amount = card ? card.offsetWidth + 14 : track.clientWidth * 0.25;

    track.scrollBy({
      left: amount * direction,
      behavior: "smooth",
    });
  };

  return (
    <div
      className={`recommendation-carousel recommendation-carousel-${variant}`}
    >
      <div className="carousel-track" ref={trackRef} onScroll={updateArrows}>
        {cards.length > 0 ? (
          cards.map((c, i) => (
            <Card
              key={c.title + i}
              data={c}
              t={t}
              hideTags
              hideReason
              onLocationClick={onLocationClick}
              onBookClick={onBookClick}
              onSalonDetailsClick={onSalonDetailsClick}
            />
          ))
        ) : (
          <p className="empty-results">{t.noResults}</p>
        )}
      </div>

      {canScrollLeft && (
        <button
          className="carousel-arrow carousel-arrow-prev"
          type="button"
          aria-label="Попередні рекомендації"
          onClick={() => scroll(-1)}
        >
          ‹
        </button>
      )}

      {canScrollRight && (
        <button
          className="carousel-arrow carousel-arrow-next"
          type="button"
          aria-label="Наступні рекомендації"
          onClick={() => scroll(1)}
        >
          ›
        </button>
      )}
    </div>
  );
}

function PartnerOffersCarousel({
  offers,
  lang,
  onLocationClick,
}: {
  offers: PartnerOffer[];
  lang: Lang;
  onLocationClick?: (
    name: string,
    district: string,
    distance: string,
    coordinates?: [number, number],
  ) => void;
}) {
  const trackRef = useRef<HTMLDivElement>(null);
  const ua = lang === "ua";

  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(offers.length > 4);

  const updateArrows = () => {
    const track = trackRef.current;
    if (!track) return;

    const maxScrollLeft = Math.max(0, track.scrollWidth - track.clientWidth);

    setCanScrollLeft(track.scrollLeft > 5);
    setCanScrollRight(track.scrollLeft < maxScrollLeft - 5);
  };

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;

    track.scrollLeft = 0;
    setCanScrollLeft(false);

    const frame = requestAnimationFrame(updateArrows);

    const resizeObserver = new ResizeObserver(updateArrows);
    resizeObserver.observe(track);

    return () => {
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
    };
  }, [offers.length]);

  const scroll = (direction: 1 | -1) => {
    const track = trackRef.current;
    if (!track) return;

    const card = track.querySelector<HTMLElement>(".partner-offer-card");

    const amount = card ? card.offsetWidth + 14 : track.clientWidth * 0.25;

    track.scrollBy({
      left: amount * direction,
      behavior: "smooth",
    });
  };

  return (
    <div className="partner-offers-carousel">
      <div
        className="partner-offers-track"
        ref={trackRef}
        onScroll={updateArrows}
      >
        {offers.length > 0 ? (
          offers.map((offer, i) => (
            <article className="partner-offer-card" key={`${offer.title}-${i}`}>
              <div
                className="partner-offer-image"
                style={
                  offer.image
                    ? { ["--partner-photo" as string]: `url(${offer.image})` }
                    : undefined
                }
              >
                <span className="partner-discount">{offer.discount}</span>

                <span className="partner-valid">{offer.validUntil}</span>

                {offer.gift && (
                  <span className="partner-gift">🎁 {offer.gift}</span>
                )}

                <FavButton />
              </div>

              <div className="partner-offer-body">
                <h3>{offer.title}</h3>

                <p className="partner-name">{offer.partner}</p>

                <div className="partner-card-meta">
                  <button
                    type="button"
                    className="card-location-link partner-location-link"
                    onClick={() =>
                      onLocationClick?.(
                        offer.partner,
                        offer.district,
                        offer.distance,
                        offer.coordinates,
                      )
                    }
                    title={ua ? "Показати на карті" : "Show on map"}
                  >
                    <span className="district-pin">
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#a855f7"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                        <circle cx="12" cy="10" r="3" />
                      </svg>
                      {offer.district}
                    </span>
                    <span>· {offer.distance}</span>
                  </button>
                  {offer.openNow && (
                    <span className="partner-availability">
                      ● {ua ? "Є вікна сьогодні" : "Slots today"}
                    </span>
                  )}
                </div>

                <div className="partner-price-row">
                  <span className="partner-old-price">
                    {offer.isDiscountOnly ? "" : `${offer.oldPrice} грн`}
                  </span>

                  <strong>
                    {offer.isDiscountOnly
                      ? ua
                        ? "Деталі в салоні"
                        : "Details at salon"
                      : `${offer.newPrice} грн`}
                  </strong>
                </div>

                <button type="button" className="partner-book-btn">
                  {ua ? "Записатися" : "Book now"}
                </button>

                <a href="#" className="partner-details-link">
                  {ua ? "Детальніше" : "Details"} →
                </a>
              </div>
            </article>
          ))
        ) : (
          <p className="empty-results">
            {ua
              ? "За цими параметрами акцій не знайдено"
              : "No offers match these filters"}
          </p>
        )}
      </div>

      {canScrollLeft && (
        <button
          className="partner-carousel-arrow partner-carousel-prev"
          type="button"
          aria-label={ua ? "Попередні пропозиції" : "Previous offers"}
          onClick={() => scroll(-1)}
        >
          ‹
        </button>
      )}

      {canScrollRight && (
        <button
          className="partner-carousel-arrow partner-carousel-next"
          type="button"
          aria-label={ua ? "Наступні пропозиції" : "Next offers"}
          onClick={() => scroll(1)}
        >
          ›
        </button>
      )}
    </div>
  );
}

function PartnerOffersSection({
  title,
  subtitle,
  link,
  offers,
  lang,
  onLocationClick,
}: {
  title: string;
  subtitle: string;
  link: string;
  offers: PartnerOffer[];
  lang: Lang;
  onLocationClick?: (
    name: string,
    district: string,
    distance: string,
    coordinates?: [number, number],
  ) => void;
}) {
  return (
    <section className="section partner-offers-section" id="promotions">
      <div className="section-head partner-section-head">
        <div className="partner-section-copy">
          <h2 className="section-title">
            <span className="accent">
              <svg
                className="section-icon"
                width="60"
                height="60"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M6 3h12l4 6-10 12L2 9z" />
                <path d="M11 3 8 9l4 12 4-12-3-6" />
                <path d="M2 9h20" />
              </svg>
            </span>
            {title}
          </h2>

          <p className="section-sub">{subtitle}</p>

          <a className="section-link partner-info-link" href="#partners-info">
            {link}
          </a>
        </div>
      </div>
      <PartnerOffersCarousel
        offers={offers}
        lang={lang}
        onLocationClick={onLocationClick}
      />
    </section>
  );
}

function KyivTopSection({
  cards,
  lang,
  onLocationClick,
  onSalonDetailsClick,
}: {
  cards: CardData[];
  lang: Lang;
  onLocationClick?: (
    name: string,
    district: string,
    distance: string,
    coordinates?: [number, number],
  ) => void;
  onSalonDetailsClick?: (salonId: number) => void;
}) {
  const trackRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(cards.length > 4);
  const ua = lang === "ua";

  const updateArrows = () => {
    const track = trackRef.current;
    if (!track) return;
    const maxScrollLeft = Math.max(0, track.scrollWidth - track.clientWidth);
    setCanScrollLeft(track.scrollLeft > 4);
    setCanScrollRight(track.scrollLeft < maxScrollLeft - 4);
  };

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    track.scrollLeft = 0;
    const frame = requestAnimationFrame(updateArrows);
    const observer = new ResizeObserver(updateArrows);
    observer.observe(track);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [cards.length]);

  const scroll = (direction: 1 | -1) => {
    const track = trackRef.current;
    if (!track) return;
    const card = track.querySelector<HTMLElement>(".kyiv-cover-card");
    const amount = card ? card.offsetWidth + 14 : track.clientWidth * 0.25;
    track.scrollBy({ left: amount * direction, behavior: "smooth" });
  };

  return (
    <section className="section kyiv-top-section" id="nearby">
      <div className="section-head kyiv-top-head">
        <div>
          <h2 className="section-title kyiv-top-title">
            <span className="kyiv-top-crown" aria-hidden="true">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M8 4h8v3a4 4 0 0 1-8 0V4Z" />
                <path d="M8 5H5v1a4 4 0 0 0 4 4" />
                <path d="M16 5h3v1a4 4 0 0 1-4 4" />
                <path d="M12 11v5" />
                <path d="M9 20h6" />
                <path d="M10 16h4v4h-4" />
              </svg>
            </span>
            {ua ? "Найкращі в Києві" : "Best in Kyiv"}
          </h2>
          <p className="section-sub">
            {ua
              ? "Салони та майстри з найвищими показниками"
              : "Top salons and masters by overall performance"}
          </p>
        </div>
        <span className="results-badge kyiv-top-badge">
          {ua ? `ТОП-${cards.length} У КИЄВІ` : `KYIV TOP ${cards.length}`}
        </span>
      </div>

      <div className="kyiv-top-carousel">
        <div className="kyiv-top-track" ref={trackRef} onScroll={updateArrows}>
          {cards.map((card, i) => (
            <article className="kyiv-cover-card" key={`${card.title}-${i}`}>
              <div
                className="kyiv-cover-photo"
                style={
                  card.image
                    ? { ["--kyiv-cover-photo" as string]: `url(${card.image})` }
                    : undefined
                }
              >
                <div className="kyiv-cover-shade" />

                <div className="kyiv-cover-topline">
                  <span className="kyiv-cover-kicker">
                    BEAUTY AI · KYIV TOP
                  </span>
                  <FavButton />
                </div>

                <span className="kyiv-cover-rank">{i + 1}</span>

                <div className="kyiv-cover-copy">
                  <span
                    className={`kyiv-cover-label kyiv-cover-label-${i % 4}`}
                  >
                    {card.badges[0]?.text ??
                      (ua ? "ВИБІР BEAUTY AI" : "BEAUTY AI PICK")}
                  </span>

                  <h3
                    className={
                      card.variant === "solo" ? "kyiv-cover-master-name" : ""
                    }
                  >
                    {card.title}
                  </h3>
                  <p className="kyiv-cover-type">{card.type}</p>

                  <div className="kyiv-cover-rating">
                    <span>★ {card.rating.toFixed(1)}</span>
                    <span>
                      {card.reviews} {ua ? "відгуків" : "reviews"}
                    </span>
                  </div>

                  <button
                    type="button"
                    className="kyiv-cover-location"
                    onClick={() =>
                      onLocationClick?.(
                        card.title,
                        card.district,
                        card.distance,
                        card.coordinates,
                      )
                    }
                    aria-label={
                      ua
                        ? `Показати ${card.title} на карті`
                        : `Show ${card.title} on map`
                    }
                  >
                    <svg
                      width="13"
                      height="13"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                      <circle cx="12" cy="10" r="3" />
                    </svg>
                    {card.district} · {card.distance}
                  </button>

                  <div className="kyiv-cover-footer">
                    <span className="kyiv-cover-price">
                      {ua ? "від" : "from"} {card.priceFrom} грн
                    </span>
                    {!card.variant && card.id && onSalonDetailsClick ? (
                      <button
                        type="button"
                        className="kyiv-cover-view kyiv-cover-view-button"
                        onClick={() => onSalonDetailsClick(card.id as number)}
                      >
                        {ua ? "Профіль" : "Profile"} →
                      </button>
                    ) : (
                      <span className="kyiv-cover-view">
                        {ua ? "Профіль" : "Profile"} →
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>

        {canScrollLeft && (
          <button
            className="carousel-arrow carousel-arrow-prev kyiv-top-arrow"
            type="button"
            aria-label={ua ? "Попередні" : "Previous"}
            onClick={() => scroll(-1)}
          >
            ‹
          </button>
        )}
        {canScrollRight && (
          <button
            className="carousel-arrow carousel-arrow-next kyiv-top-arrow"
            type="button"
            aria-label={ua ? "Наступні" : "Next"}
            onClick={() => scroll(1)}
          >
            ›
          </button>
        )}
      </div>
    </section>
  );
}

function PanelCarouselSection({
  title,
  subtitle,
  icon,
  cards,
  t,
  lang,
  variant,
  resultsWord,
  id,
  onLocationClick,
  onSalonDetailsClick,
}: {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  cards: CardData[];
  t: Translations;
  lang: Lang;
  variant: "nearby" | "worth-trying" | "fresh";
  resultsWord: string;
  id?: string;
  onLocationClick?: (
    name: string,
    district: string,
    distance: string,
    coordinates?: [number, number],
  ) => void;
  onSalonDetailsClick?: (salonId: number) => void;
}) {
  return (
    <section className="section subtle-panel-section" id={id}>
      <div className="section-head">
        <div>
          <h2 className="section-title">
            <span className="accent">{icon}</span> {title}
          </h2>
          <p className="section-sub">{subtitle}</p>
        </div>
        <span className="results-badge">
          {cards.length} {resultsWord}
        </span>
      </div>
      <RecommendationCarousel
        cards={cards}
        t={t}
        variant={variant}
        onLocationClick={onLocationClick}
        onSalonDetailsClick={onSalonDetailsClick}
      />
    </section>
  );
}

function formatReviewDate(value: string, lang: Lang) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(lang === "ua" ? "uk-UA" : "en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

function ReviewsSection({
  reviews,
  loading,
  error,
  lang,
}: {
  reviews: ApiReview[];
  loading: boolean;
  error: string | null;
  lang: Lang;
}) {
  const [selectedReview, setSelectedReview] = useState<ApiReview | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const openReview = async (reviewId: number) => {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const detail = await apiRequest<ApiReview>(
        `/api/reviews/${reviewId}/`,
        {},
        true,
        false,
      );
      setSelectedReview(detail);
    } catch (requestError) {
      setDetailError(
        requestError instanceof Error
          ? requestError.message
          : "Could not load review",
      );
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <>
      <section className="section reviews-section" id="reviews">
        <div className="section-head reviews-section-head">
          <div>
            <h2 className="section-title">
              <span className="accent">★</span>
              {lang === "ua" ? "Відгуки клієнтів" : "Customer reviews"}
            </h2>
            <p className="section-sub">
              {lang === "ua"
                ? "Реальні оцінки клієнтів Beauty AI"
                : "Real ratings from Beauty AI customers"}
            </p>
          </div>
          {!loading && !error && (
            <span className="results-badge">
              {reviews.length} {lang === "ua" ? "відгуків" : "reviews"}
            </span>
          )}
        </div>

        {loading && (
          <div className="reviews-state">
            {lang === "ua" ? "Завантажуємо відгуки…" : "Loading reviews…"}
          </div>
        )}

        {!loading && error && (
          <div className="reviews-state reviews-state-error">
            {lang === "ua"
              ? "Не вдалося завантажити відгуки з сервера."
              : "Could not load reviews from the server."}
          </div>
        )}

        {!loading && !error && reviews.length === 0 && (
          <div className="reviews-state">
            {lang === "ua"
              ? "Поки що відгуків немає."
              : "There are no reviews yet."}
          </div>
        )}

        {!loading && !error && reviews.length > 0 && (
          <div className="reviews-grid">
            {reviews.map((review) => (
              <button
                type="button"
                className="review-card"
                key={review.id}
                onClick={() => void openReview(review.id)}
                aria-label={
                  lang === "ua"
                    ? `Відкрити відгук ${review.id}`
                    : `Open review ${review.id}`
                }
              >
                <div className="review-card-topline">
                  <span
                    className="review-stars"
                    aria-label={`${review.rating} / 5`}
                  >
                    {"★".repeat(Math.max(0, Math.min(5, review.rating)))}
                    <span className="review-stars-muted">
                      {"★".repeat(Math.max(0, 5 - Math.min(5, review.rating)))}
                    </span>
                  </span>
                  <time dateTime={review.created_at}>
                    {formatReviewDate(review.created_at, lang)}
                  </time>
                </div>
                <p className="review-comment">
                  {review.comment ||
                    (lang === "ua" ? "Без коментаря" : "No comment")}
                </p>
                <span className="review-card-meta">
                  {lang === "ua"
                    ? `Майстер #${review.master}`
                    : `Master #${review.master}`}
                  <span aria-hidden="true">→</span>
                </span>
              </button>
            ))}
          </div>
        )}
      </section>

      {detailLoading && (
        <div className="review-modal-backdrop" role="presentation">
          <div
            className="review-modal-window"
            role="dialog"
            aria-modal="true"
            aria-label="Review"
          >
            <div className="reviews-state">
              {lang === "ua" ? "Завантаження…" : "Loading…"}
            </div>
          </div>
        </div>
      )}

      {detailError && !detailLoading && (
        <div
          className="review-modal-backdrop"
          role="presentation"
          onMouseDown={() => setDetailError(null)}
        >
          <div
            className="review-modal-window review-modal-error"
            role="alert"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="review-modal-close"
              onClick={() => setDetailError(null)}
              aria-label="Close"
            >
              ×
            </button>
            <p>
              {lang === "ua"
                ? "Не вдалося завантажити деталі відгуку."
                : "Could not load review details."}
            </p>
          </div>
        </div>
      )}

      {selectedReview && !detailLoading && (
        <div
          className="review-modal-backdrop"
          role="presentation"
          onMouseDown={() => setSelectedReview(null)}
        >
          <div
            className="review-modal-window"
            role="dialog"
            aria-modal="true"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="review-modal-close"
              onClick={() => setSelectedReview(null)}
              aria-label="Close"
            >
              ×
            </button>
            <span className="about-kicker">✦ BEAUTY AI</span>
            <div className="review-modal-rating">
              <span
                className="review-stars"
                aria-label={`${selectedReview.rating} / 5`}
              >
                {"★".repeat(Math.max(0, Math.min(5, selectedReview.rating)))}
                <span className="review-stars-muted">
                  {"★".repeat(
                    Math.max(0, 5 - Math.min(5, selectedReview.rating)),
                  )}
                </span>
              </span>
              <time dateTime={selectedReview.created_at}>
                {formatReviewDate(selectedReview.created_at, lang)}
              </time>
            </div>
            <p className="review-modal-comment">
              {selectedReview.comment ||
                (lang === "ua" ? "Без коментаря" : "No comment")}
            </p>
            <div className="review-modal-meta">
              <span>
                {lang === "ua"
                  ? `Запис #${selectedReview.appointment}`
                  : `Appointment #${selectedReview.appointment}`}
              </span>
              <span>
                {lang === "ua"
                  ? `Майстер #${selectedReview.master}`
                  : `Master #${selectedReview.master}`}
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function parseBackendCoordinates(
  salon: ApiSalon,
): [number, number] | undefined {
  const latitude = Number(salon.latitude);
  const longitude = Number(salon.longitude);
  if (Number.isFinite(latitude) && Number.isFinite(longitude))
    return [latitude, longitude];

  const coordinates = salon.location?.coordinates?.match(
    /POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)/i,
  );
  if (!coordinates) return undefined;

  const lng = Number(coordinates[1]);
  const lat = Number(coordinates[2]);
  return Number.isFinite(lat) && Number.isFinite(lng) ? [lat, lng] : undefined;
}

function apiSalonToCard(
  salon: ApiSalon,
  serviceNames: string[],
  index: number,
): CardData {
  const status = normalize(salon.available_status ?? "");
  const location = salon.location;
  const city = salon.city || location?.city_name || "";
  const district = salon.district || location?.region || city;
  const address =
    salon.address || location?.address || city || "Адреса не вказана";
  const statusIsOpen = ["open", "available", "відкрито", "available_now"].some(
    (value) => status.includes(value),
  );
  const statusIsClosed = ["closed", "unavailable", "закрит", "недоступ"].some(
    (value) => status.includes(value),
  );
  const todayWeekday = new Date().getDay() || 7;
  const todaySchedule = salon.working_hours?.find(
    (schedule) => schedule.weekday === todayWeekday,
  );
  const scheduleIsOpen = Boolean(
    todaySchedule &&
    !todaySchedule.is_closed &&
    todaySchedule.opening_time &&
    todaySchedule.closing_time,
  );
  const isOpen = statusIsOpen || (!statusIsClosed && scheduleIsOpen);
  const hasAvailabilityData = Boolean(
    statusIsOpen || statusIsClosed || todaySchedule,
  );
  const tags = serviceNames.slice(0, 4);
  return {
    id: salon.id,
    image: salon.logo || null,
    badges: [],
    title: salon.name,
    type: "Салон краси",
    rating: Number(salon.average_rating ?? 0),
    reviews: Number(salon.total_reviews ?? 0),
    district: district || "—",
    distance: "—",
    openNow: hasAvailabilityData ? isOpen : undefined,
    tags,
    priceFrom: "—",
    mastersCount: salon.masters_count
      ? `${salon.masters_count} майстрів`
      : undefined,
    locationNote: address,
    coordinates: parseBackendCoordinates(salon),
  };
}

function SalonDetailsModal({
  salonId,
  lang,
  onClose,
}: {
  salonId: number;
  lang: Lang;
  onClose: () => void;
}) {
  const [salon, setSalon] = useState<ApiSalon | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const ua = lang === "ua";

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setSalon(null);

    void getSalon(salonId)
      .then((result) => {
        if (!cancelled) setSalon(result);
      })
      .catch((requestError: unknown) => {
        if (!cancelled) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : ua
                ? "Не вдалося завантажити салон"
                : "Could not load salon",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [salonId, ua]);

  const location = salon?.location;
  const city = salon?.city || location?.city_name || "";
  const address =
    salon?.address ||
    location?.address ||
    city ||
    (ua ? "Адреса не вказана" : "Address unavailable");
  const district = salon?.district || location?.region || city;
  const status = normalize(salon?.available_status ?? "");
  const isAvailable = ["open", "available", "відкрито", "available_now"].some(
    (value) => status.includes(value),
  );
  const weekdays = ua
    ? [
        "",
        "Понеділок",
        "Вівторок",
        "Середа",
        "Четвер",
        "П’ятниця",
        "Субота",
        "Неділя",
      ]
    : [
        "",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
      ];

  return (
    <div
      className="salon-details-modal-backdrop"
      role="presentation"
      onMouseDown={onClose}
    >
      <div
        className="salon-details-modal-window"
        role="dialog"
        aria-modal="true"
        aria-labelledby="salon-details-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          className="salon-details-modal-close"
          onClick={onClose}
          aria-label={ua ? "Закрити" : "Close"}
        >
          ×
        </button>

        {loading && (
          <div className="salon-details-state">
            {ua ? "Завантаження даних салону…" : "Loading salon details…"}
          </div>
        )}

        {!loading && error && (
          <div className="salon-details-state salon-details-state-error">
            <p>{error}</p>
            <button
              type="button"
              className="salon-details-action"
              onClick={onClose}
            >
              {ua ? "Закрити" : "Close"}
            </button>
          </div>
        )}

        {!loading && !error && salon && (
          <>
            <div
              className="salon-details-hero"
              style={
                salon.logo
                  ? {
                      ["--salon-details-photo" as string]: `url(${salon.logo})`,
                    }
                  : undefined
              }
            >
              <div className="salon-details-hero-shade" />
              <span className="salon-details-kicker">BEAUTY AI · SALON</span>
            </div>

            <div className="salon-details-content">
              <div className="salon-details-title-row">
                <div>
                  <span className="about-kicker">
                    ✦ {ua ? "ПРО САЛОН" : "ABOUT THE SALON"}
                  </span>
                  <h2 id="salon-details-title">{salon.name}</h2>
                </div>
                <span
                  className={`salon-details-status ${isAvailable ? "is-available" : ""}`}
                >
                  {isAvailable
                    ? ua
                      ? "Доступний"
                      : "Available"
                    : ua
                      ? "Статус уточнюється"
                      : "Status unavailable"}
                </span>
              </div>

              <div className="salon-details-rating">
                <strong>
                  ★ {Number(salon.average_rating ?? 0).toFixed(1)}
                </strong>
                <span>
                  {salon.total_reviews ?? 0} {ua ? "відгуків" : "reviews"}
                </span>
              </div>

              <div className="salon-details-info">
                <span>⌖ {address}</span>
                {district && district !== address && <span>• {district}</span>}
                {salon.phone && (
                  <a href={`tel:${salon.phone}`}>☎ {salon.phone}</a>
                )}
              </div>

              <div className="salon-details-metrics">
                <div>
                  <strong>{salon.masters_count ?? 0}</strong>
                  <span>{ua ? "майстрів" : "masters"}</span>
                </div>
                <div>
                  <strong>{salon.service_count ?? 0}</strong>
                  <span>{ua ? "послуг" : "services"}</span>
                </div>
              </div>

              {salon.description && (
                <p className="salon-details-description">{salon.description}</p>
              )}

              <div className="salon-details-hours">
                <h3>{ua ? "Графік роботи" : "Working hours"}</h3>
                {salon.working_hours && salon.working_hours.length > 0 ? (
                  salon.working_hours.map((schedule) => (
                    <div
                      className="salon-details-hour-row"
                      key={`${salon.id}-${schedule.weekday}`}
                    >
                      <span>
                        {schedule.weekday
                          ? weekdays[schedule.weekday]
                          : ua
                            ? "День"
                            : "Day"}
                      </span>
                      <span>
                        {schedule.is_closed
                          ? ua
                            ? "Зачинено"
                            : "Closed"
                          : `${schedule.opening_time?.slice(0, 5) ?? "—"} – ${schedule.closing_time?.slice(0, 5) ?? "—"}`}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="salon-details-muted">
                    {ua
                      ? "Графік роботи ще не вказано"
                      : "Working hours are not available yet"}
                  </p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function apiMasterToCard(master: ApiMaster, index: number): CardData {
  const serviceNames = (master.services ?? []).map((service) => service.name);
  const salonName = master.salons?.[0]?.name;
  const firstService = master.services?.[0];
  const firstSalon = master.salons?.[0];
  const experience = master.years_of_experience
    ? `${master.years_of_experience} років досвіду`
    : undefined;
  return {
    id: master.id,
    image: master.photo || null,
    badges: [],
    title: `${master.first_name} ${master.last_name}`.trim(),
    type: serviceNames[0] ? `Майстер · ${serviceNames[0]}` : "Майстер",
    rating: Number(master.average_rating ?? 0),
    reviews: Number(master.total_reviews ?? 0),
    district: salonName || "—",
    distance: "—",
    tags: serviceNames,
    priceFrom: "—",
    experience,
    locationNote: salonName || undefined,
    profileLinkLabel: "Профіль майстра",
    variant: "solo",
    ...(firstService && firstSalon
      ? {
          booking: {
            master: master.id,
            salon: firstSalon.id,
            service: firstService.id,
            masterName: `${master.first_name} ${master.last_name}`.trim(),
            salonName: firstSalon.name,
            serviceName: firstService.name,
          },
        }
      : {}),
  };
}

function apiServiceMastersToCards(services: ApiService[]): CardData[] {
  const masters = new Map<
    number,
    {
      id: number;
      first_name: string;
      last_name: string;
      services: Map<number, { id: number; name: string }>;
      salons: Map<number, { id: number; name: string }>;
    }
  >();

  services.forEach((service) => {
    if (!Array.isArray(service.masters)) return;

    service.masters.forEach((master) => {
      const current = masters.get(master.id) ?? {
        id: master.id,
        first_name: master.first_name,
        last_name: master.last_name,
        services: new Map(),
        salons: new Map(),
      };
      current.services.set(service.id, { id: service.id, name: service.name });
      (service.salons ?? []).forEach((salon) =>
        current.salons.set(salon.id, salon),
      );
      masters.set(master.id, current);
    });
  });

  return Array.from(masters.values()).map((master) =>
    apiMasterToCard(
      {
        id: master.id,
        first_name: master.first_name,
        last_name: master.last_name,
        services: Array.from(master.services.values()),
        salons: Array.from(master.salons.values()),
      },
      master.id,
    ),
  );
}

function apiPromotionToOffer(
  promotion: ApiPromotion,
  salon?: ApiSalon,
): PartnerOffer {
  return {
    id: promotion.id,
    discount: `-${promotion.discount_percent}%`,
    validUntil: promotion.end_date
      ? `до ${new Date(promotion.end_date).toLocaleDateString("uk-UA")}`
      : "",
    title: promotion.name,
    partner: salon?.name ?? "",
    district:
      salon?.district ||
      salon?.location?.region ||
      salon?.location?.city_name ||
      "—",
    distance: "—",
    oldPrice: "—",
    newPrice: "—",
    gift: promotion.description,
    isDiscountOnly: true,
    coordinates: salon ? parseBackendCoordinates(salon) : undefined,
  };
}

type BookingSlot = { start: string; end: string };

function localDateInput(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function displayBookingDate(value: string, lang: Lang) {
  return new Intl.DateTimeFormat(lang === "ua" ? "uk-UA" : "en-US", {
    weekday: "short",
    day: "numeric",
    month: "short",
  }).format(new Date(`${value}T12:00:00`));
}

function slotTime(value: string) {
  const match = value.match(/T?(\d{2}:\d{2})/);
  return match?.[1] ?? value;
}

function bookingDateTime(date: string, time: string) {
  if (time.includes("T")) return new Date(time).toISOString();
  return new Date(
    `${date}T${time.length === 5 ? `${time}:00` : time}`,
  ).toISOString();
}

function BookingModal({
  card,
  lang,
  onClose,
  onCreated,
}: {
  card: CardData;
  lang: Lang;
  onClose: () => void;
  onCreated: (appointment: import("./api").ApiAppointment) => void;
}) {
  const ua = lang === "ua";
  const firstDate = localDateInput(new Date(Date.now() + 24 * 60 * 60 * 1000));
  const [dateFrom, setDateFrom] = useState(firstDate);
  const [slotsByDate, setSlotsByDate] = useState<Record<string, BookingSlot[]>>(
    {},
  );
  const [selectedDate, setSelectedDate] = useState(firstDate);
  const [selectedSlot, setSelectedSlot] = useState<BookingSlot | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!card.booking) return;
    const dateTo = localDateInput(
      new Date(
        new Date(`${dateFrom}T12:00:00`).getTime() + 6 * 24 * 60 * 60 * 1000,
      ),
    );
    setLoading(true);
    setError(null);
    setSelectedSlot(null);
    void apiRequest<Record<string, BookingSlot[]>>(
      `/api/appointments/available-slots/?salon=${card.booking.salon}&master=${card.booking.master}&service=${card.booking.service}&date_from=${dateFrom}&date_to=${dateTo}`,
    )
      .then((payload) => {
        setSlotsByDate(payload && typeof payload === "object" ? payload : {});
        setSelectedDate(Object.keys(payload ?? {})[0] ?? dateFrom);
      })
      .catch((requestError) => {
        setError(
          requestError instanceof Error
            ? requestError.message
            : ua
              ? "Не вдалося завантажити вільні вікна."
              : "Could not load available slots.",
        );
      })
      .finally(() => setLoading(false));
  }, [card.booking, dateFrom, ua]);

  const dates = Object.keys(slotsByDate);
  const slots = slotsByDate[selectedDate] ?? [];

  const submitBooking = async () => {
    if (!card.booking || !selectedSlot) return;
    setSaving(true);
    setError(null);
    try {
      const appointment = await createAppointment({
        master: card.booking.master,
        salon: card.booking.salon,
        service: card.booking.service,
        start: bookingDateTime(selectedDate, selectedSlot.start),
        end: bookingDateTime(selectedDate, selectedSlot.end),
      });
      onCreated(appointment);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : ua
            ? "Не вдалося створити запис."
            : "Could not create the booking.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="booking-modal-backdrop"
      role="presentation"
      onMouseDown={onClose}
    >
      <div
        className="booking-modal-window"
        role="dialog"
        aria-modal="true"
        aria-labelledby="booking-modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          className="booking-modal-close"
          onClick={onClose}
          aria-label={ua ? "Закрити" : "Close"}
        >
          ×
        </button>
        <span className="about-kicker">✦ BEAUTY AI</span>
        <h2 id="booking-modal-title">
          {ua ? "Записатися до майстра" : "Book an appointment"}
        </h2>
        <p className="booking-modal-subtitle">
          {card.booking?.masterName ?? card.title}
        </p>

        {!card.booking ? (
          <div className="booking-state booking-state-error">
            {ua
              ? "Для цього профілю поки немає підключених даних послуги та розкладу. Спробуйте майстра з позначкою LIVE API."
              : "This profile does not have connected service and schedule data yet. Try a master marked LIVE API."}
          </div>
        ) : (
          <>
            <div className="booking-summary">
              <span>{card.booking.serviceName}</span>
              <span>{card.booking.salonName}</span>
            </div>
            <label className="booking-date-field">
              <span>
                {ua ? "Показати вільні дати від" : "Show availability from"}
              </span>
              <input
                type="date"
                value={dateFrom}
                min={firstDate}
                onChange={(event) => setDateFrom(event.target.value)}
              />
            </label>
            {loading && (
              <div className="booking-state">
                {ua ? "Шукаємо вільні вікна…" : "Finding available slots…"}
              </div>
            )}
            {!loading && error && (
              <div className="booking-state booking-state-error">{error}</div>
            )}
            {!loading && !error && dates.length === 0 && (
              <div className="booking-state">
                {ua
                  ? "На найближчі дні вільних вікон немає."
                  : "There are no available slots for the next few days."}
              </div>
            )}
            {!loading && !error && dates.length > 0 && (
              <>
                <div
                  className="booking-date-tabs"
                  role="tablist"
                  aria-label={ua ? "Доступні дати" : "Available dates"}
                >
                  {dates.map((date) => (
                    <button
                      key={date}
                      type="button"
                      className={date === selectedDate ? "active" : ""}
                      onClick={() => {
                        setSelectedDate(date);
                        setSelectedSlot(null);
                      }}
                    >
                      <span>{displayBookingDate(date, lang)}</span>
                      <small>
                        {slotsByDate[date].length} {ua ? "вікон" : "slots"}
                      </small>
                    </button>
                  ))}
                </div>
                <div className="booking-slot-grid">
                  {slots.map((slot) => (
                    <button
                      key={`${slot.start}-${slot.end}`}
                      type="button"
                      className={selectedSlot === slot ? "active" : ""}
                      onClick={() => setSelectedSlot(slot)}
                    >
                      {slotTime(slot.start)} – {slotTime(slot.end)}
                    </button>
                  ))}
                </div>
                <button
                  className="cta-btn booking-submit-btn"
                  type="button"
                  disabled={!selectedSlot || saving}
                  onClick={() => void submitBooking()}
                >
                  {saving
                    ? ua
                      ? "Зберігаємо…"
                      : "Saving…"
                    : ua
                      ? "Підтвердити запис"
                      : "Confirm booking"}
                </button>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [lang, setLang] = useState<Lang>("ua");
  const [activeCategory, setActiveCategory] = useState("all");
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [authOpen, setAuthOpen] = useState(false);
  const [authIntent, setAuthIntent] = useState<{
    mode: "login" | "register";
    role: Exclude<AuthRole, "admin">;
    partnerKind?: "solo" | "salon";
  }>({
    mode: "login",
    role: "client",
  });
  const [partnerChoiceOpen, setPartnerChoiceOpen] = useState(false);
  const [user, setUser] = useState<MockUser | null>(null);
  const [view, setView] = useState<AppView>("home");
  const [authRestoring, setAuthRestoring] = useState(() =>
    Boolean(getAccessToken()),
  );
  const [verificationNotice, setVerificationNotice] = useState<string | null>(
    null,
  );
  const [verificationError, setVerificationError] = useState<string | null>(
    null,
  );
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [recommendationFiltersOpen, setRecommendationFiltersOpen] =
    useState(false);
  const [selectedMapLocation, setSelectedMapLocation] =
    useState<SelectedMapLocation | null>(null);
  const [selectedSalonId, setSelectedSalonId] = useState<number | null>(null);
  const [bookingCard, setBookingCard] = useState<CardData | null>(null);
  const [liveHomeData, setLiveHomeData] = useState<{
    salons?: CardData[];
    masters?: CardData[];
    promotions?: PartnerOffer[];
    reviews?: ApiReview[];
  }>({});
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [reviewsError, setReviewsError] = useState<string | null>(null);
  const t = dict[lang];

  useEffect(() => {
    if (!getAccessToken()) return;

    let cancelled = false;

    void getMe()
      .then((profile) => {
        if (cancelled) return;
        setUser(profileToMockUser(profile, lang));
        setView("dashboard");
      })
      .catch(() => {
        if (!cancelled) clearAuthTokens();
      })
      .finally(() => {
        if (!cancelled) setAuthRestoring(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const verificationId = params.get("id");
    const verificationToken = params.get("token");
    if (!verificationId || !verificationToken) return;

    let cancelled = false;
    setVerificationNotice(null);
    setVerificationError(null);

    void verifyEmail(verificationId, verificationToken)
      .then(() => {
        if (cancelled) return;
        setAuthIntent({ mode: "login", role: "client" });
        setVerificationNotice(
          lang === "ua"
            ? "Email підтверджено. Тепер увійдіть у свій акаунт."
            : "Your email is verified. You can now sign in.",
        );
        setAuthOpen(true);
      })
      .catch((error) => {
        if (cancelled) return;
        setVerificationError(
          getAuthErrorMessage(
            error,
            lang,
            lang === "ua"
              ? "Не вдалося підтвердити email. Посилання може бути недійсним або вже використаним."
              : "We could not verify your email. The link may be invalid or already used.",
          ),
        );
        setAuthIntent({ mode: "login", role: "client" });
        setAuthOpen(true);
      })
      .finally(() => {
        if (!cancelled) {
          window.history.replaceState(
            {},
            document.title,
            window.location.pathname,
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadHomeData = async () => {
      setReviewsLoading(true);
      setReviewsError(null);

      const [salonsResult, servicesResult, promotionsResult, reviewsResult] =
        await Promise.allSettled([
          apiRequest<{ results?: ApiSalon[] } | ApiSalon[]>(
            "/api/salons/?ordering=-rating&page=1",
            {},
            true,
            false,
          ),
          apiRequest<{ results?: ApiService[] } | ApiService[]>(
            "/api/services/?page=1",
            {},
            true,
            false,
          ),
          apiRequest<{ results?: ApiPromotion[] } | ApiPromotion[]>(
            "/api/promotions/?active=true&page=1",
            {},
            true,
            false,
          ),
          apiRequest<{ results?: ApiReview[] } | ApiReview[]>(
            "/api/reviews/?page=1",
            {},
            true,
            false,
          ),
        ]);

      if (cancelled) return;

      const salons =
        salonsResult.status === "fulfilled"
          ? apiResults(salonsResult.value)
          : [];
      const services =
        servicesResult.status === "fulfilled"
          ? apiResults(servicesResult.value)
          : [];
      const promotions =
        promotionsResult.status === "fulfilled"
          ? apiResults(promotionsResult.value)
          : [];
      const reviews =
        reviewsResult.status === "fulfilled"
          ? apiResults(reviewsResult.value)
          : [];
      const serviceMasterCards = apiServiceMastersToCards(
        services as ApiService[],
      );
      const serviceNamesBySalon = new Map<number, string[]>();

      setReviewsLoading(false);
      if (reviewsResult.status === "rejected") {
        setReviewsError(
          reviewsResult.reason instanceof Error
            ? reviewsResult.reason.message
            : "Reviews request failed",
        );
      }

      (services as ApiService[]).forEach((service) => {
        (service.salons ?? []).forEach((salon) => {
          const current = serviceNamesBySalon.get(salon.id) ?? [];
          if (!current.includes(service.name)) current.push(service.name);
          serviceNamesBySalon.set(salon.id, current);
        });
      });

      const salonCards =
        salons.length > 0
          ? salons.map((salon, index) =>
              apiSalonToCard(
                salon as ApiSalon,
                serviceNamesBySalon.get((salon as ApiSalon).id) ?? [],
                index,
              ),
            )
          : [];
      const salonsById = new Map(
        salons.map((salon) => [(salon as ApiSalon).id, salon as ApiSalon]),
      );

      setLiveHomeData({
        salons: salonCards,
        masters: serviceMasterCards,
        ...(promotionsResult.status === "fulfilled"
          ? {
              promotions: promotions.map((promotion) =>
                apiPromotionToOffer(
                  promotion as ApiPromotion,
                  salonsById.get((promotion as ApiPromotion).salon),
                ),
              ),
            }
          : {}),
        ...(reviewsResult.status === "fulfilled"
          ? { reviews: reviews as ApiReview[] }
          : {}),
      });

      // Masters are loaded separately so a protected or slow masters endpoint
      // can never delay or replace the salons section.
      void listMasters({ page: 1, ordering: "-rating" })
        .then((masters) => {
          if (cancelled || masters.length === 0) return;
          setLiveHomeData((current) => ({
            ...current,
            masters: masters.map((master, index) =>
              apiMasterToCard(master, index),
            ),
          }));
        })
        .catch(() => {
          // The public services response remains the fallback for masters.
        });
    };

    void loadHomeData();
    return () => {
      cancelled = true;
    };
  }, []);

  if (authRestoring) {
    return (
      <div
        className="app auth-session-loading"
        role="status"
        aria-live="polite"
      >
        {lang === "ua" ? "Відновлюємо сесію…" : "Restoring your session…"}
      </div>
    );
  }

  // Salons shown in the UI must always come from the backend endpoint.
  // An empty or failed API response stays empty instead of showing demo salons.
  const liveSalons = liveHomeData.salons ?? [];
  const liveMasters = liveHomeData.masters ?? [];
  const livePromotions = liveHomeData.promotions ?? [];
  const liveReviews = liveHomeData.reviews ?? [];
  const filteredRecommendations = liveSalons.filter((card) =>
    matchesCommonFilters(card, filters, activeCategory, searchQuery),
  );
  const filteredMasters = liveMasters.filter((card) =>
    matchesCommonFilters(card, filters, activeCategory, searchQuery),
  );
  const filteredPartners = livePromotions.filter((offer) =>
    matchesPartnerFilters(offer, filters, activeCategory, searchQuery),
  );
  const filteredNearby = liveSalons.filter((card) =>
    matchesCommonFilters(card, filters, activeCategory, searchQuery),
  );
  const filteredTopRated = liveSalons.filter((card) =>
    matchesCommonFilters(card, filters, activeCategory, searchQuery),
  );
  const filteredFresh = liveSalons.filter((card) =>
    matchesCommonFilters(card, filters, activeCategory, searchQuery),
  );

  const handleLocationClick = (
    name: string,
    district: string,
    distance: string,
    coordinates?: [number, number],
  ) => {
    if (!coordinates) return;
    setSelectedMapLocation({
      name,
      district,
      distance,
      lat: coordinates[0],
      lng: coordinates[1],
    });
  };

  const handleSalonDetailsClick = (salonId: number) => {
    setSelectedSalonId(salonId);
  };

  const handleBookClick = (card: CardData) => {
    if (!user) {
      setBookingCard(card);
      setAuthIntent({ mode: "login", role: "client" });
      setAuthOpen(true);
      return;
    }
    setBookingCard(card);
  };

  const handleAuthenticated = (nextUser: MockUser) => {
    setUser(nextUser);
    setAuthOpen(false);
    setView(bookingCard ? "home" : "dashboard");
  };

  const handleLogout = () => {
    setAccountMenuOpen(false);
    setUser(null);
    setView("home");
    clearAuthTokens();
  };

  if (view === "dashboard" && user) {
    return (
      <div className="app">
        <DashboardShell
          user={user}
          lang={lang}
          onHome={() => setView("home")}
          onRoleChange={(role) =>
            setUser((prev) => (prev ? { ...prev, role, avatar: null } : prev))
          }
        />
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <a className="logo" href="#" aria-label="Beauty AI — головна">
          <img
            src={beautyAISparkles}
            alt=""
            className="logo-sparkles"
            aria-hidden="true"
          />
          <span className="logo-wordmark">
            <span>Beauty</span> <strong>AI</strong>
          </span>
        </a>
        <nav className="nav">
          {t.nav.map((label, i) => (
            <a
              key={label}
              href={["#salons", "#masters", "#promotions", "#about"][i]}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="header-right">
          <button
            className="lang-select"
            onClick={() => setLang(lang === "ua" ? "en" : "ua")}
            aria-label="Switch language"
          >
            {lang === "ua" ? "UA" : "EN"} ˅
          </button>

          {user ? (
            <div className="account-menu-wrap">
              <button
                className="header-avatar-btn"
                onClick={() => setAccountMenuOpen((open) => !open)}
                aria-label={lang === "ua" ? "Меню акаунта" : "Account menu"}
                aria-expanded={accountMenuOpen}
              >
                {user.avatar ? (
                  <img src={user.avatar} alt={user.name} />
                ) : (
                  <span className="image-placeholder" aria-hidden="true">
                    ✦
                  </span>
                )}
              </button>

              {accountMenuOpen && (
                <>
                  <div
                    className="account-menu-backdrop"
                    onMouseDown={() => setAccountMenuOpen(false)}
                  />
                  <div className="account-menu" role="menu">
                    <button
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        setAccountMenuOpen(false);
                        setView("dashboard");
                      }}
                    >
                      {lang === "ua" ? "Мій кабінет" : "My account"}
                    </button>
                    <button
                      type="button"
                      role="menuitem"
                      className="account-menu-logout"
                      onClick={handleLogout}
                    >
                      {lang === "ua" ? "Вийти" : "Log out"}
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <button
              className="google-login-btn"
              onClick={() => {
                setAuthIntent({ mode: "login", role: "client" });
                setAuthOpen(true);
              }}
            >
              {t.loginGoogle}
            </button>
          )}
        </div>
      </header>

      <section className="hero-full-width">
        <div className="hero-overlay-content">
          <div className="hero-content">
            <div className="hero-eyebrow">
              <span>BEAUTY AI</span> — {t.heroEyebrow}
            </div>

            <h1 className="hero-title">
              <span className="hero-title-line">{t.heroTitle1}</span>
              <span className="hero-title-line hero-title-match">
                {t.heroTitle2}
              </span>
              <span className="hero-title-line">
                {lang === "ua" ? "ЗА ДОПОМОГОЮ" : "with the help of"}{" "}
                <span className="hero-title-ai">AI</span>
              </span>
            </h1>

            <p className="hero-subtitle">{t.heroSubtitle}</p>

            <form
              className="search-bar"
              onSubmit={(event) => {
                event.preventDefault();
                setSearchQuery(searchInput);
              }}
            >
              <input
                type="search"
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder={t.searchPlaceholder}
                aria-label={t.searchPlaceholder}
              />
              <button className="search-btn" type="submit">
                {t.searchBtn}
              </button>
            </form>
          </div>

          <div className="hero-categories">
            <CategoryFilters
              lang={lang}
              activeCategory={activeCategory}
              onCategoryChange={setActiveCategory}
            />
          </div>
        </div>
      </section>

      <section className="section ai-recommendations" id="salons">
        <div
          className={`recommendations-topline ${recommendationFiltersOpen ? "filters-open" : ""}`}
        >
          <div className="recommendations-heading">
            <h2 className="section-title">
              <span className="accent">
                <img
                  src={beautyAISparkles}
                  alt=""
                  className="beauty-ai-sparkles"
                  aria-hidden="true"
                />
              </span>
              {lang === "ua" ? (
                <>
                  Рекомендації Beauty{" "}
                  <span className="recommendations-ai">AI</span>
                </>
              ) : (
                <>
                  Beauty <span className="recommendations-ai">AI</span>{" "}
                  Recommendations
                </>
              )}
            </h2>
            <p className="section-sub">
              {lang === "ua"
                ? "Підібрано відповідно до вашого запиту"
                : "Selected for your request"}
            </p>
          </div>

          <div className="recommendations-filter-menu">
            <button
              className={`recommendations-filter-toggle ${recommendationFiltersOpen ? "is-open" : ""}`}
              type="button"
              aria-expanded={recommendationFiltersOpen}
              onClick={() => setRecommendationFiltersOpen((open) => !open)}
            >
              <span className="recommendations-filter-icon" aria-hidden="true">
                ☷
              </span>
              {lang === "ua" ? "Фільтри" : "Filters"}
              <span
                className="recommendations-filter-chevron"
                aria-hidden="true"
              >
                ⌄
              </span>
            </button>
          </div>

          {recommendationFiltersOpen && (
            <div className="recommendations-filter-panel">
              <FilterBar
                lang={lang}
                value={filters}
                onFilterChange={setFilters}
                onReset={() => {
                  setActiveCategory("all");
                  setSearchInput("");
                  setSearchQuery("");
                }}
              />
            </div>
          )}
        </div>

        <div className="recommendation-row recommendation-row-salons">
          <div className="recommendation-intro">
            <div className="recommendation-intro-head">
              <h2>
                <span className="row-symbol">✦</span>
                {t.sections.recommendations.title}
              </h2>
              <span className="results-count">
                {filteredRecommendations.length}{" "}
                {lang === "ua" ? "варіантів знайдено" : "options found"}
              </span>
            </div>
            <p>{t.sections.recommendations.subtitle}</p>
          </div>
          <RecommendationCarousel
            cards={filteredRecommendations}
            t={t}
            variant="salons"
            onLocationClick={handleLocationClick}
            onBookClick={handleBookClick}
            onSalonDetailsClick={handleSalonDetailsClick}
          />
        </div>

        <div
          className="recommendation-row recommendation-row-masters"
          id="masters"
        >
          <div className="recommendation-intro">
            <div className="recommendation-intro-head">
              <h2>
                <span className="row-symbol">✦</span>
                {t.sections.soloMasters.title}
              </h2>
              <span className="results-count">
                {filteredMasters.length}{" "}
                {lang === "ua" ? "майстрів знайдено" : "masters found"}
              </span>
            </div>
            <p>{t.sections.soloMasters.subtitle}</p>
          </div>
          <RecommendationCarousel
            cards={filteredMasters}
            t={t}
            variant="masters"
            onLocationClick={handleLocationClick}
            onBookClick={handleBookClick}
          />
        </div>
      </section>
      <div className="section-divider" aria-hidden="true">
        <span>✦</span>
      </div>
      <PartnerOffersSection
        title={t.sections.partners.title}
        subtitle={t.sections.partners.subtitle}
        link={t.partnersLink}
        offers={filteredPartners}
        lang={lang}
        onLocationClick={handleLocationClick}
      />

      <KyivTopSection
        cards={filteredNearby}
        lang={lang}
        onLocationClick={handleLocationClick}
        onSalonDetailsClick={handleSalonDetailsClick}
      />

      <PanelCarouselSection
        title={t.sections.topRated.title}
        subtitle={t.sections.topRated.subtitle}
        icon={
          <svg
            className="section-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m12 2.5 2.9 5.88 6.49.94-4.7 4.58 1.11 6.47L12 17.32l-5.8 3.05 1.11-6.47-4.7-4.58 6.49-.94L12 2.5Z" />
          </svg>
        }
        cards={filteredTopRated}
        t={t}
        lang={lang}
        variant="worth-trying"
        resultsWord={lang === "ua" ? "варіантів знайдено" : "options found"}
        id="worth-trying"
        onLocationClick={handleLocationClick}
        onSalonDetailsClick={handleSalonDetailsClick}
      />

      <PanelCarouselSection
        title={t.sections.fresh.title}
        subtitle={t.sections.fresh.subtitle}
        icon={
          <svg
            className="section-icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z" />
            <circle
              cx="7.5"
              cy="7.5"
              r="1.5"
              fill="currentColor"
              stroke="none"
            />
          </svg>
        }
        cards={filteredFresh}
        t={t}
        lang={lang}
        variant="fresh"
        resultsWord={lang === "ua" ? "новинок знайдено" : "new listings"}
        id="fresh"
        onLocationClick={handleLocationClick}
        onSalonDetailsClick={handleSalonDetailsClick}
      />

      <ReviewsSection
        reviews={liveReviews}
        loading={reviewsLoading}
        error={reviewsError}
        lang={lang}
      />

      <section className="about-section" id="about">
        <div className="about-main">
          <span className="about-kicker">✦ BEAUTY AI</span>
          <h2>{t.about.title}</h2>
          <p>{t.about.description}</p>
        </div>

        <div className="about-column">
          <h3>{t.about.contactsTitle}</h3>

          <a href="mailto:support@beautyai.ua">support@beautyai.ua</a>

          <a href="#">Telegram</a>
        </div>

        <div className="about-column about-partners" id="partners-info">
          <h3>{t.about.partnersTitle}</h3>
          <p>{t.about.partnersText}</p>

          <button
            className="partner-btn"
            onClick={() => setPartnerChoiceOpen(true)}
          >
            {t.about.partnersCta}
          </button>
        </div>
      </section>

      <p className="footer-note">ⓘ {t.footer} ✦</p>

      {partnerChoiceOpen && (
        <div
          className="partner-choice-backdrop"
          role="presentation"
          onMouseDown={() => setPartnerChoiceOpen(false)}
        >
          <div
            className="partner-choice-window"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <span className="partner-choice-kicker">✦ BEAUTY AI</span>
            <h3>{lang === "ua" ? "Хто ви?" : "Who are you?"}</h3>
            <p>
              {lang === "ua"
                ? "Оберіть, як вам зручніше приєднатись до Beauty AI"
                : "Choose how you'd like to join Beauty AI"}
            </p>

            <div className="partner-choice-options">
              <button
                type="button"
                onClick={() => {
                  setAuthIntent({
                    mode: "register",
                    role: "master",
                    partnerKind: "solo",
                  });
                  setPartnerChoiceOpen(false);
                  setAuthOpen(true);
                }}
              >
                <span className="partner-choice-title">
                  {lang === "ua" ? "Соло-майстер" : "Solo master"}
                </span>
                <span className="partner-choice-desc">
                  {lang === "ua"
                    ? "Працюю сам(а), без прив'язки до салону"
                    : "I work independently, no salon"}
                </span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setAuthIntent({
                    mode: "register",
                    role: "master",
                    partnerKind: "salon",
                  });
                  setPartnerChoiceOpen(false);
                  setAuthOpen(true);
                }}
              >
                <span className="partner-choice-title">
                  {lang === "ua" ? "Власник салону" : "Salon owner"}
                </span>
                <span className="partner-choice-desc">
                  {lang === "ua"
                    ? "Керую закладом з кількома майстрами"
                    : "I run a business with multiple masters"}
                </span>
              </button>
            </div>
          </div>
        </div>
      )}

      {authOpen && (
        <AuthModal
          lang={lang}
          onClose={() => {
            setAuthOpen(false);
            setVerificationNotice(null);
            setVerificationError(null);
          }}
          onAuthenticated={handleAuthenticated}
          initialMode={authIntent.mode}
          initialRole={authIntent.role}
          initialPartnerKind={authIntent.partnerKind}
          initialError={verificationError}
          initialSuccess={verificationNotice}
        />
      )}

      {selectedSalonId !== null && (
        <SalonDetailsModal
          salonId={selectedSalonId}
          lang={lang}
          onClose={() => setSelectedSalonId(null)}
        />
      )}

      {selectedMapLocation && (
        <div
          className="map-modal-backdrop"
          role="presentation"
          onMouseDown={() => setSelectedMapLocation(null)}
        >
          <div
            className="map-modal-window"
            onMouseDown={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="map-modal-close"
              onClick={() => setSelectedMapLocation(null)}
              aria-label={lang === "ua" ? "Закрити" : "Close"}
            >
              ×
            </button>
            <MapSection lang={lang} selectedLocation={selectedMapLocation} />
          </div>
        </div>
      )}

      {bookingCard && user && (
        <BookingModal
          card={bookingCard}
          lang={lang}
          onClose={() => setBookingCard(null)}
          onCreated={() => {
            setBookingCard(null);
            setView("dashboard");
          }}
        />
      )}
    </div>
  );
}
