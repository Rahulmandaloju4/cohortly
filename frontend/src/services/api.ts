import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercept request to inject current demo role and learner ID headers
api.interceptors.request.use((config) => {
  const currentRole = localStorage.getItem('cohortly_demo_role') || 'PLATFORM_ADMIN';
  config.headers['X-Demo-Role'] = currentRole;
  const currentLearnerId = localStorage.getItem('cohortly_demo_learner_id') || 'LRN-000001';
  config.headers['X-Demo-Learner-Id'] = currentLearnerId;
  return config;
});

// Dashboard APIs
export const getDashboardOverview = async () => {
  const res = await api.get('/dashboard/overview');
  return res.data;
};

export const getEngagementTrends = async (weeks = 6) => {
  const res = await api.get(`/dashboard/engagement-trend?weeks=${weeks}`);
  return res.data;
};

export const getCompletionTrends = async () => {
  const res = await api.get('/dashboard/completion-trend');
  return res.data;
};

// Learners APIs
export const getLearners = async (params: Record<string, any> = {}) => {
  const res = await api.get('/learners', { params });
  return res.data;
};

export const getLearnerDetail = async (learnerId: string) => {
  const res = await api.get(`/learners/${learnerId}`);
  return res.data;
};

export const getLearnerActivity = async (learnerId: string, params: Record<string, any> = {}) => {
  const res = await api.get(`/learners/${learnerId}/activity`, { params });
  return res.data;
};

// Courses APIs
export const getCourses = async (params: Record<string, any> = {}) => {
  const res = await api.get('/courses', { params });
  return res.data;
};

export const getCourseDetail = async (courseId: string) => {
  const res = await api.get(`/courses/${courseId}`);
  return res.data;
};

export const getCourseAnalytics = async (courseId: string) => {
  const res = await api.get(`/courses/${courseId}/analytics`);
  return res.data;
};

// Cohorts APIs
export const getCohorts = async () => {
  const res = await api.get('/cohorts');
  return res.data;
};

export const getCohortAnalytics = async (cohortId: string) => {
  const res = await api.get(`/cohorts/${cohortId}/analytics`);
  return res.data;
};

export const compareCohorts = async (cohortIds: string[]) => {
  const params = new URLSearchParams();
  cohortIds.forEach((id) => params.append('cohort_ids', id));
  const res = await api.get(`/cohorts/compare?${params.toString()}`);
  return res.data;
};

// Assessments APIs
export const getAssessments = async (params: Record<string, any> = {}) => {
  const res = await api.get('/assessments', { params });
  return res.data;
};

export const getAssessmentProgress = async (params: Record<string, any> = {}) => {
  const res = await api.get('/assessments/progress', { params });
  return res.data;
};

// Analytics APIs
export const getEngagementAnalytics = async () => {
  const res = await api.get('/analytics/engagement');
  return res.data;
};

export const getCompletionAnalytics = async () => {
  const res = await api.get('/analytics/completion');
  return res.data;
};

export const getContentUsageAnalytics = async (courseId?: string) => {
  const params = courseId ? { course_id: courseId } : {};
  const res = await api.get('/analytics/content-usage', { params });
  return res.data;
};

// Exceptions APIs
export const getExceptions = async (params: Record<string, any> = {}) => {
  const res = await api.get('/exceptions', { params });
  return res.data;
};

export const getExceptionDetail = async (exceptionId: string) => {
  const res = await api.get(`/exceptions/${exceptionId}`);
  return res.data;
};

export const updateExceptionStatus = async (
  exceptionId: string,
  payload: { status: string; reason: string; actor_id?: string }
) => {
  const res = await api.patch(`/exceptions/${exceptionId}/status`, payload);
  return res.data;
};

// Data Management APIs
export const triggerDataGeneration = async (payload: {
  profile: string;
  seed: number;
  num_learners?: number;
  num_courses?: number;
  num_enrollments?: number;
  num_events?: number;
}) => {
  const res = await api.post('/data/generate', payload);
  return res.data;
};

export const getDataStatus = async () => {
  const res = await api.get('/data/status');
  return res.data;
};

export const getDataValidation = async (force: boolean = false) => {
  const res = await api.get(`/data/validation${force ? '?force=true' : ''}`);
  return res.data;
};

export const getDataManifest = async (force: boolean = false) => {
  const res = await api.get(`/data/manifest${force ? '?force=true' : ''}`);
  return res.data;
};

export const getDataBenchmark = async () => {
  const res = await api.get('/data/benchmark');
  return res.data;
};

export const getExportUrl = (format: string, table: string) => {
  return `/api/data/export/${format}?table=${table}`;
};

export default api;
