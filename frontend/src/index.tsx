/* eslint-disable max-len */
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { App } from './App';
/* import { CartProvider } from './Functional/CartContext/CartContext'; */
import { HomePage } from './pages/HomePage/HomePage';
import { LoginPage } from './pages/LoginPage/LoginPage';
import { RegisterPage } from './pages/RegisterPage/RegisterPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage/VerifyEmailPage';
/* import { Aside } from './components/Aside/Aside'; */
/* import { PhonePage } from './pages/PhonePage/PhonePage'; */
/* import { TabletPage } from './pages/TabletPage/TabletPage'; */
/* import { AccessoriesPage } from './pages/AccessoriesPage/Accessories'; */
/* import { ProductDetailsPage } from './pages/ProductDetailsPage/ProductDetailsPage'; */
/* import { CartPage } from './pages/FunctionalPages/CartPage/CartPage'; */
/*import { FavoritesPage } from './pages/FunctionalPages/FavoritesPage/FavoritesPage';*/
/* import { NotFoundPage } from './pages/NotFoundPage/NotFoundPage'; */

const GOOGLE_CLIENT_ID =
  '136485800268-6lrfcd7uh3g14jhaspul8k2n8rpnm8o6.apps.googleusercontent.com';

const baseName = window.location.pathname.startsWith('/beauty.ai')
  ? '/beauty.ai'
  : '/';

const Root = () => (
  <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
    <Router basename={baseName}>
      {/* <CartProvider> */}
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<HomePage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route
            path="verify-email"
            element={<VerifyEmailPage />}
          />
          <Route path="*" element={<HomePage />} />
          {/* <Route path="menu" element={<Aside />} /> */}
          {/* <Route path="phones" element={<PhonePage />} /> */}
          {/* <Route path="tablets" element={<TabletPage />} /> */}
          {/* <Route path="accessories" element={<AccessoriesPage />} /> */}
          {/* <Route path="products/:productId" element={<ProductDetailsPage />} /> */}
          {/* <Route path="cart" element={<CartPage />} /> */}
          {/* <Route path="favorites" element={<FavoritesPage />} /> */}
          {/* <Route path="*" element={<NotFoundPage />} /> */}
        </Route>
      </Routes>
      {/* </CartProvider> */}
    </Router>
  </GoogleOAuthProvider>
);

createRoot(document.getElementById('root') as HTMLElement).render(<Root />);
