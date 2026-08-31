import React, { useEffect, useState } from "react";
import {
  createPayment,
  createPromotion,
  createReferralEvent,
  deletePayment,
  deletePromotion,
  deleteReferralEvent,
  getPayment,
  getPromotion,
  getReferralEvent,
  listPayments,
  listPromotions,
  listReferralEvents,
  patchPayment,
  patchPromotion,
  patchReferralEvent,
  updatePayment,
  updatePromotion,
  updateReferralEvent,
  type ApiPayment,
  type ApiPromotion,
  type ApiReferralEvent,
  type PaymentMethod,
  type PaymentStatus,
} from "../../api";

type Module = "payments" | "promotions" | "referrals";

type PaymentForm = {
  appointment: string;
  amount: string;
  currency: string;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
};

type PromotionForm = {
  name: string;
  description: string;
  discount_percent: string;
  start_date: string;
  end_date: string;
  salon: string;
};

type ReferralForm = {
  session_id: string;
  salon: string;
  service: string;
  source: string;
  destination_url: string;
  event_type: string;
};

const paymentMethods: PaymentMethod[] = ["cash", "card", "apple_pay", "google_pay"];
const paymentStatuses: PaymentStatus[] = ["pending", "completed", "failed", "cancelled", "refunded"];

function localDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.slice(0, 16);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

function isoDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new Error("Вкажіть коректну дату й час");
  return date.toISOString();
}

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

function numberValue(value: string, label: string) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new Error(`Вкажіть коректне поле «${label}»`);
  return number;
}

function paymentToForm(payment: ApiPayment): PaymentForm {
  return {
    appointment: String(payment.appointment),
    amount: String(payment.amount),
    currency: payment.currency || "UAH",
    payment_method: payment.payment_method,
    payment_status: payment.payment_status || "pending",
  };
}

function promotionToForm(promotion: ApiPromotion): PromotionForm {
  return {
    name: promotion.name,
    description: promotion.description || "",
    discount_percent: String(promotion.discount_percent),
    start_date: localDateTime(promotion.start_date),
    end_date: localDateTime(promotion.end_date),
    salon: String(promotion.salon),
  };
}

function referralToForm(event: ApiReferralEvent): ReferralForm {
  return {
    session_id: event.session_id,
    salon: String(event.salon),
    service: event.service == null ? "" : String(event.service),
    source: event.source,
    destination_url: event.destination_url,
    event_type: event.event_type,
  };
}

export default function BusinessOperationsPanel({ lang }: { lang: "ua" | "en" }) {
  const ua = lang === "ua";
  const [activeModule, setActiveModule] = useState<Module>("payments");
  const [payments, setPayments] = useState<ApiPayment[]>([]);
  const [promotions, setPromotions] = useState<ApiPromotion[]>([]);
  const [referrals, setReferrals] = useState<ApiReferralEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [paymentForm, setPaymentForm] = useState<PaymentForm>({
    appointment: "",
    amount: "",
    currency: "UAH",
    payment_method: "card",
    payment_status: "pending",
  });
  const [editingPayment, setEditingPayment] = useState<(PaymentForm & { id: number }) | null>(null);

  const [promotionFilters, setPromotionFilters] = useState({
    active: "all",
    discount_percent: "",
    salon_id: "",
  });
  const [promotionForm, setPromotionForm] = useState<PromotionForm>({
    name: "",
    description: "",
    discount_percent: "",
    start_date: "",
    end_date: "",
    salon: "",
  });
  const [editingPromotion, setEditingPromotion] = useState<(PromotionForm & { id: number }) | null>(null);

  const [referralForm, setReferralForm] = useState<ReferralForm>({
    session_id: "",
    salon: "",
    service: "",
    source: "",
    destination_url: "",
    event_type: "click",
  });
  const [editingReferral, setEditingReferral] = useState<(ReferralForm & { id: number }) | null>(null);

  const loadActiveModule = async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeModule === "payments") {
        setPayments(await listPayments());
      } else if (activeModule === "promotions") {
        setPromotions(
          await listPromotions({
            active: promotionFilters.active === "all" ? undefined : promotionFilters.active === "true",
            discount_percent: promotionFilters.discount_percent
              ? numberValue(promotionFilters.discount_percent, ua ? "знижка" : "discount")
              : undefined,
            salon_id: promotionFilters.salon_id
              ? numberValue(promotionFilters.salon_id, ua ? "ID салону" : "salon ID")
              : undefined,
          }),
        );
      } else {
        setReferrals(await listReferralEvents());
      }
    } catch (loadError) {
      setError(errorMessage(loadError, ua ? "Не вдалося завантажити дані" : "Could not load data"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadActiveModule();
  }, [activeModule]);

  const runMutation = async (operation: () => Promise<unknown>, successMessage: string) => {
    setError(null);
    setNotice(null);
    try {
      await operation();
      setNotice(successMessage);
      await loadActiveModule();
    } catch (mutationError) {
      setError(errorMessage(mutationError, ua ? "Операція не виконана" : "Operation failed"));
    }
  };

  const submitPayment = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const payload = {
        appointment: numberValue(paymentForm.appointment, ua ? "ID запису" : "appointment ID"),
        amount: paymentForm.amount,
        currency: paymentForm.currency.toUpperCase(),
        payment_method: paymentForm.payment_method,
        payment_status: paymentForm.payment_status,
      };
      await runMutation(
        () => createPayment(payload),
        ua ? "Платіж створено" : "Payment created",
      );
      setPaymentForm({ appointment: "", amount: "", currency: "UAH", payment_method: "card", payment_status: "pending" });
    } catch (formError) {
      setError(errorMessage(formError, ua ? "Перевірте дані платежу" : "Check payment details"));
    }
  };

  const startPaymentEdit = async (id: number) => {
    try {
      setError(null);
      const payment = await getPayment(id);
      setEditingPayment({ ...paymentToForm(payment), id });
    } catch (detailError) {
      setError(errorMessage(detailError, ua ? "Не вдалося завантажити платіж" : "Could not load payment"));
    }
  };

  const savePayment = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingPayment) return;
    try {
      const payload = {
        appointment: numberValue(editingPayment.appointment, ua ? "ID запису" : "appointment ID"),
        amount: editingPayment.amount,
        currency: editingPayment.currency.toUpperCase(),
        payment_method: editingPayment.payment_method,
        payment_status: editingPayment.payment_status,
      };
      await runMutation(() => updatePayment(editingPayment.id, payload), ua ? "Платіж оновлено через PUT" : "Payment updated with PUT");
      setEditingPayment(null);
    } catch (formError) {
      setError(errorMessage(formError, ua ? "Перевірте дані платежу" : "Check payment details"));
    }
  };

  const patchPaymentStatus = async () => {
    if (!editingPayment) return;
    await runMutation(
      () => patchPayment(editingPayment.id, { payment_status: editingPayment.payment_status }),
      ua ? "Статус платежу оновлено через PATCH" : "Payment status updated with PATCH",
    );
    setEditingPayment(null);
  };

  const submitPromotion = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const payload = {
        name: promotionForm.name.trim(),
        description: promotionForm.description.trim(),
        discount_percent: numberValue(promotionForm.discount_percent, ua ? "відсоток знижки" : "discount"),
        start_date: isoDateTime(promotionForm.start_date),
        end_date: isoDateTime(promotionForm.end_date),
        salon: numberValue(promotionForm.salon, ua ? "ID салону" : "salon ID"),
      };
      if (payload.discount_percent < 0 || payload.discount_percent > 100) {
        throw new Error(ua ? "Знижка має бути від 0 до 100%" : "Discount must be between 0 and 100%");
      }
      await runMutation(() => createPromotion(payload), ua ? "Акцію створено" : "Promotion created");
      setPromotionForm({ name: "", description: "", discount_percent: "", start_date: "", end_date: "", salon: "" });
    } catch (formError) {
      setError(errorMessage(formError, ua ? "Перевірте дані акції" : "Check promotion details"));
    }
  };

  const startPromotionEdit = async (id: number) => {
    try {
      setError(null);
      const promotion = await getPromotion(id);
      setEditingPromotion({ ...promotionToForm(promotion), id });
    } catch (detailError) {
      setError(errorMessage(detailError, ua ? "Не вдалося завантажити акцію" : "Could not load promotion"));
    }
  };

  const savePromotion = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingPromotion) return;
    try {
      const payload = {
        name: editingPromotion.name.trim(),
        description: editingPromotion.description.trim(),
        discount_percent: numberValue(editingPromotion.discount_percent, ua ? "відсоток знижки" : "discount"),
        start_date: isoDateTime(editingPromotion.start_date),
        end_date: isoDateTime(editingPromotion.end_date),
        salon: numberValue(editingPromotion.salon, ua ? "ID салону" : "salon ID"),
      };
      await runMutation(() => updatePromotion(editingPromotion.id, payload), ua ? "Акцію оновлено через PUT" : "Promotion updated with PUT");
      setEditingPromotion(null);
    } catch (formError) {
      setError(errorMessage(formError, ua ? "Перевірте дані акції" : "Check promotion details"));
    }
  };

  const patchPromotionDiscount = async () => {
    if (!editingPromotion) return;
    try {
      const discount = numberValue(editingPromotion.discount_percent, ua ? "відсоток знижки" : "discount");
      if (discount < 0 || discount > 100) throw new Error(ua ? "Знижка має бути від 0 до 100%" : "Discount must be between 0 and 100%");
      await runMutation(
        () => patchPromotion(editingPromotion.id, { discount_percent: discount }),
        ua ? "Знижку оновлено через PATCH" : "Discount updated with PATCH",
      );
      setEditingPromotion(null);
    } catch (patchError) {
      setError(errorMessage(patchError, ua ? "Не вдалося оновити знижку" : "Could not update discount"));
    }
  };

  const submitReferral = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const payload = {
        session_id: referralForm.session_id.trim(),
        salon: numberValue(referralForm.salon, ua ? "ID салону" : "salon ID"),
        service: referralForm.service ? numberValue(referralForm.service, ua ? "ID послуги" : "service ID") : null,
        source: referralForm.source.trim(),
        destination_url: referralForm.destination_url.trim(),
        event_type: referralForm.event_type.trim(),
      };
      await runMutation(() => createReferralEvent(payload), ua ? "Реферальну подію створено" : "Referral event created");
      setReferralForm({ session_id: "", salon: "", service: "", source: "", destination_url: "", event_type: "click" });
    } catch (formError) {
      setError(errorMessage(formError, ua ? "Перевірте дані події" : "Check referral event details"));
    }
  };

  const startReferralEdit = async (id: number) => {
    try {
      setError(null);
      const referral = await getReferralEvent(id);
      setEditingReferral({ ...referralToForm(referral), id });
    } catch (detailError) {
      setError(errorMessage(detailError, ua ? "Не вдалося завантажити подію" : "Could not load referral event"));
    }
  };

  const saveReferral = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingReferral) return;
    try {
      const payload = {
        session_id: editingReferral.session_id.trim(),
        salon: numberValue(editingReferral.salon, ua ? "ID салону" : "salon ID"),
        service: editingReferral.service ? numberValue(editingReferral.service, ua ? "ID послуги" : "service ID") : null,
        source: editingReferral.source.trim(),
        destination_url: editingReferral.destination_url.trim(),
        event_type: editingReferral.event_type.trim(),
      };
      await runMutation(() => updateReferralEvent(editingReferral.id, payload), ua ? "Подію оновлено через PUT" : "Referral event updated with PUT");
      setEditingReferral(null);
    } catch (formError) {
      setError(errorMessage(formError, ua ? "Перевірте дані події" : "Check referral event details"));
    }
  };

  const patchReferralType = async () => {
    if (!editingReferral) return;
    await runMutation(
      () => patchReferralEvent(editingReferral.id, { event_type: editingReferral.event_type.trim() }),
      ua ? "Тип події оновлено через PATCH" : "Event type updated with PATCH",
    );
    setEditingReferral(null);
  };

  const deleteResource = async (resource: Module, id: number) => {
    const label = resource === "payments" ? (ua ? "платіж" : "payment") : resource === "promotions" ? (ua ? "акцію" : "promotion") : (ua ? "реферальну подію" : "referral event");
    if (!window.confirm(ua ? `Видалити ${label}?` : `Delete this ${label}?`)) return;
    await runMutation(
      resource === "payments"
        ? () => deletePayment(id)
        : resource === "promotions"
          ? () => deletePromotion(id)
          : () => deleteReferralEvent(id),
      ua ? `${label[0].toUpperCase()}${label.slice(1)} видалено` : `${label[0].toUpperCase()}${label.slice(1)} deleted`,
    );
  };

  const renderPaymentForm = (editing = false) => {
    const form = editing && editingPayment ? editingPayment : paymentForm;
    const setForm = editing
      ? (patch: Partial<PaymentForm>) => setEditingPayment((current) => current ? { ...current, ...patch } : current)
      : (patch: Partial<PaymentForm>) => setPaymentForm((current) => ({ ...current, ...patch }));
    return (
      <form className="ops-form" onSubmit={editing ? savePayment : submitPayment}>
        <div className="ops-form-grid">
          <label><span>{ua ? "ID запису" : "Appointment ID"}</span><input required type="number" min="1" value={form.appointment} onChange={(event) => setForm({ appointment: event.target.value })} /></label>
          <label><span>{ua ? "Сума" : "Amount"}</span><input required type="number" min="0" step="0.01" value={form.amount} onChange={(event) => setForm({ amount: event.target.value })} /></label>
          <label><span>{ua ? "Валюта" : "Currency"}</span><input required maxLength={3} value={form.currency} onChange={(event) => setForm({ currency: event.target.value })} /></label>
          <label><span>{ua ? "Метод" : "Method"}</span><select value={form.payment_method} onChange={(event) => setForm({ payment_method: event.target.value as PaymentMethod })}>{paymentMethods.map((method) => <option key={method} value={method}>{method}</option>)}</select></label>
          <label><span>{ua ? "Статус" : "Status"}</span><select value={form.payment_status} onChange={(event) => setForm({ payment_status: event.target.value as PaymentStatus })}>{paymentStatuses.map((status) => <option key={status} value={status}>{status}</option>)}</select></label>
        </div>
        <div className="ops-form-actions">
          <button className="ops-primary" type="submit">{editing ? (ua ? "Зберегти все (PUT)" : "Save all (PUT)") : (ua ? "Створити платіж" : "Create payment")}</button>
          {editing && <><button className="ops-secondary" type="button" onClick={() => void patchPaymentStatus()}>{ua ? "Зберегти статус (PATCH)" : "Save status (PATCH)"}</button><button className="ops-link-button" type="button" onClick={() => setEditingPayment(null)}>{ua ? "Скасувати" : "Cancel"}</button></>}
        </div>
      </form>
    );
  };

  const renderPromotionForm = (editing = false) => {
    const form = editing && editingPromotion ? editingPromotion : promotionForm;
    const setForm = editing
      ? (patch: Partial<PromotionForm>) => setEditingPromotion((current) => current ? { ...current, ...patch } : current)
      : (patch: Partial<PromotionForm>) => setPromotionForm((current) => ({ ...current, ...patch }));
    return (
      <form className="ops-form" onSubmit={editing ? savePromotion : submitPromotion}>
        <div className="ops-form-grid">
          <label><span>{ua ? "Назва" : "Name"}</span><input required maxLength={100} value={form.name} onChange={(event) => setForm({ name: event.target.value })} /></label>
          <label><span>{ua ? "Знижка, %" : "Discount, %"}</span><input required type="number" min="0" max="100" value={form.discount_percent} onChange={(event) => setForm({ discount_percent: event.target.value })} /></label>
          <label><span>{ua ? "ID салону" : "Salon ID"}</span><input required type="number" min="1" value={form.salon} onChange={(event) => setForm({ salon: event.target.value })} /></label>
          <label><span>{ua ? "Початок" : "Starts"}</span><input required type="datetime-local" value={form.start_date} onChange={(event) => setForm({ start_date: event.target.value })} /></label>
          <label><span>{ua ? "Завершення" : "Ends"}</span><input required type="datetime-local" value={form.end_date} onChange={(event) => setForm({ end_date: event.target.value })} /></label>
          <label className="ops-field-wide"><span>{ua ? "Опис" : "Description"}</span><textarea rows={3} value={form.description} onChange={(event) => setForm({ description: event.target.value })} /></label>
        </div>
        <div className="ops-form-actions">
          <button className="ops-primary" type="submit">{editing ? (ua ? "Зберегти все (PUT)" : "Save all (PUT)") : (ua ? "Створити акцію" : "Create promotion")}</button>
          {editing && <><button className="ops-secondary" type="button" onClick={() => void patchPromotionDiscount()}>{ua ? "Зберегти знижку (PATCH)" : "Save discount (PATCH)"}</button><button className="ops-link-button" type="button" onClick={() => setEditingPromotion(null)}>{ua ? "Скасувати" : "Cancel"}</button></>}
        </div>
      </form>
    );
  };

  const renderReferralForm = (editing = false) => {
    const form = editing && editingReferral ? editingReferral : referralForm;
    const setForm = editing
      ? (patch: Partial<ReferralForm>) => setEditingReferral((current) => current ? { ...current, ...patch } : current)
      : (patch: Partial<ReferralForm>) => setReferralForm((current) => ({ ...current, ...patch }));
    return (
      <form className="ops-form" onSubmit={editing ? saveReferral : submitReferral}>
        <div className="ops-form-grid">
          <label><span>{ua ? "ID сесії" : "Session ID"}</span><input required maxLength={64} value={form.session_id} onChange={(event) => setForm({ session_id: event.target.value })} /></label>
          <label><span>{ua ? "ID салону" : "Salon ID"}</span><input required type="number" min="1" value={form.salon} onChange={(event) => setForm({ salon: event.target.value })} /></label>
          <label><span>{ua ? "ID послуги (необов'язково)" : "Service ID (optional)"}</span><input type="number" min="1" value={form.service} onChange={(event) => setForm({ service: event.target.value })} /></label>
          <label><span>{ua ? "Джерело" : "Source"}</span><input required maxLength={120} placeholder="instagram" value={form.source} onChange={(event) => setForm({ source: event.target.value })} /></label>
          <label><span>{ua ? "Тип події" : "Event type"}</span><input required maxLength={20} placeholder="click" value={form.event_type} onChange={(event) => setForm({ event_type: event.target.value })} /></label>
          <label className="ops-field-wide"><span>{ua ? "URL призначення" : "Destination URL"}</span><input required type="url" maxLength={200} placeholder="https://..." value={form.destination_url} onChange={(event) => setForm({ destination_url: event.target.value })} /></label>
        </div>
        <div className="ops-form-actions">
          <button className="ops-primary" type="submit">{editing ? (ua ? "Зберегти все (PUT)" : "Save all (PUT)") : (ua ? "Створити подію" : "Create event")}</button>
          {editing && <><button className="ops-secondary" type="button" onClick={() => void patchReferralType()}>{ua ? "Зберегти тип (PATCH)" : "Save type (PATCH)"}</button><button className="ops-link-button" type="button" onClick={() => setEditingReferral(null)}>{ua ? "Скасувати" : "Cancel"}</button></>}
        </div>
      </form>
    );
  };

  return (
    <section className="dashboard-panel ops-panel">
      <div className="dashboard-panel-head">
        <div>
          <h2>{ua ? "Операційні дані API" : "API operations"}</h2>
          <p>{ua ? "Повне керування оплатами, акціями та реферальними подіями" : "Full payments, promotions and referral events management"}</p>
        </div>
        <button className="ops-refresh" type="button" onClick={() => void loadActiveModule()}>{ua ? "Оновити" : "Refresh"}</button>
      </div>

      <div className="ops-tabs" role="tablist" aria-label={ua ? "Ресурси API" : "API resources"}>
        {([
          ["payments", ua ? "Оплати" : "Payments"],
          ["promotions", ua ? "Акції" : "Promotions"],
          ["referrals", ua ? "Реферальні події" : "Referral events"],
        ] as [Module, string][]).map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={activeModule === id} className={activeModule === id ? "active" : ""} onClick={() => { setActiveModule(id); setNotice(null); setError(null); }}>
            {label}
          </button>
        ))}
      </div>

      {error && <p className="ops-message error" role="alert">{error}</p>}
      {notice && <p className="ops-message success" role="status">{notice}</p>}
      {loading && <p className="ops-loading">{ua ? "Завантаження…" : "Loading…"}</p>}

      {activeModule === "payments" && (
        <div className="ops-resource">
          <div className="ops-resource-header"><div><h3>{ua ? "Платежі" : "Payments"}</h3><p>{ua ? "GET список, POST створення і CRUD для конкретного платежу" : "GET list, POST create and CRUD for one payment"}</p></div><span className="ops-count">{payments.length}</span></div>
          {!editingPayment && renderPaymentForm()}
          {editingPayment && <div className="ops-edit-box"><h4>{ua ? `Редагування платежу #${editingPayment.id}` : `Edit payment #${editingPayment.id}`}</h4>{renderPaymentForm(true)}</div>}
          <div className="ops-list">
            {payments.length === 0 && !loading && <p className="ops-empty">{ua ? "Платежів не знайдено." : "No payments found."}</p>}
            {payments.map((payment) => (
              <article className="ops-row" key={payment.id}>
                <div><b>#{payment.id} · {payment.amount} {payment.currency || ""}</b><span>{ua ? "Запис" : "Appointment"} #{payment.appointment} · {payment.payment_method_display || payment.payment_method}</span></div>
                <span className="ops-status">{payment.payment_status_display || payment.payment_status || "—"}</span>
                <div className="ops-row-actions"><button type="button" onClick={() => void startPaymentEdit(payment.id)}>{ua ? "Деталі / Edit" : "Details / Edit"}</button><button className="danger" type="button" onClick={() => void deleteResource("payments", payment.id)}>{ua ? "Видалити" : "Delete"}</button></div>
              </article>
            ))}
          </div>
        </div>
      )}

      {activeModule === "promotions" && (
        <div className="ops-resource">
          <div className="ops-resource-header"><div><h3>{ua ? "Акції" : "Promotions"}</h3><p>{ua ? "Фільтри списку та повний CRUD акцій" : "List filters and full promotion CRUD"}</p></div><span className="ops-count">{promotions.length}</span></div>
          <div className="ops-filters">
            <label><span>{ua ? "Статус" : "Status"}</span><select value={promotionFilters.active} onChange={(event) => setPromotionFilters((current) => ({ ...current, active: event.target.value }))}><option value="all">{ua ? "Усі" : "All"}</option><option value="true">{ua ? "Активні" : "Active"}</option><option value="false">{ua ? "Неактивні" : "Inactive"}</option></select></label>
            <label><span>{ua ? "Знижка, %" : "Discount, %"}</span><input type="number" min="0" max="100" value={promotionFilters.discount_percent} onChange={(event) => setPromotionFilters((current) => ({ ...current, discount_percent: event.target.value }))} /></label>
            <label><span>{ua ? "ID салону" : "Salon ID"}</span><input type="number" min="1" value={promotionFilters.salon_id} onChange={(event) => setPromotionFilters((current) => ({ ...current, salon_id: event.target.value }))} /></label>
            <button className="ops-secondary" type="button" onClick={() => void loadActiveModule()}>{ua ? "Застосувати" : "Apply"}</button>
          </div>
          {!editingPromotion && renderPromotionForm()}
          {editingPromotion && <div className="ops-edit-box"><h4>{ua ? `Редагування акції #${editingPromotion.id}` : `Edit promotion #${editingPromotion.id}`}</h4>{renderPromotionForm(true)}</div>}
          <div className="ops-list">
            {promotions.length === 0 && !loading && <p className="ops-empty">{ua ? "Акцій не знайдено." : "No promotions found."}</p>}
            {promotions.map((promotion) => (
              <article className="ops-row" key={promotion.id}>
                <div><b>#{promotion.id} · {promotion.name}</b><span>{ua ? `Салон #${promotion.salon} · ${promotion.discount_percent}%` : `Salon #${promotion.salon} · ${promotion.discount_percent}%`} · {localDateTime(promotion.end_date).replace("T", " ")}</span></div>
                <span className="ops-status">{new Date(promotion.end_date).getTime() >= Date.now() ? (ua ? "Активна" : "Active") : (ua ? "Завершена" : "Expired")}</span>
                <div className="ops-row-actions"><button type="button" onClick={() => void startPromotionEdit(promotion.id)}>{ua ? "Деталі / Edit" : "Details / Edit"}</button><button className="danger" type="button" onClick={() => void deleteResource("promotions", promotion.id)}>{ua ? "Видалити" : "Delete"}</button></div>
              </article>
            ))}
          </div>
        </div>
      )}

      {activeModule === "referrals" && (
        <div className="ops-resource">
          <div className="ops-resource-header"><div><h3>{ua ? "Реферальні події" : "Referral events"}</h3><p>{ua ? "Tracking переходів із джерела на сторінку салону або послуги" : "Track visits from a source to a salon or service destination"}</p></div><span className="ops-count">{referrals.length}</span></div>
          {!editingReferral && renderReferralForm()}
          {editingReferral && <div className="ops-edit-box"><h4>{ua ? `Редагування події #${editingReferral.id}` : `Edit referral event #${editingReferral.id}`}</h4>{renderReferralForm(true)}</div>}
          <div className="ops-list">
            {referrals.length === 0 && !loading && <p className="ops-empty">{ua ? "Реферальних подій не знайдено." : "No referral events found."}</p>}
            {referrals.map((referral) => (
              <article className="ops-row" key={referral.id}>
                <div><b>#{referral.id} · {referral.event_type}</b><span>{referral.source} → {referral.destination_url} · {ua ? "Салон" : "Salon"} #{referral.salon}</span></div>
                <span className="ops-status">{referral.created_at ? new Date(referral.created_at).toLocaleString(ua ? "uk-UA" : "en-US") : "—"}</span>
                <div className="ops-row-actions"><button type="button" onClick={() => void startReferralEdit(referral.id)}>{ua ? "Деталі / Edit" : "Details / Edit"}</button><button className="danger" type="button" onClick={() => void deleteResource("referrals", referral.id)}>{ua ? "Видалити" : "Delete"}</button></div>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}