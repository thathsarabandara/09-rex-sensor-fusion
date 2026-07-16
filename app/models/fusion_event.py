from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, text
from sqlalchemy.sql import func
from app.config.database import Base
from datetime import datetime

class FusionEvent(Base):
    __tablename__ = "fusion_events"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(String(36), index=True, nullable=False)
    event_type = Column(String(50), index=True, nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    data = Column(JSON, nullable=True)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, server_default=func.now())
