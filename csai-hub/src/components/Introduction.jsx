export default function Introduction() {
  return (
    <section className="intro">
      <h2 className="section-title">I n t r o d u c t i o n</h2>
      <div className="year-line" />

      <p className="intro-eyebrow">
        Open source project initiated by Robert Paszek.
      </p>

      <p className="intro-body">
        This platform is a community-driven resource for CSAI students at
        Tilburg University. Our goal is to create comprehensive,
        easy-to-understand summaries of all CSAI lectures and course materials.
      </p>

      <p className="intro-body">
        Have anything to add? We are looking for more contributors.
      </p>

      <div className="intro-actions">
        <a
          className="resource-link"
          href="https://wa.me/48725850750"
          target="_blank"
          rel="noreferrer"
        >
          Contact · WhatsApp +48 725 850 750
        </a>
        <span className="resource-link">Contributors</span>
      </div>
    </section>
  );
}
