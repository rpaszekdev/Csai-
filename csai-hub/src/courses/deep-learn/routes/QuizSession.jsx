import { useParams } from "react-router-dom";
import SharedQuizSession from "../../../shared/quiz/QuizSession";
import { getQuiz } from "../lib/pregeneratedQuizzes";

export default function QuizSession() {
  const { sectionId, quizType } = useParams();
  return (
    <SharedQuizSession
      courseId="deep-learn"
      sectionId={sectionId}
      quizType={quizType}
      getQuiz={getQuiz}
      backPath="../"
    />
  );
}
