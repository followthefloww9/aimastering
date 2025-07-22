import React, { useState } from 'react';
import { useAudioStore } from '../stores/audioStore';
import { trackAPI, taskAPI } from '../services/api';
import { Sliders, Zap, Play, Settings } from 'lucide-react';
import toast from 'react-hot-toast';

const MasteringControls: React.FC = () => {
  const { 
    currentTrack, 
    masteringSettings, 
    updateMasteringSettings,
    isProcessing,
    setIsProcessing,
    processingProgress,
    setProcessingProgress,
    addTask,
    updateTrack
  } = useAudioStore();
  
  const [activeTab, setActiveTab] = useState<'eq' | 'compression' | 'saturation' | 'stereo' | 'limiting' | 'masking' | 'dynamics' | 'loudness' | 'exciter'>('eq');

  if (!currentTrack || !currentTrack.is_analyzed) {
    return (
      <div className="glass rounded-xl p-6">
        <div className="text-center text-gray-400">
          <Sliders className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Track must be analyzed before mastering</p>
        </div>
      </div>
    );
  }

  const handleApplyMastering = async () => {
    if (!currentTrack) return;

    setIsProcessing(true);
    setProcessingProgress(0);

    try {
      const response = await trackAPI.master(currentTrack.id, masteringSettings);
      const taskId = response.mastering_task_id;
      
      addTask(taskId, {
        task_id: taskId,
        state: 'PENDING',
        status: 'Starting mastering...'
      });

      // Poll task status
      const pollInterval = setInterval(async () => {
        try {
          const taskStatus = await taskAPI.getStatus(taskId);
          
          if (taskStatus.state === 'PROGRESS') {
            setProcessingProgress(taskStatus.progress || 0);
          } else if (taskStatus.state === 'SUCCESS') {
            // Mastering completed
            updateTrack({ is_processed: true });
            setIsProcessing(false);
            setProcessingProgress(100);
            clearInterval(pollInterval);
            toast.success('Mastering completed successfully!');
          } else if (taskStatus.state === 'FAILURE') {
            setIsProcessing(false);
            clearInterval(pollInterval);
            toast.error(`Mastering failed: ${taskStatus.error}`);
          }
        } catch (error) {
          console.error('Error polling task status:', error);
        }
      }, 2000);

      toast.success('Mastering started!');
      
    } catch (error: any) {
      setIsProcessing(false);
      toast.error(error.response?.data?.detail || 'Mastering failed');
    }
  };

  const handleLoadPreset = async (genre: string) => {
    if (!currentTrack) return;

    try {
      const response = await trackAPI.getPreset(currentTrack.id, genre);
      updateMasteringSettings(response.preset);
      toast.success(`${genre} preset loaded`);
    } catch (error) {
      toast.error('Failed to load preset');
    }
  };

  const updateEQBand = (index: number, field: string, value: number) => {
    const newBands = [...(masteringSettings.eq_settings?.bands || [])];
    newBands[index] = { ...newBands[index], [field]: value };
    updateMasteringSettings({
      eq_settings: { bands: newBands }
    });

    // Force trigger real-time update
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('forceRealtimeUpdate'));
    }, 50);
  };

  const updateCompression = (field: string, value: number) => {
    updateMasteringSettings({
      compression_settings: {
        ...masteringSettings.compression_settings,
        [field]: value
      }
    });

    // Force trigger real-time update
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('forceRealtimeUpdate'));
    }, 50);
  };

  const updateSaturation = (field: string, value: number | string) => {
    updateMasteringSettings({
      saturation_settings: {
        ...masteringSettings.saturation_settings,
        [field]: value
      }
    });
  };

  const updateStereo = (field: string, value: number) => {
    updateMasteringSettings({
      stereo_settings: {
        ...masteringSettings.stereo_settings,
        [field]: value
      }
    });
  };

  const updateLimiting = (field: string, value: number) => {
    updateMasteringSettings({
      limiting_settings: {
        ...masteringSettings.limiting_settings,
        [field]: value
      }
    });
  };

  return (
    <div className="glass rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white flex items-center">
          <Sliders className="w-6 h-6 mr-2 text-primary-400" />
          Mastering Controls
        </h2>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleLoadPreset('rock')}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
          >
            Rock
          </button>
          <button
            onClick={() => handleLoadPreset('electronic')}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
          >
            Electronic
          </button>
          <button
            onClick={() => handleLoadPreset('jazz')}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
          >
            Jazz
          </button>
        </div>
      </div>

      {/* Tab Navigation - Fixed Layout */}
      <div className="mb-6 w-full">
        <div className="bg-gray-800 p-4 rounded-lg w-full max-w-none">
          {/* Simple 3x3 Grid Layout - Force full width */}
          <div className="grid grid-cols-3 gap-3 w-full">
            {/* Row 1 */}
            <button
              onClick={() => setActiveTab('eq')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'eq'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Sliders className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">EQ</span>
            </button>

            <button
              onClick={() => setActiveTab('compression')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'compression'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">Compression</span>
            </button>

            <button
              onClick={() => setActiveTab('saturation')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'saturation'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Settings className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">Saturation</span>
            </button>

            {/* Row 2 */}
            <button
              onClick={() => setActiveTab('stereo')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'stereo'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Play className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">Stereo</span>
            </button>

            <button
              onClick={() => setActiveTab('limiting')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'limiting'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Settings className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">Limiting</span>
            </button>

            <button
              onClick={() => setActiveTab('masking')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'masking'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Sliders className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">Masking</span>
            </button>

            {/* Row 3 */}
            <button
              onClick={() => setActiveTab('dynamics')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'dynamics'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">Dynamics</span>
            </button>

            <button
              onClick={() => setActiveTab('loudness')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'loudness'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Settings className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">LUFS</span>
            </button>

            <button
              onClick={() => setActiveTab('exciter')}
              className={`flex flex-col items-center justify-center py-3 px-2 rounded-md transition-colors min-h-[70px] ${
                activeTab === 'exciter'
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Zap className="w-5 h-5 mb-2" />
              <span className="text-sm font-medium">Exciter</span>
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="space-y-4">
        {activeTab === 'eq' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Equalizer</h3>
            <div className="grid grid-cols-2 md:grid-cols-5 lg:grid-cols-10 gap-3">
              {masteringSettings.eq_settings?.bands.map((band, index) => (
                <div key={index} className="space-y-2">
                  <div className="text-center">
                    <span className="text-sm text-gray-400">{band.frequency}Hz</span>
                  </div>
                  <div className="flex flex-col items-center space-y-2">
                    <input
                      type="range"
                      min="-12"
                      max="12"
                      step="0.1"
                      value={band.gain}
                      onChange={(e) => updateEQBand(index, 'gain', parseFloat(e.target.value))}
                      className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                      style={{ writingMode: 'bt-lr' }}
                    />
                    <span className="text-xs text-white">{band.gain.toFixed(1)}dB</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'compression' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Compression</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Threshold</label>
                <input
                  type="range"
                  min="-30"
                  max="0"
                  step="0.1"
                  value={masteringSettings.compression_settings?.threshold || -12}
                  onChange={(e) => updateCompression('threshold', parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-xs text-white">
                  {(masteringSettings.compression_settings?.threshold || -12).toFixed(1)}dB
                </span>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Ratio</label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  step="0.1"
                  value={masteringSettings.compression_settings?.ratio || 3}
                  onChange={(e) => updateCompression('ratio', parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-xs text-white">
                  {(masteringSettings.compression_settings?.ratio || 3).toFixed(1)}:1
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'saturation' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Saturation</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Drive</label>
                <input
                  type="range"
                  min="1"
                  max="3"
                  step="0.1"
                  value={masteringSettings.saturation_settings?.drive || 1}
                  onChange={(e) => updateSaturation('drive', parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-xs text-white">
                  {(masteringSettings.saturation_settings?.drive || 1).toFixed(1)}
                </span>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-2">Type</label>
                <select
                  value={masteringSettings.saturation_settings?.type || 'tube'}
                  onChange={(e) => updateSaturation('type', e.target.value)}
                  className="w-full bg-gray-700 text-white rounded-lg px-3 py-2"
                >
                  <option value="tube">Tube</option>
                  <option value="tape">Tape</option>
                  <option value="soft">Soft</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'stereo' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Advanced Stereo Processing</h3>
            {currentTrack?.stereo_analysis && (
              <div className="bg-purple-900/30 border border-purple-500/30 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-purple-300 mb-2">
                  🎵 Stereo Analysis: Width {currentTrack.stereo_analysis.stereo_width.toFixed(2)} | Correlation {currentTrack.stereo_analysis.correlation.toFixed(2)}
                </h4>
                <div className="text-xs text-purple-200 space-y-1">
                  {currentTrack.stereo_analysis.recommendations?.slice(0, 2).map((rec: string, idx: number) => (
                    <p key={idx}>• {rec}</p>
                  ))}
                </div>
              </div>
            )}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Stereo Width: {(masteringSettings.stereo_settings?.width || 1).toFixed(1)}</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={masteringSettings.stereo_settings?.width || 1}
                onChange={(e) => updateStereo('width', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Phase Correction</label>
              <input
                type="checkbox"
                checked={masteringSettings.stereo_settings?.phase_correction || false}
                onChange={(e) => updateMasteringSettings({
                  stereo_settings: { ...masteringSettings.stereo_settings, phase_correction: e.target.checked }
                })}
                className="w-4 h-4 text-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Bass Mono: {(masteringSettings.stereo_settings?.bass_mono_freq || 120)}Hz</label>
              <input
                type="range"
                min="60"
                max="200"
                step="10"
                value={masteringSettings.stereo_settings?.bass_mono_freq || 120}
                onChange={(e) => updateMasteringSettings({
                  stereo_settings: { ...masteringSettings.stereo_settings, bass_mono_freq: parseFloat(e.target.value) }
                })}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
        )}

        {activeTab === 'limiting' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Limiting</h3>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Ceiling</label>
              <input
                type="range"
                min="-3"
                max="0"
                step="0.1"
                value={masteringSettings.limiting_settings?.ceiling || -0.3}
                onChange={(e) => updateLimiting('ceiling', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
              <span className="text-xs text-white">
                {(masteringSettings.limiting_settings?.ceiling || -0.3).toFixed(1)}dB
              </span>
            </div>
          </div>
        )}

        {activeTab === 'masking' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Frequency Masking Correction</h3>
            {currentTrack?.masking_analysis && (
              <div className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-blue-300 mb-2">
                  🎵 Masking Analysis: {currentTrack.masking_analysis.total_masked_bands} bands need attention
                </h4>
                <div className="text-xs text-blue-200 space-y-1">
                  {currentTrack.masking_analysis.recommendations?.slice(0, 3).map((rec: string, idx: number) => (
                    <p key={idx}>• {rec}</p>
                  ))}
                </div>
              </div>
            )}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Auto-Correct Masked Frequencies</label>
              <input
                type="checkbox"
                checked={masteringSettings.masking_settings?.auto_correct || false}
                onChange={(e) => updateMasteringSettings({
                  masking_settings: { ...masteringSettings.masking_settings, auto_correct: e.target.checked }
                })}
                className="w-4 h-4 text-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Sensitivity: {((masteringSettings.masking_settings?.sensitivity || 0.8) * 100).toFixed(0)}%</label>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={masteringSettings.masking_settings?.sensitivity || 0.8}
                onChange={(e) => updateMasteringSettings({
                  masking_settings: { ...masteringSettings.masking_settings, sensitivity: parseFloat(e.target.value) }
                })}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
        )}

        {activeTab === 'dynamics' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Dynamic Range Optimization</h3>
            {currentTrack?.loudness && (
              <div className="bg-purple-900/30 border border-purple-500/30 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-purple-300 mb-2">
                  📊 Current DR: {currentTrack.loudness.dynamic_range?.toFixed(1)}dB
                </h4>
                <p className="text-xs text-purple-200">
                  Genre target: {currentTrack.predicted_genre === 'jazz' ? '14.0' :
                                currentTrack.predicted_genre === 'classical' ? '20.0' :
                                currentTrack.predicted_genre === 'hip-hop' ? '4.0' : '8.0'}dB
                </p>
              </div>
            )}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Target Dynamic Range: {masteringSettings.dynamic_range_settings?.target_dr || 12}dB</label>
              <input
                type="range"
                min="3"
                max="20"
                step="0.5"
                value={masteringSettings.dynamic_range_settings?.target_dr || 12}
                onChange={(e) => updateMasteringSettings({
                  dynamic_range_settings: { ...masteringSettings.dynamic_range_settings, target_dr: parseFloat(e.target.value) }
                })}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Auto-Optimize for Genre</label>
              <input
                type="checkbox"
                checked={masteringSettings.dynamic_range_settings?.auto_optimize || false}
                onChange={(e) => updateMasteringSettings({
                  dynamic_range_settings: { ...masteringSettings.dynamic_range_settings, auto_optimize: e.target.checked }
                })}
                className="w-4 h-4 text-primary-500"
              />
            </div>
          </div>
        )}

        {activeTab === 'loudness' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">LUFS Loudness Standards</h3>
            {currentTrack?.loudness && (
              <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-green-300 mb-2">
                  🔊 Current LUFS: {currentTrack.loudness.lufs_integrated?.toFixed(1)}dB
                </h4>
                <p className="text-xs text-green-200">
                  {currentTrack.predicted_genre} target: {
                    currentTrack.predicted_genre === 'jazz' ? '-18.0' :
                    currentTrack.predicted_genre === 'classical' ? '-23.0' :
                    currentTrack.predicted_genre === 'hip-hop' ? '-10.0' :
                    currentTrack.predicted_genre === 'electronic' ? '-12.0' : '-14.0'
                  } LUFS
                </p>
              </div>
            )}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Target LUFS: {masteringSettings.loudness_settings?.target_lufs || -14}dB</label>
              <input
                type="range"
                min="-30"
                max="-6"
                step="0.5"
                value={masteringSettings.loudness_settings?.target_lufs || -14}
                onChange={(e) => updateMasteringSettings({
                  loudness_settings: { ...masteringSettings.loudness_settings, target_lufs: parseFloat(e.target.value) }
                })}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Genre Compliance</label>
              <input
                type="checkbox"
                checked={masteringSettings.loudness_settings?.genre_compliance || false}
                onChange={(e) => updateMasteringSettings({
                  loudness_settings: { ...masteringSettings.loudness_settings, genre_compliance: e.target.checked }
                })}
                className="w-4 h-4 text-primary-500"
              />
            </div>
          </div>
        )}

        {activeTab === 'exciter' && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Harmonic Exciter</h3>
            <div className="bg-orange-900/30 border border-orange-500/30 rounded-lg p-4 mb-4">
              <h4 className="text-sm font-medium text-orange-300 mb-2">
                🎵 Harmonic Enhancement
              </h4>
              <p className="text-xs text-orange-200">
                Add harmonic richness and presence to your track
              </p>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Drive: {(masteringSettings.exciter_settings?.drive || 0).toFixed(1)}dB</label>
              <input
                type="range"
                min="0"
                max="10"
                step="0.5"
                value={masteringSettings.exciter_settings?.drive || 0}
                onChange={(e) => updateMasteringSettings({
                  exciter_settings: { ...masteringSettings.exciter_settings, drive: parseFloat(e.target.value) }
                })}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Frequency: {masteringSettings.exciter_settings?.frequency || 3000}Hz</label>
              <input
                type="range"
                min="1000"
                max="8000"
                step="100"
                value={masteringSettings.exciter_settings?.frequency || 3000}
                onChange={(e) => updateMasteringSettings({
                  exciter_settings: { ...masteringSettings.exciter_settings, frequency: parseFloat(e.target.value) }
                })}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Harmonics</label>
              <select
                value={masteringSettings.exciter_settings?.harmonics || 'even'}
                onChange={(e) => updateMasteringSettings({
                  exciter_settings: { ...masteringSettings.exciter_settings, harmonics: e.target.value }
                })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="even">Even Harmonics</option>
                <option value="odd">Odd Harmonics</option>
                <option value="both">Both</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Mix: {((masteringSettings.exciter_settings?.mix || 0.3) * 100).toFixed(0)}%</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={masteringSettings.exciter_settings?.mix || 0.3}
                onChange={(e) => updateMasteringSettings({
                  exciter_settings: { ...masteringSettings.exciter_settings, mix: parseFloat(e.target.value) }
                })}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
        )}
      </div>

      {/* Workflow Info */}
      <div className="mt-6 pt-6 border-t border-gray-600">
        <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-4 mb-4">
          <h3 className="text-sm font-medium text-green-300 mb-2">🤖 AI Suggestions Applied!</h3>
          <div className="text-xs text-green-200 space-y-1">
            <p>✅ AI has analyzed your track and applied optimal settings</p>
            <p>• <strong>Adjust controls above</strong> or use AI chat to modify</p>
            <p>• <strong>Click "Apply Mastering"</strong> to process with current settings</p>
            <p>• <strong>Download</strong> your professionally mastered track</p>
          </div>
        </div>

        <button
          onClick={handleApplyMastering}
          disabled={isProcessing}
          className={`w-full py-3 px-6 rounded-lg font-medium transition-all ${
            isProcessing
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-primary-500 to-accent-500 hover:from-primary-600 hover:to-accent-600 text-white'
          }`}
        >
          {isProcessing ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Processing... {Math.round(processingProgress)}%</span>
            </div>
          ) : (
            'Apply Mastering'
          )}
        </button>
      </div>
    </div>
  );
};

export default MasteringControls;
