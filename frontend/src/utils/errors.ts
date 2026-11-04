/**
 * Centralized API Error Classification Utility for Cohortly.
 * Maps HTTP status codes, network errors, and timeouts into clean, structured,
 * and user-friendly diagnostic representations without exposing internal role enums
 * or server-side Python stack traces.
 */

export interface ClassifiedError {
  type:
    | 'UNAUTHORIZED'
    | 'FORBIDDEN'
    | 'NOT_FOUND'
    | 'VALIDATION'
    | 'SERVER_ERROR'
    | 'TIMEOUT'
    | 'NETWORK_ERROR'
    | 'UNKNOWN';
  statusCode?: number;
  title: string;
  message: string;
  userMessage: string;
  isAccessRestricted: boolean;
}

export const RESTRICTED_ACCESS_MESSAGE =
  "This section isn't available for your current role. Your account does not have permission to view this information. Please switch to an authorized role or contact your platform administrator if you need access.";

export function classifyApiError(error: any): ClassifiedError {
  // 1. Check for client timeout (Axios ECONNABORTED)
  if (error?.code === 'ECONNABORTED' || error?.message?.toLowerCase().includes('timeout')) {
    const msg = 'The server took longer than expected to respond. The operation may still be processing in the background. Please try again.';
    return {
      type: 'TIMEOUT',
      title: 'Request Timed Out',
      message: msg,
      userMessage: msg,
      isAccessRestricted: false,
    };
  }

  // 2. Check for network failure (no HTTP response received from server)
  if (!error?.response) {
    const msg = 'Unable to connect to the Cohortly backend service. Please verify that the backend API server is active on port 8000.';
    return {
      type: 'NETWORK_ERROR',
      title: 'Backend Connection Error',
      message: msg,
      userMessage: msg,
      isAccessRestricted: false,
    };
  }

  const status = error.response.status;

  // 3. HTTP 401 Unauthorized
  if (status === 401) {
    const msg = 'Your active demo session is missing or invalid. Please select a valid role from the demo role switcher in the header.';
    return {
      type: 'UNAUTHORIZED',
      statusCode: 401,
      title: 'Authentication Required',
      message: msg,
      userMessage: msg,
      isAccessRestricted: true,
    };
  }

  // 4. HTTP 403 Forbidden / Access Restricted
  if (status === 403) {
    return {
      type: 'FORBIDDEN',
      statusCode: 403,
      title: 'Access Restricted',
      message: RESTRICTED_ACCESS_MESSAGE,
      userMessage: RESTRICTED_ACCESS_MESSAGE,
      isAccessRestricted: true,
    };
  }

  // 5. HTTP 404 Not Found
  if (status === 404) {
    const rawDetail = typeof error.response.data?.detail === 'string' ? error.response.data.detail : null;
    const msg = rawDetail || 'The requested entity, cohort, learner, or API resource could not be found.';
    return {
      type: 'NOT_FOUND',
      statusCode: 404,
      title: 'Resource Not Found',
      message: msg,
      userMessage: msg,
      isAccessRestricted: false,
    };
  }

  // 6. HTTP 422 Unprocessable Entity / Validation Error
  if (status === 422) {
    const msg = 'The submitted request parameters or payload did not meet schema constraints. Please check input parameters.';
    return {
      type: 'VALIDATION',
      statusCode: 422,
      title: 'Validation Error',
      message: msg,
      userMessage: msg,
      isAccessRestricted: false,
    };
  }

  // 7. HTTP 5xx Server Error
  if (status >= 500) {
    const msg = 'An unexpected internal error occurred on the server while processing this request. Please inspect backend logs.';
    return {
      type: 'SERVER_ERROR',
      statusCode: status,
      title: 'Internal Server Error',
      message: msg,
      userMessage: msg,
      isAccessRestricted: false,
    };
  }

  // 8. Other / Unknown Error
  const fallbackMessage =
    typeof error.response?.data?.detail === 'string'
      ? error.response.data.detail
      : error.message || 'An unexpected error occurred while communicating with the backend.';

  return {
    type: 'UNKNOWN',
    statusCode: status,
    title: 'Unexpected Error',
    message: fallbackMessage,
    userMessage: fallbackMessage,
    isAccessRestricted: false,
  };
}

/**
 * Helper to check whether an error represents a 403 Forbidden / Access Restriction.
 */
export function isForbiddenError(error: any): boolean {
  return error?.response?.status === 403;
}
