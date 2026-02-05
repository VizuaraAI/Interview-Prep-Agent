'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axios from 'axios';
import { API_ENDPOINTS } from '../../../../config/api';

interface ProjectEvalData {
  detail_level: number;
  clarity: number;
  socrates_metric: number;
  overall_project_score: number;
  detail_justification: string;
  clarity_justification: string;
  socrates_justification: string;
  strengths: string[];
  weaknesses: string[];
  improvement_suggestions: string[];
}

export default function ProjectEvaluationPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = params.conversationId as string;
  const [evaluation, setEvaluation] = useState<ProjectEvalData | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const fetchEvaluation = async () => {
      try {
        const response = await axios.get(
          API_ENDPOINTS.EVALUATE_PROJECT(conversationId)
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
          console.error('Error fetching project evaluation:', err);
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

  const getBarColor = (score: number) => {
    if (score >= 9) return 'bg-green-500';
    if (score >= 7) return 'bg-blue-500';
    if (score >= 5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getPerformanceLevel = (score: number) => {
    if (score >= 9) return { text: 'Exceptional', color: 'text-green-600 bg-green-50' };
    if (score >= 8) return { text: 'Excellent', color: 'text-blue-600 bg-blue-50' };
    if (score >= 7) return { text: 'Good', color: 'text-blue-500 bg-blue-50' };
    if (score >= 6) return { text: 'Satisfactory', color: 'text-yellow-600 bg-yellow-50' };
    if (score >= 5) return { text: 'Needs Improvement', color: 'text-orange-600 bg-orange-50' };
    return { text: 'Poor', color: 'text-red-600 bg-red-50' };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Generating your project evaluation report...</p>
          {retryCount > 0 && (
            <p className="text-sm text-gray-400 mt-2">Analyzing your project discussion... ({retryCount})</p>
          )}
        </div>
      </div>
    );
  }

  if (error || !evaluation) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <div className="text-red-500 text-5xl mb-4">!</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  const performance = getPerformanceLevel(evaluation.overall_project_score);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Phase III - Project Discussion Evaluation</h1>
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
            <h2 className="text-xl font-semibold text-gray-600 mb-4">Overall Project Score</h2>
            <div className={`text-6xl font-bold ${getScoreColor(evaluation.overall_project_score)}`}>
              {evaluation.overall_project_score}
              <span className="text-3xl text-gray-400">/10</span>
            </div>
            <div className={`inline-block mt-4 px-4 py-2 rounded-full text-sm font-semibold ${performance.color}`}>
              {performance.text}
            </div>
          </div>
        </div>

        {/* Metric Breakdown */}
        <h3 className="text-xl font-bold text-gray-800 mb-4">Detailed Metrics</h3>
        <div className="space-y-4 mb-8">
          {/* Detail Level */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-semibold text-gray-800">Detail Level</h4>
              <span className={`text-2xl font-bold ${getScoreColor(evaluation.detail_level)}`}>
                {evaluation.detail_level}/10
              </span>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden mb-3">
              <div
                className={`h-full rounded-full transition-all ${getBarColor(evaluation.detail_level)}`}
                style={{ width: `${evaluation.detail_level * 10}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{evaluation.detail_justification}</p>
          </div>

          {/* Clarity */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-semibold text-gray-800">Clarity</h4>
              <span className={`text-2xl font-bold ${getScoreColor(evaluation.clarity)}`}>
                {evaluation.clarity}/10
              </span>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden mb-3">
              <div
                className={`h-full rounded-full transition-all ${getBarColor(evaluation.clarity)}`}
                style={{ width: `${evaluation.clarity * 10}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{evaluation.clarity_justification}</p>
          </div>

          {/* Socrates Metric */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-semibold text-gray-800">Socrates Metric (Follow-up Q&A)</h4>
              <span className={`text-2xl font-bold ${getScoreColor(evaluation.socrates_metric)}`}>
                {evaluation.socrates_metric}/10
              </span>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden mb-3">
              <div
                className={`h-full rounded-full transition-all ${getBarColor(evaluation.socrates_metric)}`}
                style={{ width: `${evaluation.socrates_metric * 10}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{evaluation.socrates_justification}</p>
          </div>
        </div>

        {/* Strengths & Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Strengths */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-green-700 mb-4 flex items-center gap-2">
              <span className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-green-600">+</span>
              Strengths
            </h3>
            <ul className="space-y-3">
              {evaluation.strengths?.map((strength, index) => (
                <li key={index} className="flex items-start gap-3 bg-green-50 p-3 rounded-lg">
                  <span className="text-green-500 mt-0.5">&#10003;</span>
                  <span className="text-sm text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Weaknesses */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-orange-700 mb-4 flex items-center gap-2">
              <span className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center text-orange-600">!</span>
              Areas for Growth
            </h3>
            <ul className="space-y-3">
              {evaluation.weaknesses?.map((weakness, index) => (
                <li key={index} className="flex items-start gap-3 bg-orange-50 p-3 rounded-lg">
                  <span className="text-orange-500 mt-0.5">&#9679;</span>
                  <span className="text-sm text-gray-700">{weakness}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Dynamic Recommendations */}
        {recommendations.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Personalized Recommendations</h3>
            <ul className="space-y-3">
              {recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="bg-green-100 text-green-600 rounded-full w-6 h-6 flex items-center justify-center text-sm font-semibold flex-shrink-0 mt-0.5">
                    {index + 1}
                  </span>
                  <span className="text-sm text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Improvement Suggestions from GPT eval */}
        {evaluation.improvement_suggestions && evaluation.improvement_suggestions.length > 0 && (
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Improvement Suggestions</h3>
            <ul className="space-y-3">
              {evaluation.improvement_suggestions.map((sug, index) => (
                <li key={index} className="flex items-start gap-3 bg-blue-50 p-3 rounded-lg">
                  <span className="text-blue-500 mt-0.5">&#8594;</span>
                  <span className="text-sm text-gray-700">{sug}</span>
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
            className="bg-green-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-green-700 transition-colors shadow-md"
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
