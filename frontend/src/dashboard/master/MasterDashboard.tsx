import React, { useState } from "react";
import DashboardFrame, { type MasterSection } from "../DashboardFrame";
import type { AuthRole, Lang, MockUser } from "../types";

export default function MasterDashboard({ user, lang, onHome, onRoleChange }: { user: MockUser; lang: Lang; onHome: () => void; onRoleChange: (role: AuthRole) => void }) {
  const ua = lang === "ua";
  const [section, setSection] = useState<MasterSection>("home");

  const schedule = [
    { time: "10:00", client: "Олена К.", service: "Манікюр", price: "650 ₴", status: "done" },
    { time: "12:00", client: "Марія П.", service: "Брови + фарбування", price: "550 ₴", status: "done" },
    { time: "14:00", client: "Наталя С.", service: "Манікюр + покриття", price: "800 ₴", status: "now" },
    { time: "16:00", client: "Анна Д.", service: "Нарощування вій", price: "1 100 ₴", status: "next" },
    { time: "18:00", client: "Вікторія М.", service: "Манікюр", price: "700 ₴", status: "next" },
  ];

  const reviews = [
    { name: "Наталя С.", date: "22 травня", text: "Дякую за ідеальний манікюр! 💜", rating: "5.0" },
    { name: "Марія П.", date: "20 травня", text: "Брови просто супер! Дуже задоволена!", rating: "5.0" },
    { name: "Олена К.", date: "16 травня", text: "Все чудово, як завжди!", rating: "5.0" },
  ];

  const title = section === "home" ? (ua ? `Вітаємо, ${user.name}! 👋` : `Welcome, ${user.name}! 👋`) : section === "profile" ? (ua ? "Профіль майстра" : "Master profile") : (ua ? "Фінанси" : "Finance");

  return <DashboardFrame user={user} lang={lang} onHome={onHome} onRoleChange={onRoleChange} title={title} variant="master" activeSection={section} onSectionChange={setSection}>
    {section === "home" && <div className="master-home-v2">
      <div className="master-summary-v2">
        <article><span>Записи сьогодні</span><strong>6</strong><small>+2 до вчора</small><i>✂</i></article>
        <article><span>Клієнти за місяць</span><strong>18</strong><small>+12% за місяць</small><i>♙</i></article>
        <article><span>Заповненість</span><strong>98%</strong><small>Відмінний результат</small><i>◒</i></article>
        <article><span>Рейтинг</span><strong>4.9 <em>★</em></strong><small>124 відгуки</small><i>☆</i></article>
      </div>

      <div className="master-main-grid-v2">
        <section className="master-card-v2 master-schedule-v2">
          <div className="master-card-head-v2"><div><h2>Сьогодні, 27 травня</h2><p>Ваш розклад на сьогодні</p></div><button type="button">+ Додати вікно</button></div>
          <div className="master-schedule-list-v2">
            {schedule.map((slot) => <div className={`master-slot-v2 ${slot.status === "now" ? "current" : ""}`} key={slot.time}>
              <time>{slot.time}</time><div className="master-slot-copy-v2"><b>{slot.service}</b><span>{slot.client}</span></div><strong>{slot.price}</strong><span className={`master-slot-status-v2 ${slot.status}`}>{slot.status === "done" ? "Завершено" : slot.status === "now" ? "Зараз" : "Запис"}</span>
            </div>)}
          </div>
          <button className="master-all-schedule-v2" type="button">Переглянути весь розклад</button>
        </section>

        <div className="master-side-stack-v2">
          <section className="master-card-v2 master-month-v2">
            <div className="master-card-head-v2"><div><h2>Статистика за місяць</h2><p>Травень 2026</p></div><button className="link" type="button">Переглянути всі</button></div>
            <div className="master-month-grid-v2"><div><strong>24</strong><span>Записи</span></div><div><strong>18</strong><span>Клієнти</span></div><div><strong>98%</strong><span>Заповненість</span></div><div><strong>4.9 <em>★</em></strong><span>Рейтинг</span></div></div>
          </section>

          <section className="master-card-v2 master-reviews-v2">
            <div className="master-card-head-v2"><div><h2>Останні відгуки</h2></div><button className="link" type="button">Переглянути всі</button></div>
            {reviews.map((review, i) => <article key={review.name}><div className="master-review-avatar-v2">{review.name[0]}</div><div><b>{review.name}</b><span>{review.date}</span><p>{review.text}</p></div><strong>★★★★★ <span>{review.rating}</span></strong></article>)}
            <button className="master-add-work-v2" type="button">▧ &nbsp; Додати фото робіт</button>
          </section>
        </div>
      </div>
    </div>}

    {section === "profile" && <section className="master-card-v2 master-profile-v2">
      <div className="master-card-head-v2"><div><h2>Особиста інформація</h2><p>Так вас бачать клієнти Beauty AI</p></div></div>
      <div className="master-profile-top-v2"><img src={user.avatar} alt={user.name}/><div><b>{user.name}</b><span>Майстер • Beauty AI</span><button type="button">Змінити фото</button></div></div>
      <div className="master-form-grid-v2"><label>Ім'я<input defaultValue={user.name}/></label><label>Email<input defaultValue={user.email}/></label><label>Телефон<input defaultValue="+380 67 123 45 67"/></label><label>Місто<input defaultValue="Київ"/></label><label className="wide">Про себе<textarea defaultValue="Майстер манікюру та brow-artist. Люблю натуральні форми, акуратне покриття та красиві деталі."/></label></div>
      <button className="master-primary-v2" type="button">Зберегти зміни</button>
    </section>}

    {section === "finance" && <div className="master-finance-v2">
      <div className="master-summary-v2 finance"><article><span>Дохід за місяць</span><strong>28 450 ₴</strong><small>+18% до квітня</small></article><article><span>Доступно до виплати</span><strong>12 750 ₴</strong><small>Наступна виплата 1 червня</small></article><article><span>Beauty бонуси</span><strong>1 250</strong><small>Накопичено</small></article></div>
      <section className="master-card-v2"><div className="master-card-head-v2"><div><h2>Останні операції</h2><p>Травень 2026</p></div><button type="button">Вивантажити звіт</button></div><div className="master-transactions-v2">{[["27 травня","Манікюр + покриття","Наталя С.","+800 ₴"],["27 травня","Брови + фарбування","Марія П.","+550 ₴"],["26 травня","Манікюр","Олена К.","+650 ₴"],["25 травня","Виплата на картку","•• 4821","−8 000 ₴"]].map(x=><div key={x.join("")}><span>{x[0]}</span><b>{x[1]}<small>{x[2]}</small></b><strong>{x[3]}</strong></div>)}</div></section>
    </div>}
  </DashboardFrame>;
}
