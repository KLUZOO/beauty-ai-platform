import './Footer.scss';

export const Footer = () => {
  const handleScrollToTop = () => {
    document.documentElement.scrollTo({
      top: 0,
      behavior: 'smooth',
    });
  };

  return (
    <footer className="footer">
      <div className="footer__container">
        <div className="footer__img">
          <img src="./icons/logo.png" alt="Nice-Gadgets-Logo" />
        </div>
        <button className="footer__up-link" onClick={handleScrollToTop}>
          <p>Back to top</p>
          <img src="./icons/Up.svg" alt="Back to top arrow" />
        </button>
      </div>
    </footer>
  );
};
