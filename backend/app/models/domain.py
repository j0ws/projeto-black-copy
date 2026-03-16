from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    niche = Column(String, index=True)
    status = Column(String, default="pending")  # pending, processing, completed
    viral_videos_analyzed = Column(Integer, default=0)
    
    # Relação com os Vídeos e Segmentos
    videos = relationship("VideoAsset", back_populates="project")
    segments = relationship("Segment", back_populates="project")

class VideoAsset(Base):
    __tablename__ = "video_assets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    url = Column(String)
    title = Column(String)
    gmv_generated = Column(Float, default=0.0)
    
    project = relationship("Project", back_populates="videos")

class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(String)
    text_rewritten = Column(String, nullable=True)
    role = Column(String)
    tone_label = Column(String)
    risk_score = Column(Float)
    compliance_flags = Column(JSON)
    
    project = relationship("Project", back_populates="segments")
