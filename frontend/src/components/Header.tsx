import React from 'react';
import { useAudioStore } from '../stores/audioStore';
import { Music, Upload, Download, Trash2 } from 'lucide-react';
import { trackAPI } from '../services/api';
import toast from 'react-hot-toast';

const Header: React.FC = () => {
  const { currentTrack, reset } = useAudioStore();

  const handleNewTrack = () => {
    if (currentTrack) {
      const confirmed = window.confirm('Are you sure you want to start with a new track? Current progress will be lost.');
      if (confirmed) {
        reset();
      }
    }
  };

  const handleDownloadOriginal = () => {
    if (currentTrack) {
      const url = trackAPI.downloadOriginal(currentTrack.id);
      window.open(url, '_blank');
    }
  };

  const handleDownloadMastered = () => {
    if (currentTrack && currentTrack.is_processed) {
      const url = trackAPI.downloadMastered(currentTrack.id);
      window.open(url, '_blank');
    } else {
      toast.error('No mastered version available');
    }
  };

  const handleDeleteTrack = async () => {
    if (currentTrack) {
      const confirmed = window.confirm('Are you sure you want to delete this track?');
      if (confirmed) {
        try {
          await trackAPI.delete(currentTrack.id);
          reset();
          toast.success('Track deleted successfully');
        } catch (error) {
          toast.error('Failed to delete track');
        }
      }
    }
  };

  return (
    <header className="bg-gray-800 border-b border-gray-700 shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-r from-primary-500 to-accent-500 rounded-lg">
              <Music className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">AI Mastering Studio</h1>
              <p className="text-sm text-gray-400">Powered by Gemini 2.5 Flash</p>
            </div>
          </div>

          {/* Track Info */}
          {currentTrack && (
            <div className="flex-1 mx-8">
              <div className="glass rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-white truncate max-w-md">
                      {currentTrack.filename}
                    </h2>
                    <div className="flex items-center space-x-4 text-sm text-gray-300">
                      {currentTrack.duration && (
                        <span>{Math.round(currentTrack.duration)}s</span>
                      )}
                      {currentTrack.predicted_genre && (
                        <span className="px-2 py-1 bg-primary-600 rounded text-xs">
                          {currentTrack.predicted_genre}
                        </span>
                      )}
                      {currentTrack.is_analyzed && (
                        <span className="px-2 py-1 bg-green-600 rounded text-xs">
                          Analyzed
                        </span>
                      )}
                      {currentTrack.is_processed && (
                        <span className="px-2 py-1 bg-accent-600 rounded text-xs">
                          Mastered
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center space-x-2">
            {currentTrack ? (
              <>
                <button
                  onClick={handleDownloadOriginal}
                  className="btn-secondary flex items-center space-x-2"
                  title="Download Original"
                >
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Original</span>
                </button>
                
                {currentTrack.is_processed && (
                  <button
                    onClick={handleDownloadMastered}
                    className="btn-primary flex items-center space-x-2"
                    title="Download Mastered"
                  >
                    <Download className="w-4 h-4" />
                    <span className="hidden sm:inline">Mastered</span>
                  </button>
                )}
                
                <button
                  onClick={handleDeleteTrack}
                  className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                  title="Delete Track"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                
                <button
                  onClick={handleNewTrack}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <Upload className="w-4 h-4" />
                  <span className="hidden sm:inline">New Track</span>
                </button>
              </>
            ) : (
              <div className="text-sm text-gray-400">
                Upload a track to get started
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
