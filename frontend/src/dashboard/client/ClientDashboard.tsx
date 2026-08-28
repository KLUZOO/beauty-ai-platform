import React, { useMemo, useState } from "react";
import type { AuthRole, Lang, MockUser } from "../types";

const masterImages = [
  "https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
  "https://images.pexels.com/photos/3765114/pexels-photo-3765114.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
  "https://images.pexels.com/photos/1043471/pexels-photo-1043471.jpeg?auto=compress&cs=tinysrgb&w=500&h=500&fit=crop",
];

const likedImages = [
  "https://images.pexels.com/photos/3997379/pexels-photo-3997379.jpeg?auto=compress&cs=tinysrgb&w=900&h=650&fit=crop",
  "https://images.pexels.com/photos/3764014/pexels-photo-3764014.jpeg?auto=compress&cs=tinysrgb&w=900&h=650&fit=crop",
  "https://images.pexels.com/photos/705255/pexels-photo-705255.jpeg?auto=compress&cs=tinysrgb&w=900&h=650&fit=crop",
  "https://images.pexels.com/photos/3769021/pexels-photo-3769021.jpeg?auto=compress&cs=tinysrgb&w=900&h=650&fit=crop",
];

const bookingImage =
  "https://images.pexels.com/photos/705255/pexels-photo-705255.jpeg?auto=compress&cs=tinysrgb&w=1000&h=700&fit=crop";

type Review = {
  master: number;
  salon: number;
  comment: string;
  sent: boolean;
};

function Stars({ value, onChange, label }: { value: number; onChange: (value: number) => void; label: string }) {
  return (
    <div className="review-stars" role="radiogroup" aria-label={label}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className={star <= value ? "active" : ""}
          onClick={() => onChange(star)}
          aria-label={`${star} / 5`}
          aria-checked={star === value}
          role="radio"
        >
          ★
        </button>
      ))}
    </div>
  );
}

export default function ClientDashboard({
  user,
  lang,
  onHome,
  onRoleChange: _onRoleChange,
}: {
  user: MockUser;
  lang: Lang;
  onHome: () => void;
  onRoleChange: (role: AuthRole) => void;
}) {
  const ua = lang === "ua";
  const [tab, setTab] = useState<"home" | "profile">("home");
  const [openReview, setOpenReview] = useState<number | null>(null);
  const [ratings, setRatings] = useState<Record<number, Review>>({
    0: { master: 5, salon: 5, comment: ua ? "Дякую за ідеальний манікюр! 💜" : "Thank you for the perfect manicure! 💜", sent: true },
    1: { master: 0, salon: 0, comment: "", sent: false },
  });
  const [profileName, setProfileName] = useState(user.name);
  const [profilePhone, setProfilePhone] = useState("+380 67 123 45 67");
  const bonusBalance = 250;
  const [profileEmail, setProfileEmail] = useState(user.email);
  const [notifyEmail, setNotifyEmail] = useState(true);
  const [notifyPush, setNotifyPush] = useState(true);

  const firstName = useMemo(() => {
    const value = user.name?.trim().split(/\s+/)[0];
    return value || (ua ? "Наталя" : "Natalia");
  }, [user.name, ua]);

  const history = [
    {
      salon: "Beauty Room",
      master: ua ? "Ірина Бондар" : "Iryna Bondar",
      service: ua ? "Манікюр · гель-лак" : "Manicure · gel polish",
      date: ua ? "27 травня" : "May 27",
    },
    {
      salon: "Perfect Look",
      master: ua ? "Марія Левченко" : "Maria Levchenko",
      service: ua ? "Стрижка та укладка" : "Haircut & styling",
      date: ua ? "9 серпня" : "Aug 9",
    },
  ];

  const favoriteMasters = [
    { name: ua ? "Олена К." : "Olena K.", type: ua ? "Манікюр" : "Manicure", rating: 5.0, image: masterImages[0] },
    { name: ua ? "Марія П." : "Maria P.", type: ua ? "Брови" : "Brows", rating: 5.0, image: masterImages[1] },
    { name: ua ? "Дмитро С." : "Dmytro S.", type: ua ? "Чоловічі стрижки" : "Men's haircuts", rating: 4.9, image: masterImages[2] },
  ];

  const liked = [
    { name: "Velvet Nails & Spa", type: ua ? "Салон краси" : "Beauty salon", rating: 4.9, reviews: 131, distance: ua ? "0.9 км" : "0.9 km", district: ua ? "Печерський р-н" : "Pechersk", match: 96, image: likedImages[0] },
    { name: ua ? "Ірина Бондар" : "Iryna Bondar", type: ua ? "Брови" : "Brows", rating: 5.0, reviews: 107, distance: ua ? "1.1 км" : "1.1 km", district: ua ? "Брови" : "Brows", match: 90, image: likedImages[1] },
    { name: "Luna Beauty House", type: ua ? "Салон краси" : "Beauty salon", rating: 4.8, reviews: 124, distance: ua ? "0.6 км" : "0.6 km", district: ua ? "Печерський р-н" : "Pechersk", match: 90, image: likedImages[2] },
    { name: ua ? "Марина Кузьменко" : "Maryna Kuzmenko", type: ua ? "Візаж" : "Makeup", rating: 4.9, reviews: 112, distance: ua ? "1.3 км" : "1.3 km", district: ua ? "Візаж" : "Makeup", match: 88, image: likedImages[3] },
  ];

  const patchReview = (index: number, patch: Partial<Review>) =>
    setRatings((prev) => ({ ...prev, [index]: { ...prev[index], ...patch, sent: false } }));

  const renderReviewForm = (index: number) => {
    const visit = history[index];
    const review = ratings[index];

    return (
      <div className="client-review-form review-form-card">
        <div className="review-rating-grid">
          <div className="review-rating-block">
            <span>{ua ? "Майстер" : "Master"}</span>
            <strong>{visit.master}</strong>
            <Stars value={review.master} onChange={(value) => patchReview(index, { master: value })} label={ua ? "Рейтинг майстра" : "Master rating"} />
          </div>
          <div className="review-rating-block">
            <span>{ua ? "Салон" : "Salon"}</span>
            <strong>{visit.salon}</strong>
            <Stars value={review.salon} onChange={(value) => patchReview(index, { salon: value })} label={ua ? "Рейтинг салону" : "Salon rating"} />
          </div>
        </div>
        <label className="review-comment">
          <span>{ua ? "Коментар" : "Comment"}</span>
          <textarea value={review.comment} onChange={(event) => patchReview(index, { comment: event.target.value })} rows={3} />
        </label>
        <div className="review-submit-row">
          <span className={!review.master || !review.salon ? "review-hint" : "review-hint ready"}>
            {!review.master || !review.salon ? (ua ? "Поставте оцінку і майстру, і салону" : "Rate both the master and salon") : (ua ? "Все готово до відправлення" : "Ready to submit")}
          </span>
          <button type="button" className="review-submit-btn" disabled={!review.master || !review.salon} onClick={() => setRatings((prev) => ({ ...prev, [index]: { ...prev[index], sent: true } }))}>
            {review.sent ? (ua ? "Надіслано ✓" : "Sent ✓") : ua ? "Надіслати відгук" : "Submit review"}
          </button>
        </div>
      </div>
    );
  };

  return (
    <main className="client-dashboard-shell">
      <aside className="client-sidebar">
        <button className="client-brand" type="button" onClick={onHome} aria-label="Beauty AI">
          <span className="client-brand-mark"><i>✦</i><i>✦</i><i>✦</i></span>
          <span>Beauty <b>AI</b></span>
        </button>

        <nav className="client-sidebar-nav" aria-label={ua ? "Навігація кабінету" : "Account navigation"}>
          <button type="button" className={tab === "home" ? "active" : ""} onClick={() => setTab("home")}>
            <span className="client-nav-icon">⌂</span>{ua ? "Головна" : "Home"}
          </button>
          <button type="button" className={tab === "profile" ? "active" : ""} onClick={() => setTab("profile")}>
            <span className="client-nav-icon">♙</span>{ua ? "Профіль" : "Profile"}
          </button>
          <button type="button" className="client-sidebar-logout-top" onClick={onHome}>
            <span className="client-nav-icon">↪</span>{ua ? "Вийти" : "Log out"}
          </button>
        </nav>

        <div className="client-sidebar-bottom">
          <div className="client-loyalty-card">
            <div className="client-loyalty-copy">
              <b>{ua ? "Beauty бонуси" : "Beauty bonuses"}</b>
              <span>{ua ? "Накопичуй бонуси та отримуй знижки на улюблені послуги" : "Earn bonuses and get discounts on favourite services"}</span>
            </div>
            <div className="client-loyalty-sparkles" aria-hidden="true">✦ ✦ ✦</div>
            <div className="client-loyalty-diamond" aria-hidden="true">◆</div>
            <button type="button">{ua ? "Дізнатись більше" : "Learn more"}</button>
          </div>
          <div className="client-sidebar-footer">
            <p>© Beauty AI, 2024</p>
            <span>{ua ? "Усі права захищено" : "All rights reserved"}</span>
            <div className="client-socials" aria-label="Social links"><button type="button">◎</button><button type="button">f</button><button type="button">➤</button></div>
          </div>
        </div>
      </aside>

      <div className="client-dashboard-main">
        <header className="client-dashboard-header">
          <div className="client-welcome-copy">
            <h1>{ua ? `Вітаємо, ${firstName}! 👋` : `Welcome, ${firstName}! 👋`}</h1>
            <p>{ua ? "Знайдіть свого майстра краси" : "Find your beauty master"}</p>
          </div>
          <div className="client-header-actions">
            <div className="client-bonus-balance">
              <div><span>{ua ? "Твій бонусний баланс" : "Your bonus balance"}</span><strong>{bonusBalance} ₴</strong></div>
              <span className="client-bonus-diamond" aria-hidden="true">◆</span>
            </div>
            <button className="client-notification-btn" type="button" aria-label={ua ? "Сповіщення" : "Notifications"}>♧<span></span></button>
            <button className="client-profile-trigger" type="button" onClick={() => setTab("profile")}>
              <img src={user.avatar} alt={user.name} /><span>{firstName}</span><b>⌄</b>
            </button>
          </div>
        </header>

        {tab === "home" ? (
          <div className="client-dashboard-content">
            <section className="client-section client-upcoming-section client-surface-panel">
              <div className="client-section-head">
                <h2>{ua ? "Мої майбутні записи" : "My upcoming bookings"}</h2>
                <button type="button">{ua ? "Переглянути всі" : "View all"}</button>
              </div>
              <article className="client-booking-card">
                <div className="client-booking-photo-wrap">
                  <img className="client-booking-photo" src={bookingImage} alt="Beauty Room" />
                  <span className="client-booking-soon">{ua ? "Через 2 дні" : "In 2 days"}</span>
                </div>
                <div className="client-booking-info">
                  <h3>{ua ? "Манікюр + покриття гель-лаком" : "Manicure + gel polish"}</h3>
                  <p className="client-booking-salon">Beauty Room</p>
                  <p className="client-booking-master">{ua ? "Майстер: Ірина Бондар" : "Master: Iryna Bondar"}</p>
                  <div className="client-booking-meta"><span>▣ {ua ? "24 травня, пт" : "Fri, May 24"}</span><span>◯ 14:00</span><span>◷ {ua ? "1 год 30 хв" : "1 h 30 min"}</span></div>
                </div>
                <button className="client-details-btn" type="button">{ua ? "Деталі" : "Details"}</button>
              </article>
            </section>

            <div className="client-middle-grid">
              <section className="client-section client-reviews-section client-surface-panel">
                <div className="client-section-head"><h2>{ua ? "Останні відгуки" : "Latest reviews"}</h2><button type="button">{ua ? "Переглянути всі" : "View all"}</button></div>
                <div className="client-review-card">
                  <div className="client-review-mainline">
                    <div className="client-review-author"><img src={user.avatar} alt={user.name} /><div><b>{ua ? "Наталя С." : "Natalia S."}</b><span>{history[0].date}</span></div></div>
                    <div className="client-review-score"><span>★★★★★</span><strong>5.0</strong></div>
                  </div>
                  <p>{ratings[0].comment || (ua ? "Дякую за ідеальний манікюр! 💜" : "Thank you for the perfect manicure! 💜")}</p>
                  <div className="client-review-dots" aria-hidden="true"><i className="active"></i><i></i><i></i><i></i></div>
                  <button type="button" className="client-review-edit-hit" onClick={() => setOpenReview(openReview === 0 ? null : 0)} aria-label={ua ? "Редагувати відгук" : "Edit review"}></button>
                  {openReview === 0 && renderReviewForm(0)}
                </div>
              </section>

              <section className="client-section client-favorite-masters-section client-surface-panel">
                <div className="client-section-head"><h2>{ua ? "Улюблені майстри" : "Favourite masters"}</h2><button type="button">{ua ? "Переглянути всі" : "View all"}</button></div>
                <div className="client-favorite-masters-list">
                  {favoriteMasters.map((master) => (
                    <article className="client-master-row" key={master.name}>
                      <img src={master.image} alt={master.name} />
                      <div><b>{master.name}</b><span>{master.type} <i>•</i> {master.rating.toFixed(1)}</span></div>
                      <strong>♥</strong>
                    </article>
                  ))}
                </div>
              </section>
            </div>

            <section className="client-section client-liked-section client-surface-panel">
              <div className="client-section-head"><h2>{ua ? "Вам сподобалось" : "You liked"}</h2><button type="button">{ua ? "Переглянути всі" : "View all"}</button></div>
              <div className="client-liked-carousel">
                <div className="client-liked-grid">
                  {liked.map((item) => (
                    <article className="client-liked-card" key={item.name}>
                      <div className="client-liked-image-wrap">
                        <img src={item.image} alt={item.name} />
                        <span className="client-ai-match">AI MATCH {item.match}%</span>
                        <button className="client-heart-btn active" type="button" aria-label={ua ? "Прибрати з обраного" : "Remove from favourites"}>♡</button>
                      </div>
                      <div className="client-liked-body">
                        <div className="client-liked-title-row"><h3>{item.name}</h3><span className="client-liked-rating">★ {item.rating.toFixed(1)} <small>({item.reviews})</small></span></div>
                        <div className="client-liked-meta"><span>⌖ {item.distance}</span><i>•</i><span>{item.district}</span></div>
                      </div>
                    </article>
                  ))}
                </div>
                <button className="client-carousel-next" type="button" aria-label={ua ? "Наступні" : "Next"}>›</button>
              </div>
            </section>
          </div>
        ) : (
          <section className="client-profile-card client-surface-panel">
            <div className="client-section-head client-profile-head"><div><h2>{ua ? "Профіль" : "Profile"}</h2><p>{ua ? "Особисті дані та налаштування акаунта" : "Personal details and account settings"}</p></div></div>
            <div className="profile-photo-row"><div className="dashboard-avatar profile-avatar"><img src={user.avatar} alt={user.name} /></div><button type="button" className="booking-action-btn ghost">{ua ? "Змінити фото" : "Change photo"}</button></div>
            <div className="profile-fields-grid">
              <label><span>{ua ? "Ім'я" : "Name"}</span><input type="text" value={profileName} onChange={(event) => setProfileName(event.target.value)} /></label>
              <label><span>{ua ? "Телефон" : "Phone"}</span><input type="tel" value={profilePhone} onChange={(event) => setProfilePhone(event.target.value)} /></label>
              <label><span>Email</span><input type="email" value={profileEmail} onChange={(event) => setProfileEmail(event.target.value)} /></label>
            </div>
            <button type="button" className="cta-btn profile-save-btn">{ua ? "Зберегти зміни" : "Save changes"}</button>
            <div className="profile-subsection"><h3>{ua ? "Пароль" : "Password"}</h3><button type="button" className="booking-action-btn ghost">{ua ? "Змінити пароль" : "Change password"}</button></div>
            <div className="profile-subsection"><h3>{ua ? "Сповіщення" : "Notifications"}</h3><label className="profile-toggle-row"><span>{ua ? "Email-сповіщення" : "Email notifications"}</span><input type="checkbox" checked={notifyEmail} onChange={(event) => setNotifyEmail(event.target.checked)} /></label><label className="profile-toggle-row"><span>{ua ? "Push-сповіщення" : "Push notifications"}</span><input type="checkbox" checked={notifyPush} onChange={(event) => setNotifyPush(event.target.checked)} /></label></div>
            <div className="profile-subsection profile-danger-zone"><h3>{ua ? "Акаунт" : "Account"}</h3><button type="button" className="booking-action-btn ghost" onClick={onHome}>{ua ? "Вийти" : "Log out"}</button><button type="button" className="profile-delete-btn">{ua ? "Видалити акаунт" : "Delete account"}</button></div>
          </section>
        )}
      </div>
    </main>
  );
}
