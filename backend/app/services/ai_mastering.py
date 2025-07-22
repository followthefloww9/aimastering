from google import genai
from typing import Dict, Any, List
import json
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class AIMasteringService:
    """AI-powered mastering assistant using Gemini 2.5 Flash"""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"

        # Professional mastering reference standards
        self.genre_standards = self._initialize_genre_standards()
    
    def analyze_and_suggest(self, track_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze track and suggest mastering parameters"""
        try:
            prompt = self._create_analysis_prompt(track_analysis)
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            # Parse the AI response
            suggestions = self._parse_ai_response(response.text)
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting AI suggestions: {e}")
            return self._get_fallback_suggestions(track_analysis)
    
    def process_user_request(self, user_message: str, current_settings: Dict[str, Any], 
                           track_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Process user's natural language mastering request"""
        try:
            prompt = self._create_user_request_prompt(user_message, current_settings, track_analysis)
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            # Parse the response for parameter adjustments
            adjustments = self._parse_adjustment_response(response.text)
            return adjustments
            
        except Exception as e:
            logger.error(f"Error processing user request: {e}")
            return {'error': 'Could not process request'}
    
    def _create_analysis_prompt(self, track_analysis: Dict[str, Any]) -> str:
        """Create advanced prompt for professional track analysis"""
        genre = track_analysis.get('predicted_genre', 'unknown')
        loudness = track_analysis.get('loudness', {})
        freq_analysis = track_analysis.get('frequency_analysis', {})

        # Get professional reference standards for the genre
        reference_standards = self._get_genre_reference_standards(genre)

        # Analyze current vs target loudness
        current_lufs = loudness.get('lufs_approx', -23)
        target_lufs = reference_standards['target_lufs']
        loudness_adjustment = target_lufs - current_lufs

        # Analyze frequency balance vs genre standards
        freq_bands = freq_analysis.get('frequency_bands', {})
        freq_recommendations = self._analyze_frequency_balance(freq_bands, genre)

        # Advanced psychoacoustic analysis
        psychoacoustic_data = self._calculate_psychoacoustic_adjustments(track_analysis, genre)

        # Frequency masking analysis and recommendations
        masking_analysis = track_analysis.get('masking_analysis', {})
        masking_recommendations = self._process_masking_recommendations(masking_analysis, genre)

        # Stereo imaging analysis and recommendations
        stereo_analysis = track_analysis.get('stereo_analysis', {})
        stereo_recommendations = self._process_stereo_recommendations(stereo_analysis, genre)

        # Optimal mastering chain order
        chain_order = self._generate_mastering_chain_order(genre, track_analysis)

        # Reference tracks for the genre
        reference_tracks = self._get_reference_tracks(genre)

        return f"""
You are a Grammy-winning mastering engineer with 20+ years of experience. Analyze this track using professional mastering standards.

TRACK ANALYSIS:
- Genre: {genre} (Confidence: {track_analysis.get('genre_confidence', 0.8):.1%})
- Tempo: {track_analysis.get('tempo', 'unknown')} BPM
- Key: {track_analysis.get('key', 'unknown')}
- Current LUFS: {current_lufs:.1f} dB
- Target LUFS: {target_lufs:.1f} dB (Industry standard for {genre})
- Loudness Adjustment Needed: {loudness_adjustment:+.1f} dB

FREQUENCY ANALYSIS vs GENRE STANDARDS:
{freq_recommendations}

{masking_recommendations}

{stereo_recommendations}

PSYCHOACOUSTIC ANALYSIS:
- Target Spectral Centroid: {psychoacoustic_data['psychoacoustic_recommendations']['spectral_centroid_target']:.0f}Hz
- Current Brightness: {psychoacoustic_data['psychoacoustic_recommendations']['current_brightness']:.0f}Hz
- Brightness Adjustment: {psychoacoustic_data['brightness_adjustment']:+.1f}dB (8kHz-16kHz)
- Warmth Adjustment: {psychoacoustic_data['warmth_adjustment']:+.1f}dB (200Hz-800Hz)
- Dynamic Range Optimization: {psychoacoustic_data['dynamic_range_factor']:.2f}x

PROFESSIONAL REFERENCE STANDARDS FOR {genre.upper()}:
{reference_standards['description']}

OPTIMAL MASTERING CHAIN ORDER:
{' → '.join(chain_order).upper()}

PROFESSIONAL REFERENCE TRACKS FOR {genre.upper()}:
{chr(10).join([f"- {ref['artist']} - '{ref['track']}' ({ref['lufs']:.1f} LUFS): {ref['characteristics']}" for ref in reference_tracks])}

MASTERING OBJECTIVES:
1. Achieve {target_lufs:.1f} LUFS loudness standard (Industry: {genre})
2. Apply psychoacoustic-optimized frequency curve
3. Optimize dynamic range: {reference_standards['dynamic_range']:.1f}dB target
4. Enhance stereo imaging: {reference_standards['stereo_width']:.1f}x width
5. Add genre-appropriate character with optimal processing chain
6. Apply perceptual brightness/warmth balance

Please provide mastering suggestions in the following JSON format with 10-band parametric EQ:
{{
    "eq_settings": {{
        "bands": [
            {{"frequency": 60, "gain": 0, "q": 0.7, "type": "low_shelf"}},
            {{"frequency": 120, "gain": 1.0, "q": 1.0, "type": "peak"}},
            {{"frequency": 250, "gain": 0, "q": 1.0, "type": "peak"}},
            {{"frequency": 500, "gain": 0, "q": 1.0, "type": "peak"}},
            {{"frequency": 1000, "gain": 0, "q": 1.0, "type": "peak"}},
            {{"frequency": 2000, "gain": -1.0, "q": 1.0, "type": "peak"}},
            {{"frequency": 4000, "gain": 0, "q": 1.0, "type": "peak"}},
            {{"frequency": 8000, "gain": 2.0, "q": 1.0, "type": "peak"}},
            {{"frequency": 12000, "gain": 0, "q": 1.0, "type": "peak"}},
            {{"frequency": 16000, "gain": 1.0, "q": 0.7, "type": "high_shelf"}}
        ]
    }},
    "compression_settings": {{
        "threshold": -8,
        "ratio": 4.0,
        "attack": 0.003,
        "release": 0.1,
        "makeup_gain": 2
    }},
    "saturation_settings": {{
        "drive": 1.2,
        "type": "tube",
        "mix": 0.3
    }},
    "stereo_settings": {{
        "width": 1.1,
        "phase_correction": false,
        "bass_mono_freq": 120
    }},
    "limiting_settings": {{
        "ceiling": -0.3,
        "release": 0.05
    }},
    "masking_settings": {{
        "auto_correct": true,
        "boost_masked_frequencies": true,
        "sensitivity": 0.8
    }},
    "dynamic_range_settings": {{
        "target_dr": 12.0,
        "auto_optimize": true,
        "preserve_transients": true
    }},
    "loudness_settings": {{
        "target_lufs": -14.0,
        "auto_adjust": true,
        "genre_compliance": true
    }},
    "exciter_settings": {{
        "drive": 2.0,
        "frequency": 3000,
        "harmonics": "even",
        "mix": 0.3
    }},
    "reasoning": "Explanation of why these settings were chosen"
}}

Focus on:
1. Frequency balance based on the analysis using ALL 10 EQ bands
2. Dynamic range optimization with target_dr based on genre
3. Genre-appropriate character and loudness standards
4. Use the exact 10 frequencies provided (60Hz, 120Hz, 250Hz, 500Hz, 1kHz, 2kHz, 4kHz, 8kHz, 12kHz, 16kHz)
5. Set gain values between -6dB and +6dB for each band as needed
6. Use low_shelf for 60Hz, high_shelf for 16kHz, and peak for all others
7. Advanced masking correction based on frequency analysis
8. Professional LUFS targeting based on genre standards
9. Stereo imaging optimization
"""

    def _initialize_genre_standards(self) -> Dict[str, Dict[str, Any]]:
        """Initialize professional mastering standards for different genres"""
        return {
            'pop': {
                'target_lufs': -14.0,
                'dynamic_range': 8.0,
                'frequency_curve': {
                    60: 0, 120: 1.0, 250: 0, 500: 0, 1000: 0.5,
                    2000: 1.0, 4000: 1.5, 8000: 2.0, 12000: 1.0, 16000: 1.5
                },
                'compression': {'threshold': -8, 'ratio': 3.0, 'attack': 0.003, 'release': 0.1},
                'stereo_width': 1.2,
                'description': 'Modern pop: Bright, punchy, competitive loudness. Enhanced presence and air.'
            },
            'rock': {
                'target_lufs': -11.0,
                'dynamic_range': 6.0,
                'frequency_curve': {
                    60: 1.0, 120: 2.0, 250: 0.5, 500: 0, 1000: 0,
                    2000: 1.0, 4000: 2.5, 8000: 2.0, 12000: 1.0, 16000: 0.5
                },
                'compression': {'threshold': -6, 'ratio': 4.0, 'attack': 0.001, 'release': 0.05},
                'stereo_width': 1.1,
                'description': 'Rock: Powerful low-end, aggressive midrange, controlled dynamics for impact.'
            },
            'jazz': {
                'target_lufs': -18.0,
                'dynamic_range': 14.0,
                'frequency_curve': {
                    60: -1.0, 120: 0, 250: 0, 500: 0.5, 1000: 1.0,
                    2000: 1.5, 4000: 1.0, 8000: 2.0, 12000: 2.5, 16000: 2.0
                },
                'compression': {'threshold': -16, 'ratio': 2.0, 'attack': 0.01, 'release': 0.3},
                'stereo_width': 1.3,
                'description': 'Jazz: Natural dynamics, warm midrange, extended highs, wide stereo image.'
            },
            'electronic': {
                'target_lufs': -12.0,
                'dynamic_range': 5.0,
                'frequency_curve': {
                    60: 2.0, 120: 1.5, 250: 0, 500: -0.5, 1000: 0,
                    2000: 0.5, 4000: 1.0, 8000: 3.0, 12000: 2.0, 16000: 3.0
                },
                'compression': {'threshold': -4, 'ratio': 6.0, 'attack': 0.001, 'release': 0.03},
                'stereo_width': 1.4,
                'description': 'Electronic: Deep sub-bass, crisp highs, tight dynamics, wide stereo field.'
            },
            'classical': {
                'target_lufs': -23.0,
                'dynamic_range': 20.0,
                'frequency_curve': {
                    60: 0, 120: 0, 250: 0, 500: 0, 1000: 0.5,
                    2000: 1.0, 4000: 0.5, 8000: 1.5, 12000: 2.0, 16000: 1.5
                },
                'compression': {'threshold': -20, 'ratio': 1.5, 'attack': 0.05, 'release': 0.5},
                'stereo_width': 1.5,
                'description': 'Classical: Natural dynamics, subtle enhancement, preserve original character.'
            },
            'hip-hop': {
                'target_lufs': -10.0,
                'dynamic_range': 4.0,
                'frequency_curve': {
                    60: 3.0, 120: 2.5, 250: 1.0, 500: 0, 1000: -0.5,
                    2000: 0, 4000: 1.5, 8000: 2.5, 12000: 1.5, 16000: 2.0
                },
                'compression': {'threshold': -3, 'ratio': 8.0, 'attack': 0.001, 'release': 0.02},
                'stereo_width': 1.0,
                'description': 'Hip-hop: Massive sub-bass, punchy drums, aggressive limiting, controlled width.'
            },
            'country': {
                'target_lufs': -16.0,
                'dynamic_range': 10.0,
                'frequency_curve': {
                    60: 0, 120: 0.5, 250: 0.5, 500: 1.0, 1000: 1.5,
                    2000: 2.0, 4000: 2.5, 8000: 2.0, 12000: 1.5, 16000: 1.0
                },
                'compression': {'threshold': -10, 'ratio': 3.0, 'attack': 0.005, 'release': 0.15},
                'stereo_width': 1.2,
                'description': 'Country: Warm midrange, clear vocals, natural dynamics, moderate loudness.'
            }
        }

    def _get_genre_reference_standards(self, genre: str) -> Dict[str, Any]:
        """Get professional reference standards for a specific genre"""
        genre_lower = genre.lower()

        # Direct match
        if genre_lower in self.genre_standards:
            return self.genre_standards[genre_lower]

        # Fuzzy matching for similar genres
        genre_mapping = {
            'alternative': 'rock',
            'metal': 'rock',
            'punk': 'rock',
            'indie': 'pop',
            'dance': 'electronic',
            'techno': 'electronic',
            'house': 'electronic',
            'ambient': 'electronic',
            'folk': 'country',
            'blues': 'jazz',
            'r&b': 'pop',
            'soul': 'pop',
            'rap': 'hip-hop',
            'trap': 'hip-hop'
        }

        mapped_genre = genre_mapping.get(genre_lower, 'pop')
        return self.genre_standards[mapped_genre]

    def _analyze_frequency_balance(self, freq_bands: Dict[str, float], genre: str) -> str:
        """Analyze frequency balance against genre standards"""
        standards = self._get_genre_reference_standards(genre)

        # Map frequency bands to our analysis
        band_mapping = {
            'sub_bass': 60,
            'bass': 120,
            'low_mid': 250,
            'mid': 1000,
            'high_mid': 2000,
            'presence': 4000,
            'brilliance': 8000
        }

        analysis = []
        for band_name, current_level in freq_bands.items():
            if band_name in band_mapping:
                freq = band_mapping[band_name]
                target_curve = standards['frequency_curve']

                # Find closest frequency in target curve
                closest_freq = min(target_curve.keys(), key=lambda x: abs(x - freq))
                target_adjustment = target_curve[closest_freq]

                # Analyze current vs target
                if current_level < 0.1:  # Very low energy
                    if target_adjustment > 0:
                        analysis.append(f"- {band_name.upper()} ({freq}Hz): BOOST NEEDED (+{target_adjustment:.1f}dB) - Currently too quiet")
                    else:
                        analysis.append(f"- {band_name.upper()} ({freq}Hz): Appropriately low energy")
                elif current_level > 10.0:  # High energy
                    if target_adjustment < 0:
                        analysis.append(f"- {band_name.upper()} ({freq}Hz): CUT NEEDED ({target_adjustment:.1f}dB) - Currently too prominent")
                    else:
                        analysis.append(f"- {band_name.upper()} ({freq}Hz): Good energy level, enhance further (+{target_adjustment:.1f}dB)")
                else:  # Moderate energy
                    analysis.append(f"- {band_name.upper()} ({freq}Hz): Moderate energy, adjust by {target_adjustment:+.1f}dB for genre")

        return "\n".join(analysis)

    def _calculate_psychoacoustic_adjustments(self, track_analysis: Dict[str, Any], genre: str) -> Dict[str, Any]:
        """Calculate psychoacoustic-based mastering adjustments"""
        standards = self._get_genre_reference_standards(genre)
        spectral_features = track_analysis.get('spectral_features', {})

        # Analyze spectral centroid for brightness perception
        spectral_centroid = spectral_features.get('spectral_centroid_mean', 1000)
        target_brightness = {
            'pop': 2500, 'rock': 2200, 'jazz': 2800, 'electronic': 3500,
            'classical': 2000, 'hip-hop': 1800, 'country': 2300
        }.get(genre.lower(), 2500)

        brightness_adjustment = (target_brightness - spectral_centroid) / 1000.0

        # Analyze MFCC for timbral character
        mfcc_mean = spectral_features.get('mfcc_mean', [])
        if len(mfcc_mean) >= 13:
            # MFCC analysis for warmth/brightness balance
            warmth_indicator = mfcc_mean[1] if len(mfcc_mean) > 1 else 0
            brightness_indicator = mfcc_mean[2] if len(mfcc_mean) > 2 else 0

            # Calculate timbral adjustments
            warmth_adjustment = max(-2.0, min(2.0, -warmth_indicator / 50.0))
            high_freq_adjustment = max(-1.0, min(3.0, brightness_adjustment))
        else:
            warmth_adjustment = 0
            high_freq_adjustment = brightness_adjustment

        # Dynamic range analysis
        loudness = track_analysis.get('loudness', {})
        current_dr = loudness.get('dynamic_range', 10.0)
        target_dr = standards['dynamic_range']
        dr_adjustment_factor = target_dr / max(current_dr, 1.0)

        return {
            'brightness_adjustment': high_freq_adjustment,
            'warmth_adjustment': warmth_adjustment,
            'dynamic_range_factor': dr_adjustment_factor,
            'psychoacoustic_recommendations': {
                'spectral_centroid_target': target_brightness,
                'current_brightness': spectral_centroid,
                'warmth_balance': warmth_adjustment,
                'dynamic_optimization': dr_adjustment_factor
            }
        }

    def _generate_mastering_chain_order(self, genre: str, track_analysis: Dict[str, Any]) -> List[str]:
        """Generate optimal mastering chain order based on genre and track characteristics"""
        loudness = track_analysis.get('loudness', {})
        current_lufs = loudness.get('lufs_approx', -23)

        # Base chain order
        if genre.lower() in ['classical', 'jazz']:
            # Preserve dynamics, minimal processing
            return ['eq', 'saturation', 'compression', 'stereo', 'limiting']
        elif genre.lower() in ['hip-hop', 'electronic']:
            # Aggressive processing, tight control
            return ['eq', 'compression', 'saturation', 'stereo', 'limiting']
        elif current_lufs < -20:
            # Quiet track needs more aggressive processing
            return ['eq', 'compression', 'saturation', 'stereo', 'limiting']
        else:
            # Standard pop/rock chain
            return ['eq', 'saturation', 'compression', 'stereo', 'limiting']

    def _get_reference_tracks(self, genre: str) -> List[Dict[str, Any]]:
        """Get professional reference tracks for the genre"""
        reference_database = {
            'pop': [
                {'artist': 'Billie Eilish', 'track': 'Bad Guy', 'lufs': -14.1, 'characteristics': 'Modern pop loudness, controlled dynamics'},
                {'artist': 'Dua Lipa', 'track': 'Levitating', 'lufs': -13.8, 'characteristics': 'Bright, punchy, wide stereo'},
                {'artist': 'The Weeknd', 'track': 'Blinding Lights', 'lufs': -14.2, 'characteristics': 'Retro-modern balance'}
            ],
            'rock': [
                {'artist': 'Foo Fighters', 'track': 'Everlong', 'lufs': -11.5, 'characteristics': 'Powerful dynamics, guitar presence'},
                {'artist': 'Arctic Monkeys', 'track': 'Do I Wanna Know?', 'lufs': -10.8, 'characteristics': 'Modern rock loudness'},
                {'artist': 'Queens of the Stone Age', 'track': 'No One Knows', 'lufs': -11.2, 'characteristics': 'Aggressive midrange'}
            ],
            'jazz': [
                {'artist': 'Diana Krall', 'track': 'The Look of Love', 'lufs': -18.5, 'characteristics': 'Natural dynamics, warm'},
                {'artist': 'Norah Jones', 'track': 'Come Away With Me', 'lufs': -17.8, 'characteristics': 'Intimate, detailed'},
                {'artist': 'Brad Mehldau', 'track': 'Blackbird', 'lufs': -19.2, 'characteristics': 'Acoustic, spacious'}
            ],
            'electronic': [
                {'artist': 'Daft Punk', 'track': 'Get Lucky', 'lufs': -12.3, 'characteristics': 'Deep bass, crisp highs'},
                {'artist': 'Deadmau5', 'track': 'Strobe', 'lufs': -11.8, 'characteristics': 'Progressive dynamics'},
                {'artist': 'Flume', 'track': 'Never Be Like You', 'lufs': -12.1, 'characteristics': 'Modern electronic'}
            ],
            'hip-hop': [
                {'artist': 'Kendrick Lamar', 'track': 'HUMBLE.', 'lufs': -9.8, 'characteristics': 'Massive bass, tight dynamics'},
                {'artist': 'Drake', 'track': 'God\'s Plan', 'lufs': -10.2, 'characteristics': 'Commercial loudness'},
                {'artist': 'Travis Scott', 'track': 'SICKO MODE', 'lufs': -9.5, 'characteristics': 'Aggressive limiting'}
            ]
        }

        return reference_database.get(genre.lower(), reference_database['pop'])

    def _process_masking_recommendations(self, masking_analysis: Dict[str, Any], genre: str) -> str:
        """Process frequency masking analysis into actionable recommendations"""
        try:
            recommendations = masking_analysis.get('recommendations', [])
            total_masked = masking_analysis.get('total_masked_bands', 0)

            if total_masked == 0:
                return "No significant frequency masking detected - good spectral balance"

            masking_summary = f"FREQUENCY MASKING ANALYSIS ({total_masked} masked bands detected):\n"

            # Group recommendations by frequency range
            low_freq_issues = [r for r in recommendations if any(freq in r for freq in ['100', '200', '300', '400'])]
            mid_freq_issues = [r for r in recommendations if any(freq in r for freq in ['500', '600', '700', '800', '900', '1000', '1500'])]
            high_freq_issues = [r for r in recommendations if any(freq in r for freq in ['2000', '3000', '4000', '5000', '6000', '8000', '10000', '12000', '15000'])]

            if low_freq_issues:
                masking_summary += "- LOW FREQUENCIES: " + "; ".join(low_freq_issues[:2]) + "\n"
            if mid_freq_issues:
                masking_summary += "- MID FREQUENCIES: " + "; ".join(mid_freq_issues[:2]) + "\n"
            if high_freq_issues:
                masking_summary += "- HIGH FREQUENCIES: " + "; ".join(high_freq_issues[:2]) + "\n"

            return masking_summary

        except Exception as e:
            logger.error(f"Error processing masking recommendations: {e}")
            return "Masking analysis unavailable"

    def _process_stereo_recommendations(self, stereo_analysis: Dict[str, Any], genre: str) -> str:
        """Process stereo imaging analysis into actionable recommendations"""
        try:
            if stereo_analysis.get('is_mono', False):
                return "STEREO IMAGING: Track is mono - consider stereo enhancement for wider image"

            width = stereo_analysis.get('stereo_width', 1.0)
            correlation = stereo_analysis.get('correlation', 1.0)
            balance = stereo_analysis.get('balance', 0.0)
            phase_coherence = stereo_analysis.get('phase_coherence', 1.0)
            recommendations = stereo_analysis.get('recommendations', [])

            # Get genre-specific stereo standards
            standards = self._get_genre_reference_standards(genre)
            target_width = standards['stereo_width']

            stereo_summary = f"STEREO IMAGING ANALYSIS:\n"
            stereo_summary += f"- Current Width: {width:.2f} | Target: {target_width:.2f} ({genre})\n"
            stereo_summary += f"- Correlation: {correlation:.2f} | Phase Coherence: {phase_coherence:.2f}\n"

            if abs(balance) > 0.05:
                side = "right" if balance > 0 else "left"
                stereo_summary += f"- Balance Issue: {side} channel {abs(balance)*100:.1f}% louder\n"

            # Add specific recommendations
            if recommendations:
                stereo_summary += "- Recommendations: " + "; ".join(recommendations[:2])

            return stereo_summary

        except Exception as e:
            logger.error(f"Error processing stereo recommendations: {e}")
            return "Stereo analysis unavailable"
    
    def _create_user_request_prompt(self, user_message: str, current_settings: Dict[str, Any], 
                                  track_analysis: Dict[str, Any]) -> str:
        """Create prompt for user request processing"""
        return f"""
You are a mastering engineer assistant. The user wants to adjust the mastering of their track.

Current Track Analysis:
{json.dumps(track_analysis, indent=2)}

Current Mastering Settings:
{json.dumps(current_settings, indent=2)}

User Request: "{user_message}"

Please interpret the user's request and provide specific parameter adjustments in JSON format:
{{
    "adjustments": {{
        "eq_settings": {{
            "bands": [
                {{"frequency": 100, "gain": 2.0, "q": 0.7, "type": "peak"}}
            ]
        }},
        "compression_settings": {{
            "threshold": -8,
            "ratio": 4.0
        }},
        "saturation_settings": {{
            "drive": 1.2,
            "type": "tube"
        }},
        "stereo_settings": {{
            "width": 1.1
        }},
        "limiting_settings": {{
            "ceiling": -0.3
        }}
    }},
    "explanation": "Clear explanation of what changes were made and why",
    "suggestions": ["Additional suggestions for the user"]
}}

Common user requests and their meanings:
- "more bass" = boost low frequencies (60-250 Hz)
- "brighter" = boost high frequencies (8-15 kHz)
- "warmer" = slight low-mid boost, gentle high cut
- "punchier" = more compression, attack enhancement
- "wider" = increase stereo width
- "vintage/analog" = add saturation, tape-style processing
- "louder" = more compression and limiting
- "cleaner" = reduce saturation, gentle processing

Only include parameters that need to be changed based on the user's request.
"""
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract mastering parameters"""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return self._extract_parameters_from_text(response_text)
                
        except json.JSONDecodeError:
            logger.warning("Could not parse AI response as JSON")
            return self._extract_parameters_from_text(response_text)
    
    def _parse_adjustment_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response for parameter adjustments"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {'error': 'Could not parse response'}
                
        except json.JSONDecodeError:
            return {'error': 'Invalid response format'}
    
    def _extract_parameters_from_text(self, text: str) -> Dict[str, Any]:
        """Fallback method to extract parameters from text"""
        # Simple keyword-based extraction - only include settings that are being changed
        suggestions = {
            'reasoning': 'Extracted from text analysis'
        }
        
        text_lower = text.lower()

        # EQ suggestions - only add if specifically mentioned
        eq_bands = []
        if 'bass' in text_lower or 'low' in text_lower:
            eq_bands.append({
                'frequency': 60, 'gain': 3.0, 'q': 0.7, 'type': 'low_shelf'
            })

        if 'bright' in text_lower or 'treble' in text_lower or 'high' in text_lower:
            eq_bands.append({
                'frequency': 8000, 'gain': 2.0, 'q': 0.7, 'type': 'high_shelf'
            })

        # Only add EQ settings if there are actual changes
        if eq_bands:
            suggestions['eq_settings'] = {'bands': eq_bands}
        
        # Compression
        if 'compress' in text_lower or 'punch' in text_lower:
            suggestions['compression_settings'] = {
                'threshold': -8, 'ratio': 4.0, 'attack': 0.003, 'release': 0.1
            }

        # Advanced settings
        # Masking settings
        if 'mask' in text_lower or 'clarity' in text_lower or 'detail' in text_lower:
            suggestions['masking_settings'] = {
                'auto_correct': True,
                'boost_masked_frequencies': True,
                'sensitivity': 0.8
            }

        # Dynamic range settings
        if 'dynamic' in text_lower or 'punch' in text_lower or 'impact' in text_lower:
            suggestions['dynamic_range_settings'] = {
                'target_dr': 10.0,
                'auto_optimize': True,
                'preserve_transients': True
            }

        # Loudness settings
        if 'loud' in text_lower or 'volume' in text_lower or 'lufs' in text_lower:
            suggestions['loudness_settings'] = {
                'target_lufs': -14.0,
                'auto_adjust': True,
                'genre_compliance': True
            }

        # Advanced stereo settings
        if 'wide' in text_lower or 'stereo' in text_lower or 'space' in text_lower:
            suggestions['stereo_settings'] = {
                'width': 1.3,
                'phase_correction': True,
                'bass_mono_freq': 120
            }

        # Phase issues
        if 'phase' in text_lower or 'correlation' in text_lower:
            suggestions['stereo_settings'] = {
                'width': 1.0,
                'phase_correction': True,
                'bass_mono_freq': 100
            }

        # Exciter settings
        if 'bright' in text_lower or 'presence' in text_lower or 'air' in text_lower or 'sparkle' in text_lower:
            suggestions['exciter_settings'] = {
                'drive': 3.0,
                'frequency': 4000,
                'harmonics': 'even',
                'mix': 0.4
            }

        if 'warm' in text_lower or 'vintage' in text_lower or 'character' in text_lower:
            suggestions['exciter_settings'] = {
                'drive': 2.0,
                'frequency': 2000,
                'harmonics': 'odd',
                'mix': 0.3
            }

        return suggestions
    
    def _get_fallback_suggestions(self, track_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback suggestions when AI fails"""
        genre = track_analysis.get('predicted_genre', 'rock')
        
        # Basic genre-based suggestions
        if genre == 'electronic':
            return {
                'eq_settings': {
                    'bands': [
                        {'frequency': 60, 'gain': 3, 'q': 0.7, 'type': 'peak'},
                        {'frequency': 8000, 'gain': 2, 'q': 0.7, 'type': 'peak'}
                    ]
                },
                'compression_settings': {
                    'threshold': -6, 'ratio': 6.0, 'attack': 0.001, 'release': 0.05
                },
                'limiting_settings': {
                    'ceiling': -0.1, 'release': 0.03
                },
                'masking_settings': {
                    'auto_correct': True,
                    'boost_masked_frequencies': True,
                    'sensitivity': 0.9
                },
                'dynamic_range_settings': {
                    'target_dr': 5.0,
                    'auto_optimize': True,
                    'preserve_transients': False
                },
                'loudness_settings': {
                    'target_lufs': -12.0,
                    'auto_adjust': True,
                    'genre_compliance': True
                },
                'reasoning': 'Electronic music preset applied'
            }
        else:
            return {
                'eq_settings': {
                    'bands': [
                        {'frequency': 100, 'gain': 1, 'q': 0.7, 'type': 'peak'},
                        {'frequency': 3000, 'gain': -1, 'q': 1.0, 'type': 'peak'},
                        {'frequency': 10000, 'gain': 2, 'q': 0.7, 'type': 'peak'}
                    ]
                },
                'compression_settings': {
                    'threshold': -10, 'ratio': 3.0, 'attack': 0.005, 'release': 0.1
                },
                'limiting_settings': {
                    'ceiling': -0.5, 'release': 0.05
                },
                'reasoning': 'General mastering preset applied'
            }
