from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import uuid
import aiofiles
from ..core.database import get_db
from ..core.config import settings
from ..models.track import Track, MasteringSession
from ..tasks import analyze_audio_track, process_mastering, process_ai_adjustment
from ..services.mastering_engine import MasteringEngine
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.post("/upload")
async def upload_track(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload audio track for processing"""
    try:
        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {settings.ALLOWED_AUDIO_FORMATS}"
            )
        
        # Validate file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create track record
        track = Track(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content)
        )
        
        db.add(track)
        db.commit()
        db.refresh(track)
        
        # Start analysis task
        task = analyze_audio_track.delay(track.id)
        
        return {
            "track_id": track.id,
            "filename": file.filename,
            "analysis_task_id": task.id,
            "status": "uploaded",
            "message": "Track uploaded successfully. Analysis started."
        }
        
    except Exception as e:
        logger.error(f"Error uploading track: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{track_id}")
async def get_track(track_id: int, db: Session = Depends(get_db)):
    """Get track information"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return {
        "id": track.id,
        "filename": track.original_filename,
        "duration": track.duration,
        "sample_rate": track.sample_rate,
        "channels": track.channels,
        "predicted_genre": track.predicted_genre,
        "genre_confidence": track.genre_confidence,
        "tempo": track.tempo,
        "key": track.key,
        "loudness": track.loudness,
        "spectral_features": track.spectral_features,
        "frequency_analysis": track.frequency_analysis,
        "masking_analysis": track.masking_analysis,
        "stereo_analysis": track.stereo_analysis,
        "is_analyzed": track.is_analyzed,
        "is_processed": track.is_processed,
        "analysis_error": track.analysis_error,
        "created_at": track.created_at
    }


@router.get("/{track_id}/analysis")
async def get_track_analysis(track_id: int, db: Session = Depends(get_db)):
    """Get detailed track analysis"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.is_analyzed:
        raise HTTPException(status_code=400, detail="Track not yet analyzed")
    
    return {
        "track_id": track.id,
        "analysis": {
            "duration": track.duration,
            "predicted_genre": track.predicted_genre,
            "genre_confidence": track.genre_confidence,
            "tempo": track.tempo,
            "key": track.key,
            "loudness": track.loudness,
            "spectral_features": track.spectral_features,
            "frequency_analysis": track.frequency_analysis,
            "masking_analysis": track.masking_analysis,
            "stereo_analysis": track.stereo_analysis
        }
    }


@router.post("/{track_id}/master")
async def master_track(
    track_id: int,
    mastering_settings: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Apply mastering to track"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not track.is_analyzed:
        raise HTTPException(status_code=400, detail="Track must be analyzed first")
    
    # Start mastering task
    task = process_mastering.delay(track_id, mastering_settings)
    
    return {
        "track_id": track_id,
        "mastering_task_id": task.id,
        "status": "processing",
        "message": "Mastering started"
    }


@router.get("/{track_id}/preset/{genre}")
async def get_genre_preset(track_id: int, genre: str, db: Session = Depends(get_db)):
    """Get mastering preset for specific genre"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    mastering_engine = MasteringEngine()
    preset = mastering_engine.get_genre_preset(genre)
    
    return {
        "track_id": track_id,
        "genre": genre,
        "preset": preset
    }


@router.get("/{track_id}/download")
async def download_original(track_id: int, db: Session = Depends(get_db)):
    """Download original track"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if not os.path.exists(track.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=track.file_path,
        filename=track.original_filename,
        media_type='audio/mpeg'
    )


@router.get("/{track_id}/download/mastered")
async def download_mastered(track_id: int, session_id: int = None, db: Session = Depends(get_db)):
    """Download mastered track"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Get latest mastering session if session_id not provided
    if session_id:
        session = db.query(MasteringSession).filter(
            MasteringSession.id == session_id,
            MasteringSession.track_id == track_id
        ).first()
    else:
        session = db.query(MasteringSession).filter(
            MasteringSession.track_id == track_id
        ).order_by(MasteringSession.created_at.desc()).first()
    
    if not session or not session.processed_file_path:
        raise HTTPException(status_code=404, detail="No mastered version found")
    
    if not os.path.exists(session.processed_file_path):
        raise HTTPException(status_code=404, detail="Mastered file not found")
    
    mastered_filename = f"mastered_{track.original_filename}"
    
    return FileResponse(
        path=session.processed_file_path,
        filename=mastered_filename,
        media_type='audio/mpeg'
    )


@router.get("/{track_id}/sessions")
async def get_mastering_sessions(track_id: int, db: Session = Depends(get_db)):
    """Get all mastering sessions for a track"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    sessions = db.query(MasteringSession).filter(
        MasteringSession.track_id == track_id
    ).order_by(MasteringSession.created_at.desc()).all()
    
    return {
        "track_id": track_id,
        "sessions": [
            {
                "id": session.id,
                "eq_settings": session.eq_settings,
                "compression_settings": session.compression_settings,
                "limiting_settings": session.limiting_settings,
                "saturation_settings": session.saturation_settings,
                "stereo_settings": session.stereo_settings,
                "ai_suggestions": session.ai_suggestions,
                "user_feedback": session.user_feedback,
                "processing_time": session.processing_time,
                "created_at": session.created_at
            }
            for session in sessions
        ]
    }


@router.delete("/{track_id}")
async def delete_track(track_id: int, db: Session = Depends(get_db)):
    """Delete track and associated files"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Delete associated mastering sessions
    sessions = db.query(MasteringSession).filter(MasteringSession.track_id == track_id).all()
    for session in sessions:
        if session.processed_file_path and os.path.exists(session.processed_file_path):
            os.remove(session.processed_file_path)
        db.delete(session)
    
    # Delete original file
    if os.path.exists(track.file_path):
        os.remove(track.file_path)
    
    # Delete track record
    db.delete(track)
    db.commit()
    
    return {"message": "Track deleted successfully"}
