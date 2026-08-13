/* eslint-disable max-len */
import { NavLink, Link, useLocation } from 'react-router-dom';
import './Header.scss';
import classNames from 'classnames';
import { Aside } from '../Aside/Aside';
import { useState, useEffect } from 'react';
import {
  isAuthenticated,
  getUserInfo,
  logout,
} from '../../services/authService';

const navItems = [
  { label: 'Головна', to: '/' },
  { label: 'Майстри', to: '#' },
  { label: 'Обране', to: '/favorites' },
  { label: 'Про нас', to: '#' },
];

export const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [authState, setAuthState] = useState({
    isAuth: isAuthenticated(),
    user: getUserInfo(),
  });
  const favoritesCount = 0;

  const location = useLocation();

  useEffect(() => {
    const checkAuth = () => {
      setAuthState({
        isAuth: isAuthenticated(),
        user: getUserInfo(),
      });
    };

    // Check on mount and when route changes
    checkAuth();

    // Listen for storage changes (logout from other tabs)
    window.addEventListener('storage', checkAuth);
    return () => window.removeEventListener('storage', checkAuth);
  }, [location]);

  const getLinkClass = ({ isActive }: { isActive: boolean }) =>
    classNames('navbar-item', {
      'is-active': isActive,
    });

  const toggleMenu = () => {
    setIsMenuOpen(prev => !prev);
  };

  const handleLogout = () => {
    logout();
    setAuthState({
      isAuth: false,
      user: null,
    });
  };

  return (
    <header className="header">
      <div className="header__container">
        <Link to="/" className="header__brand">
          <img src="./icons/logo.png" alt="Beauty AI logo" />
        </Link>

        <nav className="header__nav">
          {navItems.map(item =>
            item.to.startsWith('/') ? (
              <NavLink key={item.label} to={item.to} className={getLinkClass}>
                {item.label}
              </NavLink>
            ) : (
              <a key={item.label} href={item.to} className="navbar-item">
                {item.label}
              </a>
            ),
          )}
        </nav>

        <div className="header__actions">
          <button type="button" className="header__locale">
            UA
          </button>
          <Link to="/favorites" className="header__icon-link">
            <img src="./icons/ActiveHeart.svg" alt="Favorites" />
            {favoritesCount > 0 && (
              <span className="cart-count">{favoritesCount}</span>
            )}
          </Link>

          {authState.isAuth ? (
            <div className="header__user-section">
              <span className="header__user-name">
                {authState.user?.name || 'User'}
              </span>
              <button
                type="button"
                className="header__button header__button--ghost"
                onClick={handleLogout}
              >
                Вийти
              </button>
            </div>
          ) : (
            <div className="header__auth-section">
              <Link
                to="/login"
                className="header__button header__button--ghost"
              >
                Увійти
              </Link>
              <Link
                to="/register"
                className="header__button header__button--ghost"
              >
                Реєстрація
              </Link>
            </div>
          )}

          <button className="header__burger" type="button" onClick={toggleMenu}>
            <span />
            <span />
            <span />
          </button>
        </div>
      </div>

      <Aside isMenuOpen={isMenuOpen} onClose={() => setIsMenuOpen(false)} />
    </header>
  );
};
