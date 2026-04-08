'use client';

import { useState } from 'react';
import axios from 'axios';
import FormInput from './ui/FormInput';

interface IncidentFormProps {
  onSubmit: (traceId: string) => void;
  onError: (error: string) => void;
}

export default function IncidentForm({ onSubmit, onError }: IncidentFormProps) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    reporter_email: '',
  });

  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [charCount, setCharCount] = useState(0);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (name === 'description') {
      setCharCount(value.length);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file size (10MB max)
      if (selectedFile.size > 10 * 1024 * 1024) {
        onError('File size exceeds 10MB limit');
        return;
      }

      // Validate MIME type
      const allowedMimes = ['image/png', 'image/jpeg', 'text/plain', 'application/json'];
      if (!allowedMimes.includes(selectedFile.type)) {
        onError('Only PNG, JPEG, TXT, and JSON files are allowed');
        return;
      }

      setFile(selectedFile);
    }
  };

  const validateForm = (): string | null => {
    // Title validation
    if (!formData.title.trim()) {
      return 'Title is required';
    }
    if (formData.title.length > 200) {
      return 'Title must not exceed 200 characters';
    }

    // Description validation
    if (!formData.description.trim()) {
      return 'Description is required';
    }
    if (formData.description.length > 2000) {
      return 'Description must not exceed 2000 characters';
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.reporter_email)) {
      return 'Please enter a valid email address';
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
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

      if (file) {
        formDataObj.append('attachment', file);
      }

      const response = await axios.post(`${API_URL}/incidents`, formDataObj, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.trace_id) {
        onSubmit(response.data.trace_id);
      } else {
        onError('No trace ID returned from server');
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
        <p className="text-xs text-slate-500 mt-1">
          {formData.title.length}/200 characters
        </p>
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
        <p className="text-xs text-slate-500 mt-1">
          {charCount}/2000 characters
        </p>
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

      <div className="form-group">
        <label htmlFor="file" className="block text-sm font-semibold text-slate-900 mb-2">
          Attachment (Optional)
        </label>
        <p className="text-xs text-slate-500 mb-2">
          PNG, JPEG, TXT, or JSON (max 10MB)
        </p>
        <input
          id="file"
          name="file"
          type="file"
          onChange={handleFileChange}
          disabled={isLoading}
          className="block w-full text-sm text-slate-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-md file:border-0
            file:text-sm file:font-semibold
            file:bg-slate-100 file:text-slate-700
            hover:file:bg-slate-200"
        />
        {file && (
          <p className="text-xs text-green-600 mt-2">
            ✓ {file.name}
          </p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="button-primary w-full flex items-center justify-center"
      >
        {isLoading && <span className="spinner mr-2">⏳</span>}
        {isLoading ? 'Submitting...' : 'Submit Incident Report'}
      </button>
    </form>
  );
}
