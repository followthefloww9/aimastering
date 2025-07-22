import React, { useState, useRef, useEffect } from 'react';
import { useAudioStore } from '../stores/audioStore';
import { trackAPI } from '../services/api';
import { Play, Pause, Volume2, Download, RefreshCw } from 'lucide-react';
import WaveformViewer from './WaveformViewer';

const AudioPlayer: React.FC = () => {
  const { currentTrack, volume, setVolume, masteringSettings } = useAudioStore();
  const [activeVersion, setActiveVersion] = useState<'original' | 'mastered'>('original');
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [realtimeProcessing, setRealtimeProcessing] = useState(false);
  const [showDebugInfo, setShowDebugInfo] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<MediaElementAudioSourceNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const eqNodesRef = useRef<BiquadFilterNode[]>([]);
  const compressorRef = useRef<DynamicsCompressorNode | null>(null);
  const limiterRef = useRef<GainNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleDurationChange = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);
    const handleLoadedMetadata = () => setDuration(audio.duration);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('durationchange', handleDurationChange);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('durationchange', handleDurationChange);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, []);

  // Update audio volume when volume state changes
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = volume;
    }
  }, [volume]);

  // Setup Web Audio API for real-time processing
  const setupWebAudio = () => {
    const audio = audioRef.current;
    if (!audio) return;

    // Clean up existing context if it exists
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch (e) {
        console.warn('Error closing existing audio context:', e);
      }
    }

    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

      // Resume context if suspended (required by browser autoplay policies)
      if (audioContext.state === 'suspended') {
        audioContext.resume();
      }

      const source = audioContext.createMediaElementSource(audio);

      // Create EQ nodes (10-band parametric EQ)
      const eqNodes: BiquadFilterNode[] = [];
      const frequencies = [60, 120, 250, 500, 1000, 2000, 4000, 8000, 12000, 16000];
      const filterTypes = ['lowshelf', 'peaking', 'peaking', 'peaking', 'peaking', 'peaking', 'peaking', 'peaking', 'peaking', 'highshelf'];

      frequencies.forEach((freq, index) => {
        const filter = audioContext.createBiquadFilter();
        filter.type = filterTypes[index] as BiquadFilterType;
        filter.frequency.value = freq;
        filter.Q.value = index === 0 || index === frequencies.length - 1 ? 0.7 : 1.0;

        // Initialize with current mastering settings if available
        const currentBand = masteringSettings.eq_settings?.bands?.[index];
        filter.gain.value = currentBand?.gain || 0;

        console.log(`Created EQ node ${index}: ${freq}Hz, gain: ${filter.gain.value}dB`);
        eqNodes.push(filter);
      });

      // Create compressor with current settings
      const compressor = audioContext.createDynamicsCompressor();
      const compSettings = masteringSettings.compression_settings;
      compressor.threshold.value = compSettings?.threshold || -24;
      compressor.knee.value = 30;
      compressor.ratio.value = compSettings?.ratio || 3;
      compressor.attack.value = compSettings?.attack || 0.003;
      compressor.release.value = compSettings?.release || 0.25;

      console.log('Created compressor with settings:', {
        threshold: compressor.threshold.value,
        ratio: compressor.ratio.value,
        attack: compressor.attack.value,
        release: compressor.release.value
      });

      // Create limiter (using gain node with aggressive compression)
      const limiter = audioContext.createGain();
      limiter.gain.value = 1.0;

      // Create analyser for real-time monitoring
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.8;

      // Create main gain node
      const gainNode = audioContext.createGain();
      gainNode.gain.value = volume;

      // Connect audio graph: source -> EQ chain -> compressor -> limiter -> analyser -> gain -> destination
      let currentNode: AudioNode = source;

      // Connect EQ chain
      eqNodes.forEach(eqNode => {
        currentNode.connect(eqNode);
        currentNode = eqNode;
      });

      // Connect compressor -> limiter -> analyser -> gain -> destination
      currentNode.connect(compressor);
      compressor.connect(limiter);
      limiter.connect(analyser);
      analyser.connect(gainNode);
      gainNode.connect(audioContext.destination);

      // Store references
      audioContextRef.current = audioContext;
      sourceNodeRef.current = source;
      gainNodeRef.current = gainNode;
      eqNodesRef.current = eqNodes;
      compressorRef.current = compressor;
      limiterRef.current = limiter;
      analyserRef.current = analyser;

      setRealtimeProcessing(true);
      console.log('Web Audio setup complete:', {
        eqNodes: eqNodes.length,
        compressor: !!compressor,
        limiter: !!limiter,
        analyser: !!analyser,
        gain: !!gainNode,
        eqFrequencies: eqNodes.map(node => node.frequency.value),
        eqGains: eqNodes.map(node => node.gain.value)
      });

      // Apply current mastering settings
      updateRealtimeSettings();

    } catch (error) {
      console.error('Web Audio API setup failed:', error);
      setRealtimeProcessing(false);
    }
  };

  // Update real-time settings based on mastering controls
  const updateRealtimeSettings = () => {
    if (!audioContextRef.current || !realtimeProcessing) {
      console.log('Skipping real-time update:', {
        hasContext: !!audioContextRef.current,
        processing: realtimeProcessing
      });
      return;
    }

    try {
      // Update EQ (10-band)
      if (eqNodesRef.current.length > 0 && masteringSettings.eq_settings?.bands) {
        console.log('Updating EQ bands:', masteringSettings.eq_settings.bands.length);
        masteringSettings.eq_settings.bands.forEach((band, index) => {
          if (eqNodesRef.current[index]) {
            // Smoothly update parameters to avoid audio artifacts
            const currentTime = audioContextRef.current!.currentTime;
            const newGain = band.gain || 0;
            const newQ = band.q || 1.0;
            const newFreq = band.frequency;

            console.log(`EQ Band ${index}: ${newFreq}Hz, ${newGain}dB, Q${newQ}`);

            eqNodesRef.current[index].gain.setTargetAtTime(newGain, currentTime, 0.01);
            eqNodesRef.current[index].Q.setTargetAtTime(newQ, currentTime, 0.01);
            eqNodesRef.current[index].frequency.setTargetAtTime(newFreq, currentTime, 0.01);
          }
        });
      } else {
        console.log('No EQ nodes or bands available:', {
          eqNodes: eqNodesRef.current.length,
          bands: masteringSettings.eq_settings?.bands?.length
        });
      }

      // Update compressor
      if (compressorRef.current && masteringSettings.compression_settings) {
        const comp = masteringSettings.compression_settings;
        compressorRef.current.threshold.value = comp.threshold || -24;
        compressorRef.current.ratio.value = comp.ratio || 3;
        compressorRef.current.attack.value = comp.attack || 0.003;
        compressorRef.current.release.value = comp.release || 0.25;
      }

      // Update limiter (simple gain-based limiting)
      if (limiterRef.current && masteringSettings.limiting_settings) {
        const ceiling = masteringSettings.limiting_settings.ceiling || -0.3;
        // Convert dB to linear gain (simplified)
        const gainReduction = Math.pow(10, ceiling / 20);
        limiterRef.current.gain.value = Math.min(gainReduction, 1.0);
      }

    } catch (error) {
      console.warn('Error updating real-time settings:', error);
    }
  };

  // Disconnect Web Audio processing
  const disconnectWebAudio = () => {
    if (!audioContextRef.current || !sourceNodeRef.current) return;

    try {
      // Disconnect all nodes
      sourceNodeRef.current.disconnect();
      eqNodesRef.current.forEach(node => node.disconnect());
      if (compressorRef.current) compressorRef.current.disconnect();
      if (limiterRef.current) limiterRef.current.disconnect();
      if (gainNodeRef.current) gainNodeRef.current.disconnect();

      // Connect source directly to destination (bypass processing)
      sourceNodeRef.current.connect(audioContextRef.current.destination);

      setRealtimeProcessing(false);
    } catch (error) {
      console.warn('Error disconnecting Web Audio:', error);
    }
  };

  // Reconnect Web Audio processing
  const reconnectWebAudio = () => {
    if (!audioContextRef.current || !sourceNodeRef.current) {
      setupWebAudio();
      return;
    }

    try {
      // Disconnect direct connection
      sourceNodeRef.current.disconnect();

      // Reconnect through processing chain
      let currentNode: AudioNode = sourceNodeRef.current;

      // Connect EQ chain
      eqNodesRef.current.forEach(eqNode => {
        currentNode.connect(eqNode);
        currentNode = eqNode;
      });

      // Connect compressor -> limiter -> analyser -> gain -> destination
      if (compressorRef.current && limiterRef.current && analyserRef.current && gainNodeRef.current) {
        currentNode.connect(compressorRef.current);
        compressorRef.current.connect(limiterRef.current);
        limiterRef.current.connect(analyserRef.current);
        analyserRef.current.connect(gainNodeRef.current);
        gainNodeRef.current.connect(audioContextRef.current.destination);
      }

      setRealtimeProcessing(true);
      updateRealtimeSettings();
    } catch (error) {
      console.warn('Error reconnecting Web Audio:', error);
      // Fallback to full setup
      setupWebAudio();
    }
  };

  // Toggle real-time processing
  const toggleRealtimeProcessing = () => {
    console.log('Toggling real-time FX:', !realtimeProcessing);
    if (realtimeProcessing) {
      console.log('Disconnecting Web Audio...');
      disconnectWebAudio();
    } else {
      console.log('Reconnecting Web Audio...');
      reconnectWebAudio();
      // Force update settings after reconnection
      setTimeout(() => {
        console.log('Force updating settings after reconnection...');
        updateRealtimeSettings();
      }, 100);
    }
  };

  // Update real-time settings when mastering settings change
  useEffect(() => {
    console.log('Mastering settings changed, updating real-time FX:', {
      processing: realtimeProcessing,
      eqBands: masteringSettings.eq_settings?.bands?.length,
      hasCompression: !!masteringSettings.compression_settings,
      hasLimiting: !!masteringSettings.limiting_settings
    });
    updateRealtimeSettings();
  }, [masteringSettings, realtimeProcessing]);

  // Force update real-time settings when user adjusts controls
  const forceUpdateRealtimeSettings = () => {
    console.log('Force updating real-time settings...');
    updateRealtimeSettings();
  };

  // Listen for force update events from mastering controls
  useEffect(() => {
    const handleForceUpdate = () => {
      console.log('Received force update event');
      forceUpdateRealtimeSettings();
    };

    window.addEventListener('forceRealtimeUpdate', handleForceUpdate);
    return () => window.removeEventListener('forceRealtimeUpdate', handleForceUpdate);
  }, []);

  if (!currentTrack) return null;

  const handlePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      // Setup Web Audio API on first play if not already setup
      if (!audioContextRef.current) {
        setupWebAudio();
      } else if (audioContextRef.current.state === 'suspended') {
        // Resume audio context if suspended (required by browser autoplay policies)
        audioContextRef.current.resume();
      }
      audio.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (time: number) => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.currentTime = time;
    setCurrentTime(time);
  };

  const handleVolumeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(event.target.value);
    setVolume(newVolume);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleDownload = (version: 'original' | 'mastered') => {
    if (version === 'original') {
      const url = trackAPI.downloadOriginal(currentTrack.id);
      window.open(url, '_blank');
    } else if (currentTrack.is_processed) {
      const url = trackAPI.downloadMastered(currentTrack.id);
      window.open(url, '_blank');
    }
  };

  return (
    <div className="glass rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Audio Player</h2>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveVersion('original')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeVersion === 'original'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Original
            </button>

            <button
              onClick={() => setActiveVersion('mastered')}
              disabled={!currentTrack.is_processed}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeVersion === 'mastered' && currentTrack.is_processed
                  ? 'bg-accent-600 text-white'
                  : currentTrack.is_processed
                  ? 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  : 'bg-gray-800 text-gray-500 cursor-not-allowed'
              }`}
            >
              Mastered
              {!currentTrack.is_processed && (
                <span className="ml-2 text-xs">(Not Available)</span>
              )}
            </button>
          </div>

          {/* Real-time Processing Toggle */}
          <div className="flex items-center space-x-2 text-sm">
            <span className="text-gray-400">Real-time FX:</span>
            <button
              onClick={toggleRealtimeProcessing}
              className={`w-10 h-5 rounded-full transition-all duration-200 cursor-pointer ${
                realtimeProcessing ? 'bg-green-600 shadow-green-400/50 shadow-lg' : 'bg-gray-600 hover:bg-gray-500'
              }`}
              title={realtimeProcessing ? 'Click to disable real-time processing' : 'Click to enable real-time processing'}
            >
              <div className={`w-4 h-4 bg-white rounded-full transition-all duration-200 transform ${
                realtimeProcessing ? 'translate-x-5 shadow-md' : 'translate-x-0.5'
              } mt-0.5`} />
            </button>
            <span className={`text-xs font-medium ${realtimeProcessing ? 'text-green-400' : 'text-gray-500'}`}>
              {realtimeProcessing ? 'ON' : 'OFF'}
            </span>
            {audioContextRef.current && (
              <span className="text-xs text-blue-400">
                ({audioContextRef.current.state})
              </span>
            )}
            <button
              onClick={() => setShowDebugInfo(!showDebugInfo)}
              className="text-xs text-gray-400 hover:text-white"
            >
              Debug
            </button>
          </div>

          {/* Debug Panel */}
          {showDebugInfo && realtimeProcessing && (
            <div className="mt-4 p-3 bg-gray-900 rounded-lg text-xs">
              <h4 className="text-white font-medium mb-2">Real-time FX Debug</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-gray-400 mb-1">EQ Bands Active:</p>
                  {eqNodesRef.current.map((node, index) => (
                    <div key={index} className="text-green-400">
                      {node.frequency.value}Hz: {node.gain.value.toFixed(1)}dB
                    </div>
                  ))}
                </div>
                <div>
                  <p className="text-gray-400 mb-1">Compressor:</p>
                  {compressorRef.current && (
                    <div className="text-blue-400">
                      Threshold: {compressorRef.current.threshold.value.toFixed(1)}dB<br/>
                      Ratio: {compressorRef.current.ratio.value.toFixed(1)}:1<br/>
                      Reduction: {compressorRef.current.reduction.toFixed(1)}dB
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        src={activeVersion === 'original'
          ? trackAPI.downloadOriginal(currentTrack.id)
          : currentTrack.is_processed
            ? trackAPI.downloadMastered(currentTrack.id)
            : trackAPI.downloadOriginal(currentTrack.id)
        }
        preload="metadata"
      />

      {/* Waveform and Controls */}
      <div className="space-y-4">
        {/* Waveform Viewer */}
        <div className="bg-gray-800 rounded-lg p-4">
          <WaveformViewer
            currentTime={currentTime}
            duration={duration}
            onSeek={handleSeek}
          />
        </div>

        {/* Transport Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={handlePlayPause}
              className="flex items-center justify-center w-12 h-12 bg-primary-600 hover:bg-primary-700 text-white rounded-full transition-colors"
            >
              {isPlaying ? (
                <Pause className="w-6 h-6" />
              ) : (
                <Play className="w-6 h-6 ml-1" />
              )}
            </button>

            <div className="text-sm text-gray-400">
              {formatTime(currentTime)} / {formatTime(duration)}
            </div>
          </div>

          {/* Volume Control */}
          <div className="flex items-center space-x-3">
            <Volume2 className="w-5 h-5 text-gray-400" />
            <div className="w-24">
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={volume}
                onChange={handleVolumeChange}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>
            <span className="text-xs text-gray-400 w-8">
              {Math.round(volume * 100)}%
            </span>
          </div>
        </div>

        {/* Download Buttons */}
        <div className="flex items-center space-x-4">
          <button
            onClick={() => handleDownload('original')}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Download Original</span>
          </button>
          
          {currentTrack.is_processed && (
            <button
              onClick={() => handleDownload('mastered')}
              className="flex items-center space-x-2 px-4 py-2 bg-accent-600 hover:bg-accent-700 text-white rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Download Mastered</span>
            </button>
          )}
        </div>

        {/* A/B Comparison */}
        {currentTrack.is_processed && (
          <div className="border-t border-gray-600 pt-4">
            <h3 className="text-lg font-medium text-white mb-3">A/B Comparison</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="font-medium text-white mb-2">Original</h4>
                <audio
                  controls
                  className="w-full"
                  src={trackAPI.downloadOriginal(currentTrack.id)}
                  preload="metadata"
                >
                  Your browser does not support the audio element.
                </audio>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="font-medium text-white mb-2">Mastered</h4>
                <audio
                  controls
                  className="w-full"
                  src={trackAPI.downloadMastered(currentTrack.id)}
                  preload="metadata"
                >
                  Your browser does not support the audio element.
                </audio>
              </div>
            </div>
          </div>
        )}

        {/* Track Info */}
        <div className="border-t border-gray-600 pt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Duration:</span>
              <div className="text-white font-medium">
                {currentTrack.duration ? `${Math.round(currentTrack.duration)}s` : 'Unknown'}
              </div>
            </div>
            
            <div>
              <span className="text-gray-400">Sample Rate:</span>
              <div className="text-white font-medium">
                {currentTrack.sample_rate ? `${currentTrack.sample_rate}Hz` : 'Unknown'}
              </div>
            </div>
            
            <div>
              <span className="text-gray-400">Channels:</span>
              <div className="text-white font-medium">
                {currentTrack.channels || 'Unknown'}
              </div>
            </div>
            
            <div>
              <span className="text-gray-400">Status:</span>
              <div className="flex items-center space-x-2">
                {currentTrack.is_analyzed && (
                  <span className="px-2 py-1 bg-green-600 text-white text-xs rounded">
                    Analyzed
                  </span>
                )}
                {currentTrack.is_processed && (
                  <span className="px-2 py-1 bg-accent-600 text-white text-xs rounded">
                    Mastered
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Custom CSS for slider */}
      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: 2px solid #1f2937;
        }
        
        .slider::-moz-range-thumb {
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: 2px solid #1f2937;
        }
      `}</style>
    </div>
  );
};

export default AudioPlayer;
