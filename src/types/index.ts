export interface ComplaintData {
  scam_type: 'UPI_PHISHING' | 'FAKE_LOAN_APP' | 'IMPERSONATION' | 'LOTTERY_SCAM' | 'INVESTMENT_FRAUD';
  amount: number;
  victim_location: {
    lat: number;
    lon: number;
  };
}

export interface Hotspot {
  id: string;
  complaint_id: string;
  hotspot_location: {
    lat: number;
    lon: number;
  };
  location_name: string;
  confidence: number;
  time_window_mins: number;
  predicted_at: string;
  status: string;
}

export interface Cordon {
  id: string;
  center_location: {
    lat: number;
    lon: number;
  };
  radius_meters: number;
  expires_at: string;
  status: string;
}

export interface AlertConfig {
  sms_enabled: boolean;
  email_enabled: boolean;
  confidence_threshold: number;
}

export interface ComplaintResponse {
  success: boolean;
  complaint_id: string;
  message: string;
  prediction_triggered: boolean;
}

export interface RiskHeatmapResponse {
  complaints: any[];
  hotspots: Hotspot[];
  cordons: Cordon[];
  system_metrics: {
    active_complaints: number;
    active_hotspots: number;
    active_cordons: number;
    system_accuracy: number;
  };
}