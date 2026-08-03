"use client";

import { Plus, X } from "lucide-react";
import { useState } from "react";
import { authInputClass } from "@/components/AuthCard";
import { ApiError } from "@/lib/api/client";
import { createCodingExercise } from "@/lib/api/assessments";
import type { CodingExerciseDetail, Section, TestCaseInput } from "@/lib/api/types";

function emptyTestCase(): TestCaseInput {
  return { input: "", expected_output: "", is_hidden: true, weight: 1 };
}

export function CodingExerciseBuilder({
  courseId,
  sections,
  token,
}: {
  courseId: string;
  sections: Section[];
  token: string;
}) {
  const [exercises, setExercises] = useState<CodingExerciseDetail[]>([]);
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [starterCode, setStarterCode] = useState("");
  const [timeLimitMs, setTimeLimitMs] = useState("2000");
  const [memoryLimitMb, setMemoryLimitMb] = useState("256");
  const [sectionId, setSectionId] = useState("");
  const [testCases, setTestCases] = useState<TestCaseInput[]>([emptyTestCase()]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateTestCase(index: number, patch: Partial<TestCaseInput>) {
    setTestCases((prev) => prev.map((tc, i) => (i === index ? { ...tc, ...patch } : tc)));
  }

  function removeTestCase(index: number) {
    setTestCases((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim() || !prompt.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const exercise = await createCodingExercise(
        courseId,
        {
          title,
          prompt,
          starter_code: starterCode,
          language: "python",
          time_limit_ms: Number(timeLimitMs) || 2000,
          memory_limit_mb: Number(memoryLimitMb) || 256,
          section: sectionId || null,
          test_cases: testCases.filter((tc) => tc.expected_output.trim()),
        },
        token
      );
      setExercises((prev) => [exercise, ...prev]);
      setTitle("");
      setPrompt("");
      setStarterCode("");
      setSectionId("");
      setTestCases([emptyTestCase()]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message_ : "Couldn't create the coding exercise.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      {exercises.length > 0 && (
        <ul className="space-y-2">
          {exercises.map((exercise) => (
            <li
              key={exercise.id}
              className="rounded-lg border border-border bg-surface-hover px-3 py-2 text-sm text-foreground/80"
            >
              {exercise.title}{" "}
              <span className="text-xs text-foreground/40">({exercise.language})</span>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-border bg-surface p-4">
        <input
          type="text"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Exercise title"
          className={authInputClass}
        />
        <textarea
          required
          rows={3}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Problem statement"
          className={authInputClass}
        />
        <textarea
          rows={3}
          value={starterCode}
          onChange={(e) => setStarterCode(e.target.value)}
          placeholder="Starter code (Python)"
          className={`font-mono ${authInputClass}`}
        />

        <div className="grid grid-cols-3 gap-3">
          <input
            type="number"
            min="1"
            value={timeLimitMs}
            onChange={(e) => setTimeLimitMs(e.target.value)}
            placeholder="Time limit (ms)"
            className={authInputClass}
          />
          <input
            type="number"
            min="1"
            value={memoryLimitMb}
            onChange={(e) => setMemoryLimitMb(e.target.value)}
            placeholder="Memory limit (MB)"
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

        <div className="space-y-2">
          <span className="block text-sm font-medium text-foreground/70">Test cases</span>
          {testCases.map((testCase, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                type="text"
                value={testCase.input}
                onChange={(e) => updateTestCase(index, { input: e.target.value })}
                placeholder="Input"
                className={authInputClass}
              />
              <input
                type="text"
                value={testCase.expected_output}
                onChange={(e) => updateTestCase(index, { expected_output: e.target.value })}
                placeholder="Expected output"
                className={authInputClass}
              />
              <label className="flex items-center gap-1.5 whitespace-nowrap text-xs text-foreground/60">
                <input
                  type="checkbox"
                  checked={testCase.is_hidden}
                  onChange={(e) => updateTestCase(index, { is_hidden: e.target.checked })}
                  className="h-4 w-4 rounded border-border-strong"
                />
                Hidden
              </label>
              <button
                type="button"
                onClick={() => removeTestCase(index)}
                className="rounded-full p-1 text-foreground/40 hover:text-rose-400"
                aria-label="Remove test case"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => setTestCases((prev) => [...prev, emptyTestCase()])}
            className="flex items-center gap-1.5 text-sm font-medium text-teal-400 hover:text-teal-300"
          >
            <Plus className="h-4 w-4" /> Add test case
          </button>
        </div>

        {error && <p className="text-sm text-rose-400">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !title.trim() || !prompt.trim()}
          className="rounded-full bg-teal-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Creating…" : "Create coding exercise"}
        </button>
      </form>
    </div>
  );
}
