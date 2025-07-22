import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Music, AlertCircle } from 'lucide-react';
import { useAudioStore } from '../stores/audioStore';
import { trackAPI, taskAPI } from '../services/api';
import toast from 'react-hot-toast';

// Function to map AI suggestions to 10-band EQ mastering settings
const mapAISuggestionsToMasteringSettings = (aiSuggestions: any) => {
  // Default 10-band EQ structure
  const default10BandEQ = [
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
  ];

  // Map AI EQ suggestions to closest 10-band frequencies
  if (aiSuggestions.eq_settings?.bands) {
    aiSuggestions.eq_settings.bands.forEach((aiBand: any) => {
      // Find the closest frequency band in our 10-band EQ
      const closestBandIndex = default10BandEQ.findIndex((band, index) => {
        const nextBand = default10BandEQ[index + 1];
        if (!nextBand) return true; // Last band

        const currentDiff = Math.abs(band.frequency - aiBand.frequency);
        const nextDiff = Math.abs(nextBand.frequency - aiBand.frequency);

        return currentDiff <= nextDiff;
      });

      if (closestBandIndex !== -1) {
        default10BandEQ[closestBandIndex] = {
          ...default10BandEQ[closestBandIndex],
          gain: aiBand.gain || 0,
          q: aiBand.q || default10BandEQ[closestBandIndex].q,
        };
      }
    });
  }

  return {
    eq_settings: {
      bands: default10BandEQ
    },
    compression_settings: aiSuggestions.compression_settings || {},
    saturation_settings: aiSuggestions.saturation_settings || {},
    stereo_settings: aiSuggestions.stereo_settings || {},
    limiting_settings: aiSuggestions.limiting_settings || {},
  };
};

const AudioUploader: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const { setCurrentTrack, setIsAnalyzing, setAnalysisProgress, addTask, updateMasteringSettings } = useAudioStore();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error('File too large. Maximum size is 100MB.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Upload the file with progress tracking
      const uploadResponse = await trackAPI.upload(file, (progress) => {
        setUploadProgress(progress);
      });
      
      // Get the track info
      const track = await trackAPI.getTrack(uploadResponse.track_id);
      setCurrentTrack(track);
      
      // Start monitoring analysis task
      setIsAnalyzing(true);
      setAnalysisProgress(0);
      
      const taskId = uploadResponse.analysis_task_id;
      addTask(taskId, {
        task_id: taskId,
        state: 'PENDING',
        status: 'Starting analysis...'
      });
      
      // Poll task status with timeout
      let pollCount = 0;
      const maxPolls = 300; // 10 minutes max (300 * 2 seconds)

      const pollInterval = setInterval(async () => {
        pollCount++;

        // Timeout after 10 minutes
        if (pollCount > maxPolls) {
          setIsAnalyzing(false);
          clearInterval(pollInterval);
          toast.error('Analysis timeout - please try again with a shorter track');
          return;
        }

        try {
          const taskStatus = await taskAPI.getStatus(taskId);

          if (taskStatus.state === 'PROGRESS') {
            const progress = taskStatus.progress || 0;
            setAnalysisProgress(progress);
            console.log(`Analysis progress: ${progress}%`);
          } else if (taskStatus.state === 'SUCCESS') {
            // Analysis completed, refresh track data
            const updatedTrack = await trackAPI.getTrack(uploadResponse.track_id);
            setCurrentTrack(updatedTrack);
            setIsAnalyzing(false);
            setAnalysisProgress(100);
            clearInterval(pollInterval);

            // Load AI suggestions automatically if they were applied
            if (taskStatus.result?.ai_suggestions && taskStatus.result?.auto_applied) {
              const aiSuggestions = taskStatus.result.ai_suggestions;
              const mappedSettings = mapAISuggestionsToMasteringSettings(aiSuggestions);
              updateMasteringSettings(mappedSettings);
              toast.success('Track analyzed and AI suggestions applied!');
            } else {
              toast.success('Track analyzed successfully!');
            }
          } else if (taskStatus.state === 'FAILURE') {
            setIsAnalyzing(false);
            clearInterval(pollInterval);
            toast.error(`Analysis failed: ${taskStatus.error}`);
          }
        } catch (error) {
          console.error('Error polling task status:', error);
        }
      }, 2000);
      
      toast.success('Track uploaded successfully! Analysis started.');
      
    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  }, [setCurrentTrack, setIsAnalyzing, setAnalysisProgress, addTask]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.flac', '.aiff', '.m4a']
    },
    maxFiles: 1,
    disabled: isUploading
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300
          ${isDragActive && !isDragReject 
            ? 'border-primary-400 bg-primary-400/10' 
            : isDragReject 
            ? 'border-red-400 bg-red-400/10'
            : 'border-gray-600 hover:border-gray-500 bg-gray-800/50'
          }
          ${isUploading ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-6">
          {/* Icon */}
          <div className="flex justify-center">
            {isUploading ? (
              <div className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
            ) : isDragReject ? (
              <AlertCircle className="w-16 h-16 text-red-400" />
            ) : (
              <Music className="w-16 h-16 text-gray-400" />
            )}
          </div>
          
          {/* Text */}
          <div>
            {isUploading ? (
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  Uploading...
                </h3>
                <p className="text-gray-400">
                  Please wait while we upload your track
                </p>
              </div>
            ) : isDragReject ? (
              <div>
                <h3 className="text-xl font-semibold text-red-400 mb-2">
                  Invalid File Type
                </h3>
                <p className="text-gray-400">
                  Please upload a valid audio file
                </p>
              </div>
            ) : isDragActive ? (
              <div>
                <h3 className="text-xl font-semibold text-primary-400 mb-2">
                  Drop your track here
                </h3>
                <p className="text-gray-400">
                  Release to upload
                </p>
              </div>
            ) : (
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  Upload Your Track
                </h3>
                <p className="text-gray-400 mb-4">
                  Drag & drop your audio file here, or click to browse
                </p>
                <div className="inline-flex items-center px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors">
                  Choose File
                </div>
              </div>
            )}
          </div>
          
          {/* Supported formats */}
          {!isUploading && !isDragReject && (
            <div className="text-sm text-gray-500">
              <p>Supported formats: WAV, MP3, FLAC, AIFF, M4A</p>
              <p>Maximum file size: 100MB</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Features */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass rounded-lg p-4 text-center">
          <div className="w-12 h-12 bg-primary-600 rounded-lg flex items-center justify-center mx-auto mb-3">
            <Music className="w-6 h-6 text-white" />
          </div>
          <h4 className="font-semibold text-white mb-2">AI Analysis</h4>
          <p className="text-sm text-gray-400">
            Automatic genre detection and frequency analysis
          </p>
        </div>
        
        <div className="glass rounded-lg p-4 text-center">
          <div className="w-12 h-12 bg-accent-600 rounded-lg flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h4 className="font-semibold text-white mb-2">Smart Mastering</h4>
          <p className="text-sm text-gray-400">
            Professional mastering chain with AI optimization
          </p>
        </div>
        
        <div className="glass rounded-lg p-4 text-center">
          <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z" />
            </svg>
          </div>
          <h4 className="font-semibold text-white mb-2">AI Chat</h4>
          <p className="text-sm text-gray-400">
            Natural language mastering adjustments
          </p>
        </div>
      </div>
    </div>
  );
};

export default AudioUploader;
