"""
Database models for Voyage application
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """
    User model for authentication and profile management
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to trip plans
    trip_plans = relationship("TripPlan", back_populates="user", cascade="all, delete-orphan")


class TripPlan(Base):
    """
    Trip plan model to store generated itineraries
    """
    __tablename__ = "trip_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Trip details
    title = Column(String, nullable=False)
    origin_city = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    num_days = Column(Integer, nullable=False)
    num_people = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    interests = Column(String, nullable=True)
    
    # Generated content
    itinerary = Column(Text, nullable=False)  # The full AI-generated plan
    
    # Metadata
    is_budget_sufficient = Column(Boolean, default=True)
    estimated_cost = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="trip_plans")


class SavedDestination(Base):
    """
    User's saved/favorite destinations
    """
    __tablename__ = "saved_destinations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination_name = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
