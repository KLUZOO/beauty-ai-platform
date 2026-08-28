import React, { useState } from "react";
import { DEFAULT_FILTERS, type FilterState } from "./filterTypes.ts";

type Lang = "ua" | "en";
interface FilterBarProps {
  lang?: Lang;
  value?: FilterState;
  onFilterChange?: (filters: FilterState) => void;
  onReset?: () => void;
}

const data = {
  ua: {
    price: "Ціна",
    from: "Від",
    to: "До",
    currency: "грн",
    rating: "Рейтинг",
    distance: "Відстань",
    availability: "Доступність",
    city: "Місто",
    district: "Район",
    service: "Послуги",
    venueType: "Тип закладу",
    reset: "Скинути всі фільтри",
    apply: "Показати результати",
    ratings: [
      ["any", "Будь-який"],
      ["from40", "Від 4.0 ⭐"],
      ["from45", "Від 4.5 ⭐"],
      ["from49", "4.9+ ⭐"],
    ],
    distances: [
      ["any", "Будь-яка"],
      ["to1km", "До 1 км"],
      ["to3km", "До 3 км"],
      ["to5km", "До 5 км"],
    ],
    availabilityOptions: [
      ["anytime", "Будь-коли"],
      ["today", "Сьогодні"],
      ["tomorrow", "Завтра"],
      ["week", "Цього тижня"],
    ],
    cities: [
      ["any", "Будь-яке місто"],
      ["kyiv", "Київ"],
      ["lviv", "Львів"],
      ["odesa", "Одеса"],
      ["dnipro", "Дніпро"],
    ],
    districts: [
      ["any", "Будь-який район"],
      ["pecherskyi", "Печерський"],
      ["shevchenkivskyi", "Шевченківський"],
      ["podilskyi", "Подільський"],
      ["holosiivskyi", "Голосіївський"],
    ],
    services: [
      ["any", "Будь-яка послуга"],
      ["hair", "Волосся"],
      ["nails", "Манікюр / педикюр"],
      ["brows", "Брови / вії"],
      ["makeup", "Макіяж"],
      ["massage", "Масаж / SPA"],
    ],
    venueTypes: [
      ["any", "Будь-який"],
      ["salon", "Салон"],
      ["studio", "Студія"],
      ["solo", "Приватний майстер"],
    ],
  },
  en: {
    price: "Price",
    from: "From",
    to: "To",
    currency: "UAH",
    rating: "Rating",
    distance: "Distance",
    availability: "Availability",
    city: "City",
    district: "District",
    service: "Services",
    venueType: "Venue type",
    reset: "Reset all filters",
    apply: "Show results",
    ratings: [
      ["any", "Any"],
      ["from40", "From 4.0 ⭐"],
      ["from45", "From 4.5 ⭐"],
      ["from49", "4.9+ ⭐"],
    ],
    distances: [
      ["any", "Any"],
      ["to1km", "Up to 1 km"],
      ["to3km", "Up to 3 km"],
      ["to5km", "Up to 5 km"],
    ],
    availabilityOptions: [
      ["anytime", "Anytime"],
      ["today", "Today"],
      ["tomorrow", "Tomorrow"],
      ["week", "This week"],
    ],
    cities: [
      ["any", "Any city"],
      ["kyiv", "Kyiv"],
      ["lviv", "Lviv"],
      ["odesa", "Odesa"],
      ["dnipro", "Dnipro"],
    ],
    districts: [
      ["any", "Any district"],
      ["pecherskyi", "Pecherskyi"],
      ["shevchenkivskyi", "Shevchenkivskyi"],
      ["podilskyi", "Podilskyi"],
      ["holosiivskyi", "Holosiivskyi"],
    ],
    services: [
      ["any", "Any service"],
      ["hair", "Hair"],
      ["nails", "Nails"],
      ["brows", "Brows / lashes"],
      ["makeup", "Makeup"],
      ["massage", "Massage / SPA"],
    ],
    venueTypes: [
      ["any", "Any"],
      ["salon", "Salon"],
      ["studio", "Studio"],
      ["solo", "Independent master"],
    ],
  },
} as const;
export default function FilterBar({
  lang = "ua",
  value,
  onFilterChange,
  onReset,
}: FilterBarProps) {
  const [filters, setFilters] = useState<FilterState>(value ?? DEFAULT_FILTERS);
  const t = data[lang];
  const update = (key: keyof FilterState, nextValue: string) => {
    const next = { ...filters, [key]: nextValue };
    setFilters(next);
    onFilterChange?.(next);
  };
  const reset = () => {
    const x: FilterState = {
      priceMin: "",
      priceMax: "",
      rating: "any",
      distance: "any",
      availability: "anytime",
      city: "any",
      district: "any",
      service: "any",
      venueType: "any",
    };
    setFilters(x);
    onFilterChange?.(x);
    onReset?.();
  };
  const select = (
    label: string,
    key: keyof FilterState,
    opts: readonly (readonly [string, string])[],
  ) => (
    <label className="filter-field">
      <span className="filter-field-label">{label}</span>
      <select
        value={filters[key]}
        onChange={(e) => update(key, e.target.value)}
      >
        {opts.map(([v, n]) => (
          <option key={v} value={v}>
            {n}
          </option>
        ))}
      </select>
    </label>
  );
  return (
    <div className="filter-panel-content">
      <div className="filter-panel-grid">
        <div className="filter-field filter-price-field">
          <span className="filter-field-label">{t.price}</span>
          <div className="filter-price-inputs">
            <label>
              <span>{t.from}</span>
              <div className="filter-price-box">
                <input
                  type="number"
                  min="0"
                  step="50"
                  inputMode="numeric"
                  value={filters.priceMin}
                  onChange={(e) => update("priceMin", e.target.value)}
                  placeholder="0"
                />
                <b>{t.currency}</b>
              </div>
            </label>
            <span className="filter-price-dash">—</span>
            <label>
              <span>{t.to}</span>
              <div className="filter-price-box">
                <input
                  type="number"
                  min="0"
                  step="50"
                  inputMode="numeric"
                  value={filters.priceMax}
                  onChange={(e) => update("priceMax", e.target.value)}
                  placeholder="3000"
                />
                <b>{t.currency}</b>
              </div>
            </label>
          </div>
        </div>
        {select(t.rating, "rating", t.ratings)}
        {select(t.distance, "distance", t.distances)}
        {select(t.availability, "availability", t.availabilityOptions)}
        {select(t.city, "city", t.cities)}
        {select(t.district, "district", t.districts)}
        {select(t.service, "service", t.services)}
        {select(t.venueType, "venueType", t.venueTypes)}
      </div>
      <div className="filter-panel-actions">
        <button className="filter-reset-btn" type="button" onClick={reset}>
          <span className="filter-reset-icon" aria-hidden="true">
            ↺
          </span>
          {t.reset}
        </button>
        <button
          className="filter-apply-btn"
          type="button"
          onClick={() => onFilterChange?.(filters)}
        >
          {t.apply}
        </button>
      </div>
    </div>
  );
}
