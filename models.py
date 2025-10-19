from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), index=True)
    email = Column(String(255), unique=True, index=True)
    activo = Column(Boolean, default=False)#Account disabled by default
    profile_picture = Column(Boolean, default=False)