import { Routes, Route, Navigate } from "react-router-dom";
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
import DeepLearnDashboard from "./courses/deep-learn/routes/DeepLearnDashboard";
import DLQuizIndex from "./courses/deep-learn/routes/QuizIndex";
import DLQuizSession from "./courses/deep-learn/routes/QuizSession";
import RWDashboard from "./courses/research-workshop/routes/RWDashboard";
import RWQuizIndex from "./courses/research-workshop/routes/QuizIndex";
import RWQuizSession from "./courses/research-workshop/routes/QuizSession";
import NotesPage from "./routes/NotesPage";
import EventModal from "./components/EventModal";
import CoffeeButton from "./components/CoffeeButton";
import IdeShell from "./shell/IdeShell";
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
        <Route path="/" element={<IdeShell />} />
        <Route path="/home" element={<Landing />} />
        <Route path="/notes" element={<NotesPage />} />
        <Route path="/courses/cog-neuro" element={<CogNeuroDashboard />}>
          <Route index element={<RoadmapView />} />
          <Route path="roadmap" element={<RoadmapView />} />
          <Route path="quiz" element={<QuizIndex />} />
          <Route path="quiz/:sectionId/:quizType" element={<QuizSession />} />
          <Route path="brain-quiz" element={<BrainQuizView />} />
        </Route>
        <Route path="/courses/deep-learn" element={<DeepLearnDashboard />}>
          <Route index element={<DLQuizIndex />} />
          <Route path="quiz" element={<DLQuizIndex />} />
          <Route path="quiz/:sectionId/:quizType" element={<DLQuizSession />} />
        </Route>
        <Route path="/courses/rw" element={<RWDashboard />}>
          <Route index element={<Navigate to="quiz" replace />} />
          <Route path="quiz" element={<RWQuizIndex />} />
          <Route path="quiz/:sectionId/:quizType" element={<RWQuizSession />} />
        </Route>
      </Routes>
      <Analytics />
    </>
  );
}

export default App;
