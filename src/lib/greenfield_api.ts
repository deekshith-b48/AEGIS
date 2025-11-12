/**
 * Project AEGIS Greenfield API Client
 * Matches exact FastAPI backend specifications
 */

import axios from 'axios';

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

// Types for Greenfield API

export interface GreenfieldComplaintRequest {
  fraud_type: 'UPI_PHISHING' | 'FAKE_LOAN_APP' | 'IMPERSONATION' | 'LOTTERY_SCAM' | 'INVESTMENT_FRAUD';
  amount: number;
  victim_lat: number;
  victim_lon: number;
}

export interface GreenfieldComplaintResponse {
  success: boolean;
  complaint_id: string;
  message: string;
  prediction_triggered: boolean;
}

export interface GreenfieldFeedbackRequest {
  hotspot_id: string;
  outcome: 'confirmed' | 'false';
}

export interface GreenfieldCordonRequest {
  hotspot_id: string;
}

export interface GreenfieldRiskHeatmapResponse {
  success: boolean;
  complaints: any[]; // GeoJSON FeatureCollection
  hotspots: any[];
  cordons: any[];
  system_metrics: {
    active_complaints: number;
    active_hotspots: number;
    active_cordons: number;
    system_accuracy: number;
    rule_weights: {
      fake_loan_app: number;
      high_value: number;
      upi_phishing: number;
      fallback: number;
    };
  };
}

// API Functions - Exact Backend Endpoints

/**
 * POST /submit-complaint
 * Validates and stores citizen report, triggers prediction
 */
export const submitComplaint = async (data: GreenfieldComplaintRequest): Promise<GreenfieldComplaintResponse> => {
  const response = await api.post('/submit-complaint', data);
  return response.data;
};

/**
 * GET /risk-heatmap
 * Returns GeoJSON of active complaints + hotspots (last 90 mins)
 */
export const getRiskHeatmap = async (): Promise<GreenfieldRiskHeatmapResponse> => {
  const response = await api.get('/risk-heatmap');
  return response.data;
};

/**
 * POST /feedback
 * Logs LEA outcome ('confirmed'/'false') for learning loop
 */
export const submitFeedback = async (data: GreenfieldFeedbackRequest) => {
  const response = await api.post('/feedback', data);
  return response.data;
};

/**
 * POST /activate-cordon
 * Creates simulated digital cordon (2km radius, 45-min expiry)
 */
export const activateCordon = async (data: GreenfieldCordonRequest) => {
  const response = await api.post('/activate-cordon', data);
  return response.data;
};

/**
 * POST /re-weight-rules
 * Manual endpoint to simulate nightly rule re-weighting for demo
 */
export const reweightRules = async (feedbackType: 'confirmed' | 'false') => {
  const response = await api.post('/re-weight-rules', null, {
    params: { feedback_type: feedbackType }
  });
  return response.data;
};

/**
 * GET /health
 * Health check endpoint
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;