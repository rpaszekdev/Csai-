import SharedQuizIndex from "../../../shared/quiz/QuizIndex";
import { listSections, QUIZ_TYPES } from "../lib/pregeneratedQuizzes";

export default function QuizIndex() {
  return (
    <SharedQuizIndex
      courseId="rw"
      listSections={listSections}
      QUIZ_TYPES={QUIZ_TYPES}
    />
  );
}
