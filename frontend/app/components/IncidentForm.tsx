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

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
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
    if (validationError) { onError(validationError); return; }
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
    } catch (err) {
      const e = err as any;
      onError(e?.response?.data?.detail || e?.message || 'Failed to submit incident');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">

      {/* Title */}
      <div className="space-y-1.5">
        <label htmlFor="title" className="block text-xs font-medium tracking-widest uppercase text-slate-400">
          Incident title <span className="text-red-400 normal-case tracking-normal">*</span>
        </label>
        <FormInput
          id="title"
          name="title"
          type="text"
          placeholder="e.g. Database connection timeout on prod-eu-1"
          value={formData.title}
          onChange={handleInputChange}
          maxLength={200}
          disabled={isLoading}
        />
        <p className="text-xs text-slate-400 text-right">{formData.title.length} / 200</p>
      </div>

      {/* Description */}
      <div className="space-y-1.5">
        <label htmlFor="description" className="block text-xs font-medium tracking-widest uppercase text-slate-400">
          Description <span className="text-red-400 normal-case tracking-normal">*</span>
        </label>
        <textarea
          id="description"
          name="description"
          placeholder="Symptoms, start time, affected services, steps to reproduce..."
          value={formData.description}
          onChange={handleInputChange}
          maxLength={2000}
          rows={6}
          disabled={isLoading}
          className="w-full px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 bg-white border border-slate-200 rounded-[10px] resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <p className="text-xs text-slate-400 text-right">{charCount} / 2000</p>
      </div>

      {/* Email */}
      <div className="space-y-1.5">
        <label htmlFor="email" className="block text-xs font-medium tracking-widest uppercase text-slate-400">
          Reporter email <span className="text-red-400 normal-case tracking-normal">*</span>
        </label>
        <FormInput
          id="email"
          name="reporter_email"
          type="email"
          placeholder="you@company.com"
          value={formData.reporter_email}
          onChange={handleInputChange}
          disabled={isLoading}
        />
      </div>

      {/* Attachment */}
      <div className="space-y-1.5">
        <label className="block text-xs font-medium tracking-widest uppercase text-slate-400">
          Attachment{" "}
          <span className="text-slate-300 normal-case tracking-normal font-normal">optional</span>
        </label>

        {!file ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border border-dashed rounded-[10px] p-7 text-center cursor-pointer transition-all duration-150 ${
              isDragging
                ? 'border-indigo-400 bg-indigo-500/5'
                : 'border-slate-200 bg-slate-50/60 hover:border-indigo-300 hover:bg-indigo-500/4'
            }`}
          >
            <div className="flex justify-center mb-3">
              <svg
                className={`w-7 h-7 transition-colors duration-150 ${isDragging ? 'text-indigo-500' : 'text-slate-300'}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </div>
            <p className="text-sm font-medium text-slate-600">
              {isDragging ? 'Release to attach' : 'Drag & drop or click to select'}
            </p>
            <p className="text-xs text-slate-400 mt-1">Screenshots, error logs, JSON payloads — max 10 MB</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.txt,.log,.json"
              onChange={handleFileChange}
              disabled={isLoading}
              className="hidden"
            />
          </div>
        ) : (
          <div className="border border-slate-200 rounded-[10px] p-4 bg-slate-50/60 flex items-start gap-3.5">
            {filePreview ? (
              <img
                src={filePreview}
                alt="Preview"
                className="w-14 h-14 object-cover rounded-lg border border-slate-200 flex-shrink-0"
              />
            ) : (
              <div className="w-14 h-14 flex items-center justify-center bg-slate-100 rounded-lg flex-shrink-0">
                <IconDocumentText className="w-6 h-6 text-slate-400" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">{file.name}</p>
              <p className="text-xs text-slate-400 mt-0.5">
                {(file.size / 1024).toFixed(1)} KB &middot; {file.type || 'unknown type'}
              </p>
              <div className="inline-flex items-center gap-1.5 mt-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="text-xs text-emerald-600 font-medium">Ready to attach</span>
              </div>
            </div>
            <button
              type="button"
              onClick={handleRemoveFile}
              disabled={isLoading}
              className="text-slate-300 hover:text-red-400 transition-colors duration-150 flex-shrink-0 p-1 -mr-1 -mt-1"
              aria-label="Remove file"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* Inline error */}
      {inlineError && (
        <div className="rounded-[10px] bg-red-500/5 border border-red-200/60 px-4 py-3 flex items-start gap-2.5">
          <IconExclamationTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-600 font-normal">{inlineError}</p>
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full inline-flex items-center justify-center gap-2 px-7 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white text-sm font-medium rounded-[10px] shadow-[0_4px_14px_rgba(79,70,229,0.28)] hover:shadow-[0_8px_24px_rgba(79,70,229,0.36)] hover:-translate-y-px transition-all duration-200"
      >
        {isLoading && (
          <svg className="animate-spin w-4 h-4 text-white/80" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {isLoading ? 'Submitting...' : 'Submit incident report'}
      </button>

    </form>
  );
}