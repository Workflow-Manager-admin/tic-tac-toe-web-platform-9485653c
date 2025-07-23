from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# --- User Models ---

# PUBLIC_INTERFACE
class UserRegister(BaseModel):
    """Request body for registering a new user."""
    username: str = Field(..., description="Unique username")
    password: str = Field(..., description="Password (plain, will be hashed)")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Request body for logging in a user."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password (plain, will be hashed)")

# PUBLIC_INTERFACE
class UserOut(BaseModel):
    """User response body (excluding password hash)."""
    id: int
    username: str

# --- JWT and Auth Models ---

# PUBLIC_INTERFACE
class Token(BaseModel):
    """Access token returned after login/registration."""
    access_token: str
    token_type: str = "bearer"

# --- Game Models ---

# PUBLIC_INTERFACE
class Move(BaseModel):
    """A move in the game."""
    row: int = Field(..., ge=0, le=2, description="Row (0..2)")
    col: int = Field(..., ge=0, le=2, description="Col (0..2)")
    player: str = Field(..., description="Symbol: 'X' or 'O'")

# PUBLIC_INTERFACE
class GameState(BaseModel):
    """Represents the current state of the board."""
    board: List[List[Optional[str]]] = Field(..., description="3x3 grid: 'X', 'O', or None")
    current_turn: str = Field(..., description="'X' or 'O'")
    is_over: bool = Field(..., description="True if game is finished")
    winner: Optional[str] = Field(None, description="Winner symbol, or None if draw/ongoing")

# PUBLIC_INTERFACE
class GameRecord(BaseModel):
    """Represents a persisted game record."""
    id: int
    created_at: datetime
    user_x: Optional[str] = Field(None, description="Username for 'X' player")
    user_o: Optional[str] = Field(None, description="Username for 'O' player (or 'AI' if vs AI)")
    winner: Optional[str] = Field(None, description="Winner symbol or None")
    moves: List[Move] = Field(..., description="List of moves made in the game")
    is_pvp: bool = True

# --- Leaderboard ---

# PUBLIC_INTERFACE
class UserStats(BaseModel):
    """Statistical summary of a user's Tic Tac Toe results."""
    username: str
    games_played: int
    wins: int
    draws: int
    losses: int

# PUBLIC_INTERFACE
class LeaderboardEntry(BaseModel):
    username: str
    wins: int

# --- Session Models ---

# PUBLIC_INTERFACE
class SessionInfo(BaseModel):
    """Describes session information for the current user."""
    user_id: int
    username: str
    valid_until: datetime

