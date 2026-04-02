from sqlalchemy import Column, Integer, String, Boolean
from .base_class import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    channel = Column(String)  # 'email', 'sms', 'push'
    is_opted_in = Column(Boolean, default=True)
