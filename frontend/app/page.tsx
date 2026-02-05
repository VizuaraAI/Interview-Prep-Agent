'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { API_ENDPOINTS } from '../config/api';

export default function Home() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [extractedData, setExtractedData] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
        setError('');
      } else {
        setError('Please upload a PDF file');
      }
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please upload a PDF file');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(API_ENDPOINTS.UPLOAD_RESUME, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setExtractedData(response.data);
      setUploadSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadSuccess(false);
    setExtractedData(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-apple-gray">
      {/* Header */}
      <header className="pt-16 pb-8 text-center">
        <h1 className="text-6xl font-semibold tracking-tight mb-4">
          ML Engineer Interview Prep
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Upload your resume to begin your personalized interview preparation journey
        </p>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 pb-20">
        {!uploadSuccess ? (
          <div className="card">
            {/* Upload Area */}
            <div
              className={`drag-area ${dragActive ? 'active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleChange}
                className="hidden"
              />

              <div className="text-center cursor-pointer">
                {/* Upload Icon */}
                <div className="mb-6">
                  <svg
                    className="w-20 h-20 mx-auto text-apple-blue"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                </div>

                {file ? (
                  <div>
                    <p className="text-2xl font-medium text-apple-dark mb-2">
                      {file.name}
                    </p>
                    <p className="text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-2xl font-medium text-apple-dark mb-2">
                      Drop your resume here
                    </p>
                    <p className="text-gray-500">
                      or click to browse files
                    </p>
                    <p className="text-sm text-gray-400 mt-4">
                      PDF format only
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-2xl">
                <p className="text-red-600 text-center">{error}</p>
              </div>
            )}

            {/* Upload Button */}
            {file && (
              <div className="mt-8 flex gap-4 justify-center">
                <button
                  onClick={handleReset}
                  className="px-8 py-3 rounded-full font-medium text-lg text-gray-600
                           hover:bg-gray-100 transition-all duration-300"
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="btn-primary"
                >
                  {uploading ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    'Upload Resume'
                  )}
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Success View */
          <div className="space-y-6">
            {/* Success Message */}
            <div className="card text-center">
              <div className="mb-6">
                <svg
                  className="w-20 h-20 mx-auto text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-3xl font-semibold mb-2">Resume Uploaded Successfully</h2>
              <p className="text-gray-600">Your resume has been processed and analyzed</p>
            </div>

            {/* Extracted Data */}
            {extractedData && (
              <div className="card">
                <h3 className="text-2xl font-semibold mb-6">Extracted Information</h3>

                {/* Contact Info */}
                <div className="mb-8">
                  <h4 className="text-lg font-medium text-apple-blue mb-3">Contact Information</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Name:</span>
                      <p className="font-medium">{extractedData.contact_info.name || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Email:</span>
                      <p className="font-medium">{extractedData.contact_info.email || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Phone:</span>
                      <p className="font-medium">{extractedData.contact_info.phone || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">GitHub:</span>
                      <p className="font-medium">{extractedData.contact_info.github || 'N/A'}</p>
                    </div>
                  </div>
                </div>

                {/* Sections */}
                <div className="space-y-6">
                  <h4 className="text-lg font-medium text-apple-blue">Resume Sections</h4>
                  {Object.keys(extractedData.sections).map((section) => (
                    <div key={section} className="border-l-4 border-apple-blue pl-4">
                      <h5 className="font-medium mb-2">{section}</h5>
                      <p className="text-sm text-gray-600 line-clamp-3">
                        {extractedData.sections[section]}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="mt-8 flex gap-4 justify-center">
                  <button
                    onClick={() => router.push(`/interview?student_id=${extractedData.student_id}&name=${encodeURIComponent(extractedData.contact_info.name)}`)}
                    className="btn-primary"
                  >
                    Start Interview
                  </button>
                  <button
                    onClick={handleReset}
                    className="px-8 py-3 rounded-full font-medium text-lg text-gray-600
                             hover:bg-gray-100 transition-all duration-300"
                  >
                    Upload Another Resume
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center pb-8 text-gray-500 text-sm">
        <p>Part 1: Resume Upload & Extraction</p>
      </footer>
    </div>
  );
}
