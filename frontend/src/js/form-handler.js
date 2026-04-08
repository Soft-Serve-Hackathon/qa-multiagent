/**
 * form-handler.js — Form Submission and Validation
 * 
 * Responsibilities:
 * - Build and validate incident report form
 * - Handle form submission (POST /api/incidents)
 * - Validate fields on client-side before sending:
 *   * title: required, max 200 chars
 *   * description: required, max 2000 chars (with counter)
 *   * reporter_email: required, valid email format
 *   * attachment: optional, PNG/JPG/TXT/LOG, max 10MB
 * - Handle multipart/form-data encoding with file attachment
 * - Parse and relay backend validation errors to UI
 * 
 * States:
 * - idle: form ready for input
 * - loading: POST in flight, show spinner
 * - success: HTTP 201 received, show confirmation
 * - error-validation: HTTP 400 with validation details
 * - error-injection: HTTP 400 with prompt_injection_detected
 * - error-server: HTTP 500 or network error
 * 
 * TODO: Implement form builder, validation logic, and submission handler
 */
