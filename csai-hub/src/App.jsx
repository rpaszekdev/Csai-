import { Routes, Route } from "react-router-dom";
import { PROGRAM } from "./data/courses";
import Year from "./components/Year";
import ExamTable from "./components/ExamTable";
import LandingSvg from "./components/LandingSvg";
import CogNeuroDashboard from "./courses/cog-neuro/routes/CogNeuroDashboard";
import RoadmapView from "./courses/cog-neuro/routes/RoadmapView";
import NotesIndex from "./courses/cog-neuro/routes/NotesIndex";
import NotesView from "./courses/cog-neuro/routes/NotesView";
import QuizIndex from "./courses/cog-neuro/routes/QuizIndex";
import QuizSession from "./courses/cog-neuro/routes/QuizSession";
import BrainQuizView from "./courses/cog-neuro/routes/BrainQuizView";
import "./App.css";

const CURRENT_SEMESTER = 4;

function Landing() {
  return (
    <div className="hub">
      <header className="landing-svg">
        <LandingSvg />
      </header>

      <main className="content">
        {PROGRAM.map((y) => (
          <Year
            key={y.year}
            year={y.year}
            semesters={y.semesters}
            currentSemester={CURRENT_SEMESTER}
          />
        ))}
        <ExamTable />
      </main>

      <footer className="footer">
        <div className="footer-line" />
        <p>CSAI&ensp;·&ensp;Tilburg University&ensp;·&ensp;2024 – 2027</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/courses/cog-neuro" element={<CogNeuroDashboard />}>
        <Route index element={<RoadmapView />} />
        <Route path="roadmap" element={<RoadmapView />} />
        <Route path="notes" element={<NotesIndex />} />
        <Route path="notes/:sectionId" element={<NotesView />} />
        <Route path="quiz" element={<QuizIndex />} />
        <Route path="quiz/:sectionId/:quizType" element={<QuizSession />} />
        <Route path="brain-quiz" element={<BrainQuizView />} />
      </Route>
    </Routes>
  );
}

export default App;
