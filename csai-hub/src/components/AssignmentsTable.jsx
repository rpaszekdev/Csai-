import { ALL_ASSIGNMENTS } from "../data/courses";

export default function AssignmentsTable() {
  if (ALL_ASSIGNMENTS.length === 0) return null;

  return (
    <section className="exam-section">
      <h2 className="section-title">R e q u i r e d&ensp;&ensp;W o r k</h2>
      <div className="year-line" />
      <p className="exam-note">
        Due dates originally set at unusual times have been moved to the
        previous day for safety.
      </p>
      <div className="exam-table-wrap">
        <table className="exam-table">
          <thead>
            <tr>
              <th>Course</th>
              <th>Type</th>
              <th>Weight</th>
              <th>Min</th>
              <th>Due</th>
              <th>Rules</th>
            </tr>
          </thead>
          <tbody>
            {ALL_ASSIGNMENTS.map((a, i) => (
              <tr key={i}>
                <td>{a.course}</td>
                <td>{a.type}</td>
                <td>{a.weight}</td>
                <td>{a.min}</td>
                <td>{a.due}</td>
                <td>{a.rules}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
