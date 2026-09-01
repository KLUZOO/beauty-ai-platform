import React from "react";
import type { AuthRole, Lang, MockUser } from "./types";

export type StatCard = [string, string, string];
export type MasterSection = "home" | "profile" | "finance";

type DashboardFrameProps = {
  user: MockUser;
  lang: Lang;
  onHome: () => void;
  onRoleChange: (role: AuthRole) => void;
  title: string;
  cards?: StatCard[];
  children: React.ReactNode;
  variant?: "default" | "master";
  activeSection?: MasterSection;
  onSectionChange?: (section: MasterSection) => void;
};

export default function DashboardFrame({
  user,
  lang,
  onHome,
  onRoleChange,
  title,
  cards = [],
  children,
  variant = "default",
  activeSection = "home",
  onSectionChange,
}: DashboardFrameProps) {
  const ua = lang === "ua";

  if (variant === "master") {
    const nav = [
      ["home", "⌂", ua ? "Головна" : "Home"],
      ["profile", "○", ua ? "Профіль" : "Profile"],
      ["finance", "₴", ua ? "Фінанси" : "Finance"],
    ] as const;

    return (
      <main className="master-cabinet-v2">
        <aside className="master-sidebar-v2">
          <button className="master-brand-v2" type="button" onClick={onHome}>
            <span className="master-brand-spark">✦</span>
            <span>Beauty <b>AI</b></span>
          </button>

          <nav className="master-nav-v2" aria-label={ua ? "Навігація кабінету" : "Account navigation"}>
            {nav.map(([id, icon, label]) => (
              <button
                key={id}
                type="button"
                className={activeSection === id ? "active" : ""}
                onClick={() => onSectionChange?.(id)}
              >
                <span className="master-nav-icon-v2">{icon}</span>{label}
              </button>
            ))}
          </nav>

          <button className="master-logout-v2" type="button" onClick={() => onRoleChange("client")}>↪ <span>{ua ? "Вийти" : "Log out"}</span></button>

          <div className="master-level-v2">
            <span className="master-level-icon-v2">♕</span>
            <div><b>{ua ? "Рівень Pro" : "Pro level"}</b><small>{ua ? "Майстер Beauty AI" : "Beauty AI master"}</small></div>
          </div>
        </aside>

        <section className="master-workspace-v2">
          <header className="master-header-v2">
            <div>
              <h1>{title}</h1>
              <p>{activeSection === "home" ? (ua ? "Керуйте записами та робочим днем" : "Manage bookings and your workday") : activeSection === "profile" ? (ua ? "Ваш профіль у Beauty AI" : "Your Beauty AI profile") : (ua ? "Доходи та виплати" : "Income and payouts")}</p>
            </div>
            <div className="master-header-actions-v2">
              <button className="master-notification-v2" type="button" aria-label={ua ? "Сповіщення" : "Notifications"}>♢<span>2</span></button>
              <div className="master-user-v2">{user.avatar ? <img src={user.avatar} alt={user.name} /> : <span className="image-placeholder" aria-hidden="true">✦</span>}<div><b>{user.name}</b><small>{ua ? "Майстер" : "Master"}</small></div><span>⌄</span></div>
            </div>
          </header>
          <div className="master-content-v2">{children}</div>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-page">
      <div className="dashboard-topbar">
        <button className="dashboard-back" type="button" onClick={onHome}>← {ua ? "На головну" : "Home"}</button>
        <div className="dashboard-role-demo">
          {(["client", "master", "admin"] as AuthRole[]).map((role) => (
            <button key={role} className={user.role === role ? "active" : ""} type="button" onClick={() => onRoleChange(role)}>
              {role === "client" ? (ua ? "Клієнт" : "Client") : role === "master" ? (ua ? "Майстер" : "Master") : "Admin"}
            </button>
          ))}
        </div>
      </div>
      <section className="dashboard-hero">
        <div><span className="dashboard-kicker">✦ BEAUTY AI</span><h1>{title}</h1><p>{user.email}</p></div>
        <div className="dashboard-avatar">{user.avatar ? <img src={user.avatar} alt={user.name} /> : <span className="image-placeholder" aria-hidden="true">✦</span>}</div>
      </section>
      {cards.length > 0 && <section className="dashboard-stats">
        {cards.map(([cardTitle, value, caption]) => (
          <article className="dashboard-stat-card" key={cardTitle}><span>{cardTitle}</span><strong>{value}</strong><p>{caption}</p></article>
        ))}
      </section>}
      {children}
    </main>
  );
}
