import { useState } from "react";

export default function CoffeeButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        className="coffee-btn"
        onClick={() => setOpen(true)}
        aria-label="Support this project"
      >
        Support this project
      </button>

      {open && (
        <div className="event-backdrop" onClick={() => setOpen(false)}>
          <div className="support-modal" onClick={(e) => e.stopPropagation()}>
            <button
              className="event-close"
              onClick={() => setOpen(false)}
              aria-label="Close"
            >
              &times;
            </button>

            <div className="support-columns">
              <div className="support-left">
                <p className="support-invite">
                  I'll be there helping out people setting up and showing some
                  AI tricks — please come join us!
                </p>
                <img
                  className="support-poster"
                  src="/builders-lab-poster.jpg"
                  alt="Build your first AI agent — May 11"
                />
              </div>

              <div className="support-right">
                <h2 className="support-heading">Thank you for the support!</h2>
                <p className="support-sub">
                  It really means a lot to see appreciation for this project.
                </p>
                <p className="support-qr-label">SCAN WITH REVOLUT</p>
                <img
                  className="support-qr"
                  src="/revolut-qr.png"
                  alt="Revolut QR code"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
