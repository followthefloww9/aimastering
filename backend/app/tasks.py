from celery import current_task
from .celery_app import celery_app
from .services.audio_analyzer import AudioAnalyzer
from .services.mastering_engine import MasteringEngine
from .services.ai_mastering import AIMasteringService
from .core.database import SessionLocal
from .models.track import Track, MasteringSession
import librosa
import soundfile as sf
import numpy as np
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def analyze_audio_track(self, track_id: int):
    """Analyze audio track in background"""
    db = SessionLocal()
    try:
        # Update task status
        current_task.update_state(state='PROGRESS', meta={'progress': 10})
        
        # Get track from database
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise ValueError(f"Track {track_id} not found")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 20})

        # Initialize analyzer
        analyzer = AudioAnalyzer()

        current_task.update_state(state='PROGRESS', meta={'progress': 30})

        # Define progress callback
        def progress_callback(step: str, progress: int):
            # Map analysis steps to progress range 30-60%
            mapped_progress = 30 + (progress * 0.3)  # 30% base + 30% range
            current_task.update_state(state='PROGRESS', meta={
                'progress': int(mapped_progress),
                'status': f'Analyzing: {step}'
            })

        # Analyze the track with progress updates
        analysis_results = analyzer.analyze_track(track.file_path, progress_callback)

        current_task.update_state(state='PROGRESS', meta={'progress': 60})

        # Update track with analysis results
        track.duration = analysis_results['duration']
        track.sample_rate = analysis_results['sample_rate']
        track.channels = analysis_results['channels']
        track.predicted_genre = analysis_results['predicted_genre']
        track.genre_confidence = analysis_results['genre_confidence']
        track.tempo = analysis_results['tempo']
        track.key = analysis_results['key']
        track.loudness = analysis_results['loudness']
        track.spectral_features = analysis_results['spectral_features']
        track.frequency_analysis = analysis_results['frequency_analysis']
        track.masking_analysis = analysis_results.get('masking_analysis')
        track.stereo_analysis = analysis_results.get('stereo_analysis')
        track.is_analyzed = True

        db.commit()

        current_task.update_state(state='PROGRESS', meta={'progress': 75})
        
        # Get AI suggestions
        current_task.update_state(state='PROGRESS', meta={'progress': 80})
        ai_service = AIMasteringService()
        ai_suggestions = ai_service.analyze_and_suggest(analysis_results)

        current_task.update_state(state='PROGRESS', meta={'progress': 95})

        # Automatically apply AI suggestions by creating a mastering session
        if ai_suggestions and 'eq_settings' in ai_suggestions:
            try:
                # Create initial mastering session with AI suggestions
                mastering_session = MasteringSession(
                    track_id=track_id,
                    eq_settings=ai_suggestions.get('eq_settings'),
                    compression_settings=ai_suggestions.get('compression_settings'),
                    limiting_settings=ai_suggestions.get('limiting_settings'),
                    saturation_settings=ai_suggestions.get('saturation_settings'),
                    stereo_settings=ai_suggestions.get('stereo_settings'),
                    ai_suggestions=ai_suggestions,
                    user_feedback="Initial AI suggestions applied automatically"
                )

                db.add(mastering_session)
                db.commit()

                logger.info(f"Applied AI suggestions automatically for track {track_id}")

            except Exception as e:
                logger.error(f"Error applying AI suggestions for track {track_id}: {e}")

        current_task.update_state(state='PROGRESS', meta={'progress': 100})

        return {
            'track_id': track_id,
            'analysis': analysis_results,
            'ai_suggestions': ai_suggestions,
            'auto_applied': True,
            'status': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Error analyzing track {track_id}: {e}")
        
        # Update track with error
        track = db.query(Track).filter(Track.id == track_id).first()
        if track:
            track.analysis_error = str(e)
            db.commit()
        
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def process_mastering(self, track_id: int, mastering_settings: Dict[str, Any]):
    """Apply mastering processing to track"""
    db = SessionLocal()
    try:
        current_task.update_state(state='PROGRESS', meta={'progress': 10})
        
        # Get track from database
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise ValueError(f"Track {track_id} not found")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 20})
        
        # Load audio file (preserve stereo)
        audio_data, sample_rate = librosa.load(track.file_path, sr=None, mono=False)
        
        current_task.update_state(state='PROGRESS', meta={'progress': 40})
        
        # Initialize mastering engine
        mastering_engine = MasteringEngine(sample_rate=sample_rate)
        
        # Apply mastering chain
        processed_audio = mastering_engine.apply_mastering_chain(audio_data, mastering_settings)
        
        current_task.update_state(state='PROGRESS', meta={'progress': 70})
        
        # Save processed audio with unique filename based on settings hash
        import hashlib
        import json

        # Create a hash of the mastering settings to ensure consistency
        settings_str = json.dumps(mastering_settings, sort_keys=True)
        settings_hash = hashlib.md5(settings_str.encode()).hexdigest()[:8]

        output_filename = f"mastered_{track.id}_{settings_hash}.wav"
        output_path = os.path.join("uploads", output_filename)

        # Handle stereo output properly - always save as stereo
        print(f"Processed audio shape before saving: {processed_audio.shape}")

        if len(processed_audio.shape) > 1:
            if processed_audio.shape[0] == 2:
                # Stereo format (2, samples) - transpose to (samples, 2) for soundfile
                processed_audio = processed_audio.T
            elif processed_audio.shape[1] == 2:
                # Already in (samples, 2) format
                pass
            else:
                # Single channel in 2D - convert to stereo
                if processed_audio.shape[0] == 1:
                    mono_channel = processed_audio[0]
                else:
                    mono_channel = processed_audio[:, 0]
                processed_audio = np.column_stack([mono_channel, mono_channel])
        else:
            # Mono 1D array - convert to stereo
            processed_audio = np.column_stack([processed_audio, processed_audio])

        # Final check - ensure exactly 2 channels
        if len(processed_audio.shape) == 2 and processed_audio.shape[1] == 1:
            processed_audio = np.column_stack([processed_audio[:, 0], processed_audio[:, 0]])

        print(f"Final audio shape for saving: {processed_audio.shape}")
        sf.write(output_path, processed_audio, sample_rate)
        
        current_task.update_state(state='PROGRESS', meta={'progress': 90})
        
        # Create mastering session record
        mastering_session = MasteringSession(
            track_id=track_id,
            eq_settings=mastering_settings.get('eq_settings'),
            compression_settings=mastering_settings.get('compression_settings'),
            limiting_settings=mastering_settings.get('limiting_settings'),
            saturation_settings=mastering_settings.get('saturation_settings'),
            stereo_settings=mastering_settings.get('stereo_settings'),
            processed_file_path=output_path
        )
        
        db.add(mastering_session)
        
        # Update track status
        track.is_processed = True
        
        db.commit()
        
        current_task.update_state(state='PROGRESS', meta={'progress': 100})
        
        return {
            'track_id': track_id,
            'session_id': mastering_session.id,
            'output_path': output_path,
            'status': 'completed'
        }
        
    except Exception as e:
        logger.error(f"Error processing mastering for track {track_id}: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def process_ai_adjustment(self, track_id: int, user_message: str, current_settings: Dict[str, Any]):
    """Process AI-based mastering adjustment"""
    db = SessionLocal()
    try:
        current_task.update_state(state='PROGRESS', meta={'progress': 20})
        
        # Get track analysis
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track or not track.is_analyzed:
            raise ValueError(f"Track {track_id} not found or not analyzed")
        
        # Prepare track analysis data
        track_analysis = {
            'predicted_genre': track.predicted_genre,
            'tempo': track.tempo,
            'key': track.key,
            'loudness': track.loudness,
            'frequency_analysis': track.frequency_analysis,
            'spectral_features': track.spectral_features
        }
        
        current_task.update_state(state='PROGRESS', meta={'progress': 50})
        
        # Get AI suggestions
        ai_service = AIMasteringService()
        adjustments = ai_service.process_user_request(user_message, current_settings, track_analysis)
        
        current_task.update_state(state='PROGRESS', meta={'progress': 80})
        
        # Apply the adjustments if requested
        if adjustments.get('adjustments'):
            # Merge adjustments with current settings
            updated_settings = current_settings.copy()
            for key, value in adjustments['adjustments'].items():
                if key in updated_settings:
                    updated_settings[key].update(value)
                else:
                    updated_settings[key] = value
            
            # Process the updated mastering
            result = process_mastering.delay(track_id, updated_settings)
            
            current_task.update_state(state='PROGRESS', meta={'progress': 100})
            
            return {
                'track_id': track_id,
                'adjustments': adjustments,
                'updated_settings': updated_settings,
                'processing_task_id': result.id,
                'status': 'completed'
            }
        else:
            return {
                'track_id': track_id,
                'adjustments': adjustments,
                'status': 'completed'
            }
        
    except Exception as e:
        logger.error(f"Error processing AI adjustment for track {track_id}: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
    finally:
        db.close()
