from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel
from ..core.database import get_db
from ..models.track import Track, MasteringSession
from ..tasks import process_ai_adjustment
from ..services.ai_mastering import AIMasteringService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    track_id: int
    message: str
    current_settings: Dict[str, Any] = {}
    apply_changes: bool = True


class ChatResponse(BaseModel):
    response: str
    adjustments: Dict[str, Any] = {}
    task_id: Optional[str] = None
    suggestions: list = []


@router.post("/mastering", response_model=ChatResponse)
async def chat_mastering(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat interface for mastering adjustments"""
    try:
        # Validate track exists and is analyzed
        track = db.query(Track).filter(Track.id == request.track_id).first()
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        if not track.is_analyzed:
            raise HTTPException(status_code=400, detail="Track must be analyzed first")
        
        # Prepare track analysis data
        track_analysis = {
            'predicted_genre': track.predicted_genre,
            'tempo': track.tempo,
            'key': track.key,
            'loudness': track.loudness,
            'frequency_analysis': track.frequency_analysis,
            'spectral_features': track.spectral_features
        }
        
        # Get AI service
        ai_service = AIMasteringService()
        
        # Process the user request
        result = ai_service.process_user_request(
            request.message,
            request.current_settings,
            track_analysis
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        response_text = result.get('explanation', 'I understand your request.')
        adjustments = result.get('adjustments', {})
        suggestions = result.get('suggestions', [])
        
        task_id = None
        
        # Apply changes if requested and adjustments are available
        if request.apply_changes and adjustments:
            # Start background task to apply adjustments
            task = process_ai_adjustment.delay(
                request.track_id,
                request.message,
                request.current_settings
            )
            task_id = task.id
            response_text += " I'm applying these changes now..."
        
        return ChatResponse(
            response=response_text,
            adjustments=adjustments,
            task_id=task_id,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error in chat mastering: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest")
async def get_ai_suggestions(
    track_id: int,
    db: Session = Depends(get_db)
):
    """Get AI mastering suggestions for a track"""
    try:
        # Validate track exists and is analyzed
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        if not track.is_analyzed:
            raise HTTPException(status_code=400, detail="Track must be analyzed first")
        
        # Prepare track analysis data
        track_analysis = {
            'predicted_genre': track.predicted_genre,
            'tempo': track.tempo,
            'key': track.key,
            'loudness': track.loudness,
            'frequency_analysis': track.frequency_analysis,
            'spectral_features': track.spectral_features
        }
        
        # Get AI suggestions
        ai_service = AIMasteringService()
        suggestions = ai_service.analyze_and_suggest(track_analysis)
        
        return {
            "track_id": track_id,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def get_chat_examples():
    """Get example chat commands for users"""
    return {
        "examples": [
            {
                "category": "EQ Adjustments",
                "commands": [
                    "Add more bass",
                    "Make it brighter",
                    "Reduce the harshness in the mids",
                    "Boost the presence",
                    "Cut the muddy frequencies"
                ]
            },
            {
                "category": "Dynamics",
                "commands": [
                    "Make it punchier",
                    "Add more compression",
                    "Reduce the compression",
                    "Make it more dynamic",
                    "Tighten the sound"
                ]
            },
            {
                "category": "Character",
                "commands": [
                    "Make it sound more vintage",
                    "Add some warmth",
                    "Make it sound more analog",
                    "Add some tape saturation",
                    "Make it cleaner"
                ]
            },
            {
                "category": "Stereo",
                "commands": [
                    "Make it wider",
                    "Narrow the stereo image",
                    "Enhance the stereo field",
                    "Make it more mono compatible"
                ]
            },
            {
                "category": "Loudness",
                "commands": [
                    "Make it louder",
                    "Reduce the limiting",
                    "Match streaming loudness",
                    "Preserve more dynamics"
                ]
            },
            {
                "category": "Genre Specific",
                "commands": [
                    "Make it sound more like rock",
                    "Give it an electronic feel",
                    "Make it jazz-like",
                    "Add hip-hop character"
                ]
            }
        ]
    }
