import Semester from "./Semester";

export default function Year({ year, semesters, currentSemester }) {
  return (
    <section className="year">
      <h2 className="year-title">Y e a r&ensp;{year}</h2>
      <div className="year-line" />
      {semesters.map((s) => (
        <Semester
          key={s.number}
          number={s.number}
          courses={s.courses}
          defaultOpen={s.number === currentSemester}
        />
      ))}
    </section>
  );
}
