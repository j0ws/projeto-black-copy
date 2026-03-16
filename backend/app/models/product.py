from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    """
    Module 2: Product Intelligence Engine (The Brain)
    Stores the strategic marketing briefing for specific products.
    JSON columns are used for simple, flat lists like ingredients and worst_alternatives
    to keep the schema scalable without over-engineering relation tables for simple tags.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    # Simple arrays stored as JSON
    ingredients = Column(JSON, default=list) # e.g. ["L-Arginine", "Taurine"]
    use_cases = Column(JSON, default=list) # e.g. ["Gym", "Sexual Performance"]
    worst_alternatives = Column(JSON, default=list) # e.g. ["Tadalafil", "Steroids"]

    # Relationships (One-To-Many)
    benefits = relationship("Benefit", back_populates="product", cascade="all, delete-orphan")
    pain_points = relationship("PainPoint", back_populates="product", cascade="all, delete-orphan")
    objections = relationship("Objection", back_populates="product", cascade="all, delete-orphan")

class Benefit(Base):
    __tablename__ = "benefits"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    description = Column(String, nullable=False)

    product = relationship("Product", back_populates="benefits")

class PainPoint(Base):
    __tablename__ = "pain_points"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    description = Column(String, nullable=False) # e.g., "Late on phone at night"
    lf8_trigger = Column(String, nullable=False) # e.g., "Survival and Life Extension (LF1)"

    product = relationship("Product", back_populates="pain_points")

class Objection(Base):
    __tablename__ = "objections"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(String, nullable=False) # 'Objection' or 'FAQ'
    question = Column(String, nullable=False) # The doubt itself
    answer = Column(String, nullable=False) # How to break it in copy

    product = relationship("Product", back_populates="objections")
