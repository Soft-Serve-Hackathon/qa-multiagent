'use client';

import { useState, useRef, useCallback } from 'react';
import axios from 'axios';
import FormInput from './ui/FormInput';
import { IconDocumentText, IconExclamationTriangle } from './Icons';

interface IncidentFormProps {
  onSubmit: (incidentId: number, traceId: string) => void;
  onError: (error: string) => void;
  inlineError?: string | null;
}

export default function IncidentForm({ onSubmit, onError, inlineError }: IncidentFormProps) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    reporter_email: '',
  });

  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (name === 'description') setCharCount(value.length);
  };

  const processFile = useCallback((selectedFile: File) => {
    if (selectedFile.size > 10 * 1024 * 1024) {
      onError('File size exceeds 10MB limit');
      return;
    }
    const allowedMimes = ['image/png', 'image/jpeg', 'text/plain', 'application/json'];
    if (!allowedMimes.includes(selectedFile.type)) {
      onError('Only PNG, JPEG, TXT, and JSON files are allowed');
      return;
    }
    setFile(selectedFile);
    if (selectedFile.type.startsWith('image/')) {
      setFilePreview(URL.createObjectURL(selectedFile));
    } else {
      setFilePreview(null);
    }
  }, [onError]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) processFile(selectedFile);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) processFile(droppedFile);
  };

  const handleRemoveFile = () => {
    setFile(null);
    setFilePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const validateForm = (): string | null => {
    if (!formData.title.trim()) return 'Title is required';
    if (formData.title.length > 200) return 'Title must not exceed 200 characters';
    if (!formData.description.trim()) return 'Description is required';
    if (formData.description.length > 2000) return 'Description must not exceed 2000 characters';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.reporter_email)) return 'Please enter a valid email address';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateForm();
    if (validationError) {
      onError(validationError);
      return;
    }
    setIsLoading(true);
    try {
      const formDataObj = new FormData();
      formDataObj.append('title', formData.title);
      formDataObj.append('description', formData.description);
      formDataObj.append('reporter_email', formData.reporter_email);
      if (file) formDataObj.append('attachment', file);

      const response = await axios.post(`/api/incidents`, formDataObj, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.incident_id && response.data.trace_id) {
        onSubmit(response.data.incident_id, response.data.trace_id);
      } else {
        onError('No incident ID returned from server');
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to submit incident';
      onError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="form-group">
        <label htmlFor="title" className="block text-sm font-semibold text-slate-900 mb-2">
          Incident Title <span className="text-red-500">*</span>
        </label>
        <FormInput
          id="title"
          name="title"
          type="text"
          placeholder="What happened? (e.g., Database connection timeout)"
          value={formData.title}
          onChange={handleInputChange}
          maxLength={200}
          disabled={isLoading}
        />
        <p className="text-xs text-slate-500 mt-1">{formData.title.length}/200 characters</p>
      </div>

      <div className="form-group">
        <label htmlFor="description" className="block text-sm font-semibold text-slate-900 mb-2">
          Description <span className="text-red-500">*</span>
        </label>
        <textarea
          id="description"
          name="description"
          placeholder="Provide detailed context (symptoms, started at, affected services)..."
          value={formData.description}
          onChange={handleInputChange}
          maxLength={2000}
          rows={6}
          disabled={isLoading}
          className="input-field resize-none"
        />
        <p className="text-xs text-slate-500 mt-1">{charCount}/2000 characters</p>
      </div>

      <div className="form-group">
        <label htmlFor="email" className="block text-sm font-semibold text-slate-900 mb-2">
          Reporter Email <span className="text-red-500">*</span>
        </label>
        <FormInput
          id="email"
          name="reporter_email"
          type="email"
          placeholder="your.email@company.com"
          value={formData.reporter_email}
          onChange={handleInputChange}
          disabled={isLoading}
        />
      </div>

      {/* Drag-and-drop attachment zone */}
      <div className="form-group">
        <label className="block text-sm font-semibold text-slate-900 mb-2">
          Attachment <span className="text-slate-400 font-normal">(Optional)</span>
        </label>
        {!file ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
              isDragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100'
            }`}
          >
            <div className="flex justify-center mb-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </div>
            <p className="text-sm font-medium text-slate-700">
              {isDragging ? 'Drop file here' : 'Drag & drop or click to select'}
            </p>
            <p className="text-xs text-slate-500 mt-1">Screenshots, error logs, JSON payloads</p>
            <p className="text-xs text-slate-400 mt-1">PNG, JPEG, TXT, or JSON — max 10MB</p>
            <input
              ref={fileInputRef}
              id="file"
              name="file"
              type="file"
              accept=".png,.jpg,.jpeg,.txt,.log,.json"
              onChange={handleFileChange}
              disabled={isLoading}
              className="hidden"
            />
          </div>
        ) : (
          <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 flex items-start gap-4">
            {filePreview ? (
              <img
                src={filePreview}
                alt="Preview"
                className="w-16 h-16 object-cover rounded-lg border border-slate-200 flex-shrink-0"
              />
            ) : (
              <div className="w-16 h-16 flex items-center justify-center bg-slate-200 rounded-lg flex-shrink-0">
                <IconDocumentText className="w-8 h-8 text-slate-500" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{file.name}</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {(file.size / 1024).toFixed(1)} KB &middot; {file.type || 'unknown type'}
              </p>
              <p className="text-xs text-green-600 mt-1 font-medium">Ready to attach</p>
            </div>
            <button
              type="button"
              onClick={handleRemoveFile}
              disabled={isLoading}
              className="text-slate-400 hover:text-red-500 transition-colors text-xl leading-none flex-shrink-0"
              aria-label="Remove file"
            >
              &times;
            </button>
          </div>
        )}
      </div>

      {/* Inline error — form stays intact */}
      {inlineError && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 flex items-start gap-3">
          <IconExclamationTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700 font-medium">{inlineError}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="button-primary w-full flex items-center justify-center"
      >
        {isLoading && (
          <svg className="animate-spin mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {isLoading ? 'Submitting...' : 'Submit Incident Report'}
      </button>
    </form>
  );
}
