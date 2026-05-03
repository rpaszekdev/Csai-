import { useState, useEffect } from "react";

const EXPIRY = new Date("2026-05-11T17:00:00+02:00");
const DISMISS_KEY = "builders-lab-dismissed";
const WHATSAPP_URL =
  "https://chat.whatsapp.com/Fj5RNX1vGppJT9jM7MZfg1?mode=gi_t";

export default function EventModal() {
  const [modalVisible, setModalVisible] = useState(false);
  const [posterOpen, setPosterOpen] = useState(false);
  const [bannerVisible, setBannerVisible] = useState(true);
  const [expired] = useState(() => new Date() >= EXPIRY);

  useEffect(() => {
    if (expired) return;
    if (sessionStorage.getItem(DISMISS_KEY)) return;

    const target = document.querySelector(".year");
    if (!target) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setModalVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 },
    );

    observer.observe(target);
    return () => observer.disconnect();
  }, [expired]);

  if (expired) return null;

  const dismissModal = () => {
    setModalVisible(false);
    sessionStorage.setItem(DISMISS_KEY, "1");
  };

  return (
    <>
      {bannerVisible && (
        <div className="event-side-banner">
          <button
            className="banner-close"
            onClick={() => setBannerVisible(false)}
            aria-label="Close banner"
          >
            &times;
          </button>
          <button
            className="banner-img-btn"
            onClick={() => setPosterOpen(true)}
            aria-label="View event poster"
          >
            <img
              src="/builders-lab-poster.jpg"
              alt="Build your first AI agent — May 11"
            />
          </button>
        </div>
      )}

      {posterOpen && (
        <div className="event-backdrop" onClick={() => setPosterOpen(false)}>
          <div className="poster-lightbox" onClick={(e) => e.stopPropagation()}>
            <button
              className="event-close"
              onClick={() => setPosterOpen(false)}
              aria-label="Close"
            >
              &times;
            </button>
            <img
              className="poster-lightbox-img"
              src="/builders-lab-poster.jpg"
              alt="Build your first AI agent — May 11"
            />
            <p className="event-note">
              I'll be there helping out people setting up and showing some AI
              tricks — please come join us!
            </p>
            <a
              className="event-cta"
              href={WHATSAPP_URL}
              target="_blank"
              rel="noreferrer"
            >
              Join the group to sign up
            </a>
          </div>
        </div>
      )}

      {modalVisible && (
        <div className="event-backdrop" onClick={dismissModal}>
          <div className="poster-lightbox" onClick={(e) => e.stopPropagation()}>
            <button
              className="event-close"
              onClick={dismissModal}
              aria-label="Close"
            >
              &times;
            </button>
            <img
              className="poster-lightbox-img"
              src="/builders-lab-poster.jpg"
              alt="Build your first AI agent — May 11"
            />
            <p className="event-note">
              I'll be there helping out people setting up and showing some AI
              tricks — please come join us!
            </p>
            <a
              className="event-cta"
              href={WHATSAPP_URL}
              target="_blank"
              rel="noreferrer"
            >
              Join the group to sign up
            </a>
          </div>
        </div>
      )}
    </>
  );
}
