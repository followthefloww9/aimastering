from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
from ..core.database import Base


class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    duration = Column(Float, nullable=True)
    
    # Audio Analysis Results
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bit_depth = Column(Integer, nullable=True)
    
    # ML Analysis
    predicted_genre = Column(String, nullable=True)
    genre_confidence = Column(Float, nullable=True)
    tempo = Column(Float, nullable=True)
    key = Column(String, nullable=True)
    loudness = Column(JSON, nullable=True)
    
    # Frequency Analysis
    spectral_features = Column(JSON, nullable=True)  # Store as JSON
    frequency_analysis = Column(JSON, nullable=True)

    # Advanced Analysis
    masking_analysis = Column(JSON, nullable=True)  # Frequency masking analysis
    stereo_analysis = Column(JSON, nullable=True)   # Stereo imaging analysis
    
    # Processing Status
    is_analyzed = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    analysis_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MasteringSession(Base):
    __tablename__ = "mastering_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, nullable=False)
    
    # Mastering Parameters
    eq_settings = Column(JSON, nullable=True)
    compression_settings = Column(JSON, nullable=True)
    limiting_settings = Column(JSON, nullable=True)
    saturation_settings = Column(JSON, nullable=True)
    stereo_settings = Column(JSON, nullable=True)
    
    # AI Suggestions
    ai_suggestions = Column(JSON, nullable=True)
    user_feedback = Column(Text, nullable=True)
    
    # Output
    processed_file_path = Column(String, nullable=True)
    processing_time = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
