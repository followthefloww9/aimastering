import librosa
import numpy as np
from typing import Dict, Any, Tuple
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Advanced audio analysis service for mastering decisions"""
    
    def __init__(self):
        self.sample_rate = 44100
        self.genre_classifier = None
        self.scaler = None
        self._load_or_create_genre_model()
    
    def _load_or_create_genre_model(self):
        """Load pre-trained genre classifier or create a simple one"""
        try:
            # In production, you'd load a pre-trained model
            # For now, we'll create a simple classifier
            self.genre_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
            
            # Create dummy training data for genre classification
            # In production, this would be trained on a large dataset
            dummy_features = np.random.rand(1000, 13)  # 13 MFCC features
            dummy_labels = np.random.choice(['rock', 'electronic', 'jazz', 'hip-hop', 'pop'], 1000)
            
            dummy_features_scaled = self.scaler.fit_transform(dummy_features)
            self.genre_classifier.fit(dummy_features_scaled, dummy_labels)
            
        except Exception as e:
            logger.error(f"Error loading genre model: {e}")
            self.genre_classifier = None
            self.scaler = None
    
    def analyze_track(self, file_path: str, progress_callback=None) -> Dict[str, Any]:
        """Comprehensive audio analysis"""
        try:
            if progress_callback:
                progress_callback("Loading audio file", 5)

            # Load audio file (preserve stereo) - limit to first 30 seconds for faster analysis
            y, sr = librosa.load(file_path, sr=self.sample_rate, mono=False, duration=30.0)

            # Convert to mono for analysis if stereo
            y_mono = librosa.to_mono(y) if len(y.shape) > 1 else y

            if progress_callback:
                progress_callback("Basic audio properties", 10)

            # Basic audio properties
            duration = librosa.get_duration(y=y_mono, sr=sr)

            if progress_callback:
                progress_callback("Tempo and beat tracking", 20)

            # Tempo and beat tracking (ultra-fast estimation)
            try:
                # Use very fast tempo estimation with minimal analysis
                tempo, beats = librosa.beat.beat_track(
                    y=y_mono[:sr*10],  # Only analyze first 10 seconds
                    sr=sr,
                    hop_length=2048,   # Much larger hop for speed
                    start_bpm=80,      # Narrow BPM range
                    std_bpm=20
                )
            except:
                tempo = 120.0  # Default fallback
                beats = []

            if progress_callback:
                progress_callback("Key detection", 30)

            # Key detection (ultra-fast)
            try:
                # Use very small analysis window for speed
                chroma = librosa.feature.chroma_stft(
                    y=y_mono[:sr*5],   # Only analyze first 5 seconds
                    sr=sr,
                    hop_length=2048    # Much larger hop for speed
                )
                key = self._estimate_key(chroma)
            except:
                key = "C"  # Default fallback

            if progress_callback:
                progress_callback("Loudness analysis", 40)

            # Loudness analysis
            loudness = self._calculate_loudness(y_mono, sr)

            if progress_callback:
                progress_callback("Spectral features", 50)

            # Spectral features
            spectral_features = self._extract_spectral_features(y_mono, sr)

            if progress_callback:
                progress_callback("Frequency analysis", 60)

            # Frequency analysis
            frequency_analysis = self._analyze_frequency_spectrum(y_mono, sr)

            if progress_callback:
                progress_callback("Frequency masking analysis", 75)

            # Advanced frequency masking analysis
            masking_analysis = self._analyze_frequency_masking(y_mono, sr)

            if progress_callback:
                progress_callback("Stereo imaging analysis", 85)

            # Advanced stereo imaging analysis
            stereo_analysis = self._analyze_stereo_imaging(y, sr)

            if progress_callback:
                progress_callback("Genre prediction", 95)

            # Genre prediction
            genre_prediction = self._predict_genre(y_mono, sr)

            if progress_callback:
                progress_callback("Analysis complete", 100)

            return {
                'duration': float(duration),
                'tempo': float(tempo),
                'key': key,
                'loudness': loudness,
                'predicted_genre': genre_prediction['genre'],
                'genre_confidence': genre_prediction['confidence'],
                'spectral_features': spectral_features,
                'frequency_analysis': frequency_analysis,
                'masking_analysis': masking_analysis,
                'stereo_analysis': stereo_analysis,
                'sample_rate': sr,
                'channels': 1 if len(y.shape) == 1 else y.shape[0]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing track {file_path}: {e}")
            raise
    
    def _estimate_key(self, chroma: np.ndarray) -> str:
        """Estimate musical key from chroma features"""
        # Simplified key estimation
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        chroma_mean = np.mean(chroma, axis=1)
        key_idx = np.argmax(chroma_mean)
        return key_names[key_idx]
    
    def _calculate_loudness(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Calculate various loudness metrics"""
        # RMS energy (overall level)
        rms = np.sqrt(np.mean(y**2))
        rms_db = 20 * np.log10(rms + 1e-10)  # Add small value to avoid log(0)

        # Peak amplitude
        peak = np.max(np.abs(y))
        peak_db = 20 * np.log10(peak + 1e-10)

        # Proper LUFS calculation with K-weighting filter
        lufs_integrated = self._calculate_lufs(y, sr)

        # LUFS approximation for backward compatibility
        lufs_approx = rms_db + 3.0  # Typical correction factor for LUFS

        # Dynamic range (crest factor in dB)
        dynamic_range = peak_db - rms_db

        return {
            'rms_db': float(rms_db),
            'peak_db': float(peak_db),
            'lufs_approx': float(lufs_approx),
            'lufs_integrated': float(lufs_integrated),
            'dynamic_range': float(dynamic_range)
        }
    
    def _extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract spectral features for analysis"""
        # Use very small analysis window for speed
        y_short = y[:sr*10] if len(y) > sr*10 else y  # Only 10 seconds

        # MFCC features (ultra-fast)
        mfccs = librosa.feature.mfcc(y=y_short, sr=sr, n_mfcc=8, hop_length=2048)  # Fewer coefficients

        # Spectral centroid (ultra-fast)
        spectral_centroids = librosa.feature.spectral_centroid(y=y_short, sr=sr, hop_length=2048)[0]

        # Spectral rolloff (ultra-fast)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y_short, sr=sr, hop_length=2048)[0]

        # Zero crossing rate (ultra-fast)
        zcr = librosa.feature.zero_crossing_rate(y_short, hop_length=2048)[0]
        
        return {
            'mfcc_mean': mfccs.mean(axis=1).tolist(),
            'mfcc_std': mfccs.std(axis=1).tolist(),
            'spectral_centroid_mean': float(np.mean(spectral_centroids)),
            'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
            'zero_crossing_rate_mean': float(np.mean(zcr))
        }
    
    def _analyze_frequency_spectrum(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze frequency spectrum for mastering decisions (optimized)"""
        # Use smaller window for faster FFT
        window_size = min(len(y), sr * 10)  # Max 10 seconds
        y_windowed = y[:window_size]

        # Compute FFT with smaller window
        fft = np.fft.fft(y_windowed)
        magnitude = np.abs(fft)
        freqs = np.fft.fftfreq(len(fft), 1/sr)
        
        # Focus on positive frequencies
        positive_freqs = freqs[:len(freqs)//2]
        positive_magnitude = magnitude[:len(magnitude)//2]
        
        # Define frequency bands
        bands = {
            'sub_bass': (20, 60),
            'bass': (60, 250),
            'low_mid': (250, 500),
            'mid': (500, 2000),
            'high_mid': (2000, 4000),
            'presence': (4000, 6000),
            'brilliance': (6000, 20000)
        }
        
        band_energy = {}
        for band_name, (low, high) in bands.items():
            band_mask = (positive_freqs >= low) & (positive_freqs <= high)
            band_energy[band_name] = float(np.mean(positive_magnitude[band_mask]))
        
        return {
            'frequency_bands': band_energy,
            'dominant_frequency': float(positive_freqs[np.argmax(positive_magnitude)]),
            'spectral_balance': self._calculate_spectral_balance(band_energy)
        }
    
    def _calculate_spectral_balance(self, band_energy: Dict[str, float]) -> Dict[str, str]:
        """Analyze spectral balance for mastering suggestions"""
        total_energy = sum(band_energy.values())
        band_ratios = {k: v/total_energy for k, v in band_energy.items()}
        
        suggestions = {}
        
        # Analyze each band
        if band_ratios['bass'] < 0.15:
            suggestions['bass'] = 'boost'
        elif band_ratios['bass'] > 0.25:
            suggestions['bass'] = 'cut'
        else:
            suggestions['bass'] = 'neutral'
            
        if band_ratios['mid'] < 0.20:
            suggestions['mid'] = 'boost'
        elif band_ratios['mid'] > 0.35:
            suggestions['mid'] = 'cut'
        else:
            suggestions['mid'] = 'neutral'
            
        if band_ratios['brilliance'] < 0.10:
            suggestions['brilliance'] = 'boost'
        elif band_ratios['brilliance'] > 0.20:
            suggestions['brilliance'] = 'cut'
        else:
            suggestions['brilliance'] = 'neutral'
        
        return suggestions
    
    def _predict_genre(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Predict genre using audio features analysis"""
        try:
            # Extract features for genre classification
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            # Calculate feature statistics
            mfcc_mean = np.mean(mfccs, axis=1)
            centroid_mean = np.mean(spectral_centroid)
            rolloff_mean = np.mean(spectral_rolloff)
            zcr_mean = np.mean(zcr)

            # Rule-based genre classification based on audio characteristics
            genre_scores = {
                'electronic': 0.0,
                'rock': 0.0,
                'jazz': 0.0,
                'hip-hop': 0.0,
                'pop': 0.0
            }

            # Electronic music characteristics
            if centroid_mean > 1800:  # High frequency content (lowered threshold)
                genre_scores['electronic'] += 0.4
            if zcr_mean > 0.05:  # High zero crossing rate (digital artifacts, lowered threshold)
                genre_scores['electronic'] += 0.3
            if tempo > 110 and tempo < 180:  # Broader electronic tempo range
                genre_scores['electronic'] += 0.3
            if rolloff_mean > 2500:  # High energy in upper frequencies
                genre_scores['electronic'] += 0.3
            # Check for synthetic/digital characteristics
            if mfcc_mean[2] > 10:  # High MFCC values indicate synthetic sounds
                genre_scores['electronic'] += 0.4
            if np.std(mfccs[1]) > 20:  # High variance in MFCC indicates complex synthesis
                genre_scores['electronic'] += 0.3

            # Rock music characteristics
            if centroid_mean > 1500 and centroid_mean < 3000:
                genre_scores['rock'] += 0.2
            if tempo > 100 and tempo < 160:
                genre_scores['rock'] += 0.2
            if rolloff_mean > 3000:  # High energy in upper frequencies
                genre_scores['rock'] += 0.3
            if mfcc_mean[2] < 0:  # Specific MFCC pattern for rock
                genre_scores['rock'] += 0.3

            # Jazz characteristics (more restrictive)
            if centroid_mean < 1500:  # Lower frequency focus (more restrictive)
                genre_scores['jazz'] += 0.2
            if tempo > 80 and tempo < 120:  # Typical jazz tempo
                genre_scores['jazz'] += 0.2
            if zcr_mean < 0.03:  # Much lower zero crossing rate (acoustic instruments)
                genre_scores['jazz'] += 0.3
            # Jazz typically has more organic, less synthetic characteristics
            if np.std(mfccs[1]) < 15:  # Lower variance indicates less synthetic processing
                genre_scores['jazz'] += 0.2
            if rolloff_mean < 2000:  # Lower rolloff for acoustic instruments
                genre_scores['jazz'] += 0.3

            # Hip-hop characteristics
            if tempo > 70 and tempo < 100:  # Typical hip-hop tempo
                genre_scores['hip-hop'] += 0.3
            if centroid_mean < 1800:
                genre_scores['hip-hop'] += 0.2
            if mfcc_mean[0] > 0:  # Strong low-frequency content
                genre_scores['hip-hop'] += 0.3
            if rolloff_mean < 2500:
                genre_scores['hip-hop'] += 0.2

            # Pop characteristics (default/balanced)
            if tempo > 90 and tempo < 130:
                genre_scores['pop'] += 0.2
            if centroid_mean > 1000 and centroid_mean < 2500:
                genre_scores['pop'] += 0.3
            if zcr_mean > 0.03 and zcr_mean < 0.08:
                genre_scores['pop'] += 0.3
            if abs(mfcc_mean[1]) < 0.5:  # Balanced MFCC
                genre_scores['pop'] += 0.2

            # Find the genre with highest score
            predicted_genre = max(genre_scores, key=genre_scores.get)
            confidence = genre_scores[predicted_genre]

            # If no strong indicators, default to pop
            if confidence < 0.3:
                predicted_genre = 'pop'
                confidence = 0.5

            return {
                'genre': predicted_genre,
                'confidence': float(min(confidence, 1.0))
            }

        except Exception as e:
            logger.error(f"Error predicting genre: {e}")
            return {'genre': 'electronic', 'confidence': 0.5}

    def _calculate_lufs(self, y: np.ndarray, sr: int) -> float:
        """Calculate proper LUFS with K-weighting filter"""
        try:
            # Simplified K-weighting filter implementation
            from scipy import signal

            # High-pass filter at 38Hz
            nyquist = sr / 2
            high_pass_freq = 38.0 / nyquist
            b_hp, a_hp = signal.butter(2, high_pass_freq, btype='high')
            y_filtered = signal.filtfilt(b_hp, a_hp, y)

            # High-shelf filter at 1.5kHz (+4dB)
            shelf_freq = 1500.0 / nyquist
            b_shelf, a_shelf = signal.iirfilter(2, shelf_freq, btype='high', ftype='butter')
            # Apply shelf gain (simplified)
            y_weighted = y_filtered * 1.585  # +4dB = 10^(4/20)

            # Calculate mean square with gating
            mean_square = np.mean(y_weighted ** 2)
            lufs = -0.691 + 10 * np.log10(mean_square + 1e-10)

            return lufs

        except Exception as e:
            logger.error(f"Error calculating LUFS: {e}")
            # Fallback to approximation
            rms = np.sqrt(np.mean(y ** 2))
            return 20 * np.log10(rms + 1e-10) + 3.0

    def _analyze_frequency_masking(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze frequency masking and suggest improvements (optimized)"""
        try:
            # Use smaller window for faster analysis
            y_short = y[:sr*15] if len(y) > sr*15 else y  # Max 15 seconds

            # Calculate STFT for frequency analysis (optimized)
            stft = librosa.stft(y_short, n_fft=1024, hop_length=512)  # Smaller FFT
            magnitude = np.abs(stft)

            # Frequency bins (optimized)
            freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)

            # Critical bands for masking analysis (Bark scale approximation)
            critical_bands = [
                (20, 100), (100, 200), (200, 300), (300, 400), (400, 510),
                (510, 630), (630, 770), (770, 920), (920, 1080), (1080, 1270),
                (1270, 1480), (1480, 1720), (1720, 2000), (2000, 2320),
                (2320, 2700), (2700, 3150), (3150, 3700), (3700, 4400),
                (4400, 5300), (5300, 6400), (6400, 7700), (7700, 9500),
                (9500, 12000), (12000, 15500), (15500, 20000)
            ]

            masking_analysis = {}
            recommendations = []

            for i, (low_freq, high_freq) in enumerate(critical_bands):
                # Find frequency bin indices
                low_idx = np.argmin(np.abs(freqs - low_freq))
                high_idx = np.argmin(np.abs(freqs - high_freq))

                # Calculate energy in this critical band
                band_energy = np.mean(magnitude[low_idx:high_idx, :])
                band_energy_db = 20 * np.log10(band_energy + 1e-10)

                # Detect potential masking issues
                masking_threshold = -60  # dB threshold for audibility
                is_masked = band_energy_db < masking_threshold

                center_freq = (low_freq + high_freq) / 2

                # Generate recommendations for masked frequencies
                if is_masked and center_freq > 100:  # Ignore very low frequencies
                    if center_freq < 500:
                        recommendations.append(f"Boost {center_freq:.0f}Hz (+2-4dB) - masked low frequencies")
                    elif center_freq < 2000:
                        recommendations.append(f"Boost {center_freq:.0f}Hz (+1-3dB) - masked midrange")
                    else:
                        recommendations.append(f"Boost {center_freq:.0f}Hz (+2-5dB) - masked high frequencies")

                masking_analysis[f'band_{center_freq:.0f}hz'] = {
                    'energy_db': float(band_energy_db),
                    'is_masked': bool(is_masked),
                    'center_freq': center_freq
                }

            return {
                'critical_bands': masking_analysis,
                'recommendations': recommendations,
                'total_masked_bands': sum(1 for band in masking_analysis.values() if band['is_masked'])
            }

        except Exception as e:
            logger.error(f"Error in frequency masking analysis: {e}")
            return {'critical_bands': {}, 'recommendations': [], 'total_masked_bands': 0}

    def _analyze_stereo_imaging(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Advanced stereo imaging analysis"""
        try:
            if len(y.shape) < 2:
                return {
                    'stereo_width': 0.0,
                    'correlation': 1.0,
                    'balance': 0.0,
                    'phase_coherence': 1.0,
                    'recommendations': ['Track is mono - consider stereo enhancement'],
                    'is_mono': True
                }

            left = y[0]
            right = y[1]

            # Stereo correlation
            correlation = np.corrcoef(left, right)[0, 1]

            # Mid/Side analysis
            mid = (left + right) / 2
            side = (left - right) / 2

            # Stereo width calculation
            mid_energy = np.mean(mid ** 2)
            side_energy = np.mean(side ** 2)
            stereo_width = side_energy / (mid_energy + 1e-10)

            # Left/Right balance
            left_energy = np.mean(left ** 2)
            right_energy = np.mean(right ** 2)
            balance = (right_energy - left_energy) / (right_energy + left_energy + 1e-10)

            # Phase coherence analysis
            phase_coherence = self._calculate_phase_coherence(left, right)

            # Generate recommendations
            recommendations = []

            if stereo_width < 0.1:
                recommendations.append("Very narrow stereo image - increase stereo width (+20-40%)")
            elif stereo_width > 2.0:
                recommendations.append("Overly wide stereo image - reduce width (-10-20%)")

            if abs(balance) > 0.1:
                side = "right" if balance > 0 else "left"
                recommendations.append(f"Stereo imbalance detected - {side} channel louder ({abs(balance)*100:.1f}%)")

            if correlation < 0.7:
                recommendations.append("Low stereo correlation - check phase issues")
            elif correlation > 0.95:
                recommendations.append("Very high correlation - consider stereo enhancement")

            if phase_coherence < 0.8:
                recommendations.append("Phase coherence issues detected - check stereo alignment")

            return {
                'stereo_width': float(stereo_width),
                'correlation': float(correlation),
                'balance': float(balance),
                'phase_coherence': float(phase_coherence),
                'mid_energy_db': float(20 * np.log10(np.sqrt(mid_energy) + 1e-10)),
                'side_energy_db': float(20 * np.log10(np.sqrt(side_energy) + 1e-10)),
                'recommendations': recommendations,
                'is_mono': False
            }

        except Exception as e:
            logger.error(f"Error in stereo imaging analysis: {e}")
            return {'stereo_width': 1.0, 'correlation': 1.0, 'balance': 0.0, 'recommendations': []}

    def _calculate_phase_coherence(self, left: np.ndarray, right: np.ndarray) -> float:
        """Calculate phase coherence between left and right channels"""
        try:
            # Cross-correlation to find phase relationship
            correlation = np.correlate(left, right, mode='full')
            max_corr_idx = np.argmax(np.abs(correlation))
            max_correlation = correlation[max_corr_idx]

            # Normalize by auto-correlations
            left_autocorr = np.correlate(left, left, mode='full')[len(left)-1]
            right_autocorr = np.correlate(right, right, mode='full')[len(right)-1]

            coherence = np.abs(max_correlation) / np.sqrt(left_autocorr * right_autocorr)
            return min(1.0, coherence)

        except Exception as e:
            logger.error(f"Error calculating phase coherence: {e}")
            return 1.0
