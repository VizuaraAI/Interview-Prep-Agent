// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  UPLOAD_RESUME: `${API_BASE_URL}/upload-resume`,
  START_CONVERSATION: (studentId: string) => `${API_BASE_URL}/start-conversation/${studentId}`,
  CONTINUE_CONVERSATION: (conversationId: string) => `${API_BASE_URL}/continue-conversation/${conversationId}`,
  SPEECH_TO_TEXT: `${API_BASE_URL}/speech-to-text`,
  EVALUATE: (conversationId: string) => `${API_BASE_URL}/evaluate?conversation_id=${conversationId}`,
  EVALUATE_PROJECT: (conversationId: string) => `${API_BASE_URL}/evaluate/project/${conversationId}`,
  EVALUATE_FACTUAL: (conversationId: string) => `${API_BASE_URL}/evaluate/factual/${conversationId}`,
};
