"use client";

import { Plus, X } from "lucide-react";
import { useState } from "react";
import { authInputClass } from "@/components/AuthCard";
import { ApiError } from "@/lib/api/client";
import { createQuiz } from "@/lib/api/assessments";
import type { AnswerInput, QuestionInput, QuizDetail, Section } from "@/lib/api/types";

function emptyQuestion(sortOrder: number): QuestionInput {
  return {
    type: "single_choice",
    prompt: "",
    explanation: "",
    sort_order: sortOrder,
    answers: [{ text: "", is_correct: true, sort_order: 0 }],
  };
}

export function QuizBuilder({
  courseId,
  sections,
  token,
}: {
  courseId: string;
  sections: Section[];
  token: string;
}) {
  const [quizzes, setQuizzes] = useState<QuizDetail[]>([]);
  const [title, setTitle] = useState("");
  const [attemptsAllowed, setAttemptsAllowed] = useState("1");
  const [passScore, setPassScore] = useState("70");
  const [sectionId, setSectionId] = useState("");
  const [questions, setQuestions] = useState<QuestionInput[]>([emptyQuestion(0)]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateQuestion(index: number, patch: Partial<QuestionInput>) {
    setQuestions((prev) => prev.map((q, i) => (i === index ? { ...q, ...patch } : q)));
  }

  function updateAnswer(qIndex: number, aIndex: number, patch: Partial<AnswerInput>) {
    setQuestions((prev) =>
      prev.map((q, i) =>
        i === qIndex
          ? { ...q, answers: q.answers.map((a, j) => (j === aIndex ? { ...a, ...patch } : a)) }
          : q
      )
    );
  }

  function addAnswer(qIndex: number) {
    setQuestions((prev) =>
      prev.map((q, i) =>
        i === qIndex
          ? {
              ...q,
              answers: [
                ...q.answers,
                { text: "", is_correct: false, sort_order: q.answers.length },
              ],
            }
          : q
      )
    );
  }

  function removeAnswer(qIndex: number, aIndex: number) {
    setQuestions((prev) =>
      prev.map((q, i) =>
        i === qIndex ? { ...q, answers: q.answers.filter((_, j) => j !== aIndex) } : q
      )
    );
  }

  function addQuestion() {
    setQuestions((prev) => [...prev, emptyQuestion(prev.length)]);
  }

  function removeQuestion(index: number) {
    setQuestions((prev) => prev.filter((_, i) => i !== index));
  }

  function resetForm() {
    setTitle("");
    setAttemptsAllowed("1");
    setPassScore("70");
    setSectionId("");
    setQuestions([emptyQuestion(0)]);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const quiz = await createQuiz(
        courseId,
        {
          title,
          attempts_allowed: Number(attemptsAllowed) || 1,
          pass_score: Number(passScore) || 0,
          section: sectionId || null,
          questions: questions.filter((q) => q.prompt.trim()),
        },
        token
      );
      setQuizzes((prev) => [quiz, ...prev]);
      resetForm();
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create the quiz.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      {quizzes.length > 0 && (
        <ul className="space-y-2">
          {quizzes.map((quiz) => (
            <li
              key={quiz.id}
              className="rounded-lg border border-border bg-surface-hover px-3 py-2 text-sm"
            >
              <span className="font-medium text-foreground">{quiz.title}</span>
              <span className="ml-2 text-xs text-foreground/50">
                {quiz.questions.length} question{quiz.questions.length === 1 ? "" : "s"} · pass{" "}
                {quiz.pass_score}%
              </span>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-surface p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Quiz title"
            className={`sm:col-span-3 ${authInputClass}`}
          />
          <input
            type="number"
            min="1"
            value={attemptsAllowed}
            onChange={(e) => setAttemptsAllowed(e.target.value)}
            placeholder="Attempts allowed"
            className={authInputClass}
          />
          <input
            type="number"
            min="0"
            max="100"
            value={passScore}
            onChange={(e) => setPassScore(e.target.value)}
            placeholder="Pass score %"
            className={authInputClass}
          />
          <select
            value={sectionId}
            onChange={(e) => setSectionId(e.target.value)}
            className={authInputClass}
          >
            <option value="">No section</option>
            {sections.map((section) => (
              <option key={section.id} value={section.id}>
                {section.title}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          {questions.map((question, qIndex) => (
            <div key={qIndex} className="rounded-lg border border-border-strong bg-background/40 p-3">
              <div className="flex items-start gap-2">
                <div className="flex-1 space-y-2">
                  <input
                    type="text"
                    value={question.prompt}
                    onChange={(e) => updateQuestion(qIndex, { prompt: e.target.value })}
                    placeholder="Question prompt"
                    className={authInputClass}
                  />
                  <select
                    value={question.type}
                    onChange={(e) =>
                      updateQuestion(qIndex, {
                        type: e.target.value as QuestionInput["type"],
                      })
                    }
                    className={authInputClass}
                  >
                    <option value="single_choice">Single choice</option>
                    <option value="multiple_choice">Multiple choice</option>
                  </select>
                </div>
                <button
                  type="button"
                  onClick={() => removeQuestion(qIndex)}
                  className="rounded-full p-1.5 text-foreground/40 hover:bg-surface-hover hover:text-rose-400"
                  aria-label="Remove question"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-3 space-y-2 pl-1">
                {question.answers.map((answer, aIndex) => (
                  <div key={aIndex} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={answer.is_correct}
                      onChange={(e) =>
                        updateAnswer(qIndex, aIndex, { is_correct: e.target.checked })
                      }
                      className="h-4 w-4 rounded border-border-strong"
                      title="Correct answer"
                    />
                    <input
                      type="text"
                      value={answer.text}
                      onChange={(e) => updateAnswer(qIndex, aIndex, { text: e.target.value })}
                      placeholder="Answer text"
                      className={authInputClass}
                    />
                    <button
                      type="button"
                      onClick={() => removeAnswer(qIndex, aIndex)}
                      className="rounded-full p-1 text-foreground/40 hover:text-rose-400"
                      aria-label="Remove answer"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => addAnswer(qIndex)}
                  className="flex items-center gap-1 text-xs font-medium text-teal-400 hover:text-teal-300"
                >
                  <Plus className="h-3.5 w-3.5" /> Add answer
                </button>
              </div>
            </div>
          ))}

          <button
            type="button"
            onClick={addQuestion}
            className="flex items-center gap-1.5 text-sm font-medium text-teal-400 hover:text-teal-300"
          >
            <Plus className="h-4 w-4" /> Add question
          </button>
        </div>

        {error && <p className="text-sm text-rose-400">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !title.trim()}
          className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Creating…" : "Create quiz"}
        </button>
      </form>
    </div>
  );
}
