import React from "react";
import DashboardFrame from "../DashboardFrame";
import type { AuthRole, Lang, MockUser } from "../types";

export default function AdminDashboard({ user, lang, onHome, onRoleChange }: { user: MockUser; lang: Lang; onHome: () => void; onRoleChange: (role: AuthRole) => void }) {
  const ua = lang === "ua";
  const cards: [string,string,string][] = [[ua?"Користувачі":"Users","2 486",ua?"+42 за тиждень":"+42 this week"],[ua?"Майстри":"Masters","684",ua?"51 на модерації":"51 pending"],[ua?"Записи":"Bookings","1 942",ua?"за останні 30 днів":"last 30 days"]];
  const modules = [ua?"Клієнти":"Clients",ua?"Майстри":"Masters",ua?"Салони":"Salons",ua?"Послуги":"Services",ua?"Записи":"Bookings",ua?"Платежі":"Payments",ua?"Відгуки":"Reviews",ua?"Аналітика":"Analytics",ua?"Налаштування":"Settings"];
  return <DashboardFrame user={user} lang={lang} onHome={onHome} onRoleChange={onRoleChange} title={ua?"Адмін-панель":"Admin panel"} cards={cards}><section className="dashboard-panel admin-grid-panel"><div className="dashboard-panel-head"><div><h2>{ua?"Керування платформою":"Platform management"}</h2><p>{ua?"React-версія адмінки в єдиному стилі Beauty AI":"React admin area in the Beauty AI design system"}</p></div></div><div className="admin-module-grid">{modules.map(item=><button className="admin-module" key={item}>{item}<span>→</span></button>)}</div></section></DashboardFrame>;
}
