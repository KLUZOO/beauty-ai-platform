import React from "react";
import "./styles/dashboard.css";
import "./styles/operations.css";
import type { AuthRole, Lang, MockUser } from "./types";
import ClientDashboard from "./client/ClientDashboard";
import MasterDashboard from "./master/MasterDashboard";
import AdminDashboard from "./admin/AdminDashboard";

export type { AuthRole, Lang, MockUser } from "./types";

export default function DashboardShell({ user, lang, onHome, onRoleChange }: {
  user: MockUser;
  lang: Lang;
  onHome: () => void;
  onRoleChange: (role: AuthRole) => void;
}) {
  if (user.role === "master") return <MasterDashboard user={user} lang={lang} onHome={onHome} onRoleChange={onRoleChange} />;
  if (user.role === "admin") return <AdminDashboard user={user} lang={lang} onHome={onHome} onRoleChange={onRoleChange} />;
  return <ClientDashboard user={user} lang={lang} onHome={onHome} onRoleChange={onRoleChange} />;
}
