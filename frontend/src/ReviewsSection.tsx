import React, { useEffect, useState } from "react";
import { listReviews, type ApiReview } from "./api";
import "./styles.css";

interface ReviewWithMaster extends ApiReview {
  master_name?: string;
}

export default function ReviewsSection() {
  const [reviews, setReviews] = useState<ReviewWithMaster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadReviews = async () => {
      try {
        setLoading(true);
        const data = await listReviews(1);
        setReviews(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Помилка завантаження рецензій",
        );
      } finally {
        setLoading(false);
      }
    };

    loadReviews();
  }, []);

  const renderStars = (rating: number) => {
    return (
      <div style={{ display: "flex", gap: "4px" }}>
        {Array.from({ length: 5 }).map((_, i) => (
          <span
            key={i}
            style={{
              color: i < rating ? "#D4AF37" : "#E0E0E0",
              fontSize: "16px",
            }}
          >
            ★
          </span>
        ))}
      </div>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("uk-UA", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return <div className="reviews-section">Завантаження рецензій...</div>;
  }

  if (error) {
    return <div className="reviews-section">Помилка: {error}</div>;
  }

  return (
    <div className="reviews-section">
      <h2>Реальні оцінки клієнтів Beauty AI</h2>
      <div className="reviews-grid">
        {reviews.map((review) => (
          <div key={review.id} className="review-card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "start",
                marginBottom: "12px",
              }}
            >
              <div>{renderStars(review.rating)}</div>
              <span style={{ fontSize: "12px", color: "#666" }}>
                {formatDate(review.created_at)}
              </span>
            </div>

            <p style={{ margin: "12px 0", color: "#666", minHeight: "40px" }}>
              {review.comment || "Без коментара"}
            </p>

            <div style={{ borderTop: "1px solid #E0E0E0", paddingTop: "12px" }}>
              <a
                href={`/master/${review.master}`}
                style={{
                  color: "#8B4513",
                  textDecoration: "none",
                  fontSize: "14px",
                }}
              >
                Майстер #{review.master} →
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
                }}
              >
                Майстер #{review.master} →
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
