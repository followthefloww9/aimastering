export interface Track {
  id: number;
  filename: string;
  duration?: number;
  sample_rate?: number;
  channels?: number;
  predicted_genre?: string;
  genre_confidence?: number;
  tempo?: number;
  key?: string;
  loudness?: LoudnessData;
  spectral_features?: SpectralFeatures;
  frequency_analysis?: FrequencyAnalysis;
  masking_analysis?: MaskingAnalysis;
  stereo_analysis?: StereoAnalysis;
  is_analyzed: boolean;
  is_processed: boolean;
  analysis_error?: string;
  created_at: string;
}

export interface LoudnessData {
  rms_db: number;
  peak_db: number;
  lufs_approx: number;
  lufs_integrated: number;
  dynamic_range: number;
}

export interface SpectralFeatures {
  mfcc_mean: number[];
  mfcc_std: number[];
  spectral_centroid_mean: number;
  spectral_rolloff_mean: number;
  zero_crossing_rate_mean: number;
}

export interface FrequencyAnalysis {
  frequency_bands: {
    sub_bass: number;
    bass: number;
    low_mid: number;
    mid: number;
    high_mid: number;
    presence: number;
    brilliance: number;
  };
  dominant_frequency: number;
  spectral_balance: {
    bass: string;
    mid: string;
    brilliance: string;
  };
}

export interface EQBand {
  frequency: number;
  gain: number;
  q: number;
  type: 'peak' | 'highpass' | 'lowpass' | 'shelf';
}

export interface EQSettings {
  bands: EQBand[];
}

export interface CompressionSettings {
  threshold: number;
  ratio: number;
  attack: number;
  release: number;
  makeup_gain: number;
}

export interface SaturationSettings {
  drive: number;
  type: 'tube' | 'tape' | 'soft';
  mix: number;
}

export interface StereoSettings {
  width: number;
  phase_correction?: boolean;
  bass_mono_freq?: number;
}

export interface LimitingSettings {
  ceiling: number;
  release: number;
}

export interface MaskingSettings {
  auto_correct: boolean;
  boost_masked_frequencies: boolean;
  sensitivity: number;
}

export interface DynamicRangeSettings {
  target_dr: number;
  auto_optimize: boolean;
  preserve_transients: boolean;
}

export interface LoudnessSettings {
  target_lufs: number;
  auto_adjust: boolean;
  genre_compliance: boolean;
}

export interface ExciterSettings {
  drive: number;
  frequency: number;
  harmonics: 'even' | 'odd' | 'both';
  mix: number;
}

export interface MasteringSettings {
  eq_settings?: EQSettings;
  compression_settings?: CompressionSettings;
  saturation_settings?: SaturationSettings;
  stereo_settings?: StereoSettings;
  limiting_settings?: LimitingSettings;
  masking_settings?: MaskingSettings;
  dynamic_range_settings?: DynamicRangeSettings;
  loudness_settings?: LoudnessSettings;
  exciter_settings?: ExciterSettings;
}

export interface MasteringSession {
  id: number;
  eq_settings?: EQSettings;
  compression_settings?: CompressionSettings;
  limiting_settings?: LimitingSettings;
  saturation_settings?: SaturationSettings;
  stereo_settings?: StereoSettings;
  ai_suggestions?: any;
  user_feedback?: string;
  processing_time?: number;
  created_at: string;
}

export interface TaskStatus {
  task_id: string;
  state: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  progress?: number;
  result?: any;
  error?: string;
  status: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  adjustments?: MasteringSettings;
  suggestions?: string[];
}

export interface UploadResponse {
  track_id: number;
  filename: string;
  analysis_task_id: string;
  status: string;
  message: string;
}

export interface MaskingAnalysis {
  critical_bands: {
    [key: string]: {
      energy_db: number;
      is_masked: boolean;
      center_freq: number;
    };
  };
  recommendations: string[];
  total_masked_bands: number;
}

export interface StereoAnalysis {
  stereo_width: number;
  correlation: number;
  balance: number;
  phase_coherence: number;
  mid_energy_db: number;
  side_energy_db: number;
  recommendations: string[];
  is_mono: boolean;
}
