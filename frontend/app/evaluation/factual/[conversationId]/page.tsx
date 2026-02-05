'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axios from 'axios';
import { API_ENDPOINTS } from '../../../../config/api';

interface QuestionEval {
  question: string;
  student_answer: string;
  score: number;
  correctness: string;
  justification: string;
  expected_key_points: string[];
}

interface FactualEvalData {
  factual_score: number;
  total_questions: number;
  correct_answers: number;
  partially_correct_answers: number;
  incorrect_answers: number;
  detailed_evaluations: QuestionEval[];
}

export default function FactualEvaluationPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = params.conversationId as string;
  const [evaluation, setEvaluation] = useState<FactualEvalData | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const fetchEvaluation = async () => {
      try {
        const response = await axios.get(
          API_ENDPOINTS.EVALUATE_FACTUAL(conversationId)
        );
        if (response.data.success) {
          setEvaluation(response.data.evaluation);
          setRecommendations(response.data.recommendations || []);
          setLoading(false);
        }
      } catch (err: any) {
        if (err?.response?.status === 404 && retryCount < 20) {
          // Evaluation not ready yet, retry
          setTimeout(() => setRetryCount(prev => prev + 1), 3000);
        } else {
          console.error('Error fetching factual evaluation:', err);
          setError('Failed to load evaluation. Please try again.');
          setLoading(false);
        }
      }
    };

    if (conversationId) {
      fetchEvaluation();
    }
  }, [conversationId, retryCount]);

  const getScoreColor = (score: number) => {
    if (score >= 9) return 'text-green-600';
    if (score >= 7) return 'text-blue-600';
    if (score >= 5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getCorrectnessBadge = (correctness: string) => {
    switch (correctness) {
      case 'correct':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'partially_correct':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'incorrect':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getCorrectnessLabel = (correctness: string) => {
    switch (correctness) {
      case 'correct': return 'Correct';
      case 'partially_correct': return 'Partially Correct';
      case 'incorrect': return 'Incorrect';
      default: return correctness;
    }
  };

  const getCardBorder = (correctness: string) => {
    switch (correctness) {
      case 'correct': return 'border-l-green-500';
      case 'partially_correct': return 'border-l-yellow-500';
      case 'incorrect': return 'border-l-red-500';
      default: return 'border-l-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Generating your factual evaluation report...</p>
          {retryCount > 0 && (
            <p className="text-sm text-gray-400 mt-2">Analyzing your answers... ({retryCount})</p>
          )}
        </div>
      </div>
    );
  }

  if (error || !evaluation) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <div className="text-red-500 text-5xl mb-4">!</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const accuracyRate = evaluation.total_questions > 0
    ? Math.round((evaluation.correct_answers / evaluation.total_questions) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Phase IV - Factual Knowledge Evaluation</h1>
          <button
            onClick={() => router.push('/')}
            className="text-gray-600 hover:text-gray-800 transition-colors"
          >
            Return Home
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        {/* Overall Score Card */}
        <div className="bg-white rounded-3xl shadow-xl p-8 mb-8">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-600 mb-4">Factual Knowledge Score</h2>
            <div className={`text-6xl font-bold ${getScoreColor(evaluation.factual_score)}`}>
              {evaluation.factual_score}
              <span className="text-3xl text-gray-400">/10</span>
            </div>

            {/* Stats Row */}
            <div className="flex justify-center gap-8 mt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">{evaluation.total_questions}</div>
                <div className="text-sm text-gray-500">Questions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">{accuracyRate}%</div>
                <div className="text-sm text-gray-500">Accuracy</div>
              </div>
              <div className="text-center">
                <div className="flex gap-3 items-center">
                  <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                    <span className="text-sm font-semibold">{evaluation.correct_answers}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
                    <span className="text-sm font-semibold">{evaluation.partially_correct_answers}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-3 h-3 bg-red-500 rounded-full"></span>
                    <span className="text-sm font-semibold">{evaluation.incorrect_answers}</span>
                  </div>
                </div>
                <div className="text-sm text-gray-500 mt-1">Correct / Partial / Incorrect</div>
              </div>
            </div>
          </div>
        </div>

        {/* Per-Question Breakdown */}
        <h3 className="text-xl font-bold text-gray-800 mb-4">Question-by-Question Breakdown</h3>
        <div className="space-y-4 mb-8">
          {evaluation.detailed_evaluations?.map((qe, index) => (
            <div key={index} className={`bg-white rounded-2xl shadow-lg p-6 border-l-4 ${getCardBorder(qe.correctness)}`}>
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-semibold text-gray-800">Question {index + 1}</h4>
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getCorrectnessBadge(qe.correctness)}`}>
                    {getCorrectnessLabel(qe.correctness)}
                  </span>
                  <span className={`text-lg font-bold ${getScoreColor(qe.score)}`}>
                    {qe.score}/10
                  </span>
                </div>
              </div>

              {/* Question */}
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-500 mb-1">Question:</p>
                <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">{qe.question}</p>
              </div>

              {/* Student Answer */}
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-500 mb-1">Your Answer:</p>
                <p className="text-sm text-gray-700 bg-blue-50 p-3 rounded-lg border border-blue-100">
                  &ldquo;{qe.student_answer}&rdquo;
                </p>
              </div>

              {/* Justification */}
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-500 mb-1">Analysis:</p>
                <p className="text-sm text-gray-700">{qe.justification}</p>
              </div>

              {/* Expected Key Points */}
              {qe.expected_key_points && qe.expected_key_points.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-1">Expected Key Points:</p>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {qe.expected_key_points.map((point, i) => (
                      <li key={i}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Dynamic Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Personalized Recommendations</h3>
            <ul className="space-y-3">
              {recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="bg-purple-100 text-purple-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-semibold flex-shrink-0 mt-0.5">
                    {index + 1}
                  </span>
                  <span className="text-sm text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex gap-4 justify-center flex-wrap">
          <button
            onClick={() => window.close()}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 transition-colors shadow-md flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
            </svg>
            Return to Interview
          </button>
          <button
            onClick={() => window.print()}
            className="bg-purple-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-purple-700 transition-colors shadow-md"
          >
            Download Report
          </button>
          <button
            onClick={() => router.push('/')}
            className="bg-white text-gray-700 px-8 py-3 rounded-xl font-semibold hover:bg-gray-50 transition-colors shadow-md border border-gray-200"
          >
            Return Home
          </button>
        </div>
        <p className="text-center text-sm text-gray-500 mt-4">
          Tip: Close this tab to return to your interview
        </p>
      </main>
    </div>
  );
}
