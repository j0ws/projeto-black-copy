from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class VideoMetadata(Base):
    __tablename__ = "video_metadata"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True) # 'youtube' or 'tiktok'
    external_id = Column(String, unique=True, index=True)
    url = Column(String)
    title = Column(String)
    duration = Column(Float)
    view_count = Column(Integer)
    like_count = Column(Integer)
    channel_name = Column(String)
    
    # Relationships
    timestamps = relationship("KeywordTimestamp", back_populates="video", cascade="all, delete")

class KeywordTimestamp(Base):
    __tablename__ = "keyword_timestamps"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("video_metadata.id"))
    keyword = Column(String, index=True)
    start_time = Column(Float)
    end_time = Column(Float)
    context_text = Column(String)
    
    # Relationships
    video = relationship("VideoMetadata", back_populates="timestamps")

class DownloadedClip(Base):
    __tablename__ = "downloaded_clips"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)
    file_path = Column(String)
