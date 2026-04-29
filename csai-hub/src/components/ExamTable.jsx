import { ALL_EXAMS } from "../data/courses";

export default function ExamTable() {
  if (ALL_EXAMS.length === 0) return null;

  return (
    <section className="exam-section">
      <h2 className="section-title">E x a m&ensp;&ensp;S c h e d u l e</h2>
      <div className="year-line" />
      <div className="exam-table-wrap">
        <table className="exam-table">
          <thead>
            <tr>
              <th>Course</th>
              <th>Type</th>
              <th>Weight</th>
              <th>Min</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {ALL_EXAMS.map((e, i) => (
              <tr key={i}>
                <td>{e.course}</td>
                <td>
                  {e.type} <span className="exam-format">({e.format})</span>
                </td>
                <td>{e.weight}</td>
                <td>{e.min}</td>
                <td>{e.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
