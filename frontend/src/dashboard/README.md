# Dashboard architecture

- `DashboardShell.tsx` — role router only.
- `DashboardFrame.tsx` — shared dashboard topbar, hero and stat cards.
- `client/ClientDashboard.tsx` — client account and profile state/UI.
- `master/MasterDashboard.tsx` — master account UI.
- `admin/AdminDashboard.tsx` — admin account UI.
- `types.ts` — shared dashboard types.
- `styles/dashboard.css` — shared dashboard styles (visual refactor comes next).

The public landing page remains in `App.tsx`; dashboard role-specific markup is no longer stored there.
