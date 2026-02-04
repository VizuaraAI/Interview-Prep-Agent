'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axios from 'axios';

interface EvaluationData {
  student_name: string;
  final_score: number;
  performance_level: string;
  project_phase: {
    overall_score: number;
    detail_level: number;
    clarity: number;
    socrates_metric: number;
    strengths: string[];
    weaknesses: string[];
    justifications: {
      detail: string;
      clarity: string;
      socrates: string;
    };
  };
  factual_phase: {
    overall_score: number;
    total_questions: number;
    correct_answers: number;
    partially_correct: number;
    incorrect_answers: number;
    accuracy_rate: number;
  };
  improvement_suggestions: string[];
  next_steps: string[];
}

export default function EvaluationPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = params.conversationId as string;
  const [evaluation, setEvaluation] = useState<EvaluationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvaluation = async () => {
      try {
        const response = await axios.post(
          `http://localhost:8000/evaluate?conversation_id=${conversationId}`
        );
        setEvaluation(response.data.evaluation);
      } catch (err) {
        console.error('Error fetching evaluation:', err);
        setError('Failed to load evaluation. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (conversationId) {
      fetchEvaluation();
    }
  }, [conversationId]);

  const getScoreColor = (score: number) => {
    if (score >= 9) return 'text-green-600';
    if (score >= 7) return 'text-blue-600';
    if (score >= 5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceBadgeColor = (level: string) => {
    switch (level) {
      case 'Exceptional':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'Excellent':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Good':
        return 'bg-indigo-100 text-indigo-800 border-indigo-300';
      case 'Satisfactory':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'Needs Improvement':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      default:
        return 'bg-red-100 text-red-800 border-red-300';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Generating your evaluation report...</p>
        </div>
      </div>
    );
  }

  if (error || !evaluation) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Interview Evaluation Report</h1>
          <button
            onClick={() => router.push('/')}
            className="text-gray-600 hover:text-gray-800 transition-colors"
          >
            Return Home
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Student Name & Overall Score */}
        <div className="bg-white rounded-3xl shadow-xl p-8 mb-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-800 mb-2">
              {evaluation.student_name}
            </h2>
            <div className="flex items-center justify-center gap-4 mb-6">
              <div className="text-center">
                <div className={`text-6xl font-bold ${getScoreColor(evaluation.final_score)}`}>
                  {evaluation.final_score}
                  <span className="text-3xl text-gray-400">/10</span>
                </div>
                <p className="text-sm text-gray-500 mt-2">Overall Score</p>
              </div>
            </div>
            <span className={`inline-block px-6 py-2 rounded-full text-sm font-semibold border-2 ${getPerformanceBadgeColor(evaluation.performance_level)}`}>
              {evaluation.performance_level}
            </span>
          </div>
        </div>

        {/* Phase Scores Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Project Phase Card */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-blue-100 rounded-full p-2">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-800">Project Discussion</h3>
            </div>

            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-600">Overall Score</span>
                <span className={`text-2xl font-bold ${getScoreColor(evaluation.project_phase.overall_score)}`}>
                  {evaluation.project_phase.overall_score}/10
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Detail Level</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${evaluation.project_phase.detail_level * 10}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold text-gray-700 w-8">
                    {evaluation.project_phase.detail_level}/10
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Clarity</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 rounded-full"
                      style={{ width: `${evaluation.project_phase.clarity * 10}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold text-gray-700 w-8">
                    {evaluation.project_phase.clarity}/10
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Socrates Metric</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-500 rounded-full"
                      style={{ width: `${evaluation.project_phase.socrates_metric * 10}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold text-gray-700 w-8">
                    {evaluation.project_phase.socrates_metric}/10
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Factual Phase Card */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-purple-100 rounded-full p-2">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-gray-800">Factual Knowledge</h3>
            </div>

            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-600">Overall Score</span>
                <span className={`text-2xl font-bold ${getScoreColor(evaluation.factual_phase.overall_score)}`}>
                  {evaluation.factual_phase.overall_score}/10
                </span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Questions</span>
                <span className="text-lg font-semibold text-gray-700">
                  {evaluation.factual_phase.total_questions}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Accuracy Rate</span>
                <span className="text-lg font-semibold text-gray-700">
                  {evaluation.factual_phase.accuracy_rate}%
                </span>
              </div>

              <div className="pt-2 border-t border-gray-100">
                <div className="flex gap-4 text-xs">
                  <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                    <span className="text-gray-600">Correct: {evaluation.factual_phase.correct_answers}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
                    <span className="text-gray-600">Partial: {evaluation.factual_phase.partially_correct}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                    <span className="text-gray-600">Incorrect: {evaluation.factual_phase.incorrect_answers}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Strengths & Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Strengths */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="text-2xl">💪</div>
              <h3 className="text-xl font-bold text-gray-800">Strengths</h3>
            </div>
            <ul className="space-y-2">
              {evaluation.project_phase.strengths.map((strength, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-green-600 mt-1">✓</span>
                  <span className="text-sm text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Weaknesses */}
          <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="text-2xl">⚠️</div>
              <h3 className="text-xl font-bold text-gray-800">Areas for Growth</h3>
            </div>
            <ul className="space-y-2">
              {evaluation.project_phase.weaknesses.map((weakness, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-orange-600 mt-1">→</span>
                  <span className="text-sm text-gray-700">{weakness}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Improvement Suggestions */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <div className="text-2xl">💡</div>
            <h3 className="text-xl font-bold text-gray-800">Improvement Suggestions</h3>
          </div>
          <ul className="space-y-3">
            {evaluation.improvement_suggestions.map((suggestion, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="bg-blue-100 text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-semibold flex-shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <span className="text-sm text-gray-700">{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Next Steps */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-lg p-6 text-white">
          <div className="flex items-center gap-2 mb-4">
            <div className="text-2xl">🚀</div>
            <h3 className="text-xl font-bold">Next Steps</h3>
          </div>
          <ul className="space-y-3">
            {evaluation.next_steps.map((step, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="bg-white/20 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-semibold flex-shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <span className="text-sm text-white/90">{step}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex gap-4 justify-center">
          <button
            onClick={() => router.push('/')}
            className="bg-white text-gray-700 px-8 py-3 rounded-xl font-semibold hover:bg-gray-50 transition-colors shadow-md"
          >
            Return Home
          </button>
          <button
            onClick={() => window.print()}
            className="bg-blue-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-md"
          >
            Download Report
          </button>
        </div>
      </main>
    </div>
  );
}
