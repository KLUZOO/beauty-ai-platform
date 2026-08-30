import React from "react";
import DashboardFrame from "../DashboardFrame";
import type { AuthRole, Lang, MockUser } from "../types";
import BusinessOperationsPanel from "./BusinessOperationsPanel";

export default function AdminDashboard({ user, lang, onHome, onRoleChange }: { user: MockUser; lang: Lang; onHome: () => void; onRoleChange: (role: AuthRole) => void }) {
  const ua = lang === "ua";
  const cards: [string,string,string][] = [[ua?"Користувачі":"Users","2 486",ua?"+42 за тиждень":"+42 this week"],[ua?"Майстри":"Masters","684",ua?"51 на модерації":"51 pending"],[ua?"Записи":"Bookings","1 942",ua?"за останні 30 днів":"last 30 days"]];
  return (
    <DashboardFrame user={user} lang={lang} onHome={onHome} onRoleChange={onRoleChange} title={ua ? "Адмін-панель" : "Admin panel"} cards={cards}>
      <BusinessOperationsPanel lang={lang} />
    </DashboardFrame>
  );
}
