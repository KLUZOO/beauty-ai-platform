export type FilterState = {
  priceMin: string;
  priceMax: string;
  rating: string;
  distance: string;
  availability: string;
  city: string;
  district: string;
  service: string;
  venueType: string;
};

export const DEFAULT_FILTERS: FilterState = {
  priceMin: "",
  priceMax: "",
  rating: "from45",
  distance: "to3km",
  availability: "today",
  city: "kyiv",
  district: "any",
  service: "any",
  venueType: "any",
};