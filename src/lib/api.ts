import axios from 'axios';
import { ComplaintData, ComplaintResponse, RiskHeatmapResponse } from '@/types';

// API client configuration
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status} from ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Complaint submission
export const submitComplaint = async (data: ComplaintData): Promise<ComplaintResponse> => {
  const response = await api.post('/api/submit-complaint', data);
  return response.data;
};

// Risk heatmap data
export const getRiskHeatmap = async (): Promise<RiskHeatmapResponse> => {
  const response = await api.get('/api/risk-heatmap');
  return response.data;
};

// LEA feedback submission
export const submitFeedback = async (data: { hotspot_id: string; lea_action: string; notes?: string }) => {
  const response = await api.post('/api/feedback', data);
  return response.data;
};

// Digital cordon activation
export const activateCordon = async (data: { hotspot_id: string; radius_meters?: number; duration_minutes?: number }) => {
  const response = await api.post('/api/activate-cordon', data);
  return response.data;
};

// Get active cordons
export const getActiveCordons = async () => {
  const response = await api.get('/api/active-cordons');
  return response.data;
};

// Deactivate cordon
export const deactivateCordon = async (cordonId: string) => {
  const response = await api.delete(`/api/deactivate-cordon/${cordonId}`);
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};