import React from 'react';
import { useAudioStore } from '../stores/audioStore';
import { BarChart3, Music, Volume2, Zap } from 'lucide-react';

const TrackAnalysis: React.FC = () => {
  const { currentTrack, isAnalyzing, analysisProgress } = useAudioStore();

  if (!currentTrack) return null;

  if (isAnalyzing) {
    return (
      <div className="glass rounded-xl p-6">
        <div className="flex items-center space-x-3 mb-4">
          <BarChart3 className="w-6 h-6 text-primary-400" />
          <h2 className="text-xl font-semibold text-white">Analyzing Track</h2>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-gray-300">
              AI is analyzing your track... {Math.round(analysisProgress)}%
            </span>
          </div>
          
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-primary-500 to-accent-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${analysisProgress}%` }}
            />
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-400">
            <div className={analysisProgress > 20 ? 'text-green-400' : ''}>
              ✓ Audio Properties
            </div>
            <div className={analysisProgress > 40 ? 'text-green-400' : ''}>
              ✓ Frequency Analysis
            </div>
            <div className={analysisProgress > 70 ? 'text-green-400' : ''}>
              ✓ Genre Detection
            </div>
            <div className={analysisProgress > 90 ? 'text-green-400' : ''}>
              ✓ AI Suggestions
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!currentTrack.is_analyzed) {
    return (
      <div className="glass rounded-xl p-6">
        <div className="text-center text-gray-400">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Track analysis not available</p>
        </div>
      </div>
    );
  }

  const { loudness, frequency_analysis, spectral_features } = currentTrack;

  return (
    <div className="glass rounded-xl p-6">
      <div className="flex items-center space-x-3 mb-6">
        <BarChart3 className="w-6 h-6 text-primary-400" />
        <h2 className="text-xl font-semibold text-white">Track Analysis</h2>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Basic Info */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-white flex items-center">
            <Music className="w-5 h-5 mr-2 text-primary-400" />
            Basic Info
          </h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Duration:</span>
              <span className="text-white">{Math.round(currentTrack.duration || 0)}s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Sample Rate:</span>
              <span className="text-white">{currentTrack.sample_rate}Hz</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Channels:</span>
              <span className="text-white">
                {currentTrack.channels === 1 ? 'Mono' : currentTrack.channels === 2 ? 'Stereo' : `${currentTrack.channels} Channels`}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Tempo:</span>
              <span className="text-white">{Math.round(currentTrack.tempo || 0)} BPM</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Key:</span>
              <span className="text-white">{currentTrack.key}</span>
            </div>
          </div>
        </div>

        {/* Genre & Confidence */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-white flex items-center">
            <Zap className="w-5 h-5 mr-2 text-accent-400" />
            AI Detection
          </h3>
          
          <div className="space-y-3">
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-gray-400 text-sm">Genre:</span>
                <span className="text-white font-medium capitalize">
                  {currentTrack.predicted_genre}
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-accent-500 to-accent-400 h-2 rounded-full"
                  style={{ width: `${(currentTrack.genre_confidence || 0) * 100}%` }}
                />
              </div>
              <span className="text-xs text-gray-500">
                {Math.round((currentTrack.genre_confidence || 0) * 100)}% confidence
              </span>
            </div>
          </div>
        </div>

        {/* Loudness */}
        {loudness && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white flex items-center">
              <Volume2 className="w-5 h-5 mr-2 text-yellow-400" />
              Loudness
            </h3>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">RMS:</span>
                <span className="text-white">{loudness.rms_db.toFixed(1)} dB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Peak:</span>
                <span className="text-white">{loudness.peak_db.toFixed(1)} dB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">LUFS:</span>
                <span className="text-white">{loudness.lufs_approx.toFixed(1)} LUFS</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Dynamic Range:</span>
                <span className="text-white">{loudness.dynamic_range.toFixed(1)} dB</span>
              </div>
            </div>
          </div>
        )}

        {/* Frequency Bands */}
        {frequency_analysis && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Frequency Balance</h3>
            
            <div className="space-y-2">
              {Object.entries(frequency_analysis.frequency_bands).map(([band, energy]) => {
                const normalizedEnergy = Math.min(energy / 1000, 1); // Normalize for display
                const suggestion = frequency_analysis.spectral_balance?.[band as keyof typeof frequency_analysis.spectral_balance];
                
                return (
                  <div key={band} className="space-y-1">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gray-400 capitalize">
                        {band.replace('_', ' ')}
                      </span>
                      <span className={`text-xs px-1 rounded ${
                        suggestion === 'boost' ? 'bg-green-600 text-white' :
                        suggestion === 'cut' ? 'bg-red-600 text-white' :
                        'bg-gray-600 text-gray-300'
                      }`}>
                        {suggestion}
                      </span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-1.5">
                      <div 
                        className="bg-gradient-to-r from-primary-500 to-accent-500 h-1.5 rounded-full"
                        style={{ width: `${normalizedEnergy * 100}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrackAnalysis;
