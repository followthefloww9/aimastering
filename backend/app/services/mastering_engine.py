import numpy as np
import librosa
from scipy import signal
from typing import Dict, Any, Tuple
import logging
from pydub import AudioSegment
import os

logger = logging.getLogger(__name__)


class MasteringEngine:
    """Professional audio mastering engine with various processing chains"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        
    def apply_mastering_chain(self, audio_data: np.ndarray, settings: Dict[str, Any]) -> np.ndarray:
        """Apply complete mastering chain based on settings"""
        try:
            processed_audio = audio_data.copy()
            
            # Apply processing in order
            if settings.get('eq_settings'):
                processed_audio = self.apply_eq(processed_audio, settings['eq_settings'])
            
            if settings.get('compression_settings'):
                processed_audio = self.apply_compression(processed_audio, settings['compression_settings'])
            
            if settings.get('saturation_settings'):
                processed_audio = self.apply_saturation(processed_audio, settings['saturation_settings'])
            
            if settings.get('stereo_settings'):
                processed_audio = self.apply_stereo_processing(processed_audio, settings['stereo_settings'])
            
            if settings.get('limiting_settings'):
                processed_audio = self.apply_limiting(processed_audio, settings['limiting_settings'])
            
            return processed_audio
            
        except Exception as e:
            logger.error(f"Error in mastering chain: {e}")
            raise
    
    def apply_eq(self, audio: np.ndarray, eq_settings: Dict[str, Any]) -> np.ndarray:
        """Apply parametric EQ with multiple bands"""
        try:
            processed = audio.copy()
            
            for band in eq_settings.get('bands', []):
                freq = band.get('frequency', 1000)
                gain = band.get('gain', 0)
                q = band.get('q', 1.0)
                eq_type = band.get('type', 'peak')
                
                if abs(gain) > 0.1:  # Only apply if significant gain change
                    processed = self._apply_eq_band(processed, freq, gain, q, eq_type)
            
            return processed
            
        except Exception as e:
            logger.error(f"Error applying EQ: {e}")
            return audio
    
    def _apply_eq_band(self, audio: np.ndarray, freq: float, gain: float, q: float, eq_type: str) -> np.ndarray:
        """Apply single EQ band"""
        nyquist = self.sample_rate / 2
        normalized_freq = freq / nyquist
        
        if eq_type == 'highpass':
            b, a = signal.butter(2, normalized_freq, btype='high')
        elif eq_type == 'lowpass':
            b, a = signal.butter(2, normalized_freq, btype='low')
        elif eq_type == 'peak':
            # Peaking EQ using biquad filter
            w = 2 * np.pi * freq / self.sample_rate
            A = 10**(gain/40)
            alpha = np.sin(w) / (2 * q)

            b0 = 1 + alpha * A
            b1 = -2 * np.cos(w)
            b2 = 1 - alpha * A
            a0 = 1 + alpha / A
            a1 = -2 * np.cos(w)
            a2 = 1 - alpha / A

            b = np.array([b0, b1, b2]) / a0
            a = np.array([1, a1/a0, a2/a0])
        elif eq_type == 'low_shelf':
            # Low shelf filter
            w = 2 * np.pi * freq / self.sample_rate
            A = 10**(gain/40)
            S = 1  # Shelf slope
            alpha = np.sin(w)/2 * np.sqrt((A + 1/A)*(1/S - 1) + 2)

            b0 = A*((A+1) - (A-1)*np.cos(w) + 2*np.sqrt(A)*alpha)
            b1 = 2*A*((A-1) - (A+1)*np.cos(w))
            b2 = A*((A+1) - (A-1)*np.cos(w) - 2*np.sqrt(A)*alpha)
            a0 = (A+1) + (A-1)*np.cos(w) + 2*np.sqrt(A)*alpha
            a1 = -2*((A-1) + (A+1)*np.cos(w))
            a2 = (A+1) + (A-1)*np.cos(w) - 2*np.sqrt(A)*alpha

            b = np.array([b0, b1, b2]) / a0
            a = np.array([1, a1/a0, a2/a0])
        elif eq_type == 'high_shelf':
            # High shelf filter
            w = 2 * np.pi * freq / self.sample_rate
            A = 10**(gain/40)
            S = 1  # Shelf slope
            alpha = np.sin(w)/2 * np.sqrt((A + 1/A)*(1/S - 1) + 2)

            b0 = A*((A+1) + (A-1)*np.cos(w) + 2*np.sqrt(A)*alpha)
            b1 = -2*A*((A-1) + (A+1)*np.cos(w))
            b2 = A*((A+1) + (A-1)*np.cos(w) - 2*np.sqrt(A)*alpha)
            a0 = (A+1) - (A-1)*np.cos(w) + 2*np.sqrt(A)*alpha
            a1 = 2*((A-1) - (A+1)*np.cos(w))
            a2 = (A+1) - (A-1)*np.cos(w) - 2*np.sqrt(A)*alpha

            b = np.array([b0, b1, b2]) / a0
            a = np.array([1, a1/a0, a2/a0])
        else:
            return audio
        
        # Handle stereo audio
        if len(audio.shape) > 1:
            # Process each channel separately
            processed = np.zeros_like(audio)
            for channel in range(audio.shape[0]):
                processed[channel] = signal.filtfilt(b, a, audio[channel])
            return processed
        else:
            return signal.filtfilt(b, a, audio)
    
    def apply_compression(self, audio: np.ndarray, comp_settings: Dict[str, Any]) -> np.ndarray:
        """Apply advanced dynamic range compression with optimization"""
        try:
            threshold = comp_settings.get('threshold', -12)  # dB
            ratio = comp_settings.get('ratio', 4.0)
            attack = comp_settings.get('attack', 0.003)  # seconds
            release = comp_settings.get('release', 0.1)  # seconds
            makeup_gain = comp_settings.get('makeup_gain', 0)  # dB

            # Advanced dynamic range optimization
            target_dr = comp_settings.get('target_dynamic_range', None)
            if target_dr:
                # Calculate current dynamic range
                current_dr = self._calculate_dynamic_range(audio)
                # Adjust compression parameters for target DR
                threshold, ratio = self._optimize_compression_for_dr(
                    current_dr, target_dr, threshold, ratio
                )

            # Handle stereo audio
            if len(audio.shape) > 1:
                # Process each channel separately
                processed = np.zeros_like(audio)
                for channel in range(audio.shape[0]):
                    processed[channel] = self._apply_compression_channel(
                        audio[channel], threshold, ratio, attack, release, makeup_gain
                    )
                return processed
            else:
                return self._apply_compression_channel(audio, threshold, ratio, attack, release, makeup_gain)

        except Exception as e:
            logger.error(f"Error applying compression: {e}")
            return audio

    def _apply_compression_channel(self, audio: np.ndarray, threshold: float, ratio: float,
                                 attack: float, release: float, makeup_gain: float) -> np.ndarray:
        """Apply compression to a single channel"""
        # Convert to dB
        audio_db = 20 * np.log10(np.abs(audio) + 1e-10)

        # Calculate gain reduction
        gain_reduction = np.zeros_like(audio_db)
        over_threshold = audio_db > threshold
        gain_reduction[over_threshold] = (audio_db[over_threshold] - threshold) * (1 - 1/ratio)

        # Apply attack and release (simplified)
        gain_reduction = self._apply_envelope(gain_reduction, attack, release)

        # Apply compression
        compressed_db = audio_db - gain_reduction
        compressed_linear = np.sign(audio) * (10 ** (compressed_db / 20))

        # Apply makeup gain
        if makeup_gain != 0:
            compressed_linear *= 10 ** (makeup_gain / 20)

        return compressed_linear
    
    def _apply_envelope(self, signal_db: np.ndarray, attack: float, release: float) -> np.ndarray:
        """Apply attack and release envelope to gain reduction"""
        attack_samples = max(1, int(attack * self.sample_rate))
        release_samples = max(1, int(release * self.sample_rate))

        envelope = np.zeros_like(signal_db)

        # Calculate attack and release coefficients
        attack_coeff = 1.0 - np.exp(-1.0 / attack_samples)
        release_coeff = 1.0 - np.exp(-1.0 / release_samples)

        for i in range(1, len(signal_db)):
            if signal_db[i] > envelope[i-1]:
                # Attack - faster response
                envelope[i] = envelope[i-1] + (signal_db[i] - envelope[i-1]) * attack_coeff
            else:
                # Release - slower response
                envelope[i] = envelope[i-1] + (signal_db[i] - envelope[i-1]) * release_coeff

        return envelope
    
    def apply_saturation(self, audio: np.ndarray, sat_settings: Dict[str, Any]) -> np.ndarray:
        """Apply harmonic saturation/distortion"""
        try:
            drive = sat_settings.get('drive', 1.0)
            saturation_type = sat_settings.get('type', 'tube')
            mix = sat_settings.get('mix', 1.0)
            
            if saturation_type == 'tube':
                saturated = self._tube_saturation(audio, drive)
            elif saturation_type == 'tape':
                saturated = self._tape_saturation(audio, drive)
            else:
                saturated = self._soft_clipper(audio, drive)
            
            # Mix with original signal
            return audio * (1 - mix) + saturated * mix
            
        except Exception as e:
            logger.error(f"Error applying saturation: {e}")
            return audio
    
    def _tube_saturation(self, audio: np.ndarray, drive: float) -> np.ndarray:
        """Tube-style saturation"""
        driven = audio * drive
        return np.tanh(driven * 0.7) * 0.95
    
    def _tape_saturation(self, audio: np.ndarray, drive: float) -> np.ndarray:
        """Tape-style saturation"""
        driven = audio * drive
        return driven / (1 + np.abs(driven))
    
    def _soft_clipper(self, audio: np.ndarray, drive: float) -> np.ndarray:
        """Soft clipping saturation"""
        driven = audio * drive
        return np.sign(driven) * (1 - np.exp(-np.abs(driven)))
    
    def apply_stereo_processing(self, audio: np.ndarray, stereo_settings: Dict[str, Any]) -> np.ndarray:
        """Apply stereo width and imaging processing - always returns stereo"""
        try:
            # Always ensure stereo output
            if len(audio.shape) == 1:
                # Mono signal - create stereo by duplicating the channel
                stereo_audio = np.array([audio, audio])
            elif len(audio.shape) == 2 and audio.shape[0] == 1:
                # Single channel in 2D array - duplicate to stereo
                stereo_audio = np.array([audio[0], audio[0]])
            else:
                # Already stereo or multi-channel
                stereo_audio = audio.copy()
                if stereo_audio.shape[0] == 1:
                    # Ensure we have 2 channels
                    stereo_audio = np.array([stereo_audio[0], stereo_audio[0]])

            width = stereo_settings.get('width', 1.0)

            if width != 1.0 and len(stereo_audio.shape) > 1 and stereo_audio.shape[0] >= 2:
                # Mid/Side processing for stereo
                left = stereo_audio[0]
                right = stereo_audio[1]

                mid = (left + right) / 2
                side = (left - right) / 2

                # Adjust stereo width
                side *= width

                # Convert back to L/R
                stereo_audio[0] = mid + side
                stereo_audio[1] = mid - side

            # Ensure we always return stereo format (2, samples)
            if len(stereo_audio.shape) == 1:
                stereo_audio = np.array([stereo_audio, stereo_audio])
            elif stereo_audio.shape[0] == 1:
                stereo_audio = np.array([stereo_audio[0], stereo_audio[0]])

            return stereo_audio

        except Exception as e:
            logger.error(f"Error applying stereo processing: {e}")
            # Return stereo version of input on error
            if len(audio.shape) == 1:
                return np.array([audio, audio])
            return audio
    
    def apply_limiting(self, audio: np.ndarray, limit_settings: Dict[str, Any]) -> np.ndarray:
        """Apply brick-wall limiting"""
        try:
            ceiling = limit_settings.get('ceiling', -0.1)  # dB
            release = limit_settings.get('release', 0.05)  # seconds

            # Convert ceiling to linear
            ceiling_linear = 10 ** (ceiling / 20)

            # Handle stereo audio
            if len(audio.shape) > 1:
                # Process each channel separately
                limited = np.zeros_like(audio)
                for channel in range(audio.shape[0]):
                    limited[channel] = self._apply_limiting_channel(audio[channel], ceiling_linear, release)
                return limited
            else:
                return self._apply_limiting_channel(audio, ceiling_linear, release)

        except Exception as e:
            logger.error(f"Error applying limiting: {e}")
            return audio

    def _calculate_dynamic_range(self, audio: np.ndarray) -> float:
        """Calculate current dynamic range of audio"""
        try:
            if len(audio.shape) > 1:
                # For stereo, use the channel with higher dynamic range
                dr_values = []
                for channel in range(audio.shape[0]):
                    peak = np.max(np.abs(audio[channel]))
                    rms = np.sqrt(np.mean(audio[channel] ** 2))
                    dr = 20 * np.log10(peak / (rms + 1e-10))
                    dr_values.append(dr)
                return max(dr_values)
            else:
                peak = np.max(np.abs(audio))
                rms = np.sqrt(np.mean(audio ** 2))
                return 20 * np.log10(peak / (rms + 1e-10))
        except Exception as e:
            logger.error(f"Error calculating dynamic range: {e}")
            return 10.0  # Default fallback

    def _optimize_compression_for_dr(self, current_dr: float, target_dr: float,
                                   threshold: float, ratio: float) -> tuple:
        """Optimize compression parameters to achieve target dynamic range"""
        try:
            dr_difference = current_dr - target_dr

            if dr_difference > 2.0:  # Need more compression
                # Increase compression by lowering threshold and/or increasing ratio
                new_threshold = threshold - min(dr_difference * 0.5, 6.0)
                new_ratio = min(ratio * (1 + dr_difference * 0.1), 10.0)
            elif dr_difference < -2.0:  # Need less compression
                # Decrease compression by raising threshold and/or decreasing ratio
                new_threshold = threshold + min(abs(dr_difference) * 0.3, 4.0)
                new_ratio = max(ratio * (1 - abs(dr_difference) * 0.05), 1.5)
            else:
                # Current DR is close to target
                new_threshold = threshold
                new_ratio = ratio

            return new_threshold, new_ratio

        except Exception as e:
            logger.error(f"Error optimizing compression: {e}")
            return threshold, ratio

    def _apply_limiting_channel(self, audio: np.ndarray, ceiling_linear: float, release: float) -> np.ndarray:
        """Apply limiting to a single channel"""
        # Professional brick-wall limiter with proper release
        limited = np.copy(audio)

        # Find peaks above ceiling
        peaks = np.abs(limited) > ceiling_linear

        # Apply limiting with proper gain reduction
        gain_reduction = np.ones_like(limited)

        # Calculate required gain reduction for peaks
        peak_indices = np.where(peaks)[0]
        for peak_idx in peak_indices:
            # Calculate gain reduction needed
            peak_level = np.abs(limited[peak_idx])
            reduction = ceiling_linear / peak_level
            gain_reduction[peak_idx] = min(gain_reduction[peak_idx], reduction)

        # Apply smooth release envelope
        release_samples = max(1, int(release * self.sample_rate))

        # Forward pass - apply attack (instant)
        for i in range(1, len(gain_reduction)):
            if gain_reduction[i] < gain_reduction[i-1]:
                # Attack - instant
                pass  # Keep the lower gain reduction
            else:
                # Release - smooth
                release_coeff = 1.0 - (1.0 / release_samples)
                gain_reduction[i] = gain_reduction[i-1] * release_coeff + gain_reduction[i] * (1 - release_coeff)

        # Apply gain reduction
        limited = limited * gain_reduction

        return limited
    
    def get_genre_preset(self, genre: str) -> Dict[str, Any]:
        """Get mastering preset based on genre"""
        presets = {
            'rock': {
                'eq_settings': {
                    'bands': [
                        {'frequency': 100, 'gain': 2, 'q': 0.7, 'type': 'peak'},
                        {'frequency': 3000, 'gain': -2, 'q': 1.0, 'type': 'peak'},
                        {'frequency': 10000, 'gain': 3, 'q': 0.7, 'type': 'peak'}
                    ]
                },
                'compression_settings': {
                    'threshold': -8, 'ratio': 4.0, 'attack': 0.003, 'release': 0.1, 'makeup_gain': 3
                },
                'saturation_settings': {
                    'drive': 1.5, 'type': 'tube', 'mix': 0.3
                },
                'limiting_settings': {
                    'ceiling': -0.3, 'release': 0.05
                }
            },
            'electronic': {
                'eq_settings': {
                    'bands': [
                        {'frequency': 60, 'gain': 4, 'q': 0.7, 'type': 'peak'},
                        {'frequency': 8000, 'gain': 2, 'q': 0.7, 'type': 'peak'}
                    ]
                },
                'compression_settings': {
                    'threshold': -6, 'ratio': 6.0, 'attack': 0.001, 'release': 0.05, 'makeup_gain': 2
                },
                'stereo_settings': {
                    'width': 1.3
                },
                'limiting_settings': {
                    'ceiling': -0.1, 'release': 0.03
                }
            },
            'jazz': {
                'eq_settings': {
                    'bands': [
                        {'frequency': 200, 'gain': 1, 'q': 0.5, 'type': 'peak'},
                        {'frequency': 5000, 'gain': 1.5, 'q': 0.7, 'type': 'peak'}
                    ]
                },
                'compression_settings': {
                    'threshold': -15, 'ratio': 2.5, 'attack': 0.01, 'release': 0.2, 'makeup_gain': 1
                },
                'saturation_settings': {
                    'drive': 1.1, 'type': 'tape', 'mix': 0.2
                },
                'limiting_settings': {
                    'ceiling': -1.0, 'release': 0.1
                }
            }
        }
        
        return presets.get(genre, presets['rock'])  # Default to rock preset
