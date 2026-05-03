import { Link } from "react-router-dom";

export default function Introduction() {
  return (
    <section className="intro">
      <h2 className="section-title">I n t r o d u c t i o n</h2>
      <div className="year-line" />

      <p className="intro-body">
        Hey! I built this to save us all some time — every lecture, transcript,
        note and quiz in one place, ready to download and study.
      </p>

      <p className="intro-body">
        The notes are generated with Claude Opus 4.7, grounded in book chapters,
        slides and lecture transcripts, so the quality stays high.
      </p>

      <p className="intro-body">
        Studying is more fun together — if you'd like to contribute, drop me a
        message.
      </p>

      <p className="intro-signoff">— Robert</p>

      <div className="intro-actions">
        <Link className="resource-link" to="/notes">
          Notes
        </Link>
        <a
          className="resource-link"
          href="https://wa.me/48725850750"
          target="_blank"
          rel="noreferrer"
        >
          Contact · WhatsApp +48 725 850 750
        </a>
        <a
          className="resource-link"
          href="https://github.com/rpaszekdev/Csai-"
          target="_blank"
          rel="noreferrer"
        >
          Contribute · GitHub
        </a>
      </div>
    </section>
  );
}
