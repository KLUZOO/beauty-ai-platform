import { useEffect, useState } from 'react';
import './HomePage.scss';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const MapRecenter = ({ center }: { center: [number, number] }) => {
  const map = useMap();

  useEffect(() => {
    map.setView(center);
  }, [center, map]);

  return null;
};

const categories = [
  { title: 'Манікюр', meta: 'від 500 грн' },
  { title: 'Перукар', meta: 'від 600 грн' },
  { title: 'Брови', meta: 'від 300 грн' },
  { title: 'Косметологія', meta: 'від 900 грн' },
  { title: 'Масаж', meta: 'від 700 грн' },
];

const result = [
  {
    title: 'Luna Beauty House',
    category: 'Салон краси',
    rating: '4.7',
    reviews: 83,
    distance: '3.0 км від вас',
    price: 'від 850 грн',
    services: [
      'Косметологія від 850 грн',
      'Масаж від 700 грн',
      'Пілінг від 500 грн',
    ],
    available: 'Завтра з 10:00',
    badge: 'Топовий',
    image: './photo/luna.jpg',
    // real coordinates (latitude, longitude)
    lat: 50.4471,
    lng: 30.5202,
  },
  {
    title: 'Perfect Nails',
    category: 'Манікюрний центр',
    rating: '4.9',
    reviews: 156,
    distance: '0.8 км від вас',
    price: 'від 550 грн',
    services: [
      'Манікюр від 550 грн',
      'Педикюр від 600 грн',
      'Дизайн від 150 грн',
    ],
    available: 'Доступний сьогодні',
    badge: 'Популярний',
    image: './photo/perfect_nails.png',
    lat: 50.4523,
    lng: 30.5247,
  },
  {
    title: 'Перукарня "Стиль"',
    category: 'Перукарня',
    rating: '4.6',
    reviews: 92,
    distance: '1.5 км від вас',
    price: 'від 650 грн',
    services: [
      'Стрижка від 650 грн',
      'Фарбування від 900 грн',
      'Укладання від 400 грн',
    ],
    available: 'Вільні місця',
    badge: 'Рекомендовано',
    image: './photo/style.jpg',
    lat: 50.455,
    lng: 30.5189,
  },
  {
    title: 'Beauty Studio',
    category: 'Салон краси',
    rating: '4.9',
    reviews: 128,
    distance: '1.2 км від вас',
    price: 'від 700 грн',
    services: [
      'Манікюр від 700 грн',
      'Стрижка від 600 грн',
      'Мейкап від 900 грн',
    ],
    available: 'Доступний сьогодні',
    badge: 'AI Рекомендація',
    image: './photo/beauty.jpg',
    lat: 50.4488,
    lng: 30.5301,
  },
  {
    title: 'Анна Коваль',
    category: 'Майстер манікюру',
    rating: '5.0',
    reviews: 96,
    distance: '0.6 км від вас',
    price: 'від 600 грн',
    services: [
      'Манікюр від 600 грн',
      'Покриття від 500 грн',
      'Дизайн від 100 грн',
    ],
    available: 'Доступний сьогодні о 18:00',
    badge: 'AI Рекомендація',
    image: './photo/anna.png',
    lat: 50.4496,
    lng: 30.5225,
  },
  {
    title: 'Chop-Chop Barbershop',
    category: 'Барбершоп',
    rating: '4.8',
    reviews: 74,
    distance: '2.1 км від вас',
    price: 'від 500 грн',
    services: [
      'Стрижка від 500 грн',
      'Борода від 300 грн',
      'Комплекс від 700 грн',
    ],
    available: 'Доступний сьогодні',
    badge: 'AI Рекомендація',
    image: './photo/chop.png',
    lat: 50.4542,
    lng: 30.5353,
  },
];

export const HomePage = () => {
  const [price, setPrice] = useState(1200);
  const [query, setQuery] = useState('');
  const [filteredResults, setFilteredResults] = useState(result);
  const [selectedCategory, setSelectedCategory] = useState('Всі категорії');
  const [selectedRating, setSelectedRating] = useState('Будь-який');
  const [selectedDistance, setSelectedDistance] = useState('Будь-яка');
  const [availableToday, setAvailableToday] = useState(false);
  const [selectedDate, setSelectedDate] = useState('');
  const [userLocation, setUserLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);

  const [, setLocationError] = useState('');

  const getPriceNumber = (price: string) => Number(price.replace(/[^\d]/g, ''));

  const getDistanceNumber = (distance: string) =>
    Number(distance.replace(',', '.').match(/\d+(\.\d+)?/)?.[0] || 0);

  // returns distance in kilometers between two coords
  const getDistanceKm = (
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number,
  ) => {
    const toRad = (v: number) => (v * Math.PI) / 180;
    const R = 6371; // Earth radius km
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(toRad(lat1)) *
        Math.cos(toRad(lat2)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  const [favorites, setFavorites] = useState<string[]>([]);

  const toggleFavorite = (id: string) => {
    setFavorites(prev =>
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id],
    );
  };

  const handleSearch = () => {
    const search = query.toLowerCase().trim();

    const filtered = result.filter(item => {
      const itemPrice = getPriceNumber(item.price);
      const itemDistance = getDistanceNumber(item.distance);
      const itemRating = Number(item.rating);

      const matchesSearch =
        !search ||
        item.title.toLowerCase().includes(search) ||
        item.category.toLowerCase().includes(search) ||
        item.services.some(service => service.toLowerCase().includes(search));

      const matchesCategory =
        selectedCategory === 'Всі категорії' ||
        item.category.toLowerCase().includes(selectedCategory.toLowerCase()) ||
        item.services.some(service =>
          service.toLowerCase().includes(selectedCategory.toLowerCase()),
        );

      const matchesPrice = itemPrice <= price;

      const matchesRating =
        selectedRating === 'Будь-який' ||
        itemRating >= Number(selectedRating.replace('+', ''));

      const matchesDistance =
        selectedDistance === 'Будь-яка' ||
        itemDistance <= Number(selectedDistance.replace(/[^\d]/g, ''));

      const matchesAvailability =
        !availableToday || item.available.toLowerCase().includes('сьогодні');

      return (
        matchesSearch &&
        matchesCategory &&
        matchesPrice &&
        matchesRating &&
        matchesDistance &&
        matchesAvailability
      );
    });

    setFilteredResults(filtered);
  };

  useEffect(() => {
    handleSearch();
  }, [
    query,
    price,
    selectedCategory,
    selectedRating,
    selectedDistance,
    availableToday,
  ]);

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError('Геолокація не підтримується браузером');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      position => {
        setUserLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
      },
      error => {
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError('Доступ до геолокації заборонено');
            break;
          case error.POSITION_UNAVAILABLE:
            setLocationError('Місцезнаходження недоступне');
            break;
          case error.TIMEOUT:
            setLocationError('Час очікування вичерпано');
            break;
          default:
            setLocationError('Помилка визначення місцезнаходження');
        }
      },
    );
  }, []);

  return (
    <div className="home-page">
      <section className="hero">
        <div className="hero__content">
          <p className="hero__eyebrow">AI Рекомендації</p>
          <h1 className="hero__title">
            Знайдіть ідеального майстра за допомогою <span>AI</span>
          </h1>
          <p className="hero__subtitle">
            Опишіть, що вам потрібно, а ми знайдемо найкращі варіанти серед
            салонів та незалежних майстрів.
          </p>

          <div className="hero__search">
            <label className="hero__search-input-field">
              <span className="hero__search-icon">✨</span>
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
                placeholder="Пошук"
              />
            </label>
            <button
              type="button"
              className="hero__search-button"
              onClick={handleSearch}
            >
              Знайти
            </button>
          </div>
        </div>
      </section>

      <section className="home-page__search-section">
        <aside className="home-page__sidebar">
          <div className="home-page__panel home-page__panel--sticky">
            <div className="home-page__panel-header">
              <h2>Фільтри</h2>
              <button type="button">Очистити все</button>
            </div>

            <div className="home-page__filter-group">
              <h3>Категорія</h3>
              <div className="home-page__checkbox-list">
                {[
                  'Всі категорії',
                  'Манікюр',
                  'Перукар',
                  'Барбери',
                  'Косметологія',
                  'Масаж',
                ].map(name => (
                  <label key={name} className="home-page__checkbox-item">
                    <input
                      type="radio"
                      name="category"
                      checked={selectedCategory === name}
                      onChange={() => setSelectedCategory(name)}
                    />
                    <span>{name}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="home-page__filter-group">
              <h3>Ціна, грн</h3>
              <div className="home-page__range-input">
                <input
                  type="range"
                  min="0"
                  max="5000"
                  value={price}
                  onChange={event => setPrice(Number(event.target.value))}
                />
                <div className="home-page__price-value">
                  {price.toLocaleString('uk-UA')} грн
                </div>
                <div className="home-page__range-values">
                  <span>0</span>
                  <span>5000+</span>
                </div>
              </div>
            </div>

            <div className="home-page__filter-group">
              <h3>Рейтинг</h3>
              <div className="home-page__chip-list">
                {['Будь-який', '4.5+', '4.9+', '5.0'].map(name => (
                  <button
                    key={name}
                    type="button"
                    onClick={() => setSelectedRating(name)}
                    className={
                      selectedRating === name
                        ? 'home-page__chip home-page__chip--active'
                        : 'home-page__chip'
                    }
                  >
                    {name}
                  </button>
                ))}
              </div>
            </div>

            <div className="home-page__filter-group">
              <h3>Відстань</h3>
              <select
                value={selectedDistance}
                onChange={e => setSelectedDistance(e.target.value)}
              >
                <option>Будь-яка</option>
                <option>До 1 км</option>
                <option>До 3 км</option>
                <option>До 5 км</option>
              </select>
            </div>

            <div className="home-page__filter-group">
              <h3>Доступність</h3>
              <label className="home-page__switch">
                <input
                  type="checkbox"
                  checked={availableToday}
                  onChange={e => setAvailableToday(e.target.checked)}
                />
                <span>Доступний сьогодні</span>
              </label>
            </div>
            <div className="home-page__filter-group">
              <h3>Дата бронювання</h3>

              <input
                type="date"
                value={selectedDate}
                min={new Date().toISOString().split('T')[0]}
                onChange={e => setSelectedDate(e.target.value)}
                className="home-page__date-picker"
              />
            </div>
          </div>

          <div className="home-page__panel home-page__panel--compact">
            <h3>Популярні категорії</h3>
            <div className="home-page__popular-grid">
              {categories.map(item => (
                <div key={item.title} className="home-page__popular-card">
                  <div className="home-page__popular-card-icon">
                    {item.title.charAt(0)}
                  </div>
                  <div>
                    <p>{item.title}</p>
                    <span>{item.meta}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <div>
          <main className="home-page__results">
            <div className="home-page__cards-grid">
              {filteredResults.map(item => (
                <article key={item.title} className="home-page__result-card">
                  <div className="home-page__result-card-top">
                    <div className="home-page__result-card-badge">
                      {item.badge}
                    </div>
                    <button
                      className="heart-circle"
                      onClick={() => toggleFavorite(item.title)}
                    >
                      <img
                        className="heart"
                        src={
                          favorites.includes(item.title)
                            ? './icons/ActiveHeart.svg'
                            : './icons/heart.png'
                        }
                        alt="Favorite"
                      />
                    </button>
                  </div>

                  <div className="home-page__result-card-all">
                    <div className="home-page__result-card-image">
                      {item.image && <img src={item.image} alt={item.title} />}
                    </div>
                    <div className="home-page__result-card-body">
                      <div className="home-page__result-card-label">
                        {item.category}
                      </div>
                      <h3>{item.title}</h3>
                      <div className="home-page__result-card-info">
                        <span>{item.rating}</span>
                        <span>({item.reviews})</span>
                        <span>• {item.distance}</span>
                      </div>

                      <div className="home-page__result-card-services">
                        {item.services.map(service => (
                          <span key={service}>{service}</span>
                        ))}
                      </div>
                      <div className="home-page__result-card-footer">
                        <span>{item.price}</span>
                        {selectedDate && (
                          <div className="home-page__booking-date">
                            Дата: {selectedDate}
                          </div>
                        )}
                        <button
                          type="button"
                          className="home-page__result-card-button"
                          onClick={() => {
                            console.log('Майстер:', item.title);
                            console.log('Дата:', selectedDate);
                          }}
                        >
                          Перейти до бронювання
                        </button>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </main>
        </div>

        <aside className="home-page__map">
          <div className="home-page__map-card">
            <div className="home-page__map-card-header">
              <div>
                <h3>Карта</h3>
                <p>OpenStreetMap</p>
              </div>
              <div className="home-page__map-card-status">Показано 3</div>
            </div>

            <div className="home-page__map-card-canvas">
              <MapContainer
                center={
                  userLocation
                    ? [userLocation.lat, userLocation.lng]
                    : [50.4501, 30.5234]
                }
                zoom={13}
              >
                <TileLayer
                  attribution="&copy; OpenStreetMap contributors"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {userLocation && (
                  <MapRecenter center={[userLocation.lat, userLocation.lng]} />
                )}
                {userLocation && (
                  <Marker position={[userLocation.lat, userLocation.lng]}>
                    <Popup className="home-page__map-popup">
                      Ваше місцезнаходження
                    </Popup>
                  </Marker>
                )}
                {filteredResults.map(item => {
                  if (
                    typeof item.lat !== 'number' ||
                    typeof item.lng !== 'number'
                  ) {
                    return null;
                  }

                  const actualDistanceKm = userLocation
                    ? getDistanceKm(
                        userLocation.lat,
                        userLocation.lng,
                        item.lat,
                        item.lng,
                      )
                    : null;

                  // If we have user location, only show salons within 5 km
                  if (userLocation) {
                    if (actualDistanceKm !== null && actualDistanceKm <= 5) {
                      return (
                        <Marker
                          key={item.title}
                          position={[item.lat, item.lng]}
                        >
                          <Popup>
                            <strong>{item.title}</strong>
                            <br />
                            {item.category}
                            <br />
                            {actualDistanceKm !== null
                              ? `${actualDistanceKm.toFixed(1)} км від вас`
                              : item.distance}
                          </Popup>
                        </Marker>
                      );
                    }
                    return null;
                  }

                  // If no user location, show all salon markers
                  return (
                    <Marker key={item.title} position={[item.lat, item.lng]}>
                      <Popup>
                        <strong>{item.title}</strong>
                        <br />
                        {item.category}
                        <br />
                        {item.distance}
                      </Popup>
                    </Marker>
                  );
                })}
              </MapContainer>
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
};
