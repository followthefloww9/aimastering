import { create } from 'zustand';
import { Track, MasteringSettings, ChatMessage, TaskStatus } from '../types';

interface AudioState {
  // Current track
  currentTrack: Track | null;
  
  // Mastering settings
  masteringSettings: MasteringSettings;
  
  // Chat messages
  chatMessages: ChatMessage[];
  
  // UI state
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  
  // Processing state
  isAnalyzing: boolean;
  isProcessing: boolean;
  analysisProgress: number;
  processingProgress: number;
  
  // Task tracking
  activeTasks: Map<string, TaskStatus>;
  
  // Actions
  setCurrentTrack: (track: Track | null) => void;
  updateTrack: (updates: Partial<Track>) => void;
  setMasteringSettings: (settings: MasteringSettings) => void;
  updateMasteringSettings: (updates: Partial<MasteringSettings>) => void;
  addChatMessage: (message: ChatMessage) => void;
  clearChatMessages: () => void;
  setIsPlaying: (playing: boolean) => void;
  setCurrentTime: (time: number) => void;
  setDuration: (duration: number) => void;
  setVolume: (volume: number) => void;
  setIsAnalyzing: (analyzing: boolean) => void;
  setIsProcessing: (processing: boolean) => void;
  setAnalysisProgress: (progress: number) => void;
  setProcessingProgress: (progress: number) => void;
  addTask: (taskId: string, status: TaskStatus) => void;
  updateTask: (taskId: string, status: TaskStatus) => void;
  removeTask: (taskId: string) => void;
  reset: () => void;
}

const defaultMasteringSettings: MasteringSettings = {
  eq_settings: {
    bands: [
      { frequency: 60, gain: 0, q: 0.7, type: 'low_shelf' },
      { frequency: 120, gain: 0, q: 1.0, type: 'peak' },
      { frequency: 250, gain: 0, q: 1.0, type: 'peak' },
      { frequency: 500, gain: 0, q: 1.0, type: 'peak' },
      { frequency: 1000, gain: 0, q: 1.0, type: 'peak' },
      { frequency: 2000, gain: 0, q: 1.0, type: 'peak' },
      { frequency: 4000, gain: 0, q: 1.0, type: 'peak' },
      { frequency: 8000, gain: 0, q: 1.0, type: 'peak' },
      { frequency: 12000, gain: 0, q: 1.0, type: 'peak' },
      { frequency: 16000, gain: 0, q: 0.7, type: 'high_shelf' },
    ],
  },
  compression_settings: {
    threshold: -12,
    ratio: 3.0,
    attack: 0.003,
    release: 0.1,
    makeup_gain: 0,
  },
  saturation_settings: {
    drive: 1.0,
    type: 'tube',
    mix: 0.0,
  },
  stereo_settings: {
    width: 1.0,
    phase_correction: false,
    bass_mono_freq: 120,
  },
  limiting_settings: {
    ceiling: -0.3,
    release: 0.05,
  },
  // Advanced settings
  masking_settings: {
    auto_correct: true,
    boost_masked_frequencies: true,
    sensitivity: 0.8,
  },
  dynamic_range_settings: {
    target_dr: 12.0,
    auto_optimize: true,
    preserve_transients: true,
  },
  loudness_settings: {
    target_lufs: -14.0,
    auto_adjust: true,
    genre_compliance: true,
  },
  exciter_settings: {
    drive: 0.0,
    frequency: 3000,
    harmonics: 'even' as const,
    mix: 0.3,
  },
};

export const useAudioStore = create<AudioState>((set, get) => ({
  // Initial state
  currentTrack: null,
  masteringSettings: defaultMasteringSettings,
  chatMessages: [],
  isPlaying: false,
  currentTime: 0,
  duration: 0,
  volume: 0.8,
  isAnalyzing: false,
  isProcessing: false,
  analysisProgress: 0,
  processingProgress: 0,
  activeTasks: new Map(),

  // Actions
  setCurrentTrack: (track) => set((state) => {
    // Reset to default 10-band EQ when loading a new track
    const resetSettings = track ? defaultMasteringSettings : state.masteringSettings;
    return {
      currentTrack: track,
      masteringSettings: resetSettings
    };
  }),
  
  updateTrack: (updates) => set((state) => ({
    currentTrack: state.currentTrack ? { ...state.currentTrack, ...updates } : null,
  })),
  
  setMasteringSettings: (settings) => set({ masteringSettings: settings }),
  
  updateMasteringSettings: (updates) => set((state) => {
    const newSettings = { ...state.masteringSettings, ...updates };

    // Ensure we always have 10 EQ bands
    if (newSettings.eq_settings?.bands && newSettings.eq_settings.bands.length < 10) {
      const defaultBands = defaultMasteringSettings.eq_settings.bands;
      newSettings.eq_settings.bands = defaultBands;
    }

    return { masteringSettings: newSettings };
  }),
  
  addChatMessage: (message) => set((state) => ({
    chatMessages: [...state.chatMessages, message],
  })),
  
  clearChatMessages: () => set({ chatMessages: [] }),
  
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  
  setCurrentTime: (time) => set({ currentTime: time }),
  
  setDuration: (duration) => set({ duration }),
  
  setVolume: (volume) => set({ volume }),
  
  setIsAnalyzing: (analyzing) => set({ isAnalyzing: analyzing }),
  
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  
  setAnalysisProgress: (progress) => set({ analysisProgress: progress }),
  
  setProcessingProgress: (progress) => set({ processingProgress: progress }),
  
  addTask: (taskId, status) => set((state) => ({
    activeTasks: new Map(state.activeTasks).set(taskId, status),
  })),
  
  updateTask: (taskId, status) => set((state) => {
    const newTasks = new Map(state.activeTasks);
    newTasks.set(taskId, status);
    return { activeTasks: newTasks };
  }),
  
  removeTask: (taskId) => set((state) => {
    const newTasks = new Map(state.activeTasks);
    newTasks.delete(taskId);
    return { activeTasks: newTasks };
  }),
  
  reset: () => set({
    currentTrack: null,
    masteringSettings: defaultMasteringSettings,
    chatMessages: [],
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    isAnalyzing: false,
    isProcessing: false,
    analysisProgress: 0,
    processingProgress: 0,
    activeTasks: new Map(),
  }),
}));
