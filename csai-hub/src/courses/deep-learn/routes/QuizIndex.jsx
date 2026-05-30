import SharedQuizIndex from "../../../shared/quiz/QuizIndex";
import { listSections, QUIZ_TYPES } from "../lib/pregeneratedQuizzes";

export default function QuizIndex() {
  return (
    <SharedQuizIndex
      courseId="deep-learn"
      listSections={listSections}
      QUIZ_TYPES={QUIZ_TYPES}
    />
  );
}
