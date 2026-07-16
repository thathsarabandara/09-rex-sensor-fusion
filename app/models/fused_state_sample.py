from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.config.database import Base
from datetime import datetime

class FusedStateSample(Base):
    __tablename__ = "fused_state_samples"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(String(36), index=True, nullable=False)
    sequence = Column(Integer, nullable=False)
    fused_data = Column(JSON, nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, server_default=func.now())
