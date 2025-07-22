import React, { useEffect, useRef } from 'react';

interface WaveformViewerProps {
  currentTime: number;
  duration: number;
  onSeek?: (time: number) => void;
}

const WaveformViewer: React.FC<WaveformViewerProps> = ({
  currentTime,
  duration,
  onSeek
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Handle canvas click for seeking
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onSeek || duration === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const clickPosition = x / rect.width;
    const seekTime = clickPosition * duration;

    onSeek(seekTime);
  };

  // Draw waveform visualization
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Clear canvas
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, rect.width, rect.height);

    // Draw waveform (simplified visualization)
    const barWidth = 3;
    const barSpacing = 1;
    const numBars = Math.floor(rect.width / (barWidth + barSpacing));

    for (let i = 0; i < numBars; i++) {
      const x = i * (barWidth + barSpacing);
      // Create a stable waveform pattern (no random values)
      const normalizedPos = i / numBars;
      const waveHeight = Math.sin(normalizedPos * Math.PI * 8) * 0.4 +
                        Math.sin(normalizedPos * Math.PI * 20) * 0.3 +
                        Math.sin(normalizedPos * Math.PI * 50) * 0.2;
      const height = Math.abs(waveHeight) * rect.height * 0.8 + rect.height * 0.1;
      const y = (rect.height - height) / 2;

      // Progress indicator
      const progress = duration > 0 ? currentTime / duration : 0;
      const isPlayed = i / numBars < progress;

      ctx.fillStyle = isPlayed
        ? '#3b82f6' // Blue for played portion
        : '#4b5563'; // Gray for unplayed

      ctx.fillRect(x, y, barWidth, height);
    }

    // Draw playhead if we have duration
    if (duration > 0) {
      const playheadX = (currentTime / duration) * rect.width;
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, rect.height);
      ctx.stroke();
    }

  }, [currentTime, duration]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={800}
        height={120}
        className="w-full h-24 rounded-lg cursor-pointer"
        onClick={handleCanvasClick}
        title="Click to seek"
      />
    </div>
  );
};

export default WaveformViewer;
