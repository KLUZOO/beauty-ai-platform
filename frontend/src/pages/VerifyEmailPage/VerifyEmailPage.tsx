import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { verifyEmail } from '../../services/authService';
import './VerifyEmailPage.scss';

type Status = 'loading' | 'success' | 'error';

export const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const id = searchParams.get('id');
  const token = searchParams.get('token');

  const [status, setStatus] = useState<Status>('loading');
  const [title, setTitle] = useState('Підтвердження...');
  const [message, setMessage] = useState(
    'Перевірка даних на сервері...',
  );

  useEffect(() => {
    const verifyEmailRequest = async () => {
      if (!id || !token) {
        setStatus('error');
        setTitle('Посилання некоректне');
        setMessage(
          'Посилання не містить даних для підтвердження.',
        );
        return;
      }

      try {
        const data = await verifyEmail(id, token);

        setStatus('success');
        setTitle('Email успішно підтверджено');
        setMessage(
          data?.message ||
            'Дякуємо! Ваш email успішно підтверджено.',
        );
      } catch (error) {
        console.error('verifyEmail error:', error);

        setStatus('error');
        setTitle('Не вдалося підтвердити email');

        setMessage(
          error instanceof Error
            ? error.message
            : 'Токен недійсний або прострочений.',
        );
      }
    };

    verifyEmailRequest();
  }, [id, token]);

  return (
    <section className="verify-email">
      <div className="verify-email__card">
        <div className="email-header">
          <div className="brand-icon" aria-hidden="true">
            <img
              className="brand-icon-img"
              src={`${import.meta.env.BASE_URL}icons/logo.png`}
              alt="Beauty AI Logo"
            />
          </div>
        </div>

        <div className="email-body">
          <h1 className="verify-email__title">
            {title}
          </h1>

          <p className="verify-email__message">
            {message}
          </p>

          <p className="note">
            Якщо ви не створювали обліковий запис,
            просто проігноруйте цей лист.
          </p>

          {status !== 'loading' && (
            <button
              type="button"
              className="verify-email__button"
              onClick={() => navigate('/login')}
            >
              Перейти до входу
            </button>
          )}
        </div>

        <div className="email-footer">
          <small>
            З любов&apos;ю, команда Beauty AI&nbsp;•{' '}
            <a
              href="http://beautyaiservice.polandcentral.cloudapp.azure.com/beauty.ai/"
              target="_blank"
              rel="noreferrer"
            >
              Перейти на сайт
            </a>
          </small>
        </div>
      </div>
    </section>
  );
};
