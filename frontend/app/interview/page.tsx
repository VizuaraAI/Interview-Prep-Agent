'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api';

interface Message {
  role: 'assistant' | 'user';
  content: string;
  audio?: string;
}

function InterviewContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const studentId = searchParams.get('student_id');
  const studentName = searchParams.get('name');

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [readyToStart, setReadyToStart] = useState(true);
  const [starting, setStarting] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [currentPhase, setCurrentPhase] = useState<string>('greeting');
  const [studentTopics, setStudentTopics] = useState<string[]>([]);
  const [showTopics, setShowTopics] = useState(false);
  const [isInterviewerSpeaking, setIsInterviewerSpeaking] = useState(false);
  const [showInterruptionWarning, setShowInterruptionWarning] = useState(false);
  const [questionMetadata, setQuestionMetadata] = useState<any>(null);
  const [interviewComplete, setInterviewComplete] = useState(false);
  const [projectPhaseComplete, setProjectPhaseComplete] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    scrollToBottom();

    // Play audio for the latest assistant message
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      if (latestMessage.role === 'assistant' && latestMessage.audio) {
        setTimeout(() => {
          playAudio(latestMessage.audio!);
        }, 100);
      }
    }
  }, [messages]);

  useEffect(() => {
    console.log('Current Phase:', currentPhase);
    // Mark project phase as complete when we move past it
    if (currentPhase === 'gpa_questions' || currentPhase === 'factual_questions') {
      setProjectPhaseComplete(true);
    }
  }, [currentPhase]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const playAudio = (audioBase64: string) => {
    if (audioRef.current && audioBase64) {
      const audioBlob = base64ToBlob(audioBase64, 'audio/mpeg');
      const audioUrl = URL.createObjectURL(audioBlob);
      audioRef.current.src = audioUrl;

      audioRef.current.onplay = () => setIsInterviewerSpeaking(true);
      audioRef.current.onended = () => setIsInterviewerSpeaking(false);
      audioRef.current.onpause = () => setIsInterviewerSpeaking(false);

      audioRef.current.play().catch(err => {
        console.error('Error playing audio:', err);
        setIsInterviewerSpeaking(false);
      });
    }
  };

  const base64ToBlob = (base64: string, mimeType: string) => {
    const byteCharacters = atob(base64);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += 512) {
      const slice = byteCharacters.slice(offset, offset + 512);
      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }

    return new Blob(byteArrays, { type: mimeType });
  };

  const startConversation = async () => {
    setReadyToStart(false);
    setStarting(true);

    try {
      const response = await axios.post(API_ENDPOINTS.START_CONVERSATION(studentId!));
      setConversationId(response.data.conversation_id);
      setCurrentPhase(response.data.phase || 'greeting');
      setMessages([{
        role: 'assistant',
        content: response.data.message,
        audio: response.data.audio
      }]);
    } catch (error) {
      console.error('Error starting conversation:', error);
    } finally {
      setStarting(false);
    }
  };

  const sendMessage = async () => {
    if (!userInput.trim() || !conversationId) return;

    // If interviewer is speaking, stop audio and allow user to respond
    if (isInterviewerSpeaking && audioRef.current) {
      audioRef.current.pause();
      setIsInterviewerSpeaking(false);
    }

    const userMessage: Message = {
      role: 'user',
      content: userInput
    };

    setMessages(prev => [...prev, userMessage]);
    setUserInput('');
    setLoading(true);

    try {
      const response = await axios.post(
        API_ENDPOINTS.CONTINUE_CONVERSATION(conversationId!),
        { message: userInput }
      );

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.message,
        audio: response.data.audio
      };

      setMessages(prev => [...prev, assistantMessage]);

      const newPhase = response.data.phase || currentPhase;
      console.log('Backend returned phase:', response.data.phase, '| Current phase:', currentPhase, '| New phase:', newPhase);
      if (newPhase !== currentPhase) {
        console.log('Phase changing from', currentPhase, 'to', newPhase);
        setCurrentPhase(newPhase);

        if (newPhase === 'factual_questions' && response.data.student_topics) {
          setStudentTopics(response.data.student_topics);
          setShowTopics(true);
          setTimeout(() => setShowTopics(false), 5000);
        }
      }

      if (response.data.question_metadata) {
        setQuestionMetadata(response.data.question_metadata);
      }

      // Track interview completion from backend
      if (response.data.interview_complete) {
        setInterviewComplete(true);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startRecording = async () => {
    if (isInterviewerSpeaking) {
      setShowInterruptionWarning(true);
      setTimeout(() => setShowInterruptionWarning(false), 3000);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await transcribeAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please ensure you have granted microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setIsTranscribing(true);

    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'audio.wav');

      const response = await axios.post(API_ENDPOINTS.SPEECH_TO_TEXT, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const transcribedText = response.data.text;
      setUserInput(transcribedText);
    } catch (error) {
      console.error('Error transcribing audio:', error);
      alert('Error transcribing audio. Please try again.');
    } finally {
      setIsTranscribing(false);
    }
  };

  if (readyToStart) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white to-apple-gray flex items-center justify-center">
        <div className="text-center card max-w-md">
          <h1 className="text-3xl font-semibold mb-4">Ready to Begin?</h1>
          <p className="text-gray-600 mb-2">Candidate: {studentName}</p>
          <p className="text-gray-500 text-sm mb-8">
            Click the button below to start your ML Engineer interview with Raj.
          </p>
          <button
            onClick={startConversation}
            className="btn-primary w-full"
          >
            Start Interview
          </button>
        </div>
      </div>
    );
  }

  if (starting) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white to-apple-gray flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-apple-blue mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Preparing your interview...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-apple-gray">
      <audio ref={audioRef} className="hidden" />

      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-semibold">ML Engineer Interview</h1>
              <p className="text-gray-600">Candidate: {studentName}</p>
            </div>

            {/* Phase Indicator */}
            <div className="flex gap-2">
              <span className={`px-4 py-2 rounded-full text-sm font-medium transition-all bg-green-500 text-white`}>
                Phase I
              </span>
              <span className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                currentPhase === 'greeting' ? 'bg-apple-blue text-white' :
                ['project_questions', 'gpa_questions', 'factual_questions'].includes(currentPhase) ? 'bg-green-500 text-white' :
                'bg-gray-200 text-gray-600'
              }`}>
                Phase II
              </span>
              <span className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                currentPhase === 'project_questions' ? 'bg-apple-blue text-white' :
                ['gpa_questions', 'factual_questions'].includes(currentPhase) ? 'bg-green-500 text-white' :
                'bg-gray-200 text-gray-600'
              }`}>
                Phase III
              </span>
              <span className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                currentPhase === 'factual_questions' ? 'bg-apple-blue text-white' :
                currentPhase === 'gpa_questions' ? 'bg-gray-200 text-gray-600' :
                'bg-gray-200 text-gray-600'
              }`}>
                Phase IV
              </span>
            </div>
          </div>

          {/* RAG Matching Details - Show in Phase IV */}
          {currentPhase === 'factual_questions' && questionMetadata && questionMetadata.current_topic && (
            <div className="mt-3 bg-purple-50 border border-purple-200 rounded-xl p-3">
              <div className="flex items-start gap-3">
                <div className="bg-purple-500 rounded-full p-1.5 mt-0.5">
                  <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    <span className="text-xs font-medium text-purple-900">RAG Match:</span>
                    {questionMetadata.current_topic && (
                      <span className="bg-white px-2 py-0.5 rounded-full text-xs font-medium text-purple-700 border border-purple-200">
                        {questionMetadata.current_topic}
                      </span>
                    )}
                    {questionMetadata.similarity_score !== null && questionMetadata.similarity_score !== undefined && (
                      <span className="text-xs text-purple-700">
                        Similarity: <span className="font-semibold">{(questionMetadata.similarity_score * 100).toFixed(1)}%</span>
                        {questionMetadata.max_similarity && (
                          <span className="text-purple-600"> (Max: {(questionMetadata.max_similarity * 100).toFixed(1)}%)</span>
                        )}
                      </span>
                    )}
                  </div>

                  {questionMetadata.question_text && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-purple-900 mb-1">Question from Bank:</p>
                      <p className="text-xs text-purple-800 bg-white p-2 rounded border border-purple-100">
                        &ldquo;{questionMetadata.question_text}&rdquo;
                      </p>
                    </div>
                  )}

                  {questionMetadata.question_source && (
                    <div className="mb-1">
                      <p className="text-xs text-purple-700">
                        <span className="font-medium">Source:</span> {questionMetadata.question_source} section of ML Questions Bank
                      </p>
                    </div>
                  )}

                  {questionMetadata.match_reason && (
                    <p className="text-xs text-purple-600 mt-1">{questionMetadata.match_reason}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Chat Messages */}
      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* RAG Topics Display */}
        {showTopics && studentTopics.length > 0 && (
          <div className="bg-blue-50 border-2 border-blue-200 rounded-2xl p-4 mb-4 animate-fade-in">
            <div className="flex items-start gap-3">
              <div className="bg-blue-500 rounded-full p-2">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900 mb-2">RAG Analysis Complete</h3>
                <p className="text-sm text-blue-800 mb-2">Based on your resume, we&apos;ve identified these ML topics:</p>
                <div className="flex flex-wrap gap-2">
                  {studentTopics.map((topic, index) => (
                    <span key={index} className="bg-white px-3 py-1 rounded-full text-sm font-medium text-blue-700 border border-blue-200">
                      {topic}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-blue-600 mt-2">Questions will be tailored to these topics</p>
              </div>
            </div>
          </div>
        )}

        {/* Interruption Warning */}
        {showInterruptionWarning && (
          <div className="bg-yellow-50 border-2 border-yellow-300 rounded-2xl p-4 mb-4 animate-fade-in">
            <div className="flex items-center gap-3">
              <div className="bg-yellow-500 rounded-full p-2">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-900">Please let the interviewer finish speaking before responding.</p>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-3xl shadow-xl p-6 min-h-[600px] max-h-[600px] overflow-y-auto mb-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`mb-6 flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-2xl px-6 py-4 ${
                  message.role === 'user'
                    ? 'bg-apple-blue text-white'
                    : 'bg-apple-gray text-apple-dark'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-full bg-apple-blue flex items-center justify-center text-white font-semibold">
                      R
                    </div>
                    <span className="font-medium text-sm">Raj (Interviewer)</span>
                  </div>
                )}
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start mb-6">
              <div className="bg-apple-gray rounded-2xl px-6 py-4">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white rounded-3xl shadow-xl p-4">
          <div className="flex gap-4">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your response or use the microphone..."
              className="flex-1 rounded-2xl border-2 border-gray-200 px-6 py-4 focus:outline-none focus:border-apple-blue resize-none"
              rows={2}
              disabled={loading || isRecording || isTranscribing}
            />
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={loading || isTranscribing}
              className={`h-fit self-end px-6 py-3 rounded-2xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                isRecording
                  ? 'bg-red-500 text-white hover:bg-red-600'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              title={isRecording ? 'Stop Recording' : 'Start Recording'}
            >
              {isRecording ? (
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <rect x="6" y="6" width="8" height="8" rx="1" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>
            <button
              onClick={sendMessage}
              disabled={loading || !userInput.trim() || isRecording || isTranscribing}
              className="btn-primary h-fit self-end disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2 px-2">
            {isRecording ? 'Recording... Click the microphone to stop' :
             isTranscribing ? 'Transcribing your speech...' :
             'Type or click the microphone to speak. Press Enter to send.'}
          </p>
        </div>

        {/* Evaluation Buttons - Show at bottom */}
        {(projectPhaseComplete || interviewComplete) && (
          <div className="mt-6 bg-gradient-to-r from-gray-50 to-slate-50 rounded-3xl shadow-lg p-6 border-2 border-gray-200">
            <div className="text-center mb-4">
              <h3 className="text-lg font-bold text-gray-800">
                {interviewComplete ? 'Interview Complete!' : 'Phase III Complete!'}
              </h3>
              <p className="text-sm text-gray-600">
                {interviewComplete
                  ? 'View your evaluation scores for each phase.'
                  : 'Your project discussion has been evaluated.'}
              </p>
            </div>
            <div className="flex flex-wrap gap-4 justify-center">
              {/* Phase 3 (Project) Scores Button - Opens in new tab */}
              {projectPhaseComplete && (
                <button
                  onClick={() => window.open(`/evaluation/project/${conversationId}`, '_blank')}
                  className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-md flex items-center gap-2"
                >
                  <span>View Phase 3 Scores</span>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </button>
              )}

              {/* Phase 4 (Factual) Scores Button - Opens in new tab */}
              {interviewComplete && (
                <button
                  onClick={() => window.open(`/evaluation/factual/${conversationId}`, '_blank')}
                  className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all shadow-md flex items-center gap-2"
                >
                  <span>View Phase 4 Scores</span>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function InterviewPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading interview...</p>
        </div>
      </div>
    }>
      <InterviewContent />
    </Suspense>
  );
}
