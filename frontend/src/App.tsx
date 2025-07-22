import React from 'react';
import { Toaster } from 'react-hot-toast';
import { useAudioStore } from './stores/audioStore';
import Header from './components/Header';
import AudioUploader from './components/AudioUploader';
import TrackAnalysis from './components/TrackAnalysis';
import MasteringControls from './components/MasteringControls';
import AIChat from './components/AIChat';
import AudioPlayer from './components/AudioPlayer';

function App() {
  const { currentTrack } = useAudioStore();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#374151',
            color: '#fff',
            border: '1px solid #4B5563',
          },
        }}
      />
      
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {!currentTrack ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                AI Mastering Studio
              </h1>
              <p className="text-xl text-gray-300 mb-8">
                Professional audio mastering powered by Gemini 2.5 Flash
              </p>
            </div>
            <AudioUploader />
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Main Content */}
            <div className="xl:col-span-2 space-y-6">
              {/* Track Info & Analysis */}
              <TrackAnalysis />

              {/* Audio Player */}
              <AudioPlayer />

              {/* Mastering Controls */}
              <MasteringControls />
            </div>
            
            {/* Sidebar */}
            <div className="xl:col-span-1">
              <AIChat />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
