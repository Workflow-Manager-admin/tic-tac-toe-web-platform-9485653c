from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    games_x = relationship("Game", back_populates="user_x", foreign_keys="Game.user_x_id")
    games_o = relationship("Game", back_populates="user_o", foreign_keys="Game.user_o_id")

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_x_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user_o_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user_x = relationship("User", foreign_keys=[user_x_id], back_populates="games_x")
    user_o = relationship("User", foreign_keys=[user_o_id], back_populates="games_o")
    moves = Column(JSON, default=list)
    winner = Column(String, nullable=True) # 'X', 'O', or None
    is_pvp = Column(Boolean, default=True)

class SessionToken(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    user = relationship("User")
