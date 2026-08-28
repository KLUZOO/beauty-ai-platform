import React from "react";
import { Footprints } from "lucide-react";

const IconBase = ({ children }: { children: React.ReactNode }) => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    {children}
  </svg>
);

const Icons = {
  Manicure: () => (
    <IconBase>
      <path d="M15 5l4 4" />
      <path d="M13 7l-4.3-4.3a2.41 2.41 0 0 0-3.4 0L2.7 5.3a2.41 2.41 0 0 0 0 3.4L7 13" />
      <path d="M8 6l5 5" />
      <path d="M14 12l7.3 7.3a2.41 2.41 0 0 1 0 3.4l-.6.6a2.41 2.41 0 0 1-3.4 0L10 16" />
    </IconBase>
  ),
  Pedicure: () => <Footprints size={18} strokeWidth={1.8} />,
  Scissors: () => (
    <IconBase>
      <circle cx="6" cy="6" r="3" />
      <circle cx="6" cy="18" r="3" />
      <line x1="20" y1="4" x2="8.12" y2="15.88" />
      <line x1="14.47" y1="14.48" x2="20" y2="20" />
      <line x1="8.12" y1="8.12" x2="12" y2="12" />
    </IconBase>
  ),
  Palette: () => (
    <IconBase>
      <circle cx="13.5" cy="6.5" r=".5" fill="currentColor" />
      <circle cx="17.5" cy="10.5" r=".5" fill="currentColor" />
      <circle cx="8.5" cy="7.5" r=".5" fill="currentColor" />
      <circle cx="6.5" cy="12.5" r=".5" fill="currentColor" />
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.92 0 1.67-.75 1.67-1.67 0-.42-.16-.8-.43-1.09-.27-.29-.43-.68-.43-1.09 0-.92.75-1.67 1.67-1.67H16c3.31 0 6-2.69 6-6 0-4.96-4.49-9-10-9z" />
    </IconBase>
  ),
  Botox: () => (
    <IconBase>
      <path d="m18 2 4 4" />
      <path d="m17 7 3-3" />
      <path d="M19 9 8.7 19.3a1 1 0 0 1-1.4 0l-2.6-2.6a1 1 0 0 1 0-1.4L15 5" />
      <path d="m9 11 4 4" />
      <path d="m5 19-3 3" />
    </IconBase>
  ),
  Massage: () => (
    <IconBase>
      <path d="M18 11V6a2 2 0 0 0-4 0" />
      <path d="M14 10V4a2 2 0 0 0-4 0v6" />
      <path d="M10 10.5V6a2 2 0 0 0-4 0v8" />
      <path d="M18 8a2 2 0 0 1 2 2v4a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.83L7 15" />
    </IconBase>
  ),
  Eyelashes: () => (
    <IconBase>
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </IconBase>
  ),
  Brows: () => (
    <IconBase>
      {/* Брова */}
      <path d="M3.5 10.5c2.8-2.7 5.7-4 8.8-3.9 3.2.1 5.9 1.3 8.2 3.4" />

      {/* Лінія ока / вій */}
      <path d="M4 14c2.2 1.8 4.8 2.7 7.8 2.7 3.2 0 6-1 8.2-3" />

      {/* Вії */}
      <path d="M6.2 15.2 5.2 17" />
      <path d="M9 16.2 8.6 18.2" />
      <path d="M12 16.7v2" />
      <path d="M15 16.2l.5 2" />
      <path d="M17.8 15.2l1 1.8" />
    </IconBase>
  ),
  Makeup: () => (
    <IconBase>
      <path d="M9 3h6v7H9z" />
      <path d="M8 10h8v11H8z" />
      <path d="M10.5 3V1.8" />
      <path d="M13.5 3V1.8" />
    </IconBase>
  ),
  Cosmetology: () => (
    <IconBase>
      <path d="M12 3c-4 0-7 3.2-7 7.4V14c0 4 3.1 7 7 7s7-3 7-7v-3.6C19 6.2 16 3 12 3z" />
      <path d="M9 11h.01" />
      <path d="M15 11h.01" />
      <path d="M9.7 16c1.3.9 3.3.9 4.6 0" />
    </IconBase>
  ),
  Depilation: () => (
    <IconBase>
      <path d="M5 19 19 5" />
      <path d="M7.5 6.5c1.1 1.4 1.1 3 0 4.4" />
      <path d="M11.5 4.8c1.1 1.4 1.1 3 0 4.4" />
      <path d="M15.5 3.6c1.1 1.4 1.1 3 0 4.4" />
    </IconBase>
  ),
  Solarium: () => (
    <IconBase>
      <circle cx="12" cy="12" r="3.5" />
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2" />
      <path d="m4.93 4.93 1.42 1.42m11.3 11.3 1.42 1.42M6.35 17.65l-1.42 1.42M19.07 4.93l-1.42 1.42" />
    </IconBase>
  ),
  Facial: () => (
    <IconBase>
      <path d="M12 3c-4 0-7 3.2-7 7.4V14c0 4 3.1 7 7 7s7-3 7-7v-3.6C19 6.2 16 3 12 3z" />
      <path d="M8.8 10.8h.01M15.2 10.8h.01M10 16h4" />
      <path d="m18.2 4 1-2m1 4 2-1" />
    </IconBase>
  ),
  Spa: () => (
    <IconBase>
      <path d="M12 21c0-5 3-8 8-9-1 5-3.5 8-8 9Z" />
      <path d="M12 21c0-5-3-8-8-9 1 5 3.5 8 8 9Z" />
      <path d="M12 21c-2.5-5-2.2-9 0-13 2.2 4 2.5 8 0 13Z" />
    </IconBase>
  ),
};

interface CategoryFiltersProps {
  lang?: "ua" | "en";
  activeCategory?: string;
  onCategoryChange?: (category: string) => void;
}

export default function CategoryFilters({
  lang = "ua",
  activeCategory = "all",
  onCategoryChange,
}: CategoryFiltersProps) {
  const isEn = lang === "en";

  const mainCategories = [
    { id: "all", label: isEn ? "All" : "Усі", icon: null },
    { id: "manicure", label: isEn ? "Manicure" : "Манікюр", icon: Icons.Manicure },
    { id: "pedicure", label: isEn ? "Pedicure" : "Педикюр", icon: Icons.Pedicure },
    { id: "haircut", label: isEn ? "Haircut" : "Стрижка", icon: Icons.Scissors },
    { id: "coloring", label: isEn ? "Coloring" : "Фарбування", icon: Icons.Palette },
    { id: "botox", label: isEn ? "Botox" : "Ботокс", icon: Icons.Botox },
    { id: "massage", label: isEn ? "Massage" : "Масаж", icon: Icons.Massage },
    { id: "eyelashes", label: isEn ? "Eyelashes" : "Нарощування вій", icon: Icons.Eyelashes },
  ];

  const extraCategories = [
    { id: "brows", label: isEn ? "Brows & Lashes" : "Брови та вії", icon: Icons.Brows },
    { id: "makeup", label: isEn ? "Makeup" : "Макіяж", icon: Icons.Makeup },
    { id: "cosmetology", label: isEn ? "Cosmetology" : "Косметологія", icon: Icons.Cosmetology },
    { id: "depilation", label: isEn ? "Depilation" : "Депіляція", icon: Icons.Depilation },
    { id: "solarium", label: isEn ? "Solarium" : "Солярій", icon: Icons.Solarium },
    { id: "facial", label: isEn ? "Facial" : "Чистка обличчя", icon: Icons.Facial },
    { id: "spa", label: "SPA", icon: Icons.Spa },
  ];

  const renderCategory = (cat: typeof mainCategories[number]) => {
    const IconComponent = cat.icon;

    return (
      <button
        key={cat.id}
        className={`category-chip ${activeCategory === cat.id ? "active" : ""}`}
        onClick={() => onCategoryChange?.(cat.id)}
      >
        {IconComponent && (
          <span className="chip-icon">
            <IconComponent />
          </span>
        )}
        <span>{cat.label}</span>
      </button>
    );
  };

  return (
    <div className="categories-container">
      <div className="categories-row">
        {mainCategories.map(renderCategory)}
      </div>

      <div className="categories-row extra-row">
        {extraCategories.map(renderCategory)}
      </div>
    </div>
  );
}
