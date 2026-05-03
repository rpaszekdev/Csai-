import { Routes, Route } from "react-router-dom";
import { Analytics } from "@vercel/analytics/react";
import { PROGRAM } from "./data/courses";
import Year from "./components/Year";
import ExamTable from "./components/ExamTable";
import AssignmentsTable from "./components/AssignmentsTable";
import Introduction from "./components/Introduction";
import LandingSvg from "./components/LandingSvg";
import CogNeuroDashboard from "./courses/cog-neuro/routes/CogNeuroDashboard";
import RoadmapView from "./courses/cog-neuro/routes/RoadmapView";
import QuizIndex from "./courses/cog-neuro/routes/QuizIndex";
import QuizSession from "./courses/cog-neuro/routes/QuizSession";
import BrainQuizView from "./courses/cog-neuro/routes/BrainQuizView";
import NotesPage from "./routes/NotesPage";
import EventModal from "./components/EventModal";
import CoffeeButton from "./components/CoffeeButton";
import "./App.css";

const CURRENT_SEMESTER = 4;

function Landing() {
  return (
    <div className="hub">
      <header className="landing-svg">
        <LandingSvg />
      </header>

      <main className="content">
        <Introduction />
        {PROGRAM.map((y) => (
          <Year
            key={y.year}
            year={y.year}
            semesters={y.semesters}
            currentSemester={CURRENT_SEMESTER}
          />
        ))}
        <ExamTable />
        <AssignmentsTable />
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
    <>
      <CoffeeButton />
      <EventModal />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/notes" element={<NotesPage />} />
        <Route path="/courses/cog-neuro" element={<CogNeuroDashboard />}>
          <Route index element={<RoadmapView />} />
          <Route path="roadmap" element={<RoadmapView />} />
          <Route path="quiz" element={<QuizIndex />} />
          <Route path="quiz/:sectionId/:quizType" element={<QuizSession />} />
          <Route path="brain-quiz" element={<BrainQuizView />} />
        </Route>
      </Routes>
      <Analytics />
    </>
  );
}

export default App;
